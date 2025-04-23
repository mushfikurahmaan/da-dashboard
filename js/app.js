/**
 * Data Analyst Job Insights Dashboard
 * Main JavaScript file that loads and displays job data
 * Data refreshed daily at 5 AM Bangladesh time (GMT+6)
 */

// Global variables
let jobData = null;
let remoteOnsiteChart = null;
let countryComparisonChart = null;

// DOM elements
const countrySelector = document.getElementById('country-selector');
const lastUpdatedElement = document.getElementById('last-updated');
const jobs24hElement = document.getElementById('jobs-24h');
const jobs7dElement = document.getElementById('jobs-7d');
const jobs30dElement = document.getElementById('jobs-30d');
const jobListingsElement = document.getElementById('job-listings');

/**
 * Initialize the dashboard
 */
async function initDashboard() {
    try {
        // Fetch the data
        jobData = await fetchJobData();
        
        // Display the last updated timestamp
        updateTimestamp(jobData.last_updated);
        
        // Set up event listeners
        setupEventListeners();
        
        // Load data for the initially selected country
        const initialCountry = countrySelector.value;
        displayCountryData(initialCountry);
        
        // Initialize charts
        initializeCharts();
        
        // Update charts with data
        updateCharts(initialCountry);
        
    } catch (error) {
        console.error('Error initializing dashboard:', error);
        showError('Failed to load dashboard data. Please try again later.');
    }
}

/**
 * Fetch job data from the JSON file
 */
async function fetchJobData() {
    try {
        const response = await fetch('data/data.json');
        
        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error('Error fetching job data:', error);
        throw error;
    }
}

/**
 * Set up event listeners for interactive elements
 */
function setupEventListeners() {
    // Country selector change event
    countrySelector.addEventListener('change', (event) => {
        const selectedCountry = event.target.value;
        displayCountryData(selectedCountry);
        updateCharts(selectedCountry);
    });
}

/**
 * Display job data for the selected country
 */
function displayCountryData(countryName) {
    if (!jobData || !jobData.countries || !jobData.countries[countryName]) {
        showError(`No data available for ${countryName}`);
        return;
    }
    
    const countryData = jobData.countries[countryName];
    
    // Update summary cards
    jobs24hElement.textContent = countryData.last_24h;
    jobs7dElement.textContent = countryData.last_7d;
    jobs30dElement.textContent = countryData.last_30d;
    
    // Render job listings
    renderJobListings(countryData.job_listings);
}

/**
 * Render job listings for the selected country
 */
function renderJobListings(listings) {
    // Clear existing listings
    jobListingsElement.innerHTML = '';
    
    if (!listings || listings.length === 0) {
        jobListingsElement.innerHTML = '<div class="text-gray-500">No job listings available</div>';
        return;
    }
    
    // Filter to show only jobs from the last 24 hours
    const last24HoursJobs = listings.filter(job => job.posted_date.includes('1d') || job.posted_date.includes('0d') || 
                                               job.posted_date.includes('hours') || job.posted_date.includes('hour') || 
                                               job.posted_date.includes('just now'));
    
    if (last24HoursJobs.length === 0) {
        jobListingsElement.innerHTML = '<div class="text-gray-500">No job listings available from the last 24 hours</div>';
        return;
    }
    
    // Create job cards for each listing
    last24HoursJobs.forEach(job => {
        const jobCard = document.createElement('div');
        jobCard.className = 'job-card bg-white border border-gray-200 p-4 rounded-lg shadow-sm fade-in';
        
        // Check if the job is remote
        const isRemote = job.location.toLowerCase().includes('remote');
        
        // All jobs shown are recent (within last 24 hours)
        const isRecent = true;
        
        jobCard.innerHTML = `
            <div class="flex flex-col md:flex-row md:justify-between md:items-start mb-2">
                <div>
                    <h3 class="text-lg font-semibold text-gray-900">${job.title}</h3>
                    <p class="text-gray-700">${job.company}</p>
                </div>
                <div class="mt-2 md:mt-0 text-sm text-gray-500">${job.posted_date}</div>
            </div>
            
            <div class="mb-2">
                <p class="text-gray-600">${job.location}</p>
                ${job.salary !== 'N/A' ? `<p class="salary mt-1">${job.salary}</p>` : ''}
            </div>
            
            <div class="mb-3">
                ${isRemote ? '<span class="job-tag job-tag-remote">Remote</span>' : '<span class="job-tag job-tag-onsite">On-site</span>'}
                ${isRecent ? '<span class="job-tag job-tag-recent">Recent</span>' : ''}
            </div>
            
            <div class="mt-4">
                <h4 class="font-medium text-gray-900">Requirements:</h4>
                <p class="text-gray-600 text-sm mt-1">${job.requirements}</p>
            </div>
            
            <div class="mt-4">
                <h4 class="font-medium text-gray-900">Responsibilities:</h4>
                <p class="text-gray-600 text-sm mt-1">${job.responsibilities}</p>
            </div>
            
            <div class="mt-4">
                <a href="${job.link}" target="_blank" class="inline-block px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 transition-colors">
                    View Job
                </a>
            </div>
        `;
        
        jobListingsElement.appendChild(jobCard);
    });
}

/**
 * Initialize the charts
 */
function initializeCharts() {
    // Remote vs On-site chart
    const remoteOnsiteCtx = document.getElementById('remote-onsite-chart').getContext('2d');
    remoteOnsiteChart = new Chart(remoteOnsiteCtx, {
        type: 'pie',
        data: {
            labels: ['Remote', 'On-site'],
            datasets: [{
                data: [0, 0],
                backgroundColor: ['#818cf8', '#4f46e5'],
                borderColor: ['#ffffff', '#ffffff'],
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom'
                }
            }
        }
    });
    
    // Country comparison chart
    const countryComparisonCtx = document.getElementById('country-comparison-chart').getContext('2d');
    countryComparisonChart = new Chart(countryComparisonCtx, {
        type: 'bar',
        data: {
            labels: Object.keys(jobData.countries),
            datasets: [{
                label: 'Last 30 Days',
                data: Object.values(jobData.countries).map(country => country.last_30d),
                backgroundColor: '#818cf8'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Number of Jobs'
                    }
                }
            },
            plugins: {
                legend: {
                    display: false
                }
            }
        }
    });
}

/**
 * Update charts with new data
 */
function updateCharts(countryName) {
    if (!jobData || !jobData.countries || !jobData.countries[countryName]) {
        return;
    }
    
    const countryData = jobData.countries[countryName];
    
    // Update Remote vs On-site chart
    remoteOnsiteChart.data.datasets[0].data = [countryData.remote, countryData.on_site];
    remoteOnsiteChart.update();
    
    // The country comparison chart already has all countries, doesn't need to be updated
}

/**
 * Format and display the last updated timestamp
 */
function updateTimestamp(isoTimestamp) {
    if (!isoTimestamp) {
        lastUpdatedElement.textContent = 'Last updated: Unknown';
        return;
    }
    
    const date = new Date(isoTimestamp);
    const formattedDate = date.toLocaleString();
    lastUpdatedElement.textContent = `Last updated: ${formattedDate}`;
}

/**
 * Display an error message
 */
function showError(message) {
    console.error(message);
    // For now, just log to console, but could be enhanced to show an on-screen notification
}

// Initialize the dashboard when the page loads
document.addEventListener('DOMContentLoaded', initDashboard); 