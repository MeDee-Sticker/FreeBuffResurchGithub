"""Render the Claude-BugHunter clip (GitHub Trending, 18 Nov 2026).

Same 22 s beat sheet, look and score as the rest of the series; only the copy changes.
The numbers card counts **stars gained this week** and the weekly rank, with the daily
board as a second line — the repo was #1 on daily and #3 on weekly the day it was scouted.

Facts: elementalsouls/Claude-BugHunter README + repo page, 2026-11-18.
MIT for the code, CC-BY-4.0 for the written content.

Usage:
  python render_bughunter_1118.py --render              # silent master
  python render_bughunter_1118.py --scored              # score + _scored.mp4
  SUB_MARGIN_V=260 python render_bughunter_1118.py --tiktok
"""
import os
import subprocess
import sys

from PIL import ImageDraw

import render_t3code_promo as base
import render_trending_1109 as S

W, H, FPS, DUR = S.W, S.H, S.FPS, S.DUR

CLIPS = {
    "bughunter": {
        "out": "claude_bughunter_promo_22s",
        "monogram": "BH",
        "accent": S.RED,
        "glow": base.GLOW_VIOLET,
        "rank": 3,
        "gained": 2508,
        "daily": 2322,
        "daily_rank": 1,
        "window": "STARS  THIS  WEEK",
        "chips": ["MIT", "83 SKILLS", "BURP MCP"],
        "term_title": "~/engagements  acme",
        "term": [
            ("cmd", "> /hunt acme.com --scope h1"),
            ("ok", "  recon → 47 hosts, ranked"),
            ("ok", "  hunt-xss · hunt-oauth … auto"),
            ("dim", "  7-question gate before submit"),
        ],
        "steps": [
            ("think", "methodology + red-team discipline", S.CYAN),
            ("hunt", "58 vuln classes from 681 reports", S.VIOLET),
            ("validate", "scope in code, gate, then report", S.GREEN),
        ],
        "payoff_title": "~/engagements  acme  findings",
        "payoff": [
            ("ok", "  confirmed 2  ·  needs proof 3  ·  out 11"),
            ("dim", "  severity mapped to VRT, PII redacted"),
            ("ok", "  HackerOne / Bugcrowd ready  ·  MIT"),
        ],
        "head": [
            (0.5, 2.9, "ล่าจากข้างนอก", 92, 540),
            (3.15, 8.9, "83 สกิล 15 คำสั่ง", 60, 486),
            (9.3, 14.9, "ในขอบเขตเสมอ", 76, 500),
            (19.4, 21.8, "Claude-BugHunter", 62, 460),
        ],
        "subs": [
            (0.6, 2.9, "ตรวจโค้ดตัวเอง กับล่าจากข้างนอก เป็นคนละงาน"),
            (3.4, 6.1, "ชุดสกิลนี้ติดตั้งครั้งเดียว Claude Code เปลี่ยนบท"),
            (6.1, 8.9, "83 สกิล โหลดเองตามหัวข้อที่คุณกำลังทดสอบ"),
            (9.4, 12.6, "58 หัวข้อช่องโหว่ สกัดจากรายงาน HackerOne 681 ฉบับ"),
            (12.6, 14.9, "ตรวจขอบเขตในโค้ด มีด่าน 7 คำถามก่อนส่งรายงาน"),
            (15.4, 18.9, "สัปดาห์นี้ +2,508 ดาว อันดับ 3 · วันนี้ +2,322 อันดับ 1"),
            (19.5, 21.8, "ใช้กับเป้าที่ได้รับอนุญาตเท่านั้น · MIT"),
        ],
        "cmd": "git clone elementalsouls/Claude-BugHunter",
    },
}

S.CLIPS.update(CLIPS)


def scene_numbers(t, img, c):
    """Weekly numbers card + the daily board as a second line."""
    local = t - 15.0
    img = S.paste_glow(img, base.GLOW_CYAN, 540, 760, 0.9, 0.45)
    d = ImageDraw.Draw(img, "RGBA")
    v = int(c["gained"] * S.ease(S.seg(local, 0.15, 1.3)))
    d.text((540, 690), f"+{v:,}", font=S.F("bold", 176), fill=S.TXT + (255,), anchor="mm")
    d.text((540, 812), c["window"], font=S.F("mono", 30), fill=S.CYAN + (235,), anchor="mm")
    badge = S.ease(S.seg(local, 1.7, 0.5))
    if badge > 0:
        bw = int(720 * badge)
        S.rr(d, [540 - bw // 2, 880, 540 + bw // 2, 966], 24, fill=(251, 191, 36, int(240 * badge)))
        if badge > 0.6:
            d.text((540, 924), f"#{c['rank']}  GITHUB  TRENDING  ·  WEEKLY",
                   font=S.F("bold", 28), fill=(26, 22, 10, 255), anchor="mm")
    dk = S.ease(S.seg(local, 2.1, 0.5))
    if dk > 0:  # daily board, the reason the repo got scouted
        S.rr(d, [240, 998, 840, 1082], 22, fill=S.PANEL + (int(240 * dk),),
             outline=c["accent"] + (int(170 * dk),), width=2)
        if dk > 0.7:
            d.text((540, 1040), f"+{c['daily']:,}  TODAY   ·   DAILY  #{c['daily_rank']}",
                   font=S.F("bold", 30), fill=S.TXT + (int(250 * dk),), anchor="mm")
    note = S.ease(S.seg(local, 2.5, 0.6))
    if note > 0:
        d.text((540, 1180), c["chips"][0], font=S.F("bold", 84), fill=S.TXT + (int(250 * note),), anchor="mm")
        d.text((540, 1256), "CODE  ·  CONTENT  CC-BY-4.0", font=S.F("mono", 24),
               fill=S.MUTED + (int(235 * note),), anchor="mm")
        bw2 = int(760 * S.ease(S.seg(local, 2.8, 0.9)))
        S.rr(d, [160, 1310, 920, 1322], 8, fill=(255, 255, 255, 24))
        S.rr(d, [160, 1310, 160 + bw2, 1322], 8, fill=c["accent"] + (int(210 * note),))
    return img


S.SCENES = [(0.0, S.scene_hook), (3.0, S.scene_steps), (9.0, S.scene_payoff),
            (15.0, scene_numbers), (19.0, S.scene_cta)]


def score_slug(slug):
    import build_audio
    path = os.path.join("build", f"score_{slug}.wav")
    if not os.path.exists(path):
        build_audio.build(slug, 22.0, 100, build_audio.IMP_CUTS, (0, 2), 8,
                          ticks=(15.15, 16.45, 0.08), end_fade=(20.9, 22.0))
    return path


def main(argv):
    slug = "bughunter"
    c = CLIPS[slug]
    if not argv or "--list" in argv:
        print(__doc__)
        print(f"  {slug} {c['out']}.mp4  +{c['gained']:,} this week #{c['rank']}"
              f"  ·  +{c['daily']:,} today #{c['daily_rank']}")
        return 0
    if "--render" in argv:
        return S.encode(slug)
    if "--scored" in argv:
        import build_audio
        master = f"{c['out']}.mp4"
        if not os.path.exists(master):
            sys.exit(f"{master} missing — run --render first")
        return build_audio.mux(master, score_slug(slug), f"{c['out']}_scored.mp4")
    if "--tiktok" in argv:
        import build_audio
        silent = os.path.join("build", f"{c['out']}_tiktok.mp4")
        env = dict(os.environ, OUT_NAME=silent)
        rc = subprocess.run([sys.executable, "render_bughunter_1118.py", "--render"], env=env).returncode
        print(f"[{slug}] tiktok render exit {rc} at MarginV {S.SUB_MV}", flush=True)
        if rc != 0:
            return rc
        return build_audio.mux(silent, score_slug(slug), f"{c['out']}_tiktok_scored.mp4")
    print(__doc__)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
