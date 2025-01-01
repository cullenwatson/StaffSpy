from staffspy import LinkedInAccount
from staffspy.utils.utils import upload_to_clay

session_file = "session.pkl"
account = LinkedInAccount(session_file=session_file, log_level=2)

connections = account.scrape_connections(extra_profile_data=True, max_results=3)

clay_webhook_url = (
    "https://api.clay.com/v3/sources/webhook/pull-in-data-from-a-webhook-XXXXXXXXXXXXXX"
)
upload_to_clay(webhook_url=clay_webhook_url, data=connections)
