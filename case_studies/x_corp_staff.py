"""
CASE STUDY: X CORP EMPLOYEES
RESULT: We retrieved 2153 profiles out of reported 2800 employees.
results.csv - https://drive.google.com/file/d/1A1QlgG0chMPg4Ac51Dbfy25iDv32Jdo8/view

Strategies to get around LinkedIn 1000 result limit:
1) It blocks the user after searching to prevent it from appearing in future searches
2) it then tries to search by department and location to get more results.

Lastly, it saves the results in CSV files and then combines them into one DataFrame at the end to view the results.
"""

import os
from datetime import datetime
import pandas as pd
import glob


from staffspy import LinkedInAccount

session_file = "session.pkl"
account = LinkedInAccount(session_file=str(session_file), log_level=2)


departments = [
    # Leadership
    "CEO",
    "CFO",
    "CTO",
    "COO",
    "executive",
    "director",
    "vice president",
    "head",
    "lead",
    # Engineering/Tech
    "software",
    "developer",
    "engineer",
    "architect",
    "devops",
    "QA",
    "data",
    "IT",
    "security",
    # Business/Operations
    "sales",
    "account",
    "business development",
    "operations",
    "project manager",
    "product manager",
    # Support Functions
    "HR",
    "recruiter",
    "marketing",
    "finance",
    "legal",
    "accounting",
    "admin",
    "support",
    # Customer-Facing
    "customer success",
    "account manager",
    "sales representative",
    "customer support",
    # Specialists
    "analyst",
    "consultant",
    "coordinator",
    "specialist",
]
locations = [
    "San Francisco",
    "New York",
    "Los Angeles",
    "Seattle",
    "Miami",
    "Boston",
    "Austin",
    "Chicago",
    "Toronto",
    "London",
    "Singapore",
    "Tokyo",
    "Dublin",
]


def save_results(users: pd.DataFrame):
    output_dir = f"output/{company_name}"
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = f"{output_dir}/users_{timestamp}.csv"
    users.to_csv(output_path, index=False)


def scrape_and_save(term=None, location=None):
    users = account.scrape_staff(
        company_name=company_name,
        search_term=term,
        location=location,
        extra_profile_data=True,
        max_results=1000,
        block=True,
    )
    if not users.empty:
        save_results(users)


company_name = "x-corp"

# generic search
for _ in range(5):
    scrape_and_save()

# Search by departments
for department in departments:
    scrape_and_save(term=department)

# Search by locations
for location in locations:
    scrape_and_save(location=location)

# load all csvs into one df
files = glob.glob("output/x-corp/*.csv")
dfs = [pd.read_csv(f) for f in files]
combined_df = pd.concat(dfs, ignore_index=True)

# Filter out hidden profiles
filtered_df = combined_df[combined_df["urn"] != "headless"]
filtered_df = filtered_df[filtered_df["current_company"] == "X"]
filtered_df = filtered_df.drop_duplicates(subset="urn")

# output all unique staff to csv
total_urns = len(filtered_df["urn"])
print(f"Total unique profiles: {total_urns}")
filtered_df.to_csv(
    f"output/{company_name}/final_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
    index=False,
)
