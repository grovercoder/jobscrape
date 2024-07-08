#!/bin/python3

import sys
from jobscrape.analyzer import Analyzer
from jobscrape.db import DB, Job

if len(sys.argv) < 2:
    print('Usage:')
    print('    ./compare /path/to/resume.md')
    sys.exit()

source_file = sys.argv[1]

content = ""
with open(source_file, 'r') as f:
    content = f.read()

analyzer = Analyzer()

resume_keywords = analyzer.extract_keywords(content)

db = DB()
session = db.get_session()
jobs = Job.get_jobs_with_keywords(session, resume_keywords)

rk = set(resume_keywords)
items = []

for j in jobs:
    jk = set([job_keyword.keyword.keyword for job_keyword in j.keywords])
    fk = rk.intersection(jk)
    
    score = len(fk) / len(rk) * 100 

    items.append({
        "job_id": j.id,
        "source": j.source,
        "title": j.title,
        "url": j.url,
        "score": score
    })

sorted_items = sorted(items, key=lambda x: x['score'], reverse=True)


# Restrict to the top 20 entries
top_20_items = sorted_items[:20]

# Print or use the top 20 items
for item in top_20_items:
    print(f"Job ID: {item['job_id']}, Title: {item['title']}, Score: {item['score']}")

