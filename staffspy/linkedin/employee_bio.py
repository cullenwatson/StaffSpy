import json
import logging

from staffspy.utils.exceptions import TooManyRequests

logger = logging.getLogger(__name__)


class EmployeeBioFetcher:
    def __init__(self, session):
        self.session = session
        self.endpoint = "https://www.linkedin.com/voyager/api/graphql?queryId=voyagerIdentityDashProfileComponents.9117695ef207012719e3e0681c667e14&queryName=ProfileComponentsBySectionType&variables=(tabIndex:0,sectionType:languages,profileUrn:urn%3Ali%3Afsd_profile%3A{employee_id},count:50)"

    def fetch_employee_bio(self, base_staff):
        ep = self.endpoint.format(employee_id=base_staff.id)
        res = self.session.get(ep)
        logger.debug(f"bio info, status code - {res.status_code}")
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
            employee_json = list(
                filter(
                    lambda x: ",ABOUT," in x["entityUrn"],
                    res_json["data"]["identityDashProfileCardsByInitialCards"][
                        "elements"
                    ],
                )
            )
        except (KeyError, IndexError, TypeError):
            logger.debug(res_json)
            return False

        self.parse_emp_bio(base_staff, employee_json)
        return True

    def parse_emp_bio(self, emp, emp_dict):
        """Parse the employee data from the employee profile."""
        try:
            bio = emp_dict[0]["topComponents"][1]["components"]["textComponent"][
                "text"
            ]["text"]
        except:
            bio = None
        emp.bio = bio
