import json
import pandas as pd

from staffspy.linkedin.comments import CommentFetcher
from staffspy.linkedin.linkedin import LinkedInScraper
from staffspy.utils.models import Staff
from staffspy.solvers.capsolver import CapSolver
from staffspy.solvers.solver_type import SolverType
from staffspy.solvers.two_captcha import TwoCaptchaSolver
from staffspy.utils.utils import (
    set_logger_level,
    logger,
    Login,
    parse_company_data,
    extract_emails_from_text,
    clean_df,
)
from staffspy.utils.driver_type import DriverType, BrowserType

__all__ = [
    "LinkedInAccount",
    "SolverType",
    "DriverType",
    "BrowserType",
]


class LinkedInAccount:
    """LinkedinAccount storing cookie data and providing outer facing methods for client"""

    solver_map = {
        SolverType.CAPSOLVER: CapSolver,
        SolverType.TWO_CAPTCHA: TwoCaptchaSolver,
    }

    def __init__(
        self,
        session_file: str = None,
        username: str = None,
        password: str = None,
        log_level: int = 0,
        solver_api_key: str = None,
        solver_service: SolverType = SolverType.CAPSOLVER,
        driver_type: DriverType = None,
    ):
        self.session_file = session_file
        self.username = username
        self.password = password
        self.log_level = log_level
        self.solver = self.solver_map[solver_service](solver_api_key)
        self.driver_type = driver_type
        self.session = None
        self.linkedin_scraper = None
        self.on_block = False
        self.login()

    def login(self):
        set_logger_level(self.log_level)
        login = Login(
            self.username,
            self.password,
            self.solver,
            self.session_file,
            self.driver_type,
        )
        self.session = login.load_session()

    def scrape_staff(
        self,
        company_name: str = None,
        search_term: str = None,
        location: str = None,
        extra_profile_data: bool = False,
        max_results: int = 1000,
        block: bool = False,
        connect: bool = False,
    ):
        if self.on_block:
            return logger.error(
                "Account is on cooldown as a safety precaution after receiving a 429 (TooManyRequests) from LinkedIn. Please recreate a new LinkedInAccount to proceed."
            )
        """Main function entry point to scrape LinkedIn staff"""
        li_scraper = LinkedInScraper(self.session)
        staff = li_scraper.scrape_staff(
            company_name=company_name,
            extra_profile_data=extra_profile_data,
            search_term=search_term,
            location=location,
            max_results=max_results,
            block=block,
            connect=connect,
        )
        if li_scraper.on_block:
            self.on_block = True
        staff_dicts = [staff.to_dict() for staff in staff]
        staff_df = pd.DataFrame(staff_dicts)
        if staff_df.empty:
            return staff_df

        staff_df = clean_df(staff_df)
        linkedin_member_df = staff_df[staff_df["name"] == "LinkedIn Member"]
        non_linkedin_member_df = staff_df[staff_df["name"] != "LinkedIn Member"]
        staff_df = pd.concat([non_linkedin_member_df, linkedin_member_df])
        logger.info(
            f"3) Staff from {company_name}: {len(staff_df)} total, {len(linkedin_member_df)} hidden, {len(staff_df) - len(linkedin_member_df)} visible"
        )
        return staff_df.reset_index(drop=True)

    def scrape_users(
        self, user_ids: list[str], block: bool = False, connect: bool = False
    ) -> pd.DataFrame | None:
        """Scrape users from Linkedin by user IDs"""
        if self.on_block:
            return logger.error(
                "Account is on cooldown as a safety precaution after receiving a 429 (TooManyRequests) from LinkedIn. Please recreate a new LinkedInAccount to proceed."
            )

        li_scraper = LinkedInScraper(self.session)
        li_scraper.num_staff = len(user_ids)
        users = [
            Staff(
                id="",
                search_term="manual",
                profile_id=user_id,
                profile_link=f"https://www.linkedin.com/in/{user_id}",
            )
            for user_id in user_ids
        ]

        for i, user in enumerate(users, start=1):
            user.id, user.urn = li_scraper.fetch_user_profile_data_from_public_id(
                user.profile_id, "user_id"
            )
            if user.id:
                li_scraper.fetch_all_info_for_employee(user, i)
                if block:
                    li_scraper.block_user(user)
                elif connect:
                    li_scraper.connect_user(user)

        users_dicts = [user.to_dict() for user in users if user.id]
        users_df = pd.DataFrame(users_dicts)

        if users_df.empty:
            return users_df
        linkedin_member_df = users_df[users_df["name"] == "LinkedIn Member"]
        non_linkedin_member_df = users_df[users_df["name"] != "LinkedIn Member"]
        users_df = pd.concat([non_linkedin_member_df, linkedin_member_df])
        logger.info(f"Scraped {len(users_df)} users")
        return users_df

    def scrape_comments(self, post_ids: list[str]) -> pd.DataFrame:
        """Scrape comments from Linkedin by post IDs"""
        if self.on_block:
            return logger.error(
                "Account is on cooldown as a safety precaution after receiving a 429 (TooManyRequests) from LinkedIn. Please recreate a new LinkedInAccount to proceed."
            )

        comment_fetcher = CommentFetcher(self.session)
        all_comments = []
        for i, post_id in enumerate(post_ids, start=1):
            comments = comment_fetcher.fetch_comments(post_id)
            all_comments.extend(comments)

        comment_dict = [comment.to_dict() for comment in all_comments]
        comment_df = pd.DataFrame(comment_dict)

        if not comment_df.empty:
            comment_df["emails"] = comment_df["text"].apply(extract_emails_from_text)
            comment_df = comment_df.sort_values(by="created_at", ascending=False)

        return comment_df

    def scrape_companies(
        self,
        company_names: list[str] = None,
    ) -> pd.DataFrame:
        """Scrape company details from Linkedin"""
        if self.on_block:
            return logger.error(
                "Account is on cooldown as a safety precaution after receiving a 429 (TooManyRequests) from LinkedIn. Please recreate a new LinkedInAccount to proceed."
            )

        if not company_names:
            raise ValueError("company_names list cannot be empty")

        li_scraper = LinkedInScraper(self.session)
        company_dfs = []

        for company_name in company_names:
            try:
                company_res = li_scraper.fetch_or_search_company(company_name)
                try:
                    company_data = company_res.json()
                except json.decoder.JSONDecodeError:
                    logger.error(f"Failed to fetch company data for {company_name}")
                    continue

                company_df = parse_company_data(company_data, search_term=company_name)
                company_dfs.append(company_df)

            except Exception as e:
                logger.error(f"Failed to process company {company_name}: {str(e)}")
                continue

        if not company_dfs:
            return pd.DataFrame()

        return pd.concat(company_dfs, ignore_index=True)

    def scrape_connections(
        self,
        max_results: int = 10**8,
        extra_profile_data: bool = False,
    ) -> pd.DataFrame:
        """Scrape connections from Linkedin"""
        if self.on_block:
            return logger.error(
                "Account is on cooldown as a safety precaution after receiving a 429 (TooManyRequests) from LinkedIn. Please recreate a new LinkedInAccount to proceed."
            )
        li_scraper = LinkedInScraper(self.session)

        connections = li_scraper.scrape_connections(
            max_results=max_results,
            extra_profile_data=extra_profile_data,
        )
        connections_df = pd.DataFrame()
        if connections:
            staff_dicts = [staff.to_dict() for staff in connections]
            connections_df = pd.DataFrame(staff_dicts)
            connections_df = clean_df(connections_df)

        return connections_df
