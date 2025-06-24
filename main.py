#!/usr/bin/env python3
"""
Job Matcher: Main Application

This script orchestrates the job matching pipeline:
1. Fetches jobs from LinkedIn and SEEK
2. Matches jobs against your CV using Gemini API
3. Enriches job data with Glassdoor insights
4. Ranks and presents the best job matches
"""


import os
import argparse
import pandas as pd
from dotenv import load_dotenv
from tabulate import tabulate
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from glassdoor_cse import GlassdoorEnricher  # Import the new CSE-based enricher

# Import custom modules
from fetch_jobs.linkedin_jobs import LinkedInJobFetcher
from fetch_jobs.seek_jobs import SeekJobFetcher
from match_resume.parse_resume import ResumeParser
from match_resume.gemini_matcher import GeminiMatcher
#from enrich_data.glassdoor_reviews import GlassdoorEnricher

import time
from datetime import datetime

# Load environment variables
load_dotenv()

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Job Matcher Pipeline')
    parser.add_argument('--resume', type=str, required=True, help='Path to your resume PDF')
    parser.add_argument('--keywords', type=str, default='Frontend Developer, Software Engineer, Full Stack Developer',
                        help='Job keywords, comma separated. Multi-word phrases will be searched exactly on supported platforms (like LinkedIn)')
    parser.add_argument('--location', type=str, default='Sydney',
                        help='Job location')
    parser.add_argument('--limit', type=int, default=5,
                        help='Maximum number of jobs to fetch from each source')
    parser.add_argument('--output', type=str, default='public/job_matches.csv',
                        help='Output CSV file name')
    return parser.parse_args()

def main():
    """Main execution function."""
    print("Running at:", datetime.now())
    args = parse_arguments()
    print(f"[+] Job Matcher Pipeline Started - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    print("\n[+] Parsing resume...")
    resume_parser = ResumeParser(args.resume)
    resume_text = resume_parser.extract_text()

    print("\n[+] Fetching jobs...")
    all_jobs = []
    job_ids_seen = set() 

    keywords_list = [k.strip() for k in args.keywords.split(',')]

    # LinkedIn jobs
    try:
        linkedin_fetcher = LinkedInJobFetcher()
        processed_linkedin_keywords = []
        for kw in keywords_list:
            if ' ' in kw:
                processed_linkedin_keywords.append(f'"{kw}"')
            else:
                processed_linkedin_keywords.append(kw)

        print(f"    - Searching LinkedIn for: {processed_linkedin_keywords}") # Show what's being searched
        linkedin_jobs = linkedin_fetcher.fetch_jobs(keywords = processed_linkedin_keywords, location= args.location, days_ago=3, limit = args.limit)

        new_linkedin_jobs_count = 0
        for job in linkedin_jobs:
             if job.get('job_id') and job['job_id'] not in job_ids_seen:
                 all_jobs.append(job)
                 job_ids_seen.add(job['job_id'])
                 new_linkedin_jobs_count += 1
        print(f"    - LinkedIn: Added {new_linkedin_jobs_count} unique jobs (found {len(linkedin_jobs)} total)")

    except Exception as e:
        print(f"    - LinkedIn fetching error: {str(e)}")

    # SEEK jobs
    try:
        seek_fetcher = SeekJobFetcher()
        print(f"    - Searching SEEK for: {args.keywords}") 
        seek_jobs = seek_fetcher.fetch_jobs(keywords= args.keywords, location=args.location, limit=args.limit, max_days_old=3)

        new_seek_jobs_count = 0
        for job in seek_jobs:
            if job.get('job_id') and job['job_id'] not in job_ids_seen:
                all_jobs.append(job)
                job_ids_seen.add(job['job_id'])
                new_seek_jobs_count += 1
        print(f"    - SEEK: Added {new_seek_jobs_count} unique jobs (found {len(seek_jobs)} total)")

    except Exception as e:
        print(f"    - SEEK fetching error: {str(e)}")

    print(f"\n    - Total unique jobs found across sources: {len(all_jobs)}")


    exclude_keywords = []
    exclude_companies = []
    
    # Filter out jobs with titles containing any of the exclude keywords
    seen = set()
    unique_jobs = []
    
    for job in all_jobs:
        title = job.get('title', '').strip().lower()
        company = job.get('company', '').strip().lower()
        identifier = (title, company)
    
        if identifier not in seen:
            seen.add(identifier)
            unique_jobs.append(job)

    print('all jobs:', len(all_jobs))
    all_jobs = [
        job for job in unique_jobs
        if not any(kw.lower() in job.get('title', '').lower() for kw in exclude_keywords)
        if not any(kw.lower() in job.get('company', '').lower() for kw in exclude_companies)
    ]
    print('deleted keywords:',len(all_jobs))
    # 4. Enrich with Glassdoor data
    print("\n[+] Enriching with Glassdoor data...")
    glassdoor_enricher = GlassdoorEnricher()  # No parameters needed if using environment variables
    
    with ThreadPoolExecutor(max_workers=5) as executor:
        future_to_job = {
            executor.submit(glassdoor_enricher.get_company_insights, job['company']): job 
            for job in all_jobs
        }
        
        for i, future in enumerate(as_completed(future_to_job)):
            job = future_to_job[future]
            try:
                glassdoor_data = future.result()
                job.update(glassdoor_data)
                print(f"    - Enriched {i+1}/{len(all_jobs)}: {job['company']} - Rating: {job.get('rating', 'N/A')}")
            except Exception as e:
                print(f"    - Error enriching {job['company']}: {str(e)}")

    all_jobs = [
    job for job in all_jobs
    if (
        (job.get('rating', 0) == 0 or job.get('rating', 0) >= 3.9))]  # Allow if rating is missing (0) or >= 3.9
       # and "Contract" not in job.get('employment_type', "")        # Exclude if employment type includes "Contract"
      #  and job.get('title', "") != ""                

    print('filtered jobs:',len(all_jobs))
    
    df = pd.DataFrame(all_jobs)
    df.to_csv('test.csv', index=False, encoding='utf-8', errors='replace')
    print('df saved')

    
    # 3. Match jobs with resume using Gemini API
    print("\n[+] Matching jobs with resume...")
    gemini_matcher = GeminiMatcher()
    
    # Use ThreadPoolExecutor for parallel processing
    with ThreadPoolExecutor(max_workers=5) as executor:
        future_to_job = {
            executor.submit(gemini_matcher.match_job, job, resume_text): job 
            for job in all_jobs
        }
        
        for i, future in enumerate(as_completed(future_to_job)):
            job = future_to_job[future]
            try:
                match_result = future.result()
                job.update(match_result)
                print(f"    - Matched job {i+1}/{len(all_jobs)}: {job['title']} ({job['company']}) - Score: {job['match_score']}")
            except Exception as e:
                print(f"    - Error matching job {job['title']}: {str(e)}")

    all_jobs = [job for job in all_jobs if job.get('match_score', 0) > 70]

    print('matched jobs:',len(all_jobs))
    
    # 5. Rank and output results
    print("\n[+] Ranking and outputting results...")

    try:
        # Convert to DataFrame for easier manipulation
        df = pd.DataFrame(all_jobs)
        print(df)
        
        # Convert rating to numeric (invalid parsing results in NaN)
        df['rating'] = pd.to_numeric(df['rating'], errors='coerce')
        
        df = df.sort_values(by=['match_score', 'rating'], ascending=False)
        
        # Display top matches
        top_matches = df.head(10)
        display_columns = ['title', 'company', 'match_score', 'rating', 'match_reason']
        print("\n=== TOP 10 JOB MATCHES ===")
        print(tabulate(top_matches[display_columns], headers='keys', tablefmt='pretty'))
        
        output_file = args.output

        EXPECTED_COLUMNS = [
    'job_id',
    'title',
    'company',
    'location',
    'job_url',
    'apply',
    'comments',
    'match_score',
    'rating',
    'source',
    'seniority',
    'employment_type',
    'match_reason',
    'description',
    'skill_matches',
    'skill_gaps'
]
        
        # Check if output file already exists
        if os.path.exists(output_file):
            # Read existing data
            try:
                if os.path.exists(output_file):
                    existing_df = pd.read_csv(output_file)
                    print(f"[+] Found existing file with {len(existing_df)} records")
                
                    for col in EXPECTED_COLUMNS:
                        if col not in existing_df.columns:
                            existing_df[col] = None 
                
                    for col in EXPECTED_COLUMNS:
                        if col not in df.columns:
                            df[col] = None 
                
                    df = df.reindex(columns=EXPECTED_COLUMNS)
                
                    if 'title' in existing_df.columns and 'company' in existing_df.columns and \
                       'title' in df.columns and 'company' in df.columns:
                
                        existing_df['job_identifier'] = existing_df['title'].astype(str).str.lower() + '|' + existing_df['company'].astype(str).str.lower()
                        df['job_identifier'] = df['title'].astype(str).str.lower() + '|' + df['company'].astype(str).str.lower()
                
                        # Identify new jobs (not in existing file)
                        existing_identifiers = set(existing_df['job_identifier'].tolist())
                        df_new = df[~df['job_identifier'].isin(existing_identifiers)].copy()  
                        df_new = df_new.reindex(columns=existing_df.columns)
                        combined_df = pd.concat([df_new,existing_df], ignore_index=True)
                
                        combined_df = combined_df.drop('job_identifier', axis=1)
                
                        print(f"[+] Added {len(df_new)} new jobs to the existing file")
                
                        # Save the combined dataframe
                        combined_df.to_csv(output_file, index=False)
                        print(f"[+] Complete results saved to {output_file} (total: {len(combined_df)} jobs)")
                
                    else:
                        print("[-] 'title' or 'company' column missing in one of the DataFrames. Cannot create job identifier for deduplication.")

        
            except Exception as e:
                print(f"[!] Error reading existing file: {str(e)}. Creating new file.")
                df.to_csv(output_file, index=False)
                print(f"[+] Complete results saved to {output_file}")
        else:
            # No existing file, create new one
            df.to_csv(output_file, index=False)
            print(f"[+] Complete results saved to {output_file}")
        
        print(f"\n[+] Job Matcher Pipeline Completed - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    except Exception as e:
            print(f"No new jobs.")

if __name__ == "__main__":
    main()
