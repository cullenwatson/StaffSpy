import logging
import os
import pickle
import re
import sys
from datetime import datetime
from dateutil.parser import parse

import requests
import tldextract
from selenium import webdriver
from selenium.common.exceptions import WebDriverException


logger = logging.getLogger("StaffSpy")
logger.propagate = False
if not logger.handlers:
    logger.setLevel(logging.INFO)
    console_handler = logging.StreamHandler()
    format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    formatter = logging.Formatter(format)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)


def set_csrf_token(session):
    csrf_token = session.cookies["JSESSIONID"].replace('"', "")
    session.headers.update({"Csrf-Token": csrf_token})
    return session


def extract_base_domain(url: str):
    extracted = tldextract.extract(url)
    base_domain = "{}.{}".format(extracted.domain, extracted.suffix)
    return base_domain


def create_email(first, last, domain):
    first = "".join(filter(str.isalpha, first))
    last = "".join(filter(str.isalpha, last))
    return f"{first.lower()}.{last.lower()}@{domain}"


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
        logger.debug("No browser found for selenium")
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
    if not session_file or not os.path.exists(session_file):
        session = login()
        if not session:
            sys.exit("Failed to log in.")
        if session_file:
            save_session(session, session_file)
    else:
        with open(session_file, "rb") as f:
            data = pickle.load(f)
            session = requests.Session()
            session.cookies.update(data["cookies"])
            session.headers.update(data["headers"])
    return session


def parse_date(date_str):
    formats = ["%b %Y", "%Y"]
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    return None


def parse_duration(duration):
    from_date = to_date = None
    dates = duration.split(" · ")
    if len(dates) > 1:
        date_range, _ = duration.split(" · ")
        dates = date_range.split(" - ")
        from_date_str = dates[0]
        to_date_str = dates[1] if dates[1] != "Present" else None
        from_date = parse_date(from_date_str) if from_date_str else None
        to_date = parse_date(to_date_str) if to_date_str else None

    return from_date, to_date


def set_logger_level(verbose: int = 0):
    """
    Adjusts the logger's level. This function allows the logging level to be changed at runtime.

    Parameters:
    - verbose: int {0, 1, 2} (default=0, no logs)
    """
    if verbose is None:
        return
    level_name = {2: "DEBUG", 1: "INFO", 0: "WARNING"}.get(verbose, "INFO")
    level = getattr(logging, level_name.upper(), None)
    if level is not None:
        logger.setLevel(level)
    else:
        raise ValueError(f"Invalid log level: {level_name}")


def parse_dates(date_str):
    regex = r"(\b\w+ \d{4}|\b\d{4}|\bPresent)"
    matches = re.findall(regex, date_str)

    start_date, end_date = None, None
    if matches:
        if "Present" in matches:
            if len(matches) == 1:
                start_date = None
                end_date = None
            else:
                # Extract only the date part to avoid including time
                start_date = parse(matches[0]).date()
                end_date = None
        else:
            if len(matches) == 2:
                start_date = parse(matches[0]).date()
                end_date = parse(matches[1]).date()
            elif len(matches) == 1:
                start_date = parse(matches[0]).date()

    return start_date, end_date


if __name__ == "__main__":
    p = parse_dates("May 2018 - Jun 2024")
