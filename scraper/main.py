#!/usr/bin/env python3
"""
Job Insights Dashboard Scraper
This script generates sample job data for Data Analyst positions in 
Canada, Ireland, Portugal, UAE, and Germany.
"""

import os
import json
import random
import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
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


class JobDataGenerator:
    """Generator for job data."""
    
    def generate_data(self, country: str) -> Dict[str, Any]:
        """
        Generate sample data for Data Analyst jobs in the specified country.
        
        Args:
            country: The country to generate data for.
            
        Returns:
            Dictionary with job data for the country.
        """
        print(f"Generating sample data for {JOB_TITLE} jobs in {country}...")
        
        # Create realistic sample data based on the country
        if country == "Canada":
            job_count = random.randint(40, 60)
            remote_ratio = 0.3
        elif country == "Ireland":
            job_count = random.randint(10, 20)
            remote_ratio = 0.5
        elif country == "Portugal":
            job_count = random.randint(5, 15)
            remote_ratio = 0.6
        elif country == "United Arab Emirates":
            job_count = random.randint(8, 25)
            remote_ratio = 0.15
        elif country == "Germany":
            job_count = random.randint(30, 70)
            remote_ratio = 0.4
        else:
            job_count = random.randint(20, 40)
            remote_ratio = 0.35
        
        last_24h = int(job_count * 0.1)
        last_7d = int(job_count * 0.3)
        last_30d = job_count
        
        remote_count = int(job_count * remote_ratio)
        onsite_count = job_count - remote_count
        
        # Sample job listings data
        sample_job_listings = self._generate_sample_job_listings(country, 5)
        
        return {
            "country": country,
            "last_24h": last_24h,
            "last_7d": last_7d,
            "last_30d": last_30d,
            "remote": remote_count,
            "on_site": onsite_count,
            "job_listings": sample_job_listings
        }
    
    def _generate_sample_job_listings(self, country: str, count: int = 5) -> List[Dict[str, Any]]:
        """Generate sample job listings for a given country."""
        job_listings = []
        
        companies = {
            "Canada": ["TD Bank", "Shopify", "RBC", "CIBC", "Bell Canada", "Rogers", "Air Canada"],
            "Ireland": ["Google Dublin", "Facebook Ireland", "Accenture Ireland", "Microsoft Ireland", "Salesforce Dublin"],
            "Portugal": ["Farfetch", "Feedzai", "OutSystems", "Talkdesk", "Unbabel", "Volkswagen Digital Solutions"],
            "United Arab Emirates": ["Emirates Group", "Etihad Airways", "Dubai Holding", "ADNOC", "Emaar Properties"],
            "Germany": ["SAP", "Siemens", "Deutsche Bank", "Bosch", "Allianz", "BMW Group", "Volkswagen"]
        }
        
        locations = {
            "Canada": ["Toronto, ON", "Vancouver, BC", "Montreal, QC", "Calgary, AB", "Ottawa, ON"],
            "Ireland": ["Dublin", "Cork", "Galway", "Limerick", "Waterford"],
            "Portugal": ["Lisbon", "Porto", "Braga", "Coimbra", "Aveiro"],
            "United Arab Emirates": ["Dubai", "Abu Dhabi", "Sharjah", "Ajman", "Ras Al Khaimah"],
            "Germany": ["Berlin", "Munich", "Frankfurt", "Hamburg", "Cologne", "Stuttgart"]
        }
        
        currencies = {
            "Canada": {"symbol": "CAD", "min": 65000, "max": 110000, "period": "a year"},
            "Ireland": {"symbol": "€", "min": 45000, "max": 75000, "period": "a year"},
            "Portugal": {"symbol": "€", "min": 25000, "max": 50000, "period": "a year"},
            "United Arab Emirates": {"symbol": "AED", "min": 12000, "max": 25000, "period": "a month"},
            "Germany": {"symbol": "€", "min": 50000, "max": 80000, "period": "a year"}
        }
        
        job_titles = [
            "Data Analyst", 
            "Business Intelligence Analyst", 
            "Data Analyst - Finance", 
            "Marketing Data Analyst", 
            "Senior Data Analyst",
            "BI Developer",
            "Junior Data Analyst",
            "Data Analyst Specialist"
        ]
        
        for i in range(count):
            # Pick random values
            company = random.choice(companies.get(country, companies["Canada"]))
            location = random.choice(locations.get(country, locations["Canada"]))
            is_remote = random.random() < 0.4
            if is_remote:
                location += " (Remote)"
            
            title = random.choice(job_titles)
            
            # Generate random salary
            currency_info = currencies.get(country, currencies["Canada"])
            salary_min = currency_info["min"]
            salary_max = currency_info["max"]
            salary = f"{currency_info['symbol']}{salary_min:,} - {currency_info['symbol']}{salary_max:,} {currency_info['period']}"
            
            # Generate random posting date
            days = random.randint(1, 14)
            posted_date = f"{days}d ago"
            
            # Create job listing
            job_listing = {
                "title": title,
                "company": company,
                "location": location,
                "salary": salary,
                "posted_date": posted_date,
                "description": f"We are looking for a skilled {title} to join our team...",
                "requirements": "Bachelor's degree in a relevant field. Experience with SQL, Excel, and data visualization tools. Strong analytical skills and attention to detail.",
                "responsibilities": "Analyze business data to identify trends and insights. Create dashboards and reports. Collaborate with stakeholders to support business decisions.",
                "link": f"https://www.glassdoor.com/job-listing/example-{i}"
            }
            
            job_listings.append(job_listing)
        
        return job_listings


def save_data(data: Dict[str, Any], output_path: str) -> None:
    """Save the generated data to a JSON file."""
    # Create output directory if it doesn't exist
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Add timestamp
    data["last_updated"] = datetime.datetime.now().isoformat()
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)


def main():
    """Main entry point for the data generator."""
    output_file = Path(__file__).parent.parent / "data" / "data.json"
    
    generator = JobDataGenerator()
    
    try:
        all_data = {"countries": {}}
        
        for country in tqdm(COUNTRIES, desc="Generating data for countries"):
            country_data = generator.generate_data(country)
            all_data["countries"][country] = country_data
        
        save_data(all_data, output_file)
        print(f"Data saved to {output_file}")
    
    except Exception as e:
        print(f"Error during data generation: {str(e)}")


if __name__ == "__main__":
    main() 