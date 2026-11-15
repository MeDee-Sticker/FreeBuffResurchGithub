"""Render the two AI-agent clips slotted into 17-18 Nov 2026 (TikTok 20:00).

Reuses the 2026-11-09 series renderer so the picture, beat sheet and caption system stay
identical to the clips already published. Differences from that series:

  * the numbers scene counts **stars gained this week** and the weekly rank, because both
    repos were scouted from the weekly board, not the daily one
  * the score is built from the same cue grid as the rest of the 22 s set

Usage:
  python render_aiagents_1117.py --list
  python render_aiagents_1117.py --render              # silent masters
  python render_aiagents_1117.py --render ade          # one clip
  python render_aiagents_1117.py --scored              # build scores + mux _scored.mp4
  SUB_MARGIN_V=260 python render_aiagents_1117.py --tiktok
"""
import os
import subprocess
import sys

from PIL import ImageDraw

import render_t3code_promo as base
import render_trending_1109 as S

W, H, FPS, DUR = S.W, S.H, S.FPS, S.DUR

CLIPS = {
    "ade": {
        "out": "agent_desktop_promo_22s",
        "monogram": "AD",
        "accent": S.CYAN,
        "glow": base.GLOW_CYAN,
        "rank": 2,
        "gained": 12120,
        "window": "STARS  THIS  WEEK",
        "chips": ["APACHE-2.0", "MACOS · WIN · LINUX", "CLI + C LIB"],
        "term_title": "~/desktop  snapshot",
        "term": [
            ("cmd", "> agent-desktop snapshot --app Finder"),
            ("ok", "  window  Downloads  ·  59 refs"),
            ("ok", "  @s8f3k2p9:e8   Click"),
            ("dim", "  the accessibility tree, as JSON"),
        ],
        "steps": [
            ("tree", "the UI as JSON, a ref per element", S.CYAN),
            ("act", "click or type on a ref, then re-read", S.VIOLET),
            ("loop", "no model inside — the loop is yours", S.GREEN),
        ],
        "payoff_title": "~/desktop  loop",
        "payoff": [
            ("cmd", "> agent-desktop click @s8f3k2p9:e8"),
            ("dim", "  no screenshots, no pixel matching"),
            ("ok", "  snapshots hold private data — keep logs clean"),
        ],
        "head": [
            (0.5, 2.9, "agent ที่คุมหน้าจอคอม", 70, 540),
            (3.15, 8.9, "ไม่ต้องเดาพิกเซล", 86, 486),
            (9.3, 14.9, "ลูปอยู่ที่ agent คุณ", 68, 500),
            (19.4, 21.8, "npm i -g agent-desktop", 64, 460),
        ],
        "subs": [
            (0.6, 2.9, "คุมหน้าจอคอม ไม่ต้องถ่ายภาพจอแล้วเดาพิกเซล"),
            (3.4, 6.1, "agent-desktop อ่าน accessibility tree ของแอป"),
            (6.1, 8.9, "คืนมาเป็น JSON ทุกปุ่มมี ref ให้สั่งตรงตัว"),
            (9.4, 12.6, "คลิกหรือพิมพ์บน ref แล้วอ่านซ้ำเพื่อยืนยันผล"),
            (12.6, 14.9, "ตัวมันไม่มีโมเดล ลูปตัดสินใจอยู่ที่ agent ของคุณ"),
            (15.4, 18.9, "สัปดาห์นี้ +12,120 ดาว อันดับ 2 ของ trending"),
            (19.5, 21.8, "macOS · Windows · Linux · Apache-2.0"),
        ],
        "cmd": "npm i -g agent-desktop",
    },
    "sec": {
        "out": "security_audit_promo_22s",
        "monogram": "SA",
        "accent": S.GREEN,
        "glow": base.GLOW_VIOLET,
        "rank": 12,
        "gained": 10695,
        "window": "STARS  THIS  WEEK",
        "chips": ["MIT", "CODING-AGENT SKILL", "6 PHASES"],
        "term_title": "~/repo  /security-audit",
        "term": [
            ("cmd", "> skills add security-audit"),
            ("dim", "  recon  →  coverage ledger"),
            ("ok", "  hunters  ·  fresh verifiers"),
            ("ok", "  findings.json  validated"),
        ],
        "steps": [
            ("recon", "map trust boundaries into a ledger", S.CYAN),
            ("hunt", "isolated hunters, critics find gaps", S.VIOLET),
            ("disprove", "a fresh verifier tries to kill it", S.GREEN),
        ],
        "payoff_title": "~/repo  findings",
        "payoff": [
            ("ok", "  confirmed 5  ·  needs 2  ·  rejected 9"),
            ("dim", "  every claim traced back to source"),
            ("ok", "  REPORT.md  ·  FINDINGS-DETAIL.md"),
        ],
        "head": [
            (0.5, 2.9, "ให้ agent ตรวจช่องโหว่", 74, 540),
            (3.15, 8.9, "มีคนคอยค้าน", 88, 486),
            (9.3, 14.9, "ไม่เชื่อรอบแรก", 72, 500),
            (19.4, 21.8, "สกิลของ Cloudflare", 64, 460),
        ],
        "subs": [
            (0.6, 2.9, "agent เขียนโค้ดเร็วขึ้น แล้วใครตรวจว่าปลอดภัย"),
            (3.4, 6.1, "security-audit สั่งตรวจเป็นเฟส ไม่ใช่ถามครั้งเดียว"),
            (6.1, 8.9, "แมปสถาปัตยกรรม แล้วแบ่งงานให้นักล่าแยกกัน"),
            (9.4, 12.6, "ทุกข้อสงสัยต้องผ่านผู้ตรวจใหม่ที่พยายามหักล้าง"),
            (12.6, 14.9, "ผลแยก ยืนยันแล้ว · ยังต้องตรวจ · ตกไป"),
            (15.4, 18.9, "สัปดาห์นี้ +10,695 ดาว อันดับ 12 ของ trending"),
            (19.5, 21.8, "MIT · ติดตั้งผ่าน skills CLI · ไม่ใช่โปรแกรมกดใช้"),
        ],
        "cmd": "npx skills add cloudflare/security-audit-skill",
    },
}

S.CLIPS.update(CLIPS)


def scene_numbers(t, img, c):
    """Weekly variant of the series numbers card: gained this week + weekly rank."""
    local = t - 15.0
    img = S.paste_glow(img, base.GLOW_CYAN, 540, 760, 0.9, 0.45)
    d = ImageDraw.Draw(img, "RGBA")
    v = int(c["gained"] * S.ease(S.seg(local, 0.15, 1.3)))
    d.text((540, 700), f"+{v:,}", font=S.F("bold", 176), fill=S.TXT + (255,), anchor="mm")
    d.text((540, 826), c["window"], font=S.F("mono", 30), fill=S.CYAN + (235,), anchor="mm")
    badge = S.ease(S.seg(local, 1.7, 0.5))
    if badge > 0:
        bw = int(720 * badge)
        S.rr(d, [540 - bw // 2, 902, 540 + bw // 2, 994], 24, fill=(251, 191, 36, int(240 * badge)))
        if badge > 0.6:
            d.text((540, 948), f"#{c['rank']}  GITHUB  TRENDING  ·  WEEKLY",
                   font=S.F("bold", 30), fill=(26, 22, 10, 255), anchor="mm")
    note = S.ease(S.seg(local, 2.3, 0.6))
    if note > 0:
        d.text((540, 1130), c["chips"][0], font=S.F("bold", 84), fill=S.TXT + (int(250 * note),), anchor="mm")
        d.text((540, 1210), "LICENCE  ·  ON  THE  REPO", font=S.F("mono", 24),
               fill=S.MUTED + (int(235 * note),), anchor="mm")
        bw2 = int(760 * S.ease(S.seg(local, 2.6, 1.0)))
        S.rr(d, [160, 1270, 920, 1284], 8, fill=(255, 255, 255, 24))
        S.rr(d, [160, 1270, 160 + bw2, 1284], 8, fill=S.CYAN + (int(210 * note),))
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
    if not argv or "--list" in argv:
        print(__doc__)
        for slug, c in CLIPS.items():
            print(f"  {slug:4} {c['out']}.mp4   +{c['gained']:,} this week  #{c['rank']}")
        return 0
    if "--render" in argv:
        rest = [a for a in argv[argv.index("--render") + 1:] if not a.startswith("-")]
        wanted = rest or list(CLIPS)
        bad = 0
        for slug in wanted:
            if slug not in CLIPS:
                sys.exit(f"unknown clip {slug}")
            if len(wanted) > 1:
                os.environ.pop("OUT_NAME", None)  # one OUT_NAME cannot name two files
            bad |= S.encode(slug) != 0
        return 1 if bad else 0
    if "--scored" in argv:
        import build_audio
        bad = 0
        for slug, c in CLIPS.items():
            master = f"{c['out']}.mp4"
            if not os.path.exists(master):
                sys.exit(f"{master} missing — run --render first")
            bad |= build_audio.mux(master, score_slug(slug), f"{c['out']}_scored.mp4") != 0
        return 1 if bad else 0
    if "--tiktok" in argv:
        import build_audio
        bad = 0
        for slug, c in CLIPS.items():
            silent = os.path.join("build", f"{c['out']}_tiktok.mp4")
            env = dict(os.environ, OUT_NAME=silent)
            rc = subprocess.run([sys.executable, "render_aiagents_1117.py", "--render", slug], env=env).returncode
            print(f"[{slug}] tiktok render exit {rc} at MarginV {S.SUB_MV}", flush=True)
            bad |= rc
            if rc == 0:
                bad |= build_audio.mux(silent, score_slug(slug), f"{c['out']}_tiktok_scored.mp4") != 0
        return 1 if bad else 0
    print(__doc__)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
