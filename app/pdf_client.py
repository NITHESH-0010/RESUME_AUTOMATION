"""
Converts resume HTML to a PDF using Gotenberg (self-hosted, free, no API
key, no usage caps) — the same free replacement for paid PDF APIs that the
n8n workflow's "Convert HTML to PDF" node used. Requires the `gotenberg`
container to be running (see docker-compose.yml).

On a free hosting tier (e.g. Render), Gotenberg's own service can spin
down after inactivity — the platform's edge proxy returns 429 for
several seconds to a minute while it wakes back up, before any request
reaches Gotenberg's own application code. The retry policy below is
tuned for that: 8 attempts, 15s apart, covering roughly two minutes —
comfortably past Render's own documented "50 seconds or more" cold-start
window. Locally, or on an always-on host, this just means the first
attempt succeeds immediately and the extra retries are simply unused.
"""
import logging

import httpx
from tenacity import retry, stop_after_attempt, wait_fixed

from app.config import settings

logger = logging.getLogger("resume_automation.pdf")


class PdfError(RuntimeError):
    pass


@retry(stop=stop_after_attempt(8), wait=wait_fixed(15), reraise=True)
async def html_to_pdf(html: str) -> bytes:
    url = f"{settings.gotenberg_url}/forms/chromium/convert/html"
    files = {"files": ("index.html", html.encode("utf-8"), "text/html")}

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(url, files=files)
        if response.status_code >= 400:
            logger.warning(
                "Gotenberg returned %s (likely still waking from sleep) — will retry.",
                response.status_code,
            )
            raise PdfError(f"Gotenberg error {response.status_code}: {response.text[:500]}")
        return response.content