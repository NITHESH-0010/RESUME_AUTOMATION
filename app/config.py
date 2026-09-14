"""
Central place all credentials/config are loaded from environment variables.
Keeping this in one module means every other file just does:
    from app.config import settings
and never touches os.environ directly.
"""
import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()  # no-op in production if using docker-compose env_file, harmless


def _require(name: str) -> str:
    value = os.getenv(name, "")
    if not value:
        # We don't hard-crash at import time (so the app still boots and
        # /health works even if you haven't finished setup yet), but every
        # client module checks this and raises a clear error the moment
        # that specific integration is actually used.
        pass
    return value


@dataclass(frozen=True)
class Settings:
    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")
    gemini_model: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

    google_service_account_file: str = os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE", "")
    google_sheet_id: str = os.getenv("GOOGLE_SHEET_ID", "")
    google_sheet_name: str = os.getenv("GOOGLE_SHEET_NAME", "Sheet1")

    gmail_address: str = os.getenv("GMAIL_ADDRESS", "")
    brevo_api_key: str = os.getenv("BREVO_API_KEY", "")

    telegram_bot_token: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    telegram_chat_id: str = os.getenv("TELEGRAM_CHAT_ID", "")


settings = Settings()
