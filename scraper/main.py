import os
import time
import requests
import psycopg2
from datetime import datetime

POSTGRES_DB = os.getenv("POSTGRES_DB")
POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")

COMPANY = "stripe"
API_URL = f"https://boards-api.greenhouse.io/v1/boards/{COMPANY}/jobs"

KEYWORDS = ["devops", "sre", "cloud", "engineer"]

def get_connection():
    return psycopg2.connect(
        host="postgres",
        database=POSTGRES_DB,
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD,
    )

def job_matches(title):
    #print("Job title:", title)
    return any(keyword in title.lower() for keyword in KEYWORDS)

def scrape_greenhouse_api():
    print(f"[{datetime.now()}] Fetching jobs from API...")

    response = requests.get(API_URL)
    print("Status Code:", response.status_code)

    if response.status_code != 200:
        print("Failed to fetch jobs.")
        return

    data = response.json()
    jobs = data.get("jobs", [])

    conn = get_connection()
    cur = conn.cursor()

    inserted_count = 0

    for job in jobs:
        title = job.get("title", "")
        job_id = job.get("id")
        location = job.get("location", {}).get("name", "Unknown")

        if job_matches(title):
            link = f"https://boards.greenhouse.io/{COMPANY}/jobs/{job_id}"

            cur.execute("""
                INSERT INTO jobs (title, company, location, remote, url, source, match_score)
                VALUES (%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT (url) DO NOTHING;
            """, (
                title,
                COMPANY.capitalize(),
                location,
                "remote" in location.lower(),
                link,
                "greenhouse_api",
                75
            ))

            inserted_count += 1
            print(f"Inserted: {title}")

    conn.commit()
    cur.close()
    conn.close()

    print(f"Inserted {inserted_count} matching jobs.")
    print("Scrape complete.\n")

if __name__ == "__main__":
    print("Scraper service started...\n")

    while True:
        try:
            scrape_greenhouse_api()
        except Exception as e:
            print("Error:", e)

        time.sleep(60)  # temporary for testing (change to 3600 later)
