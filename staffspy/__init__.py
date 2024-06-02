import pandas as pd

from linkedin import LinkedInScraper


def scrape_staff(
    *,
    company_name: str,
    session_file: str,
    profile_details: bool = False,
    skills: bool = False,
    experiences: bool = False,
    certifications: bool = False,
    num_threads: int = 10,
    max_results: int = 10**8,
) -> pd.DataFrame:
    li = LinkedInScraper(session_file)

    staff = li.scrape_staff(
        company_name=company_name,
        profile_details=profile_details,
        num_threads=num_threads,
        skills=skills,
        experiences=experiences,
        certifications=certifications,
        max_results=max_results,
    )
    staff_dicts = [staff.to_dict() for staff in staff]
    staff_df = pd.DataFrame(staff_dicts)

    linkedin_member_df = staff_df[staff_df["name"] == "LinkedIn Member"]
    non_linkedin_member_df = staff_df[staff_df["name"] != "LinkedIn Member"]
    staff_df = pd.concat([non_linkedin_member_df, linkedin_member_df])
    return staff_df
