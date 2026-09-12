"""
Emails the finished PDF resume to the candidate. Uses plain SMTP with a
Gmail App Password instead of the Gmail API/OAuth2 that n8n used — far
simpler to automate headlessly (no browser consent flow, no token refresh).

Setup: enable 2FA on the Gmail account, then create an App Password at
https://myaccount.google.com/apppasswords
"""
import asyncio
import logging
import smtplib
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from tenacity import retry, stop_after_attempt, wait_fixed

from app.config import settings

logger = logging.getLogger("resume_automation.email")


class EmailError(RuntimeError):
    pass


def _send_sync(to_email: str, full_name: str, pdf_bytes: bytes) -> None:
    if not settings.gmail_address or not settings.gmail_app_password:
        raise EmailError("GMAIL_ADDRESS or GMAIL_APP_PASSWORD is not configured.")

    msg = MIMEMultipart()
    msg["From"] = settings.gmail_address
    msg["To"] = to_email
    msg["Subject"] = "Your Professional ATS Resume"

    body = (
        f"Hi {full_name},\n\n"
        "Your AI-generated, ATS-optimized resume is attached as a PDF.\n\n"
        "Best of luck with your applications!"
    )
    msg.attach(MIMEText(body, "plain"))

    attachment = MIMEApplication(pdf_bytes, _subtype="pdf")
    safe_name = "".join(c for c in full_name if c.isalnum() or c in " _-").strip() or "resume"
    attachment.add_header(
        "Content-Disposition", "attachment", filename=f"{safe_name}_Resume.pdf"
    )
    msg.attach(attachment)

    with smtplib.SMTP("smtp.gmail.com", 587, timeout=20) as server:
        server.starttls()
        server.login(settings.gmail_address, settings.gmail_app_password)
        server.send_message(msg)


@retry(stop=stop_after_attempt(2), wait=wait_fixed(3), reraise=True)
async def send_resume_email(to_email: str, full_name: str, pdf_bytes: bytes) -> None:
    logger.info("Emailing resume to %s", to_email)
    await asyncio.to_thread(_send_sync, to_email, full_name, pdf_bytes)
