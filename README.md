**StaffSpy** is a staff scraper library for LinkedIn.

## Features

- Scrapes staff from a company on **LinkedIn**
- Obtains skills, experiences, certifications & more
- Aggregates the employees in a Pandas DataFrame

### Installation

```
pip install -U staffspy
```

_Python version >= [3.10](https://www.python.org/downloads/release/python-3100/) required_


### Usage

```python
from staffspy import scrape_jobs

staff = scrape_staff(
    company="openai",
    results_wanted=20,
    
    # optional filters
    # search_term="software engineer",
    # location="Dallas, TX",
    # num_threads=10
)
print(f"Found {len(staff)} staff")
print(staff.head())
staff.to_csv("staff.csv", index=False)
```
A browser will open to sign in to LinkedIn. Press enter after signing in to begin scraping. Ctrl-c to stop scraping.

### Staff Schema

```plaintext
Staff
├── id
├── name
├── position
├── profile_id
├── first_name
├── last_name
├── company
├── school
├── location
├── followers
├── connections
├── premium
├── creator
├── influencer
├── skills
├── profile_link
├── profile_photo
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
**A:** It is a possiblity, although there are no recorded incidents. Let me know if you are the first.

---

**Q: Encountering issues with your queries?**  
**A:** If problems
persist, [submit an issue](https://github.com/cullenwatson/StaffSpy/issues).

---
