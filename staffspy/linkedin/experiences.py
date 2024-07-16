import json
import logging

import staffspy.utils as utils
from staffspy.exceptions import TooManyRequests
from staffspy.models import Experience

logger = logging.getLogger(__name__)


class ExperiencesFetcher:
    def __init__(self, session):
        self.session = session
        self.endpoint = "https://www.linkedin.com/voyager/api/graphql?queryId=voyagerIdentityDashProfileComponents.277ba7d7b9afffb04683953cede751fb&queryName=ProfileComponentsBySectionType&variables=(tabIndex:0,sectionType:experience,profileUrn:urn%3Ali%3Afsd_profile%3A{employee_id},count:50)"

    def fetch_experiences(self, staff):
        ep = self.endpoint.format(employee_id=staff.id)
        res = self.session.get(ep)
        logger.debug(f"exps, status code - {res.status_code}")
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
            skills_json = res_json["data"][
                "identityDashProfileComponentsBySectionType"
            ]["elements"][0]["components"]["pagedListComponent"]["components"][
                "elements"
            ]
        except (KeyError, IndexError, TypeError) as e:
            logger.debug(res_json)
            return False

        staff.experiences = self.parse_experiences(skills_json)
        return True

    def parse_experiences(self, elements):
        exps = []
        for elem in elements:
            entity = elem["components"]["entityComponent"]
            try:
                if (
                    not entity["subComponents"]
                    or not entity["subComponents"]["components"][0]["components"][
                        "pagedListComponent"
                    ]
                ):
                    emp_type = None
                    duration = entity["caption"]["text"]
                    from_date, to_date = utils.parse_duration(duration)
                    if from_date:
                        duration = duration.split(" · ")[1]
                    company = entity["subtitle"]["text"] if entity["subtitle"] else None
                    title = entity["titleV2"]["text"]["text"]
                    location = (
                        entity["metadata"]["text"] if entity["metadata"] else None
                    )
                    parts = company.split(" · ")
                    if len(parts) > 1:
                        company = parts[0]
                        emp_type = parts[-1].lower()
                    exp = Experience(
                        duration=duration,
                        title=title,
                        company=company,
                        emp_type=emp_type,
                        from_date=from_date,
                        to_date=to_date,
                        location=location,
                    )
                    exps.append(exp)

                else:
                    multi_exps = self.parse_multi_exp(entity)
                    exps += multi_exps

            except Exception as e:
                logger.exception(e)

        return exps

    def parse_multi_exp(self, entity):
        exps = []
        company = entity["titleV2"]["text"]["text"]
        elements = entity["subComponents"]["components"][0]["components"][
            "pagedListComponent"
        ]["components"]["elements"]
        for elem in elements:
            entity = elem["components"]["entityComponent"]
            duration = entity["caption"]["text"]
            title = entity["titleV2"]["text"]["text"]
            emp_type = (
                entity["subtitle"]["text"].lower() if entity["subtitle"] else None
            )
            location = entity["metadata"]["text"] if entity["metadata"] else None
            from_date, to_date = utils.parse_duration(duration)
            if from_date:
                duration = duration.split(" · ")[1]
            exp = Experience(
                duration=duration,
                title=title,
                company=company,
                emp_type=emp_type,
                from_date=from_date,
                to_date=to_date,
                location=location,
            )
            exps.append(exp)
        return exps
