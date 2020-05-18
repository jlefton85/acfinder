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

class Company:
    def __init__(self, company_name, url, selector):
        self.company_name = company_name
        self.url = url
        self.selector = selector

    @classmethod
    def from_tuple(cls, data):
        return cls(data[0], data[1], data[2])

class Article:
    def __init__(self, company_name, date, headline):
        self.company_name = company_name
        self.date = date
        self.headline = headline

    @classmethod
    def from_tuple(cls, data):
        return cls(data[0], data[1], data[2])

    def to_tuple(self):
        return (self.company_name, self.date, self.headline)

KEYWORDS = [
   r"(^|\W)buy(|ing)(s|\W)",
   r"(^|\W)bought\W",
   r"(^|\W)sell(|ing)(s|\W)",
   r"(^|\W)sale(s|\W)",
   r"(^|\W)sold\W",
   r"(^|\W)acqui(re|red|ring|sition)(s|\W)",
   r"(^|\W)divest(|ed|ing|ment|iture)(s|\W)",
   r"(^|\W)invest(|ed|ing)(s|\W)",
   r"(^|\W)merg(e|ed|ing|er)(s|\W)"
]



DIRNAME = os.path.dirname(__file__)
DATE = datetime.today().strftime('%m-%d-%Y')


def main():
    create_companies_table()
    create_articles_table()
    companies = get_companies()
    articles = scrape_articles(companies)
    if articles:
        articles = remove_duplicates(articles)
        store_articles(articles)
        text = write_text(articles)
        html = write_html(articles)
    else:
        text = "No articles found."
    
    write_html(text)
    # send_email(text)


def create_companies_table():
    conn = sqlite3.connect("acfinder.db")
    cur = conn.cursor()
    cur.execute("DROP TABLE IF EXISTS companies")
    cur.execute("CREATE TABLE companies (company_name text, url text, selector text)")
    
    with open("companies.csv", "r") as company_list:
        dr = csv.DictReader(company_list)
        tuples = [(i["company_name"], i["url"], i["selector"]) for i in dr]

    cur.executemany("INSERT INTO companies (company_name, url, selector) VALUES (?, ?, ?)", tuples)
    conn.commit()
    cur.close()


def get_companies():
    conn = sqlite3.connect("acfinder.db")
    cur = conn.cursor()
    cur.execute("SELECT company_name, url, selector FROM companies")
    companies = [Company.from_tuple(company) for company in cur.fetchall()]
    conn.close()
    return companies

def scrape_articles(companies):
    articles = []
    for company in companies:
        request = requests.get(company.url, headers={"user-agent": "Mozilla/5.0"})
        soup = BeautifulSoup(request.text, "html.parser")
        tags = [tag.text.strip() for tag in soup.select(company.selector)]
        for tag in tags:
            for keyword in KEYWORDS:
                match = re.search(keyword, tag)
                if match:
                    article = Article(company.company_name, DATE, tag)
                    articles.append(article)
    return articles

def remove_duplicates(articles):
    conn = sqlite3.connect("acfinder.db")
    cur = conn.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS articles (company_name text, date text, headline text)")
    cur.execute("SELECT company_name, date, headline FROM articles")
    history = [Article.from_tuple(article) for article in cur.fetchall()]
    for article in articles[:]:
        for hist in history:
            if (article.company_name == hist.company_name) and (article.headline == hist.headline):
                articles.remove(article)
    conn.commit()
    conn.close()
    return articles
    
def store_articles(articles):
    conn = sqlite3.connect("acfinder.db")
    cur = conn.cursor()
    for article in articles:
        cur.execute("INSERT INTO articles (company_name, date, headline) VALUES (?, ?, ?)", article.to_tuple())
    conn.commit()
    conn.close()

def write_text(articles):
    text = ""
    for number, article in enumerate(articles):
        text += str(number + 1) + ".) " + article.company_name + "-\n"
        text += article.headline + "\n\n"
    print(text)
    return text


def write_html(articles):
    title = str(DATE + " Report")
    default_html = '''<!doctype html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <title>%s</title>
</head>
<body>
</body>
</html>''' % title

    with open("%s.html" % DATE, "w") as output:
        output.write(default_html)

def send_email():
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login("leftonpythonbot@gmail.com", "Python123")

    msg = MIMEMultipart()

    msg['Subject'] = "Test"
    msg['From'] = "leftonpythonbot@gmail.com"
    msg['To'] = "jlefton85@gmail.com, plefton@coverassociates.com"

    msg.attach(MIMEText(report, 'plain'))

    server.send_message(msg)
    server.quit()

if __name__ == "__main__":
    main()
