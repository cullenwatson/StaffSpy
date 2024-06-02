from pydantic import BaseModel


class Staff(BaseModel):
    search_term: str
    id: str
    name: str
    position: str | None = None

    profile_id: str | None = None
    profile_link: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    followers: int | None = None
    connections: int | None = None
    location: str | None = None
    company: str | None = None
    school: str | None = None
    influencer: bool | None = None
    creator: bool | None = None
    premium: bool | None = None
    profile_photo: str | None = None
    skills: list | None = None

    def to_dict(self):
        return {
            "search_term": self.search_term,
            "id": self.id,
            "name": self.name,
            "position": self.position,
            "profile_id": self.profile_id,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "company": self.company,
            "school": self.school,
            "location": self.location,
            "followers": self.followers,
            "connections": self.connections,
            "premium": self.premium,
            "creator": self.creator,
            "influencer": self.influencer,
            "skills": ", ".join(self.skills) if self.skills else None,
            "profile_link": self.profile_link,
            "profile_photo": self.profile_photo,
        }
