import logging
import os
import pickle
import re
from datetime import datetime

import pandas as pd
from typing import Optional
from urllib.parse import quote

import requests
import tldextract
from bs4 import BeautifulSoup
from dateutil.parser import parse
from tenacity import stop_after_attempt, retry_if_exception_type, retry, RetryError

from staffspy.solvers.solver import Solver
from staffspy.utils.driver_type import DriverType, BrowserType
from staffspy.utils.exceptions import BlobException

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


def create_emails(first, last, domain):
    first = "".join(filter(str.isalpha, first)).lower()
    last = "".join(filter(str.isalpha, last)).lower()
    emails = [
        f"{first}.{last}@{domain}",
        f"{first[:1]}{last}@{domain}",
        f"{first[:2]}{last}@{domain}",
        f"{first}{last[:1]}@{domain}",
        f"{first}{last[:2]}@{domain}",
    ]
    return emails


def get_webdriver(driver_type: Optional[DriverType] = None):
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.service import Service as ChromeService
        from selenium.webdriver.firefox.service import Service as FirefoxService
    except ImportError as e:
        raise Exception(
            "install package `pip install staffspy[browser]` to login with browser"
        )

    if driver_type:
        if str(driver_type.browser_type) == str(BrowserType.CHROME):
            if driver_type.executable_path:
                service = ChromeService(executable_path=driver_type.executable_path)
                return webdriver.Chrome(service=service)
            else:
                return webdriver.Chrome()
        elif str(driver_type.browser_type) == str(BrowserType.FIREFOX):
            if driver_type.executable_path:
                service = FirefoxService(executable_path=driver_type.executable_path)
                return webdriver.Firefox(service=service)
            else:
                return webdriver.Firefox()
    else:
        for browser in [webdriver.Chrome, webdriver.Firefox]:
            try:
                return browser()
            except Exception:
                continue
    return None


class Login:

    def __init__(
        self,
        username: str,
        password: str,
        solver: Solver,
        session_file: str,
        driver_type: DriverType = None,
    ):
        (
            self.username,
            self.password,
            self.solver,
            self.session_file,
            self.driver_type,
        ) = (username, password, solver, session_file, driver_type)

    def solve_captcha(self, session, data, payload):
        url = data["challenge_url"]
        r = session.post(url, data=payload)

        soup = BeautifulSoup(r.text, "html.parser")

        code_tag = soup.find("code", id="securedDataExchange")

        logger.info("Searching for captcha blob in linkedin to begin captcha solving")
        if code_tag:
            comment = code_tag.contents[0]
            extracted_code = str(comment).strip('<!--""-->').strip()
            logger.debug("Extracted captcha blob:", extracted_code)
        elif "Please choose a more secure password." in r.text:
            raise Exception(
                "linkedin is requiring a more secure password. reset pw and try again"
            )
        else:
            raise BlobException(
                "blob to solve captcha not found - rerunning the program usually solves this"
            )

        if not self.solver:
            raise Exception(
                "captcha hit - provide solver_api_key and solver_service name to solve or switch to the browser-based login with `pip install staffspy[browser]`"
            )
        token = self.solver.solve(extracted_code, url)
        if not token:
            raise Exception("failed to solve captcha after 10 attempts")

        captcha_site_key = soup.find("input", {"name": "captchaSiteKey"})["value"]
        challenge_id = soup.find("input", {"name": "challengeId"})["value"]
        challenge_data = soup.find("input", {"name": "challengeData"})["value"]
        challenge_details = soup.find("input", {"name": "challengeDetails"})["value"]
        challenge_type = soup.find("input", {"name": "challengeType"})["value"]
        challenge_source = soup.find("input", {"name": "challengeSource"})["value"]
        request_submission_id = soup.find("input", {"name": "requestSubmissionId"})[
            "value"
        ]
        display_time = soup.find("input", {"name": "displayTime"})["value"]
        page_instance = soup.find("input", {"name": "pageInstance"})["value"]
        failure_redirect_uri = soup.find("input", {"name": "failureRedirectUri"})[
            "value"
        ]
        sign_in_link = soup.find("input", {"name": "signInLink"})["value"]
        join_now_link = soup.find("input", {"name": "joinNowLink"})["value"]
        for cookie in session.cookies:
            if cookie.name == "JSESSIONID":
                jsession_value = cookie.value.split("ajax:")[1].strip('"')
                break
        else:
            raise Exception("jsessionid not found, raise issue on GitHub")
        csrf_token = f"ajax:{jsession_value}"
        payload = {
            "csrfToken": csrf_token,
            "captchaSiteKey": captcha_site_key,
            "challengeId": challenge_id,
            "language": "en-US",
            "displayTime": display_time,
            "challengeType": challenge_type,
            "challengeSource": challenge_source,
            "requestSubmissionId": request_submission_id,
            "captchaUserResponseToken": token,
            "challengeData": challenge_data,
            "pageInstance": page_instance,
            "challengeDetails": challenge_details,
            "failureRedirectUri": failure_redirect_uri,
            "signInLink": sign_in_link,
            "joinNowLink": join_now_link,
            "_s": "CONSUMER_LOGIN",
        }
        encoded_payload = {
            key: f'{quote(str(value), "")}' for key, value in payload.items()
        }
        query_string = "&".join(
            [f"{key}={value}" for key, value in encoded_payload.items()]
        )
        response = session.post(
            "https://www.linkedin.com/checkpoint/challenge/verify", data=query_string
        )

        if not response.ok:
            raise Exception(f"verify captcha failed {response.text[:200]}")

    @retry(stop=stop_after_attempt(5), retry=retry_if_exception_type(BlobException))
    def login_requests(self):

        url = "https://www.linkedin.com/uas/authenticate"

        encoded_username = quote(self.username)
        encoded_password = quote(self.password)
        session = requests.Session()
        session.headers = {
            "X-Li-User-Agent": "LIAuthLibrary:44.0.* com.linkedin.LinkedIn:9.29.8962 iPhone:17.5.1",
            "User-Agent": "LinkedIn/9.29.8962 CFNetwork/1496.0.7 Darwin/23.5.0",
            "X-User-Language": "en",
            "X-User-Locale": "en_US",
            "Accept-Language": "en-us",
        }

        response = session.get(url)
        if response.status_code != 200:
            raise Exception(
                f"failed to begin auth process: {response.status_code} {response.text}"
            )
        for cookie in session.cookies:
            if cookie.name == "JSESSIONID":
                jsession_value = cookie.value.split("ajax:")[1].strip('"')
                break
        else:
            raise Exception("jsessionid not found, raise issue on GitHub")
        session.headers["content-type"] = "application/x-www-form-urlencoded"
        csrf_token = f"ajax%3A{jsession_value}"
        payload = f"session_key={encoded_username}&session_password={encoded_password}&JSESSIONID=%22{csrf_token}%22"
        response = session.post(url, data=payload)
        data = response.json()

        if data["login_result"] == "BAD_USERNAME_OR_PASSWORD":
            raise Exception("incorrect username or password")
        elif data["login_result"] == "CHALLENGE":
            self.solve_captcha(session, data, payload)

        session = set_csrf_token(session)
        return session

    def login_browser(self):
        """Backup login method"""
        driver = get_webdriver(self.driver_type)

        if driver is None:
            logger.debug("No browser found for selenium")
            raise Exception("driver not found for selenium")

        driver.get("https://linkedin.com/login")
        input("Press enter after logged in")

        selenium_cookies = driver.get_cookies()
        driver.quit()

        session = requests.Session()
        for cookie in selenium_cookies:
            session.cookies.set(cookie["name"], cookie["value"])

        session = set_csrf_token(session)
        return session

    def save_session(self, session, session_file: str):
        data = {"cookies": session.cookies, "headers": session.headers}
        with open(session_file, "wb") as f:
            pickle.dump(data, f)

    def load_session(self):
        """Load session from session file, otherwise login"""
        session = None
        if not self.session_file or not os.path.exists(self.session_file):
            if self.username and self.password:
                try:
                    session = self.login_requests()
                except RetryError as retry_err:
                    retry_err.reraise()
            else:
                session = self.login_browser()
            if not session:
                raise Exception("Failed to log in.")
            if self.session_file:
                self.save_session(session, self.session_file)
        else:
            with open(self.session_file, "rb") as f:
                data = pickle.load(f)
                session = requests.Session()
                session.cookies.update(data["cookies"])
                session.headers.update(data["headers"])
        session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Linux; U; Android 4.4.2; en-us; SCH-I535 Build/KOT49H) AppleWebKit/534.30 (KHTML, like Gecko) Version/4.0 Mobile Safari/534.30",
                "X-RestLi-Protocol-Version": "2.0.0",
                "X-Li-Track": '{"clientVersion":"1.13.1665"}',
            }
        )
        if not self.check_logged_in(session):
            raise Exception(
                "Failed to log in. Likely outdated session file and cookies have expired. Delete the file and rerun the LinkedAccount() code"
            )
        return session

    def check_logged_in(self, session):
        logger.info("Testing if logged in by checking arbitrary LinkedIn company page")
        try:
            res = session.get(
                "https://www.linkedin.com/voyager/api/organization/companies?q=universalName&universalName=amazon"
            )
            if res.status_code != 200:
                logger.error(f"{res.status_code} status code returned from linkeind")
                return False
        except:
            return False
        logger.info("Account successfully logged in - res code 200")
        return True


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
                start_date = parse(matches[0]).date()
                end_date = None
        else:
            if len(matches) == 2:
                start_date = parse(matches[0]).date()
                end_date = parse(matches[1]).date()
            elif len(matches) == 1:
                start_date = parse(matches[0]).date()

    return start_date, end_date


def extract_emails_from_text(text: str) -> list[str] | None:
    if not text:
        return None
    email_regex = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
    return email_regex.findall(text)


def parse_company_data(json_data, search_term=None):
    company_info = json_data["elements"][0]

    company_name = company_info.get("name", "")
    staff_count = company_info.get("staffCount", None)
    company_type = company_info.get("type", "")
    description = company_info.get("description", "")

    industries_list = [
        ind.get("localizedName", "")
        for ind in company_info.get("companyIndustries", [])
    ]

    headquarter = company_info.get("headquarter", {})
    headquarter_full = f'{headquarter.get("line1", "")}, {headquarter.get("city", "")}, {headquarter.get("country", "")} {headquarter.get("postalCode", "")}'

    logo_data = company_info.get("logo", {})
    vector_image = logo_data.get("image", {}).get("com.linkedin.common.VectorImage", {})
    root_url = vector_image.get("rootUrl", "")
    artifacts = vector_image.get("artifacts", [])

    logo_url = None
    if artifacts:
        first_artifact = artifacts[0]
        file_path = first_artifact.get("fileIdentifyingUrlPathSegment", "")
        logo_url = root_url + file_path

    tracking_info = company_info.get("trackingInfo", {})
    object_urn = tracking_info.get("objectUrn", "")
    internal_id = None
    if object_urn.startswith("urn:li:company:"):
        internal_id = object_urn.split(":")[-1]

    bg_photo = company_info.get("backgroundCoverPhoto", {})
    vector_image = bg_photo.get("com.linkedin.common.VectorImage", {})
    root_url = vector_image.get("rootUrl", "")
    artifacts = vector_image.get("artifacts", [])
    banner_url = None
    if artifacts:
        chosen_artifact = artifacts[0]
        file_segment = chosen_artifact.get("fileIdentifyingUrlPathSegment", "")
        banner_url = root_url + file_segment

    company_df = pd.DataFrame(
        {
            "search_term": [search_term],
            "linkedin_company_id": [internal_id],
            "company_name": [company_name],
            "staff_count": [staff_count],
            "company_type": [company_type],
            "industries": [industries_list],
            "headquarters_address": [headquarter_full],
            "description": [description],
            "logo_url": [logo_url],
            "banner_url": [banner_url],
        }
    )
    return company_df


def clean_df(staff_df):
    if "estimated_age" in staff_df.columns:
        staff_df["estimated_age"] = staff_df["estimated_age"].astype("Int64")
    if "followers" in staff_df.columns:
        staff_df["followers"] = staff_df["followers"].astype("Int64")
    if "connections" in staff_df.columns:
        staff_df["connections"] = staff_df["connections"].astype("Int64")
    if "mutuals" in staff_df.columns:
        staff_df["mutuals"] = staff_df["mutuals"].astype("Int64")
    return staff_df


def upload_to_clay(webhook_url: str, data: pd.DataFrame):
    records = data.to_dict("records")

    responses = []
    for i, row in enumerate(records, start=1):
        try:
            response = requests.post(
                webhook_url, headers={"Accept": "application/json"}, json=row
            )
            response.raise_for_status()
            logger.info(f"Uploaded row to Clay: {i} / {len(records)}")
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to upload row to Clay: {str(e)}")
            responses.append({"error": str(e), "data": row})

    return responses


if __name__ == "__main__":
    p = parse_dates("May 2018 - Jun 2024")
