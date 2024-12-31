<img width="640" alt="3FAD4652-488F-4F6F-A744-4C2AA5855E92" src="https://github.com/user-attachments/assets/73b701ff-2db8-4d72-9ad3-42b7e1db537f">

**StaffSpy** is a staff scraper library for LinkedIn.

_why pay $100/mo for LSN when you could do it for free and get a nice csv to go along with it?_

## Features

- Scrapes staff from a company on **LinkedIn**
- Obtains skills, experiences, certifications & more
- Or fetch individuals users / comments on posts
- Aggregates the employees in a Pandas DataFrame

[Video Guide for StaffSpy](https://youtu.be/DNFmjvpZBTs) - _updated for release v0.2.18_

### Installation

```
pip install -U staffspy[browser]
```

_Python version >= [3.10](https://www.python.org/downloads/release/python-3100/) required_

### Usage

```python
from staffspy import LinkedInAccount, SolverType, DriverType, BrowserType

account = LinkedInAccount(
    # if issues with webdriver, specify its exact location
    # driver_type=DriverType(
    #     browser_type=BrowserType.CHROME,
    #     executable_path="/Users/pc/chromedriver-mac-arm64/chromedriver"
    # ),

    session_file="session.pkl", # save login cookies to only log in once (lasts a week or so)
    log_level=1, # 0 for no logs
)

# search by company
staff = account.scrape_staff(
    company_name="openai",
    search_term="software engineer",
    location="london",
    extra_profile_data=True, # fetch all past experiences, schools, & skills
    max_results=50, # can go up to 1000
)
# or fetch by user ids
users = account.scrape_users(
    user_ids=['williamhgates', 'rbranson', 'jeffweiner08']
)

# fetch all comments on two of Bill Gates' posts 
comments = account.scrape_comments(
    ['7252421958540091394','7253083989547048961']
)

# fetch company details
companies = account.scrape_companies(
    company_names=['openai', 'microsoft']
)

staff.to_csv("staff.csv", index=False)
users.to_csv("users.csv", index=False)
comments.to_csv("comments.csv", index=False)
companies.to_csv("companies.csv", index=False)
```

#### Browser login

If you rather use a browser to log in, install the browser add-on to StaffSpy .

`pip install staffspy[browser]`

If you do not pass the `username` & `password` params, then a browser will open to sign in to LinkedIn on the first sign-in. Press enter after signing in to begin scraping.

### Output

| profile_id       | name           | first_name | last_name | location                        | age | position                        | followers | connections | company | past_company1 | past_company2 | school1                             | school2                    | skill1   | skill2     | skill3     | is_connection | premium | creator | potential_email                                  | profile_link                                 | profile_photo                                                                                                                                                               |
| ---------------- | -------------- | ---------- | --------- | ------------------------------- | --- | ------------------------------- | --------- | ----------- | ------- | ------------- | ------------- | ---------------------------------- | ------------------------- | -------- | ---------- | ---------- | ------------- | ------- | ------- | ------------------------------------------------ | -------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| javiersierra2102 | Javier Sierra  | Javier     | Sierra    | London, England, United Kingdom | 39  | Software Engineer               | 735       | 725         | OpenAI  | Meta          | Oculus VR     | Hult International Business School | Universidad Simón Bolívar | Java     | JavaScript | C++        | FALSE         | FALSE   | FALSE   | javier.sierra@openai.com, jsierra@openai.com     | https://www.linkedin.com/in/javiersierra2102 | https://media.licdn.com/dms/image/C4D03AQHEyUg1kGT08Q/profile-displayphoto-shrink_800_800/0/1516504680512?e=1727913600&v=beta&t=3enCmNDBtJ7LxfbW6j1hDD8qNtHjO2jb2XTONECxUXw |
| dougli           | Douglas Li     | Douglas    | Li        | London, England, United Kingdom | 37  | @ OpenAI UK, previously at Meta | 583       | 401         | OpenAI  | Shift Lab     | Facebook      | Washington University in St. Louis |                           | Java     | Python     | JavaScript | FALSE         | TRUE    | FALSE   | douglas.li@openai.com, dli@openai.com            | https://www.linkedin.com/in/dougli           | https://media.licdn.com/dms/image/D4E03AQETmRyb3_GB8A/profile-displayphoto-shrink_800_800/0/1687996628597?e=1727913600&v=beta&t=HRYGJ4RxsTMcPF1YcSikXlbz99hx353csho3PWT6fOQ |
| nkartashov       | Nick Kartashov | Nick       | Kartashov | London, England, United Kingdom | 33  | Software Engineer               | 2186      | 2182        | OpenAI  | Google        | DeepMind      | St. Petersburg Academic University | Bioinformatics Institute  | Teamwork | Java       | Haskell    | FALSE         | FALSE   | FALSE   | nick.kartashov@openai.com, nkartashov@openai.com | https://www.linkedin.com/in/nkartashov       | https://media.licdn.com/dms/image/D4E03AQEjOKxC5UgwWw/profile-displayphoto-shrink_800_800/0/1680706122689?e=1727913600&v=beta&t=m-JnG9nm0zxp1Z7njnInwbCoXyqa3AN-vJZntLfbzQ4 |


### Parameters for `LinkedInAccount()`

```plaintext
Optional
├── session_file (str):
|    file path to save session cookies, so only one manual login is needed.
|    can use mult profiles this way
|
| For automated login
├── username (str):
|    linkedin account email
│
├── password (str):
|    linkedin account password
|
├── driver_type (DriverType):
|    signs in with the given BrowserType (Chrome, Firefox) and executable_path
|
├── solver_service (SolverType):
|    solves the captcha using the desired service - either CapSolver, or 2Captcha (worse of the two)
|
├── solver_api_key (str):
|    api key for the solver provider
│
├── log_level (int):
|    Controls the verbosity of the runtime printouts
|    (0 prints only errors, 1 is info, 2 is all logs. Default is 0.)
```

### Parameters for `scrape_staff()`

```plaintext
Optional
├── company_name (str):
|    company identifier on linkedin, will search for that company if that company id does not exist
|    e.g. openai from https://www.linkedin.com/company/openai
|
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
```

### Parameters for `scrape_users()`

```plaintext
├── user_ids (list):
|    user ids to scrape from
|     e.g. dougmcmillon from https://www.linkedin.com/in/dougmcmillon
```


### Parameters for `scrape_comments()`

```plaintext
├── post_ids (list):
|    post ids to scrape from
|     e.g. 7252381444906364929 from https://www.linkedin.com/posts/williamhgates_technology-transformtheeveryday-activity-7252381444906364929-Bkls
```


### Parameters for `scrape_companies()`

```plaintext
├── company_names (list):
|    list of company names to scrape details from
|     e.g. ['openai', 'microsoft', 'google']
```


### LinkedIn notes

    - only 1000 max results per search
    - extra_profile_data increases runtime by O(n)
    - if rate limited, the program will stop scraping
    - if using non-browser sign in, turn off 2fa

---

## Frequently Asked Questions

---

**Q: Can I get my account banned?**  
**A:** It is a possibility, although there are no recorded incidents. Let me know if you are the first.

---

**Q: Scraped 999 staff members, with 869 hidden LinkedIn Members?**  
A: It means your LinkedIn account is bad. Not sure how they classify it but unverified email, new account, low connections and a bunch of factors go into it.

---

**Q: How to get around the 1000 search limit result?**  
**A:**  I created a case study here: [📊 X Corp Staff Analysis Case Study](https://github.com/cullenwatson/StaffSpy/blob/main/case_studies/x_corp_staff.py)  
       We can block the user after searching and try many different locations and search terms to maximize results.
---



**Q: Exception: driver not found for selenium?**  
**A:** You need chromedriver installed (not the chrome): https://googlechromelabs.github.io/chrome-for-testing/#stable

---

**Q: Encountering issues with your queries?**  
**A:** If problems
persist, [submit an issue](https://github.com/cullenwatson/StaffSpy/issues).


### Staff Schema

```plaintext
Staff
├── Personal Information
│   ├── search_term
│   ├── id
│   ├── name
│   ├── first_name
│   ├── last_name
│   ├── location
│   └── bio
│
├── Professional Details
│   ├── position
│   ├── profile_id
│   ├── profile_link
│   ├── potential_emails
│   └── estimated_age
│
├── Social Connectivity
│   ├── followers
│   ├── connections
│   └── mutuals_count
│
├── Status
│   ├── influencer
│   ├── creator
│   ├── premium
│   ├── open_to_work
│   ├── is_hiring
│   └── is_connection
│
├── Visuals
│   ├── profile_photo
│   └── banner_photo
│
├── Skills
│   ├── name
│   └── endorsements
│
├── Experiences
│   ├── from_date
│   ├── to_date
│   ├── duration
│   ├── title
│   ├── company
│   ├── location
│   └── emp_type
│
├── Certifications
│   ├── title
│   ├── issuer
│   ├── date_issued
│   ├── cert_id
│   └── cert_link
│
└── Educational Background
    ├── years
    ├── school
    └── degree
```
