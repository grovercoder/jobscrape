#!/usr/bin/env python3

import argparse
import sys
from jobscrape.scraper import JobScraper


search_terms = [
    "Senior Software Developer",
    "Firmware Developer",
    "DevOps Engineer",
    "Full Stack Developer",
    "Software Engineer",
    "Database Administrator",
    "Network Engineer",
    "Project Manager",
    "Team Leader",
    "System Administrator",
    "AI/ML Engineer",
    "Web Developer",
    "Cloud Engineer",
    "Technical Lead",
    "IT Manager",
    "Technical Consultant",
    "Solutions Architect",
    "IT Infrastructure Manager",
    "Software Development Manager",
    "Automation Engineer"
]

def main():
    parser = argparse.ArgumentParser(description="Updates job postings in the database")

    parser.add_argument('-b', '--boards', help="include job boards", action='store_true')
    parser.add_argument('-t', '--target', type=str, help="career site to update", default="")
    parser.add_argument('-i', '--import_json', action="store_true")
    
    args = parser.parse_args()
   
    js = JobScraper()


    if args.import_json:
        js.import_sites_from_json()
        sys.exit


    js.purge_old_jobs()

    # Run JobSpy for Indeed, LinkedIn, Glassdoor, and ZipRecruiter
    if args.boards:
        js.load_boards(search_phrases=search_terms)

    # process the career sites
    js.load_urls(desired_sites=args.target)

if __name__ == "__main__":
    main()



