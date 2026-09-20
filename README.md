# RadarScan — Automated Web Vulnerability Scanner Dashboard

Graduation project: a platform that runs a pipeline of 5 Python
security-scanning scripts against a target website, and streams the
results live to a web dashboard.

![status](https://img.shields.io/badge/status-work--in--progress-orange)
![python](https://img.shields.io/badge/python-3.12-blue)
![flask](https://img.shields.io/badge/flask-3.x-black)

## What it does

1. Browse the public site: **Home**, **Features** (the scan catalog), **Pricing** (plans + monthly/annual billing), and **About**.
2. Create an account (email/password or Google) — optionally starting on a paid plan picked from the Pricing page.
3. On the dashboard, enter a target URL. `main.py` runs 5 scanner scripts against it, one after the other: **Security Headers**, **SQL Injection**, **XSS**, **IDOR**, **API Security**.
4. Every log line each scanner produces streams live into the dashboard terminal as it happens, and your daily scan usage (tied to your plan's limit) is shown at the top.
5. Findings are saved per scan — click any row in "Recent scans" to open a full **scan detail page** with every finding and the original log, even after a server restart.
6. From your **Account** page, switch plans any time (demo billing — no real payment processor is wired up yet).

A small intentionally-vulnerable Flask app (`vulnerable_target/`) is
included so you can test the scanners safely, without touching a real
website.

## Pages

| Route | What's there |
|---|---|
| `/` | Landing page |
| `/features` | Scan catalog — what each of the 5 modules does, plus "how it works" |
| `/pricing` | Plan cards (Free / Student / Pro / Team), monthly ↔ annual toggle |
| `/about` | Project description + responsible-use notice |
| `/register`, `/login` | Auth (email/password + Google OAuth) |
| `/dashboard` | Start a scan, watch live logs, see recent scans |
| `/dashboard/scans/<scan_uid>` | Full detail view of one past scan |
| `/account` | Profile info, usage stats, plan switcher |

## Plans (demo billing)

Plan data lives in `plans.py` — a single source of truth used by both
the pricing page and the account page. Selecting a plan (at signup, from
Pricing, or from Account) just updates the user's `plan` /
`billing_cycle` columns instantly; there's no real payment processor
connected yet, and the UI says so wherever a plan is chosen. Each plan
carries a daily scan limit (`User.scan_limit_per_day`), enforced when a
scan is started.

## Project structure

```
vuln_scanner_project/
├── app.py                   # Dashboard entry point (Flask app factory)
├── main.py                  # Orchestrator: runs every scanner in order
├── scan_manager.py          # In-memory scan state (logs/status/findings), polled live
├── auth.py                  # Register / login / Google OAuth
├── account.py                # Profile page + plan switching
├── dashboard.py                # Dashboard page, scan history, scan start/poll API
├── main_routes.py              # Landing / Features / Pricing / About
├── plans.py                     # Pricing catalog (single source of truth)
├── models.py                     # DB models (User, Scan)
├── extensions.py                 # db / login_manager / oauth instances
├── config.py                      # App config (reads from .env)
├── scanners/
│   ├── security_headers.py
│   ├── sql_injection.py
│   ├── xss_scanner.py
│   ├── idor_scanner.py
│   └── api_scanner.py
├── vulnerable_target/
│   └── app.py                 # Test site with 5 intentional vulnerabilities
├── templates/                  # Jinja2 HTML pages
├── static/                     # CSS and JS
├── reports/                     # JSON reports from CLI runs (git-ignored)
└── requirements.txt
```

## Getting started

### 1. Clone and enter the project

```bash
git clone https://github.com/YousefElSayed19/Graduation-Project.git
cd vuln_scanner_project
```

### 2. Create a virtual environment (recommended)

```bash
python -m venv venv

# macOS / Linux
source venv/bin/activate

# Windows (cmd)
venv\Scripts\activate.bat

# Windows (PowerShell)
venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```bash
python -m pip install -r requirements.txt
```

> Using `python -m pip` (instead of a bare `pip`) makes sure the
> packages install into the same Python interpreter you'll run the app
> with — this matters a lot on Windows if you have multiple Python
> installs.

### 4. Set up environment variables

```bash
# macOS / Linux
cp .env.example .env

# Windows (cmd)
copy .env.example .env
```

Open `.env` and set `SECRET_KEY` to any random string. Google OAuth
variables are optional — see the [Google OAuth setup](#google-oauth-setup-optional)
section below.

### 5. Run the vulnerable test target (in its own terminal)

```bash
python vulnerable_target/app.py
```

Runs on **http://127.0.0.1:5001**

### 6. Run the dashboard (in a second terminal)

```bash
python app.py
```

Runs on **http://127.0.0.1:5000**

### 7. Use it

1. Open `http://127.0.0.1:5000`
2. Create an account (Register)
3. In the dashboard, enter a target URL, e.g. `http://127.0.0.1:5001/search`
4. Click **Start scan** and watch the live log
5. Check the **Findings** panel once the scan finishes

## Running the scanners without the dashboard

```bash
python main.py http://127.0.0.1:5001/search
```

Saves a JSON report to `reports/`.

## Google OAuth setup (optional)

1. Go to [Google Cloud Console](https://console.cloud.google.com/apis/credentials)
2. Create an OAuth Client ID of type "Web application"
3. Under **Authorized redirect URIs**, add:
   `http://127.0.0.1:5000/login/google/callback`
4. Copy the Client ID and Client Secret into your `.env` file

## Current scan-target limitation

Each scanner currently checks only the single page you give it — it
does **not** crawl links on that page. So scanning the homepage
(`http://127.0.0.1:5001`) will only catch the IDOR and API findings,
since the SQLi and XSS forms live on `/search` and `/comment`. To scan
those, point the target directly at those pages, e.g.
`http://127.0.0.1:5001/search`.

## Ideas for the team to build on

- [ ] Add a basic crawler so a scan can follow links from the target
      page instead of checking one page only
- [ ] Reduce false positives / improve payload coverage in each scanner
- [ ] Add a 6th scanner (e.g. CSRF, open redirect, directory listing)
- [ ] Export a PDF/Excel report from scan results
- [ ] Wire up a real payment processor (Stripe/Paddle) behind `account.py`'s
      plan switcher — the UI and daily-limit logic are already in place
- [ ] Verify student status (e.g. `.edu` email check) before granting
      the Student plan
- [ ] Swap `scan_manager.py`'s in-memory store for Redis if you need to
      support many concurrent scans

## ⚠️ Important

This tool is for use **only on sites you own or are explicitly
authorized to test**. Scanning a website without permission may be
illegal depending on your local laws.
