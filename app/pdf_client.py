"""
Converts resume HTML to a PDF using Gotenberg (self-hosted, free, no API
key, no usage caps) — the same free replacement for paid PDF APIs that the
n8n workflow's "Convert HTML to PDF" node used. Requires the `gotenberg`
container to be running (see docker-compose.yml).

On a free hosting tier (e.g. Render), a sleeping instance's proxy often
can't properly forward a heavy multipart POST while the container is
still waking up, and returns 429 for that request specifically — even
though a plain lightweight GET to the same host succeeds and is what
actually completes the wake-up. So before attempting the real PDF
conversion, we first ping Gotenberg's own /health endpoint with simple
GETs until it responds, THEN send the conversion request. Locally, or
on an always-on host, the health ping succeeds instantly and adds no
real delay.
"""
import logging

import httpx
from tenacity import retry, stop_after_attempt, wait_fixed

from app.config import settings

logger = logging.getLogger("resume_automation.pdf")


class PdfError(RuntimeError):
    pass


@retry(stop=stop_after_attempt(8), wait=wait_fixed(15), reraise=True)
async def _wait_until_awake() -> None:
    url = f"{settings.gotenberg_url}/health"
    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.get(url)
        if response.status_code >= 400:
            logger.warning(
                "Gotenberg health check returned %s — still waking, will retry.",
                response.status_code,
            )
            raise PdfError(f"Gotenberg not ready yet: {response.status_code}")


@retry(stop=stop_after_attempt(3), wait=wait_fixed(5), reraise=True)
async def html_to_pdf(html: str) -> bytes:
    await _wait_until_awake()

    url = f"{settings.gotenberg_url}/forms/chromium/convert/html"
    files = {"files": ("index.html", html.encode("utf-8"), "text/html")}

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(url, files=files)
        if response.status_code >= 400:
            logger.warning(
                "Gotenberg conversion returned %s — will retry.",
                response.status_code,
            )
            raise PdfError(f"Gotenberg error {response.status_code}: {response.text[:500]}")
        return response.content