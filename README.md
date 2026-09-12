# Resume Automation (Python port of RESUME_AUTOMATION_v3 n8n workflow)

A FastAPI backend that replaces the n8n workflow 1:1, plus the existing
frontend (`static/index.html`, `style.css`, `script.js`) served from the
same app — one deployment, one URL, no separate n8n instance to host.

## What it does

1. `POST /webhook/RESUME_BUILDER` receives the form submission
2. Validates required fields (`full_name`, `email`) — same rules as before
3. **Responds immediately** with a submission ID (candidate isn't kept waiting)
4. In the background: logs to Google Sheets → generates resume HTML with
   Gemini → converts HTML to PDF via Gotenberg → emails the PDF to the
   candidate → notifies you on Telegram

## 1. Get your 4 credentials

| # | Credential | Where to get it |
|---|---|---|
| 1 | **Gemini API key** | [aistudio.google.com](https://aistudio.google.com) → "Get API key" |
| 2 | **Google service account JSON** | Google Cloud Console → IAM & Admin → Service Accounts → Create → Keys → Add Key (JSON). Then enable the **Google Sheets API** for that project, and **share your Google Sheet** with the service account's email (`...@...iam.gserviceaccount.com`) as an Editor |
| 3 | **Gmail App Password** | Enable 2FA on the sending Gmail account, then create one at [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords) |
| 4 | **Telegram bot token + chat ID** | Message `@BotFather` → `/newbot` → copy the token. Message `@userinfobot` to get your numeric chat ID |

Save the service account JSON as `service-account.json` in this folder
(it's already gitignored-equivalent via the `.env` pattern — **never commit
it**).

## 2. Configure environment

```bash
cp .env.example .env
# then fill in all 4 credentials in .env
```

## 3. Run locally (no Docker)

```bash
pip install -r requirements.txt

# You'll also need a local Gotenberg instance for PDF conversion:
docker run --rm -p 3000:3000 gotenberg/gotenberg:8
# then in .env set: GOTENBERG_URL=http://localhost:3000

uvicorn app.main:app --reload --port 8000
```

Open `http://localhost:8000` — the frontend and API are served from the
same place, so the form just works.

## 4. Run with Docker Compose (recommended, matches production)

```bash
docker compose up --build -d
```

This starts both the app and Gotenberg together, networked internally.
Visit `http://localhost:8000` (or your server's IP/domain).

## 5. Deploy permanently (Oracle Cloud Free Tier VPS)

1. Spin up an Always Free Ampere A1 instance (Ubuntu), get its public IP
2. Install Docker + Docker Compose plugin on the VPS
3. Copy this whole folder to the VPS (`scp` or `git clone`), including your
   filled-in `.env` and `service-account.json` (upload these separately —
   don't put real secrets in git)
4. `docker compose up --build -d`
5. Point a domain at the VPS IP (A record), then put **Caddy** or **nginx +
   certbot** in front for automatic free HTTPS — e.g. a minimal Caddy
   reverse proxy config:
   ```
   yourdomain.com {
       reverse_proxy localhost:8000
   }
   ```
6. Update the DNS-facing URL — no code change needed, since `script.js`
   now uses a relative path and assumes it's served from the same origin
   as the API.

## Project layout

```
resume-automation/
├── app/
│   ├── main.py            # FastAPI app, webhook route, static mount
│   ├── validators.py      # field validation (port of n8n Code node)
│   ├── gemini_client.py   # prompt + Gemini call + HTML extraction
│   ├── pdf_client.py      # HTML -> PDF via Gotenberg
│   ├── sheets_client.py   # Google Sheets logging (service account)
│   ├── email_client.py    # Gmail send via SMTP app password
│   ├── telegram_client.py # admin notification
│   ├── pipeline.py        # orchestrates the background steps
│   └── config.py          # loads all env vars in one place
├── static/                # your existing frontend, served as-is
├── docker-compose.yml     # app + gotenberg containers
├── Dockerfile
├── requirements.txt
└── .env.example
```

## Notes on what changed vs. the n8n version

- **Gmail/Sheets auth**: swapped OAuth2 for a Gmail App Password + a Google
  service account. Both are headless-friendly (no browser consent screen
  to click through on a server) and functionally equivalent.
- **Retries**: same retry counts/delays as the original node settings
  (Sheets: 2 tries/2s, Gemini: 3 tries/3s, PDF: 2 tries/2s, Email: 2 tries/3s).
- **Failure behavior**: if Sheets logging or Gemini generation fails after
  retries, the pipeline stops (matches n8n's default "halt on node error").
  Email and Telegram run independently at the end, so one failing doesn't
  block the other — same as the two parallel branches in the original graph.
- **Telegram is optional**: if you leave the token/chat ID blank, that step
  is skipped with a warning log instead of failing the whole submission.
