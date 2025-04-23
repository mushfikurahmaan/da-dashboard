#!/usr/bin/env python3
"""
Glassdoor Job Scraper

Scrapes job count data from Glassdoor using Playwright with stealth mode.
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
import re  # Import re at the top level
from pathlib import Path
from typing import Dict, List, Any, Optional

from playwright.async_api import async_playwright, Browser, Page, TimeoutError
from playwright_stealth import stealth_async

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
        "remote_url": "https://www.glassdoor.com/Job/canada-remote-data-analyst-jobs-SRCH_IL.0,6_IN3_KO7,27.htm"
    },
    "Ireland": {
        "base_url": "https://www.glassdoor.com/Job/ireland-data-analyst-jobs-SRCH_IL.0,7_IN70_KO8,20.htm",
        "remote_url": "https://www.glassdoor.com/Job/ireland-remote-data-analyst-jobs-SRCH_IL.0,7_IN70_KO8,28.htm"
    },
    "Portugal": {
        "base_url": "https://www.glassdoor.com/Job/portugal-data-analyst-jobs-SRCH_IL.0,8_IN195_KO9,21.htm",
        "remote_url": "https://www.glassdoor.com/Job/portugal-remote-data-analyst-jobs-SRCH_IL.0,8_IN195_KO9,29.htm"
    },
    "United Arab Emirates": {
        "base_url": "https://www.glassdoor.com/Job/united-arab-emirates-data-analyst-jobs-SRCH_IL.0,20_IN6_KO21,33.htm",
        "remote_url": "https://www.glassdoor.com/Job/united-arab-emirates-remote-data-analyst-jobs-SRCH_IL.0,20_IN6_KO21,41.htm"
    },
    "Germany": {
        "base_url": "https://www.glassdoor.com/Job/germany-data-analyst-jobs-SRCH_IL.0,7_IN96_KO8,20.htm",
        "remote_url": "https://www.glassdoor.com/Job/germany-remote-data-analyst-jobs-SRCH_IL.0,7_IN96_KO8,28.htm"
    }
}

# Check if running in GitHub Actions
is_github_actions = os.environ.get('GITHUB_ACTIONS') == 'true'


class GlassdoorScraper:
    """Scraper for Glassdoor job data using Playwright."""
    
    def __init__(self):
        self.browser = None
        self.context = None
    
    async def initialize(self) -> None:
        """Initialize the browser."""
        logger.info("Initializing browser...")
        playwright_instance = await async_playwright().start()
        
        # Configure browser launch options based on environment
        launch_options = {
            # When running in GitHub Actions with xvfb, we can still use headful mode
            # Otherwise, use headful mode on local dev machines
            "headless": False,
            "args": [
                "--disable-dev-shm-usage",
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-blink-features=AutomationControlled"
            ]
        }
        
        # Extra arguments for CI environment
        if is_github_actions:
            logger.info("Running in GitHub Actions environment")
            launch_options["args"].extend([
                "--disable-gpu",
                "--disable-infobars",
                "--window-size=1280,800",
                "--start-maximized"
            ])
        
        self.browser = await playwright_instance.chromium.launch(**launch_options)
        
        # Create context with specific options to avoid detection
        self.context = await self.browser.new_context(
            viewport={"width": 1280, "height": 800},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36",
            has_touch=False,
            java_script_enabled=True,
            locale="en-US",
            timezone_id="America/New_York"
        )
    
    async def close(self) -> None:
        """Close the browser."""
        if self.browser:
            await self.browser.close()
    
    async def _setup_page(self) -> Page:
        """Create and set up a new page with stealth mode."""
        page = await self.context.new_page()
        await stealth_async(page)
        
        # Additional page configurations to avoid bot detection
        await page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => false
            });
        """)
        
        return page
    
    async def _extract_job_count(self, page: Page) -> Optional[int]:
        """Extract the job count from the page."""
        try:
            # Try multiple approaches to find the job count
            
            # 1. First try to get the HTML content and use regex
            content = await page.content()
            # Look for patterns like "1,234 jobs" or "1,234 Data Analyst jobs"
            count_matches = re.findall(r'[\d,]+\s+(?:Data Analyst\s+)?jobs', content, re.IGNORECASE)
            if count_matches:
                # Extract just the number from the match
                count_str = re.sub(r'[^\d]', '', count_matches[0])
                if count_str:
                    return int(count_str)
            
            # 2. Try to find specific elements with the count
            selectors = [
                '[data-test="jobCount"]', 
                '.jobsCount', 
                '.count', 
                'header h1',
                '.job-search-key-1mn3ow8',  # Common Glassdoor class for job count
                '.heading5',
                'h1'
            ]
            
            for selector in selectors:
                elements = await page.query_selector_all(selector)
                for element in elements:
                    try:
                        text = await element.inner_text()
                        # Look for numbers in the text
                        numbers = re.findall(r'\d+,?\d*', text)
                        if numbers:
                            count_str = numbers[0].replace(',', '')
                            return int(count_str)
                    except Exception:
                        continue
            
            # 3. Extract from page title as last resort
            title = await page.title()
            numbers = re.findall(r'\d+,?\d*', title)
            if numbers:
                count_str = numbers[0].replace(',', '')
                return int(count_str)
            
            # 4. Take a screenshot for debugging in local development
            if not is_github_actions:
                await page.screenshot(path=f"debug_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
                
            # If we got here, no count was found
            logger.warning(f"Could not parse job count from the page with URL: {page.url}")
            # Try to log the page title for debugging
            try:
                logger.warning(f"Page title: {await page.title()}")
            except:
                pass
                
            return 0
        except Exception as e:
            logger.error(f"Error extracting job count: {str(e)}")
            return 0
    
    async def _scroll_page(self, page: Page) -> None:
        """Scroll down the page to ensure all content is loaded."""
        await page.evaluate("""
            () => {
                window.scrollTo(0, document.body.scrollHeight / 2);
            }
        """)
        await asyncio.sleep(1)
        await page.evaluate("""
            () => {
                window.scrollTo(0, document.body.scrollHeight);
            }
        """)
        await asyncio.sleep(1)
    
    async def _handle_popups(self, page: Page) -> None:
        """Handle common popups and overlays on Glassdoor."""
        try:
            # Try various selectors for close buttons on modals
            selectors = [
                'button[aria-label="Close"]', 
                '.modal-close', 
                '.close',
                '[data-test="modal-close"]',
                '.ReactModal__Close',
                '.emailAlertPopup button',
                '.UserAlert button',
                'button:has-text("Close")',
                'button:has-text("Accept")',
                'button:has-text("Accept All")',
                'button:has-text("Reject")'
            ]
            
            for selector in selectors:
                buttons = await page.query_selector_all(selector)
                for button in buttons:
                    try:
                        await button.click()
                        await asyncio.sleep(0.5)
                    except:
                        pass
            
            # Sometimes there's a sign-in prompt or cookie dialog
            try:
                buttons = await page.query_selector_all('button:has-text("Skip"), button:has-text("Continue"), button:has-text("Accept"), button:has-text("No Thanks")')
                for button in buttons:
                    try:
                        await button.click()
                        await asyncio.sleep(0.5)
                    except:
                        pass
            except Exception:
                pass
                
        except Exception as e:
            logger.warning(f"Error handling popups: {str(e)}")
    
    async def scrape_jobs_by_period(self, country: str, period_days: int) -> int:
        """
        Scrape job count for a specific country and time period.
        
        Args:
            country: Country name to search in
            period_days: Number of days to look back (1, 7, or 30)
            
        Returns:
            The number of jobs found
        """
        logger.info(f"Scraping {JOB_TITLE} jobs in {country} for last {period_days} days")
        
        country_config = COUNTRY_CONFIGS.get(country)
        if not country_config:
            logger.error(f"No configuration found for country: {country}")
            return 0
        
        page = await self._setup_page()
        
        try:
            # Construct the URL with filters
            url = f"{country_config['base_url']}?fromAge={period_days}"
            
            # Navigate to the page
            logger.info(f"Navigating to: {url}")
            await page.goto(url, wait_until="domcontentloaded", timeout=60000)
            
            # Wait for the page to load and handle potential overlays/modals
            await asyncio.sleep(3)
            
            # Handle any popups
            await self._handle_popups(page)
            
            # Wait a bit more for the page to fully load
            await asyncio.sleep(2)
            
            # Scroll to load all content
            await self._scroll_page(page)
            
            # Extract the job count
            job_count = await self._extract_job_count(page)
            logger.info(f"Found {job_count} jobs in {country} for last {period_days} days")
            
            return job_count
        
        except Exception as e:
            logger.error(f"Error scraping {country} for {period_days} days: {str(e)}")
            return 0
        
        finally:
            await page.close()
    
    async def scrape_remote_vs_onsite(self, country: str) -> Dict[str, int]:
        """
        Scrape job counts for remote and on-site jobs.
        
        Args:
            country: Country name to search in
            
        Returns:
            Dictionary with remote and on-site job counts
        """
        logger.info(f"Scraping remote vs on-site {JOB_TITLE} jobs in {country}")
        
        country_config = COUNTRY_CONFIGS.get(country)
        if not country_config:
            logger.error(f"No configuration found for country: {country}")
            return {"remote": 0, "on_site": 0}
        
        results = {"remote": 0, "on_site": 0}
        
        # Scrape remote jobs
        page = await self._setup_page()
        try:
            # Use the remote URL from the config
            url = country_config['remote_url']
            
            logger.info(f"Navigating to remote jobs: {url}")
            await page.goto(url, wait_until="domcontentloaded", timeout=60000)
            await asyncio.sleep(3)
            
            # Handle any popups
            await self._handle_popups(page)
            
            # Wait a bit more for the page to fully load
            await asyncio.sleep(2)
            
            # Scroll to load all content
            await self._scroll_page(page)
            
            # Extract the job count
            remote_count = await self._extract_job_count(page)
            logger.info(f"Found {remote_count} remote jobs in {country}")
            results["remote"] = remote_count
            
        except Exception as e:
            logger.error(f"Error scraping remote jobs for {country}: {str(e)}")
        finally:
            await page.close()
        
        # Calculate on-site jobs (total - remote)
        # We'll get total jobs for the last 30 days first
        total_jobs = await self.scrape_jobs_by_period(country, 30)
        results["on_site"] = max(0, total_jobs - results["remote"])
        
        return results
    
    async def scrape_country(self, country: str) -> Dict[str, Any]:
        """
        Scrape all job data for a specific country.
        
        Args:
            country: Country name to scrape
            
        Returns:
            Dictionary with all job data for the country
        """
        logger.info(f"Starting scrape for {country}")
        
        # Initialize country data
        country_data = {
            "country": country,
            "last_24h": 0,
            "last_7d": 0,
            "last_30d": 0,
            "remote": 0,
            "on_site": 0,
            "job_listings": []
        }
        
        # Scrape job counts for different time periods
        for period_name, days in TIME_PERIODS.items():
            count = await self.scrape_jobs_by_period(country, days)
            country_data[period_name] = count
        
        # Scrape remote vs on-site counts
        remote_onsite = await self.scrape_remote_vs_onsite(country)
        country_data["remote"] = remote_onsite["remote"]
        country_data["on_site"] = remote_onsite["on_site"]
        
        logger.info(f"Completed scrape for {country}: {country_data}")
        return country_data


async def run_scraper() -> Dict[str, Any]:
    """
    Run the scraper for all countries.
    
    Returns:
        Dictionary with all job data
    """
    scraper = GlassdoorScraper()
    
    try:
        await scraper.initialize()
        
        all_data = {"countries": {}}
        
        for country in COUNTRIES:
            logger.info(f"Processing country: {country}")
            country_data = await scraper.scrape_country(country)
            all_data["countries"][country] = country_data
        
        # Add timestamp in UTC for consistency
        all_data["last_updated"] = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
        
        return all_data
    
    finally:
        await scraper.close()


def save_data(data: Dict[str, Any], output_path: Path) -> None:
    """Save the scraped data to a JSON file."""
    logger.info(f"Saving data to {output_path}")
    
    # Create output directory if it doesn't exist
    os.makedirs(output_path.parent, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    
    logger.info(f"Data saved successfully to {output_path}")


async def main():
    """Main entry point for the scraper."""
    logger.info("Starting Glassdoor Job Scraper")
    
    try:
        data = await run_scraper()
        save_data(data, OUTPUT_FILE)
        logger.info("Scraping completed successfully")
    
    except Exception as e:
        logger.error(f"Error during scraping: {str(e)}", exc_info=True)


if __name__ == "__main__":
    asyncio.run(main()) 