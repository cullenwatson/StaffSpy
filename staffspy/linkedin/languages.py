import json
import logging

from staffspy.utils.exceptions import TooManyRequests
from staffspy.utils.models import Skill, Staff

logger = logging.getLogger(__name__)


class LanguagesFetcher:
    def __init__(self, session):
        self.session = session
        self.endpoint = "https://www.linkedin.com/voyager/api/graphql?queryId=voyagerIdentityDashProfileComponents.9117695ef207012719e3e0681c667e14&queryName=ProfileComponentsBySectionType&variables=(tabIndex:0,sectionType:languages,profileUrn:urn%3Ali%3Afsd_profile%3A{employee_id},count:50)"

    def fetch_languages(self, staff: Staff):
        ep = self.endpoint.format(employee_id=staff.id)
        res = self.session.get(ep)
        logger.debug(f"skills, status code - {res.status_code}")
        if res.status_code == 429:
            return TooManyRequests("429 Too Many Requests")
        if not res.ok:
            logger.debug(res.text)
            return False
        try:
            res_json = res.json()
        except json.decoder.JSONDecodeError:
            logger.debug(res.text)
            return False

        if res_json.get("errors"):
            return False
        staff.languages = self.parse_languages(res_json)
        return True

    def parse_languages(self, language_json: dict) -> list[str]:
        languages = []
        elements = language_json["data"]["identityDashProfileComponentsBySectionType"][
            "elements"
        ][0]["components"]["pagedListComponent"]["components"]["elements"]

        for element in elements:
            if comp := element["components"]["entityComponent"]:
                title = comp["titleV2"]["text"]["text"]
                languages.append(title)

        return languages
