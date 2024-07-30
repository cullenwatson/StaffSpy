from datetime import datetime, date

from pydantic import BaseModel

from staffspy.utils import extract_emails_from_text


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
    search_term: str
    id: str
    name: str
    position: str | None = None

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
    is_connection: bool | None = None
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

    def get_top_skills(self):
        top_three_skills = []
        if self.skills:
            sorted_skills = sorted(self.skills, key=lambda x: x.endorsements, reverse=True)
            top_three_skills = [skill.name for skill in sorted_skills[:3]]
        top_three_skills += [None] * (3 - len(top_three_skills))
        return top_three_skills

    def to_dict(self):
        sorted_schools = sorted(
            self.schools, key=lambda x: (x.end_date is None, x.end_date), reverse=True
        ) if self.schools else []

        top_three_school_names = [school.school for school in sorted_schools[:3]]
        top_three_school_names += [None] * (3 - len(top_three_school_names))
        estimated_age = self.estimate_age_based_on_education()

        sorted_experiences = sorted(
            self.experiences,
            key=lambda x: (x.end_date is None, x.end_date),
            reverse=True
        ) if self.experiences else []

        top_three_companies = []
        seen_companies = set()
        for exp in sorted_experiences:
            if exp.company not in seen_companies:
                top_three_companies.append(exp.company)
                seen_companies.add(exp.company)
            if len(top_three_companies) == 3:
                break

        top_three_companies += [None] * (3 - len(top_three_companies))
        top_three_skills=self.get_top_skills()

        self.emails_in_bio=extract_emails_from_text(self.bio) if self.bio else None
        return {
            "search_term": self.search_term,
            "id": self.id,
            "profile_id": self.profile_id,
            "name": self.name,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "location": self.location,
            "position": self.position,
            "estimated_age": estimated_age,
            "followers": self.followers,
            "connections": self.connections,
            "mutuals": self.mutual_connections,
            "is_connection": self.is_connection,
            "premium": self.premium,
            "creator": self.creator,
            "influencer": self.influencer,
            "company_1": top_three_companies[0],
            "company_2": top_three_companies[1],
            "company_3": top_three_companies[2],
            "school_1": top_three_school_names[0],
            "school_2": top_three_school_names[1],
            "skill_1": top_three_skills[0],
            "skill_2": top_three_skills[1],
            "skill_3": top_three_skills[2],
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
            "emails_in_bio": ', '.join(self.emails_in_bio) if self.emails_in_bio else None,
            "potential_emails": ', '.join(self.potential_emails) if self.potential_emails else None,
            "profile_link": self.profile_link,
            "profile_photo": self.profile_photo,
        }

    def estimate_age_based_on_education(self):
        """Adds 18 to their first college start date"""
        college_words = ["uni", "college"]

        sorted_schools = sorted(
            [school for school in self.schools if school.start_date],
            key=lambda x: x.start_date,
        ) if self.schools else []

        current_date = datetime.now().date()
        for school in sorted_schools:
            if any(word in school.school.lower() for word in college_words) or school.degree:
                if school.start_date:
                    years_in_education = (current_date - school.start_date).days // 365
                    return int(18 + years_in_education)
        return None
