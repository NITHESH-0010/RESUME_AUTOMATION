# Resume AI — Automated Resume Builder

An end-to-end automation pipeline that takes form input, generates a
professional ATS-optimized resume using Google Gemini, converts it to a
polished PDF, and delivers it to the candidate by email — while logging
every submission to Google Sheets and notifying an admin via Telegram.

Originally prototyped as an n8n workflow, then rebuilt as a standalone
Python service (FastAPI) for full control over error handling, retries,
and deployment — with zero dependency on a hosted workflow platform.

## How it works

```
 Frontend (HTML/CSS/JS)
        │  POST /webhook/RESUME_BUILDER
        ▼
 FastAPI backend  ──▶  responds immediately (202) to the candidate
        │
        ▼  (background task)
 1. Log submission ──▶ Google Sheets
 2. Build prompt   ──▶ Gemini API           → generates resume HTML
 3. Convert HTML   ──▶ Gotenberg            → resume PDF
 4. Deliver        ──▶ Email (SMTP)  +  Telegram notification (parallel)
```

Each external call (Sheets, Gemini, PDF conversion, Email) has its own
retry policy and isolated error handling, so a failure in one step is
logged clearly without silently breaking the rest of the pipeline.

## Features

- **AI-generated resumes** — Gemini rewrites raw form input into a
  polished, ATS-friendly resume with proper structure and phrasing
- **Instant response, async processing** — the candidate isn't kept
  waiting on Gemini/PDF/email; the webhook responds immediately and the
  rest runs in the background
- **Automatic PDF generation** — via Gotenberg, self-hosted and free,
  no per-conversion API costs
- **Submission logging** — every entry recorded to Google Sheets for
  tracking and auditing
- **Dual notification** — candidate gets the resume by email, admin gets
  a Telegram alert, independently of one another
- **Config-driven** — all credentials live in `.env`; zero secrets in code

## Tech stack

| Layer | Technology |
|---|---|
| Backend | Python, FastAPI, httpx |
| AI generation | Google Gemini API |
| PDF conversion | Gotenberg (self-hosted, Docker) |
| Data logging | Google Sheets API (service account) |
| Notifications | Gmail SMTP, Telegram Bot API |
| Frontend | Vanilla HTML/CSS/JS (multi-step form) |
| Resilience | Tenacity (retry/backoff on every external call) |

## Project structure

```
resume-automation/
├── app/
│   ├── main.py             # FastAPI app, webhook route, static mount
│   ├── validators.py       # input validation & normalization
│   ├── gemini_client.py    # prompt construction + Gemini API call
│   ├── sheets_client.py    # Google Sheets logging
│   ├── pdf_client.py       # HTML → PDF via Gotenberg
│   ├── email_client.py     # resume delivery via SMTP
│   ├── telegram_client.py  # admin notification
│   ├── pipeline.py         # orchestrates the full submission flow
│   └── config.py           # centralized environment config
├── static/
│   ├── index.html
│   ├── style.css
│   └── script.js
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── .env.example
└── .gitignore
```

## Getting started

### 1. Clone and configure

```bash
git clone https://github.com/NITHESH-0010/resume-automation.git
cd resume-automation
cp .env.example .env
```

Fill in `.env` with your own credentials:

| Variable | Source |
|---|---|
| `GEMINI_API_KEY` | [Google AI Studio](https://aistudio.google.com) |
| `GOOGLE_SERVICE_ACCOUNT_FILE` | Google Cloud Console → Service Accounts (JSON key) |
| `GOOGLE_SHEET_ID` | Your target Sheet's URL |
| `GMAIL_ADDRESS` / `GMAIL_APP_PASSWORD` | [App Passwords](https://myaccount.google.com/apppasswords) |
| `TELEGRAM_BOT_TOKEN` / `TELEGRAM_CHAT_ID` | `@BotFather` / `@userinfobot` on Telegram |

Place your downloaded service account key as `service-account.json` in
the project root, and share your target Google Sheet with that
account's `client_email` (Editor access).

### 2. Run locally

```bash
pip install -r requirements.txt

# PDF conversion needs Gotenberg running separately:
docker run --rm -p 3000:3000 gotenberg/gotenberg:8
# then in .env: GOTENBERG_URL=http://localhost:3000

uvicorn app.main:app --reload --port 8000
```

Visit `http://localhost:8000` — the form and API are served from the
same origin.

### 3. Run with Docker Compose (app + Gotenberg together)

```bash
docker compose up --build
```

## Environment variables

See [`.env.example`](.env.example) for the full list with inline
explanations of where to obtain each value.

## Security notes

- `.env` and `service-account.json` are gitignored — never commit either
- Gmail delivery uses an App Password (requires 2FA), not the account's
  main password
- Sheets access uses a scoped service account, not a personal OAuth token

## License
Copyright (c) 2026 NITHESH
