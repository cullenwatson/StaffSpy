"""
staffspy.linkedin
~~~~~~~~~~~~~~~~~~~

This module contains routines to scrape LinkedIn.
"""

import json
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import quote

import requests

import staffspy.utils as utils
from staffspy.exceptions import TooManyRequests, BadCookies, GeoUrnNotFound
from staffspy.linkedin.certifications import CertificationFetcher
from staffspy.linkedin.employee import EmployeeFetcher
from staffspy.linkedin.employee_bio import EmployeeBioFetcher
from staffspy.linkedin.experiences import ExperiencesFetcher
from staffspy.linkedin.schools import SchoolsFetcher
from staffspy.linkedin.skills import SkillsFetcher
from staffspy.models import Staff
from staffspy.utils import logger


class LinkedInScraper:
    employees_ep = "https://www.linkedin.com/voyager/api/graphql?variables=(start:{offset},query:(flagshipSearchIntent:SEARCH_SRP,{search}queryParameters:List((key:currentCompany,value:List({company_id})),{location}(key:resultType,value:List(PEOPLE))),includeFiltersInResponse:false),count:{count})&queryId=voyagerSearchDashClusters.66adc6056cf4138949ca5dcb31bb1749"
    company_id_ep = "https://www.linkedin.com/voyager/api/organization/companies?q=universalName&universalName="
    company_search_ep = "https://www.linkedin.com/voyager/api/graphql?queryId=voyagerSearchDashClusters.02af3bc8bc85a169bb76bb4805d05759&queryName=SearchClusterCollection&variables=(query:(flagshipSearchIntent:SEARCH_SRP,keywords:{company},includeFiltersInResponse:false,queryParameters:(keywords:List({company}),resultType:List(COMPANIES))),count:10,origin:GLOBAL_SEARCH_HEADER,start:0)"
    location_id_ep = "https://www.linkedin.com/voyager/api/graphql?queryId=voyagerSearchDashReusableTypeahead.57a4fa1dd92d3266ed968fdbab2d7bf5&queryName=SearchReusableTypeaheadByType&variables=(query:(showFullLastNameForConnections:false,typeaheadFilterQuery:(geoSearchTypes:List(MARKET_AREA,COUNTRY_REGION,ADMIN_DIVISION_1,CITY))),keywords:{location},type:GEO,start:0)"
    get_company_from_user_ep = "https://www.linkedin.com/voyager/api/identity/profiles/{user_id}/profileView"

    def __init__(self, session: requests.Session):
        self.session = session
        (
            self.company_id,
            self.staff_count,
            self.num_staff,
            self.company_name,
            self.domain,
            self.max_results,
            self.search_term,
            self.location,
            self.raw_location,
        ) = (None, None, None, None, None, None, None, None, None)
        self.certs = CertificationFetcher(self.session)
        self.skills = SkillsFetcher(self.session)
        self.employees = EmployeeFetcher(self.session)
        self.schools = SchoolsFetcher(self.session)
        self.experiences = ExperiencesFetcher(self.session)
        self.bio = EmployeeBioFetcher(self.session)

    def search_companies(self, company_name):
        """Get the company id and staff count from the company name."""
        company_search_ep = self.company_search_ep.format(company=quote(company_name))
        self.session.headers['x-li-graphql-pegasus-client'] = "true"
        res = self.session.get(company_search_ep)
        self.session.headers.pop('x-li-graphql-pegasus-client', '')
        if res.status_code != 200:
            raise Exception(
                f"Failed to search for company {company_name}",
                res.status_code,
                res.text[:200],
            )
        logger.debug(f"Searched companies {res.status_code}")
        try:
            first_company = res.json()['data']['searchDashClustersByAll']['elements'][1]['items'][0]['item'][
                'entityResult']
            company_link = first_company['navigationUrl']
            company_name_id = re.search(r'/company/([^/]+)', company_link).group(1)
            company_name_new = first_company['title']['text']
        except Exception as e:
            raise Exception(f'Failed to load json in search_companies {str(e)}, Response: {res.text[:200]}')

        logger.info(
            f"Searched company {company_name} on LinkedIn and found company id - '{company_name_id}' with company name - '{company_name_new}'")
        return company_name_id

    def fetch_or_search_company(self, company_name):
        """Fetch the company details by name, or search if not found."""
        res = self.session.get(f"{self.company_id_ep}{company_name}")

        if res.status_code not in (200, 404):
            raise Exception(
                f"Failed to find company {company_name}",
                res.status_code,
                res.text[:200],
            )
        elif res.status_code == 404:
            logger.info(f"Failed to directly use company '{company_name}' as company id, now searching for the company")
            company_name = self.search_companies(company_name)
            res = self.session.get(f"{self.company_id_ep}{company_name}")
            if res.status_code != 200:
                raise Exception(
                    f"Failed to find company after performing a direct and generic search for {company_name}",
                    res.status_code,
                    res.text[:200],
                )

        logger.debug(f"Fetched company {res.status_code}")
        return res

    def get_company_id_and_staff_count(self, company_name: str):
        """Extract company id and staff count from the company details."""
        res = self.fetch_or_search_company(company_name)

        try:
            response_json = res.json()
        except json.decoder.JSONDecodeError:
            logger.debug(res.text[:200])
            raise Exception(f'Failed to load json in get_company_id_and_staff_count {res.text[:200]}')

        company = response_json["elements"][0]
        self.domain = utils.extract_base_domain(company["companyPageUrl"]) if company.get('companyPageUrl') else None
        staff_count = company["staffCount"]
        company_id = company["trackingInfo"]["objectUrn"].split(":")[-1]

        try:
            company_name = re.search(r'/company/([^/]+)', company['url']).group(1)
        except:
            pass

        logger.info(f"Found company '{company_name}' with {staff_count} staff")
        return company_id, staff_count

    def parse_staff(self, elements):
        """Parse the staff from the search results"""
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
                        search_term=" - ".join(
                            filter(
                                None,
                                [
                                    self.company_name,
                                    self.search_term,
                                    self.raw_location,
                                ],
                            )
                        ),
                    )
                )
        return staff

    def fetch_staff(self, offset, company_id):
        """Fetch the staff at the company using LinkedIn search"""
        ep = self.employees_ep.format(
            offset=offset,
            company_id=company_id,
            count=min(50, self.max_results),
            search=f"keywords:{quote(self.search_term)}," if self.search_term else "",
            location=(
                f"(key:geoUrn,value:List({self.location}))," if self.location else ""
            ),
        )
        res = self.session.get(ep)
        logger.debug(f"employees, status code - {res.status_code}")
        if res.status_code == 400:
            raise BadCookies("Outdated login, delete the session file to log in again")
        elif res.status_code == 429:
            raise TooManyRequests("429 Too Many Requests")
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

    def fetch_location_id(self):
        """Fetch the location id for the location to be used in LinkedIn search"""
        ep = self.location_id_ep.format(location=quote(self.raw_location))
        res = self.session.get(ep)
        try:
            res_json = res.json()
        except json.decoder.JSONDecodeError:
            if res.reason=='INKApi Error':
                raise Exception('Delete session file and log in again', res.status_code, res.text[:200], res.reason)
            raise GeoUrnNotFound("Failed to send request to get geo id", res.status_code, res.text[:200], res.reason)

        try:
            elems = res_json["data"]["searchDashReusableTypeaheadByType"]["elements"]
        except (KeyError, IndexError, TypeError):
            raise GeoUrnNotFound("Failed to locate geo id", res_json[:200])

        geo_id = None
        if elems:
            urn = elems[0]["trackingUrn"]
            m = re.search("urn:li:geo:(.+)", urn)
            if m:
                geo_id = m.group(1)
        if not geo_id:
            raise GeoUrnNotFound("Failed to parse geo id")
        self.location = geo_id

    def scrape_staff(
            self,
            company_name: str,
            search_term: str,
            location: str,
            extra_profile_data: bool,
            max_results: int,
    ):
        """Main driver function"""
        self.search_term = search_term
        self.company_name = company_name
        self.max_results = max_results
        self.raw_location = location

        company_id, staff_count = self.get_company_id_and_staff_count(company_name)
        staff_list: list[Staff] = []
        self.num_staff = min(staff_count, max_results, 1000)

        if self.raw_location:
            try:
                self.fetch_location_id()
            except GeoUrnNotFound as e:
                logger.error(str(e))
                return staff_list[:max_results]

        try:
            for offset in range(0, self.num_staff, 50):
                staff = self.fetch_staff(offset, company_id)
                if not staff:
                    break
                staff_list += staff
            logger.info(
                f"Found {len(staff_list)} staff at {company_name} {f'in {location}' if location else ''}"
            )
        except (BadCookies, TooManyRequests) as e:
            logger.error(str(e))
            return staff_list[:max_results]

        reduced_staff_list = staff_list[:max_results]

        non_restricted = list(
            filter(lambda x: x.name != "LinkedIn Member", reduced_staff_list)
        )

        if extra_profile_data:
            try:
                for i, employee in enumerate(non_restricted, start=1):
                    self.fetch_all_info_for_employee(employee, i)
            except (BadCookies, TooManyRequests) as e:
                logger.error(str(e))

        return reduced_staff_list

    def fetch_all_info_for_employee(self, employee: Staff, index: int):
        """Simultaniously fetch all the data for an employee"""
        logger.info(
            f"Fetching employee data for {employee.id} {index} / {self.num_staff}"
        )

        with ThreadPoolExecutor(max_workers=5) as executor:
            tasks = {}
            tasks[
                executor.submit(self.employees.fetch_employee, employee, self.domain)
            ] = "employee"
            tasks[executor.submit(self.skills.fetch_skills, employee)] = "skills"
            tasks[executor.submit(self.experiences.fetch_experiences, employee)] = (
                "experiences"
            )
            tasks[executor.submit(self.certs.fetch_certifications, employee)] = (
                "certifications"
            )
            tasks[executor.submit(self.schools.fetch_schools, employee)] = "schools"
            tasks[executor.submit(self.bio.fetch_employee_bio, employee)] = "bio"

            for future in as_completed(tasks):
                result = future.result()
                if isinstance(result, TooManyRequests):
                    logger.debug(f"API rate limit exceeded for {tasks[future]}")
                    raise TooManyRequests(
                        f"Stopping due to API rate limit exceeded for {tasks[future]}"
                    )

    def fetch_company_id_from_user(self, user_id: str):
        ep = self.get_company_from_user_ep.format(user_id=user_id)
        res = self.session.get(ep)
        try:
            res_json = res.json()
        except json.decoder.JSONDecodeError:
            logger.debug(res.text[:200])
            raise Exception(f'Failed to load json in fetch_comany_id_from_user', res.status_code)
        try:
            return res_json['positionView']['elements'][0]['company']['miniCompany']['universalName']
        except:
            raise Exception(f'Failed to fetch company for user_id {user_id}')
