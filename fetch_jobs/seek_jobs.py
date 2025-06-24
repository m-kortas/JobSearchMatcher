"""
SEEK Job Fetcher

This module fetches job listings from SEEK by scraping the search results and
job detail pages to extract relevant information with anti-detection measures.
"""

import requests
import time
import random
import re
import datetime
from bs4 import BeautifulSoup
from urllib.parse import urljoin, quote_plus
import itertools

class SeekJobFetcher:
    """Class to fetch job listings from SEEK website with anti-detection measures."""
    
    def __init__(self, proxies=None, enable_anti_detection=True):
        """
        Initialize the SEEK job fetcher with necessary headers and base URL.
        
        Args:
            proxies (list): List of proxy dictionaries in format:
                          [{'http': 'http://user:pass@ip:port', 'https': 'https://user:pass@ip:port'}, ...]
            enable_anti_detection (bool): Enable anti-detection measures
        """
        self.session = requests.Session()
        self.proxies = proxies or []
        self.proxy_cycle = itertools.cycle(self.proxies) if self.proxies else None
        self.enable_anti_detection = enable_anti_detection
        self.request_count = 0
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:122.0) Gecko/20100101 Firefox/122.0',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 Edg/121.0.0.0'
        ]
        
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
        }
        self.base_url = "https://www.seek.com.au"
        
        # Configure session for incognito mode simulation
        if self.enable_anti_detection:
            self._configure_anti_detection()
    
    def _configure_anti_detection(self):
        """Configure session with anti-detection measures."""
        # Disable SSL warnings and configure session
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        
        # Set session timeout and connection pooling
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=1,
            pool_maxsize=1,
            max_retries=3
        )
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)
        
        # Add common browser headers for incognito simulation
        self.session.headers.update({
            'Accept-Encoding': 'gzip, deflate, br',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Sec-Ch-Ua': '"Not A(Brand";v="99", "Google Chrome";v="121", "Chromium";v="121"',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Ch-Ua-Platform': '"macOS"',
            'Upgrade-Insecure-Requests': '1'
        })

    def _get_next_proxy(self):
        """Get the next proxy from the rotation."""
        if self.proxy_cycle:
            return next(self.proxy_cycle)
        return None

    def _rotate_user_agent(self):
        """Rotate user agent for anti-detection."""
        if self.enable_anti_detection:
            user_agent = random.choice(self.user_agents)
            self.headers['User-Agent'] = user_agent

    def _make_request(self, url, **kwargs):
        """Make a request with proxy rotation and anti-detection measures."""
        self.request_count += 1
        
        # Rotate user agent every few requests
        if self.request_count % random.randint(3, 7) == 0:
            self._rotate_user_agent()
        
        # Get proxy for this request
        proxy = self._get_next_proxy()
        if proxy:
            kwargs['proxies'] = proxy
        
        # Add anti-detection headers dynamically
        headers = self.headers.copy()
        if self.enable_anti_detection:
            # Randomize some header values
            headers['Accept-Language'] = random.choice([
                'en-US,en;q=0.9',
                'en-AU,en;q=0.9,en-US;q=0.8',
                'en-GB,en;q=0.9,en-US;q=0.8'
            ])
            
            # Randomize viewport hints
            headers['Viewport-Width'] = str(random.choice([1920, 1366, 1440, 1536]))
            
            # Add random referer occasionally
            if random.random() < 0.3:
                headers['Referer'] = random.choice([
                    'https://www.google.com/',
                    'https://www.google.com.au/',
                    'https://www.seek.com.au/'
                ])
        
        # Make request with retry logic
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = self.session.get(url, headers=headers, **kwargs)
                
                # Check for rate limiting or blocking
                if response.status_code == 429:
                    wait_time = random.uniform(30, 60)
                    print(f"Rate limited. Waiting {wait_time:.1f} seconds...")
                    time.sleep(wait_time)
                    continue
                
                # Check for potential blocking patterns
                if response.status_code == 403 or 'blocked' in response.text.lower():
                    print(f"Potential blocking detected on attempt {attempt + 1}")
                    if attempt < max_retries - 1:
                        time.sleep(random.uniform(10, 20))
                        continue
                
                return response
                
            except requests.exceptions.ProxyError:
                print(f"Proxy error on attempt {attempt + 1}. Trying next proxy...")
                proxy = self._get_next_proxy()
                if proxy:
                    kwargs['proxies'] = proxy
                continue
            except requests.exceptions.RequestException as e:
                if attempt == max_retries - 1:
                    raise e
                time.sleep(random.uniform(2, 5))
        
        return response
    
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
                
                # Make the request with anti-detection measures
                response = self._make_request(search_url, timeout=15)
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
                                
                                # Enhanced delay with randomization for anti-detection
                                delay = random.uniform(1.0, 3.0) if self.enable_anti_detection else random.uniform(0.5, 1.5)
                                time.sleep(delay)
                            
                    except Exception as e:
                        print(f"Error processing SEEK job card: {str(e)}")
                        continue
                
                # Move to the next page
                page += 1
                
                # Enhanced delay between pages for anti-detection
                delay = random.uniform(2.0, 6.0) if self.enable_anti_detection else random.uniform(1.0, 3.0)
                time.sleep(delay)
                
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
            # Enhanced delay with randomization for anti-detection
            delay = random.uniform(1.0, 2.5) if self.enable_anti_detection else random.uniform(0.5, 1.0)
            time.sleep(delay)
            
            response = self._make_request(job_url, timeout=15)
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
