# JobScrape

Jobscrape is a personal job board type of tool.  It collects job postings from specified careers pages into a central location for further purusal.  The intent is to reduce the time needed to manually review postings at various sites.

In addition, Jobscrape extracts keywords from the job descriptions, and from a specified resume.  A quick report is then generated to display the top postings that match the resume's keywords.

Jobscrape began as a research project, and the focus has shifted some as things progressed.  This was intended for personal use only, so the code is a little messy.  

## Setup

Start with cloning this repository.  Use the command line to complete the setup:

```bash
cd project_dir

# setup a virtual environment (substitute the flavour of your choosing here - I use venv)
python3 -m venv .venv

# activate the environment
source .venv/bin/activate

# install dependencies
pip install -r requirements.txt

# load the initial list of sites from the `sites.json` file
python3 update_jobs.py -i

```

## Usage

```bash
# scan for new job postings from each of the specified "sites"
# - this uses HTTP proxies and some small delays to reduce the load on the target servers
#   and minimize the chance of getting your own IP address blocked.  
python3 update_jobs.py

# scan for new job postings from the "big 4" job boards (indeed, linkedin, glassdoor, ziprecruiter)
# - using proxies here currently fails.  I recommend doing this sporadically, as your own IP address will be exposed.
# - Think of this method as a complete scan - it scans the big four AND the specified sites.
python3 update_jobs.py -b

# scan a specific site
# - where site is an entry in the "sites" table or the `sites.json` file.
# - The "code" property is used here.
python3 update_jobs.py -t GoA

# Extract keywords from resume and generate a quick_report.html file listing the top matches
# - Only .pdf and .md files are supported at this time
python3 compare.py /path/to/my_resume.pdf

```

The last step will create a `quick_report.html` file.  You can open this in your browser.  It provides a simple list of job titles and a "score".  The titles are linked to the original job posting.  The score is a percentage calculation indicating how many of the resume keywords matched the job description's keywords.  

Scanning takes some time to complete.  I'm seeing a range of a few minutes up to 30ish minutes depending on what I'm doing (fresh DB or not), the state of my Internet connection, etc. 

## Legal Disclaimer

If you use this tool, you assume all legal risks.  This code filled a need for me in a manner that is considered legal in my jurisdiction (to the best of my knowledge), and in a manner that I am comfortable with for myself.  These considerations may not apply to you and your jurisdiction.  

Screen scraping is a gray matter where the law is concerned. This tool is only looking for data that is publicly accessible anyway, but we are doing so in a manner that may be deemed "hacking" to the non-technical minded lawyers.  

Use your own judgement on the legal concerns.  I am not responsible for any legal issues that may occur as a result of you using this code.

## How it works

The `update_jobs.py` script does a number of steps:

1. It creates a connection to an SQLite3 database (`project_directory/jobs.db` by default).  This DB is created if needed.
1. A list of proxy servers is retrieved and set up.  I have this favoring anonymous proxies at the moment.  The list of proxies is randomized each time it is called.  This has more to do with trying to keep your IP from being identified and blocked, and spreading the load across different geographically located servers (i.e. CDNs).
1. It uses [JobSpy](https://github.com/Bunsly/JobSpy) to scan the larger job boards.
1. It grabs a list of sites from the `sites` table, and finds the list of job links.  It handles paging if this has been set up for the site.
1. The job details page is loaded and the basic job information is extracted if possible.  Job Title, location, Job ID (as defined by the remote site), and the job description. This information is stored in the local database for later analysis, along with the URL to the job posting.
1. Keywords are extracted from the job description and stored for later use.

You can use the database natively to scan, analyze, and/or search the job postings as you'd like.

The `compare.py` script is used to automate some of that database work:

1. The specified resume file is read, and the keywords for the text content are extracted.
1. For each resume keyword, a search is done against the database to find jobs that also have that keyword
1. A score is calculated to indicate the percentage of resume keywords that matched the job posting's keywords.  This scoring system is not perfect and can be improved, but it is a starting point.  You can expect low percentage values here - I'm currently considering 25% a very strong match.  This score is only intended as a tool to indicate which job postings should receive more attention.
1. The `quick_report.html` file is generated listing the top matching jobs.  This list is roughly equivalent to spending the time to manually load and scan each of the job boards to find matches that are relevant to you.

For myself, the whole process takes approximately 15 minutes, most of it doing the job scans while I work on something else.  Before using this code I was spending half a day on this process.

## Be Kind

The sites are providing a mutual service.  They are looking for candidates for their job postings, while job seekers want to see what job postings might be relevant to them.  However abusing the service degrades the performance of the servers and can lead to decreased good will.  

Try not to scan too often.  The job postings do not change much in an hour, or even a day.  So let's be kind to the system administrators who run the servers we are pulling the data from.  Scanning too often could lead to a Denial of Service type result on the server which just hurts all of us.

The larger job boards treat the postings as proprietary information in some cases, and are quick to block or ban IP addresses that do not access the data through the preferred means (i.e. view it in a browser after logging into your account, so that everything can be tracked and monetized.)  This is partially based on the abuse early job boards received with thier contents being pilfered and reposted on competing platforms.  

I manually trigger the job scans periodically - usually only once or twice a day.

## Adding sites

A "site" is any resource that provides a list of links to a job posting.  This could be an RSS feed, a multi-page government job postings site, or a simple company Careers page. The intent here is to list the "sites" that might be relevant to you.  

The easiest way to add a site is to use the `sites.json` file. You can run `./update_jobs.py -i` to import the this file at anytime.  Only new sites will be added to the database.  You can modify the database directly if you'd like, keeping in mind that if you delete the DB file, you'll have to redo that site unless it was backed up in some way. 

We use CSS selectors to find the information we are looking for.  For "normal" pages (not RSS feeds), We assume there are two pages involved - the listing page, and the detail page.

Sites have the following properties then:

- **code** - a short string used to quickly identify this site.  This is used if/when a specific site is being scanned.  Example 'GoA' for "Government of Alberta".  Avoid using spaces in this code.
- name - the name of the site.  i.e. "Government of Alberta".
- **postings_url** - the URL to the page that has the list of job links.  This might be a direct link, or it might be the result of a search post.  If you see something like "searchresults/page2", try just "searchresults" or "searchresults/page1" to find the first page.  We can use the paging options to adjust for other pages.
- **rss** - this should be a value of "1" (number 1) if the postings_url is an RSS feed.  Otherwise it should be a value of zero.
- **page_pattern** - this is a regular expression to find the page number.  Example, if the postings_url is "https://jobpostings.alberta.ca/search/?q=&sortColumn=referencedate&sortDirection=desc&startrow=1", then the page_pattern would likely be ```"(https://jobpostings.alberta.ca/search/\\?q=&sortColumn=referencedate&sortDirection=desc&startrow=)(\\d+)"```  Basically matching the whole URL except for the actual "page number" or "offset" value.  Leave the page_pattern empty if the site does not show pages
- **page_group** - the regular expression "group" that hold the page number or offset value.  In the above this would be the ```(\\d+)``` part, but it is the second "group", so the value here should be "2".  It will likely be "2" in most cases.
- **page_type** - the method of paging used.  This should be "page" if the number indicates page 1, page 2, page 3, etc. with each page having X number of rows.  If the value instead indicates something like "startrow=25" or "offset=100", then the page_type value should be "offset".  This field is used to indicate how the system determines what the next page should be.  For instance, consider the first page of results shows the first 25 jobs.  The next page value could be "2" or "26".

- **selector_jobs_container** - The CSS selector for the HTML container for the job listings on the listings page.  This might be "div.job-listings", or "table#results tbody", or something similar.
- **selector_job_links** - The CSS selector for the anchor tags that contains the link to the details page.  This might be simply "a", or something more complex like ".job-item a.title" or "tr td.title a"
- **selector_job_title** - The CSS selector on the job detail page where the title of the job can be found.  This might be something clear like "div.job-title", or it might be obtuse like "div.job > div > ul > li:first-child"
- **selector_job_id** - The CSS selector on the job detail page to indicate the job ID as used by the site.  This may be blank if not used.
- **selector_location** - The CSS selector on the job detail page to indicate the job location / city.  This may be blank if not used.
- **selector_job_description** - The CSS selector on the job detail page to indicate the job description.  This value may be very specific, or may be broad and encapsulate the title, location, and other details.  It is important to make this value as accurate as possible to get just the job description.  Any other details may introduce keywords that reduce the scoring probablilities.

## Limitations

- The `sites.json` file is a small list of initial sites.  So the initial list of jobs may not be very large. I'm averaging around 300 job postings each run, keeping in mind that a small subset of these are not relevant to my field.  However, it is interesting to note that some postings I would not consider have a high keyword match.  For instance in my case I am a senior software developer, but a "judicial clerk" role had a high match for me.  Being a law clerk was NOT on my radar at all, but maybe...

- Sites that do client side rendering of content cannot be scraped using the current technique.  You need to be able to do an HTTP GET and see the relevant content in that output.  If instead you only see a ```<script>``` tag with javascript that then fetches and creates the content, this approach will not work.  

- Duplication.  While the system attempts to find existing jobs when examining a job record, there are a number of factors that can lead to a job posting being stored more than once.  For instance, if the same job posting were posted to Indeed and Glassdoor, or if a site uses a variable in their URL - perhaps a timestamp - so that the URL is always different.  This means that the current system can see duplication of job postings.  Effort is needed here to help reduce this.  One option might be to use the "company" and "title" as a sort of unique key, but the "company" value may not be available on the detail page for some sites.

- JobSpy - At the moment using the proxies with the JobSpy tool results in errors.  I have not gotten to the bottom of this yet.  Not specifying the proxy list allows JobSpy to run, but it is then using your local IP which could lead to issues.

- Job Relevance.  By default the routine grabs all job postings it can see without any searches.  That means you are as likely to see a "Senior Python Developer" role right beside a "Junior Electrician" role. 

- Job Relevance (part II).  The JobSpy project requires search terms.  This limits the number of job postings it finds.  I originally used a `search_terms.txt` file to list the desired terms, but have shifted this into a hardcoded list (see line #8 in the `update_jobs.py` script).  This list of search terms is relevant to me.  You should replace this list with something that is relevant to you.  JobSpy is run once for each search term you specify, so the more you list the longer the process takes.

- Keywords.  The keywords are not aware of context.  Essentially we are splitting the content into individual words, and removing "stop words" ('a', 'the', 'I', 'we', etc.).  This leaves words like 'team', or 'experience', or 'southwest', which may not be especially relevant to the meaning of the content.  Some work can be done here to improve or capture the relevance of the keywords and use that information for an improved scoring.

- Scoring.  The scoring routine is not the best yet.  

    I originally used LLMs and various NLP based routines to generate the scores.  But the results were not great.  The LLM routine was a subjective evaluation of how well the resume fit the job description, and generated questionable results.  The NLP based routines evaluated how "similar" the job posting was to the resume, not taking into account symantic meanings.  When symantic meanings were attempted, we ended up matching how similar the resume was to the job description, again giving questionable results.

    At the moment, we simply look at the keywords.  If we find 100 keywords for the resume, and 25 of those can be found in a job description, then the "score" for that job posting is %25 percent.  This is overly simplistic, but seems to be more relevant than the other scoring attempts.

- 7 Days.  I have the code automatically purge jobs that are older than seven days.  This can be adjusted if needed.  If jobs are being scanned/loaded each day and you are looking to generate the quick report, then older jobs can be considered "already seen", or "possibly filled or innundated already".


## Future Steps

1. I want to explore [Playwright](https://playwright.dev/python/docs/intro) or Selenium and see if I can make use of the same CSS selectors to extract information.  If successful this would allow the tool be used for sites that do client side content rendering.
1. Scoring improvements.  I want to find better scoring methods.  There are more advanced NLP tools that can be applied here, and AI or LLMs may be used in a better manner than my first attempts.
1. Web Frontend.  I want to introduce a web front end to better manage the tool and allow multiple users of the system.  User management would allow user specific search terms and multiple resumes.
1. Better separation of the tasks.  Data collection, Data Analysis, and Data Presentation are all separate tasks.  The data collection can be moved to a cron job and better managed in terms of timings and can be run independently of the analysis / presentation processes.
