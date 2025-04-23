# Data Analyst Job Insights Dashboard

A real-time dashboard tracking Data Analyst job opportunities from Glassdoor across multiple countries.

## Features

- **Job Counts**: Track jobs posted in the last 24 hours, 7 days, and 30 days
- **Remote vs On-site**: Compare remote and on-site job opportunities 
- **Country Comparison**: Data from multiple countries (Canada, Ireland, Portugal, UAE, Germany)
- **Latest Job Listings**: View job listings posted in the last 24 hours only
- **Automated Updates**: Data refreshed daily at 5 AM Bangladesh time (GMT+6) via GitHub Actions

## How It Works

The dashboard uses a Playwright-based scraper to collect job count data from Glassdoor:

1. **Scraper**: Uses Playwright with stealth mode to navigate Glassdoor without being detected
2. **Data Collection**: Gathers counts of Data Analyst jobs based on:
   - Time period: Last 24h, 7d, and 30d
   - Job type: Remote vs on-site
   - Geography: Multiple countries
3. **Automation**: Scheduled to run daily at 5 AM Bangladesh time (GMT+6) via GitHub Actions
4. **Visualization**: Frontend dashboard built with HTML, CSS, and vanilla JavaScript

## Setting Up Locally

1. Clone this repository
2. Install dependencies:
   ```bash
   pip install -r scraper/requirements.txt
   python -m playwright install chromium
   ```
3. Run the scraper:
   ```bash
   python scraper/main.py
   ```
4. Open `index.html` in your browser to view the dashboard

## Adding More Countries

To add more countries to the dashboard:

1. Edit `scraper/main.py`:
   - Add your countries to the `COUNTRIES` list:
     ```python
     COUNTRIES = ["Canada", "Ireland", "Portugal", "United Arab Emirates", "Germany", "Your Country"]
     ```
   - Add country configuration to the `COUNTRY_CONFIGS` dictionary:
     ```python
     "Your Country": {
         "base_url": "https://www.glassdoor.com/Job/yourcountry-data-analyst-jobs-SRCH_...",
         "remote_url": "https://www.glassdoor.com/Job/yourcountry-remote-data-analyst-jobs-SRCH_...",
         "avg_count": 300,  # Approximate average job count
         "remote_ratio": 0.3  # Approximate remote job ratio
     }
     ```
   - To find the correct URLs, search for "Data Analyst" jobs in your country on Glassdoor and copy the URL

2. Edit `index.html` to add the country to the dropdown menu:
   ```html
   <select id="country-selector">
       <!-- Add your new country here -->
       <option value="Your Country">Your Country</option>
   </select>
   ```

3. Run the scraper to collect data for the new country:
   ```bash
   python scraper/main.py
   ```

## Adding More Fields to Scrape

To scrape additional fields or information:

1. Modify the `scrape_country` method in `scraper/main.py` to collect additional data:
   ```python
   def scrape_country(self, country: str) -> Dict[str, Any]:
       # Existing code...
       
       # Add your additional fields here
       country_data["your_new_field"] = your_scraping_function(country)
       
       return country_data
   ```

2. Create a new scraping function in the `GlassdoorScraper` class:
   ```python
   def your_scraping_function(self, country: str):
       # Your scraping logic here
       # Use self.driver to interact with the browser
       return result
   ```

3. Update the frontend files (`index.html` and `js/app.js`) to display the new data.

## Technology Stack

- **Frontend**: HTML5, CSS3, JavaScript, Chart.js, Tailwind CSS
- **Scraping**: Python, Playwright, playwright-stealth
- **Automation**: GitHub Actions
- **Data Storage**: JSON (stored in the repository)

## Contributing

Contributions are welcome! Here are some ways you can contribute:

- Add support for additional countries
- Improve scraper reliability
- Enhance dashboard visualizations
- Fix bugs or improve documentation

## Legal Note

This tool is for educational purposes only. Please ensure your scraping activities comply with Glassdoor's terms of service and robots.txt policy. Use at your own risk. 