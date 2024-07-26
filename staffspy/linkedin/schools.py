import json
import logging

from staffspy.exceptions import TooManyRequests
from staffspy.models import School
from staffspy.utils import parse_dates

logger = logging.getLogger(__name__)


class SchoolsFetcher:

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

        staff.schools = self.parse_schools(elements)
        return True

    def parse_schools(self, elements):
        schools = []
        start = end = None
        for elem in elements:
            entity = elem["components"]["entityComponent"]
            if not entity:
                break
            years = entity["caption"]["text"] if entity["caption"] else None
            school_name = entity["titleV2"]["text"]["text"]

            if years:
                start, end = parse_dates(years)
            degree = entity["subtitle"]["text"] if entity["subtitle"] else None
            school = School(
                start_date=start, end_date=end, school=school_name, degree=degree
            )
            schools.append(school)

        return schools
