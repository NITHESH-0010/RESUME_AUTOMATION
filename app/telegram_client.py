"""
Sends an admin-side Telegram notification when a resume is generated
(not the candidate's own Telegram — the form doesn't collect one).
Get a bot token from @BotFather and your chat ID from @userinfobot.
"""
import logging

import httpx

from app.config import settings

logger = logging.getLogger("resume_automation.telegram")


class TelegramError(RuntimeError):
    pass


async def notify_admin(data: dict) -> None:
    if not settings.telegram_bot_token or not settings.telegram_chat_id:
        logger.warning("Telegram not configured — skipping admin notification.")
        return

    text = (
        "\U0001F4C4 New resume generated\n"
        f"Name: {data['full_name']}\n"
        f"Email: {data['email']}\n"
        f"Submission ID: {data['submission_id']}"
    )
    url = f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendMessage"

    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.post(
            url, json={"chat_id": settings.telegram_chat_id, "text": text}
        )
        if response.status_code >= 400:
            raise TelegramError(f"Telegram error {response.status_code}: {response.text[:300]}")
