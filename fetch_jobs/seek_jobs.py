"""
SEEK Job Fetcher

This module fetches job listings from SEEK by scraping the search results and
job detail pages to extract relevant information.
"""

import requests
import time
import random
import re
import datetime
from bs4 import BeautifulSoup
from urllib.parse import urljoin, quote_plus

class SeekJobFetcher:
    """Class to fetch job listings from SEEK website."""
    
    def __init__(self):
        """Initialize the SEEK job fetcher with necessary headers and base URL."""
        self.session = requests.Session()
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
        }
        self.base_url = "https://www.seek.com.au"
    
    def fetch_jobs(self, keywords, location, limit=20, max_days_old=3):
        """
        Fetch job listings from SEEK based on specified criteria.
        
        Args:
            keywords (str): Keywords to search for (comma-separated)
            location (str): Location to search in
            limit (int): Maximum number of job listings to fetch
            max_days_old (int): Maximum age of jobs in days to include
        
        Returns:
            list: List of job dictionaries with details
        """
        all_jobs = []
        page = 1
        
        # Format location and keywords for URL
        if location.lower() == 'sydney':
            location_param = 'All-Sydney-NSW'
        else:
            location_param = quote_plus(location)
        
        # Convert keywords to URL-friendly format
        if isinstance(keywords, list):
            keywords = " ".join(keywords)
        
        # Replace spaces with hyphens and handle special characters
        keywords_param = keywords.replace(' ', '-').replace(',', '-').lower()
        keywords_param = re.sub(r'[^a-z0-9-]', '', keywords_param)
        keywords_param = re.sub(r'-+', '-', keywords_param).strip('-')
        
        # Calculate the cutoff date
        cutoff_date = datetime.datetime.now() - datetime.timedelta(days=max_days_old)
        
        while len(all_jobs) < limit:
            try:
                # Construct the search URL with date filter
                # Adding date filter directly to the URL
                search_url = f"{self.base_url}/{keywords_param}-jobs/in-{location_param}?daterange=3&page={page}"
                
                # Make the request
                response = self.session.get(search_url, headers=self.headers)
                response.raise_for_status()
                
                # Parse job results
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Find all job cards
                job_cards = soup.select('article[data-automation="normalJob"]')
                
                if not job_cards:
                    # No more jobs or reached the end
                    break
                
                # Process each job card
                for card in job_cards:
                    if len(all_jobs) >= limit:
                        break
                    
                    try:
                        job = self._parse_job_card(card)
                        if job:
                            # Check if job is within the date range
                            if self._is_job_recent(job['date_posted'], max_days_old):
                                # Fetch full job details
                                job_details = self._fetch_job_details(job['job_url'])
                                if job_details:
                                    job.update(job_details)
                                
                                all_jobs.append(job)
                                
                                # Add slight delay to avoid rate limiting
                                time.sleep(random.uniform(0.5, 1.5))
                            
                    except Exception as e:
                        print(f"Error processing SEEK job card: {str(e)}")
                        continue
                
                # Move to the next page
                page += 1
                
                # Add delay between pages to avoid rate limiting
                time.sleep(random.uniform(1.0, 3.0))
                
            except Exception as e:
                print(f"Error fetching SEEK jobs: {str(e)}")
                break
        
        return all_jobs
    
    def _is_job_recent(self, date_string, max_days_old):
        """
        Check if a job is recent based on its posting date string.
        
        Args:
            date_string (str): Date string from SEEK (e.g., '2d ago', 'Today', etc.)
            max_days_old (int): Maximum age in days
            
        Returns:
            bool: True if the job is within the specified age range
        """
        try:
            # Handle common date formats on SEEK
            date_string = date_string.lower().strip()
            
            # Handle "Today" case
            if 'today' in date_string:
                return True
                
            # Handle "Yesterday" case
            if 'yesterday' in date_string:
                return max_days_old >= 1
                
            # Handle "Xh ago" case (hours)
            hour_match = re.search(r'(\d+)h ago', date_string)
            if hour_match:
                return True  # Hours old is definitely within any reasonable day limit
                
            # Handle "Xd ago" case (days)
            day_match = re.search(r'(\d+)d ago', date_string)
            if day_match:
                days = int(day_match.group(1))
                return days <= max_days_old
                
            # Handle specific date format if present
            # This would need to be expanded based on actual observed formats
            
            # Default to keeping the job if we can't parse the date format
            # (Could be changed to exclude by default instead)
            return True
            
        except Exception as e:
            print(f"Error parsing job date '{date_string}': {str(e)}")
            return True  # Keep by default in case of parsing errors
    
    def _parse_job_card(self, card):
        """Extract job information from a job card element."""
        try:
            # Extract job title
            title_element = card.select_one('[data-automation="jobTitle"]')
            title = title_element.text.strip() if title_element else "No Title"
            
            # Extract company name
            company_element = card.select_one('[data-automation="jobCompany"]')
            company = company_element.text.strip() if company_element else "No Company"
            
            # Extract location
            location_element = card.select_one('[data-automation="jobLocation"]')
            location = location_element.text.strip() if location_element else "No Location"
            
            # Extract job URL
            url_element = card.select_one('a[data-automation="jobTitle"]')
            job_url = urljoin(self.base_url, url_element['href']) if url_element and 'href' in url_element.attrs else None
            
            # Extract job ID from URL
            job_id_match = re.search(r'/job/(\d+)/?', job_url) if job_url else None
            job_id = job_id_match.group(1) if job_id_match else "unknown"
            
            # Extract listing date if available
            date_element = card.select_one('[data-automation="jobListingDate"]')
            date_posted = date_element.text.strip() if date_element else "Unknown"
            
            # Basic job dictionary
            job = {
                'source': 'SEEK',
                'title': title,
                'company': company,
                'location': location,
                'job_url': job_url,
                'job_id': job_id,
                'date_posted': date_posted,
                'description': '',
                'match_score': 0,
                'rating': 0
            }
            
            return job
        except Exception as e:
            print(f"Error parsing SEEK job card: {str(e)}")
            return None
    
    def _fetch_job_details(self, job_url):
        """Fetch detailed job description from the job page."""
        if not job_url:
            return {}
            
        try:
            # Add slight delay before fetching details
            time.sleep(random.uniform(0.5, 1.0))
            
            response = self.session.get(job_url, headers=self.headers)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract job description
            description_element = soup.select_one('[data-automation="jobAdDetails"]')
            description = description_element.text.strip() if description_element else "No description available"
            
            # Extract employment type if available
            employment_type = "Not specified"
            employment_element = soup.select_one('[data-automation="job-detail-work-type"]')
            if employment_element:
                employment_type = employment_element.text.strip()
            
            # Extract salary information if available
            salary = "Not specified"
            salary_element = soup.select_one('[data-automation="job-detail-salary"]')
            if salary_element:
                salary = salary_element.text.strip()
            
            # Extract other details if available
            details = {
                'description': description,
                'employment_type': employment_type,
                'salary': salary
            }
            
            # Look for other job details like classification, etc.
            for bullet in soup.select('[data-automation^="job-detail-"]'):
                try:
                    key = bullet.get('data-automation').replace('job-detail-', '')
                    details[key] = bullet.text.strip()
                except:
                    pass
            
            return details
            
        except Exception as e:
            print(f"Error fetching SEEK job details from {job_url}: {str(e)}")
            return {'description': 'Failed to fetch job details'}