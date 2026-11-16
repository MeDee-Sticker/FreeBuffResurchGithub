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

EXTRA = {
    "three": {
        "out": "one_clip_three_assets_promo_22s",
        "monogram": "3X",
        "accent": S.CYAN,
        "glow": base.GLOW_CYAN,
        "chips": ["REPURPOSE", "15 MIN", "NO RESHOOT"],
        "term_title": "~/clip  exports",
        "term": [
            ("cmd", "> clip.mov  →  3 assets"),
            ("ok", "  hook.mp4    15s"),
            ("ok", "  post.md     transcript"),
            ("dim", "  frames/3    carousel"),
        ],
        "steps": [
            ("hook", "the 15 s people actually finish", S.CYAN),
            ("text", "transcript becomes the long post", S.VIOLET),
            ("frames", "three stills make a how-to carousel", S.GREEN),
        ],
        "payoff_title": "~/clip  rules",
        "payoff": [
            ("ok", "  pick only what needs no reshoot"),
            ("dim", "  one idea, three doors in"),
            ("ok", "  fifteen minutes, not three shoots"),
        ],
        "recap_title": "~/notes  repurpose",
        "recap": [
            ("ok", "  hook  ·  transcript  ·  stills"),
            ("dim", "  same clip, three entry points"),
            ("ok", "  stop paying for the same idea twice"),
        ],
        "head": [
            (0.5, 2.9, "คลิปเดียว จบ?", 80, 540),
            (3.15, 8.9, "จ่ายไอเดีย 3 รอบ", 78, 486),
            (9.3, 14.9, "สินค้า 3 ชิ้น", 88, 500),
            (19.4, 21.8, "15 นาทีก็พอ", 76, 460),
        ],
        "subs": [
            (0.6, 2.9, "ถ่ายคลิปเดียวแล้วจบ = จ่ายค่าไอเดียแพงกว่าคนอื่น"),
            (3.4, 6.1, "คลิปที่ดีไม่ควรจบที่ปุ่มโพสต์"),
            (6.1, 8.9, "ตัด 15 วิที่คนดูจบมากสุด เป็น hook คลิปหน้า"),
            (9.4, 12.6, "ถอดเสียงเป็นข้อความ ได้โพสต์ยาวทั้งอัน"),
            (12.6, 14.9, "จับภาพนิ่ง 3 เฟรม ได้ carousel สอนทีละขั้น"),
            (15.4, 18.9, "เกณฑ์เดียว: ทำได้โดยไม่ต้องถ่ายใหม่"),
            (19.5, 21.8, "หนึ่งไอเดีย สามทางเข้า"),
        ],
        "cmd": "ffmpeg -ss 0 -t 15 -i clip.mov hook.mp4",
    },
    "price": {
        "out": "digital_pricing_promo_22s",
        "monogram": "฿",
        "accent": S.AMBER,
        "glow": base.GLOW_VIOLET,
        "chips": ["OUTCOME", "TIME SAVED", "3 TIERS"],
        "term_title": "~/pricing  sheet",
        "term": [
            ("cmd", "> price --by outcome"),
            ("ok", "  saves 5 h  →  their hourly rate"),
            ("dim", "  low price, low expectation"),
            ("ok", "  start  ·  full  ·  ongoing"),
        ],
        "steps": [
            ("outcome", "price what they get back", S.CYAN),
            ("time", "price the hours you remove", S.VIOLET),
            ("tiers", "let people choose their depth", S.GREEN),
        ],
        "payoff_title": "~/pricing  check",
        "payoff": [
            ("ok", "  99 x 100  vs  990 x 10"),
            ("dim", "  cheap buys more work, not less"),
            ("ok", "  refunds rise when the price whispers"),
        ],
        "recap_title": "~/notes  pricing",
        "recap": [
            ("ok", "  outcome  ·  hours  ·  tiers"),
            ("dim", "  fear is not a pricing method"),
            ("ok", "  raise it before chasing more buyers"),
        ],
        "head": [
            (0.5, 2.9, "ตั้ง 99 บาท", 86, 540),
            (3.15, 8.9, "ต้องขาย 100 คน", 72, 486),
            (9.3, 14.9, "ราคาไม่ใช่ความกลัว", 62, 500),
            (19.4, 21.8, "คิดจากผลลัพธ์", 76, 460),
        ],
        "subs": [
            (0.6, 2.9, "ตั้งราคาถูกไม่ได้ทำให้ขายง่ายขึ้น"),
            (3.4, 6.1, "แค่ทำให้คุณต้องขายให้มากขึ้น"),
            (6.1, 8.9, "คิดจากผลลัพธ์ที่ลูกค้าได้กลับไป"),
            (9.4, 12.6, "คิดจากชั่วโมงที่คุณประหยัดให้เขา"),
            (12.6, 14.9, "แบ่ง 3 ชั้น ให้เลือกตามกำลัง"),
            (15.4, 18.9, "ราคาต่ำ = คาดหวังน้อย แต่ขอคืนเงินง่าย"),
            (19.5, 21.8, "ถ้าต้องขายเยอะ นั่นคือซื้อความเหนื่อย"),
        ],
        "cmd": "cat pricing.md",
    },
    "audit": {
        "out": "ai_review_3min_promo_22s",
        "monogram": "QA",
        "accent": S.RED,
        "glow": base.GLOW_VIOLET,
        "chips": ["NUMBERS", "LINKS", "VOICE"],
        "term_title": "~/deliver  checklist",
        "term": [
            ("cmd", "> review --3min"),
            ("ok", "  numbers  ·  names  ·  dates"),
            ("ok", "  links clicked, images zoomed"),
            ("dim", "  read it aloud, last"),
        ],
        "steps": [
            ("facts", "numbers, names and dates first", S.CYAN),
            ("links", "open every one, not just the look", S.VIOLET),
            ("voice", "read it aloud — is it still you", S.GREEN),
        ],
        "payoff_title": "~/deliver  before send",
        "payoff": [
            ("ok", "  cut the line the model invented"),
            ("dim", "  fix the hands, the logo, the type"),
            ("ok", "  three minutes, one page, every job"),
        ],
        "recap_title": "~/notes  review",
        "recap": [
            ("ok", "  facts  ·  links  ·  images  ·  tone"),
            ("dim", "  fast is not the same as correct"),
            ("ok", "  the checklist is the product"),
        ],
        "head": [
            (0.5, 2.9, "ลูกค้าไม่ได้เลิก", 70, 540),
            (3.15, 8.9, "เพราะคุณทำช้า", 76, 486),
            (9.3, 14.9, "เพราะไม่ได้ตรวจ", 76, 500),
            (19.4, 21.8, "3 นาทีก่อนกดส่ง", 72, 460),
        ],
        "subs": [
            (0.6, 2.9, "ลูกค้าไม่ได้เลิกจ้างเพราะคุณทำช้า"),
            (3.4, 6.1, "เขาเลิกเพราะคุณส่งงานที่ยังไม่ได้ตรวจ"),
            (6.1, 8.9, "AI ทำให้เร็วขึ้น ไม่ได้ทำให้ถูกขึ้น"),
            (9.4, 12.6, "เช็กตัวเลข วันที่ ชื่อเฉพาะ และกดลิงก์จริง"),
            (12.6, 14.9, "ดูภาพที่มือเพี้ยน ตัดประโยคที่โมเดลเติม"),
            (15.4, 18.9, "อ่านออกเสียง — ถ้าฟังไม่เหมือนคุณ ให้แก้"),
            (19.5, 21.8, "เช็กลิสต์ 1 หน้า ใช้ซ้ำได้ทุกงาน"),
        ],
        "cmd": "cat review-checklist.md",
    },
}

CLIPS.update(EXTRA)

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
        wanted = [a for a in argv[argv.index("--scored") + 1:] if not a.startswith("-")] or list(CLIPS)
        for slug in wanted:
            c = CLIPS[slug]
            master = f"{c['out']}.mp4"
            if not os.path.exists(master):
                sys.exit(f"{master} missing — run --render first")
            path = os.path.join("build", f"score_{slug}.wav")
            if not os.path.exists(path):
                build_audio.build(slug, 22.0, 100, build_audio.IMP_CUTS, (0, 2), 8,
                                  ticks=(15.15, 16.45, 0.08), end_fade=(20.9, 22.0))
            bad |= build_audio.mux(master, path, f"{c['out']}_scored.mp4") != 0
        return 1 if bad else 0
    if "--tiktok" in argv:
        import subprocess
        import build_audio
        bad = 0
        wanted = [a for a in argv[argv.index("--tiktok") + 1:] if not a.startswith("-")] or list(CLIPS)
        for slug in wanted:
            c = CLIPS[slug]
            silent = os.path.join("build", f"{c['out']}_tiktok.mp4")
            env = dict(os.environ, OUT_NAME=silent, SUB_MARGIN_V=os.environ.get("SUB_MARGIN_V", "260"))
            rc = subprocess.run([sys.executable, "render_evergreen_1117.py", "--render", slug], env=env).returncode
            print(f"[{slug}] tiktok render exit {rc} at MarginV {env['SUB_MARGIN_V']}", flush=True)
            bad |= rc
            if rc == 0:
                score = os.path.join("build", f"score_{slug}.wav")
                if not os.path.exists(score):
                    build_audio.build(slug, 22.0, 100, build_audio.IMP_CUTS, (0, 2), 8,
                                      ticks=(15.15, 16.45, 0.08), end_fade=(20.9, 22.0))
                bad |= build_audio.mux(silent, score, f"{c['out']}_tiktok_scored.mp4") != 0
        return 1 if bad else 0

    print(__doc__)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
