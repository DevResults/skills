#!/usr/bin/env python3
"""
Devex Funding Search
Fetches open/forecast opportunities from devex.com using your saved Chrome session.

Usage:
  python devex-funding.py --login                         # first-time login
  python devex-funding.py                                 # fetch all open+forecast
  python devex-funding.py --keywords "monitoring evaluation" "MERL"
  python devex-funding.py --places Kenya Uganda --since 30
  python devex-funding.py --email you@example.com --smtp-host smtp.gmail.com \
      --smtp-user you@gmail.com --smtp-pass <app-password>

See SKILL.md for full documentation.
"""

import argparse
import asyncio
import csv
import html
import os
import smtplib
import sys
from datetime import datetime, timezone, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

try:
    from playwright.async_api import async_playwright
except ImportError:
    sys.exit("playwright not installed. Run: pip install playwright && playwright install chromium")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args():
    p = argparse.ArgumentParser(description="Fetch Devex funding opportunities")
    p.add_argument("--login", action="store_true",
                   help="Open browser for first-time login and save session")
    p.add_argument("--profile", default=str(Path(__file__).parent / "chrome-profile"),
                   help="Path to Chrome profile directory (default: ./chrome-profile)")
    p.add_argument("--keywords", nargs="+", default=[],
                   help="Keyword search terms (OR logic)")
    p.add_argument("--status", choices=["open", "forecast", "both"], default="both",
                   help="Opportunity status filter (default: both)")
    p.add_argument("--types", nargs="+", default=[],
                   choices=["tender", "grant", "program", "contract"],
                   help="Opportunity types to include (default: all)")
    p.add_argument("--places", nargs="+", default=[],
                   help="Country or region names to filter by")
    p.add_argument("--donors", nargs="+", default=[],
                   help="Donor short codes or names to filter by")
    p.add_argument("--topics", nargs="+", default=[],
                   help="Topic labels (e.g. 'Global Health', 'Infrastructure')")
    p.add_argument("--since", type=int, default=None,
                   help="Only include opportunities updated in the last N days")
    p.add_argument("--pages", type=int, default=5,
                   help="Maximum pages to fetch, 100 results/page (default: 5)")
    p.add_argument("--output", default="devex-opportunities.csv",
                   help="CSV output file path (default: devex-opportunities.csv)")
    p.add_argument("--no-csv", action="store_true",
                   help="Skip saving CSV output")
    p.add_argument("--email", default=None,
                   help="Send results to this email address")
    p.add_argument("--smtp-host", default="smtp.gmail.com")
    p.add_argument("--smtp-port", type=int, default=587)
    p.add_argument("--smtp-user", default=None)
    p.add_argument("--smtp-pass", default=None,
                   help="SMTP password (or set DEVEX_SMTP_PASS env var)")
    p.add_argument("--from-email", default=None,
                   help="Sender address (defaults to --smtp-user)")
    return p.parse_args()


# ---------------------------------------------------------------------------
# Playwright helpers
# ---------------------------------------------------------------------------

async def login_and_save(profile_dir: str):
    """Open visible Chrome so user can log in; waits for them to finish."""
    async with async_playwright() as pw:
        ctx = await pw.chromium.launch_persistent_context(
            user_data_dir=profile_dir,
            headless=False,
            args=["--start-maximized"],
        )
        page = await ctx.new_page()
        await page.goto("https://www.devex.com/login")
        print("Log in to Devex in the browser window, then press Enter here...")
        input()
        await ctx.close()
    print(f"Session saved to: {profile_dir}")


async def fetch_opportunities(args) -> list[dict]:
    """Use the saved Chrome session to call the Devex API."""
    statuses = (
        ["open", "forecast"] if args.status == "both"
        else [args.status]
    )
    since_iso = None
    if args.since:
        since_iso = (datetime.now(timezone.utc) - timedelta(days=args.since)).isoformat()

    results = []

    async with async_playwright() as pw:
        ctx = await pw.chromium.launch_persistent_context(
            user_data_dir=args.profile,
            headless=True,
        )
        page = await ctx.new_page()
        await page.goto("https://www.devex.com/funding/r")
        # Wait for the page to settle so cookies and CSRF token are set
        await page.wait_for_load_state("networkidle")

        for page_num in range(1, args.pages + 1):
            params: dict[str, list | str] = {}

            for kw in args.keywords:
                params.setdefault("query[]", []).append(kw)
            for s in statuses:
                params.setdefault("filter[statuses][]", []).append(s)
            for t in args.types:
                params.setdefault("filter[types][]", []).append(t)
            for pl in args.places:
                params.setdefault("filter[places][]", []).append(pl)
            for d in args.donors:
                params.setdefault("filter[donors][]", []).append(d)
            for tp in args.topics:
                params.setdefault("filter[news_topics][]", []).append(tp)

            if since_iso:
                params["filter[updated_since]"] = since_iso

            params["page[number]"] = str(page_num)
            params["page[size]"] = "100"
            params["sorting[field]"] = "_score" if args.keywords else "updated_at"
            params["sorting[order]"] = "desc"

            data = await page.evaluate(
                """async (params) => {
                    const p = new URLSearchParams();
                    for (const [k, v] of Object.entries(params)) {
                        for (const val of [].concat(v)) {
                            p.append(k, val);
                        }
                    }
                    const csrf = document.querySelector('meta[name="csrf-token"]')?.content ?? '';
                    const resp = await fetch('/api/funding_projects?' + p.toString(), {
                        credentials: 'include',
                        headers: {
                            'x-requested-with': 'XMLHttpRequest',
                            'x-csrf-token': csrf,
                        },
                    });
                    if (!resp.ok) throw new Error('API error ' + resp.status);
                    return resp.json();
                }""",
                params,
            )

            batch = data.get("data", [])
            results.extend(batch)
            total = data.get("total", 0)
            total_pages = data.get("page", {}).get("pages", 1)
            print(f"  Page {page_num}/{min(args.pages, total_pages)} — {len(results)}/{total} fetched", flush=True)

            if page_num >= total_pages:
                break

        await ctx.close()

    return results


# ---------------------------------------------------------------------------
# Output helpers
# ---------------------------------------------------------------------------

DEVEX_URL = "https://www.devex.com/funding/r/{id}"

def flatten(opps: list[dict]) -> list[dict]:
    rows = []
    for o in opps:
        rows.append({
            "id": o["id"],
            "type": o.get("type", ""),
            "status": o.get("status", ""),
            "title": o.get("title", ""),
            "places": "; ".join(p["name"] for p in o.get("places", [])),
            "donors": "; ".join(d["short_name"] for d in o.get("donors", [])),
            "deadline": o.get("deadline") or "",
            "updated": o.get("updated_at", "")[:10],
            "url": DEVEX_URL.format(id=o["id"]),
        })
    return rows


def save_csv(rows: list[dict], path: str):
    if not rows:
        print("No results to save.")
        return
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"Saved {len(rows)} opportunities → {path}")


def build_html_email(rows: list[dict], filters_summary: str) -> str:
    if not rows:
        body = "<p>No opportunities matched your filters.</p>"
    else:
        table_rows = "\n".join(
            f"""<tr>
              <td><a href="{html.escape(r['url'])}">{html.escape(r['title'])}</a></td>
              <td>{html.escape(r['type'])}</td>
              <td>{html.escape(r['status'])}</td>
              <td>{html.escape(r['places'])}</td>
              <td>{html.escape(r['donors'])}</td>
              <td>{html.escape(r['deadline'])}</td>
            </tr>"""
            for r in rows
        )
        body = f"""
        <table border="1" cellpadding="6" cellspacing="0" style="border-collapse:collapse;font-family:sans-serif;font-size:13px">
          <thead style="background:#f0f0f0">
            <tr>
              <th>Title</th><th>Type</th><th>Status</th>
              <th>Location</th><th>Donors</th><th>Deadline</th>
            </tr>
          </thead>
          <tbody>{table_rows}</tbody>
        </table>"""

    date_str = datetime.now().strftime("%B %d, %Y")
    return f"""<html><body>
    <h2>Devex Funding Opportunities — {date_str}</h2>
    <p><strong>Filters:</strong> {html.escape(filters_summary)}</p>
    <p><strong>{len(rows)} opportunities</strong> matched.</p>
    {body}
    <hr><p style="color:#888;font-size:11px">
      Generated by devex-funding.py &nbsp;|&nbsp;
      <a href="https://www.devex.com/funding/r">View on Devex</a>
    </p>
    </body></html>"""


def send_email(args, rows: list[dict], filters_summary: str):
    smtp_pass = args.smtp_pass or os.environ.get("DEVEX_SMTP_PASS")
    if not smtp_pass:
        sys.exit("--smtp-pass or DEVEX_SMTP_PASS env var required for email delivery")

    from_addr = args.from_email or args.smtp_user or args.email
    to_addr = args.email
    date_str = datetime.now().strftime("%Y-%m-%d")

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"Devex Funding Opportunities — {date_str} ({len(rows)} results)"
    msg["From"] = from_addr
    msg["To"] = to_addr

    html_body = build_html_email(rows, filters_summary)
    msg.attach(MIMEText(html_body, "html"))

    with smtplib.SMTP(args.smtp_host, args.smtp_port) as server:
        server.starttls()
        server.login(args.smtp_user, smtp_pass)
        server.sendmail(from_addr, [to_addr], msg.as_string())

    print(f"Email sent to {to_addr}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

async def main():
    args = parse_args()

    if args.login:
        await login_and_save(args.profile)
        return

    if not Path(args.profile).exists():
        sys.exit(
            f"Chrome profile not found at: {args.profile}\n"
            "Run first with --login to set up your session."
        )

    filters_parts = []
    if args.keywords:
        filters_parts.append("keywords: " + ", ".join(args.keywords))
    if args.status != "both":
        filters_parts.append(f"status: {args.status}")
    if args.places:
        filters_parts.append("places: " + ", ".join(args.places))
    if args.donors:
        filters_parts.append("donors: " + ", ".join(args.donors))
    if args.topics:
        filters_parts.append("topics: " + ", ".join(args.topics))
    if args.since:
        filters_parts.append(f"updated in last {args.since} days")
    filters_summary = "; ".join(filters_parts) if filters_parts else "all open + forecast"

    print(f"Fetching Devex opportunities ({filters_summary}) ...")
    opps = await fetch_opportunities(args)
    rows = flatten(opps)

    if not args.no_csv:
        save_csv(rows, args.output)

    if args.email:
        send_email(args, rows, filters_summary)

    if not rows:
        print("No matching opportunities found.")


if __name__ == "__main__":
    asyncio.run(main())
