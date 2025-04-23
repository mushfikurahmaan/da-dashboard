#!/usr/bin/env python3
"""
Job Insights Dashboard Scraper
This script scrapes job data from Glassdoor for Data Analyst positions in 
Canada, Ireland, Portugal, UAE, and Germany.
"""

import os
import json
import time
import random
import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

from playwright.sync_api import sync_playwright, Page, Playwright
from fake_useragent import UserAgent
from tqdm import tqdm

# Constants
JOB_TITLE = "Data Analyst"
COUNTRIES = ["Canada", "Ireland", "Portugal", "United Arab Emirates", "Germany"]
COUNTRY_CODES = {
    "Canada": "ca",
    "Ireland": "ie",
    "Portugal": "pt",
    "United Arab Emirates": "ae",
    "Germany": "de"
}

# Glassdoor URLs
GLASSDOOR_BASE_URL = "https://www.glassdoor.com"
GLASSDOOR_SEARCH_URL = "https://www.glassdoor.com/Job/jobs.htm"


class JobScraper:
    """Scraper for job listings."""
    
    def __init__(self):
        """Initialize the scraper."""
        self.playwright = None
        self.browser = None
        self.page = None
        self.user_agent = UserAgent().random
    
    def start(self) -> None:
        """Start the browser and create a new page."""
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(headless=True)
        self.page = self.browser.new_page(
            user_agent=self.user_agent,
            viewport={"width": 1920, "height": 1080}
        )
        self.page.set_default_timeout(60000)  # 60 seconds timeout
    
    def stop(self) -> None:
        """Close the browser and stop playwright."""
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()
    
    def wait_random(self, min_seconds: float = 1.0, max_seconds: float = 3.0) -> None:
        """Wait a random amount of time."""
        time.sleep(random.uniform(min_seconds, max_seconds))
    
    def search_jobs(self, country: str) -> Dict[str, Any]:
        """
        Search for Data Analyst jobs in the specified country.
        
        Args:
            country: The country to search in.
            
        Returns:
            Dictionary with job data for the country.
        """
        print(f"Searching for {JOB_TITLE} jobs in {country}...")
        
        country_code = COUNTRY_CODES.get(country)
        url = f"{GLASSDOOR_SEARCH_URL}?sc.keyword={JOB_TITLE.replace(' ', '+')}&locT=N&locId=2"
        
        # Different URL structure for different countries
        if country_code:
            url = f"https://www.glassdoor.{country_code}/Job/{JOB_TITLE.replace(' ', '-')}-jobs-SRCH_KO0,13.htm"
        
        self.page.goto(url)
        self.wait_random(2.0, 4.0)
        
        # Handle cookie consent if it appears
        try:
            self.page.click('button[data-selector="accept-cookies"]', timeout=5000)
            self.wait_random()
        except:
            pass
        
        jobs_data = {
            "country": country,
            "last_24h": self._get_job_count("24 hours"),
            "last_7d": self._get_job_count("7 days"),
            "last_30d": self._get_job_count("30 days"),
            "remote": self._get_job_count("Remote"),
            "on_site": self._get_job_count("On-site"),
            "job_listings": self._get_job_listings(max_jobs=10)
        }
        
        return jobs_data
    
    def _get_job_count(self, filter_text: str) -> int:
        """Get the number of jobs for a specific filter."""
        try:
            # Try to click the filter first
            self.page.click(f'text="{filter_text}"', timeout=5000)
            self.wait_random()
            
            # Get the count from the results header
            count_text = self.page.text_content('div[data-test="jobCount"]')
            if count_text:
                # Extract only the number
                import re
                match = re.search(r'(\d+,?\d*)', count_text)
                if match:
                    return int(match.group(1).replace(',', ''))
            
            # Fallback: try to get the count from the filter itself
            filter_elem = self.page.query_selector(f'//span[contains(text(), "{filter_text}")]/following-sibling::span')
            if filter_elem:
                count_text = filter_elem.text_content()
                if count_text and count_text.strip() != '':
                    return int(count_text.strip().replace('(', '').replace(')', '').replace(',', ''))
            
            return 0
        except Exception as e:
            print(f"Error getting job count for {filter_text}: {str(e)}")
            return 0
    
    def _get_job_listings(self, max_jobs: int = 10) -> List[Dict[str, Any]]:
        """Get detailed information for job listings."""
        job_listings = []
        
        try:
            # Find all job cards on the page
            job_cards = self.page.query_selector_all('li.react-job-listing')
            
            for i, card in enumerate(job_cards[:max_jobs]):
                try:
                    # Click on the job card to view details
                    card.click()
                    self.wait_random(1.5, 3.0)
                    
                    # Extract job details
                    title_elem = self.page.query_selector('div[data-test="jobTitle"]')
                    company_elem = self.page.query_selector('div[data-test="employerName"]')
                    location_elem = self.page.query_selector('div[data-test="location"]')
                    salary_elem = self.page.query_selector('span[data-test="detailSalary"]')
                    date_elem = self.page.query_selector('div[data-test="job-age"]')
                    
                    # Job description sections
                    desc_elem = self.page.query_selector('div#JobDescriptionContainer')
                    
                    job_data = {
                        "title": title_elem.text_content().strip() if title_elem else "N/A",
                        "company": company_elem.text_content().strip() if company_elem else "N/A",
                        "location": location_elem.text_content().strip() if location_elem else "N/A",
                        "salary": salary_elem.text_content().strip() if salary_elem else "N/A",
                        "posted_date": date_elem.text_content().strip() if date_elem else "N/A",
                        "description": desc_elem.text_content().strip() if desc_elem else "N/A",
                        "link": self.page.url
                    }
                    
                    # Try to extract requirements and responsibilities
                    job_data["requirements"] = self._extract_section(desc_elem, ["requirements", "qualifications"])
                    job_data["responsibilities"] = self._extract_section(desc_elem, ["responsibilities", "duties"])
                    
                    job_listings.append(job_data)
                except Exception as e:
                    print(f"Error processing job {i+1}: {str(e)}")
        except Exception as e:
            print(f"Error getting job listings: {str(e)}")
        
        return job_listings
    
    def _extract_section(self, desc_elem, keywords: List[str]) -> str:
        """Extract a section from the job description based on keywords."""
        if not desc_elem:
            return "N/A"
        
        full_text = desc_elem.text_content()
        lines = full_text.split('\n')
        
        # Find sections that might contain our keywords
        section_text = []
        in_section = False
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Check if this line is a section header
            lower_line = line.lower()
            is_header = any(keyword in lower_line for keyword in keywords)
            
            if is_header:
                in_section = True
                continue
            
            # If we're in our target section, add the line
            if in_section:
                # Check if we've hit another section header (usually shorter lines with a colon)
                if len(line) < 50 and ':' in line and line[0].isupper():
                    break
                
                section_text.append(line)
        
        return '\n'.join(section_text) if section_text else "N/A"


def save_data(data: Dict[str, Any], output_path: str) -> None:
    """Save the scraped data to a JSON file."""
    # Create output directory if it doesn't exist
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Add timestamp
    data["last_updated"] = datetime.datetime.now().isoformat()
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)


def main():
    """Main entry point for the scraper."""
    output_file = Path(__file__).parent.parent / "data" / "data.json"
    
    scraper = JobScraper()
    
    try:
        scraper.start()
        
        all_data = {"countries": {}}
        
        for country in tqdm(COUNTRIES, desc="Scraping countries"):
            country_data = scraper.search_jobs(country)
            all_data["countries"][country] = country_data
        
        save_data(all_data, output_file)
        print(f"Data saved to {output_file}")
    
    except Exception as e:
        print(f"Error during scraping: {str(e)}")
    
    finally:
        scraper.stop()


if __name__ == "__main__":
    main() 