"""Collect GitHub weekly trending repos and enrich with GitHub API data."""
import csv
import html
import json
import re
import time
import urllib.request
from datetime import datetime, timezone

RAW = open("trending.html", encoding="utf-8").read()
arts = re.split(r'<article class="Box-row">', RAW)[1:]

rows = []
for a in arts:
    m = re.search(r'<h2 class="h3 lh-condensed">.*?href="/([^"]+?)"', a, re.S)
    if not m:
        continue
    repo = m.group(1)
    d = re.search(r'<p class="col-9 color-fg-muted[^"]*">\s*(.*?)\s*</p>', a, re.S)
    desc = html.unescape(re.sub(r"<[^>]+>", "", d.group(1))).strip() if d else ""
    lang = re.search(r'itemprop="programmingLanguage">([^<]+)<', a)
    total = re.search(
        r'href="/%s/stargazers"[^>]*>\s*(?:<svg.*?</svg>)?\s*([\d,]+)' % re.escape(repo), a, re.S
    )
    week = re.search(r"([\d,]+)\s+stars this week", a)
    forks = re.search(
        r'href="/%s/forks"[^>]*>\s*(?:<svg.*?</svg>)?\s*([\d,]+)' % re.escape(repo), a, re.S
    )
    rows.append(
        {
            "repo": repo,
            "desc": desc,
            "lang": lang.group(1).strip() if lang else "",
            "week": int(week.group(1).replace(",", "")) if week else 0,
            "total": total.group(1) if total else "",
            "forks": forks.group(1) if forks else "",
        }
    )

rows.sort(key=lambda r: r["week"], reverse=True)


def api(path):
    req = urllib.request.Request(
        "https://api.github.com" + path,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "trending-report",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


downloads = {}
for r in rows:
    try:
        rels = api("/repos/%s/releases?per_page=100" % r["repo"])
        if isinstance(rels, list):
            downloads[r["repo"]] = sum(
                a.get("download_count", 0) for release in rels for a in release.get("assets", [])
            )
        else:
            downloads[r["repo"]] = 0
    except Exception as exc:  # noqa: BLE001 - keep going, mark as n/a
        print("releases failed", r["repo"], exc)
        downloads[r["repo"]] = ""
    time.sleep(0.3)

METRIC_LABELS = {
    "en": [
        "Rank",
        "Repository",
        "URL",
        "Description",
        "Language",
        "Stars gained this week",
        "Total stars",
        "Forks",
        "Release downloads (all releases)",
        "Watchers",
        "Open issues",
        "Created",
        "Last push",
        "License",
        "Homepage",
    ]
}

out = []
for i, r in enumerate(rows, 1):
    try:
        meta = api("/repos/" + r["repo"])
        time.sleep(0.3)
    except Exception as exc:  # noqa: BLE001
        print("repo failed", r["repo"], exc)
        meta = {}
    lic = (meta.get("license") or {}).get("spdx_id") or ""
    out.append(
        [
            i,
            r["repo"],
            "https://github.com/" + r["repo"],
            r["desc"],
            r["lang"],
            r["week"],
            meta.get("stargazers_count", r["total"]),
            meta.get("forks_count", r["forks"]),
            downloads.get(r["repo"], ""),
            meta.get("subscribers_count", ""),
            meta.get("open_issues_count", ""),
            (meta.get("created_at") or "")[:10],
            (meta.get("pushed_at") or "")[:10],
            lic,
            meta.get("homepage") or "",
        ]
    )

with open("github_trending_weekly.csv", "w", encoding="utf-8-sig", newline="") as f:
    w = csv.writer(f, quoting=csv.QUOTE_ALL)
    w.writerow(METRIC_LABELS["en"])
    w.writerows(out)

collected_at = datetime.now(timezone.utc).replace(microsecond=0)
with open("github_trending_weekly.meta.json", "w", encoding="utf-8") as f:
    json.dump(
        {
            "collected_at": collected_at.isoformat(),
            "source": "https://github.com/trending?since=weekly",
            "rows": len(out),
        },
        f,
        indent=2,
    )
print("collected", len(out), "rows on", collected_at.isoformat())
for row in out[:5]:
    print(row[0], row[1], row[5], row[6], row[8])
