"""
Direct Python port of the n8n "Validate & Normalize Input" Code node.
Same required fields, same email regex, same default placeholder text.
"""
import re
import uuid
from datetime import datetime, timezone

EMAIL_PATTERN = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
REQUIRED_FIELDS = ("full_name", "email")


class ValidationError(ValueError):
    pass


def _clean(value) -> str:
    return str(value or "").strip()


def validate_and_normalize(body: dict) -> dict:
    missing = [f for f in REQUIRED_FIELDS if not _clean(body.get(f))]
    if missing:
        raise ValidationError(f"Missing required field(s): {', '.join(missing)}")

    email = _clean(body.get("email"))
    if not EMAIL_PATTERN.match(email):
        raise ValidationError("Invalid email address format.")

    return {
        "full_name": _clean(body.get("full_name")),
        "email": email,
        "phone": _clean(body.get("phone")),
        "linkedin": _clean(body.get("linkedin")),
        "github": _clean(body.get("github")),
        "portfolio": _clean(body.get("portfolio")),
        "career_objective": _clean(body.get("career_objective")),
        "education": _clean(body.get("education")),
        "skills": _clean(body.get("skills")),
        "projects": _clean(body.get("projects")),
        "certifications": _clean(body.get("certifications"))
        or "Additional certifications available upon request.",
        "internships": _clean(body.get("internships"))
        or "Relevant internship experience available upon request.",
        "achievements": _clean(body.get("achievements"))
        or "Additional achievements available upon request.",
        "languages": _clean(body.get("languages")) or "English (Professional)",
        "submission_id": str(uuid.uuid4()),
        "submitted_at": datetime.now(timezone.utc).isoformat(),
    }
