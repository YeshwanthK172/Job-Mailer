from dataclasses import dataclass, field


@dataclass
class Profile:
    name: str
    email: str
    current_role: str
    grad_year: int
    target_roles: list
    locations: list
    experience_years: float
    experience_text: str
    resume_text: str
    resume_bytes: bytes
    resume_name: str
    skills: list = field(default_factory=list)


@dataclass
class Job:
    title: str
    company: str
    location: str
    url: str
    description: str = ""
    source: str = ""
    posted: str = ""
    score: float = 0.0
    eligible: bool = False
    reasons: list = field(default_factory=list)


@dataclass
class Contact:
    company: str
    email: str
    name: str = ""
    position: str = ""
    confidence: int = 0
