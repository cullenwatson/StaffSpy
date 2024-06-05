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
    search_term="software engineer",
    extra_profile_data=True,

    max_results=50,
    session_file=str(session_file),
    log_level=1,
)
filename = f"staff.csv"
staff.to_csv(filename, index=False)
```
A browser will open to sign in to LinkedIn on the first sign-in. Press enter after signing in to begin scraping.

### Output
| Name              | Position                          | Profile ID                | First Name      | Last Name | Company | School                                     | Location                                | Potential Email                  |
|-------------------|-----------------------------------|---------------------------|-----------------|-----------|---------|--------------------------------------------|-----------------------------------------|----------------------------------|
| Ethan C.          | Software Engineer @ OpenAI        | ethan-c-772952138         | Ethan           | C.        | OpenAI  | University of Southern California          | Los Angeles, California, United States  | ethan.c@openai.com               |
| Pavel K.          | Software Engineer!                | pavel-komlev              | Pavel           | K.        | OpenAI  | Lomonosov Moscow State University (MSU)    | Redmond, Washington, United States      | pavel.k@openai.com               |
| Jason (Qiang) Xu  | Software Engineer                 | jason-qiang-xu-7101b025   | Jason (Qiang)   | Xu        | OpenAI  | Texas A&M University                       | San Francisco, California, United States| jason.xu@openai.com              |


### Parameters for `scrape_staff()`

```plaintext
├── company_name (str): 
|    company identifier on linkedin 
|    e.g. openai from https://www.linkedin.com/company/openai

Optional 
├── search_term (str): 
|    employee title to search for
|    e.g. software engineer
│
├── extra_profile_data (bool)
|    fetches educations, experiences, skills, certifications (Default false)
│
├── max_results (int): 
|    number of employees to fetch, default/max is 1000 for a search imposed by LinkedIn
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
|
├── location
├── company
├── school
|
├── influencer
├── creator
├── premium
|
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


## Frequently Asked Questions

---

**Q: Can I get my account banned?**  
**A:** It is a possiblity, although there are no recorded incidents. Let me know if you are the first.

---

**Q: Encountering issues with your queries?**  
**A:** If problems
persist, [submit an issue](https://github.com/cullenwatson/StaffSpy/issues).

---
