#!/bin/python3

import mimetypes
import os
import sys
from jobscrape.analyzer import Analyzer
from jobscrape.db import DB, Job
from pypdf import PdfReader

if len(sys.argv) < 2:
    print('Usage:')
    print('    ./compare /path/to/resume.md')
    sys.exit()

source_file = sys.argv[1]
if not os.path.exists(source_file):
    print(f'File not found at {source_file}')
    sys.exit(1)


content = ""
mtype, encoding = mimetypes.guess_type(source_file)
if mtype == 'application/pdf':
    reader = PdfReader(source_file) 
    for page in reader.pages:
        content += " "
        content += page.extract_text()
else:
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


output = "<html><head><title>Quick Report</title></head><body>"
output += "<table><thead><th>Title</th><th>Score</th></thead><tbody>"

# Print or use the top 20 items
for item in top_20_items:
    score = int(item['score'] * 100) / 100
    output += "<tr>"
    output += f'<td><a href="{item["url"]}" target="_blank">{item["title"]}</a></td>'
    output += f'<td>{score}</td>'
    output += '</tr>'

    print(f"Job ID: {item['job_id']}, Title: {item['title']}, Score: {item['score']}")

with open('quick_report.html', 'w') as f:
    f.write(output)


