import os
import json
import requests
import time
import random

def get_file_age_seconds(target_file):
    """
    Returns the age of a file in seconds.
    """
    try:
        # Get the last modification time of the file
        last_modified_time = os.path.getmtime(target_file)
        # Get the current time
        current_time = time.time()
        # Calculate the difference in seconds
        time_difference = current_time - last_modified_time
        return time_difference
    except FileNotFoundError:
        return None
    
# PROXY_URL = "https://www.proxynova.com/proxy-server-list/country-ca"
PROXY_URL = 'https://raw.githubusercontent.com/vakhov/fresh-proxy-list/master/proxylist.json'
PROXY_FILE = 'proxylist.json'

class Proxies:
    def __init__(self):
        self.proxies = None
        self.file_age = get_file_age_seconds(PROXY_FILE)

        self._load_proxies()

        # how old the file can be before downloading a fresh copy
        # 12 hours or 24 hours is recommended
        self._max_age = 60 * 60 * 12
        
        if not self.file_age or self.file_age > self._max_age:
            self._get_proxy_file()

    def _load_proxies(self):
        if not os.path.exists(PROXY_FILE):
            self._get_proxy_file()

        with open(PROXY_FILE, 'r') as f:
            self.proxies = json.load(f)

    def _get_proxy_file(self):
        print('downloading proxy file...')
        content = requests.get(PROXY_URL).text

        with open(PROXY_FILE, 'w') as f:
            f.write(content)   

        self.file_age = get_file_age_seconds(PROXY_FILE)

    def filter(self, country_name=None, anon=None, ssl=None):
        if ssl:
            ssl = "1"
        
        if self.proxies:
            return [
                entry for entry in self.proxies
                if (country_name is None or str(entry.get('country_name', 'unknown')).lower() == country_name.lower()) and
                   (anon is None or entry['anon'] >= str(anon)) and
                   (ssl is None or entry['ssl'] == ssl)
            ]
        return []


    def proxy_list(self,country_name=None, anon=None, ssl=None):
        filtered = self.filter(country_name=country_name, anon=anon, ssl=ssl)
        plist = []
        for entry in filtered:
            item_string = '{}:{}'.format(entry['ip'], entry['port'])
            plist.append(item_string)

        return plist

    def anonymous_proxies(self):
        return self.proxy_list(anon=4)
    
    def requests_proxies(self):
        anonymous = self.filter(anon=4)
        ssl = self.filter(anon=4, ssl=True)
        
        unsecure = random.choice(anonymous)
        # secure = random.choice(ssl)


        return {
            'http': f'http://{unsecure["ip"]}:{unsecure["port"]}',
            # 'https': f'http://{secure["ip"]}:{secure["port"]}',
        }
