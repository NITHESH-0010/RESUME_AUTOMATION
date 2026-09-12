"""
Builds the same prompt the n8n "Build Gemini Prompt" node built, sends it to
Gemini, and extracts/validates the returned HTML — same logic as the
"Extract & Validate Resume HTML" Code node.
"""
import logging

import httpx
from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_exception_type

from app.config import settings

logger = logging.getLogger("resume_automation.gemini")

GEMINI_URL_TEMPLATE = (
    "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
)


class GeminiError(RuntimeError):
    pass


def build_prompt(data: dict) -> str:
    return f"""You are a world-class ATS Resume Writer, Senior Technical Recruiter, Hiring Manager, Career Coach, and Professional Resume Designer.

Your task is to create an exceptionally professional, ATS-optimized, recruiter-friendly resume using the candidate information provided below.

OBJECTIVE:
Create a premium-quality resume suitable for internships and entry-level roles in Artificial Intelligence, Data Science, Machine Learning, Software Development, Data Analytics, and related technology domains.

INSTRUCTIONS:
1. Create a powerful Professional Summary that highlights technical strengths, problem-solving ability, learning mindset, and career aspirations.
2. Rewrite and enhance all provided content professionally. Do not simply copy raw user input.
3. Make project descriptions highly professional by including: Project Objective, Technologies Used, Key Features, Impact and Outcomes.
4. Organize the resume into: Header, Contact Information, Professional Summary, Education, Technical Skills, Projects, Certifications, Internships / Experience, Achievements, Leadership & Extracurricular Activities, Languages.
5. If Certifications, Experience, or Achievements are missing, intelligently create professional placeholders.
6. Use strong action verbs (Developed, Designed, Implemented, Built, Optimized, Engineered, Automated, Analyzed, Created, Integrated, Deployed).
7. ATS OPTIMIZATION: naturally include keywords common in AI Engineer, Data Scientist, ML Engineer, Data Analyst, and Software Developer job descriptions.
8. DESIGN REQUIREMENTS: modern corporate appearance, premium professional layout, white background, professional blue accent color (#2563EB), excellent spacing and typography, clear section hierarchy, ATS compatible structure.
9. HTML REQUIREMENTS: return a complete HTML document, CSS inside a <style> tag, A4 print optimized, responsive, PDF-friendly, semantic HTML.
10. IMPORTANT: do not use markdown, do not use code blocks, do not provide explanations, return ONLY valid HTML.

Candidate Information:
Name: {data['full_name']}
Email: {data['email']}
Phone: {data['phone']}
LinkedIn: {data['linkedin']}
GitHub: {data['github']}
Portfolio: {data['portfolio']}
Career Objective: {data['career_objective']}
Education: {data['education']}
Skills: {data['skills']}
Projects: {data['projects']}
Certifications: {data['certifications']}
Internships: {data['internships']}
Achievements: {data['achievements']}
Languages: {data['languages']}"""


@retry(
    stop=stop_after_attempt(3),
    wait=wait_fixed(3),
    retry=retry_if_exception_type((httpx.HTTPError, GeminiError)),
    reraise=True,
)
async def _call_gemini(prompt: str) -> dict:
    if not settings.gemini_api_key:
        raise GeminiError("GEMINI_API_KEY is not set.")

    url = GEMINI_URL_TEMPLATE.format(model=settings.gemini_model)
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.4},
    }
    headers = {
        "Content-Type": "application/json",
        "x-goog-api-key": settings.gemini_api_key,
    }

    async with httpx.AsyncClient(timeout=45.0) as client:
        response = await client.post(url, json=payload, headers=headers)
        if response.status_code >= 400:
            raise GeminiError(f"Gemini API error {response.status_code}: {response.text[:500]}")
        return response.json()


def _extract_html(response: dict) -> str:
    try:
        html = response["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError, TypeError):
        raise GeminiError(
            f"Gemini API did not return valid resume content: {str(response)[:500]}"
        )

    html = html.strip()
    # Strip accidental markdown code fences if the model adds them.
    if html.lower().startswith("```html"):
        html = html[7:]
    if html.endswith("```"):
        html = html[:-3]
    html = html.strip()

    if "<html" not in html.lower():
        raise GeminiError("Gemini response did not contain a valid HTML document.")

    return html


async def generate_resume_html(data: dict) -> str:
    prompt = build_prompt(data)
    logger.info("Calling Gemini for submission %s", data["submission_id"])
    response = await _call_gemini(prompt)
    return _extract_html(response)
