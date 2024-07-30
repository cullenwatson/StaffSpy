import pandas as pd

from staffspy.linkedin.linkedin import LinkedInScraper
from staffspy.solvers.capsolver import CapSolver
from staffspy.solvers.solver_type import SolverType
from staffspy.solvers.two_captcha import TwoCaptchaSolver

from staffspy.utils import set_logger_level, logger, Login


def scrape_staff(
        *,
        company_name: str = None,
        user_id: str = None,
        session_file: str = None,
        search_term: str = None,
        location: str = None,
        extra_profile_data: bool = False,
        max_results: int = 1000,
        log_level: int = 0,
        username: str = None,
        password: str = None,
        solver_api_key: str = None,
        solver_service: SolverType = SolverType.CAPSOLVER

) -> pd.DataFrame:
    """Scrape staff from Linkedin
    company_name - name of company to find staff frame
    user_id - alternative to company_name, fetches the company_name from the user profile
    session_file - place to save cookies to only sign in once
    search_term - occupation / term to search for at the company
    location - filter for staff at a location
    extra_profile_data - fetches staff's experiences, schools, and mor
    max_results - amount of results you desire
    log_level - level of logs, 0 for no logs, 2 for all
    usernme,password - for requests based sign in
    solver_api_key,solver_service - options to bypass captcha
    """
    set_logger_level(log_level)

    solver=None
    if solver_service == SolverType.CAPSOLVER:
        solver = CapSolver(solver_api_key)
    elif solver_service == SolverType.TWO_CAPTCHA:
        solver = TwoCaptchaSolver(solver_api_key)
    login = Login(username, password, solver, session_file)
    session = login.load_session()

    li = LinkedInScraper(session)

    if not company_name:
        if not user_id:
            raise ValueError("Either company_name or user_id must be provided")

        company_name = li.fetch_company_id_from_user(user_id)

    staff = li.scrape_staff(
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
        f"Scraped {len(staff_df)} staff members, with {len(linkedin_member_df)} hidden LinkedIn Members."
    )
    return staff_df
