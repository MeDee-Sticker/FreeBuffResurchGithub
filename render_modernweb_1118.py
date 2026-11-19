"""Render the Modern Web Guidance clip (GitHub Trending, 18 Nov 2026).

Same 22 s beat sheet, look and score as the rest of the series; only the copy changes.
This one was #1 on the weekly board, so the numbers card counts **stars gained this week**
and the weekly rank — no total-star figure anywhere.

Facts: GoogleChrome/modern-web-guidance-src README + repo page, 2026-11-18.
262 covered web features / 204 guides, offline CLI search (BM25 + local embeddings, no keys),
Nov 8 eval snapshot guided 94% vs unguided 58%, Apache-2.0, stewarded by Chrome/Edge/Firefox/MDN.

Usage:
  python render_modernweb_1118.py --render              # silent master
  python render_modernweb_1118.py --scored              # score + _scored.mp4
  SUB_MARGIN_V=260 python render_modernweb_1118.py --tiktok
"""
import os
import subprocess
import sys

from PIL import ImageDraw

import render_t3code_promo as base
import render_trending_1109 as S

W, H, FPS, DUR = S.W, S.H, S.FPS, S.DUR

CLIPS = {
    "modernweb": {
        "out": "modern_web_guidance_promo_22s",
        "monogram": "MW",
        "accent": S.CYAN,
        "glow": base.GLOW_CYAN,
        "rank": 1,
        "gained": 7015,
        "chips": ["APACHE-2.0", "262 FEATURES", "OFFLINE CLI"],
        "term_title": "~/webapp  before",
        "term": [
            ("cmd", "> agent: add a smooth modal"),
            ("dim", "  reaches for a 12 kb polyfill"),
            ("ok", "  mwg search \"dialog backdrop\""),
            ("ok", "  guide + fallback → 9 lines"),
        ],
        "steps": [
            ("cover", "262 features, CSS to Baseline", S.CYAN),
            ("search", "offline BM25 + local embeddings", S.VIOLET),
            ("prove", "guided 94% vs unguided 58%", S.GREEN),
        ],
        "payoff_title": "~/webapp  after",
        "payoff": [
            ("ok", "  dialog, view transitions, no polyfill"),
            ("dim", "  fallback < 50 LOC, trial APIs gated"),
            ("ok", "  Apache-2.0  ·  9 agent harnesses"),
        ],
        "head": [
            (0.5, 2.9, "โค้ดเว็บจากข้อมูลเก่า", 78, 500),
            (3.15, 8.9, "262 ฟีเจอร์ใหม่", 84, 486),
            (9.3, 14.9, "วัดผลแล้วว่าไวกว่า", 76, 500),
            (19.4, 21.8, "Modern Web Guidance", 56, 452),
        ],
        "subs": [
            (0.6, 2.9, "โมเดลเขียนเว็บจากโค้ดเก่าที่มันเคยเห็น"),
            (3.4, 6.1, "ชุดนี้ป้อนคู่มือเว็บสมัยใหม่ให้ agent"),
            (6.1, 8.9, "262 ฟีเจอร์ ตั้งแต่ CSS จนถึง Baseline"),
            (9.4, 12.6, "ค้นหาในเครื่อง ปิดเน็ตก็ใช้ได้ ไม่ต้องมีคีย์"),
            (12.6, 14.9, "eval 8 พ.ย. ผ่าน 58% → 94% เมื่อมีคู่มือ"),
            (15.4, 18.9, "สัปดาห์นี้ +7,015 ดาว อันดับ 1 ของ weekly"),
            (19.5, 21.8, "Apache-2.0 · Chrome, Edge, Firefox, MDN"),
        ],
        "cmd": "npx modern-web-guidance install",
    },
}

S.CLIPS.update(CLIPS)


def scene_numbers(t, img, c):
    """Weekly numbers card — this repo topped the weekly board, not the daily one."""
    local = t - 15.0
    img = S.paste_glow(img, base.GLOW_CYAN, 540, 760, 0.9, 0.45)
    d = ImageDraw.Draw(img, "RGBA")
    v = int(c["gained"] * S.ease(S.seg(local, 0.15, 1.3)))
    d.text((540, 690), f"+{v:,}", font=S.F("bold", 176), fill=S.TXT + (255,), anchor="mm")
    d.text((540, 812), "STARS  THIS  WEEK", font=S.F("mono", 30), fill=S.CYAN + (235,), anchor="mm")
    badge = S.ease(S.seg(local, 1.7, 0.5))
    if badge > 0:
        bw = int(720 * badge)
        S.rr(d, [540 - bw // 2, 880, 540 + bw // 2, 966], 24, fill=(251, 191, 36, int(240 * badge)))
        if badge > 0.6:
            d.text((540, 924), f"#{c['rank']}  GITHUB  TRENDING  ·  WEEKLY",
                   font=S.F("bold", 28), fill=(26, 22, 10, 255), anchor="mm")
    note = S.ease(S.seg(local, 2.1, 0.6))
    if note > 0:
        d.text((540, 1160), c["chips"][0], font=S.F("bold", 84), fill=S.TXT + (int(250 * note),), anchor="mm")
        d.text((540, 1236), "LICENCE  ·  ON  THE  REPO", font=S.F("mono", 24),
               fill=S.MUTED + (int(235 * note),), anchor="mm")
        bw2 = int(760 * S.ease(S.seg(local, 2.4, 0.9)))
        S.rr(d, [160, 1290, 920, 1302], 8, fill=(255, 255, 255, 24))
        S.rr(d, [160, 1290, 160 + bw2, 1302], 8, fill=c["accent"] + (int(210 * note),))
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
    slug = "modernweb"
    c = CLIPS[slug]
    if not argv or "--list" in argv:
        print(__doc__)
        print(f"  {slug} {c['out']}.mp4  +{c['gained']:,} this week #{c['rank']}")
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
        rc = subprocess.run([sys.executable, "render_modernweb_1118.py", "--render"], env=env).returncode
        print(f"[{slug}] tiktok render exit {rc} at MarginV {S.SUB_MV}", flush=True)
        if rc != 0:
            return rc
        return build_audio.mux(silent, score_slug(slug), f"{c['out']}_tiktok_scored.mp4")
    print(__doc__)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
