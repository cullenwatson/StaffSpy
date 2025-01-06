from calendar import month_name
from datetime import datetime
import json
import logging

import pytz

from staffspy.utils.exceptions import TooManyRequests
from staffspy.utils.models import ContactInfo, Staff

logger = logging.getLogger(__name__)


class ContactInfoFetcher:
    def __init__(self, session):
        self.session = session
        self.endpoint = "https://www.linkedin.com/voyager/api/graphql?queryId=voyagerIdentityDashProfiles.13618f886ce95bf503079f49245fbd6f&queryName=ProfilesByMemberIdentity&variables=(memberIdentity:{employee_id},count:1)"

    def fetch_contact_info(self, base_staff):
        ep = self.endpoint.format(employee_id=base_staff.id)
        res = self.session.get(ep)
        logger.debug(f"bio info, status code - {res.status_code}")
        if res.status_code == 429:
            return TooManyRequests("429 Too Many Requests")
        if not res.ok:
            logger.debug(res.text)
            return False
        try:
            employee_json = res.json()
        except json.decoder.JSONDecodeError:
            logger.debug(res.text)
            return False

        self.parse_emp_contact_info(base_staff, employee_json)
        return True

    def parse_emp_contact_info(self, emp: Staff, emp_dict: dict):
        """Parse the employee data from the employee profile."""
        contact_info = ContactInfo()
        emp_dict = emp_dict["data"]["identityDashProfilesByMemberIdentity"]["elements"][
            0
        ]
        try:
            contact_info.email_address = emp_dict["emailAddress"]["emailAddress"]
        except (KeyError, IndexError, TypeError):
            pass

        try:
            contact_info.address = emp_dict["address"]
        except (KeyError, IndexError, TypeError):
            pass

        try:
            month = month_name[emp_dict["birthDateOn"]["month"]]
            day = emp_dict["birthDateOn"]["day"]
            contact_info.birthday = f"{month} {day}"
        except (KeyError, IndexError, TypeError):
            pass

        try:
            contact_info.websites = [x["url"] for x in emp_dict["websites"]]
        except (KeyError, IndexError, TypeError):
            pass

        try:
            contact_info.phone_numbers = [
                x["phoneNumber"]["number"] for x in emp_dict["phoneNumbers"]
            ]
        except (KeyError, IndexError, TypeError):
            pass

        try:
            created_at = emp_dict["memberRelationship"][
                "memberRelationshipDataResolutionResult"
            ]["connection"]["createdAt"]
            timezone = pytz.timezone("UTC")
            dt = datetime.fromtimestamp(created_at / 1000, tz=timezone)
            contact_info.created_at = dt.strftime("%Y-%m-%d %H:%M:%S %Z")
        except (KeyError, IndexError, TypeError):
            pass
        emp.contact_info = contact_info
