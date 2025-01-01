""" Script to connect with 10 software engineers daily from random tech companies """

from staffspy import LinkedInAccount, DriverType, BrowserType
import random
import time
from datetime import datetime
import schedule

# List of tech companies to randomly choose from
TECH_COMPANIES = [
    "microsoft",
    "google",
    "apple",
    "meta",
    "amazon",
    "netflix",
    "salesforce",
    "adobe",
    "intel",
    "nvidia",
    "oracle",
    "ibm",
    "vmware",
    "twitter",
    "linkedin",
    "airbnb",
    "uber",
    "stripe",
    "snowflake",
    "databricks",
]


def connect_with_staff():
    print(f"Starting connection run at {datetime.now()}")

    # Initialize LinkedIn account
    account = LinkedInAccount(session_file="session.pkl", log_level=1)

    # Choose a random company
    company = random.choice(TECH_COMPANIES)
    print(f"Selected company: {company}")

    # Connect with 10 users
    account.scrape_staff(
        company_name=company,
        search_term="software engineer",
        max_results=10,
        extra_profile_data=True,
        connect=True,
    )


if __name__ == "__main__":
    # Schedule to run once a day at 10 AM
    schedule.every().day.at("10:00").do(connect_with_staff)

    # Run immediately on script start
    connect_with_staff()

    # Keep the script running
    while True:
        schedule.run_pending()
        time.sleep(60)
