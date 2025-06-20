# Job Matcher 🎯

**AI-Powered Job Matching System with LinkedIn, SEEK & Glassdoor Integration**

An intelligent job search automation tool that fetches job listings from multiple sources, matches them against your resume using AI, and enriches the results with company insights from Glassdoor.

<img width="1330" alt="obraz" src="https://github.com/user-attachments/assets/3f7e5176-8df4-4d6a-b553-dcf6f5fc5afb" />

## ✨ Features

- **Multi-Platform Job Fetching**: Automatically scrapes jobs from LinkedIn and SEEK
- **AI-Powered Resume Matching**: Uses Google's Gemini API to match jobs against your CV
- **Company Intelligence**: Enriches job data with Glassdoor ratings and reviews
- **Smart Filtering**: Filters jobs by rating, contract type, and custom exclusions
- **Duplicate Detection**: Prevents duplicate jobs across different platforms
- **Concurrent Processing**: Multi-threaded job processing for faster results
- **Web Interface**: Node.js frontend for easy job browsing

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- Node.js (for frontend)
- API Keys (see Environment Setup)

### Installation

1. **Clone and setup the project structure**:
   ```bash
   python setup_project.py
   ```

2. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Install Node.js dependencies** (for frontend):
   ```bash
   npm install
   ```

### Environment Setup

Create a `.env` file in the root directory with your API keys:

```env
# Google API Key (for Gemini AI job matching)
GOOGLE_API_KEY=your_google_api_key_here

# Google Custom Search Engine credentials (for Glassdoor company insights)
GOOGLE_CSE_ID=your_custom_search_engine_id
GOOGLE_CSE_KEY=your_google_cse_api_key
```

## 🎯 Usage

### Job Screening (Backend)

Run the main job matching pipeline:

```bash
python main.py --resume CV.pdf
```

**Command Line Options:**

| Option | Description | Default |
|--------|-------------|---------|
| `--resume` | Path to your resume PDF (required) | - |
| `--keywords` | Job keywords, comma separated | "Frontend developer, UI/UX Developer, Web Designer" |
| `--location` | Job location | "Sydney" |
| `--limit` | Max jobs per source | 50 |
| `--output` | Output CSV filename | "public/job_matches.csv" |

**Example:**
```bash
python main.py --resume my_resume.pdf --keywords "Frontend developer, Javascript developer" --location "Melbourne" --limit 100
```

### Web Interface (Frontend)

Start the web server to browse results:

```bash
node server.js
```

Then open your browser to view the job matches in a user-friendly interface.

## 📁 Project Structure

```
job_matcher/
├── main.py                    # Main application orchestrator
├── setup_project.py           # Project structure setup
├── server.js                  # Node.js frontend server
├── requirements.txt           # Python dependencies
├── .env                       # Environment variables (create this)
├── fetch_jobs/               # Job fetching modules
│   ├── __init__.py
│   ├── linkedin_jobs.py      # LinkedIn job scraper
│   └── seek_jobs.py          # SEEK job scraper
├── match_resume/             # Resume matching modules
│   ├── __init__.py
│   ├── parse_resume.py       # PDF resume parser
│   └── gemini_matcher.py     # AI job matching
├── enrich_data/              # Data enrichment modules
│   ├── __init__.py
│   └── glassdoor_cse.py      # Glassdoor company insights
├── public/                   # Output directory
│   └── job_matches.csv       # Generated job matches
└── sample/                   # Sample data directory
```

## 🔧 How It Works

### 1. **Job Fetching**
- Searches LinkedIn and SEEK simultaneously
- Handles multi-word search phrases with proper quoting
- Filters by date (last 3 days by default)
- Removes duplicates across platforms

### 2. **AI Matching**
- Parses your resume using PDF extraction
- Uses Google's Gemini AI to analyze job descriptions
- Scores jobs based on skills, experience, and requirements
- Provides detailed match reasoning

### 3. **Company Enrichment**
- Fetches company ratings from Glassdoor
- Adds review insights and culture information
- Filters out low-rated companies (below 3.9 stars)

### 4. **Smart Filtering**
- Excludes contract positions (configurable)
- Filters by minimum match score (75% by default)
- Removes duplicate job titles from same companies
- Custom keyword and company exclusions

### 5. **Results Output**
- Saves to CSV with comprehensive job data
- Appends new jobs to existing results
- Ranks by match score and company rating
- Displays top 10 matches in terminal

## 🎛️ Configuration

### Custom Filtering

Edit the filtering logic in `main.py`:

```python
# Exclude specific keywords in job titles
exclude_keywords = ["intern", "junior"]

# Exclude specific companies
exclude_companies = ["company_to_avoid"]

# Minimum company rating (0 to disable)
minimum_rating = 3.9

# Minimum match score threshold
minimum_match_score = 75
```

### Search Customization

Modify search parameters:

```python
# LinkedIn exact phrase matching
processed_linkedin_keywords = [f'"{kw}"' if ' ' in kw else kw for kw in keywords_list]

# Job age filter (days)
days_ago = 3
max_days_old = 3
```

## 📊 Output Format

The system generates a CSV file with these columns:

- `job_id` - Unique identifier
- `title` - Job title
- `company` - Company name
- `location` - Job location
- `job_url` - Direct link to job posting
- `match_score` - AI matching score (0-100)
- `rating` - Glassdoor company rating
- `match_reason` - AI explanation of the match
- `skill_matches` - Skills that align with your resume
- `skill_gaps` - Missing skills to highlight
- `employment_type` - Full-time, Contract, etc.
- `seniority` - Experience level required

## 🚨 Troubleshooting

### Common Issues

1. **No jobs found**: Check your keywords and try broader terms
2. **API rate limits**: The system includes delays between requests
3. **Missing environment variables**: Ensure your `.env` file is properly configured
4. **PDF parsing errors**: Make sure your resume is a readable PDF

### Debug Mode

Add debug prints to see what's happening:

```python
print(f"Searching for: {keywords_list}")
print(f"Total jobs before filtering: {len(all_jobs)}")
```

## 🔑 API Keys Setup

### Google API Key (for Gemini AI)
1. Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create a new API key for Gemini
3. Add to `.env` as `GOOGLE_API_KEY`

### Google Custom Search Engine (for Glassdoor)
1. Set up a [Google Custom Search Engine](https://cse.google.com/)
2. Configure it to search `glassdoor.com`
3. Get your Search Engine ID and add to `.env` as `GOOGLE_CSE_ID`
4. Get a Google Custom Search API key from [Google Cloud Console](https://console.cloud.google.com/apis/credentials)
5. Add to `.env` as `GOOGLE_CSE_KEY`

## 🤝 Contributing

Feel free to submit issues, feature requests, or pull requests to improve the job matcher!

## 📝 License

This project is for personal use. Please respect the terms of service of LinkedIn, SEEK, and Glassdoor when using their data.

## 👨‍💻 Author

**Magda**  
📧 magdalenekortas@gmail.com

---

*Happy job hunting! 🎉*
