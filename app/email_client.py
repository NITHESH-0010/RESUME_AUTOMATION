"""
Emails the finished PDF resume to the candidate via Brevo's HTTPS API
(port 443) instead of SMTP (port 587).

Render's free web services block outbound traffic to SMTP ports 25,
465, and 587 as an anti-spam measure (confirmed on Render's own
changelog) — so a Gmail App Password over smtplib, which worked
locally, cannot work on Render's free tier no matter how correct the
credentials are. Brevo's API runs over plain HTTPS, which is never
blocked.
"""
import base64
import logging

import httpx
from tenacity import retry, stop_after_attempt, wait_fixed

from app.config import settings

logger = logging.getLogger("resume_automation.email")

BREVO_URL = "https://api.brevo.com/v3/smtp/email"


class EmailError(RuntimeError):
    pass


@retry(stop=stop_after_attempt(2), wait=wait_fixed(3), reraise=True)
async def send_resume_email(to_email: str, full_name: str, pdf_bytes: bytes) -> None:
    if not settings.brevo_api_key or not settings.gmail_address:
        raise EmailError("BREVO_API_KEY or GMAIL_ADDRESS is not configured.")

    logger.info("Emailing resume to %s", to_email)

    safe_name = "".join(c for c in full_name if c.isalnum() or c in " _-").strip() or "resume"
    encoded_pdf = base64.b64encode(pdf_bytes).decode("ascii")

    payload = {
        "sender": {"email": settings.gmail_address, "name": "Resume AI"},
        "to": [{"email": to_email, "name": full_name}],
        "subject": "Your Professional ATS Resume",
        "textContent": (
            f"Hi {full_name},\n\n"
            "Your AI-generated, ATS-optimized resume is attached as a PDF.\n\n"
            "Best of luck with your applications!"
        ),
        "attachment": [
            {"content": encoded_pdf, "name": f"{safe_name}_Resume.pdf"}
        ],
    }
    headers = {
        "api-key": settings.brevo_api_key,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    async with httpx.AsyncClient(timeout=20.0) as client:
        response = await client.post(BREVO_URL, json=payload, headers=headers)
        if response.status_code >= 400:
            raise EmailError(f"Brevo error {response.status_code}: {response.text[:500]}")