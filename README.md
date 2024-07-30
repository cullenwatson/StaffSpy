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
from staffspy import scrape_staff, SolverType
from pathlib import Path
session_file = Path(__file__).resolve().parent / "session.pkl"

staff = scrape_staff(
    company_name="openai",
    search_term="software engineer",
    location="london",
    extra_profile_data=True, # fetch all past experiences, schools, & skills
    
    # login credentials (remove these to sign in with browser)
    username="myemail@gmail.com",
    password="mypassword",
    
    # in case hit with captcha on sign-in
    solver_api_key="CAP-6D6A8CE981803A309A0D531F8B4790BC",
    solver_service=SolverType.CAPSOLVER,

    max_results=50, # can go up to 1000
    session_file=str(session_file), # save login cookies to only log in once (lasts a week or so)
    log_level=1, # 0 for no logs
)
filename = "staff.csv"
staff.to_csv(filename, index=False)
```

### Two login methods

#### Requests login
If you pass in a ```username``` & ```password```, it will sign in via LinkedIn api (you should disable 2fa for this method). If hit with a captcha, you need to pass ```capsolver_api_key``` for the third-party service to solve it. 


#### Browser login

If that fails or you rather use a browser, install the browser add-on to StaffSpy .

```pip install staffspy[browser]```

Do not pass the ```username``` & ```password``` params, then a browser will open to sign in to LinkedIn on the first sign-in. Press enter after signing in to begin scraping.

### Output
| profile_id     | name          | first_name | last_name | location                                 | age | position                                   | followers | connections | premium | company | past_company1 | past_company2 | school                                         | extra_school                   | skill1    | skill2      | skill3     | is_connection | premium | creator | potential_email                               | profile_link                                | profile_photo |
|----------------|---------------|------------|-----------|------------------------------------------|-----|--------------------------------------------|-----------|-------------|---------|---------|---------------|---------------|-----------------------------------------------|-------------------------------|-----------|-------------|------------|---------------|----------|---------|----------------------------------------------|---------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------|
| javiersierra2102 | Javier Sierra | Javier     | Sierra    | London, England, United Kingdom           | 39  | Software Engineer                          | 735       | 725         | FALSE   | OpenAI  | Meta           | Oculus VR     | Hult International Business School            | Universidad Simón Bolívar     | Java      | JavaScript  | C++        | FALSE         | FALSE    | FALSE   | javier.sierra@openai.com, jsierra@openai.com | https://www.linkedin.com/in/javiersierra2102 | https://media.licdn.com/dms/image/C4D03AQHEyUg1kGT08Q/profile-displayphoto-shrink_800_800/0/1516504680512?e=1727913600&v=beta&t=3enCmNDBtJ7LxfbW6j1hDD8qNtHjO2jb2XTONECxUXw |
| dougli          | Douglas Li    | Douglas    | Li        | London, England, United Kingdom           | 37  | @ OpenAI UK, previously at Meta            | 583       | 401         | FALSE   | OpenAI  | Shift Lab      | Facebook      | Washington University in St. Louis            |                               | Java      | Python      | JavaScript | FALSE         | TRUE     | FALSE   | douglas.li@openai.com, dli@openai.com        | https://www.linkedin.com/in/dougli           | https://media.licdn.com/dms/image/D4E03AQETmRyb3_GB8A/profile-displayphoto-shrink_800_800/0/1687996628597?e=1727913600&v=beta&t=HRYGJ4RxsTMcPF1YcSikXlbz99hx353csho3PWT6fOQ |
| nkartashov      | Nick Kartashov| Nick       | Kartashov | London, England, United Kingdom           | 33  | Software Engineer                          | 2186      | 2182        | TRUE    | OpenAI  | Google         | DeepMind      | St. Petersburg Academic University            | Bioinformatics Institute      | Teamwork  | Java        | Haskell    | FALSE         | FALSE    | FALSE   | nick.kartashov@openai.com, nkartashov@openai.com | https://www.linkedin.com/in/nkartashov      | https://media.licdn.com/dms/image/D4E03AQEjOKxC5UgwWw/profile-displayphoto-shrink_800_800/0/1680706122689?e=1727913600&v=beta&t=m-JnG9nm0zxp1Z7njnInwbCoXyqa3AN-vJZntLfbzQ4 |




### Parameters for `scrape_staff()`

```plaintext
Optional 
├── company_name (str): 
|    company identifier on linkedin, will search for that company if that company id does not exist
|    e.g. openai from https://www.linkedin.com/company/openai
|
├── user_id (str): 
|    alternative to company_name, provide user identifier on linkedin, will find this user's company and then proceed
|    e.g. dougmcmillon from https://www.linkedin.com/in/dougmcmillon
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
│
├── session_file (str): 
|    file path to save session cookies, so only one manual login is needed.
|    can use mult profiles this way
│
├── username (str): 
|    linkedin account email
│
├── password (str): 
|    linkedin account password
|
├── solver_service (SolverType): 
|    solves the captcha using the desired service - either CapSolver, or 2Captcha (lower quality)
|
├── solver_api_key (str): 
|    api key for the solver provider
│
├── log_level (int): 
|    Controls the verbosity of the runtime printouts 
|    (0 prints only errors, 1 is info, 2 is all logs. Default is 0.)
```

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
├── Employment History
│   ├── company
│   ├── past_company1
│   ├── past_company2
│   ├── school
│   ├── extra_school
│   ├── top_skill_1
│   ├── top_skill_2
│   └── top_skill_3
│
├── Status
│   ├── influencer
│   ├── creator
│   ├── premium
│   └── is_connection
│
├── Visuals
│   └── profile_photo
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
### LinkedIn notes
    - only 1000 max results per search
    - extra_profile_data increases runtime by O(n)

## Frequently Asked Questions

---

**Q: Can I get my account banned?**  
**A:** It is a possibility, although there are no recorded incidents. Let me know if you are the first.

---

**Q: Scraped 999 staff members, with 869 hidden LinkedIn Members?**  
**A:** It means your LinkedIn account is bad. Not sure how they classify it but unverified email, new account, low connections and a bunch of factors go into it.

---

**Q: Encountering issues with your queries?**  
**A:** If problems
persist, [submit an issue](https://github.com/cullenwatson/StaffSpy/issues).

---
