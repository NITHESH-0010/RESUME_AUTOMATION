"""
Runs after the webhook has already responded to the caller — mirrors the
n8n graph exactly:

  Validate -> [respond immediately, Log to Sheets]
  Log to Sheets -> Build Prompt -> Gemini -> Extract HTML -> HTML->PDF
  HTML->PDF -> [Email candidate, Notify admin]  (both run, independently)
"""
import asyncio
import logging

from app.email_client import send_resume_email
from app.gemini_client import generate_resume_html
from app.pdf_client import html_to_pdf
from app.sheets_client import append_submission
from app.telegram_client import notify_admin

logger = logging.getLogger("resume_automation.pipeline")


async def process_submission(data: dict) -> None:
    submission_id = data["submission_id"]

    # Step 1: log to Sheets. In the original workflow this node has no
    # continueOnFail set, so a failure here (after retries) halts the run.
    try:
        await append_submission(data)
    except Exception:
        logger.exception("Sheets logging failed for %s — aborting.", submission_id)
        return

    # Step 2: generate resume HTML via Gemini.
    try:
        html = await generate_resume_html(data)
    except Exception:
        logger.exception("Gemini generation failed for %s — aborting.", submission_id)
        return

    # Step 3: convert HTML to PDF via Gotenberg.
    try:
        pdf_bytes = await html_to_pdf(html)
    except Exception:
        logger.exception("PDF conversion failed for %s — aborting.", submission_id)
        return

    # Step 4: email candidate + notify admin — these run independently,
    # same as the two parallel branches in the n8n graph, so one failing
    # doesn't block the other.
    results = await asyncio.gather(
        send_resume_email(data["email"], data["full_name"], pdf_bytes),
        notify_admin(data),
        return_exceptions=True,
    )
    for label, result in zip(("email", "telegram"), results):
        if isinstance(result, Exception):
            logger.error("%s step failed for %s: %s", label, submission_id, result)

    logger.info("Submission %s completed.", submission_id)
