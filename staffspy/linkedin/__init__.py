import json
import sys

import utils
from models import Staff


class LinkedInScraper:
    company_id_ep = 'https://www.linkedin.com/voyager/api/organization/companies?q=universalName&universalName='
    employees_ep = 'https://www.linkedin.com/voyager/api/graphql?variables=(start:{offset},query:(flagshipSearchIntent:SEARCH_SRP,queryParameters:List((key:currentCompany,value:List({company_id})),(key:resultType,value:List(PEOPLE))),includeFiltersInResponse:false),count:50)&queryId=voyagerSearchDashClusters.66adc6056cf4138949ca5dcb31bb1749'
    session_file = '/Users/pc/PycharmProjects/staffspy/session.pkl'

    def __init__(self):
        self.session = utils.load_session(self.session_file)

        self.company_id = self.staff_count = None

    def get_company_id(self, company_name):
        response = self.session.get(f'{self.company_id_ep}{company_name}')
        try:
            response_json = response.json()
        except json.decoder.JSONDecodeError:
            print(response.text[:200])
            sys.exit()
        company = response_json["elements"][0]
        self.staff_count = company['staffCount']
        company_id = company['trackingInfo']['objectUrn'].split(':')[-1]
        return company_id

    def parse_staff(self, elements):
        staff = []

        for elem in elements:
            for card in elem.get('items', []):
                person = card.get('item', {}).get('entityResult', {})
                if not person: continue

                name = person['title']['text'].strip()
                position = person.get('primarySubtitle', {}).get('text', '') if person.get('primarySubtitle') else ''
                staff += Staff(
                    name=name,
                    position=position
                ),
        return staff

    def fetch_staff(self, page, company_id):
        ep = self.employees_ep.format(offset=page * 50, company_id=company_id)
        res = self.session.get(ep)
        if not res.ok:
            return
        try:
            res_json = res.json()
        except json.decoder.JSONDecodeError:
            print(res.text[:200])
            return False

        try:
            elements = res_json['data']['searchDashClustersByAll']['elements']
        except (KeyError, IndexError, TypeError):
            print(res_json)
            return False

        staff = self.parse_staff(elements)
        return staff

    def scrape_staff(self, company_name):
        company_id = self.get_company_id(company_name)
        staff_list = []
        for page in range(2):
            staff = self.fetch_staff(page, company_id)
            if not staff:
                break
            staff_list += staff
        return staff_list


if __name__ == '__main__':
    scraper = LinkedInScraper()
    scraper.scrape_staff('openai')
    pass


