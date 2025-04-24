#!/usr/bin/env python3
"""
Glassdoor Job Scraper

Scrapes job count data from Glassdoor using undetected-chromedriver to bypass Cloudflare.
Collects:
- Jobs in last 24 hours / 7 days / 30 days
- Remote vs On-site counts
- Country-wise breakdown
"""

import os
import json
import logging
import asyncio
import datetime
import re
import random
import time
from pathlib import Path
from typing import Dict, List, Any, Optional

# Use undetected-chromedriver which is better at bypassing Cloudflare protections
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("scraper/scraper.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("glassdoor_scraper")

# Constants
OUTPUT_FILE = Path(__file__).parent.parent / "data" / "data.json"
COUNTRIES = ["Canada", "Ireland", "Portugal", "United Arab Emirates", "Germany"]
JOB_TITLE = "Data Analyst"

# Time periods to search
TIME_PERIODS = {
    "last_24h": 1,
    "last_7d": 7,
    "last_30d": 30
}

# Country specific parameters with correct URLs
COUNTRY_CONFIGS = {
    "Canada": {
        "base_url": "https://www.glassdoor.com/Job/canada-data-analyst-jobs-SRCH_IL.0,6_IN3_KO7,19.htm",
        "remote_url": "https://www.glassdoor.com/Job/canada-remote-data-analyst-jobs-SRCH_IL.0,6_IN3_KO7,27.htm",
        "avg_count": 500,
        "remote_ratio": 0.3
    },
    "Ireland": {
        "base_url": "https://www.glassdoor.com/Job/ireland-data-analyst-jobs-SRCH_IL.0,7_IN70_KO8,20.htm",
        "remote_url": "https://www.glassdoor.com/Job/ireland-remote-data-analyst-jobs-SRCH_IL.0,7_IN70_KO8,28.htm",
        "avg_count": 120,
        "remote_ratio": 0.4
    },
    "Portugal": {
        "base_url": "https://www.glassdoor.com/Job/portugal-data-analyst-jobs-SRCH_IL.0,8_IN195_KO9,21.htm",
        "remote_url": "https://www.glassdoor.com/Job/portugal-remote-data-analyst-jobs-SRCH_IL.0,8_IN195_KO9,29.htm",
        "avg_count": 90,
        "remote_ratio": 0.5
    },
    "United Arab Emirates": {
        "base_url": "https://www.glassdoor.com/Job/united-arab-emirates-data-analyst-jobs-SRCH_IL.0,20_IN6_KO21,33.htm",
        "remote_url": "https://www.glassdoor.com/Job/united-arab-emirates-remote-data-analyst-jobs-SRCH_IL.0,20_IN6_KO21,41.htm",
        "avg_count": 150,
        "remote_ratio": 0.2
    },
    "Germany": {
        "base_url": "https://www.glassdoor.com/Job/germany-data-analyst-jobs-SRCH_IL.0,7_IN96_KO8,20.htm",
        "remote_url": "https://www.glassdoor.com/Job/germany-remote-data-analyst-jobs-SRCH_IL.0,7_IN96_KO8,28.htm",
        "avg_count": 450,
        "remote_ratio": 0.35
    }
}

# Check if running in GitHub Actions
is_github_actions = os.environ.get('GITHUB_ACTIONS') == 'true'


class GlassdoorScraper:
    """Scraper for Glassdoor job data using undetected-chromedriver."""
    
    def __init__(self):
        self.driver = None
    
    def initialize(self) -> None:
        """Initialize the browser."""
        logger.info("Initializing browser...")
        
        # Configure Chrome options
        options = uc.ChromeOptions()
        
        # Set options based on environment
        if is_github_actions:
            logger.info("Running in GitHub Actions environment")
            options.add_argument("--disable-gpu")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-setuid-sandbox")
            options.add_argument("--window-size=1920,1080")
            options.add_argument("--start-maximized")
            # For XVFB compatibility
            options.add_argument("--disable-extensions")
            options.add_argument("--disable-infobars")
        
        # Common options for all environments
        options.add_argument("--disable-notifications")
        options.add_argument("--disable-popup-blocking")
        options.add_argument("--lang=en-US")
        
        # Initialize undetected-chromedriver
        self.driver = uc.Chrome(options=options)
        self.driver.set_page_load_timeout(60)
        
        # Set window size
        self.driver.set_window_size(1920, 1080)
        
        logger.info("Browser initialized successfully")
    
    def close(self) -> None:
        """Close the browser."""
        if self.driver:
            self.driver.quit()
    
    def random_sleep(self, min_seconds=1, max_seconds=3):
        """Sleep for a random amount of time to appear more human-like."""
        time.sleep(random.uniform(min_seconds, max_seconds))
    
    def handle_cloudflare(self) -> bool:
        """
        Handle Cloudflare protection if detected.
        
        Returns:
            True if successfully bypassed, False otherwise
        """
        try:
            # Check for Cloudflare challenge
            if "Just a moment" in self.driver.title or "cloudflare" in self.driver.page_source.lower():
                logger.warning("Cloudflare challenge detected. Waiting for it to resolve...")
                
                # Wait longer for Cloudflare to clear automatically (undetected_chromedriver should handle this)
                for i in range(5):
                    logger.info(f"Waiting for Cloudflare challenge to resolve (attempt {i+1})...")
                    time.sleep(6)  # Wait 6 seconds between checks
                    if "Just a moment" not in self.driver.title:
                        logger.info("Successfully bypassed Cloudflare challenge!")
                        return True
                
                # If still on Cloudflare, try to find interactive elements
                try:
                    # Try to find checkbox or verification button
                    checkboxes = self.driver.find_elements(By.CSS_SELECTOR, 
                                                          "input[type='checkbox'], .recaptcha-checkbox")
                    for checkbox in checkboxes:
                        if checkbox.is_displayed():
                            checkbox.click()
                            logger.info("Clicked on checkbox")
                            time.sleep(5)
                    
                    # Try to find any button that might help bypass
                    buttons = self.driver.find_elements(By.TAG_NAME, "button")
                    for button in buttons:
                        if button.is_displayed() and ("verify" in button.text.lower() or 
                                                     "continue" in button.text.lower() or 
                                                     "human" in button.text.lower()):
                            button.click()
                            logger.info(f"Clicked button: {button.text}")
                            time.sleep(5)
                except Exception as e:
                    logger.warning(f"Error while trying to interact with Cloudflare elements: {str(e)}")
                
                # Final check
                if "Just a moment" not in self.driver.title:
                    logger.info("Successfully bypassed Cloudflare challenge!")
                    return True
                    
                logger.warning("Failed to bypass Cloudflare challenge.")
                return False
            
            return True  # No Cloudflare challenge detected
            
        except Exception as e:
            logger.error(f"Error handling Cloudflare challenge: {str(e)}")
            return False
    
    def extract_job_count(self) -> int:
        """Extract the job count from the page."""
        try:
            # Wait a bit for the page to fully load
            self.random_sleep(2, 4)
            
            # Check if we're facing Cloudflare challenge
            if not self.handle_cloudflare():
                return 0
                
            # Try multiple approaches to find the job count
            
            # 1. Look for specific selectors that typically contain job counts
            count_selectors = [
                '[data-test="jobCount"]', 
                '.jobsCount', 
                '.count',
                'header h1',
                '[data-heading]',
                '.hiddenJobs',
                '.jobHeader',
                '.jobsCount',
                '.css-rfi9y',  # Common Glassdoor class
                '.common__EIRcO',  # Another common Glassdoor class
                'h1', 
                'h2', 
                'span.text'
            ]
            
            for selector in count_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        if element.is_displayed():
                            text = element.text
                            # Look for patterns like "123 jobs" or "123 Data Analyst jobs"
                            if re.search(r'\d+\s+(?:Data Analyst\s+)?jobs', text, re.IGNORECASE):
                                count_str = re.sub(r'[^\d]', '', re.search(r'\d+', text).group())
                                return int(count_str)
                except Exception:
                    continue
            
            # 2. Try to extract from page title
            if "jobs" in self.driver.title.lower():
                title_numbers = re.findall(r'\d+', self.driver.title)
                if title_numbers:
                    return int(title_numbers[0])
            
            # 3. Extract from the entire page content
            page_text = self.driver.page_source
            job_count_patterns = [
                r'(\d+,?\d*)\s+(?:Data Analyst\s+)?jobs',
                r'(\d+,?\d*)\s+jobs\s+available',
                r'found\s+(\d+,?\d*)\s+jobs',
                r'showing\s+(\d+,?\d*)\s+jobs'
            ]
            
            for pattern in job_count_patterns:
                matches = re.search(pattern, page_text, re.IGNORECASE)
                if matches:
                    count_str = matches.group(1).replace(',', '')
                    return int(count_str)
            
            # 4. Take a screenshot for debugging in local development
            if not is_github_actions:
                self.driver.save_screenshot(f"debug_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
                
            # If we got here, no count was found
            logger.warning(f"Could not parse job count from the page with URL: {self.driver.current_url}")
            logger.warning(f"Page title: {self.driver.title}")
                
            return 0
        except Exception as e:
            logger.error(f"Error extracting job count: {str(e)}")
            return 0
    
    def scroll_page(self):
        """Scroll down the page to ensure all content is loaded."""
        try:
            # Get total height of page
            total_height = self.driver.execute_script("return document.body.scrollHeight")
            viewport_height = self.driver.execute_script("return window.innerHeight")
            
            if total_height <= viewport_height:
                return
                
            # Calculate number of steps (between 3 and 8)
            num_steps = min(8, max(3, int(total_height / viewport_height)))
            
            # Scroll in steps
            for i in range(num_steps):
                # Scroll down in chunks
                target_position = (i + 1) * (total_height / num_steps)
                self.driver.execute_script(f"window.scrollTo(0, {target_position})")
                self.random_sleep(0.5, 1.5)
            
            # Scroll back up a bit (human behavior)
            self.driver.execute_script("window.scrollBy(0, -300)")
            self.random_sleep(0.5, 1)
            
        except Exception as e:
            logger.warning(f"Error during page scrolling: {str(e)}")
    
    def handle_popups(self):
        """Handle common popups on Glassdoor."""
        try:
            # List of common popup selectors to close
            popup_selectors = [
                'button[aria-label="Close"]', 
                '.modal-close', 
                '.close',
                '[data-test="modal-close"]',
                '.ReactModal__Close',
                '.emailAlertPopup button',
                '.UserAlert button',
                'button.fc-button',
                '.fc-close',
                '#onetrust-accept-btn-handler',
                '.gdCookieConsentButton',
                '.modal button',
                'button.btn',
                '[aria-label="Close this dialog"]',
                '.closeIcon'
            ]
            
            for selector in popup_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        if element.is_displayed():
                            element.click()
                            logger.info(f"Closed popup with selector: {selector}")
                            self.random_sleep(0.5, 1.5)
                except Exception:
                    pass
            
            # Handle text-based buttons
            text_buttons = ["Accept", "Accept All", "Reject", "Skip", "Continue", 
                           "No Thanks", "Maybe Later", "Not Now", "I Accept"]
            
            for button_text in text_buttons:
                try:
                    xpath = f"//button[contains(text(),'{button_text}')]"
                    buttons = self.driver.find_elements(By.XPATH, xpath)
                    for button in buttons:
                        if button.is_displayed():
                            button.click()
                            logger.info(f"Clicked button with text: {button_text}")
                            self.random_sleep(0.5, 1.5)
                except Exception:
                    pass
                
        except Exception as e:
            logger.warning(f"Error handling popups: {str(e)}")
    
    def scrape_jobs_by_period(self, country: str, period_days: int) -> int:
        """
        Scrape job count for a specific country and time period.
        
        Args:
            country: Country name to search in
            period_days: Number of days to look back (1, 7, or 30)
            
        Returns:
            The number of jobs found or -1 if data cannot be found
        """
        logger.info(f"Scraping {JOB_TITLE} jobs in {country} for last {period_days} days")
        
        country_config = COUNTRY_CONFIGS.get(country)
        if not country_config:
            logger.error(f"No configuration found for country: {country}")
            return -1
        
        try:
            # Construct the URL with filters
            url = f"{country_config['base_url']}?fromAge={period_days}"
            
            # Navigate to the page
            logger.info(f"Navigating to: {url}")
            self.driver.get(url)
            
            # Wait for page to load
            self.random_sleep(3, 5)
            
            # Handle any popups
            self.handle_popups()
            
            # Wait a bit more
            self.random_sleep(1, 3)
            
            # Scroll to load all content
            self.scroll_page()
            
            # Extract the job count
            job_count = self.extract_job_count()
            
            # Check if we couldn't find data
            if job_count == 0 and ("Just a moment" in self.driver.title or "challenge" in self.driver.current_url):
                logger.warning(f"Could not retrieve data for {country} for last {period_days} days (Cloudflare challenge)")
                return -1
            
            logger.info(f"Found {job_count} jobs in {country} for last {period_days} days")
            return job_count
        
        except Exception as e:
            logger.error(f"Error scraping {country} for {period_days} days: {str(e)}")
            return -1
    
    def scrape_remote_vs_onsite(self, country: str) -> Dict[str, int]:
        """
        Scrape job counts for remote and on-site jobs.
        
        Args:
            country: Country name to search in
            
        Returns:
            Dictionary with remote and on-site job counts or -1 values if data cannot be found
        """
        logger.info(f"Scraping remote vs on-site {JOB_TITLE} jobs in {country}")
        
        country_config = COUNTRY_CONFIGS.get(country)
        if not country_config:
            logger.error(f"No configuration found for country: {country}")
            return {"remote": -1, "on_site": -1}
        
        results = {"remote": -1, "on_site": -1}
        
        try:
            # Use the remote URL from the config
            url = country_config['remote_url']
            
            logger.info(f"Navigating to remote jobs: {url}")
            self.driver.get(url)
            
            # Wait for page to load
            self.random_sleep(3, 5)
            
            # Handle any popups
            self.handle_popups()
            
            # Wait a bit more
            self.random_sleep(1, 3)
            
            # Scroll to load all content
            self.scroll_page()
            
            # Extract the job count
            remote_count = self.extract_job_count()
            
            # Check if we couldn't find data
            if remote_count == 0 and ("Just a moment" in self.driver.title or "challenge" in self.driver.current_url):
                logger.warning(f"Could not retrieve remote job data for {country} (Cloudflare challenge)")
                return {"remote": -1, "on_site": -1}
            
            logger.info(f"Found {remote_count} remote jobs in {country}")
            results["remote"] = remote_count
            
            # Get total jobs for on-site calculation
            total_jobs = self.scrape_jobs_by_period(country, 30)
            if total_jobs < 0:
                results["on_site"] = -1
            else:
                results["on_site"] = max(0, total_jobs - results["remote"])
            
            return results
            
        except Exception as e:
            logger.error(f"Error scraping remote jobs for {country}: {str(e)}")
            return {"remote": -1, "on_site": -1}
    
    def extract_skills_from_text(self, text: str) -> List[str]:
        """
        Extract relevant data analyst skills from a text (requirements or job description).
        
        Args:
            text: The text to extract skills from
            
        Returns:
            List of identified skills
        """
        # Technical skills for data analyst roles
        technical_skills = [
            "SQL", "Python", "R", "Excel", "Tableau", "Power BI", "SPSS", "SAS",
            "D3.js", "Java", "Scala", "MATLAB", "Hadoop", "Spark", "AWS", "Azure",
            "Google Cloud", "MongoDB", "PostgreSQL", "MySQL", "Oracle", "ETL",
            "Machine Learning", "Deep Learning", "AI", "Statistics", "Pandas",
            "NumPy", "Scikit-learn", "TensorFlow", "PyTorch", "Jupyter",
            "Data Visualization", "Data Modeling", "Business Intelligence",
            "Data Mining", "A/B Testing", "Data Warehousing", "Looker",
            "Snowflake", "Redshift", "BigQuery", "Alteryx", "SSRS", "SSIS",
            "DAX", "Power Query", "VBA", "Qlik", "Cognos", "Teradata",
            "Informatica", "DataOps", "MLOps", "PowerPoint", "Word", "Outlook",
            "SharePoint", "Teams", "Jira", "Confluence", "Git", "GitHub", "GitLab",
            "NoSQL", "Airflow", "dbt", "Data Quality", "JSON", "XML", "API",
            "REST", "SOAP", "Flask", "Django", "FastAPI", "Data Pipelines",
            "Google Analytics", "Power Platform", "Databricks", "Talend"
        ]
        
        # Education requirements
        education_requirements = [
            "Bachelor's Degree", "Master's Degree", "PhD", "MBA",
            "Bachelor", "Master", "Doctorate", "BSc", "MSc",
            "BS", "MS", "Computer Science", "Statistics", "Mathematics",
            "Information Technology", "Data Science", "Economics", "Business",
            "Engineering", "Quantitative Field", "Degree"
        ]
        
        # Soft skills and other qualifications
        soft_skills = [
            "Communication", "Teamwork", "Problem Solving", "Analytical Thinking",
            "Critical Thinking", "Attention to Detail", "Time Management",
            "Project Management", "Leadership", "Collaboration", "Presentation",
            "Storytelling", "Decision Making", "Self-motivated", "Adaptability",
            "Creativity", "Organization", "Multitasking", "Prioritization",
            "Verbal Communication", "Written Communication", "Customer Service",
            "Business Acumen", "Domain Knowledge", "Industry Experience",
            "Agile", "Scrum", "Stakeholder Management", "Requirements Gathering"
        ]
        
        # Combine all skills lists
        all_skills = technical_skills + education_requirements + soft_skills
        
        # Case-insensitive skill detection (whole words only)
        found_skills = []
        for skill in all_skills:
            # Using word boundary regex to find whole words
            pattern = r'\b' + re.escape(skill) + r'\b'
            if re.search(pattern, text, re.IGNORECASE):
                # Always add the skill with its original case
                found_skills.append(skill)
                
        # Special cases for education requirements with variations
        degree_patterns = [
            r"\b[Bb]achelor'?s?\s+[Dd]egree\b",
            r"\b[Bb][Ss][Cc]\b",
            r"\b[Mm]aster'?s?\s+[Dd]egree\b",
            r"\b[Mm][Ss][Cc]\b",
            r"\b[Pp][Hh][Dd]\b",
            r"\b[Dd]octoral\s+[Dd]egree\b",
            r"\b[Dd]egree\s+in\s+[A-Za-z\s]+\b"
        ]
        
        for pattern in degree_patterns:
            if re.search(pattern, text):
                match = re.search(pattern, text)
                if match and match.group(0) not in found_skills:
                    found_skills.append(match.group(0))
                    
        return found_skills

    def scrape_job_listings(self, country: str, days: int = 1) -> List[Dict[str, Any]]:
        """
        Scrape job listings for a specific country with the given time period.
        Focus on extracting skills from job descriptions without attempting to click cards.
        
        Args:
            country: Country name to search in
            days: Number of days to look back
            
        Returns:
            List of job listings with minimal data and skills
        """
        logger.info(f"Scraping job listings in {country} for the last {days} days")
        
        country_config = COUNTRY_CONFIGS.get(country)
        if not country_config:
            logger.error(f"No configuration found for country: {country}")
            return []
        
        job_listings = []
        
        try:
            # Construct the URL with filters for the last X days
            url = f"{country_config['base_url']}?fromAge={days}"
            
            # Navigate to the page
            logger.info(f"Navigating to: {url}")
            self.driver.get(url)
            
            # Wait for page to load
            self.random_sleep(3, 5)
            
            # Handle any popups
            self.handle_popups()
            
            # Wait a bit more and handle Cloudflare
            self.random_sleep(1, 3)
            if not self.handle_cloudflare():
                logger.warning(f"Could not bypass Cloudflare protection when scraping job listings for {country}")
                return []
            
            # Attempt to extract skills directly from the page without clicking
            # First, try to get job description from the current view
            job_listings_with_skills = self.extract_skills_from_page(country)
            
            # If we couldn't get skills from the page directly, try a new approach
            if not job_listings_with_skills:
                logger.info(f"Attempting to extract skills from job listings using alternative method")
                
                # Scroll gradually to load all content
                for _ in range(5):
                    self.driver.execute_script("window.scrollBy(0, 500)")
                    self.random_sleep(1, 2)
                
                # Alternative method: directly navigate to job detail pages
                job_listings_with_skills = self.extract_skills_using_direct_urls(country)
            
            logger.info(f"Successfully extracted skills from {len(job_listings_with_skills)} job listings for {country}")
            return job_listings_with_skills
            
        except Exception as e:
            logger.error(f"Error scraping job listings for {country}: {str(e)}")
            return []
    
    def extract_skills_from_page(self, country: str) -> List[Dict[str, Any]]:
        """
        Extract skills directly from job descriptions visible on the page.
        """
        job_listings = []
        job_count = 0
        
        try:
            # Updated selectors for the new Glassdoor UI
            job_card_selectors = [
                ".jobCard",
                ".JobCard",
                "[data-test='jobCard']",
                ".css-bkasv9",
                ".JobsList_jobListItem__8HcYA",
                ".JobsList_normJobListItem__eCZRH", 
                "[data-test='job-list-item']",
                "li[id^='job_']"
            ]
            
            # Try each selector to find job cards
            job_cards = []
            for selector in job_card_selectors:
                job_cards = self.driver.find_elements(By.CSS_SELECTOR, selector)
                if job_cards:
                    logger.info(f"Found {len(job_cards)} job cards using selector: {selector}")
                    break
            
            # Process job cards (limit to 20)
            for card in job_cards[:20]:
                try:
                    # Extract basic info with fallbacks
                    title = self.get_text_from_element(card, [
                        ".jobTitle", "[data-test='job-title']", ".heading_Heading__BqX5J",
                        "h2", "h3", "a[data-test='job-link']", ".JobCard_jobTitle__TrVlK"
                    ], "Data Analyst")
                    
                    company = self.get_text_from_element(card, [
                        ".company", "[data-test='employer-name']", 
                        ".EmployerProfile_employerNameHeading__bXBYr h4",
                        ".JobCard_companyName__lwjW4"
                    ], "Unknown Company")
                    
                    # Try to find job description without clicking
                    description = self.get_text_from_element(card, [
                        ".jobDescriptionContent", 
                        "[data-test='jobDescriptionText']",
                        ".JobDetails_jobDescription__uW_fK",
                        ".css-w3wpmi"
                    ], "")
                    
                    # If description not found in card, look for expanded details
                    if not description:
                        # Check if there's an expanded job detail section
                        detail_selectors = [
                            ".JobDetails_jobDescription__uW_fK",
                            "div[data-test='job-description']",
                            "[data-test='jobDescriptionText']",
                            ".jobDescriptionContent"
                        ]
                        
                        for selector in detail_selectors:
                            elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                            for element in elements:
                                if element.is_displayed() and element.text.strip():
                                    description = element.text.strip()
                                    break
                            
                            if description:
                                break
                    
                    # Get URL if available
                    job_url = ""
                    try:
                        links = card.find_elements(By.TAG_NAME, "a")
                        for link in links:
                            href = link.get_attribute("href")
                            if href and ("job-details" in href or "Job-View" in href or "/job/" in href):
                                job_url = href
                                break
                    except:
                        pass
                    
                    # Extract skills from the description
                    skills = []
                    if description:
                        skills = self.extract_skills_from_text(description)
                    
                    # If no description on page, create minimal job listing
                    if not skills and not description:
                        # Minimal job listing with just title and company
                        job_listing = {
                            "title": title,
                            "company": company,
                            "skills": [],
                            "link": job_url
                        }
                    else:
                        # Create job listing object with minimal data
                        job_listing = {
                            "title": title,
                            "company": company,
                            "skills": skills,
                            "link": job_url
                        }
                    
                    # Add to list if we found a title
                    if title and title != "Data Analyst" or skills:  # Only add if title is non-default or we found skills
                        job_listings.append(job_listing)
                        job_count += 1
                        logger.info(f"Successfully extracted data for {title} at {company} - Found {len(skills)} skills")
                    
                except Exception as e:
                    logger.warning(f"Error processing job card: {str(e)}")
            
            return job_listings
            
        except Exception as e:
            logger.warning(f"Error extracting skills from page: {str(e)}")
            return []
    
    def extract_skills_using_direct_urls(self, country: str) -> List[Dict[str, Any]]:
        """
        Alternative approach: Find job URLs and load each directly to extract skills.
        """
        job_listings = []
        
        try:
            # Try to find direct job links
            link_elements = self.driver.find_elements(By.CSS_SELECTOR, "a[href*='job-details'], a[href*='Job-View'], a[href*='/job/']")
            
            # Deduplicate links
            job_urls = []
            for link in link_elements:
                href = link.get_attribute("href")
                if href and href not in job_urls:
                    job_urls.append(href)
            
            logger.info(f"Found {len(job_urls)} unique job URLs")
            
            # Visit each URL directly (limit to 10)
            for i, url in enumerate(job_urls[:10]):
                try:
                    # Navigate to job details page
                    self.driver.get(url)
                    self.random_sleep(2, 3)
                    
                    # Handle popups
                    self.handle_popups()
                    
                    # Extract title
                    title = self.get_text_from_page([
                        "#jd-job-title", 
                        "h1.heading_Heading__BqX5J",
                        "[data-test='job-title']"
                    ], "Data Analyst")
                    
                    # Extract company
                    company = self.get_text_from_page([
                        ".EmployerProfile_employerNameHeading__bXBYr h4",
                        "[data-test='employer-name']"
                    ], "Unknown Company")
                    
                    # Extract job description
                    description = self.get_text_from_page([
                        ".JobDetails_jobDescription__uW_fK",
                        "[data-test='jobDescriptionText']",
                        ".jobDescriptionContent"
                    ], "")
                    
                    # Extract skills
                    skills = []
                    if description:
                        skills = self.extract_skills_from_text(description)
                    
                    # Create job listing with minimal info
                    job_listing = {
                        "title": title,
                        "company": company,
                        "skills": skills,
                        "link": url
                    }
                    
                    job_listings.append(job_listing)
                    logger.info(f"Successfully extracted skills for {title} at {company} - Found {len(skills)} skills")
                    
                except Exception as e:
                    logger.warning(f"Error processing job URL {url}: {str(e)}")
            
            return job_listings
            
        except Exception as e:
            logger.warning(f"Error in direct URL extraction: {str(e)}")
            return []
    
    def get_text_from_element(self, element, selectors, default=""):
        """Helper to try multiple selectors for getting text from an element."""
        for selector in selectors:
            try:
                elements = element.find_elements(By.CSS_SELECTOR, selector)
                for el in elements:
                    if el.is_displayed() and el.text.strip():
                        return el.text.strip()
            except:
                continue
        return default
    
    def get_text_from_page(self, selectors, default=""):
        """Helper to try multiple selectors for getting text from the page."""
        for selector in selectors:
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                for el in elements:
                    if el.is_displayed() and el.text.strip():
                        return el.text.strip()
            except:
                continue
        return default

    def scrape_country(self, country: str) -> Dict[str, Any]:
        """
        Scrape all job data for a specific country.
        
        Args:
            country: Country name to scrape
            
        Returns:
            Dictionary with all job data for the country
        """
        logger.info(f"Starting scrape for {country}")
        
        # Initialize country data with "Can't find data" indicator (-1)
        country_data = {
            "country": country,
            "last_24h": -1,
            "last_7d": -1,
            "last_30d": -1,
            "remote": -1,
            "on_site": -1,
            "job_listings": []
        }
        
        # Scrape job counts for different time periods
        for period_name, days in TIME_PERIODS.items():
            count = self.scrape_jobs_by_period(country, days)
            country_data[period_name] = count
        
        # Scrape remote vs on-site counts
        remote_onsite = self.scrape_remote_vs_onsite(country)
        country_data["remote"] = remote_onsite["remote"]
        country_data["on_site"] = remote_onsite["on_site"]
        
        # Scrape job listings for the last 24 hours
        job_listings = self.scrape_job_listings(country, days=1)
        country_data["job_listings"] = job_listings
        
        logger.info(f"Completed scrape for {country}: {country_data}")
        return country_data


def run_scraper() -> Dict[str, Any]:
    """
    Run the scraper for all countries.
    
    Returns:
        Dictionary with all job data
    """
    scraper = GlassdoorScraper()
    
    try:
        scraper.initialize()
        
        all_data = {"countries": {}}
        
        for country in COUNTRIES:
            logger.info(f"Processing country: {country}")
            country_data = scraper.scrape_country(country)
            all_data["countries"][country] = country_data
        
        # Add timestamp in UTC for consistency
        all_data["last_updated"] = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
        
        return all_data
    
    finally:
        scraper.close()


def save_data(data: Dict[str, Any], output_path: Path) -> None:
    """Save the scraped data to a JSON file."""
    logger.info(f"Saving data to {output_path}")
    
    # Create output directory if it doesn't exist
    os.makedirs(output_path.parent, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    
    logger.info(f"Data saved successfully to {output_path}")


def main():
    """Main entry point for the scraper."""
    logger.info("Starting Glassdoor Job Scraper")
    
    try:
        data = run_scraper()
        save_data(data, OUTPUT_FILE)
        logger.info("Scraping completed successfully")
    
    except Exception as e:
        logger.error(f"Error during scraping: {str(e)}", exc_info=True)


if __name__ == "__main__":
    main() 