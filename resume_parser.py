import io
import re

from pypdf import PdfReader
import docx

COMMON_SKILLS = [
    "python", "java", "javascript", "typescript", "c++", "c#", "go", "rust", "sql",
    "mysql", "postgresql", "mongodb", "html", "css", "react", "angular", "vue",
    "node", "django", "flask", "fastapi", "spring", "aws", "azure", "gcp", "docker",
    "kubernetes", "git", "linux", "machine learning", "deep learning", "nlp",
    "pandas", "numpy", "tensorflow", "pytorch", "scikit-learn", "tableau",
    "power bi", "excel", "data analysis", "data science", "devops", "ci/cd",
    "rest", "api", "microservices", "selenium", "testing", "manual testing",
    "automation", "figma", "ui", "ux", "android", "ios", "flutter", "swift",
    "kotlin", "php", "laravel", "salesforce", "sap", "spark", "hadoop", "kafka",
    "networking", "cybersecurity", "agile", "scrum", "communication",
]


def extract_text(data: bytes, filename: str) -> str:
    name = filename.lower()
    if name.endswith(".pdf"):
        reader = PdfReader(io.BytesIO(data))
        return "\n".join((p.extract_text() or "") for p in reader.pages)
    if name.endswith(".docx"):
        d = docx.Document(io.BytesIO(data))
        return "\n".join(p.text for p in d.paragraphs)
    return data.decode("utf-8", errors="ignore")


def extract_skills(text: str) -> list:
    low = text.lower()
    found = []
    for s in COMMON_SKILLS:
        if re.search(r"(?<![a-z0-9])" + re.escape(s) + r"(?![a-z0-9])", low):
            found.append(s)
    return found
