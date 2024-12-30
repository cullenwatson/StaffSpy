import json
import logging

from staffspy.utils.exceptions import TooManyRequests
from staffspy.utils.models import Skill, Staff

logger = logging.getLogger(__name__)


class SkillsFetcher:
    def __init__(self, session):
        self.session = session
        self.endpoint = "https://www.linkedin.com/voyager/api/graphql?queryId=voyagerIdentityDashProfileComponents.277ba7d7b9afffb04683953cede751fb&queryName=ProfileComponentsBySectionType&variables=(tabIndex:0,sectionType:skills,profileUrn:urn%3Ali%3Afsd_profile%3A{employee_id},count:50)"

    def fetch_skills(self, staff: Staff):
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

        if res_json.get("errors"):
            return False
        tab_comp = res_json["data"]["identityDashProfileComponentsBySectionType"][
            "elements"
        ][0]["components"]["tabComponent"]
        if tab_comp:
            sections = tab_comp["sections"]
            staff.skills = self.parse_skills(sections)
        return True

    def parse_skills(self, sections):
        names = set()
        skills = []
        for section in sections:
            elems = section["subComponent"]["components"]["pagedListComponent"][
                "components"
            ]["elements"]
            for elem in elems:
                passed_assessment, endorsements = None, 0
                entity = elem["components"]["entityComponent"]
                name = entity["titleV2"]["text"]["text"]
                if name in names:
                    continue
                names.add(name)
                components = entity["subComponents"]["components"]
                for component in components:

                    try:
                        candidate = component["components"]["insightComponent"]["text"][
                            "text"
                        ]["text"]
                        if " endorsements" in candidate:
                            endorsements = int(candidate.replace(" endorsements", ""))
                        if "Passed LinkedIn Skill Assessment" in candidate:
                            passed_assessment = True
                    except:
                        pass

                skills.append(
                    Skill(
                        name=name,
                        endorsements=endorsements,
                        passed_assessment=passed_assessment,
                    )
                )
        return skills
