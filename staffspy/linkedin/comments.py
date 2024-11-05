import json
import re
from datetime import datetime as dt

from staffspy.utils.exceptions import TooManyRequests
from staffspy.utils.models import Comment

from staffspy.utils.utils import logger


class CommentFetcher:

    def __init__(self, session):
        self.session = session
        self.endpoint = "https://www.linkedin.com/voyager/api/graphql?queryId=voyagerSocialDashComments.8cb29aedde780600a7ad17fc7ebb8277&queryName=SocialDashCommentsBySocialDetail&variables=(origins:List(),count:100,socialDetailUrn:urn%3Ali%3Afsd_socialDetail%3A%28urn%3Ali%3Aactivity%3A{post_id}%2Curn%3Ali%3Aactivity%3A7254884361622208512%2Curn%3Ali%3AhighlightedReply%3A-%29,sortOrder:REVERSE_CHRONOLOGICAL,start:{start})"
        self.post_id = None
        self.num_commments = 100

    def fetch_comments(self, post_id: str):
        all_comments = []
        self.post_id = post_id

        for i in range(0, 200_000, self.num_commments):
            logger.info(f"Fetching comments for post {post_id}, start {i}")

            ep = self.endpoint.format(post_id=post_id, start=i)
            res = self.session.get(ep)
            logger.debug(f"comments info, status code - {res.status_code}")

            if res.status_code == 429:
                raise TooManyRequests("429 Too Many Requests")
            if not res.ok:
                logger.debug(res.text[:200])
                return False
            try:
                comments_json = res.json()
            except json.decoder.JSONDecodeError:
                logger.debug(res.text[:200])
                return False

            comments, num_results = self.parse_comments(comments_json)
            all_comments.extend(comments)
            if not num_results:
                break

        return all_comments

    def parse_comments(self, comments_json: dict):
        """Parse the comment data from the employee profile."""
        comments = []
        for element in (
            results := comments_json.get("data", {})
            .get("socialDashCommentsBySocialDetail", {})
            .get("elements", [])
        ):
            internal_profile_id = (commenter := element["commenter"])[
                "commenterProfileId"
            ]
            name = commenter["title"]["text"]
            linkedin_id_match = re.search("/in/(.+)", commenter["navigationUrl"])
            linkedin_id = linkedin_id_match.group(1) if linkedin_id_match else None

            commentary = element.get("commentary", {}).get("text", "")
            comment_id = element["urn"].split(",")[-1].rstrip(")")
            num_likes = element["socialDetail"]["totalSocialActivityCounts"]["numLikes"]
            comment = Comment(
                post_id=self.post_id,
                comment_id=comment_id,
                internal_profile_id=internal_profile_id,
                public_profile_id=linkedin_id,
                name=name,
                text=commentary,
                num_likes=num_likes,
                created_at=dt.utcfromtimestamp(element["createdAt"] / 1000),
            )
            comments.append(comment)

        return comments, len(results)
