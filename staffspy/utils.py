import os
import pickle
import sys
from datetime import datetime

import requests
from selenium import webdriver
from selenium.common.exceptions import WebDriverException


def set_csrf_token(session):
    csrf_token = session.cookies["JSESSIONID"].replace('"', "")
    session.headers.update({"Csrf-Token": csrf_token})
    return session


def get_webdriver():
    for browser in [webdriver.Firefox, webdriver.Chrome]:
        try:
            return browser()
        except WebDriverException:
            continue
    return None


def login():
    driver = get_webdriver()

    if driver is None:
        print("No browser found for selenium")
        sys.exit(1)

    driver.get("https://linkedin.com/login")
    input("Press enter after logged in")

    selenium_cookies = driver.get_cookies()
    driver.quit()

    session = requests.Session()
    for cookie in selenium_cookies:
        session.cookies.set(cookie["name"], cookie["value"])

    user_agent = "Mozilla/5.0 (Linux; U; Android 4.4.2; en-us; SCH-I535 Build/KOT49H) AppleWebKit/534.30 (KHTML, like Gecko) Version/4.0 Mobile Safari/534.30"
    session.headers.update(
        {
            "User-Agent": user_agent,
            "X-RestLi-Protocol-Version": "2.0.0",
            "X-Li-Track": '{"clientVersion":"1.13.1665"}',
        }
    )

    session = set_csrf_token(session)
    return session


def save_session(session, session_file):
    data = {"cookies": session.cookies, "headers": session.headers}
    with open(session_file, "wb") as f:
        pickle.dump(data, f)


def load_session(session_file):
    if not os.path.exists(session_file):
        session = login()
        if not session:
            sys.exit("Failed to log in.")
        save_session(session, session_file)
    else:
        with open(session_file, "rb") as f:
            data = pickle.load(f)
            session = requests.Session()
            session.cookies.update(data["cookies"])
            session.headers.update(data["headers"])
    return session


def parse_duration(duration):
    from_date = to_date = None
    dates = duration.split(" · ")
    if len(dates) > 1:
        date_range, _ = duration.split(" · ")
        dates = date_range.split(" - ")
        from_date_str = dates[0]
        to_date_str = dates[1] if dates[1] != "Present" else None
        from_date = datetime.strptime(from_date_str, "%b %Y") if from_date_str else None
        to_date = datetime.strptime(to_date_str, "%b %Y") if to_date_str else None

    return from_date, to_date
