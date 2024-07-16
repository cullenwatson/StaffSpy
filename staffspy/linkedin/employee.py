import json
import logging
import re

import staffspy.utils as utils
from staffspy.exceptions import TooManyRequests

logger = logging.getLogger(__name__)


class EmployeeFetcher:
    def __init__(self, session):
        self.session = session
        self.endpoint = "https://www.linkedin.com/voyager/api/voyagerIdentityDashProfiles?count=1&decorationId=com.linkedin.voyager.dash.deco.identity.profile.TopCardComplete-138&memberIdentity={employee_id}&q=memberIdentity"

        self.domain = None

    def fetch_employee(self, base_staff, domain):
        self.domain = domain
        ep = self.endpoint.format(employee_id=base_staff.id)
        res = self.session.get(ep)
        logger.debug(f"basic info, status code - {res.status_code}")
        if res.status_code == 429:
            return TooManyRequests("429 Too Many Requests")
        if not res.ok:
            logger.debug(res.text[:200])
            return False
        try:
            res_json = res.json()
        except json.decoder.JSONDecodeError:
            logger.debug(res.text[:200])
            return False

        try:
            employee_json = res_json["elements"][0]
        except (KeyError, IndexError, TypeError):
            logger.debug(res_json)
            return False

        self.parse_emp(base_staff, employee_json)
        return True

    def parse_emp(self, emp, emp_dict):
        """Parse the employee data from the employee profile."""
        try:
            photo_data = emp_dict["profilePicture"]["displayImageReference"][
                "vectorImage"
            ]
            photo_base_url = photo_data["rootUrl"]
            photo_ext_url = photo_data["artifacts"][-1]["fileIdentifyingUrlPathSegment"]
            profile_photo = f"{photo_base_url}{photo_ext_url}"
        except:
            profile_photo = None

        emp.profile_id = emp_dict["publicIdentifier"]

        emp.profile_link = f'https://www.linkedin.com/in/{emp_dict["publicIdentifier"]}'

        emp.profile_photo = profile_photo
        emp.first_name = emp_dict["firstName"]
        emp.last_name = emp_dict["lastName"]
        emp.potential_email = utils.create_email(
            emp.first_name, emp.last_name, self.domain
        )

        emp.followers = emp_dict.get("followingState", {}).get("followerCount")
        emp.connections = emp_dict["connections"]["paging"]["total"]
        emp.location = emp_dict["geoLocation"]["geo"]["defaultLocalizedName"]
        emp.company = emp_dict["profileTopPosition"]["elements"][0]["companyName"]
        edu_cards = emp_dict["profileTopEducation"]["elements"]
        if edu_cards:
            emp.school = edu_cards[0].get(
                "schoolName", edu_cards[0].get("school", {}).get("name")
            )
        emp.influencer = emp_dict["influencer"]
        emp.creator = emp_dict["creator"]
        emp.premium = emp_dict["premium"]
        try:
            profile_insight = emp_dict["profileInsight"]["elements"]
            if profile_insight:
                mutual_connections_str = profile_insight[0]["text"]["text"]
                match = re.search(r"\d+", mutual_connections_str)
                if match:
                    emp.mutual_connections = int(match.group()) + 2
                else:
                    emp.mutual_connections = (
                        2 if " and " in mutual_connections_str else 1
                    )
        except:
            emp.mutual_connections = None
        pass
