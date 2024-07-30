import json
import time

import requests
from tenacity import retry, stop_after_attempt, retry_if_result

from staffspy.solvers.solver import Solver


def is_none(value):
    return value is None


class CapSolver(Solver):
    """ https://www.capsolver.com/ """

    @retry(stop=stop_after_attempt(10), retry=retry_if_result(is_none))
    def solve(self, blob_data: str, page_url: str=None):
        from staffspy.utils import logger
        logger.info(f'Waiting on CapSolver to solve captcha...')

        payload = {
            "clientKey": self.solver_api_key,
            "task": {
                "type": 'FunCaptchaTaskProxyLess',
                "websitePublicKey": self.public_key,
                "websiteURL": self.page_url,
                "data": json.dumps({"blob": blob_data}) if blob_data else ''
            }
        }
        res = requests.post("https://api.capsolver.com/createTask", json=payload)
        resp = res.json()
        task_id = resp.get("taskId")
        if not task_id:
            raise Exception("CapSolver failed to create task, try another captcha solver like 2Captcha if this persists or use browser sign in `pip install staffspy[browser]` and then remove the username/password params to the scrape_staff()",res.text)
        logger.info(f"Received captcha solver taskId: {task_id} / Getting result...")

        while True:
            time.sleep(1)  # delay
            payload = {"clientKey": self.solver_api_key, "taskId": task_id}
            res = requests.post("https://api.capsolver.com/getTaskResult", json=payload)
            resp = res.json()
            status = resp.get("status")
            if status == "ready":
                logger.info(f'CapSolver finished solving captcha')
                return resp.get("solution", {}).get('token')
            if status == "failed" or resp.get("errorId"):
                logger.info(f"Captcha solve failed! response: {res.text}")
                return None
