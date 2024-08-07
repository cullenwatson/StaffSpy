import json
import logging
import re

import staffspy.utils.utils as utils
from staffspy.utils.exceptions import TooManyRequests
from staffspy.utils.models import Staff

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

    def parse_emp(self, emp: Staff, emp_dict: dict):
        """Parse the employee data from the employee profile."""

        def get_photo_url(emp_dict: dict, key: str):
            try:
                photo_data = emp_dict[key]["displayImageReference"]["vectorImage"]
                photo_base_url = photo_data["rootUrl"]
                photo_ext_url = photo_data["artifacts"][-1]["fileIdentifyingUrlPathSegment"]
                return f"{photo_base_url}{photo_ext_url}"
            except (KeyError, TypeError, IndexError, ValueError):
                return None

        emp.profile_photo = get_photo_url(emp_dict, "profilePicture")
        emp.banner_photo = get_photo_url(emp_dict, "backgroundPicture")
        emp.profile_id = emp_dict["publicIdentifier"]
        try:
            emp.headline = emp_dict.get('headline')
            if not emp.headline:
                emp.headline = emp_dict['memberRelationship']['memberRelationshipData']['noInvitation']['targetInviteeResolutionResult']['headline']
        except:
            pass
        emp.is_connection = next(iter(emp_dict['memberRelationship']['memberRelationshipUnion'])) == 'connection'
        emp.open_to_work = emp_dict['profilePicture'].get('frameType')=='OPEN_TO_WORK'
        emp.is_hiring = emp_dict['profilePicture'].get('frameType')=='HIRING'

        emp.profile_link = f'https://www.linkedin.com/in/{emp_dict["publicIdentifier"]}'

        emp.first_name = emp_dict["firstName"]
        emp.last_name = emp_dict["lastName"].split(',')[0]
        emp.potential_emails = utils.create_emails(
            emp.first_name, emp.last_name, self.domain
        ) if self.domain else None

        emp.followers = emp_dict.get("followingState", {}).get("followerCount")
        emp.connections = emp_dict["connections"]["paging"]["total"]
        emp.location = emp_dict.get("geoLocation",{}).get("geo",{}).get("defaultLocalizedName")

        # Handle empty elements case for company
        top_positions = emp_dict.get("profileTopPosition", {}).get("elements", [])
        if top_positions:
            emp.company = top_positions[0].get("companyName", None)
        else:
            emp.company = None

        edu_cards = emp_dict.get("profileTopEducation", {}).get("elements", [])
        if edu_cards:
            emp.school = edu_cards[0].get(
                "schoolName", edu_cards[0].get("school", {}).get("name")
            )
        emp.influencer = emp_dict.get("influencer", False)
        emp.creator = emp_dict.get("creator", False)
        emp.premium = emp_dict.get("premium", False)
        emp.mutual_connections = 0

        try:
            profile_insight = emp_dict.get("profileInsight", {}).get("elements", [])
            if profile_insight:
                mutual_connections_str = profile_insight[0]["text"]["text"]
                match = re.search(r"\d+", mutual_connections_str)
                if match:
                    emp.mutual_connections = int(match.group()) + 2
                else:
                    emp.mutual_connections = (
                        2 if " and " in mutual_connections_str else 1
                    )
        except (KeyError, TypeError, IndexError, ValueError) as e:
            pass
