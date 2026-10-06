# Ines Kesselring Hub

The official website and backoffice for the **Ines Kesselring** YouTube channel:
videos grouped into series, a live-stream schedule with a countdown, news posts,
and free member accounts — all managed from a Django backoffice.

**Stack:** Next.js 16 (TypeScript) · Django 5.2 LTS + Django REST Framework · PostgreSQL 16 · Docker · GitHub Actions

---

## What it does

**For fans (website)**
- Home page with an on-air countdown to the next live, which switches to a "live now" state while streaming
- Videos by series, synced from YouTube
- Live schedule in Thai time, with members-only streams
- News, with members-only articles (guests see a teaser)
- Free registration and login

**For the team (backoffice at `/admin/`)**
- Manage series, videos, live schedule and news with thumbnails, filters, search, bulk publish/unpublish
- "Sync selected series from YouTube" action
- Image upload for news covers

**Roles**

| Role   | Website | Backoffice | Manage content | Manage users |
|--------|:------:|:----------:|:--------------:|:------------:|
| Member | ✓ | – | – | – |
| Staff  | ✓ | ✓ | ✓ | – |
| Admin  | ✓ | ✓ | ✓ | ✓ |

Everyone signs in with **email + password**. Staff and admins see a "Backoffice" button on their account page.
Public registration can only ever create members.

## Architecture

```
Browser ──► Next.js (port 3000) ──server-side──► Django REST API (port 8000) ──► PostgreSQL
                │                                       │
                │  login token kept in an               └── /admin/  Django backoffice
                │  httpOnly cookie (never readable           (staff & admin)
                │  by browser JavaScript)
```

- The browser only talks to Next.js. Next.js calls Django **server-side**, so the API token never reaches client JavaScript.
- Login/register/logout are Next.js Server Actions that set or clear the httpOnly cookie.
- Each page section degrades gracefully: if the API is down, the section shows an empty state instead of crashing the page.
- `GET /api/health/` checks the database — used by Docker healthchecks and uptime monitors.

## Project layout

```
backend/            Django project
  accounts/         Email-login user model, roles, auth API
  content/          Series, Video, LiveStream, Article; admin; API; YouTube sync
  config/           Settings (all from environment variables), URLs
frontend/           Next.js app (App Router)
  app/              Pages and server actions
  components/       UI components
  lib/              API client, auth helpers, formatting
docker-compose.yml  PostgreSQL + backend + frontend
.github/workflows/  CI: backend tests on PostgreSQL, frontend type-check/lint/build
```

---

## Run locally (Windows / macOS / Linux)

Requirements: **Python 3.12+** and **Node.js 22+**.

### 1. Backend

```powershell
cd backend
python -m venv .venv
.venv\Scripts\activate          # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
copy .env.example .env          # macOS/Linux: cp .env.example .env
```

If PowerShell refuses to run `activate`, run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` once.

Edit `backend/.env`: set `DJANGO_SECRET_KEY` (any long random string) and `DEMO_PASSWORD` (for demo accounts). Then:

```powershell
python manage.py migrate
python manage.py createsuperuser          # your admin account (email + password)
python manage.py seed_demo --with-users   # optional: sample content + staff@example.com / member@example.com
python manage.py runserver
```

Backoffice: http://localhost:8000/admin/

### 2. Frontend (second terminal)

```powershell
cd frontend
npm install
copy .env.example .env.local    # macOS/Linux: cp .env.example .env.local
npm run dev
```

Website: http://localhost:3000

### Pull real videos from YouTube

```powershell
python manage.py sync_youtube --rss   # no API key: latest ~15 uploads
python manage.py sync_youtube         # with YOUTUBE_API_KEY: all playlists → series
python manage.py seed_demo --clear    # remove the sample content
```

Re-running sync updates titles and thumbnails but **keeps any publish/unpublish choices** made in the backoffice.

### Give someone staff access

Backoffice → **Users** → choose the user → tick **Staff status** and add the **Content Staff** group.
(The group and its permissions are created automatically on `migrate`.)

---

## Run with Docker

```bash
cp .env.example .env    # set DJANGO_SECRET_KEY and POSTGRES_PASSWORD
docker compose up --build
docker compose exec backend python manage.py createsuperuser
```

Website http://localhost:3000 · Backoffice http://localhost:8000/admin/

---

## Tests

```bash
cd backend && python manage.py test     # 31 tests: auth, roles & backoffice access, API, YouTube sync, seed
cd frontend && npx tsc --noEmit && npm run lint && npm run build
```

CI runs both on every push (backend against a real PostgreSQL service).

## Security notes

- Tokens live in an `httpOnly`, `SameSite=Lax` cookie; `Secure` in production.
- Login and registration are rate-limited (`AUTH_THROTTLE_RATE`, default 20/min).
- Password strength uses Django's validators; errors are shown in Thai.
- Login redirects only allow same-site paths (no open redirects).
- Settings refuse to start without `DJANGO_SECRET_KEY` when `DEBUG` is off.
- Behind HTTPS, set `DJANGO_HTTPS=1` to enable SSL redirect, secure cookies and HSTS.
- Never commit `.env` files — they are git-ignored; use the `.env.example` templates.

## Roadmap

- LINE notification when a live is about to start
- AI-generated Thai summaries of new videos
- Backoffice theme matching the website
- Deployment to Hetzner Cloud with Caddy (HTTPS) and automatic deploy from CI
