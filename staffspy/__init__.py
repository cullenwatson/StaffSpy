import pandas as pd

from staffspy.linkedin.linkedin import LinkedInScraper

from staffspy.utils import set_logger_level, logger


def scrape_staff(
    *,
    company_name: str,
    session_file: str = None,
    search_term: str = None,
    location: str = None,
    extra_profile_data: bool = False,
    max_results: int = 1000,
    log_level: int = 0,
) -> pd.DataFrame:
    set_logger_level(log_level)
    li = LinkedInScraper(session_file)

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
        f"Scraped {len(staff_df)} staff members, with {len(linkedin_member_df)} hidedn LinkedIn Members."
    )
    return staff_df
