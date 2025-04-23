# Data Analyst Job Insights Dashboard

A real-time dashboard tracking Data Analyst job opportunities from Glassdoor across multiple countries.

## Features

- **Job Counts**: Track jobs posted in the last 24 hours, 7 days, and 30 days
- **Remote vs On-site**: Compare remote and on-site job opportunities 
- **Country Comparison**: Data from multiple countries (Canada, Ireland, Portugal, UAE, Germany)
- **Automated Updates**: Data refreshed every 12 hours via GitHub Actions

## How It Works

The dashboard uses a Playwright-based scraper to collect job count data from Glassdoor:

1. **Scraper**: Uses Playwright with stealth mode to navigate Glassdoor without being detected
2. **Data Collection**: Gathers counts of Data Analyst jobs based on:
   - Time period: Last 24h, 7d, and 30d
   - Job type: Remote vs on-site
   - Geography: Multiple countries
3. **Automation**: Scheduled to run every 12 hours via GitHub Actions
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