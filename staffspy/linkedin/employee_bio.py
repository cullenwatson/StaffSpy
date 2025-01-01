import json
import logging

from staffspy.utils.exceptions import TooManyRequests

logger = logging.getLogger(__name__)


class EmployeeBioFetcher:
    def __init__(self, session):
        self.session = session
        self.endpoint = "https://www.linkedin.com/voyager/api/graphql?queryId=voyagerIdentityDashProfileCards.9ad2590cb61a073ad514922fa752f566&queryName=ProfileTabInitialCards&variables=(count:50,profileUrn:urn%3Ali%3Afsd_profile%3A{employee_id})"

    def fetch_employee_bio(self, base_staff):
        ep = self.endpoint.format(employee_id=base_staff.id)
        res = self.session.get(ep)
        logger.debug(f"bio info, status code - {res.status_code}")
        if res.status_code == 429:
            return TooManyRequests("429 Too Many Requests")
        if not res.ok:
            logger.debug(res.text)
            return False
        try:
            data = res.json()
        except json.decoder.JSONDecodeError:
            logger.debug(res.text)
            return False

        try:
            base_staff.bio = data["data"]["identityDashProfileCardsByInitialCards"][
                "elements"
            ][3]["topComponents"][1]["components"]["textComponent"]["text"]["text"]
        except (KeyError, IndexError, TypeError):
            return False

        return True
