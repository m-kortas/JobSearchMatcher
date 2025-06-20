"""
Gemini Matcher Module

This module uses Google's Gemini API to match job descriptions with resume content,
providing a match score and insights into skill matches and gaps.
"""

import os
import json
import time
import random
import google.generativeai as genai
from dotenv import load_dotenv

class GeminiMatcher:
    """Class to match job descriptions with resume using Google's Gemini API."""
    
    def __init__(self, api_key=None):
        """
        Initialize the Gemini Matcher.
        
        Args:
            api_key (str, optional): Google API key for Gemini. If not provided,
                                     it will try to load from environment variables.
        """
        # Load API key from environment if not provided
        if api_key is None:
            load_dotenv()
            api_key = os.getenv('GOOGLE_API_KEY')
            
        if not api_key:
            raise ValueError("Google API key is required. Set GOOGLE_API_KEY environment variable.")
        
        # Configure the Gemini API
        genai.configure(api_key=api_key)
        
        # Get available models
        self.model = genai.GenerativeModel('gemini-1.5-pro')
    
    def match_job(self, job, resume_text):
        """
        Match a job description with the resume content.
    
        Args:
            job (dict): Job information including description
            resume_text (str): Text content of the resume
    
        Returns:
            dict: Dictionary with match score and insights
        """
        max_retries = 3
        retry_delay = 2
    
        # Add reasonable text limits to avoid exceeding token limits
        # These are just examples, adjust based on typical input size and model limits
        max_resume_tokens = 8000 # Example limit, adjust as needed
        max_job_desc_tokens = 4000 # Example limit, adjust as needed
        
        # Simple truncation - consider using a more sophisticated tokenizer if needed
        resume_text = resume_text[:max_resume_tokens * 4] # Rough estimate, ~4 chars per token
        job_description = job.get('description', '')
        job_description = job_description[:max_job_desc_tokens * 4]
    
        if not job_description:
            return {
                'match_score': 0,
                'skill_matches': [],
                'skill_gaps': [],
                'match_reason': 'No job description available'
            }
    
        for attempt in range(max_retries):
            try:
                # Construct the prompt for Gemini
                prompt = self._construct_prompt(resume_text, job_description, job.get('title', ''), job.get('company', ''))
    
                # Call the Gemini API with the correct parameter name
                response = self.model.generate_content(
                    prompt,
                    generation_config={"response_mime_type": "application/json"}  # Changed from request_options
                )
    
                # Access the text property of the response content
                response_text = response.text
    
                # Parse the response
                match_result = self._parse_response(response_text)
    
                # If parsing was successful, return the result
                if match_result.get('match_reason') != 'Unable to parse API response':
                     return match_result
    
                # If parsing failed but no API exception, it means the model didn't return valid JSON
                # Treat as an API error.
                raise ValueError("API returned non-parseable content despite JSON response type request.")
    
            except Exception as e:
                if attempt < max_retries - 1:
                    sleep_time = retry_delay * (2 ** attempt) + random.uniform(0, 1)
                    print(f"Gemini API error: {str(e)}. Retrying in {sleep_time:.1f}s...")
                    # Optionally log the raw response text here if available, for debugging
                    # print(f"Raw response causing error: {getattr(response, 'text', 'N/A')}")
                    time.sleep(sleep_time)
                else:
                    print(f"Failed to match job after {max_retries} attempts: {str(e)}")
                    # Include the specific inputs that failed for debugging
                    print(f"Job Description: {job_description[:200]}...") # Print first 200 chars
                    print(f"Job Title: {job.get('title', 'N/A')}")
                    print(f"Company: {job.get('company', 'N/A')}")
                    print(f"Resume Text: {resume_text[:200]}...") # Print first 200 chars
    
                    return {
                        'match_score': 0,
                        'skill_matches': [],
                        'skill_gaps': [],
                        'match_reason': f'API error after retries: {str(e)}'
                    }
    
    def _construct_prompt(self, resume_text, job_description, job_title, company):
        """Construct an effective prompt for the Gemini API."""
        return f"""
You are a seasoned recruitment analyst evaluating how well a candidate's resume aligns with a specific job description.

INPUT:
RESUME:
{resume_text}

JOB DETAILS:
Title: {job_title}
Company: {company}
Description: {job_description}

TASK:
Analyze the resume against the job description and return only a JSON object with the following fields:

1. "match_score": Integer (0–100). Overall fit between resumeand job.
2. "skill_matches": List of 5 key skills, qualifications, or experiences from the resume that clearly align with the job requirements.
3. "skill_gaps": List of 5 job requirements not present or weak in the resume.
4. "match_reason": 1-2 sentence explanation of the score.  

FORMAT:
Respond only with a JSON object like this:
{{
  "match_score": 85,
  "skill_matches": ["Python programming", "Data analysis", "Machine learning experience", "Project management"],
  "skill_gaps": ["Knowledge of AWS", "Hadoop experience"],
  "match_reason": "Strong analytical and technical alignment."
}}
"""
    
    def _parse_response(self, response_text):
        """
        Parse the response from Gemini API expecting strict JSON.

        Args:
            response_text (str): Text response from the API (expected to be JSON)

        Returns:
            dict: Parsed match results
        """
        try:
            # With mime_type='application/json', the entire response should be the JSON object
            result = json.loads(response_text)
            print(result)

            # Ensure all expected keys are present (still a good practice)
            required_keys = ['match_score', 'skill_matches', 'skill_gaps', 'match_reason']
            for key in required_keys:
                if key not in result:
                    # Provide sensible defaults if a key is missing
                    result[key] = [] if key in ['skill_matches', 'skill_gaps'] else None if key == 'match_score' else ''

            # Ensure match_score is an integer between 0-100
            try:
                score = int(result.get('match_score', 50)) # Default to 50 if key missing or not number
                result['match_score'] = max(0, min(100, score))
            except (ValueError, TypeError):
                 result['match_score'] = 50 # Default if conversion fails


            # Ensure skill_matches and skill_gaps are lists
            if not isinstance(result.get('skill_matches'), list):
                result['skill_matches'] = []
            if not isinstance(result.get('skill_gaps'), list):
                 result['skill_gaps'] = []

            # Ensure match_reason is a string
            if not isinstance(result.get('match_reason'), str):
                 result['match_reason'] = ''

            return result

        except json.JSONDecodeError as e:
            print(f"JSON decoding error: {e}")
            print(f"Raw response text: {response_text}") # Log the problematic response
            return {
                'match_score': 50,
                'skill_matches': [],
                'skill_gaps': [],
                'match_reason': f'Unable to parse API response (JSON Error: {e})'
            }
        except Exception as e:
            print(f"Error parsing Gemini response: {str(e)}")
            print(f"Raw response text: {response_text}") # Log the problematic response
            return {
                'match_score': 50,
                'skill_matches': [],
                'skill_gaps': [],
                'match_reason': f'Error parsing response: {str(e)}'
            }