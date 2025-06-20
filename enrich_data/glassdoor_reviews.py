"""
Glassdoor Enricher

This module fetches company reviews and ratings from Glassdoor
to enrich job data with insights about company culture and employee satisfaction.
"""

import os
import re
import time
import random
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from urllib.parse import urlencode, quote_plus

class GlassdoorEnricher:
    """Class to fetch company insights from Glassdoor."""
    
    def __init__(self, serpapi_key=None):
        """
        Initialize the Glassdoor enricher.
        
        Args:
            serpapi_key (str, optional): SerpAPI key. If not provided,
                                        it will try to load from environment variables.
        """
        # Load API key from environment if not provided
        if serpapi_key is None:
            load_dotenv()
            serpapi_key = os.getenv('SERPAPI_KEY')
        
        self.serpapi_key = serpapi_key
        self.use_serpapi = serpapi_key is not None
        
        # Initialize a session for direct scraping fallback
        self.session = requests.Session()
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
        }
    
    def get_company_insights(self, company_name):
        """
        Get company insights from Glassdoor.
        
        Args:
            company_name (str): Name of the company
            
        Returns:
            dict: Dictionary with company insights
        """
        if self.use_serpapi:
            return self._get_insights_serpapi(company_name)
        else:
            return self._get_insights_direct(company_name)
    
    def _get_insights_serpapi(self, company_name):
        """
        Get company insights using SerpAPI.
        
        Args:
            company_name (str): Name of the company
            
        Returns:
            dict: Dictionary with company insights
        """
        try:
            # Clean up company name
            company_name = company_name.strip()
            
            # Prepare SerpAPI query
            params = {
                'api_key': self.serpapi_key,
                'engine': 'glassdoor',
                'q': company_name,
                'hl': 'en'
            }
            
            # Make API request
            response = requests.get(
                'https://serpapi.com/search', 
                params=params
            )
            
            if response.status_code != 200:
                print(f"SerpAPI request failed: {response.status_code}")
                return self._get_default_insights()
            
            # Parse response
            data = response.json()
            
            # Extract company insights
            insights = {
                'rating': 0,
                'reviews_count': 0,
                'pros': [],
                'cons': [],
                'salaries': {}
            }
            
            # Check if we have company results
            if 'companies' in data and data['companies']:
                company = data['companies'][0]
                
                # Extract basic info
                insights['rating'] = company.get('rating', 0)
                insights['reviews_count'] = company.get('reviews_count', 0)
                
                # Extract pros and cons if available
                if 'reviews' in company:
                    for review in company['reviews'][:20]:  # Take top 3 reviews
                        if 'pros' in review and review['pros']:
                            insights['pros'].append(review['pros'])
                        if 'cons' in review and review['cons']:
                            insights['cons'].append(review['cons'])
                
                # Extract salary info if available
                if 'salaries' in company:
                    for salary in company['salaries'][:5]:  # Take top 5 salaries
                        role = salary.get('job_title', '')
                        amount = salary.get('salary', '')
                        if role and amount:
                            insights['salaries'][role] = amount
            
            return insights
            
        except Exception as e:
            print(f"Error getting Glassdoor insights via SerpAPI: {str(e)}")
            return self._get_default_insights()
    
    def _get_insights_direct(self, company_name):
        try:
            # Clean up company name
            company_name = company_name.strip()
            company_name_query = quote_plus(company_name)
            
            # Search for the company on Glassdoor
            search_url = f"https://www.glassdoor.com/Search/results.htm?keyword={company_name_query}"
            
            # Add more browser-like headers
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'Referer': 'https://www.google.com/',
                'Sec-Ch-Ua': '"Not A(Brand";v="99", "Google Chrome";v="120", "Chromium";v="120"',
                'Sec-Ch-Ua-Mobile': '?0',
                'Sec-Ch-Ua-Platform': '"Windows"',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'cross-site',
                'Sec-Fetch-User': '?1',
                'Upgrade-Insecure-Requests': '1',
                'Cache-Control': 'max-age=0',
            }
    
            # Set cookies if available - this helps bypass some protections
            cookies = {
                # You might want to manually copy some cookies from a browser session
                'gdId': 'some-cookie-value',  # Replace with actual value
                'JSESSIONID': 'some-session-value',  # Replace with actual value
            }
            
            # Add proxy support (consider using rotating proxies)
            # proxies = {
            #     'http': 'http://user:pass@proxy.example.com:8080',
            #     'https': 'http://user:pass@proxy.example.com:8080',
            # }
            
            # Make request with a timeout and retry logic
            for attempt in range(3):  # Try up to 3 times
                try:
                    # Uncomment the line below to use proxies
                    # response = self.session.get(search_url, headers=headers, cookies=cookies, proxies=proxies, timeout=10)
                    response = self.session.get(search_url, headers=headers, cookies=cookies, timeout=10)
                    
                    # Check if request was successful
                    if response.status_code == 200:
                        break
                    
                    print(f"Attempt {attempt+1} failed with status code {response.status_code}")
                    time.sleep(random.uniform(2, 5))  # Add a longer delay between retries
                except Exception as e:
                    print(f"Request error on attempt {attempt+1}: {str(e)}")
                    time.sleep(random.uniform(2, 5))
            else:
                # This executes if all attempts fail
                print(f"Glassdoor search request failed after 3 attempts")
                return self._get_default_insights()
            
            # Parse the response
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Check if we hit a CAPTCHA page
            if "captcha" in response.text.lower() or "please verify" in response.text.lower():
                print("Captcha detected, please implement a captcha solving solution")
                return self._get_default_insights()
            
            # Extract insights
            insights = {
                'rating': 0,
                'reviews_count': 0,
                'pros': [],
                'cons': [],
                'salaries': {}
            }
            
            # Look for company rating - update selectors based on current Glassdoor HTML structure
            rating_element = soup.select_one('.css-1pmc6te, .ratingNum, ._92skDVmktPG_grAw0Oaw3')
            if rating_element:
                try:
                    insights['rating'] = float(rating_element.text.strip())
                except:
                    pass
            
            # Look for number of reviews - update selectors
            reviews_element = soup.select_one('.count, .reviews-count, ._2DVF9EnkTjjqwPFcHoLJ1X')
            if reviews_element:
                text = reviews_element.text.strip()
                # Extract digits from text
                digits = re.sub(r'[^\d]', '', text)
                if digits:
                    insights['reviews_count'] = int(digits)
            
            # Try to find pros and cons - update selectors
            pros_elements = soup.select('.pros, ._2ldiUEpIELIgO9fBzVMH7O')
            for element in pros_elements[:2]:  # Take top 2
                if element.text.strip():
                    insights['pros'].append(element.text.strip())
            
            cons_elements = soup.select('.cons, ._32Suf_wmC4T9hLTlS_pQ91')
            for element in cons_elements[:2]:  # Take top 2
                if element.text.strip():
                    insights['cons'].append(element.text.strip())
            
            # Add a longer delay to avoid rate limiting
            time.sleep(random.uniform(2, 5))
            
            return insights
            
        except Exception as e:
            print(f"Error getting Glassdoor insights directly: {str(e)}")
            return self._get_default_insights()
        
    
    def _get_default_insights(self):
        """Return default empty insights."""
        return {
            'rating': 0,
            'reviews_count': 0,
            'pros': [],
            'cons': [],
            'salaries': {}
        }