from bs4 import BeautifulSoup
from pathlib import Path
from urllib.parse import urljoin, urlparse, parse_qs, urlencode, urlunparse
import json
import random
import requests
from requests.exceptions import ProxyError, RequestException
import re
import sys
import time

import logging

import pandas as pd
from jobspy import scrape_jobs

from jobscrape.models import Job, Keyword, JobKeyword, Site
from jobscrape.db import DB
from jobscrape.analyzer import Analyzer
from jobscrape.proxies import Proxies

SITES_JSON = '../sites.json'

logging.basicConfig(level=logging.INFO,  # Set the logging level
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',  # Log message format
                    handlers=[
                        # logging.FileHandler("app.log"),  # Log to a file
                        logging.StreamHandler()  # Log to the console
                    ])

logger = logging.getLogger(__name__)

class JobScraper:
    def __init__(self):
        self.db = DB()
        self.analyzer = Analyzer(logger=logger)

        self.sites = []
        self.load_sites()

        self.proxies = Proxies()
        self.proxy_list = self.proxies.anonymous_proxies()
        # print(self.proxy_list)
        # sys.exit()

    def import_sites_from_json(self):
        logger.info("IMPORTING SITES")

        target = Path(__file__).resolve().parent.joinpath(SITES_JSON).resolve()
        if not Path(target).exists():
            self.sites = []
            return
        
        sites = []
        with open(target) as f:
            sites_data = json.load(f)
        
        session = self.db.get_session()
        try:
            for site_data in sites_data:
                site = Site(**site_data)
                site_dict = {k: v for k, v in site.__dict__.items() if not k.startswith('_')}
                Site.add(session, **site_dict)
        except Exception as e:
            print(f"Error adding sites to the database: {e}")
        finally:
            session.close()
           
            


    def load_sites(self):
        session = self.db.get_session()
        self.sites = Site.list_all(session)
        session.close()

        if len(self.sites) == 0:
            logger.warn("No sites found in database.  Did you forget to import with the `-i` parameter?")
            sys.exit(1)

    def load_boards(self, search_phrases=[]):
        """
        Use JobSpy (https://github.com/Bunsly/JobSpy) to load Indeed, LinkedIn, etc.
        """

        proxy_list = self.proxies.proxy_list(anon=4) 
        if not proxy_list or len(proxy_list) == 0:
            print('No proxies found. Stopping.')
            return

        session = self.db.get_session()
        for phrase in search_phrases:
            random.shuffle(self.proxy_list)
            logger.info(f"JobSpy: {phrase}")
            jobs = scrape_jobs(
                site_name=["indeed", "linkedin", "zip_recruiter", "glassdoor"],
                search_term=phrase,
                location="Calgary, AB",
                results_wanted=50,
                hours_old=72, # (only Linkedin/Indeed is hour specific, others round up to days old)
                country_indeed='Canada',  # only needed for indeed / glassdoor

                # proxies=proxy_list, 
            )

            # convert NaN to None
            jobs = jobs.where(pd.notnull(jobs), None)

            for index, row in jobs.iterrows():
                job = Job.add(
                    session,
                    collected = int(time.time() * 1000),
                    source = row["site"],
                    title = row["title"],
                    url = row["job_url"],
                    description = row["description"],
                    location = row["location"],
                    remote_id = row["id"]
                )

                if job.id > 0 and not row["description"] is None:
                    keywords = self.analyzer.extract_keywords(row["description"])
                    for kw in keywords:
                        keyword_record = Keyword.add(session, kw)
                        jk = JobKeyword.add(session, job_id=job.id, keyword_id=keyword_record.id)

            session.commit()
            time.sleep(random.randrange(start=10, stop=30))

        session.close()        
        
    def load_urls(self, desired_sites=None):        
        for site in self.sites:
            if not desired_sites or site.code in desired_sites:
                # print(f'Loading {site.name} ')
                logger.info(f'Loading site: {site.name}')

                if not site.page_pattern:
                    self.extract_jobs(site.postings_url, site)
               
                if site.page_pattern:
                    # If a page_pattern exists, the site uses paging for the job listings
                    # In this case, we start by requesting the postings_url, and process the jobs we found.
                    # If we found jobs, we then adjust the page using the page_pattern, and page_type.
                    # The "page_group" is used to indicate what regular expression group in the page_pattern
                    # represents the actual page or offset value.
                    # If page_type is "page", then the next page is the current page + 1.
                    # If page_type is "offset", then the next page is the current page + job count.
                    # The paging process should exit if we cannot match the regular expression or we find no more jobs.
                    current_page = 1
                    job_count = self.extract_jobs(site.postings_url, site)
                    # Use 20 pages as the maximum to help prevent run-away situtions
                    while job_count and current_page < 20:
                        if site.page_type == 'offset':
                            current_page += job_count
                            logger.debug(f'> determining offset: {current_page}')
                        else:
                            current_page += 1
                            logger.debug(f'> determining page: {current_page}')


                        pattern = re.compile(site.page_pattern)
                        page_group = int(getattr(site, 'page_group', 2))
                        match = re.search(pattern, site.postings_url)
                        logger.debug(f'attempting to move to next page: {site.page_pattern}')
                        if match:
                            base_url = match.group(1)
                            current_url_page = int(match.group(page_group))
                            updated_url = re.sub(f"{current_url_page}", f"{current_page}", site.postings_url)
                            logger.info(f'> next {site.page_type} {current_page} : {updated_url}')
                            job_count = self.extract_jobs(updated_url, site)
                        else:
                            break


    def get_url(self, target, max_retries=3):
        retries = 0
        while retries < max_retries:
            try:
                proxy = self.proxies.requests_proxies()  
                response = requests.get(target, proxies=proxy, timeout=10)
                return response
            except (ProxyError, RequestException) as e:
                retries += 1
                logger.warn(f"Request failed with proxy {proxy}. Retrying with a different proxy.")
                # Handle or log the exception
                if retries < max_retries:
                    continue  # Retry with a different proxy
                else:
                    logger.error(f"Max retries ({max_retries}) reached. Unable to fetch URL {target}. Error: {e}")
                    break
        return None  # or handle failure as per your requirement

    def extract_jobs(self, target_url, site):
        jobs_found = 0
        response = self.get_url(target_url)

        if response and response.status_code == 200:
            content_parser = "html.parser"
            if site.rss:
                content_parser = "lxml-xml"

            soup = BeautifulSoup(response.content, content_parser)

            if content_parser == 'html.parser':
                careers_div = soup.select_one(site.selector_jobs_container)

                if not careers_div:
                    logger.error(f'Could not find jobs container - is the site client side rendered?')
                    return jobs_found

                container = getattr(site, 'selector_job_links', 'a')
                links = careers_div.select(container)
                links = [urljoin(site.postings_url, link.get('href')) for link in links]

            # Extract the RSS Feed links
            # (This may be specific to the Job Bank at this time and need to be generalized more)
            if content_parser == "lxml-xml":
                container = getattr(site, 'selector_job_links', None)
                if not container:
                    return 0
                
                entries = soup.find_all(container)
                links = []
                for entry in entries:
                    if entry.find(site.selector_job_title)
                    tag = entry.find('link')
                    if tag and 'href' in tag.attrs:
                        links.append(tag['href'])
            
            session = self.db.get_session()
            for link in links:
                if not Job.job_url_exists(session, link):
                    job = self.parse_job(target_url=link, site=site)
                    time.sleep(0.5)

            session.close()
            jobs_found = len(links)

        else:
            logger.error(f'HTTP STATUS: {response.status_code} returned for {target_url}')

        return jobs_found

    def parse_job(self, target_url="", site=None):
        if not site:
            return None
        
        if target_url:
            logger.info(f"JOB URL: {target_url}")
            response = self.get_url(target_url)

            if not response or response.status_code >= 400:
                # we could not retrieve the job page
                return None
            
            logger.debug(' - response received')
            # response = requests.get(target_url, proxies=self.proxy_list)
            soup = BeautifulSoup(response.content, 'html.parser')
            description = self._get_value(soup, site.selector_job_description)

            session = self.db.get_session()
            logger.debug(' - adding job')
            job = Job.add(session, 
                collected = int(time.time() * 1000),
                source = site.name,
                title = self._get_value(soup, site.selector_job_title),
                url = target_url,
                description = description,
                location = self._get_value(soup, site.selector_location),
                remote_id = self._get_value(soup, site.selector_job_id)
            )

            if job.id > 0:
                logger.debug(' - extracting keywords')
                keywords = self.analyzer.extract_keywords(description)
                logger.debug(' - adding keywords')
                for kw in keywords:
                    keyword_record = Keyword.add(session, kw)
                    jk = JobKeyword.add(session, job_id=job.id, keyword_id=keyword_record.id)
                    # jk = JobKeyword(job_id=job.id, keyword_id=keyword_record.id)
                    # session.add(jk)
                    # JobKeyword.add(session, job.id, keyword_record.id)
                    # self.db.add_job_keyword(stored_job, kw)

            session.commit()
            session.close()


    def _get_value(self, soup, selector):
        if selector:
            nodes = soup.select(selector)
            if nodes:
                texts = [node.get_text().strip() for node in nodes]
                return " ".join(texts)
        
        return ""
    
    def purge_old_jobs(self):
        limit = 7
        logger.info(f'Purging jobs older than {limit} days')
        return self.db.purge_old_jobs(olderthan=limit)