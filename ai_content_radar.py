"""Collect AI-education content and score how much attention each piece got.

Sources (no API keys needed):
  * YouTube search results (relevance + most-viewed) and watch pages for exact stats
  * Hacker News via the Algolia search API
  * Reddit top posts via the per-subreddit Atom feed (best effort, often blocked)
  * Google Trends daily RSS, filtered down to AI keywords
  * Google + YouTube autocomplete = search demand for the Thai audience

Every network call is cached under data/cache/ with retries and per-host pacing, so a
partial failure degrades to "this source is unavailable" instead of losing the run.

Usage:
    python ai_content_radar.py                       # everything, default queries
    python ai_content_radar.py --platforms youtube,hn
    python ai_content_radar.py --queries "th:สอนใช้ AI,en:ai for beginners"
    python ai_content_radar.py --offline             # reuse cache, no network

Outputs:
    data/ai_content_<YYYY-MM-DD>.json   full payload (items, sources, demand, trends)
    data/ai_content_<YYYY-MM-DD>.csv    flat table, one row per item
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import html as html_mod
import json
import math
import os
import re
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from statistics import median

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(ROOT, "data")
CACHE_DIR = os.path.join(DATA_DIR, "cache")

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0 Safari/537.36"
)
# Seconds between requests to the same host. Reddit throttles hard, YouTube is tolerant.
HOST_DELAY = {
    "www.youtube.com": 1.5,
    "youtube.com": 1.5,
    "suggestqueries.google.com": 0.7,
    "hn.algolia.com": 0.5,
    "www.reddit.com": 4.0,
    "trends.google.com": 1.0,
}

_CACHE: dict[str, str] = {}
_LAST_HIT: dict[str, float] = {}
STALE_URLS: set[str] = set()

# --------------------------------------------------------------------------- #
# HTTP with cache, pacing and retries
# --------------------------------------------------------------------------- #


def _cache_path(url: str) -> str:
    key = hashlib.sha1(url.encode("utf-8")).hexdigest()[:24]
    return os.path.join(CACHE_DIR, key + ".txt")


def http_get(
    url: str,
    *,
    ttl: int = 1800,
    offline: bool = False,
    retries: int = 3,
    timeout: int = 45,
) -> str:
    """Return the body of `url`, preferring a fresh cache entry over the network."""
    if url in _CACHE:
        return _CACHE[url]

    path = _cache_path(url)
    if os.path.exists(path):
        age = time.time() - os.path.getmtime(path)
        if offline or age < ttl:
            with open(path, encoding="utf-8", errors="replace") as fh:
                body = fh.read()
            if body.strip():
                _CACHE[url] = body
                return body
    if offline:
        raise RuntimeError("no cached copy (offline mode)")

    host = urllib.parse.urlparse(url).netloc
    last_error: Exception | None = None
    for attempt in range(retries):
        wait = HOST_DELAY.get(host, 1.0) - (time.time() - _LAST_HIT.get(host, 0.0))
        if wait > 0:
            time.sleep(wait)
        try:
            request = urllib.request.Request(
                url,
                headers={
                    "User-Agent": UA,
                    "Accept-Language": "en-US,en;q=0.9",
                    "Accept": (
                        "text/html,application/xhtml+xml,application/json;q=0.9,*/*;q=0.8"
                    ),
                },
            )
            with urllib.request.urlopen(request, timeout=timeout) as response:
                body = response.read().decode("utf-8", "replace")
            _LAST_HIT[host] = time.time()
            if not body.strip():
                raise RuntimeError("empty body")
            os.makedirs(CACHE_DIR, exist_ok=True)
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(body)
            _CACHE[url] = body
            return body
        except Exception as exc:  # noqa: BLE001 - retried below, reported by caller
            last_error = exc
            _LAST_HIT[host] = time.time()
            if attempt < retries - 1:
                time.sleep(min(12.0, 1.5 ** (attempt + 1)))

    # Network is down but we may still have a stale copy worth using.
    if os.path.exists(path):
        with open(path, encoding="utf-8", errors="replace") as fh:
            body = fh.read()
        if body.strip():
            STALE_URLS.add(url)
            _CACHE[url] = body
            return body
    raise RuntimeError("%s" % (last_error,))


# --------------------------------------------------------------------------- #
# Small JSON / HTML helpers
# --------------------------------------------------------------------------- #


def json_object_at(text: str, start: int) -> tuple[dict | None, int]:
    """Parse the first balanced {...} object at or after `start`."""
    begin = text.find("{", start)
    if begin < 0:
        return None, -1
    depth = 0
    in_string = False
    escaped = False
    for index in range(begin, len(text)):
        char = text[index]
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            continue
        if char == '"':
            in_string = True
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                try:
                    return json.loads(text[begin : index + 1]), index + 1
                except json.JSONDecodeError:
                    return None, -1
    return None, -1


def yt_initial_data(page: str) -> dict | None:
    """Return the page's ytInitialData object, or None when the page is not a result page."""
    for marker in ("ytInitialData", "ytInitialData ="):
        position = page.find(marker)
        if position >= 0:
            data, _ = json_object_at(page, position)
            if data:
                return data
    return None


def walk_collect(node, key: str, out: list) -> None:
    if isinstance(node, dict):
        value = node.get(key)
        if isinstance(value, dict):
            out.append(value)
        for child in node.values():
            walk_collect(child, key, out)
    elif isinstance(node, list):
        for child in node:
            walk_collect(child, key, out)


def runs_text(node) -> str:
    """Read both {"simpleText": ...} and {"runs": [{"text": ...}]} shapes."""
    if not isinstance(node, dict):
        return ""
    if isinstance(node.get("simpleText"), str):
        return node["simpleText"]
    runs = node.get("runs")
    if isinstance(runs, list):
        return "".join(str(run.get("text", "")) for run in runs if isinstance(run, dict))
    return ""


def xml_text(blob: str, tag: str) -> str:
    match = re.search(r"<%s[^>]*>(.*?)</%s>" % (re.escape(tag), re.escape(tag)), blob, re.S)
    if not match:
        return ""
    value = match.group(1).strip()
    cdata = re.match(r"^<!\[CDATA\[(.*?)\]\]>$", value, re.S)
    if cdata:
        value = cdata.group(1)
    value = re.sub(r"<[^>]+>", "", value)
    return html_mod.unescape(value).strip()


def lang_of(text: str) -> str:
    return "th" if re.search(r"[\u0e00-\u0e7f]", text or "") else "en"


# Matched against titles: search results drift, so a phone review or a tablet ad can
# rank for "ใช้ AI". Without this gate the ranking fills up with off-topic videos.
AI_RE = re.compile(
    r"(?:\b(?:a\.?i|gpt\d*|chatgpt\d*|gemini|claude|copilot|llm|openai|midjourney|sora|grok"
    r"|deepseek|perplexity|anthropic|nvidia|meta ai)\b)|เอไอ",
    re.I,
)


def looks_like_ai(text: str) -> bool:
    return bool(AI_RE.search(text or ""))


# --------------------------------------------------------------------------- #
# Field parsers (locale aware: YouTube serves numbers in the UI language)
# --------------------------------------------------------------------------- #

_THAI_UNITS = {"พัน": 1e3, "หมื่น": 1e4, "แสน": 1e5, "ล้าน": 1e6}
_AGE_EN = {
    "second": 1 / 86400,
    "minute": 1 / 1440,
    "hour": 1 / 24,
    "day": 1,
    "week": 7,
    "month": 30.44,
    "year": 365.25,
}
_AGE_EN_SHORT = {"s": 1 / 86400, "m": 1 / 1440, "h": 1 / 24, "d": 1, "w": 7, "mo": 30.44, "y": 365.25}
_AGE_TH = {
    "วินาที": 1 / 86400,
    "นาที": 1 / 1440,
    "ชั่วโมง": 1 / 24,
    "วัน": 1,
    "สัปดาห์": 7,
    "เดือน": 30.44,
    "ปี": 365.25,
}


def parse_views(text: str, default: int = 0) -> int:
    """387,752 views / 1.2M views / การดู 387,752 ครั้ง / 5.3 แสนครั้ง -> int."""
    if not text:
        return default
    raw = text.strip()
    lowered = raw.lower().replace(",", "").replace("\u00a0", " ")
    if "no views" in lowered:
        return 0
    match = re.search(r"(\d+(?:\.\d+)?)\s*([mkb])(?![a-z])", lowered)
    if match:
        scale = {"m": 1e6, "k": 1e3, "b": 1e9}[match.group(2)]
        return int(float(match.group(1)) * scale)
    match = re.search(r"(\d+(?:\.\d+)?)\s*(พัน|หมื่น|แสน|ล้าน)", raw)
    if match:
        return int(float(match.group(1)) * _THAI_UNITS[match.group(2)])
    match = re.search(r"\d+", lowered)
    return int(match.group(0)) if match else default


def parse_age_days(text: str) -> float | None:
    """'2 weeks ago' / '1y ago' / '2 สัปดาห์ที่แล้ว' -> days since publication."""
    if not text:
        return None
    raw = text.strip()
    lowered = raw.lower()
    if "สักครู่" in raw or "just now" in lowered or "moment ago" in lowered:
        return 0.0
    match = re.search(r"(\d+)\s*(mo|[smhdwy])\s*ago", lowered)
    if match:
        return int(match.group(1)) * _AGE_EN_SHORT[match.group(2)]
    match = re.search(r"(\d+)\s*(second|minute|hour|day|week|month|year)s?\s+ago", lowered)
    if match:
        return int(match.group(1)) * _AGE_EN[match.group(2)]
    match = re.search(r"(\d+)\s*(วินาที|นาที|ชั่วโมง|วัน|สัปดาห์|เดือน|ปี)\s*ที่แล้ว", raw)
    if match:
        return int(match.group(1)) * _AGE_TH[match.group(2)]
    return None


def parse_duration(text: str) -> int | None:
    """'14:31' or '1:02:03' -> seconds. None for LIVE badges and junk."""
    if not text:
        return None
    parts = text.strip().split(":")
    if not 1 <= len(parts) <= 3 or not all(part.isdigit() for part in parts):
        return None
    seconds = 0
    for part in parts:
        seconds = seconds * 60 + int(part)
    return seconds


def age_from_date(date_text: str) -> float | None:
    try:
        published = datetime.strptime(date_text, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    except (ValueError, TypeError):
        return None
    return round((datetime.now(timezone.utc) - published).total_seconds() / 86400, 2)


# --------------------------------------------------------------------------- #
# YouTube
# --------------------------------------------------------------------------- #

DEFAULT_QUERIES = [
    ("th", "สอนใช้ AI"),
    ("th", "AI สำหรับมือใหม่"),
    ("th", "ใช้ AI ทำงาน"),
    ("th", "AI สร้างวิดีโอ"),
    ("th", "ChatGPT สอนใช้"),
    ("en", "ai for beginners"),
]
SORTS = [("relevance", ""), ("views", "&sp=CAMSAhAB")]

BEGINNER_WORDS = [
    "มือใหม่",
    "เริ่มต้น",
    "พื้นฐาน",
    "ครั้งแรก",
    "ง่าย",
    "ฟรี",
    "สอน",
    "วิธี",
    "beginner",
    "basics",
    "getting started",
    "how to",
    "tutorial",
    "guide",
    "for beginners",
]


def parse_search_page(page: str) -> list[dict]:
    data = yt_initial_data(page)
    if not data:
        return []
    renderers: list[dict] = []
    walk_collect(data, "videoRenderer", renderers)
    rows = []
    for renderer in renderers:
        video_id = renderer.get("videoId")
        title = runs_text(renderer.get("title"))
        if not video_id or not title:
            continue
        rows.append(
            {
                "id": video_id,
                "title": title,
                "channel": runs_text(renderer.get("ownerText")),
                "views_text": runs_text(renderer.get("viewCountText")),
                "published_text": runs_text(renderer.get("publishedTimeText")),
                "duration_text": runs_text(renderer.get("lengthText")),
                "url": "https://www.youtube.com/watch?v=" + video_id,
            }
        )
    return rows


def parse_watch_page(page: str) -> dict:
    """Exact stats from a watch page: views, length, publish date, likes, comments, copy."""
    out: dict = {}
    position = page.find("ytInitialPlayerResponse")
    if position >= 0:
        data, _ = json_object_at(page, position)
        if data:
            details = data.get("videoDetails") or {}
            micro = ((data.get("microformat") or {}).get("playerMicroformatRenderer")) or {}
            if details.get("viewCount"):
                out["views"] = parse_views(str(details["viewCount"]))
            if details.get("lengthSeconds"):
                out["duration_s"] = int(details["lengthSeconds"])
            if details.get("shortDescription"):
                out["description"] = details["shortDescription"]
            if details.get("keywords"):
                out["keywords"] = [str(k) for k in details["keywords"]]
            published = micro.get("publishDate") or micro.get("uploadDate") or ""
            if published:
                out["published_date"] = published[:10]

    match = re.search(r"like this video along with ([\d,]+) (?:other )?people", page)
    if match:
        out["likes"] = parse_views(match.group(1))
    if "likes" not in out:
        match = re.search(r'"likeCount"\s*:\s*"?(\d+)"?', page)
        if match:
            out["likes"] = int(match.group(1))
    match = re.search(r'"commentCount"\s*:\s*\{\s*"simpleText"\s*:\s*"([\d,]+)"', page)
    if match:
        out["comments"] = parse_views(match.group(1))
    return out


def fit_score(item: dict) -> float:
    """How well a piece targets Thai beginners, per the approved plan's weights."""
    text = (item.get("title") or "") + " " + (item.get("channel") or "")
    beginner = any(word in text.lower() for word in BEGINNER_WORDS)
    if item.get("lang") == "th":
        return 1.0 if beginner else 0.75
    return 0.6 if beginner else 0.35


def engagement_rate(likes, comments, views) -> float | None:
    if not views or (likes is None and comments is None):
        return None
    return ((likes or 0) + 2 * (comments or 0)) / views


def provisional_youtube(item: dict, window_days: int) -> float:
    """Score before likes are known, so enrichment can target the right videos."""
    age = item["age_days"] if item["age_days"] is not None else window_days / 2
    per_day = item["views"] / max(age, 0.5)
    reach = min(1.0, math.log10(per_day + 1) / 4.5)
    recency = 1 - min(1.0, age / window_days)
    return 0.60 * reach + 0.25 * recency + 0.15 * fit_score(item)


def score_youtube(item: dict, window_days: int, fallback_engagement: float) -> None:
    age = item["age_days"] if item["age_days"] is not None else window_days / 2
    per_day = item["views"] / max(age, 0.5)
    reach = min(1.0, math.log10(per_day + 1) / 4.5)

    engagement = item.get("engagement")
    estimated = engagement is None
    if estimated:
        engagement = fallback_engagement
    engagement_norm = min(1.0, engagement / 0.06)
    recency = 1 - min(1.0, age / window_days)

    item["views_per_day"] = round(per_day, 1)
    item["engagement"] = round(engagement, 5)
    item["engagement_estimated"] = estimated
    item["score_parts"] = {
        "reach": round(reach, 3),
        "engagement": round(engagement_norm, 3),
        "recency": round(recency, 3),
        "fit": round(fit_score(item), 3),
    }
    item["attention"] = round(
        100 * (0.45 * reach + 0.25 * engagement_norm + 0.20 * recency + 0.10 * fit_score(item)),
        1,
    )


def collect_youtube(
    queries: list[tuple[str, str]],
    window_days: int,
    enrich: int,
    offline: bool,
    log=print,
) -> tuple[list[dict], dict]:
    status = {"status": "ok", "requests": 0, "errors": [], "raw_rows": 0, "collected": 0}
    seen: dict[str, dict] = {}

    for query_lang, query in queries:
        for sort_name, sp in SORTS:
            url = "https://www.youtube.com/results?search_query=%s&hl=en&gl=TH%s" % (
                urllib.parse.quote_plus(query),
                sp,
            )
            try:
                page = http_get(url, ttl=1800, offline=offline)
                status["requests"] += 1
            except Exception as exc:  # noqa: BLE001 - reported in the payload
                status["errors"].append("%s/%s: %s" % (query, sort_name, exc))
                log("  ! youtube %s (%s) failed: %s" % (query, sort_name, exc))
                continue

            rows = parse_search_page(page)
            status["raw_rows"] += len(rows)
            for row in rows:
                item = seen.get(row["id"])
                if item is None:
                    item = dict(row)
                    item.update(
                        {
                            "platform": "youtube",
                            "lang": lang_of(row["title"]),
                            "query_lang": query_lang,
                            "queries": [],
                        }
                    )
                    seen[row["id"]] = item
                for tag in (query, "sort:" + sort_name):
                    if tag not in item["queries"]:
                        item["queries"].append(tag)
            log("  youtube %-26s %-9s %3d rows" % (query[:26], sort_name, len(rows)))

    items = list(seen.values())
    for item in items:
        item["views"] = parse_views(item.get("views_text"))
        item["age_days"] = parse_age_days(item.get("published_text"))
        item["duration_s"] = parse_duration(item.get("duration_text"))

    kept = []
    dropped_old = 0
    dropped_no_views = 0
    off_topic = []
    for item in items:
        if not item["views"]:
            dropped_no_views += 1
            continue
        if item["age_days"] is not None and item["age_days"] > window_days:
            dropped_old += 1
            continue
        if not looks_like_ai(item["title"]):
            off_topic.append(item["title"])
            continue
        kept.append(item)
    status["dropped_older_than_window"] = dropped_old
    status["dropped_zero_views"] = dropped_no_views
    status["dropped_not_ai"] = len(off_topic)
    status["dropped_examples"] = off_topic[:5]

    for item in kept:
        item["provisional"] = provisional_youtube(item, window_days)
    kept.sort(key=lambda row: row["provisional"], reverse=True)

    for item in kept[: max(0, enrich)]:
        try:
            page = http_get(item["url"], ttl=86400 * 7, offline=offline, retries=2)
            status["requests"] += 1
        except Exception as exc:  # noqa: BLE001 - keep the search-level numbers
            status["errors"].append("watch %s: %s" % (item["id"], exc))
            continue
        extra = parse_watch_page(page)
        for key in ("likes", "comments", "description", "keywords", "published_date"):
            if extra.get(key) is not None:
                item[key] = extra[key]
        if extra.get("views"):
            item["views"] = extra["views"]
        if extra.get("duration_s"):
            item["duration_s"] = extra["duration_s"]
        if item.get("published_date"):
            exact_age = age_from_date(item["published_date"])
            if exact_age is not None:
                item["age_days"] = exact_age
        item["enriched"] = True
        log(
            "  enriched %-40s %8s views  %s  likes=%s comments=%s"
            % (
                item["title"][:40],
                item["views"],
                item.get("published_date", "?"),
                item.get("likes", "n/a"),
                item.get("comments", "n/a"),
            )
        )

    for item in kept:
        item["engagement"] = engagement_rate(
            item.get("likes"), item.get("comments"), item.get("views")
        )
    known = [item["engagement"] for item in kept if item["engagement"] is not None]
    fallback = median(known) if known else 0.02

    for item in kept:
        score_youtube(item, window_days, fallback)
        item.pop("provisional", None)

    kept.sort(key=lambda row: row["attention"], reverse=True)
    status["collected"] = len(kept)
    status["enriched"] = sum(1 for item in kept if item.get("enriched"))
    status["median_engagement"] = round(fallback, 5)
    if status["errors"] and not kept:
        status["status"] = "failed"
    elif status["errors"]:
        status["status"] = "partial"
    return kept, status


# --------------------------------------------------------------------------- #
# Hacker News
# --------------------------------------------------------------------------- #

HN_QUERIES = ["ai", "chatgpt", "llm", "ai agents", "claude", "openai"]


def collect_hn(window_days: int, offline: bool, log=print) -> tuple[list[dict], dict]:
    status = {"status": "ok", "requests": 0, "errors": [], "collected": 0}
    since = int(time.time() - window_days * 86400)
    seen: dict[str, dict] = {}

    for query in HN_QUERIES:
        url = (
            "https://hn.algolia.com/api/v1/search?query=%s&tags=story"
            "&numericFilters=created_at_i%%3E%d,points%%3E100&hitsPerPage=40"
            % (urllib.parse.quote_plus(query), since)
        )
        try:
            body = http_get(url, ttl=1800, offline=offline)
            status["requests"] += 1
            payload = json.loads(body)
        except Exception as exc:  # noqa: BLE001 - reported in the payload
            status["errors"].append("%s: %s" % (query, exc))
            log("  ! hn %s failed: %s" % (query, exc))
            continue

        hits = payload.get("hits") or []
        for hit in hits:
            object_id = hit.get("objectID")
            if not object_id or object_id in seen:
                continue
            # Algolia matches "ai" inside "aid"/"said", so filter on the title itself.
            if not looks_like_ai(hit.get("title") or ""):
                status["skipped_off_topic"] = status.get("skipped_off_topic", 0) + 1
                continue
            created = hit.get("created_at_i") or 0
            seen[object_id] = {
                "platform": "hn",
                "id": object_id,
                "title": hit.get("title") or "",
                "url": hit.get("url") or ("https://news.ycombinator.com/item?id=" + object_id),
                "discussion_url": "https://news.ycombinator.com/item?id=" + object_id,
                "channel": "Hacker News",
                "lang": lang_of(hit.get("title") or ""),
                "points": int(hit.get("points") or 0),
                "comments": int(hit.get("num_comments") or 0),
                "published_date": (
                    datetime.fromtimestamp(created, timezone.utc).strftime("%Y-%m-%d")
                    if created
                    else ""
                ),
                "age_days": round((time.time() - created) / 86400, 2) if created else None,
                "queries": [query],
            }
        log("  hn %-14s %3d hits" % (query, len(hits)))

    for item in seen.values():
        # Log scale wide enough that the biggest stories of the year (~5k combined) do
        # not all pin at 100 and turn the ranking into a list of ties.
        combined = item["points"] + 2 * item["comments"]
        item["attention"] = round(100 * min(1.0, math.log10(combined + 1) / 4.2), 1)
        item["score_parts"] = {"points": item["points"], "comments": item["comments"]}

    items = sorted(
        seen.values(), key=lambda row: (row["attention"], row["points"]), reverse=True
    )
    status["collected"] = len(items)
    if status["errors"] and not items:
        status["status"] = "failed"
    elif status["errors"]:
        status["status"] = "partial"
    return items, status


# --------------------------------------------------------------------------- #
# Reddit (best effort - the public JSON API blocks this host, the Atom feed is flaky)
# --------------------------------------------------------------------------- #

REDDIT_SUBS = ["artificial", "ChatGPT", "OpenAI", "LocalLLaMA"]


def collect_reddit(offline: bool, log=print) -> tuple[list[dict], dict]:
    status = {"status": "ok", "requests": 0, "errors": [], "collected": 0}
    items: list[dict] = []

    for subreddit in REDDIT_SUBS:
        url = "https://www.reddit.com/r/%s/top/.rss?t=week&limit=25" % subreddit
        try:
            body = http_get(url, ttl=1800, offline=offline, retries=2)
            status["requests"] += 1
        except Exception as exc:  # noqa: BLE001 - Reddit blocks often; keep going
            status["errors"].append("%s: %s" % (subreddit, str(exc)[:140]))
            log("  ! reddit r/%s failed: %s" % (subreddit, str(exc)[:90]))
            continue

        entries = re.findall(r"<entry>(.*?)</entry>", body, re.S)
        for entry in entries:
            title = xml_text(entry, "title")
            if not title:
                continue
            link = re.search(r'<link[^>]*href="([^"]+)"', entry)
            items.append(
                {
                    "platform": "reddit",
                    "id": link.group(1) if link else title[:40],
                    "title": title,
                    "url": link.group(1) if link else "",
                    "channel": "r/" + subreddit,
                    "lang": lang_of(title),
                    "published_date": xml_text(entry, "updated")[:10],
                    "age_days": None,
                    # The Atom feed carries no score, so these stay out of the ranking.
                    "attention": None,
                    "score_parts": {"note": "feed has no score"},
                    "queries": [subreddit],
                }
            )
        log("  reddit r/%-12s %3d entries" % (subreddit, len(entries)))

    status["collected"] = len(items)
    if not items:
        status["status"] = "failed" if status["errors"] else "empty"
    elif status["errors"]:
        status["status"] = "partial"
    return items, status


# --------------------------------------------------------------------------- #
# Google Trends
# --------------------------------------------------------------------------- #

def collect_trends(offline: bool, log=print) -> tuple[list[dict], dict]:
    status = {"status": "ok", "requests": 0, "errors": [], "collected": 0}
    matches: list[dict] = []

    for geo in ("TH", "US"):
        url = "https://trends.google.com/trending/rss?geo=%s" % geo
        try:
            body = http_get(url, ttl=3600, offline=offline, retries=2)
            status["requests"] += 1
        except Exception as exc:  # noqa: BLE001 - reported in the payload
            status["errors"].append("%s: %s" % (geo, str(exc)[:140]))
            log("  ! trends %s failed: %s" % (geo, str(exc)[:90]))
            continue

        entries = re.findall(r"<item>(.*?)</item>", body, re.S)
        for entry in entries:
            title = xml_text(entry, "title")
            if not title or not AI_RE.search(title):
                continue
            matches.append(
                {
                    "geo": geo,
                    "query": title,
                    "approx_traffic": xml_text(entry, "ht:approx_traffic"),
                    "news_title": xml_text(entry, "ht:news_item_title"),
                    "published": xml_text(entry, "pubDate"),
                }
            )
        log("  trends %s %3d items, %d AI matches" % (geo, len(entries), len(matches)))

    status["collected"] = len(matches)
    status["scanned"] = True
    if status["errors"] and not matches:
        status["status"] = "failed"
    elif status["errors"]:
        status["status"] = "partial"
    return matches, status


# --------------------------------------------------------------------------- #
# Search demand (autocomplete)
# --------------------------------------------------------------------------- #

DEMAND_SEEDS = [
    "ai",
    "สอนใช้ ai",
    "ai ทำ",
    "chatgpt",
    "ai ทำงาน",
    "ai สร้าง",
    "ai ฟรี",
    "เรียน ai",
    "ai เขียน",
    "ai สรุป",
]


def parse_suggest(body: str, kind: str) -> list[str]:
    text = body.strip()
    if kind == "youtube":
        start = text.find("([")
        end = text.rfind("])")
        if start < 0 or end <= start:
            return []
        text = text[start + 1 : end + 1]
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return []
    if isinstance(data, list) and len(data) > 1 and isinstance(data[1], list):
        return [row[0] for row in data[1] if isinstance(row, list) and row]
    return []


def collect_demand(offline: bool, log=print) -> tuple[list[dict], dict]:
    status = {"status": "ok", "requests": 0, "errors": [], "collected": 0}
    entries: dict[str, dict] = {}

    for seed in DEMAND_SEEDS:
        for kind in ("google", "youtube"):
            if kind == "google":
                url = (
                    "https://suggestqueries.google.com/complete/search"
                    "?client=firefox&hl=th&gl=th&q=" + urllib.parse.quote(seed)
                )
            else:
                url = (
                    "https://suggestqueries.google.com/complete/search"
                    "?client=youtube&ds=yt&hl=th&gl=th&q=" + urllib.parse.quote(seed)
                )
            try:
                body = http_get(url, ttl=3600, offline=offline, retries=2)
                status["requests"] += 1
            except Exception as exc:  # noqa: BLE001 - reported in the payload
                status["errors"].append("%s/%s: %s" % (seed, kind, str(exc)[:100]))
                continue

            for suggestion in parse_suggest(body, kind):
                key = suggestion.strip().lower()
                if len(key) < 4:
                    continue
                record = entries.setdefault(
                    key,
                    {"query": suggestion.strip(), "count": 0, "kinds": set(), "seeds": []},
                )
                record["count"] += 1
                record["kinds"].add(kind)
                if seed not in record["seeds"]:
                    record["seeds"].append(seed)

    demand = []
    for record in entries.values():
        demand.append(
            {
                "query": record["query"],
                "count": record["count"],
                "kinds": sorted(record["kinds"]),
                "seeds": record["seeds"],
                "lang": lang_of(record["query"]),
            }
        )
    demand.sort(key=lambda row: (-row["count"], row["query"]))

    status["collected"] = len(demand)
    if status["errors"] and not demand:
        status["status"] = "failed"
    elif status["errors"]:
        status["status"] = "partial"
    log("  demand %d unique suggestions from %d seeds" % (len(demand), len(DEMAND_SEEDS)))
    return demand, status


# --------------------------------------------------------------------------- #
# Output
# --------------------------------------------------------------------------- #


def parse_query_spec(spec: str) -> list[tuple[str, str]]:
    if not spec.strip():
        return list(DEFAULT_QUERIES)
    queries = []
    for chunk in spec.split(","):
        chunk = chunk.strip()
        if not chunk:
            continue
        if ":" in chunk and chunk.split(":", 1)[0] in ("th", "en"):
            lang, query = chunk.split(":", 1)
            queries.append((lang.strip(), query.strip()))
        else:
            queries.append(("th", chunk))
    return queries


def flatten_rows(payload: dict) -> list[dict]:
    rows = []
    ranks: dict[str, int] = {}
    for item in payload["items"]:
        platform = item["platform"]
        ranks[platform] = ranks.get(platform, 0) + 1
        parts = item.get("score_parts") or {}
        rows.append(
            {
                "platform": platform,
                "rank": ranks[platform],
                "title": item.get("title", ""),
                "channel": item.get("channel", ""),
                "url": item.get("url", ""),
                "lang": item.get("lang", ""),
                "published_date": item.get("published_date", ""),
                "published_text": item.get("published_text", ""),
                "age_days": item.get("age_days", ""),
                "duration_s": item.get("duration_s", ""),
                "views": item.get("views", ""),
                "views_per_day": item.get("views_per_day", ""),
                "likes": item.get("likes", ""),
                "comments": item.get("comments", ""),
                "engagement": item.get("engagement", ""),
                "engagement_estimated": item.get("engagement_estimated", ""),
                "attention": item.get("attention", ""),
                "queries": " | ".join(item.get("queries") or []),
                "score_parts": json.dumps(parts, ensure_ascii=False, sort_keys=True),
            }
        )
    return rows


CSV_COLUMNS = [
    "platform",
    "rank",
    "title",
    "channel",
    "url",
    "lang",
    "published_date",
    "published_text",
    "age_days",
    "duration_s",
    "views",
    "views_per_day",
    "likes",
    "comments",
    "engagement",
    "engagement_estimated",
    "attention",
    "queries",
    "score_parts",
]


def write_outputs(payload: dict, out_prefix: str | None) -> tuple[str, str]:
    os.makedirs(DATA_DIR, exist_ok=True)
    stamp = payload["generated_at"][:10]
    base = out_prefix or os.path.join(DATA_DIR, "ai_content_" + stamp)
    json_path, csv_path = base + ".json", base + ".csv"

    with open(json_path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2)
    with open(csv_path, "w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=CSV_COLUMNS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(flatten_rows(payload))
    return json_path, csv_path


def latest_data_path() -> str | None:
    """Newest data/ai_content_*.json snapshot, for the analyzer to read."""
    if not os.path.isdir(DATA_DIR):
        return None
    names = sorted(
        name
        for name in os.listdir(DATA_DIR)
        if name.startswith("ai_content_") and name.endswith(".json")
    )
    return os.path.join(DATA_DIR, names[-1]) if names else None


def print_summary(payload: dict) -> None:
    print("\n=== sources ===")
    for name, status in payload["sources"].items():
        print(
            "  %-8s %-8s items=%s requests=%s errors=%d"
            % (
                name,
                status.get("status", "?"),
                status.get("collected", "-"),
                status.get("requests", "-"),
                len(status.get("errors") or []),
            )
        )
        for error in (status.get("errors") or [])[:2]:
            print("            ! " + str(error)[:110])
    if STALE_URLS:
        print("  note: %d request(s) fell back to a stale cache copy" % len(STALE_URLS))

    for platform, label in (("youtube", "YouTube"), ("hn", "Hacker News")):
        rows = [item for item in payload["items"] if item["platform"] == platform][:5]
        if not rows:
            continue
        print("\n=== top %s ===" % label)
        for index, item in enumerate(rows, 1):
            print(
                "  %d. %5.1f  %-58s %s"
                % (index, item["attention"], item["title"][:58], item.get("channel", "")[:22])
            )

    trends = payload.get("trends") or []
    print("\ntrends: %d AI matches" % len(trends))
    for row in trends[:3]:
        print("  - %s (%s)" % (row["query"], row.get("approx_traffic") or "?"))
    demand = payload.get("demand") or []
    print("demand: %d suggestions, top: %s" % (
        len(demand), ", ".join(row["query"] for row in demand[:5]) or "-"
    ))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--platforms",
        default="youtube,hn,reddit,trends,demand",
        help="comma separated: youtube,hn,reddit,trends,demand",
    )
    parser.add_argument(
        "--queries", default="", help="YouTube queries as 'th:คำค้น,en:query' (defaults built in)"
    )
    parser.add_argument("--days", type=int, default=365, help="publication window in days")
    parser.add_argument("--enrich", type=int, default=10, help="watch pages to fetch")
    parser.add_argument("--offline", action="store_true", help="cache only, no network")
    parser.add_argument("--out", default="", help="output path prefix (without extension)")
    args = parser.parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    wanted = {name.strip().lower() for name in args.platforms.split(",") if name.strip()}
    generated_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    payload = {
        "generated_at": generated_at,
        "window_days": args.days,
        "platforms": sorted(wanted),
        "sources": {},
        "items": [],
        "trends": [],
        "demand": [],
        "method": {
            "attention_youtube": (
                "100 x (0.45*log10(views per day)/4.5 capped + 0.25*engagement/6% capped "
                "+ 0.20*recency + 0.10*Thai-beginner fit)"
            ),
            "attention_hn": "100 x log10(points + 2*comments + 1)/4.2 capped",
            "engagement": (
                "(likes + 2*comments) / views; the watch page exposes likes but loads "
                "comments lazily, so comments are usually None; videos without likes use "
                "the median of the enriched sample"
            ),
            "relevance": (
                "a title must name an AI term (ai, chatgpt, claude, gemini, llm, เอไอ, ...); "
                "videos that only mention AI in the description are missed by design"
            ),
            "recency": "1 - age_days/window_days, so old hits cannot win on volume alone",
            "reddit": "Atom feed has no score, so Reddit rows are listed but not ranked",
        },
    }

    items: list[dict] = []
    if "youtube" in wanted:
        print("youtube:")
        rows, status = collect_youtube(
            parse_query_spec(args.queries), args.days, args.enrich, args.offline
        )
        items.extend(rows)
        payload["sources"]["youtube"] = status
    if "hn" in wanted:
        print("hacker news:")
        rows, status = collect_hn(args.days, args.offline)
        items.extend(rows)
        payload["sources"]["hn"] = status
    if "reddit" in wanted:
        print("reddit:")
        rows, status = collect_reddit(args.offline)
        items.extend(rows)
        payload["sources"]["reddit"] = status
    if "trends" in wanted:
        print("google trends:")
        rows, status = collect_trends(args.offline)
        payload["trends"] = rows
        payload["sources"]["trends"] = status
    if "demand" in wanted:
        print("search demand:")
        rows, status = collect_demand(args.offline)
        payload["demand"] = rows
        payload["sources"]["demand"] = status

    payload["items"] = sorted(
        items,
        key=lambda item: (item.get("attention") is None, -(item.get("attention") or 0)),
    )
    payload["counts"] = {
        platform: sum(1 for item in payload["items"] if item["platform"] == platform)
        for platform in ("youtube", "hn", "reddit")
    }

    json_path, csv_path = write_outputs(payload, args.out or None)
    print_summary(payload)
    print("\nwrote %s" % os.path.relpath(json_path, ROOT))
    print("wrote %s" % os.path.relpath(csv_path, ROOT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
