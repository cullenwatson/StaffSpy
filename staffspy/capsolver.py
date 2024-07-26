import requests
import json
import time
from tenacity import retry, stop_after_attempt, retry_if_result

public_key = "3117BF26-4762-4F5A-8ED9-A85E69209A46"
page_url = "https://iframe.arkoselabs.com"


def is_none(value):
    return value is None


@retry(stop=stop_after_attempt(10), retry=retry_if_result(is_none))
def capsolver(blob_data: str, api_key: str):
    from staffspy.utils import logger

    payload = {
        "clientKey": api_key,
        "task": {
            "type": 'FunCaptchaTaskProxyLess',
            "websitePublicKey": public_key,
            "websiteURL": page_url,
            "data": json.dumps({"blob": blob_data}) if blob_data else ''
        }
    }
    res = requests.post("https://api.capsolver.com/createTask", json=payload)
    resp = res.json()
    task_id = resp.get("taskId")
    if not task_id:
        logger.info(f"Failed to create task: {res.text}")
        return None
    logger.info(f"Got captcha solver taskId: {task_id} / Getting result...")

    while True:
        time.sleep(1)  # delay
        payload = {"clientKey": api_key, "taskId": task_id}
        res = requests.post("https://api.capsolver.com/getTaskResult", json=payload)
        resp = res.json()
        status = resp.get("status")
        if status == "ready":
            return resp.get("solution", {}).get('token')
        if status == "failed" or resp.get("errorId"):
            logger.info(f"Captcha solve failed! response: {res.text}")
            return None
