import json
import re
import sys

import utils
from models import Staff


class LinkedInScraper:
    company_id_ep = "https://www.linkedin.com/voyager/api/organization/companies?q=universalName&universalName="
    employees_ep = "https://www.linkedin.com/voyager/api/graphql?variables=(start:{offset},query:(flagshipSearchIntent:SEARCH_SRP,queryParameters:List((key:currentCompany,value:List({company_id})),(key:resultType,value:List(PEOPLE))),includeFiltersInResponse:false),count:50)&queryId=voyagerSearchDashClusters.66adc6056cf4138949ca5dcb31bb1749"  # 50 max
    employee_ep = "https://www.linkedin.com/voyager/api/voyagerIdentityDashProfiles?count=1&decorationId=com.linkedin.voyager.dash.deco.identity.profile.TopCardComplete-138&memberIdentity={employee_id}&q=memberIdentity"
    skills_ep = "https://www.linkedin.com/voyager/api/graphql?queryId=voyagerIdentityDashProfileComponents.277ba7d7b9afffb04683953cede751fb&queryName=ProfileComponentsBySectionType&variables=(tabIndex:0,sectionType:skills,profileUrn:urn%3Ali%3Afsd_profile%3A{employee_id},count:50)"

    def __init__(self, session_file):
        self.session = utils.load_session(session_file)

        self.company_id = self.staff_count = None

    def get_company_id(self, company_name):
        response = self.session.get(f"{self.company_id_ep}{company_name}")
        try:
            response_json = response.json()
        except json.decoder.JSONDecodeError:
            print(response.text[:200])
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
                staff += (Staff(id=linkedin_id, name=name, position=position),)
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

        emp.profile_id = (emp_dict["publicIdentifier"],)
        emp.profile_link = (
            f'https://www.linkedin.com/in/{emp_dict["publicIdentifier"]}',
        )
        emp.profile_photo = (profile_photo,)
        emp.first_name = (emp_dict["firstName"],)
        emp.last_name = (emp_dict["lastName"],)
        emp.followers = (emp_dict["followingState"]["followerCount"],)
        emp.connections = (emp_dict["connections"]["paging"]["total"],)
        emp.location = (emp_dict["geoLocation"]["geo"]["defaultLocalizedName"],)
        emp.company = (emp_dict["profileTopPosition"]["elements"][0]["companyName"],)
        emp.school = (emp_dict["profileTopEducation"]["elements"][0]["school"]["name"],)
        emp.influencer = (emp_dict["influencer"],)
        emp.creator = (emp_dict["creator"],)
        emp.premium = (emp_dict["premium"],)
        emp.public_profile = (emp_dict["privacySettings"]["showPublicProfile"],)
        emp.open_profile = (emp_dict["privacySettings"]["allowOpenProfile"],)
        emp.profile_viewer = (emp_dict["privacySettings"]["discloseAsProfileViewer"],)

    def fetch_employee(self, base_staff):
        ep = self.employee_ep.format(employee_id=base_staff.id)
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
            employee_json = res_json["elements"][0]
        except (KeyError, IndexError, TypeError):
            print(res_json)
            return False

        self.parse_emp(base_staff, employee_json)
        return True

    def fetch_skills(self, staff):
        ep = self.skills_ep.format(employee_id=staff.id)
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

    def fetch_staff(self, offset, company_id):
        ep = self.employees_ep.format(offset=offset, company_id=company_id)
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

    def scrape_staff(self, company_name, profile_details, skills, max_results):
        company_id, staff_count = self.get_company_id(company_name)
        staff_list: list[Staff] = []
        for offset in range(0, min(staff_count, max_results), 50):
            staff = self.fetch_staff(offset, company_id)
            if not staff:
                break
            staff_list += staff
        reduced_staff_list = staff_list[:max_results]

        non_restricted = list(
            filter(lambda x: x.name != "LinkedIn Member", reduced_staff_list)
        )
        if profile_details:
            for emp in non_restricted:
                res = self.fetch_employee(emp)
                if not res:
                    break

        if skills:
            for emp in non_restricted:
                res = self.fetch_skills(emp)
                if not res:
                    break
        return reduced_staff_list

    def parse_skills(self, sections):
        skills = []
        for section in sections:
            elems = section["subComponent"]["components"]["pagedListComponent"][
                "components"
            ]["elements"]
            for elem in elems:
                skill = elem["components"]["entityComponent"]["titleV2"]["text"]["text"]
                skills += (skill,)
        return skills


if __name__ == "__main__":
    scraper = LinkedInScraper()
    staff_result = scraper.scrape_staff("openai")
    pass
