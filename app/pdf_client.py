"""
Converts resume HTML to a PDF using WeasyPrint — runs entirely inside
this app's own process, no separate PDF-conversion service required.

This replaces an earlier Gotenberg-based approach: on a free hosting
tier with two separate services (app + Gotenberg), the Gotenberg
service's own sleep/wake behavior behind Render's proxy caused
persistent, hard-to-diagnose 429 responses that never reached
Gotenberg's own application logs. Rendering the PDF in-process removes
that entire class of problem — there's nothing else that needs to be
awake or reachable.
"""
import asyncio
import logging

from weasyprint import HTML

logger = logging.getLogger("resume_automation.pdf")


class PdfError(RuntimeError):
    pass


def _render_sync(html: str) -> bytes:
    return HTML(string=html).write_pdf()


async def html_to_pdf(html: str) -> bytes:
    logger.info("Rendering resume HTML to PDF with WeasyPrint")
    try:
        # WeasyPrint is synchronous/CPU-bound; run it off the event loop.
        return await asyncio.to_thread(_render_sync, html)
    except Exception as exc:
        raise PdfError(f"WeasyPrint rendering failed: {exc}") from exc
