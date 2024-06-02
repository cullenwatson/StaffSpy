**StaffSpy** is a staff scraper library for LinkedIn companies.

## Features

- Scrapes all staff from a company on **LinkedIn**
- Aggregates the employees in a Pandas DataFrame

### Installation

```
pip install -U staffspy
```

_Python version >= [3.10](https://www.python.org/downloads/release/python-3100/) required_


### Usage

```python
from staffspy import scrape_staff
from pathlib import Path
session_file = Path(__file__).resolve().parent / "session.pkl"

staff = scrape_staff(
    company="openai",
    session_file=session_file
    
    # optional filters
    # search_term="software engineer",
    # location="Dallas, TX",
    # results_wanted=20,
)
print(f"Found {len(staff)} staff")
print(staff.head())
staff.to_csv("jobs.csv", index=False)
```
A browser will open to sign in to LinkedIn on the first sign-in. Press enter after signing in to begin scraping. Ctrl-c to stop scraping.

### Parameters for `scrape_staff()`

```plaintext
├── company_name (str): 
|    company identifier on linkedin 
|    e.g. openai from https://www.linkedin.com/company/openai
│
├── profile_details (bool)
|    fetches most recent company, school,
|    locations, # of connections/followers, bio, profile link, pfp
│
├── num_threads (int)
|    speed of the scraping, default 10
│
├── max_results (int): 
|    number of employees to fetch, max is 1000 imposed by linkedin
│
├── session_file (str): 
|    file path to save session cookies, so only one login is needed.
|    can use mult profiles this way
│

### Staff Schema

```plaintext
Staff
├── name
├── username
├── about
├── skills
├── location
├── experiences
│   ├── position
│   ├── company
│   ├── location
│   ├── duration
│   ├── from_date
│   └── to_date
├── educations
    ├── school_name
    ├── degree
    ├── location
    ├── duration
    ├── from_date
    └── to_date
```


## Frequently Asked Questions

---

**Q: Can I get my account banned?**  
**A:** It is a possiblity, although there are no recorded incidents. Let me know if you are the first!

---

**Q: Encountering issues with your queries?**  
**A:** If problems
persist, [submit an issue](https://github.com/cullenwatson/StaffSpy/issues).

---
