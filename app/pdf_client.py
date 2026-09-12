"""
Converts resume HTML to a PDF using Gotenberg (self-hosted, free, no API
key, no usage caps) — the same free replacement for paid PDF APIs that the
n8n workflow's "Convert HTML to PDF" node used. Requires the `gotenberg`
container to be running (see docker-compose.yml).
"""
import logging

import httpx
from tenacity import retry, stop_after_attempt, wait_fixed

from app.config import settings

logger = logging.getLogger("resume_automation.pdf")


class PdfError(RuntimeError):
    pass


@retry(stop=stop_after_attempt(2), wait=wait_fixed(2), reraise=True)
async def html_to_pdf(html: str) -> bytes:
    url = f"{settings.gotenberg_url}/forms/chromium/convert/html"
    files = {"files": ("index.html", html.encode("utf-8"), "text/html")}

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(url, files=files)
        if response.status_code >= 400:
            raise PdfError(f"Gotenberg error {response.status_code}: {response.text[:500]}")
        return response.content
