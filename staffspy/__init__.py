import pandas as pd

from linkedin import LinkedInScraper


def scrape_staff(
    *,
    company_name: str,
    session_file: str,
    profile_details: bool = False,
    skills: bool = False,
    max_results: int = 10**8,
) -> pd.DataFrame:
    li = LinkedInScraper(session_file)

    staff = li.scrape_staff(
        company_name=company_name,
        profile_details=profile_details,
        skills=skills,
        max_results=max_results,
    )
    staff_dicts = [staff.to_dict() for staff in staff]
    staff_df = pd.DataFrame(staff_dicts)

    return staff_df
