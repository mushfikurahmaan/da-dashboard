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
const skillsContainerElement = document.getElementById('skills-container');

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
    
    // Update summary cards with appropriate text based on value
    jobs24hElement.textContent = countryData.last_24h === -1 ? "Can't find data" : countryData.last_24h;
    jobs7dElement.textContent = countryData.last_7d === -1 ? "Can't find data" : countryData.last_7d;
    jobs30dElement.textContent = countryData.last_30d === -1 ? "Can't find data" : countryData.last_30d;
    
    // Display skills from job listings
    displaySkills(countryData.job_listings);
}

/**
 * Display skills from job listings, sorted by frequency
 */
function displaySkills(listings) {
    // Clear existing skills
    skillsContainerElement.innerHTML = '';
    
    if (!listings || listings.length === 0) {
        skillsContainerElement.innerHTML = '<div class="text-gray-500">No skills data available</div>';
        return;
    }
    
    // Collect all skills from job listings
    const skillsCount = {};
    
    listings.forEach(job => {
        if (job.skills && Array.isArray(job.skills) && job.skills.length > 0) {
            job.skills.forEach(skill => {
                if (skill) {
                    skillsCount[skill] = (skillsCount[skill] || 0) + 1;
                }
            });
        }
    });
    
    // Convert to array for sorting
    const sortedSkills = Object.entries(skillsCount)
        .sort((a, b) => b[1] - a[1]) // Sort by count in descending order
        .map(([skill, count]) => ({ skill, count }));
    
    if (sortedSkills.length === 0) {
        skillsContainerElement.innerHTML = '<div class="text-gray-500">No skills data available</div>';
        return;
    }
    
    // Create a container for organized skills
    const skillsContainer = document.createElement('div');
    skillsContainer.className = 'w-full';
    
    // Define skill categories
    const technicalSkills = [
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
        "REST", "SOAP", "Flask", "Django", "FastAPI"
    ];
    
    const educationSkills = [
        "Bachelor's Degree", "Master's Degree", "PhD", "MBA",
        "Bachelor", "Master", "Doctorate", "BSc", "MSc",
        "BS", "MS", "Computer Science", "Statistics", "Mathematics",
        "Information Technology", "Data Science", "Economics", "Business",
        "Engineering", "Quantitative Field", "Degree"
    ];
    
    // Filter skills by category
    const technicalSkillsFound = sortedSkills.filter(item => 
        technicalSkills.includes(item.skill)
    );
    
    const educationSkillsFound = sortedSkills.filter(item => 
        educationSkills.includes(item.skill) || 
        /degree|bachelor|master|phd|msc|bsc/i.test(item.skill)
    );
    
    const softSkillsFound = sortedSkills.filter(item => 
        !technicalSkills.includes(item.skill) && 
        !educationSkills.includes(item.skill) && 
        !/degree|bachelor|master|phd|msc|bsc/i.test(item.skill)
    );
    
    // Function to create a skill category section
    function createSkillSection(title, skills, colorClass) {
        if (skills.length === 0) return '';
        
        const section = document.createElement('div');
        section.className = 'mb-6';
        
        const heading = document.createElement('h3');
        heading.className = 'font-medium text-gray-800 mb-3';
        heading.textContent = title;
        section.appendChild(heading);
        
        const skillsWrapper = document.createElement('div');
        skillsWrapper.className = 'flex flex-wrap gap-2';
        
        skills.forEach(({ skill, count }) => {
            const skillTag = document.createElement('div');
            skillTag.className = `skill-tag px-3 py-2 ${colorClass} rounded-lg text-sm font-medium`;
            skillTag.innerHTML = `
                <span>${skill}</span>
                <span class="ml-2 px-2 py-1 bg-opacity-50 rounded-full text-xs">${count}</span>
            `;
            skillsWrapper.appendChild(skillTag);
        });
        
        section.appendChild(skillsWrapper);
        return section;
    }
    
    // Add sections to container
    skillsContainer.appendChild(
        createSkillSection('Technical Skills', technicalSkillsFound, 'bg-blue-100 text-blue-800')
    );
    
    skillsContainer.appendChild(
        createSkillSection('Education Requirements', educationSkillsFound, 'bg-purple-100 text-purple-800')
    );
    
    skillsContainer.appendChild(
        createSkillSection('Other Skills & Qualifications', softSkillsFound, 'bg-green-100 text-green-800')
    );
    
    // Add the container to the DOM
    skillsContainerElement.appendChild(skillsContainer);
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
    
    // Process data for country comparison, replacing -1 with null for better visualization
    const countryLabels = Object.keys(jobData.countries);
    const countryData = Object.values(jobData.countries).map(country => {
        return country.last_30d === -1 ? null : country.last_30d;
    });
    
    // Check if all values are null/can't find data
    const allDataMissing = countryData.every(value => value === null);
    
    countryComparisonChart = new Chart(countryComparisonCtx, {
        type: 'bar',
        data: {
            labels: countryLabels,
            datasets: [{
                label: 'Last 30 Days',
                data: countryData,
                backgroundColor: '#818cf8'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: {
                    ticks: {
                        autoSkip: false,
                        maxRotation: 0,
                        minRotation: 0
                    }
                },
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
                },
                title: {
                    display: allDataMissing,
                    text: "Can't find data",
                    color: '#888',
                    font: {
                        size: 14
                    }
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
    // If data can't be found, show empty chart
    if (countryData.remote === -1 || countryData.on_site === -1) {
        remoteOnsiteChart.data.datasets[0].data = [0, 0];
        // Add a note to the chart
        remoteOnsiteChart.options.plugins.title = {
            display: true,
            text: "Can't find data",
            color: '#888',
            font: {
                size: 14
            }
        };
    } else {
        remoteOnsiteChart.data.datasets[0].data = [countryData.remote, countryData.on_site];
        // Remove the note
        remoteOnsiteChart.options.plugins.title = {
            display: false
        };
    }
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