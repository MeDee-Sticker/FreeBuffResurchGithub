"""Collect the on-screen script of every clip into one table (CSV + TSV).

Source of truth is the renderer: each clip's burned captions live in its spec, so the sheet
cannot drift from what is actually on screen. Dates and Page Auto ids come from the schedule
and batch docs. Usage:  python scripts/export_scripts_sheet.py
"""
import csv
import importlib
import io
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
sys.path.insert(0, ROOT)

# title, renderer module, output clip, reel-file, planned (date, time, channel, id) or None
CLIPS = [
    ("sherlock — หนึ่งชื่อ หลายบัญชี", "render_trending_1109", "sherlock_promo_22s",
     "sherlock_promo_22s_scored.mp4", None),
    ("OpenMausBot — บอทละเครื่อง", "render_trending_1109", "openmausbot_promo_22s",
     "openmausbot_promo_22s_scored.mp4", None),
    ("agent-browser — เบราว์เซอร์ที่ agent สั่งได้", "render_trending_1109", "agent_browser_promo_22s",
     "agent_browser_promo_22s_scored.mp4", None),
    ("astryx — design system สำหรับ agent", "render_trending_1109", "astryx_promo_22s",
     "astryx_promo_22s_scored.mp4", None),
    ("anthropics/skills — โฟลเดอร์ที่สอนงาน agent", "render_trending_1109", "anthropics_skills_promo_22s",
     "anthropics_skills_promo_22s_scored.mp4", None),
    ("agent-desktop — agent เห็นหน้าจอคอม", "render_aiagents_1117", "agent_desktop_promo_22s",
     "agent_desktop_promo_22s_tiktok_scored.mp4", ("17 พ.ย.", "20:00", "TikTok", "15")),
    ("security-audit-skill — ให้ agent ตรวจช่องโหว่", "render_aiagents_1117", "security_audit_promo_22s",
     "security_audit_promo_22s_tiktok_scored.mp4", ("18 พ.ย.", "20:00", "TikTok", "16")),
    ("MCP — ปลั๊กที่ทำให้ agent เห็นเครื่องมือ", "render_evergreen_1117", "mcp_promo_22s",
     "mcp_promo_22s_scored.mp4", ("17 พ.ย.", "19:00", "รีล เพจ", "174")),
    ("prompt ที่ดีคือข้อมูล ไม่ใช่คำสั่ง", "render_evergreen_1117", "prompt_is_data_promo_22s",
     "prompt_is_data_promo_22s_scored.mp4", ("18 พ.ย.", "19:00", "รีล เพจ", "175")),
    ("คลิปเดียว ทำได้ 3 ชิ้นงาน", "render_evergreen_1117", "one_clip_three_assets_promo_22s",
     "one_clip_three_assets_promo_22s_scored.mp4", ("19 พ.ย.", "19:00", "รีล เพจ", "186")),
    ("ตั้งราคาสินค้าดิจิทัล", "render_evergreen_1117", "digital_pricing_promo_22s",
     "digital_pricing_promo_22s_scored.mp4", ("20 พ.ย.", "19:00", "รีล เพจ", "187")),
    ("ตรวจงาน AI 3 นาทีก่อนส่งลูกค้า", "render_evergreen_1117", "ai_review_3min_promo_22s",
     "ai_review_3min_promo_22s_scored.mp4", ("21 พ.ย.", "19:00", "รีล เพจ", "188")),
]

# clips whose copy lives in their own single-clip renderer as HEAD / SUBS
OLDER = [
    ("t3code — พิมพ์หัวข้อ ได้คลิป", "render_t3code_promo", "t3code_promo_45s_scored.mp4"),
    ("claude-mem — context ข้าม session", "render_claude_mem_22s", "claude_mem_promo_22s_scored.mp4"),
    ("impeccable — คำสั่งแต่งงาน", "render_impeccable_22s", "impeccable_promo_22s_scored.mp4"),
    ("Scrapling — scraper ที่ทน anti-bot", "render_scrapling_22s", "scrapling_promo_22s_scored.mp4"),
    ("hallmark — กันงานหน้าตา AI", "render_hallmark_22s", "hallmark_promo_22s_scored.mp4"),
]


def schedule_rows():
    """[(date, time, channel, id, filename)] rows from the 10-16 Nov schedule."""
    path = "schedule_kopwang_2026-11-09_to_16.md"
    if not os.path.exists(path):
        return []
    out, cur = [], None
    for line in io.open(path, encoding="utf-8"):
        head = re.match(r"^###\s+.*?(\d{1,2})\s+พ\.ย\.", line)
        if head:
            cur = f"{head.group(1)} พ.ย."
            continue
        if not cur or not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) >= 6 and ":" in cells[0] and cells[3]:
            out.append((cur, cells[0], cells[1], cells[2], re.sub(r"`", "", cells[3])))
    return out


def schedule_for(rows, fragments):
    """First matching schedule slot plus every other slot sharing it (reel + TikTok)."""
    hits = [r for r in rows if any(f and f in r[4] for f in fragments)]
    if not hits:
        return ("", "", "", "")
    first = hits[0]
    if len(hits) == 1:
        return first[:4]
    ids = " · ".join(f"{h[2]} {h[3]}" for h in hits)
    channels = " + ".join(sorted({h[2] for h in hits}, key=lambda c: -len(c)))
    return (first[0], "/".join(sorted({h[1] for h in hits})), channels, ids)


# the schedule names files REELS_02_mausbot_…, so a slug does not always appear verbatim
SLUG_ALIASES = {
    "openmausbot_promo_22s": ["mausbot"],
    "agent_browser_promo_22s": ["agentbr"],
    "anthropics_skills_promo_22s": ["skills"],
}


def text_of(items):
    """SUBS/head entries are (start, end, text) or (start, end, text, ...); keep the text."""
    return [i[2] for i in items if isinstance(i, (list, tuple)) and len(i) > 2]


def main():
    sched = schedule_rows()
    rows = []
    for title, module, slug, fname, planned in CLIPS:
        mod = importlib.import_module(module)
        spec = next((c for c in mod.CLIPS.values() if isinstance(c, dict) and c.get("out") == slug), None)
        if not spec:
            print("missing spec:", slug)
            continue
        when = planned or schedule_for(
            sched, SLUG_ALIASES.get(slug, [slug.replace("_promo_22s", "")]))
        rows.append([title, fname, when[0], when[1], when[2], when[3],
                     " | ".join(text_of(spec["head"])),
                     " / ".join(text_of(spec["subs"])),
                     spec.get("cmd", "")])

    for title, module, fname in OLDER:
        try:
            mod = importlib.import_module(module)
        except Exception as exc:  # a single-clip renderer may need optional deps
            print("skip", module, exc)
            continue
        when = schedule_for(sched, [fname.replace("_promo_22s_scored.mp4", "").replace("_promo_45s_scored.mp4", "")])
        rows.append([title, fname, when[0], when[1], when[2], when[3],
                     " | ".join(text_of(getattr(mod, "HEAD", []))),
                     " / ".join(text_of(getattr(mod, "SUBS", []))),
                     ""])

    header = ["คลิป", "ไฟล์", "วันที่ลง", "เวลา", "ช่อง", "id ใน Page Auto",
              "ฮุกบนจอ (4 ช่วง)", "สคริปต์ซับไตเติล (เรียงตามเวลา)", "คำสั่งท้ายคลิป"]
    with io.open("scripts_all_clips.csv", "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)
    with io.open("scripts_all_clips.tsv", "w", encoding="utf-8") as f:
        f.write("\t".join(header) + "\n")
        for r in rows:
            f.write("\t".join(str(x).replace("\t", " ") for x in r) + "\n")
    print(f"{len(rows)} clips -> scripts_all_clips.csv / .tsv")
    for r in rows:
        print(f"  {r[0][:36]:38s} {r[2]:8s} {r[3]:6s} {r[4]:9s} id={r[5]:4s} subs={len(r[7].split(' / ')) if r[7] else 0}")


if __name__ == "__main__":
    main()
