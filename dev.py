import acfinder as ac
import cProfile
import pstats
import io 
import sqlite3
import requests
import json
import re
import os
import csv
import smtplib
import datetime
from bs4 import BeautifulSoup
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def profile():
    profile = cProfile.Profile()
    profile.enable()
    main()
    profile.disable
    s = io.StringIO()
    ps = pstats.Stats(profile, stream=s).sort_stats("cumulative")
    ps.print_stats(.01)
    print(s.getvalue())

def test_scrape_articles(target_company):
    ac.create_companies_table()
    create_articles_table()
    companies = ac.get_companies()
    articles = []
    for company in companies:
        if company.company_name == target_company:
            request = requests.get(company.url, headers={"user-agent": "Mozilla/5.0"})
            soup = BeautifulSoup(request.text, "html.parser")
            tags = [tag.text.strip() for tag in soup.select(company.selector)]
            for tag in tags:
                print(tag)

def create_articles_table():
    conn = sqlite3.connect("acfinder.db")
    cur = conn.cursor()
    cur.execute("DROP TABLE IF EXISTS articles")
    cur.execute("CREATE TABLE articles (company_name text, date text, headline text)")
    conn.commit()
    cur.close()

test_scrape_articles("Air Liquide")
