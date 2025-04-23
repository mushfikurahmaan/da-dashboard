#!/usr/bin/env python3
"""
Test script for the job scraper
This script runs the scraper for a single country to test functionality
"""

import sys
from main import JobScraper, save_data
from pathlib import Path

def test_single_country(country_name):
    """Test the scraper with a single country."""
    print(f"Testing scraper with country: {country_name}")
    
    output_file = Path(__file__).parent.parent / "data" / "test_data.json"
    
    scraper = JobScraper()
    
    try:
        scraper.start()
        country_data = scraper.search_jobs(country_name)
        
        all_data = {
            "countries": {
                country_name: country_data
            }
        }
        
        save_data(all_data, output_file)
        print(f"Test data saved to {output_file}")
    
    except Exception as e:
        print(f"Error during test: {str(e)}")
    
    finally:
        scraper.stop()

if __name__ == "__main__":
    # Use the first command-line argument as the country name, or default to "Canada"
    country = sys.argv[1] if len(sys.argv) > 1 else "Canada"
    test_single_country(country) 