"""
Logs each submission to Google Sheets — same columns/order as the n8n
"Log Submission to Google Sheets" node. Uses a service account (no OAuth
consent flow needed, which is the whole point of doing this headlessly).

Setup:
  1. Google Cloud Console -> new project (or reuse one) -> enable "Google Sheets API"
  2. IAM & Admin -> Service Accounts -> Create -> download the JSON key
  3. Open your Google Sheet -> Share -> paste the service account's
     "client_email" (looks like xxx@xxx.iam.gserviceaccount.com) -> Editor
  4. Point GOOGLE_SERVICE_ACCOUNT_FILE at that JSON key file
"""
import asyncio
import logging

from google.oauth2 import service_account
from googleapiclient.discovery import build
from tenacity import retry, stop_after_attempt, wait_fixed

from app.config import settings

logger = logging.getLogger("resume_automation.sheets")

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

# Same column order as the original n8n mapping.
COLUMN_ORDER = [
    "submission_id",
    "submitted_at",
    "full_name",
    "email",
    "phone",
    "linkedin",
    "github",
    "portfolio",
    "career_objective",
    "education",
    "skills",
    "projects",
    "certifications",
    "internships",
    "achievements",
    "languages",
]


class SheetsError(RuntimeError):
    pass


def _append_sync(data: dict) -> None:
    if not settings.google_service_account_file or not settings.google_sheet_id:
        raise SheetsError(
            "GOOGLE_SERVICE_ACCOUNT_FILE or GOOGLE_SHEET_ID is not configured."
        )

    creds = service_account.Credentials.from_service_account_file(
        settings.google_service_account_file, scopes=SCOPES
    )
    service = build("sheets", "v4", credentials=creds, cache_discovery=False)

    row = [data.get(col, "") for col in COLUMN_ORDER]
    range_ = f"{settings.google_sheet_name}!A:P"

    service.spreadsheets().values().append(
        spreadsheetId=settings.google_sheet_id,
        range=range_,
        valueInputOption="USER_ENTERED",
        insertDataOption="INSERT_ROWS",
        body={"values": [row]},
    ).execute()


@retry(stop=stop_after_attempt(2), wait=wait_fixed(2), reraise=True)
async def append_submission(data: dict) -> None:
    logger.info("Logging submission %s to Google Sheets", data["submission_id"])
    # google-api-python-client is synchronous; run it off the event loop.
    await asyncio.to_thread(_append_sync, data)
