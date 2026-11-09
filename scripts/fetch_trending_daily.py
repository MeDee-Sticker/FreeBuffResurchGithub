#!/usr/bin/env python3
"""Fetch GitHub Trending live and write one dated snapshot into data/.

This replaces the hand-download step: no trending.html is needed before a run.
Each snapshot is a JSON file with its metadata plus a CSV twin for spreadsheets.

    python scripts/fetch_trending_daily.py                 # today
    python scripts/fetch_trending_daily.py --since weekly   # this week
    python scripts/fetch_trending_daily.py --since monthly --out-dir /tmp/trend
"""
from __future__ import annotations

import argparse
import csv
import html
import json
import re
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

BASE_URL = "https://github.com/trending"
PERIOD_LABELS = {"daily": "today", "weekly": "this week", "monthly": "this month"}
USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)
SCHEMA = "github-trending-snapshot/1"
CACHE_DIR = Path("data/cache")
CSV_HEADER = [
    "Rank",
    "Repository",
    "URL",
    "Description",
    "Language",
    "Stars gained",
    "Total stars",
    "Forks",
]

ARTICLE_SPLIT = re.compile(r'<article class="Box-row">')
REPO_LINK = re.compile(r'<h2 class="h3 lh-condensed">.*?href="/([^"]+?)"', re.S)
DESCRIPTION = re.compile(r'<p class="col-9 color-fg-muted[^"]*">\s*(.*?)\s*</p>', re.S)
LANGUAGE = re.compile(r'itemprop="programmingLanguage">([^<]+)<')
STARS_GAINED = re.compile(r"([\d,]+)\s+stars\s+(today|this week|this month)")
TOTAL_STARS = re.compile(
    r'href="/(?P<repo>[^"]+?)/stargazers"[^>]*>\s*(?:<svg.*?</svg>)?\s*([\d,]+)', re.S
)
FORKS = re.compile(
    r'href="/(?P<repo>[^"]+?)/forks"[^>]*>\s*(?:<svg.*?</svg>)?\s*([\d,]+)', re.S
)


def url_for(since: str) -> str:
    return BASE_URL if since == "daily" else f"{BASE_URL}?since={since}"


def fetch(url: str, attempts: int = 3, timeout: int = 30) -> str:
    """Download a trending page, retrying transient failures."""
    last_error: Exception | None = None
    for attempt in range(1, attempts + 1):
        request = urllib.request.Request(
            url,
            headers={"User-Agent": USER_AGENT, "Accept": "text/html"},
        )
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                charset = response.headers.get_content_charset() or "utf-8"
                return response.read().decode(charset, "replace")
        except (urllib.error.URLError, TimeoutError, OSError) as exc:  # noqa: PERF203
            last_error = exc
            if attempt < attempts:
                print(f"fetch attempt {attempt} failed ({exc}); retrying", file=sys.stderr)
                time.sleep(2 * attempt)
    raise SystemExit(f"could not fetch {url}: {last_error}")


def as_int(value: str | None) -> int | None:
    return int(value.replace(",", "")) if value else None


def parse(raw: str, period_label: str) -> list[dict]:
    rows: list[dict] = []
    for article in ARTICLE_SPLIT.split(raw)[1:]:
        repo_match = REPO_LINK.search(article)
        if not repo_match:
            continue
        repo = repo_match.group(1)
        description = DESCRIPTION.search(article)
        language = LANGUAGE.search(article)
        gained = STARS_GAINED.search(article)
        totals = TOTAL_STARS.search(article)
        forks = FORKS.search(article)
        rows.append(
            {
                "repo": repo,
                "url": f"https://github.com/{repo}",
                "description": (
                    html.unescape(re.sub(r"<[^>]+>", "", description.group(1))).strip()
                    if description
                    else ""
                ),
                "language": language.group(1).strip() if language else "",
                "stars_gained": as_int(gained.group(1)) if gained else 0,
                "total_stars": as_int(totals.group(2)) if totals else None,
                "forks": as_int(forks.group(2)) if forks else None,
                "_period_label": period_label,
            }
        )

    rows.sort(key=lambda row: row["stars_gained"], reverse=True)
    for rank, row in enumerate(rows, 1):
        row["rank"] = rank
        row.pop("_period_label", None)
    return rows


def write_snapshot(rows: list[dict], meta: dict, out_dir: Path) -> tuple[Path, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = f"trending_{meta['collected_on']}_{meta['since']}"
    json_path = out_dir / f"{stem}.json"
    csv_path = out_dir / f"{stem}.csv"

    json_path.write_text(
        json.dumps({**meta, "repos": rows}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    with csv_path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.writer(handle, quoting=csv.QUOTE_ALL)
        writer.writerow(CSV_HEADER)
        for row in rows:
            writer.writerow(
                [
                    row["rank"],
                    row["repo"],
                    row["url"],
                    row["description"],
                    row["language"],
                    row["stars_gained"],
                    row["total_stars"] if row["total_stars"] is not None else "",
                    row["forks"] if row["forks"] is not None else "",
                ]
            )
    return json_path, csv_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--since",
        choices=sorted(PERIOD_LABELS),
        default="daily",
        help="trending window (default: daily)",
    )
    parser.add_argument("--out-dir", default="data", help="snapshot directory (default: data)")
    parser.add_argument(
        "--keep-html",
        action="store_true",
        help="also cache the fetched page under data/cache for debugging",
    )
    args = parser.parse_args(argv)

    url = url_for(args.since)
    period_label = PERIOD_LABELS[args.since]
    raw = fetch(url)
    rows = parse(raw, period_label)
    if not rows:
        raise SystemExit(
            f"no repositories parsed from {url} — GitHub may have changed its markup"
        )

    collected_at = datetime.now(timezone.utc).replace(microsecond=0)
    meta = {
        "schema": SCHEMA,
        "collected_at": collected_at.isoformat(),
        "collected_on": collected_at.date().isoformat(),
        "source": url,
        "since": args.since,
        "period_label": period_label,
        "rows": len(rows),
    }
    json_path, csv_path = write_snapshot(rows, meta, Path(args.out_dir))

    if args.keep_html:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        (CACHE_DIR / f"trending_{meta['collected_on']}_{args.since}.html").write_text(
            raw, encoding="utf-8"
        )

    print(f"{len(rows)} repos, {args.since} — {json_path} / {csv_path.name}")
    for row in rows[:5]:
        total = f"{row['total_stars']:,}*" if row["total_stars"] is not None else "n/a"
        print(f"{row['rank']:2} {row['repo']:45} +{row['stars_gained']:,} {period_label:10} {total}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
