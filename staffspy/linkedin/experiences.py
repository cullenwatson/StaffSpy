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
            try:
                components = elem.get("components")
                if components is None:
                    continue

                entity = components.get("entityComponent")
                if entity is None:
                    continue

                sub_components = entity.get("subComponents")
                if (sub_components is None or
                        len(sub_components.get("components", [])) == 0 or
                        sub_components["components"][0].get("components") is None or
                        sub_components["components"][0]["components"].get("pagedListComponent") is None):

                    emp_type = start_date = end_date = None

                    caption = entity.get("caption")
                    duration = caption.get("text") if caption else None
                    if duration:
                        start_date, end_date = utils.parse_dates(duration)
                        from_date, to_date = utils.parse_duration(duration)
                        if from_date:
                            duration_parts = duration.split(" · ")
                            if len(duration_parts) > 1:
                                duration = duration_parts[1]

                    subtitle = entity.get("subtitle")
                    company = subtitle.get("text") if subtitle else None

                    titleV2 = entity.get("titleV2")
                    title_text = titleV2.get("text") if titleV2 else None
                    title = title_text.get("text") if title_text else None

                    metadata = entity.get("metadata")
                    location = metadata.get("text") if metadata else None

                    if company:
                        parts = company.split(" · ")
                        if len(parts) > 1:
                            company = parts[0]
                            emp_type = parts[-1].lower()

                    exp = Experience(
                        duration=duration,
                        title=title,
                        company=company,
                        emp_type=emp_type,
                        start_date=start_date,
                        end_date=end_date,
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
            start_date, end_date = utils.parse_dates(duration)
            from_date, to_date = utils.parse_duration(duration)
            if from_date:
                duration = duration.split(" · ")[1]
            exp = Experience(
                duration=duration,
                title=title,
                company=company,
                emp_type=emp_type,
                start_date=start_date,
                end_date=end_date,
                location=location,
            )
            exps.append(exp)
        return exps
