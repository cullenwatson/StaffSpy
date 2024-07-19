from datetime import datetime

from pydantic import BaseModel


class School(BaseModel):
    years: str | None = None
    school: str | None = None
    degree: str | None = None

    def to_dict(self):
        return {
            "years": self.years,
            "school": self.school,
            "degree": self.degree,
        }


class Skill(BaseModel):
    name: str | None = None
    endorsements: int | None = None

    def to_dict(self):
        return {
            "name": self.name,
            "endorsements": self.endorsements if self.endorsements else 0,
        }


class Certification(BaseModel):
    title: str | None = None
    issuer: str | None = None
    date_issued: str | None = None
    cert_id: str | None = None
    cert_link: str | None = None

    def to_dict(self):
        return {
            "title": self.title,
            "issuer": self.issuer,
            "date_issued": self.date_issued,
            "cert_id": self.cert_id,
            "cert_link": self.cert_link,
        }


class Experience(BaseModel):
    duration: str | None = None
    title: str | None = None
    company: str | None = None
    location: str | None = None
    emp_type: str | None = None
    from_date: datetime | None = None
    to_date: datetime | None = None

    def to_dict(self):
        return {
            "from_date": self.from_date.strftime("%b %Y") if self.from_date else None,
            "to_date": self.to_date.strftime("%b %Y") if self.to_date else None,
            "duration": self.duration,
            "title": self.title,
            "company": self.company,
            "location": self.location,
            "emp_type": self.emp_type,
        }


class Staff(BaseModel):
    search_term: str
    id: str
    name: str
    position: str | None = None

    profile_id: str | None = None
    profile_link: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    potential_email: str | None = None
    estimated_age: int | None = None
    bio: str | None = None
    followers: int | None = None
    connections: int | None = None
    mutual_connections: int | None = None
    location: str | None = None
    company: str | None = None
    school: str | None = None
    influencer: bool | None = None
    creator: bool | None = None
    premium: bool | None = None
    profile_photo: str | None = None
    skills: list[Skill] | None = None
    experiences: list[Experience] | None = None
    certifications: list[Certification] | None = None
    schools: list[School] | None = None

    def to_dict(self):
        return {
            "search_term": self.search_term,
            "id": self.id,
            "name": self.name,
            "position": self.position,
            "profile_id": self.profile_id,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "potential_email": self.potential_email,
            "company": self.company,
            "school": self.school,
            "location": self.location,
            "estimated_age": self.estimated_age,
            "followers": self.followers,
            "connections": self.connections,
            "mutuals": self.mutual_connections if self.mutual_connections else 0,
            "premium": self.premium,
            "creator": self.creator,
            "influencer": self.influencer,
            "profile_link": self.profile_link,
            "bio": self.bio,
            "skills": (
                [skill.to_dict() for skill in self.skills] if self.skills else None
            ),
            "experiences": (
                [exp.to_dict() for exp in self.experiences]
                if self.experiences
                else None
            ),
            "schools": (
                [school.to_dict() for school in self.schools] if self.schools else None
            ),
            "certifications": (
                [cert.to_dict() for cert in self.certifications]
                if self.certifications
                else None
            ),
            "profile_photo": self.profile_photo,
        }
