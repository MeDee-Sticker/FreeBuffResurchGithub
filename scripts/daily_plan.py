#!/usr/bin/env python3
"""Plan today's trending clip from the freshest weekly snapshot, and gate stale numbers.

The daily loop is: fetch the board -> pick a repo nobody has covered -> write the renderer with
that repo's `rank` and `stars gained this week` -> render -> check -> upload -> schedule. This
script owns the first two steps and the freshness rule, so a render can never quietly ship
numbers that are older than `FRESH_DAYS` or a repo that already has a clip.

    python scripts/daily_plan.py                        # today's plan, human readable
    python scripts/daily_plan.py --top 8 --markdown     # table for the daily report
    python scripts/daily_plan.py --json                 # same, machine readable
    python scripts/daily_plan.py --write-plan data/daily_plan.md

    python scripts/daily_plan.py --verify render_<slug>_<MMDD>.py
        fail (exit 1) when a renderer's on-screen numbers match no row of today's board, or when
        its repo / output name was already used.

    python scripts/daily_plan.py --record --repo GoogleChrome/modern-web-guidance-src \
        --out modern_web_guidance_promo_22s --renderer render_modernweb_1118.py \
        --clip-ids 82,83 --reel-post 190 --tiktok-post 23 \
        --slot 2026-11-22T19:00,2026-11-22T20:00
        append the finished clip to data/clip_registry.json (the "do not repeat" list).

Exit codes: 0 ok, 1 gate failure (stale board, used repo, numbers off the board), 2 no snapshot.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date, datetime
from pathlib import Path

DATA_DIR = Path("data")
REGISTRY = DATA_DIR / "clip_registry.json"
FRESH_DAYS = 3          # numbers are good for 3 days after the board was fetched (see runbook)
DEFAULT_TOP = 6


def snapshot_paths(data_dir: Path = DATA_DIR) -> list[Path]:
    return sorted(data_dir.glob("trending_*_weekly.json"))


def load_snapshot(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if "repos" not in data:
        raise SystemExit(f"{path} is not a trending snapshot (no 'repos')")
    return data


def newest_snapshot(data_dir: Path = DATA_DIR) -> Path | None:
    """Newest weekly snapshot by its collected date, falling back to the filename."""
    best: tuple[str, Path] | None = None
    for path in snapshot_paths(data_dir):
        try:
            collected = str(load_snapshot(path).get("collected_on") or "")
        except (SystemExit, json.JSONDecodeError):
            collected = ""
        key = collected or path.stem
        if best is None or key > best[0]:
            best = (key, path)
    return best[1] if best else None


def rows_of(snap: dict) -> list[dict]:
    """Normalise both snapshot shapes: the fetcher's (`stars_gained`) and the merged board (`gain`)."""
    rows = []
    for index, row in enumerate(snap.get("repos") or [], 1):
        repo = row.get("repo") or ""
        if not repo:
            continue
        rows.append(
            {
                "repo": repo,
                "rank": int(row.get("rank") or index),
                "gain": int(row.get("gain") or row.get("stars_gained") or 0),
                "lang": row.get("lang") or row.get("language") or "",
                "desc": (row.get("desc") or row.get("description") or "").strip(),
            }
        )
    rows.sort(key=lambda r: (-r["gain"], r["rank"]))
    return rows


def load_registry(path: Path = REGISTRY) -> dict:
    if not path.exists():
        return {"schema": "clip-registry/1", "updated_on": None, "clips": []}
    return json.loads(path.read_text(encoding="utf-8"))


def save_registry(registry: dict, path: Path = REGISTRY) -> None:
    registry["updated_on"] = date.today().isoformat()
    registry["clips"] = sorted(registry["clips"], key=lambda c: (c.get("made_on") or "", c["out"]))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(registry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def freshness(snap: dict) -> dict:
    collected = str(snap.get("collected_on") or "")
    try:
        day = date.fromisoformat(collected)
    except ValueError:
        return {"collected_on": collected, "age_days": None, "valid_until": None, "fresh": False}
    age = (date.today() - day).days
    return {
        "collected_on": collected,
        "age_days": age,
        "valid_until": (day.toordinal() and date.fromordinal(day.toordinal() + FRESH_DAYS)).isoformat(),
        "fresh": age <= FRESH_DAYS,
    }


def plan(path: Path | None, registry: dict, top: int) -> dict:
    if path is None:
        raise SystemExit("no data/trending_*_weekly.json — run scripts/fetch_trending_daily.py --since weekly")
    snap = load_snapshot(path)
    used = {c["repo"] for c in registry.get("clips", []) if c.get("repo")}
    rows = rows_of(snap)
    candidates = [r for r in rows if r["repo"] not in used]
    return {
        "snapshot": str(path),
        "freshness": freshness(snap),
        "board_rows": len(rows),
        "used_repos": len(used),
        "candidates": candidates[:top],
    }


def print_plan(result: dict, markdown: bool) -> None:
    f = result["freshness"]
    state = "ใช้ได้" if f["fresh"] else "หมดอายุ — ดึงบอร์ดใหม่ก่อนเรนเดอร์"
    head = (
        f"บอร์ด: `{result['snapshot']}` · เก็บ {f['collected_on'] or '?'} · "
        f"อายุ {f['age_days']} วัน · ใช้ได้ถึง {f['valid_until'] or '?'} · **{state}**\n"
        f"คลิปที่ทำแล้ว {result['used_repos']} รีโป · เหลือให้เลือกในบอร์ดนี้ {len(result['candidates'])}\n"
    )
    if markdown:
        print(head)
        print("| # | รีโป | +ดาวสัปดาห์นี้ | ภาษา | ทำอะไร |")
        print("|---|---|---|---|---|")
        for c in result["candidates"]:
            desc = c["desc"].replace("|", "/")
            print(f"| {c['rank']} | `{c['repo']}` | +{c['gain']:,} | {c['lang'] or '—'} | {desc[:90]} |")
        return

    print(head)
    print("เรียงตามดาวที่ได้ในสัปดาห์นี้ (gain) — เลือกตามมุมที่ยังไม่ซ้ำ ไม่ใช่ตามลำดับนี้เสมอ\n")
    for c in result["candidates"]:
        print(f"  #{c['rank']:<2} {c['repo']:<42} +{c['gain']:>6,}  {c['lang']:<10} {c['desc'][:60]}")
    if result["candidates"]:
        top = result["candidates"][0]
        print("\nตัวเลขที่ต้องใส่ในสคริปต์เรนเดอร์:")
        print(f'  "rank": {top["rank"]},')
        print(f'  "gained": {top["gain"]},')
        print(f"  # {top['repo']}")


def verify(renderer: Path, path: Path | None, registry: dict) -> int:
    if not renderer.exists():
        raise SystemExit(f"{renderer} not found")
    if path is None:
        raise SystemExit("no data/trending_*_weekly.json — nothing to verify against")
    text = renderer.read_text(encoding="utf-8")
    outs = re.findall(r'"out":\s*"([^"]+)"', text)
    gains = [int(g) for g in re.findall(r'"gained":\s*(\d+)', text)]
    ranks = [int(r) for r in re.findall(r'"rank":\s*(\d+)', text)]
    if not outs or not gains:
        raise SystemExit(f"{renderer} has no \"out\"/\"gained\" entry to verify")

    snap = load_snapshot(path)
    f = freshness(snap)
    rows = rows_of(snap)
    used = {c["repo"] for c in registry.get("clips", []) if c.get("repo")}
    used_outs = {c["out"] for c in registry.get("clips", [])}

    fails = []
    if not f["fresh"]:
        fails.append(
            f"บอร์ดเก่า {f['age_days']} วัน (เก็บ {f['collected_on']}, ใช้ได้ถึง {f['valid_until']}) "
            "— ดึงใหม่แล้วแก้ตัวเลขก่อนเรนเดอร์"
        )
    for out in outs:
        if out in used_outs:
            fails.append(f"ชื่อคลิป `{out}` มีใน registry แล้ว — ห้ามเรนเดอร์ทับของเก่า")
    for gain, rank in zip(gains, ranks):
        match = next((r for r in rows if r["gain"] == gain), None)
        if match is None:
            fails.append(f"+{gain:,} ไม่อยู่ในบอร์ด {f['collected_on']} — ตัวเลขบนจอไม่ตรงกับบอร์ด")
            continue
        if match["rank"] != rank:
            fails.append(f"+{gain:,} อยู่อันดับ {match['rank']} ไม่ใช่ {rank}")
        if match["repo"] in used:
            fails.append(f"`{match['repo']}` ทำคลิปไปแล้ว — เลือกตัวอื่น")
        print(f"{renderer.name}: +{gain:,} · #{rank} → `{match['repo']}`")

    for line in fails:
        print(f"  - {line}")
    print("PASS — ตัวเลขตรงกับบอร์ดล่าสุด" if not fails else "FAIL — แก้ก่อนเรนเดอร์")
    return 0 if not fails else 1


def record(args) -> int:
    if not args.repo or not args.out:
        raise SystemExit("--record needs --repo and --out")
    registry = load_registry()
    if any(c["out"] == args.out for c in registry["clips"]):
        raise SystemExit(f"`{args.out}` already in {REGISTRY} — edit the entry instead of adding it twice")
    entry = {
        "repo": args.repo,
        "out": args.out,
        "made_on": args.made_on or date.today().isoformat(),
        "renderer": args.renderer,
        "clip_ids": [int(x) for x in (args.clip_ids or "").replace(" ", "").split(",") if x],
        "reel_post": int(args.reel_post) if args.reel_post else None,
        "tiktok_post": int(args.tiktok_post) if args.tiktok_post else None,
        "scheduled": [s.strip() for s in (args.slot or "").split(",") if s.strip()],
        "note": args.note or "",
    }
    registry["clips"].append(entry)
    save_registry(registry)
    print(f"recorded `{args.out}` ({args.repo}) — {len(registry['clips'])} clips in {REGISTRY}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--snapshot", help="snapshot file (default: newest data/trending_*_weekly.json)")
    parser.add_argument("--top", type=int, default=DEFAULT_TOP, help=f"candidates to list (default {DEFAULT_TOP})")
    parser.add_argument("--markdown", action="store_true", help="print the candidate table as markdown")
    parser.add_argument("--json", action="store_true", help="print the plan as JSON")
    parser.add_argument("--write-plan", metavar="FILE", help="also write the markdown plan to FILE")
    parser.add_argument("--verify", metavar="RENDERER", help="gate one renderer against the board")
    parser.add_argument("--record", action="store_true", help="append a finished clip to the registry")
    parser.add_argument("--repo")
    parser.add_argument("--out")
    parser.add_argument("--renderer")
    parser.add_argument("--made-on", dest="made_on")
    parser.add_argument("--clip-ids", dest="clip_ids")
    parser.add_argument("--reel-post", dest="reel_post")
    parser.add_argument("--tiktok-post", dest="tiktok_post")
    parser.add_argument("--slot", help="scheduled slots, comma separated, e.g. 2026-11-23T19:00,2026-11-23T20:00")
    parser.add_argument("--note")
    parser.add_argument("--allow-stale", action="store_true", help="plan anyway on an old board")
    args = parser.parse_args(argv)

    path = Path(args.snapshot) if args.snapshot else newest_snapshot()
    registry = load_registry()

    if args.record:
        return record(args)
    if args.verify:
        return verify(Path(args.verify), path, registry)
    if path is None:
        print("no data/trending_*_weekly.json — run scripts/fetch_trending_daily.py --since weekly",
              file=sys.stderr)
        return 2

    result = plan(path, registry, args.top)
    if args.write_plan:
        import contextlib
        import io
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            print_plan(result, markdown=True)
        Path(args.write_plan).parent.mkdir(parents=True, exist_ok=True)
        Path(args.write_plan).write_text(buffer.getvalue(), encoding="utf-8")

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print_plan(result, markdown=args.markdown)

    if not result["freshness"]["fresh"] and not args.allow_stale:
        print(
            f"\nboard is {result['freshness']['age_days']} days old (valid {FRESH_DAYS}) — "
            "fetch again before rendering",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
