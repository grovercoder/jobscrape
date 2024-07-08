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

from jobscrape.db import Job, DB, Keyword, JobKeyword
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

class Site:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)


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

    def load_sites(self):
        logger.info("LOADING SITES")
        target = Path(__file__).resolve().parent.joinpath(SITES_JSON).resolve()
        if not Path(target).exists():
            self.sites = []
            return
        
        with open(target) as f:
            sites_data = json.load(f)
            self.sites = [Site(**site) for site in sites_data]
            

    def load_urls(self, desired_sites=None):        
        for site in self.sites:
            if not desired_sites or site.code in desired_sites:
                # print(f'Loading {site.name} ')
                logger.info(f'Loading site: {site.name}')
                if not hasattr(site, 'offset') and not hasattr(site, 'page_pattern'):
                    self.extract_jobs(site.postings_url, site)
                
                # if hasattr(site, 'offset'):
                #     current_offset = 0
                #     job_count = self.extract_jobs(site.postings_url, site)
                #     while job_count:
                #         current_offset += job_count
                #         parsed_url = urlparse(site.postings_url)
                #         query_params = parse_qs(parsed_url.query)
                #         query_params[site.offset] = [str(current_offset)]
                #         updated_query = urlencode(query_params, doseq=True)
                #         updated_url = urlunparse(parsed_url._replace(query=updated_query))
                #         logger.debug(f'> adjusting offset {current_offset} : {updated_url}')
                #         job_count = self.extract_jobs(updated_url, site)

                if hasattr(site, 'page_pattern'):
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
                        if hasattr(site, 'page_type') and site.page_type == 'offset':
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
                proxy = self.proxies.requests_proxies()  # Replace with your proxy retrieval logic
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
            soup = BeautifulSoup(response.content, 'html.parser')
            careers_div = soup.select_one(site.selector_jobs_container)

            if not careers_div:
                logger.error(f'Could not find jobs container - is the site client side rendered?')
                return jobs_found

            container = getattr(site, 'selector_job_links', 'a')
            links = careers_div.select(container)
            links = [urljoin(site.postings_url, link.get('href')) for link in links]
            
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