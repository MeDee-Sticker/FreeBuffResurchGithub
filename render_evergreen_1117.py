"""Render the two evergreen reel clips for 17-18 Nov 2026 (Reels 19:00).

Same picture system and 22 s beat sheet as the 2026-11-09 series, but these clips carry no
star numbers: on the 15-19 s slot the series shows a numbers card, and here that slot is a
recap card instead. Copy follows next_batch_2026-11-17_to_21.md (the reel variants).

Usage:
  python render_evergreen_1117.py --render            # silent masters, both clips
  python render_evergreen_1117.py --scored            # scores + <clip>_scored.mp4
  python render_evergreen_1117.py --render mcp
"""
import os
import sys

import render_t3code_promo as base
import render_trending_1109 as S

W, H, FPS, DUR = S.W, S.H, S.FPS, S.DUR

CLIPS = {
    "mcp": {
        "out": "mcp_promo_22s",
        "monogram": "MC",
        "accent": S.VIOLET,
        "glow": base.GLOW_VIOLET,
        "chips": ["PROTOCOL", "SCHEMA", "PERMISSIONS"],
        "term_title": "~/agent  tools",
        "term": [
            ("cmd", "> tools/list"),
            ("dim", "  calendar  ·  mail  ·  db"),
            ("ok", "  each one publishes a schema"),
            ("ok", "  scope lives on the tool side"),
        ],
        "steps": [
            ("declare", "each tool says what it can do", S.CYAN),
            ("choose", "the agent picks one per task", S.VIOLET),
            ("contain", "approvals stay with the tool", S.GREEN),
        ],
        "payoff_title": "~/agent  task",
        "payoff": [
            ("cmd", '> "find a free slot next week"'),
            ("dim", "  calendar.read  →  mail.draft"),
            ("ok", "  one round trip, not five tabs"),
        ],
        "recap_title": "~/notes  mcp",
        "recap": [
            ("ok", "  start with the tool you open 10x a day"),
            ("dim", "  one integration at a time"),
            ("ok", "  read the schema before granting scope"),
        ],
        "head": [
            (0.5, 2.9, "agent เห็นแค่ไฟล์", 72, 540),
            (3.15, 8.9, "ไม่เห็นเครื่องมือ", 80, 486),
            (9.3, 14.9, "MCP คือสะพาน", 86, 500),
            (19.4, 21.8, "เริ่มจากเครื่องมือที่ใช้บ่อย", 54, 460),
        ],
        "subs": [
            (0.6, 2.9, "ทำไม agent เห็นแค่ไฟล์ ไม่เห็นปฏิทินหรืออีเมล"),
            (3.4, 6.1, "ไม่ใช่เพราะมันโง่ — มันขาดทางคุยกับเครื่องมือ"),
            (6.1, 8.9, "MCP ให้แต่ละเครื่องมือประกาศว่ามีอะไรให้เรียก"),
            (9.4, 12.6, "agent เห็นรายการนั้น แล้วเลือกเรียกตามงานที่เจอ"),
            (12.6, 14.9, "สิทธิ์อยู่ฝั่งเครื่องมือ ไม่ใช่ฝั่งโมเดล"),
            (15.4, 18.9, 'จาก "สรุปไฟล์นี้" เป็น "ดูตารางว่างแล้วร่างนัด"'),
            (19.5, 21.8, "เริ่มจากเครื่องมือที่คุณเปิดวันละ 10 รอบ 1 ตัว"),
        ],
        "cmd": "npx @modelcontextprotocol/inspector",
    },
    "prompt": {
        "out": "prompt_is_data_promo_22s",
        "monogram": "PR",
        "accent": S.AMBER,
        "glow": base.GLOW_CYAN,
        "chips": ["FORMAT", "LIMITS", "EXAMPLE"],
        "term_title": "~/prompts  brief.md",
        "term": [
            ("cmd", "> cat brief.md"),
            ("ok", "  output: 120 words, 3 bullets"),
            ("dim", "  never: hype words, invented numbers"),
            ("ok", "  good:  →  attached sample"),
        ],
        "steps": [
            ("format", "say what the answer looks like", S.CYAN),
            ("limits", "name what must never appear", S.VIOLET),
            ("example", "one good sample beats ten rules", S.GREEN),
        ],
        "payoff_title": "~/prompts  result",
        "payoff": [
            ("cmd", "> run brief.md"),
            ("dim", "  first draft is editable, not a rewrite"),
            ("ok", "  same input, same shape, next time"),
        ],
        "recap_title": "~/notes  prompt",
        "recap": [
            ("ok", "  format  ·  limits  ·  example  ·  test"),
            ("dim", "  long is not the same as clear"),
            ("ok", "  add data, not hope"),
        ],
        "head": [
            (0.5, 2.9, "prompt ยาวขึ้น", 84, 540),
            (3.15, 8.9, "ผลกลับแย่ลง", 88, 486),
            (9.3, 14.9, "ขาดข้อมูล ไม่ใช่ขาดคำ", 62, 500),
            (19.4, 21.8, "เพิ่มข้อมูล ไม่ใช่เพิ่มคำ", 60, 460),
        ],
        "subs": [
            (0.6, 2.9, "prompt ที่ยาวขึ้นไม่เคยแก้ปัญหาที่กำกวม"),
            (3.4, 6.1, "โมเดลไม่ได้อ่านใจ มันอ่านแค่ที่คุณเขียน"),
            (6.1, 8.9, "ไม่บอกหน้าตาผลลัพธ์ = มันเดาแทนคุณ"),
            (9.4, 12.6, "ไม่ให้ตัวอย่างที่ดี 1 ชิ้น = มันเดาโทนเอง"),
            (12.6, 14.9, 'ไม่บอกว่าอะไรคือ "ถูก" = ต้องแก้ทั้งชิ้น'),
            (15.4, 18.9, "ก่อนเพิ่มประโยค ถามว่า นี่ข้อมูลหรือความหวัง"),
            (19.5, 21.8, "รูปแบบ · ข้อห้าม · ตัวอย่าง · เกณฑ์ตัดสิน"),
        ],
        "cmd": "cat prompts/brief.md",
    },
}

S.CLIPS.update(CLIPS)


def scene_recap(t, img, c):
    """15-19 s slot: a plain recap card instead of the series numbers card."""
    local = t - 15.0
    img = S.paste_glow(img, c["glow"], 540, 950, 0.85, 0.40)
    return S.term_card(img, [96, 640, 984, 1240], c["recap_title"], c["recap"], c["accent"],
                       reveal=S.ease(S.seg(local, 0.15, 1.3)), dim=0.92, lh=64, fs=28)


S.SCENES = [(0.0, S.scene_hook), (3.0, S.scene_steps), (9.0, S.scene_payoff),
            (15.0, scene_recap), (19.0, S.scene_cta)]


def main(argv):
    if not argv or "--list" in argv:
        print(__doc__)
        for slug, c in CLIPS.items():
            print(f"  {slug:7} {c['out']}.mp4")
        return 0
    if "--render" in argv:
        wanted = [a for a in argv[argv.index("--render") + 1:] if not a.startswith("-")] or list(CLIPS)
        bad = 0
        for slug in wanted:
            if slug not in CLIPS:
                sys.exit(f"unknown clip {slug}")
            if len(wanted) > 1:
                os.environ.pop("OUT_NAME", None)
            bad |= S.encode(slug) != 0
        return 1 if bad else 0
    if "--scored" in argv:
        import build_audio
        bad = 0
        for slug, c in CLIPS.items():
            master = f"{c['out']}.mp4"
            if not os.path.exists(master):
                sys.exit(f"{master} missing — run --render first")
            path = os.path.join("build", f"score_{slug}.wav")
            if not os.path.exists(path):
                build_audio.build(slug, 22.0, 100, build_audio.IMP_CUTS, (0, 2), 8,
                                  ticks=(15.15, 16.45, 0.08), end_fade=(20.9, 22.0))
            bad |= build_audio.mux(master, path, f"{c['out']}_scored.mp4") != 0
        return 1 if bad else 0
    print(__doc__)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
