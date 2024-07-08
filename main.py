import sys

from jobscrape.scraper import JobScraper

targetSites = None
if len(sys.argv) > 1:
    targetSites = sys.argv[1]

js = JobScraper()
js.load_urls(desired_sites=targetSites)
