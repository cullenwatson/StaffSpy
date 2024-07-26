import json
import logging

from staffspy.exceptions import TooManyRequests
from staffspy.models import Certification

logger = logging.getLogger(__name__)


class CertificationFetcher:
    def __init__(self, session):
        self.session = session
        self.endpoint = "https://www.linkedin.com/voyager/api/graphql?queryId=voyagerIdentityDashProfileComponents.277ba7d7b9afffb04683953cede751fb&queryName=ProfileComponentsBySectionType&variables=(tabIndex:0,sectionType:certifications,profileUrn:urn%3Ali%3Afsd_profile%3A{employee_id},count:50)"

    def fetch_certifications(self, staff):
        ep = self.endpoint.format(employee_id=staff.id)
        res = self.session.get(ep)
        logger.debug(f"certs, status code - {res.status_code}")
        if res.status_code == 429:
            raise TooManyRequests("429 Too Many Requests")
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
