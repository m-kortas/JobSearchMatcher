import requests
import time
import json # Retained for potential future use, though current parsing is HTML-based
import re
import random
from bs4 import BeautifulSoup
from urllib.parse import urlencode, quote_plus

class LinkedInJobFetcher:
    """Class to fetch job listings from LinkedIn using XHR API calls."""

    def __init__(self):
        """Initialize the LinkedIn job fetcher with necessary headers and base URL."""
        self.session = requests.Session()
        # General headers, good for fetching individual job pages if needed
        self.general_headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': 'https://www.linkedin.com/jobs/', # General referer
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-origin', # Can be 'cross-site' if navigating from elsewhere
            'Upgrade-Insecure-Requests': '1',
        }
        # Specific headers for the XHR API calls
        self.api_headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'Accept': 'application/vnd.linkedin.normalized+json+streaming', # LinkedIn often uses this for its newer APIs
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': 'https://www.linkedin.com/jobs/search/', # Referer for job search API calls
            'Origin': 'https://www.linkedin.com',
            'X-Li-Track': '{"clientVersion":"1.13.1590","mpVersion":"1.13.1590","osName":"web","timezoneOffset":10,"timezone":"Australia/Sydney","deviceFormFactor":"DESKTOP","mpName":"voyager-web","displayDensity":1,"displayWidth":1920,"displayHeight":1080}', # Example X-Li-Track
            'X-Li-Page-Instance': f'urn:li:page:d_flagship3_search_srp_jobs;{random.getrandbits(64)}', # Dynamic page instance
            'Csrf-Token': 'ajax:0000000000000000000', # Placeholder, real token might be needed for some interactions if not guest
            'X-RestLi-Protocol-Version': '2.0.0', # Common for LinkedIn RestLi APIs
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
        }
        self.base_url = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"
        
        # Optional: Make an initial request to the jobs page to try and get cookies
        # try:
        #     self.session.get("https://www.linkedin.com/jobs/", headers=self.general_headers, timeout=10)
        #     time.sleep(random.uniform(0.5, 1.5))
        # except requests.RequestException as e:
        #     print(f"Warning: Initial request to LinkedIn jobs page failed: {e}")


    def fetch_jobs(self, keywords, location, limit=100, days_ago=5):
        """
        Fetch job listings from LinkedIn based on specified criteria.
        Searches each keyword separately.
        
        Args:
            keywords (list or str): Keywords to search for
            location (str): Location to search in
            limit (int): Maximum number of jobs to fetch
            days_ago (int): Fetch jobs posted within this many days (default: 5)
        """
        all_jobs = []
        job_ids_seen = set()

        if not isinstance(keywords, list):
            keywords = [keywords]

        for keyword in keywords:
            print(f"[+] Fetching jobs for keyword: '{keyword}'")
            if len(all_jobs) >= limit:
                print(f"Global job limit ({limit}) reached. Stopping search for '{keyword}'.")
                break
            
            # Parameters for the search query
            # Note: LinkedIn's guest API params can be minimal. 'f_WT' for worldwide, 'geoId' for specific locations.
            # Not using geoId for now to keep it simpler, relies on 'location' string.
            search_params = {
                'keywords': keyword,
                'location': location,
                # 'geoId': '92000000', # Example: Worldwide, can be more specific
                'trk': 'public_jobs_jobs-search-bar_search-submit', # Initial tracking ID
                'start': 0,
                'count': 25,  # Number of jobs to fetch per request (max 25 for this API)
                'f_TPR': f'r{days_ago * 86400}'  # Time Posted Range: r86400 = last 24 hours, r432000 = last 5 days
            }
            
            jobs_found_for_this_keyword = 0
            while True: # Loop for paginating results for the current keyword
                if len(all_jobs) >= limit:
                    print(f"    Global job limit ({limit}) reached during pagination for '{keyword}'.")
                    break

                query_string = urlencode(search_params, quote_via=quote_plus)
                url = f"{self.base_url}?{query_string}"
                # print(f"    Fetching URL: {url}") # Uncomment for debugging

                try:
                    response = self.session.get(url, headers=self.api_headers, timeout=15)
                    # print(f"    Status Code: {response.status_code}") # Uncomment for debugging
                    response.raise_for_status() # Raises HTTPError for bad responses (4XX or 5XX)

                    # The response from this guest API is typically HTML snippets
                    html_content = response.text
                    if not html_content.strip():
                        print(f"    Received empty response for '{keyword}' at start={search_params['start']}. Assuming no more jobs.")
                        break

                    soup = BeautifulSoup(html_content, 'html.parser')
                    
                    # LinkedIn uses different class names, try a few common ones for job cards
                    job_cards = soup.find_all('div', class_='base-search-card')
                    if not job_cards:
                        job_cards = soup.find_all('li', class_=re.compile(r'job-result-card|job-card-list__item|job-search-card'))
                    if not job_cards: # If still no cards, try the original selector
                         job_cards = soup.find_all('div', class_='base-card')

                    # print(f"    Found {len(job_cards)} raw job cards on page (start={search_params['start']}).") # Uncomment for debugging

                    if not job_cards and search_params['start'] > 0:
                        print(f"    No more job cards found for keyword '{keyword}' after page with start={search_params['start'] - search_params['count']}.")
                        break
                    elif not job_cards and search_params['start'] == 0:
                        print(f"    No job cards found on the first page for keyword '{keyword}'.")
                        # print(f"DEBUG Response HTML (first 500 chars): {html_content[:500]}") # For debugging
                        break
                    
                    newly_added_jobs_this_page = 0
                    for card in job_cards:
                        if len(all_jobs) >= limit:
                            break
                        
                        job_data = self._parse_job_card(card)
                        if job_data and job_data['job_id'] not in job_ids_seen and job_data['job_id'] != "unknown":
                            # Fetch full job details (this is resource-intensive)
                            detailed_info = self._fetch_job_details(job_data['job_url'])
                            if detailed_info:
                                job_data.update(detailed_info)
                            
                            job_data['search_keyword'] = keyword # Add the keyword that found this job
                            all_jobs.append(job_data)
                            job_ids_seen.add(job_data['job_id'])
                            newly_added_jobs_this_page += 1
                            jobs_found_for_this_keyword +=1
                            # print(f"      Added job: {job_data['title'][:50]}...") # Uncomment for debugging
                            time.sleep(random.uniform(0.5, 1.2)) # Small delay after processing each job
                    
                    print(f"    Added {newly_added_jobs_this_page} new jobs from this page for '{keyword}'.")

                    if newly_added_jobs_this_page == 0 and search_params['start'] > 0:
                        print(f"    No new unique jobs processed from this page for '{keyword}', stopping pagination.")
                        break
                        
                    if search_params['start'] == 0 and newly_added_jobs_this_page == 0 and not job_cards: # Should be caught by earlier break
                         print(f"    No jobs found at all for '{keyword}'.")
                         break


                    # Prepare for the next page
                    search_params['start'] += search_params['count']
                    
                    # IMPORTANT: Update 'trk' for pagination requests
                    search_params['trk'] = 'public_jobs_jobs-search-results_see-more-jobs_bottom' # Critical for subsequent loads

                    # LinkedIn guest search depth is limited (around 40 pages or 1000 jobs)
                    if search_params['start'] >= 975: # Max offset is typically 975 (page 40 if count=25)
                        print(f"    Reached LinkedIn's typical pagination depth (around 1000 results) for '{keyword}'.")
                        break
                    
                    time.sleep(random.uniform(1.8, 4.0)) # Delay between paginated requests

                except requests.exceptions.HTTPError as e:
                    print(f"    HTTP error for '{keyword}' at start={search_params['start']}: {e}")
                    if e.response.status_code == 400:
                        print(f"    Received 400 Bad Request. This often means pagination limit or invalid parameters for '{keyword}'.")
                    elif e.response.status_code == 429:
                        print(f"    Received 429 Too Many Requests. Consider increasing delays or using proxies.")
                    # print(f"DEBUG Response text for HTTP error:\n{e.response.text[:500]}\n") # For debugging
                    break # Stop paginating for this keyword on error
                except requests.exceptions.RequestException as e:
                    print(f"    Request error for '{keyword}' at start={search_params['start']}: {e}")
                    break
                except Exception as e:
                    print(f"    An unexpected error occurred while fetching for '{keyword}' at start={search_params['start']}: {e}")
                    break
            
            print(f"  Finished searching for '{keyword}'. Total jobs added for this keyword: {jobs_found_for_this_keyword}")
            # Delay between different keywords
            if keyword != keywords[-1]: # Avoid sleeping after the last keyword
                 time.sleep(random.uniform(2.0, 4.5))
        
        return all_jobs

    def _parse_job_card(self, card):
        """Extract job information from a job card element."""
        try:
            title_element = card.find(['h3', 'a'], class_=re.compile(r'base-search-card__title|job-card-list__title'))
            title = title_element.text.strip() if title_element else "No Title"

            company_element = card.find(['h4', 'a'], class_=re.compile(r'base-search-card__subtitle|job-card-container__company-name'))
            company = company_element.text.strip() if company_element else "No Company"

            location_element = card.find('span', class_=re.compile(r'job-search-card__location|job-card-meta__location'))
            location = location_element.text.strip() if location_element else "No Location"

            job_url_element = card.find('a', class_=re.compile(r'base-card__full-link|job-card-list__title-link'))
            job_url = ""
            if job_url_element and job_url_element.get('href'):
                job_url = job_url_element.get('href').split('?')[0]
                if not job_url.startswith('http'): # Ensure URL is absolute
                    job_url = "https://www.linkedin.com" + job_url
            
            # Try to get job ID from URL or data attributes
            job_id = "unknown"
            if job_url:
                match = re.search(r'/jobs/view/(\d+)', job_url) or \
                        re.search(r'currentJobId=(\d+)', job_url) or \
                        re.search(r'view/(\d+)', job_url.split('/')[-1] if '/' in job_url else "") 
                if match:
                    job_id = match.group(1)
            
            if job_id == "unknown": # Fallback to data attributes on the card
                data_job_id = card.get('data-job-id') or card.get('data-entity-urn')
                if data_job_id:
                    match = re.search(r'(\d+)', str(data_job_id))
                    if match:
                        job_id = match.group(1)
            
            # If essential information is missing, this might not be a valid job card
            if title == "No Title" and company == "No Company" and not job_url:
                return None

            return {
                'source': 'LinkedIn',
                'title': title,
                'company': company,
                'location': location,
                'job_url': job_url,
                'job_id': job_id,
                'description': '', # To be filled by _fetch_job_details
                'match_score': 0,  # Placeholder
                'rating': 0        # Placeholder
            }
        except Exception as e:
            # print(f"      Error parsing a job card's basic info: {str(e)}\n      Card HTML: {str(card)[:200]}") # Debug
            return None

    def _fetch_job_details(self, job_url):
        """Fetch detailed job description from the job page."""
        if not job_url:
            return {}
        
        try:
            time.sleep(random.uniform(0.7, 1.5)) # Be respectful with delays
            # Use general headers for fetching the job detail page
            response = self.session.get(job_url, headers=self.general_headers, timeout=15)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')

            description_html_element = soup.find('div', class_=re.compile(r'description__text|show-more-less-html__markup'))
            description = "No description available"
            if description_html_element:
                # get_text() is better for extracting clean text from complex HTML
                description = description_html_element.get_text(separator='\n', strip=True)
            else: # Fallback for other description containers if the primary one is not found
                desc_container = soup.find('section', class_=re.compile(r'show-more-less-html|main-job-description'))
                if desc_container:
                    description_markup = desc_container.find('div', class_=re.compile(r'show-more-less-html__markup|decorated-job-posting__details'))
                    if description_markup:
                        description = description_markup.get_text(separator='\n', strip=True)
            
            details = {
                'description': description,
                'date_posted': self._extract_criterion_from_page(soup, ['Date posted', 'Posted Date']),
                'seniority': self._extract_criterion_from_page(soup, ['Seniority level']),
                'employment_type': self._extract_criterion_from_page(soup, ['Employment type']),
                'job_function': self._extract_criterion_from_page(soup, ['Job function']),
                'industries': self._extract_criterion_from_page(soup, ['Industries'])
            }
            return details

        except requests.exceptions.RequestException as e:
            # print(f"        Network error fetching details from {job_url}: {e}") # Debug
            return {'description': f'Failed to fetch job details (network): {e}'}
        except Exception as e:
            # print(f"        Error fetching/parsing job details from {job_url}: {e}") # Debug
            return {'description': f'Failed to fetch job details (parsing): {e}'}

    def _extract_criterion_from_page(self, soup, header_options):
        """Helper to extract text based on a list of possible header texts for criteria."""
        try:
            # Common structure for job criteria
            criteria_items = soup.find_all('li', class_=re.compile(r'description__job-criteria-item|job-details-jobs-unified-top-card__job-insight'))
            for item in criteria_items:
                header_el = item.find(['h3','dt'], class_=re.compile(r'description__job-criteria-subheader|job-details-jobs-unified-top-card__job-insight-header'))
                if header_el and any(opt.lower() in header_el.text.lower() for opt in header_options):
                    value_el = item.find(['span','dd'], class_=re.compile(r'description__job-criteria-text|job-details-jobs-unified-top-card__job-insight-text'))
                    if value_el:
                        return value_el.text.strip()
            
            # Fallback for information often found in the top card (e.g., posted date)
            top_card_info_elements = soup.select('div.topcard__flavor-indicator span, span.job-details-jobs-unified-top-card__posted-date,figcaption.job-poster__tagline time')
            for el in top_card_info_elements:
                text_content = el.text.strip()
                if any(opt.lower() in text_content.lower() for opt in ["day", "week", "month", "hour", "ago", "posted", "on"]):
                     if any(hdr.lower() in " ".join(header_options).lower() for hdr in ["date", "posted"]): # Check if we're looking for date
                        return text_content
            
            return "Not specified"
        except Exception:
            return "Not specified"