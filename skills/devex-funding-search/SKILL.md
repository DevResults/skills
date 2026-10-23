---
name: devex-funding-search
description: Use when the user wants to search, export, or automate retrieval of funding opportunities from Devex (devex.com). Covers running the Playwright script, configuring filters (keywords, status, country, topic, donor), first-time login setup, scheduling, and email/CSV delivery.
user-invocable: true
---

# Devex Funding Search

Automate retrieval of funding opportunities from Devex using a Playwright script that runs inside your logged-in Chrome session.

## Overview

Devex exposes a clean REST API at `https://www.devex.com/api/funding_projects`. The script authenticates by reusing your existing Chrome profile (no credentials stored), makes paginated API calls, and delivers results as a CSV and/or HTML email.

## First-Time Setup

```bash
pip install playwright
playwright install chromium
```

Run once with `headless=False` to log in and save the session:

```bash
python devex-funding.py --login
```

This opens Chrome, navigates to devex.com, waits for you to log in manually, then saves the session to `./chrome-profile/`. All future runs reuse that profile headlessly.

## Running the Script

```bash
# Export to CSV (default)
python devex-funding.py

# With keyword filter
python devex-funding.py --keywords "monitoring evaluation" "MERL"

# Filter by country and topic
python devex-funding.py --places "Kenya" "Uganda" --topics "Global Health"

# Only open opportunities, last 7 days
python devex-funding.py --status open --since 7

# Email results
python devex-funding.py --email you@example.com --smtp-host smtp.gmail.com --smtp-user you@gmail.com

# Email + save CSV
python devex-funding.py --email you@example.com --output results.csv
```

## Key Filters

| Flag | Values | Notes |
|---|---|---|
| `--keywords` | any text | Multiple values → OR search |
| `--status` | `open`, `forecast`, `both` | Default: `both` |
| `--types` | `tender` `grant` `program` `contract` | Default: all |
| `--places` | country or region names | e.g. `Kenya`, `West Africa` |
| `--donors` | short codes or full names | e.g. `USAID`, `WBG` |
| `--topics` | topic labels | e.g. `Global Health`, `Infrastructure` |
| `--since` | integer (days) | Opportunities updated within N days |
| `--pages` | integer | Max pages to fetch (default 5, 100/page) |

## Output

Each row in the CSV contains:

| Field | Description |
|---|---|
| `id` | Devex opportunity ID |
| `type` | tender / grant / program / contract |
| `status` | open / forecast |
| `title` | Full title |
| `places` | Countries or regions |
| `donors` | Funding organizations (short names) |
| `deadline` | Closing date |
| `updated` | Last updated timestamp |
| `url` | Direct link: `https://www.devex.com/funding/r/<id>` |

## Scheduling (Windows Task Scheduler)

Run weekly on Monday at 8 AM:

```powershell
$action = New-ScheduledTaskAction -Execute "python" `
  -Argument "C:\path\to\devex-funding.py --keywords `"monitoring evaluation`" --email you@example.com" `
  -WorkingDirectory "C:\path\to\script"

$trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday -At 8am

Register-ScheduledTask -TaskName "DevexFundingSearch" -Action $action -Trigger $trigger -RunLevel Highest
```

## Email Setup

Gmail requires an App Password (not your main password):
1. Go to myaccount.google.com → Security → 2-Step Verification → App passwords
2. Generate a password for "Mail"
3. Pass it via `--smtp-pass` or set env var `DEVEX_SMTP_PASS`

The email sends a plain HTML table of results with clickable titles linking directly to each opportunity.

## Notes

- The DataDome bot-protection cookie rotates with each response; the script handles this automatically when running via Playwright's browser context.
- The CSRF token is read from the page's meta tag each run.
- If the session expires, re-run `python devex-funding.py --login`.
- The API returns up to 100 results per page; default fetch is 5 pages (500 opportunities). Raise `--pages` for broader sweeps.
