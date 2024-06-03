import json
import re
import sys
from urllib.parse import quote
from concurrent.futures import ThreadPoolExecutor, as_completed

import utils
from staffspy.utils import logger
from staffspy.exceptions import TooManyRequests
from staffspy.models import Staff, Experience, Certification, Skill, School


class LinkedInScraper:
    company_id_ep = "https://www.linkedin.com/voyager/api/organization/companies?q=universalName&universalName="
    employees_ep = "https://www.linkedin.com/voyager/api/graphql?variables=(start:{offset},query:(flagshipSearchIntent:SEARCH_SRP,{search}queryParameters:List((key:currentCompany,value:List({company_id})),(key:resultType,value:List(PEOPLE))),includeFiltersInResponse:false),count:{count})&queryId=voyagerSearchDashClusters.66adc6056cf4138949ca5dcb31bb1749"
    employee_ep = "https://www.linkedin.com/voyager/api/voyagerIdentityDashProfiles?count=1&decorationId=com.linkedin.voyager.dash.deco.identity.profile.TopCardComplete-138&memberIdentity={employee_id}&q=memberIdentity"
    skills_ep = "https://www.linkedin.com/voyager/api/graphql?queryId=voyagerIdentityDashProfileComponents.277ba7d7b9afffb04683953cede751fb&queryName=ProfileComponentsBySectionType&variables=(tabIndex:0,sectionType:skills,profileUrn:urn%3Ali%3Afsd_profile%3A{employee_id},count:50)"
    experience_ep = "https://www.linkedin.com/voyager/api/graphql?queryId=voyagerIdentityDashProfileComponents.277ba7d7b9afffb04683953cede751fb&queryName=ProfileComponentsBySectionType&variables=(tabIndex:0,sectionType:experience,profileUrn:urn%3Ali%3Afsd_profile%3A{employee_id},count:50)"
    certifications_ep = "https://www.linkedin.com/voyager/api/graphql?queryId=voyagerIdentityDashProfileComponents.277ba7d7b9afffb04683953cede751fb&queryName=ProfileComponentsBySectionType&variables=(tabIndex:0,sectionType:certifications,profileUrn:urn%3Ali%3Afsd_profile%3A{employee_id},count:50)"
    schools_ep = "https://www.linkedin.com/voyager/api/graphql?queryId=voyagerIdentityDashProfileComponents.277ba7d7b9afffb04683953cede751fb&queryName=ProfileComponentsBySectionType&variables=(tabIndex:0,sectionType:education,profileUrn:urn%3Ali%3Afsd_profile%3A{employee_id},count:50)"

    def __init__(self, session_file):
        self.session = utils.load_session(session_file)
        self.company_id = self.staff_count = self.num_staff = self.company_name = (
            self.max_results
        ) = self.search_term = None

    def get_company_id(self, company_name):
        res = self.session.get(f"{self.company_id_ep}{company_name}")
        if res.status_code != 200:
            raise Exception(
                f"Failed to find company {company_name}",
                res.status_code,
                res.text[:200],
            )
        logger.debug(f"Fetched company {res.status_code}")
        try:
            response_json = res.json()
        except json.decoder.JSONDecodeError:
            logger.debug(res.text[:200])
            sys.exit()
        company = response_json["elements"][0]
        staff_count = company["staffCount"]
        company_id = company["trackingInfo"]["objectUrn"].split(":")[-1]
        logger.info(f"Found company {company_name} with {staff_count} staff")
        return company_id, staff_count

    def parse_staff(self, elements):
        staff = []

        for elem in elements:
            for card in elem.get("items", []):
                person = card.get("item", {}).get("entityResult", {})
                if not person:
                    continue
                pattern = r"urn:li:fsd_profile:([^,]+),SEARCH_SRP"
                match = re.search(pattern, person["entityUrn"])
                linkedin_id = match.group(1)

                name = person["title"]["text"].strip()
                position = (
                    person.get("primarySubtitle", {}).get("text", "")
                    if person.get("primarySubtitle")
                    else ""
                )
                staff.append(
                    Staff(
                        id=linkedin_id,
                        name=name,
                        position=position,
                        search_term=(
                            f"{self.company_name}"
                            if not self.search_term
                            else f"{self.company_name} - {self.search_term}"
                        ),
                    )
                )
        return staff

    def parse_emp(self, emp, emp_dict):
        try:
            photo_data = emp_dict["profilePicture"]["displayImageReference"][
                "vectorImage"
            ]
            photo_base_url = photo_data["rootUrl"]
            photo_ext_url = photo_data["artifacts"][-1]["fileIdentifyingUrlPathSegment"]
            profile_photo = f"{photo_base_url}{photo_ext_url}"
        except:
            profile_photo = None

        emp.profile_id = emp_dict["publicIdentifier"]

        emp.profile_link = f'https://www.linkedin.com/in/{emp_dict["publicIdentifier"]}'

        emp.profile_photo = profile_photo
        emp.first_name = emp_dict["firstName"]
        emp.last_name = emp_dict["lastName"]
        emp.followers = emp_dict.get("followingState", {}).get("followerCount")
        emp.connections = emp_dict["connections"]["paging"]["total"]
        emp.location = emp_dict["geoLocation"]["geo"]["defaultLocalizedName"]
        emp.company = emp_dict["profileTopPosition"]["elements"][0]["companyName"]
        edu_cards = emp_dict["profileTopEducation"]["elements"]
        if edu_cards:
            emp.school = edu_cards[0].get(
                "schoolName", edu_cards[0].get("school", {}).get("name")
            )
        emp.influencer = emp_dict["influencer"]
        emp.creator = emp_dict["creator"]
        emp.premium = emp_dict["premium"]

    def fetch_employee(self, base_staff):
        ep = self.employee_ep.format(employee_id=base_staff.id)
        res = self.session.get(ep)
        logger.debug(f"basic info, status code - {res.status_code}")
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
            employee_json = res_json["elements"][0]
        except (KeyError, IndexError, TypeError):
            logger.debug(res_json)
            return False

        self.parse_emp(base_staff, employee_json)
        return True

    def fetch_skills(self, staff):
        ep = self.skills_ep.format(employee_id=staff.id)
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

    def fetch_experiences(self, staff):
        ep = self.experience_ep.format(employee_id=staff.id)
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

    def fetch_certifications(self, staff):
        ep = self.certifications_ep.format(employee_id=staff.id)
        res = self.session.get(ep)
        logger.debug(f"certs, status code - {res.status_code}")
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
            elems = res_json["data"]["identityDashProfileComponentsBySectionType"][
                "elements"
            ]
        except (KeyError, IndexError, TypeError) as e:
            logger.debug(res_json)
            return False
        if elems:
            cert_elems = elems[0]["components"]["pagedListComponent"]["components"][
                "elements"
            ]
            staff.certifications = self.parse_certifications(cert_elems)
        return True

    def fetch_schools(self, staff):
        ep = self.schools_ep.format(employee_id=staff.id)
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
        for elem in elements:
            entity = elem["components"]["entityComponent"]
            if not entity:
                break
            years = entity["caption"]["text"] if entity["caption"] else None
            school_name = entity["titleV2"]["text"]["text"]
            degree = entity["subtitle"]["text"] if entity["subtitle"] else None
            school = School(
                years=years,
                school=school_name,
                degree=degree,
            )
            schools.append(school)

        return schools

    def parse_certifications(self, sections):
        certs = []
        for section in sections:
            elem = section["components"]["entityComponent"]
            if not elem:
                break
            title = elem["titleV2"]["text"]["text"]
            issuer = elem["subtitle"]["text"] if elem["subtitle"] else None
            date_issued = (
                elem["caption"]["text"].replace("Issued ", "")
                if elem["caption"]
                else None
            )
            cert_id = (
                elem["metadata"]["text"].replace("Credential ID ", "")
                if elem["metadata"]
                else None
            )
            try:
                subcomp = elem["subComponents"]["components"][0]
                cert_link = subcomp["components"]["actionComponent"]["action"][
                    "navigationAction"
                ]["actionTarget"]
            except:
                cert_link = None
            cert = Certification(
                title=title,
                issuer=issuer,
                date_issued=date_issued,
                cert_link=cert_link,
                cert_id=cert_id,
            )
            certs.append(cert)

        return certs

    def fetch_staff(self, offset, company_id):
        ep = self.employees_ep.format(
            offset=offset,
            company_id=company_id,
            count=min(50, self.max_results),
            search=f"keywords:{quote(self.search_term)}," if self.search_term else "",
        )
        res = self.session.get(ep)
        logger.debug(f"employees, status code - {res.status_code}")
        if res.status_code == 429:
            return TooManyRequests("429 Too Many Requests")
        if not res.ok:
            return
        try:
            res_json = res.json()
        except json.decoder.JSONDecodeError:
            logger.debug(res.text[:200])
            return False

        try:
            elements = res_json["data"]["searchDashClustersByAll"]["elements"]
        except (KeyError, IndexError, TypeError):
            logger.debug(res_json)
            return False
        new_staff = self.parse_staff(elements) if elements else []
        logger.debug(
            f"Fetched {len(new_staff)} employees at offset {offset} / {self.num_staff}"
        )
        return new_staff

    def scrape_staff(
        self,
        company_name: str,
        search_term: str,
        extra_profile_data: bool,
        max_results: int,
    ):
        self.search_term = search_term
        self.company_name = company_name
        self.max_results = max_results
        company_id, staff_count = self.get_company_id(company_name)
        staff_list: list[Staff] = []
        self.num_staff = min(staff_count, max_results, 1000)
        for offset in range(0, self.num_staff, 50):
            staff = self.fetch_staff(offset, company_id)
            if not staff:
                break
            staff_list += staff
        logger.info(f"Found {len(staff_list)} staff")
        reduced_staff_list = staff_list[:max_results]

        non_restricted = list(
            filter(lambda x: x.name != "LinkedIn Member", reduced_staff_list)
        )

        def fetch_all_info_for_employee(employee: Staff, index: int):
            logger.info(
                f"Fetching employee data for {employee.id} {index} / {self.num_staff}"
            )

            with ThreadPoolExecutor(max_workers=5) as executor:
                tasks = {}
                tasks[executor.submit(self.fetch_employee, employee)] = "employee"
                tasks[executor.submit(self.fetch_skills, employee)] = "skills"
                tasks[executor.submit(self.fetch_experiences, employee)] = "experiences"
                tasks[executor.submit(self.fetch_certifications, employee)] = (
                    "certifications"
                )
                tasks[executor.submit(self.fetch_schools, employee)] = "schools"

                for future in as_completed(tasks):
                    result = future.result()
                    if isinstance(result, TooManyRequests):
                        logger.debug(f"API rate limit exceeded for {tasks[future]}")
                        raise TooManyRequests(
                            f"Stopping due to API rate limit exceeded for {tasks[future]}"
                        )

        if extra_profile_data:
            try:
                for i, employee in enumerate(non_restricted, start=1):
                    fetch_all_info_for_employee(employee, i)
            except TooManyRequests as e:
                logger.error(str(e))

        return reduced_staff_list

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
                    company = entity["subtitle"]["text"]
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

    def parse_skills(self, sections):
        skills = []
        for section in sections:
            elems = section["subComponent"]["components"]["pagedListComponent"][
                "components"
            ]["elements"]
            for elem in elems:
                entity = elem["components"]["entityComponent"]
                skill = entity["titleV2"]["text"]["text"]
                try:
                    endorsements = int(
                        entity["subComponents"]["components"][0]["components"][
                            "insightComponent"
                        ]["text"]["text"]["text"].replace(" endorsements", "")
                    )
                except:
                    endorsements = None
                skills.append(Skill(name=skill, endorsements=endorsements))
        return skills
