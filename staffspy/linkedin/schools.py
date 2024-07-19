import json
import logging
import re
from datetime import datetime
from math import inf

from staffspy.exceptions import TooManyRequests
from staffspy.models import School

logger = logging.getLogger(__name__)


class SchoolsFetcher:
    college_words = ["uni", "college"]

    def __init__(self, session):
        self.session = session
        self.endpoint = "https://www.linkedin.com/voyager/api/graphql?queryId=voyagerIdentityDashProfileComponents.277ba7d7b9afffb04683953cede751fb&queryName=ProfileComponentsBySectionType&variables=(tabIndex:0,sectionType:education,profileUrn:urn%3Ali%3Afsd_profile%3A{employee_id},count:50)"

    def fetch_schools(self, staff):
        ep = self.endpoint.format(employee_id=staff.id)
        res = self.session.get(ep)
        logger.debug(f"schools, status code - {res.status_code}")
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
            elements = res_json["data"]["identityDashProfileComponentsBySectionType"][
                "elements"
            ][0]["components"]["pagedListComponent"]["components"]["elements"]
        except (KeyError, IndexError, TypeError) as e:
            logger.debug(res_json)
            return False

        staff.schools, staff.estimated_age = self.parse_schools(elements)
        return True

    def parse_schools(self, elements):
        schools = []
        first_college_year = inf
        person_age = None
        for elem in elements:
            entity = elem["components"]["entityComponent"]
            if not entity:
                break
            years = entity["caption"]["text"] if entity["caption"] else None
            school_name = entity["titleV2"]["text"]["text"]
            if years:
                if any(word in school_name.lower() for word in self.college_words):
                    start_year_match = re.search(r"\d{4}", years)
                    if start_year_match:
                        start_year = int(start_year_match.group())
                        first_college_year = min(first_college_year, start_year)
                        person_age = 18 + (datetime.now().year - first_college_year)
            degree = entity["subtitle"]["text"] if entity["subtitle"] else None
            school = School(
                years=years,
                school=school_name,
                degree=degree,
            )
            schools.append(school)

        return (
            (schools, person_age)
            if person_age and person_age < inf
            else (schools, None)
        )
