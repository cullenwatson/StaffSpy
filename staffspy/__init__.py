import pandas as pd

from staffspy.linkedin.comments import CommentFetcher
from staffspy.linkedin.linkedin import LinkedInScraper
from staffspy.utils.models import Staff
from staffspy.solvers.capsolver import CapSolver
from staffspy.solvers.solver_type import SolverType
from staffspy.solvers.two_captcha import TwoCaptchaSolver
from staffspy.utils.utils import set_logger_level, logger, Login
from staffspy.utils.driver_type import DriverType, BrowserType


class LinkedInAccount:
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
    ) -> pd.DataFrame:
        """Scrape staff from Linkedin
        company_name - name of company to find staff frame
        search_term - occupation / term to search for at the company
        location - filter for staff at a location
        extra_profile_data - fetches staff's experiences, schools, and mor
        max_results - amount of results you desire
        """
        li_scraper = LinkedInScraper(self.session)

        staff = li_scraper.scrape_staff(
            company_name=company_name,
            extra_profile_data=extra_profile_data,
            search_term=search_term,
            location=location,
            max_results=max_results,
        )
        staff_dicts = [staff.to_dict() for staff in staff]
        staff_df = pd.DataFrame(staff_dicts)

        if staff_df.empty:
            return staff_df
        linkedin_member_df = staff_df[staff_df["name"] == "LinkedIn Member"]
        non_linkedin_member_df = staff_df[staff_df["name"] != "LinkedIn Member"]
        staff_df = pd.concat([non_linkedin_member_df, linkedin_member_df])
        logger.info(
            f"Scraped {len(staff_df)} staff members from {company_name}, with {len(linkedin_member_df)} hidden LinkedIn users"
        )
        return staff_df

    def scrape_users(self, user_ids: list[str]) -> pd.DataFrame:
        """Scrape users from Linkedin by user IDs
        user_ids - list of LinkedIn user IDs
        """
        li_scraper = LinkedInScraper(self.session)
        li_scraper.num_staff = len(user_ids)
        users = [
            Staff(
                id="",
                search_term="manual",
                profile_id=user_id,
            )
            for user_id in user_ids
        ]

        for i, user in enumerate(users, start=1):
            user.id = li_scraper.fetch_user_profile_data_from_public_id(
                user.profile_id, "user_id"
            )
            if user.id:
                li_scraper.fetch_all_info_for_employee(user, i)

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
        comment_fetcher = CommentFetcher(self.session)
        all_comments = []
        for i, post_id in enumerate(post_ids, start=1):

            comments = comment_fetcher.fetch_comments(post_id)
            all_comments.extend(comments)

        comment_dict = [comment.to_dict() for comment in all_comments]
        comment_df = pd.DataFrame(comment_dict)

        return comment_df.sort_values(by="created_at", ascending=False)

    def scrape_company(self,
                       company_name: str = None,
                       search_term: str = None,
                       location: str = None,
                       max_results: int = 20,
                       ) -> pd.DataFrame:
        """Scrape company details from Linkedin
        company_name - name of company to find company
        search_term - occupation / term to search for at the company
        location - filter for location
        max_results - amount of results you desire
        """

        li_scraper = LinkedInScraper(self.session)

        company_res = li_scraper.fetch_or_search_company(company_name)

        try:
            company_data = company_res.json()
        except json.decoder.JSONDecodeError:
            logger.error("Failed to fetch company data")
            raise Exception("Failed to load company data", company_res.text)

        company_details = company_data["elements"][0]
        company_df = pd.DataFrame([company_details])

        return company_df
