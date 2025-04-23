# Real-Time Job Insights Dashboard

A dashboard that provides real-time insights on Data Analyst job opportunities across multiple countries (Canada, Ireland, Portugal, UAE, and Germany).

## Features

- Job counts for the last 24 hours, 7 days, and 30 days
- Breakdown of remote vs. on-site positions
- Detailed job listings with responsibilities, requirements, and salary information
- Automated data collection every 12 hours via GitHub Actions

## Technologies Used

- **Backend**: Python with Playwright for web scraping
- **Frontend**: HTML, JavaScript, and Tailwind CSS
- **Deployment**: GitHub Pages
- **Automation**: GitHub Actions

## Project Structure

- `scraper/` - Python scripts for data collection
- `data/` - Contains the scraped job data in JSON format
- `index.html` - Main dashboard interface
- `js/` - JavaScript files for the frontend
- `css/` - Custom CSS (in addition to Tailwind)
- `.github/workflows/` - GitHub Actions workflow files

## Setup and Usage

1. Clone this repository
2. Install dependencies: `pip install -r scraper/requirements.txt`
3. Run the scraper manually: `python scraper/main.py`
4. Open `index.html` in your browser

For automatic updates, the GitHub Actions workflow will run the scraper every 12 hours and update the data. 