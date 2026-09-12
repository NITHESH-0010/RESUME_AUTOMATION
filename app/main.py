import logging

from fastapi import BackgroundTasks, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.pipeline import process_submission
from app.validators import ValidationError, validate_and_normalize

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("resume_automation.main")

app = FastAPI(title="Resume Automation")

# Same as the n8n webhook node's allowedOrigins: "*"
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/webhook/RESUME_BUILDER")
async def resume_builder(request: Request, background_tasks: BackgroundTasks):
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body.")

    try:
        data = validate_and_normalize(body)
    except ValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    logger.info("Accepted submission %s (%s)", data["submission_id"], data["email"])

    # Respond immediately, exactly like "Acknowledge Request Immediately"
    # in n8n — the rest of the pipeline runs after the response is sent.
    background_tasks.add_task(process_submission, data)

    return {
        "status": "success",
        "message": "Your resume is being generated and will be emailed to you shortly.",
        "submission_id": data["submission_id"],
    }


# Serves index.html / style.css / script.js at "/". Registered last so it
# doesn't shadow the /webhook and /health routes above.
app.mount("/", StaticFiles(directory="static", html=True), name="static")
