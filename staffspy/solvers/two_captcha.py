from tenacity import retry_if_exception_type, stop_after_attempt, retry
from twocaptcha import TwoCaptcha, TimeoutException, ApiException

from staffspy.solvers.solver import Solver


class TwoCaptchaSolver(Solver):
    """ https://2captcha.com/ """

    attempt = 1

    @retry(stop=stop_after_attempt(5), retry=retry_if_exception_type((TimeoutException, ApiException)))
    def solve(self, blob_data: str, page_url:str=None):
        super().solve(blob_data, page_url)
        from staffspy.utils import logger

        logger.info(f'Waiting on 2Captcha to solve captcha attempt {self.attempt} / 5 ...')
        self.attempt+=1

        solver = TwoCaptcha(self.solver_api_key)

        result = solver.funcaptcha(sitekey=self.public_key,
                                  url=page_url,
                                   **{'data[blob]': blob_data},
                                   surl="https://iframe.arkoselabs.com"
                                  )
        logger.info(f'2Captcha finished solving captcha')
        return result['code']
