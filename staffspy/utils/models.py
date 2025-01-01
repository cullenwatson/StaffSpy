from datetime import datetime, date

from pydantic import BaseModel
from datetime import datetime as dt

from staffspy.utils.utils import extract_emails_from_text


class Comment(BaseModel):
    post_id: str
    comment_id: str | None = None
    internal_profile_id: str | None = None
    public_profile_id: str | None = None
    name: str | None = None
    text: str | None = None
    num_likes: int | None = None
    created_at: dt | None = None

    def to_dict(self):
        return {
            "post_id": self.post_id,
            "comment_id": self.comment_id,
            "internal_profile_id": self.internal_profile_id,
            "public_profile_id": self.public_profile_id,
            "name": self.name,
            "text": self.text,
            "num_likes": self.num_likes,
            "created_at": self.created_at,
        }


class School(BaseModel):
    start_date: date | None = None
    end_date: date | None = None
    school: str | None = None
    degree: str | None = None

    def to_dict(self):
        return {
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "school": self.school,
            "degree": self.degree,
        }


class Skill(BaseModel):
    name: str | None = None
    endorsements: int | None = None
    passed_assessment: bool | None = None

    def to_dict(self):
        return {
            "name": self.name,
            "endorsements": self.endorsements if self.endorsements else 0,
            "passed_assessment": self.passed_assessment,
        }


class ContactInfo(BaseModel):
    email_address: str | None = None
    websites: list | None = None
    phone_numbers: list | None = None
    address: str | None = None
    birthday: str | None = None
    created_at: str | None = None

    def to_dict(self):
        return {
            "email_address": self.email_address,
            "websites": self.websites,
            "phone_numbers": self.phone_numbers,
            "address": self.address,
            "birthday": self.birthday,
            "created_at": self.created_at,
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
    start_date: date | None = None
    end_date: date | None = None

    def to_dict(self):
        return {
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "duration": self.duration,
            "title": self.title,
            "company": self.company,
            "location": self.location,
            "emp_type": self.emp_type,
        }


class Staff(BaseModel):
    urn: str | None = None
    search_term: str
    id: str
    name: str | None = None
    headline: str | None = None
    current_position: str | None = None

    profile_id: str | None = None
    profile_link: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    potential_emails: list | None = None
    bio: str | None = None
    emails_in_bio: str | None = None
    followers: int | None = None
    connections: int | None = None
    mutual_connections: int | None = None
    is_connection: str | None = None  # yes, no, pending
    location: str | None = None
    company: str | None = None
    school: str | None = None
    influencer: bool | None = None
    creator: bool | None = None
    premium: bool | None = None
    open_to_work: bool | None = None
    is_hiring: bool | None = None
    profile_photo: str | None = None
    banner_photo: str | None = None
    skills: list[Skill] | None = None
    experiences: list[Experience] | None = None
    certifications: list[Certification] | None = None
    contact_info: ContactInfo | None = None
    schools: list[School] | None = None
    languages: list[str] | None = None

    def get_top_skills(self):
        top_three_skills = []
        if self.skills:
            sorted_skills = sorted(
                self.skills, key=lambda x: x.endorsements, reverse=True
            )
            top_three_skills = [skill.name for skill in sorted_skills[:3]]
        top_three_skills += [None] * (3 - len(top_three_skills))
        return top_three_skills

    def to_dict(self):
        sorted_schools = (
            sorted(
                self.schools,
                key=lambda x: (x.end_date is None, x.end_date),
                reverse=True,
            )
            if self.schools
            else []
        )

        top_three_school_names = [school.school for school in sorted_schools[:3]]
        top_three_school_names += [None] * (3 - len(top_three_school_names))
        estimated_age = self.estimate_age_based_on_education()

        sorted_experiences = (
            sorted(
                self.experiences,
                key=lambda x: (x.end_date is None, x.end_date),
                reverse=True,
            )
            if self.experiences
            else []
        )

        top_three_companies = []
        seen_companies = set()
        for exp in sorted_experiences:
            if exp.company not in seen_companies:
                top_three_companies.append(exp.company)
                seen_companies.add(exp.company)
            if len(top_three_companies) == 3:
                break

        top_three_companies += [None] * (3 - len(top_three_companies))
        top_three_skills = self.get_top_skills()
        self.emails_in_bio = extract_emails_from_text(self.bio) if self.bio else None
        self.current_position = (
            sorted_experiences[0].title
            if len(sorted_experiences) > 0 and sorted_experiences[0].end_date is None
            else None
        )

        contact_info = self.contact_info.to_dict() if self.contact_info else {}
        return {
            "search_term": self.search_term,
            "id": self.id,
            "urn": self.urn,
            "profile_link": self.profile_link,
            "profile_id": self.profile_id,
            "name": self.name,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "location": self.location,
            "headline": self.headline,
            "estimated_age": estimated_age,
            "followers": self.followers,
            "connections": self.connections,
            "mutuals": self.mutual_connections,
            "is_connection": self.is_connection,
            "premium": self.premium,
            "creator": self.creator,
            "influencer": self.influencer,
            "open_to_work": self.open_to_work,
            "is_hiring": self.is_hiring,
            "current_position": self.current_position,
            "current_company": top_three_companies[0],
            "past_company_1": top_three_companies[1],
            "past_company_2": top_three_companies[2],
            "school_1": top_three_school_names[0],
            "school_2": top_three_school_names[1],
            "top_skill_1": top_three_skills[0],
            "top_skill_2": top_three_skills[1],
            "top_skill_3": top_three_skills[2],
            "bio": self.bio,
            "experiences": (
                [exp.to_dict() for exp in self.experiences]
                if self.experiences
                else None
            ),
            "schools": (
                [school.to_dict() for school in self.schools] if self.schools else None
            ),
            "skills": (
                [skill.to_dict() for skill in self.skills] if self.skills else None
            ),
            "certifications": (
                [cert.to_dict() for cert in self.certifications]
                if self.certifications
                else None
            ),
            "languages": self.languages,
            "emails_in_bio": (
                ", ".join(self.emails_in_bio) if self.emails_in_bio else None
            ),
            "potential_emails": self.potential_emails,
            "profile_photo": self.profile_photo,
            "banner_photo": self.banner_photo,
            "connection_created_at": contact_info.get("created_at"),
            "connection_email": contact_info.get("email_address"),
            "connection_phone_numbers": contact_info.get("phone_numbers"),
            "connection_websites": contact_info.get("websites"),
            "connection_street_address": contact_info.get("address"),
            "connection_birthday": contact_info.get("birthday"),
        }

    def estimate_age_based_on_education(self):
        """Adds 18 to their first college start date"""
        college_words = ["uni", "college"]

        sorted_schools = (
            sorted(
                [school for school in self.schools if school.start_date],
                key=lambda x: x.start_date,
            )
            if self.schools
            else []
        )

        current_date = datetime.now().date()
        for school in sorted_schools:
            if (
                any(word in school.school.lower() for word in college_words)
                or school.degree
            ):
                if school.start_date:
                    years_in_education = (current_date - school.start_date).days // 365
                    return int(18 + years_in_education)
        return None
