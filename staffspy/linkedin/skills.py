import json
import logging

from staffspy.exceptions import TooManyRequests
from staffspy.models import Skill

logger = logging.getLogger(__name__)


class SkillsFetcher:
    def __init__(self, session):
        self.session = session
        self.endpoint = "https://www.linkedin.com/voyager/api/graphql?queryId=voyagerIdentityDashProfileComponents.277ba7d7b9afffb04683953cede751fb&queryName=ProfileComponentsBySectionType&variables=(tabIndex:0,sectionType:skills,profileUrn:urn%3Ali%3Afsd_profile%3A{employee_id},count:50)"

    def fetch_skills(self, staff):
        ep = self.endpoint.format(employee_id=staff.id)
        res = self.session.get(ep)
        logger.debug(f"skills, status code - {res.status_code}")
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

        tab_comp = res_json["data"]["identityDashProfileComponentsBySectionType"][
            "elements"
        ][0]["components"]["tabComponent"]
        if tab_comp:
            sections = tab_comp["sections"]
            staff.skills = self.parse_skills(sections)
        return True

    def parse_skills(self, sections):
        names=set()
        skills = []
        for section in sections:
            elems = section["subComponent"]["components"]["pagedListComponent"][
                "components"
            ]["elements"]
            for elem in elems:
                entity = elem["components"]["entityComponent"]
                name = entity["titleV2"]["text"]["text"]
                if name in names:
                    continue
                names.add(name)
                try:
                    endorsements = int(
                        entity["subComponents"]["components"][0]["components"][
                            "insightComponent"
                        ]["text"]["text"]["text"].replace(" endorsements", "")
                    )
                except:
                    endorsements = 0
                skills.append(Skill(name=name, endorsements=endorsements))
        return skills
