import json
import re
import sys
from concurrent.futures import ThreadPoolExecutor
import utils
from models import Staff, Experience, Certification, Skill


class LinkedInScraper:
    company_id_ep = "https://www.linkedin.com/voyager/api/organization/companies?q=universalName&universalName="
    employees_ep = "https://www.linkedin.com/voyager/api/graphql?variables=(start:{offset},query:(flagshipSearchIntent:SEARCH_SRP,queryParameters:List((key:currentCompany,value:List({company_id})),(key:resultType,value:List(PEOPLE))),includeFiltersInResponse:false),count:{count})&queryId=voyagerSearchDashClusters.66adc6056cf4138949ca5dcb31bb1749"
    employee_ep = "https://www.linkedin.com/voyager/api/voyagerIdentityDashProfiles?count=1&decorationId=com.linkedin.voyager.dash.deco.identity.profile.TopCardComplete-138&memberIdentity={employee_id}&q=memberIdentity"
    skills_ep = "https://www.linkedin.com/voyager/api/graphql?queryId=voyagerIdentityDashProfileComponents.277ba7d7b9afffb04683953cede751fb&queryName=ProfileComponentsBySectionType&variables=(tabIndex:0,sectionType:skills,profileUrn:urn%3Ali%3Afsd_profile%3A{employee_id},count:50)"
    experience_ep = "https://www.linkedin.com/voyager/api/graphql?queryId=voyagerIdentityDashProfileComponents.277ba7d7b9afffb04683953cede751fb&queryName=ProfileComponentsBySectionType&variables=(tabIndex:0,sectionType:experience,profileUrn:urn%3Ali%3Afsd_profile%3A{employee_id},count:50)"
    certifications_ep = "https://www.linkedin.com/voyager/api/graphql?queryId=voyagerIdentityDashProfileComponents.277ba7d7b9afffb04683953cede751fb&queryName=ProfileComponentsBySectionType&variables=(tabIndex:0,sectionType:certifications,profileUrn:urn%3Ali%3Afsd_profile%3A{employee_id},count:50)"

    def __init__(self, session_file):
        self.session = utils.load_session(session_file)

        self.company_id = self.staff_count = None
        self.company_name = None
        self.max_results = None

    def get_company_id(self, company_name):
        res = self.session.get(f"{self.company_id_ep}{company_name}")
        if res.status_code != 200:
            raise Exception(
                f"Failed to find company {company_name}",
                res.status_code,
                res.text[:200],
            )
        print("Fetched company", res.status_code)
        try:
            response_json = res.json()
        except json.decoder.JSONDecodeError:
            print(res.text[:200])
            sys.exit()
        company = response_json["elements"][0]
        staff_count = company["staffCount"]
        company_id = company["trackingInfo"]["objectUrn"].split(":")[-1]
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
                        search_term=self.company_name,
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
        print("Fetched employee", emp.profile_id)

        try:
            emp.profile_link = (
                f'https://www.linkedin.com/in/{emp_dict["publicIdentifier"]}'
            )

            emp.profile_photo = profile_photo
            emp.first_name = emp_dict["firstName"]
            emp.last_name = emp_dict["lastName"]
            emp.followers = emp_dict.get("followingState", {}).get("followerCount")
            emp.connections = emp_dict["connections"]["paging"]["total"]
            emp.location = emp_dict["geoLocation"]["geo"]["defaultLocalizedName"]
            emp.company = emp_dict["profileTopPosition"]["elements"][0]["companyName"]
            edu_cards = emp_dict["profileTopEducation"]["elements"]
            if edu_cards:
                try:
                    emp.school = edu_cards[0].get(
                        "schoolName", edu_cards[0].get("school", {}).get("name")
                    )
                except Exception as e:
                    pass
            emp.influencer = emp_dict["influencer"]
            emp.creator = emp_dict["creator"]
            emp.premium = emp_dict["premium"]
        except Exception as e:
            pass

    def fetch_employee(self, base_staff):
        ep = self.employee_ep.format(employee_id=base_staff.id)
        res = self.session.get(ep)
        print("Fetched employee", base_staff.id, res.status_code)
        if not res.ok:
            print(res.text[:200])
            return False
        try:
            res_json = res.json()
        except json.decoder.JSONDecodeError:
            print(res.text[:200])
            return False

        try:
            employee_json = res_json["elements"][0]
        except (KeyError, IndexError, TypeError):
            print(res_json)
            return False

        self.parse_emp(base_staff, employee_json)
        return True

    def fetch_skills(self, staff):
        ep = self.skills_ep.format(employee_id=staff.id)
        print("Fetched employee skills", staff.profile_id)
        res = self.session.get(ep)
        if not res.ok:
            print(res.text[:200])
            return False
        try:
            res_json = res.json()
        except json.decoder.JSONDecodeError:
            print(res.text[:200])
            return False

        try:
            skills_json = res_json["data"][
                "identityDashProfileComponentsBySectionType"
            ]["elements"][0]["components"]["tabComponent"]["sections"]
        except (KeyError, IndexError, TypeError) as e:
            print(res_json)
            return False

        staff.skills = self.parse_skills(skills_json)
        return True

    def fetch_experiences(self, staff):
        ep = self.experience_ep.format(employee_id=staff.id)
        print("Fetched employee exps", staff.profile_id)
        res = self.session.get(ep)
        if not res.ok:
            print(res.text[:200])
            return False
        try:
            res_json = res.json()
        except json.decoder.JSONDecodeError:
            print(res.text[:200])
            return False

        try:
            skills_json = res_json["data"][
                "identityDashProfileComponentsBySectionType"
            ]["elements"][0]["components"]["pagedListComponent"]["components"][
                "elements"
            ]
        except (KeyError, IndexError, TypeError) as e:
            print(res_json)
            return False

        staff.experiences = self.parse_experiences(skills_json)
        return True

    def fetch_certifications(self, staff):
        ep = self.certifications_ep.format(employee_id=staff.id)
        print("Fetched employee certs", staff.profile_id)
        res = self.session.get(ep)
        if not res.ok:
            print(res.text[:200])
            return False
        try:
            res_json = res.json()
        except json.decoder.JSONDecodeError:
            print(res.text[:200])
            return False

        try:
            certs_json = res_json["data"]["identityDashProfileComponentsBySectionType"][
                "elements"
            ][0]["components"]["pagedListComponent"]["components"]["elements"]
        except (KeyError, IndexError, TypeError) as e:
            print(res_json)
            return False

        staff.certifications = self.parse_certifications(certs_json)
        return True

    def parse_certifications(self, sections):
        certs = []
        for section in sections:
            elem = section["components"]["entityComponent"]
            if not elem:
                break
            title = elem["titleV2"]["text"]["text"]
            issuer = elem["subtitle"]["text"]
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
            offset=offset, company_id=company_id, count=min(50, self.max_results)
        )
        res = self.session.get(ep)
        if not res.ok:
            return
        try:
            res_json = res.json()
        except json.decoder.JSONDecodeError:
            print(res.text[:200])
            return False

        try:
            elements = res_json["data"]["searchDashClustersByAll"]["elements"]
        except (KeyError, IndexError, TypeError):
            print(res_json)
            return False

        return self.parse_staff(elements) if elements else []

    def scrape_staff(
        self,
        company_name,
        profile_details,
        skills,
        experiences,
        certifications,
        max_results,
        num_threads,
    ):
        self.company_name = company_name
        self.max_results = max_results
        company_id, staff_count = self.get_company_id(company_name)
        staff_list: list[Staff] = []
        for offset in range(0, min(staff_count, max_results), 50):
            staff = self.fetch_staff(offset, company_id)
            if not staff:
                break
            staff_list += staff
        print(f"Found {len(staff_list)} staff")
        reduced_staff_list = staff_list[:max_results]

        non_restricted = list(
            filter(lambda x: x.name != "LinkedIn Member", reduced_staff_list)
        )
        if profile_details:
            with ThreadPoolExecutor(max_workers=num_threads) as executor:
                list(executor.map(self.fetch_employee, non_restricted))

        if skills:
            with ThreadPoolExecutor(max_workers=num_threads) as executor:
                list(executor.map(self.fetch_skills, non_restricted))

        if experiences:
            with ThreadPoolExecutor(max_workers=num_threads) as executor:
                list(executor.map(self.fetch_experiences, non_restricted))

        if certifications:
            with ThreadPoolExecutor(max_workers=num_threads) as executor:
                list(executor.map(self.fetch_certifications, non_restricted))

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
                if entity["caption"]:
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
                import traceback

                traceback.print_exc()
                pass
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


if __name__ == "__main__":
    scraper = LinkedInScraper()
    staff_result = scraper.scrape_staff("openai")
    pass
