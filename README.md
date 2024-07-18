<img width="640" alt="3FAD4652-488F-4F6F-A744-4C2AA5855E92" src="https://github.com/user-attachments/assets/73b701ff-2db8-4d72-9ad3-42b7e1db537f">

**StaffSpy** is a staff scraper library for LinkedIn.

## Features

- Scrapes staff from a company on **LinkedIn**
- Obtains skills, experiences, certifications & more
- Aggregates the employees in a Pandas DataFrame

[Video Guide for StaffSpy](https://youtu.be/qAqaqwhil7E) - _updated for release v0.1.4_

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
    company_name="openai",
    search_term="software engineer", # optional
    location="london", # optional
    extra_profile_data=True, # fetch all past experiences, schools, & skills

    max_results=50, # can go up to 1000
    session_file=str(session_file), # save browser cookies
    log_level=1,
)
filename = f"staff.csv"
staff.to_csv(filename, index=False)
```
A browser will open to sign in to LinkedIn on the first sign-in. Press enter after signing in to begin scraping.

### Partial Output
| name           | position                                   | profile_id          | first_name | last_name | potential_email              | company | school                                         | location                                 | followers | connections | premium |
|----------------|--------------------------------------------|---------------------|------------|-----------|------------------------------|---------|-----------------------------------------------|------------------------------------------|-----------|-------------|---------|
| Andrei Gheorghe| Product Engineer                           | idevelop            | Andrei     | Gheorghe  | andrei.gheorghe@openai.com   | OpenAI  | Universitatea „Politehnica” din București    | London, England, United Kingdom           | 723       | 704         | FALSE   |
| Douglas Li     | @ OpenAI UK, previously at Meta            | dougli              | Douglas    | Li        | douglas.li@openai.com        | OpenAI  | Washington University in St. Louis          | London, England, United Kingdom           | 533       | 401         | TRUE    |
| Javier Sierra  | Software Engineer                          | javiersierra2102    | Javier     | Sierra    | javier.sierra@openai.com     | OpenAI  | Hult International Business School          | London, England, United Kingdom           | 726       | 717         | FALSE   |


### Parameters for `scrape_staff()`

```plaintext
├── company_name (str): 
|    company identifier on linkedin 
|    e.g. openai from https://www.linkedin.com/company/openai

Optional 
├── search_term (str): 
|    staff title to search for
|    e.g. software engineer
|
├── location (str): 
|    location the staff resides
|    e.g. london
│
├── extra_profile_data (bool)
|    fetches educations, experiences, skills, certifications (Default false)
│
├── max_results (int): 
|    number of staff to fetch, default/max is 1000 for a search imposed by LinkedIn
│
├── session_file (str): 
|    file path to save session cookies, so only one manual login is needed.
|    can use mult profiles this way
│
├── log_level (int): 
|    Controls the verbosity of the runtime printouts 
|    (0 prints only errors, 1 is info, 2 is all logs. Default is 0.)
```

### Staff Schema
```plaintext
Staff
├── search_term
├── id
├── name
├── bio
|
├── position
├── profile_id
├── profile_link
├── first_name
├── last_name
├── potential_email
|
├── followers
├── connections
├── mutual_connections
|
├── location
├── company
├── school
|
├── influencer
├── creator
├── premium
├── profile_photo
|
├── skills
│   ├── name
│   └── endorsements
├── experiences
│   ├── from_date
│   ├── to_date
│   ├── duration
│   ├── title
│   ├── company
│   ├── location
│   └── emp_type
├── certifications
│   ├── title
│   ├── issuer
│   ├── date_issued
│   ├── cert_id
│   └── cert_link
└── schools
    ├── years
    ├── school
    └── degree
```
```
└── LinkedIn notes:
|    - only 1000 max results per search
|    - extra_profile_data increases runtime by O(n)
```

## Frequently Asked Questions

---

**Q: Can I get my account banned?**  
**A:** It is a possibility, although there are no recorded incidents. Let me know if you are the first.

---

**Q: Scraped 999 staff members, with 869 hidden LinkedIn Members?**  
**A:** It means your LinkedIn account is bad. Not sure how they classify it but unverified email and a bunch of factors go into it.

---

**Q: Encountering issues with your queries?**  
**A:** If problems
persist, [submit an issue](https://github.com/cullenwatson/StaffSpy/issues).

---
