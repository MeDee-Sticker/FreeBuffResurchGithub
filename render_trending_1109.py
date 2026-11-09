"""Render the 2026-11-09 GitHub Trending series: five 22 s vertical clips, one per repo.

Same visual system and 22 s beat sheet as the rest of the series (render_t3code_promo.py provides
the look, build_audio.py the score), so the clips drop into the existing Reels/TikTok slots.
Copy is data-driven: add a spec to CLIPS and the clip grows its own scenes and captions.

Facts come from the snapshot in data/trending_2026-11-09_daily.json plus each repo's live metadata
on 2026-11-09. On-screen numbers are stars gained today and the daily rank; total stars are never
shown, per the series rule.

Usage:
  python render_trending_1109.py --list
  python render_trending_1109.py --render              # all five silent masters
  python render_trending_1109.py --render sherlock     # named clip(s)
  python render_trending_1109.py --stills sherlock 1.5,5.2,11.0
"""
import os
import subprocess
import sys

from PIL import Image, ImageChops, ImageDraw, ImageFilter

import render_t3code_promo as base

W, H, FPS, DUR = 1080, 1920, 30, 22.0
BUILD = "build"
CAP_FONT = os.environ.get("PROMO_CAPTION_FONT") or ("Leelawadee UI" if os.name == "nt" else "Tahoma")
# Page logo, top-left of every frame. Swap the file or set PAGE_LOGO to use another mark.
LOGO_PATH = os.environ.get("PAGE_LOGO") or os.path.join("assets", "logo.png")
LOGO_H = int(os.environ.get("PAGE_LOGO_HEIGHT") or 96)
LOGO_PAD = int(os.environ.get("PAGE_LOGO_PAD") or 60)
ensure_fontconfig = base.ensure_fontconfig

F = base.F
clamp, ease, lerp, seg = base.clamp, base.ease, base.lerp, base.seg
rr, term_card, paste_glow = base.rr, base.term_card, base.paste_glow
BG = base.BG
PANEL, TXT, MUTED = base.PANEL, base.TXT, base.MUTED
CYAN, VIOLET, GREEN, RED, AMBER = base.CYAN, base.VIOLET, base.GREEN, base.RED, base.AMBER

CLIPS = {
    "sherlock": {
        "out": "sherlock_promo_22s",
        "monogram": "SH",
        "accent": CYAN,
        "glow": base.GLOW_CYAN,
        "rank": 1,
        "gained": 2373,
        "chips": ["MIT", "PYTHON", "SINCE 2018"],
        "term_title": "~/sherlock  run",
        "term": [
            ("cmd", "> sherlock @handle"),
            ("dim", "  checking 400+ sites"),
            ("ok", "  github  reddit  instagram"),
            ("ok", "  37 accounts found"),
        ],
        "steps": [
            ("username", "400+ social networks, one lookup", CYAN),
            ("crawl", "no browser tabs, one process", VIOLET),
            ("report", "machine-readable output", GREEN),
        ],
        "payoff_title": "~/sherlock  report",
        "payoff": [
            ("ok", "  37 accounts  ·  9 platforms"),
            ("dim", "  export, then keep going"),
            ("ok", "  MIT  ·  Python  ·  active since 2018"),
        ],
        "head": [
            (0.5, 2.9, "หนึ่งชื่อ หลายบัญชี", 94, 540),
            (3.15, 8.9, "400+ เครือข่าย", 84, 486),
            (9.3, 14.9, "ตัวเก่าที่ยังแรง", 86, 500),
            (19.4, 21.8, "sherlockproject.xyz", 76, 460),
        ],
        "subs": [
            (0.6, 2.9, "ชื่อผู้ใช้เดียว ไปโผล่ที่ไหนได้บ้าง"),
            (3.4, 6.1, "sherlock ไล่เช็ก 400+ เครือข่ายสังคม"),
            (6.1, 8.9, "จบในครั้งเดียว ไม่ต้องเปิดทีละแท็บ"),
            (9.4, 12.6, "ผลออกมาเป็นลิสต์ เอาไปทำรายงานต่อได้"),
            (12.6, 14.9, "repo ปี 2018 ที่ยังมี commit อยู่ทุกวันนี้"),
            (15.4, 18.9, "วันนี้ +2,373 ดาว อันดับ 1 ของ trending"),
            (19.5, 21.8, "ใช้กับงานที่ได้รับอนุญาตเท่านั้น · MIT"),
        ],
        "cmd": "pipx install sherlock-project",
    },
    "mausbot": {
        "out": "openmausbot_promo_22s",
        "monogram": "MB",
        "accent": VIOLET,
        "glow": base.GLOW_VIOLET,
        "rank": 2,
        "gained": 1439,
        "chips": ["APACHE-2.0", "TYPESCRIPT", "SELF-HOSTED"],
        "term_title": "~/mausbot  bots",
        "term": [
            ("cmd", "> maus-1  claude"),
            ("cmd", "> maus-2  codex"),
            ("dim", "  each bot: own VM, own apps"),
            ("ok", "  waiting for your approval"),
        ],
        "steps": [
            ("chat", "bots as contacts in the sidebar", CYAN),
            ("vm", "one machine per bot, running on its own", VIOLET),
            ("approve", "nothing touches files without a yes", GREEN),
        ],
        "payoff_title": "~/mausbot  settings",
        "payoff": [
            ("ok", "  local-first  ·  Claude or Codex"),
            ("dim", "  Windows  ·  macOS  ·  Ubuntu"),
            ("ok", "  your models, your machine"),
        ],
        "head": [
            (0.5, 2.9, "ทีมบอทในแอปแชท", 82, 540),
            (3.15, 8.9, "บอทละเครื่อง", 92, 486),
            (9.3, 14.9, "ไม่ต้องฝากงานไว้กับ cloud", 64, 500),
            (19.4, 21.8, "mausbot.com", 84, 460),
        ],
        "subs": [
            (0.6, 2.9, "Grok Bot แบบโอเพนซอร์ส ที่รันบนเครื่องคุณ"),
            (3.4, 6.1, "ทุกบอทในแถบข้างคือ agent ตัวจริง"),
            (6.1, 8.9, "Claude หรือ Codex ที่รันอยู่ข้างใน"),
            (9.4, 12.6, "บอทแต่ละตัวมี VM และแอปของตัวเอง"),
            (12.6, 14.9, "สั่งงานจากแชท อนุมัติจากแชท"),
            (15.4, 18.9, "วันนี้ +1,439 ดาว · สัปดาห์นี้ +7,621"),
            (19.5, 21.8, "Apache-2.0 · โคลนแล้ว build เองได้"),
        ],
        "cmd": "git clone github.com/milind-soni/OpenMausBot",
    },
    "astryx": {
        "out": "astryx_promo_22s",
        "monogram": "AX",
        "accent": GREEN,
        "glow": base.GLOW_CYAN,
        "rank": 3,
        "gained": 875,
        "chips": ["MIT", "REACT 19", "BETA"],
        "term_title": "~/app  design system",
        "term": [
            ("cmd", "> npm i @astryxdesign/core"),
            ("dim", "  tokens + components, one package"),
            ("ok", "  stylex compiled, no runtime cost"),
            ("ok", "  storybook ready"),
        ],
        "steps": [
            ("components", "React 19 + StyleX under the hood", CYAN),
            ("tokens", "customise the whole set, not one link", VIOLET),
            ("agents", "docs an agent can read and follow", GREEN),
        ],
        "payoff_title": "~/app  tokens.css",
        "payoff": [
            ("ok", "  one set of tokens, every component"),
            ("dim", "  no override wars between screens"),
            ("ok", "  same rules for people and agents"),
        ],
        "head": [
            (0.5, 2.9, "Design System สำหรับ agent", 70, 540),
            (3.15, 8.9, "ปรับได้ทั้งชุด", 88, 486),
            (9.3, 14.9, "จาก Meta · ตอนนี้ beta", 72, 500),
            (19.4, 21.8, "astryx.atmeta.com", 76, 460),
        ],
        "subs": [
            (0.6, 2.9, "design system ที่ไม่ได้ทำมาเพื่อคนอย่างเดียว"),
            (3.4, 6.1, "astryx สร้างบน React 19 กับ StyleX"),
            (6.1, 8.9, "โทเคนและ component ปรับได้ทั้งชุด"),
            (9.4, 12.6, "เอกสารกับ storybook เปิดให้ agent อ่าน"),
            (12.6, 14.9, "หน้าจอทีมไหน ก็ได้หน้าตาเดียวกัน"),
            (15.4, 18.9, "วันนี้ +875 ดาว อันดับ 3 ของ trending"),
            (19.5, 21.8, "MIT · ยังเป็น beta · astryx.atmeta.com"),
        ],
        "cmd": "npm i @astryxdesign/core",
    },
    "agentbr": {
        "out": "agent_browser_promo_22s",
        "monogram": "AB",
        "accent": AMBER,
        "glow": base.GLOW_VIOLET,
        "rank": 4,
        "gained": 815,
        "chips": ["APACHE-2.0", "RUST", "CLI"],
        "term_title": "~/tasks  browser",
        "term": [
            ("cmd", "> agent-browser snapshot"),
            ("ok", "  @e1 Sign in   @e2 Search"),
            ("cmd", "> agent-browser click @e1"),
            ("ok", "  navigated /dashboard"),
        ],
        "steps": [
            ("snapshot", "the page as compact text with refs", CYAN),
            ("act", "click, type, scroll one command at a time", VIOLET),
            ("rust", "one binary, no driver to babysit", GREEN),
        ],
        "payoff_title": "~/tasks  loop",
        "payoff": [
            ("cmd", "> agent-browser snapshot"),
            ("dim", "  read refs, decide, act, repeat"),
            ("ok", "  the agent stops guessing the DOM"),
        ],
        "head": [
            (0.5, 2.9, "เบราว์เซอร์ที่ agent สั่งได้", 66, 540),
            (3.15, 8.9, "หน้าจอเป็นข้อความ", 82, 486),
            (9.3, 14.9, "สั่งทีละคำสั่ง", 88, 500),
            (19.4, 21.8, "agent-browser.dev", 76, 460),
        ],
        "subs": [
            (0.6, 2.9, "ให้ agent คุมเบราว์เซอร์ ไม่ใช่เดา DOM"),
            (3.4, 6.1, "snapshot คืนหน้าเว็บเป็นข้อความสั้น ๆ"),
            (6.1, 8.9, "ทุก element มี ref ให้สั่งต่อได้ทันที"),
            (9.4, 12.6, "คลิก พิมพ์ เลื่อน จาก shell ทีละคำสั่ง"),
            (12.6, 14.9, "เขียนด้วย Rust · Apache-2.0 · จาก Vercel Labs"),
            (15.4, 18.9, "วันนี้ +815 ดาว · สัปดาห์นี้ +2,190"),
            (19.5, 21.8, "npm i -g agent-browser · agent-browser.dev"),
        ],
        "cmd": "npm i -g agent-browser",
    },
    "skills": {
        "out": "anthropics_skills_promo_22s",
        "monogram": "SK",
        "accent": (244, 114, 182),
        "glow": base.GLOW_CYAN,
        "rank": 5,
        "gained": 792,
        "chips": ["PYTHON", "AGENT SKILLS", "EXAMPLES"],
        "term_title": "~/.claude/skills",
        "term": [
            ("cmd", "> ls skills/"),
            ("dim", "  docs/  testing/  slides/  brand/"),
            ("ok", "  each: instructions + scripts"),
            ("ok", "  loaded only when a task needs it"),
        ],
        "steps": [
            ("folder", "instructions, scripts and resources", CYAN),
            ("on demand", "pulled in for the task, not every turn", VIOLET),
            ("repeatable", "the same job, the same way, again", GREEN),
        ],
        "payoff_title": "~/.claude/skills  docs",
        "payoff": [
            ("ok", "  creative, technical, enterprise examples"),
            ("dim", "  copy one folder, edit it, done"),
            ("ok", "  the standard lives at agentskills.io"),
        ],
        "head": [
            (0.5, 2.9, "โฟลเดอร์ที่สอนงาน agent", 68, 540),
            (3.15, 8.9, "โหลดตอนต้องใช้", 84, 486),
            (9.3, 14.9, "งานซ้ำ ทำให้เหมือนเดิม", 62, 500),
            (19.4, 21.8, "agentskills.io", 84, 460),
        ],
        "subs": [
            (0.6, 2.9, "สอน agent ทำงานเฉพาะทางด้วยโฟลเดอร์"),
            (3.4, 6.1, "skill = คำสั่ง + สคริปต์ + ไฟล์ประกอบ"),
            (6.1, 8.9, "Claude โหลดเฉพาะตอนที่งานต้องใช้"),
            (9.4, 12.6, "repo นี้รวมตัวอย่างตั้งแต่ศิลปะถึงงานองค์กร"),
            (12.6, 14.9, "ก็อปโฟลเดอร์ไปแก้ แล้วใช้ซ้ำได้เลย"),
            (15.4, 18.9, "วันนี้ +792 ดาว อันดับ 5 ของ trending"),
            (19.5, 21.8, "มาตรฐาน Agent Skills อยู่ที่ agentskills.io"),
        ],
        "cmd": "git clone github.com/anthropics/skills",
    },
}


# ---------------------------------------------------------------- scenes
def scene_hook(t, img, c):
    img = paste_glow(img, c["glow"], 540, 980, 0.82, 0.34 + 0.14 * base.math.sin(t * 2.4))
    img = term_card(img, [96, 720, 984, 1268], c["term_title"], c["term"], c["accent"],
                    reveal=ease(seg(t, 0.12, 1.2)), dim=0.72, lh=60, fs=28)
    d = ImageDraw.Draw(img, "RGBA")
    k = ease(seg(t, 2.15, 0.5))
    if k > 0:  # repo slug lands under the card so the hook names its subject
        rr(d, [96, 1300, 96 + int(360 * k), 1356], 18, fill=base.PANEL + (int(240 * k),),
           outline=c["accent"] + (int(120 * k),), width=2)
        d.text((126, 1328), "github  ·  " + c["out"].split("_promo")[0].replace("_", "-"),
               font=F("mono", 22), fill=MUTED + (int(240 * k),), anchor="lm")
    return img


def _step_card(img, box, title, sub, accent, k, idx):
    d = ImageDraw.Draw(img, "RGBA")
    x0, y0 = box[0], int(box[1] + (1 - k) * 70)
    x1, y1 = box[2], y0 + (box[3] - box[1])
    rr(d, [x0, y0, x1, y1], 26, fill=PANEL + (int(250 * k),),
       outline=accent + (int(120 * k),), width=2)
    d.rounded_rectangle([x0 + 18, y0 + 18, x0 + 26, y1 - 18], radius=4, fill=accent + (int(210 * k),))
    d.text((x0 + 52, y0 + 34), title, font=F("mono", 30), fill=accent + (int(245 * k),))
    d.text((x0 + 52, y0 + 92), sub, font=F("monoreg", 24), fill=TXT + (int(225 * k),))
    d.text((x1 - 52, y0 + 40), f"0{idx}", font=F("bold", 40),
           fill=(255, 255, 255, int(70 * k)), anchor="ra")
    return img


def scene_steps(t, img, c):
    local = t - 3.0
    img = paste_glow(img, c["glow"], 540, 980, 0.8, 0.34)
    y0, ch, gap = 620, 196, 84
    for i, (title, sub, col) in enumerate(c["steps"]):
        k = ease(seg(local, -0.12 + i * 0.32, 0.42))
        if k <= 0:
            continue
        box = [96, y0 + i * (ch + gap), 984, y0 + i * (ch + gap) + ch]
        img = _step_card(img, box, title, sub, col, k, i + 1)
        if i < 2:
            kk = ease(seg(local, 0.2 + i * 0.32, 0.36))
            if kk > 0:
                d = ImageDraw.Draw(img, "RGBA")
                cx, top = 540, box[3] + 14
                bot = top + int((gap - 28) * kk)
                d.line([(cx, top), (cx, bot)], fill=(255, 255, 255, int(50 * kk)), width=3)
                d.line([(cx - 13, bot - 16), (cx, bot - 2)], fill=MUTED + (int(200 * kk),), width=3)
                d.line([(cx + 13, bot - 16), (cx, bot - 2)], fill=MUTED + (int(200 * kk),), width=3)
    return img


def scene_payoff(t, img, c):
    local = t - 9.0
    img = paste_glow(img, c["glow"], 540, 1000, 0.85, 0.42)
    img = term_card(img, [96, 660, 984, 1210], c["payoff_title"], c["payoff"], c["accent"],
                    reveal=ease(seg(local, 0.15, 1.5)), dim=0.95, lh=62, fs=26)
    d = ImageDraw.Draw(img, "RGBA")
    x = 96
    for i, chip in enumerate(c["chips"]):
        k = ease(seg(local, 1.5 + i * 0.16, 0.4))
        if k <= 0:
            continue
        w = int(d.textlength(chip, font=F("mono", 24)) + 56)
        y = 1250 + int((1 - k) * 30)
        rr(d, [x, y, x + int(w * k), y + 62], 18, fill=PANEL + (int(245 * k),),
           outline=c["accent"] + (int(150 * k),), width=2)
        if k > 0.85:
            d.text((x + 28, y + 31), chip, font=F("mono", 24), fill=TXT + (240,), anchor="lm")
        x += w + 18
    return img


def scene_numbers(t, img, c):
    local = t - 15.0
    img = paste_glow(img, base.GLOW_CYAN, 540, 760, 0.9, 0.45)
    d = ImageDraw.Draw(img, "RGBA")
    v = int(c["gained"] * ease(seg(local, 0.15, 1.3)))
    d.text((540, 700), f"+{v:,}", font=F("bold", 176), fill=TXT + (255,), anchor="mm")
    d.text((540, 826), "STARS  TODAY", font=F("mono", 30), fill=CYAN + (235,), anchor="mm")
    badge = ease(seg(local, 1.7, 0.5))
    if badge > 0:
        bw = int(720 * badge)
        rr(d, [540 - bw // 2, 902, 540 + bw // 2, 994], 24, fill=(251, 191, 36, int(240 * badge)))
        if badge > 0.6:
            d.text((540, 948), f"#{c['rank']}  GITHUB  TRENDING  ·  TODAY", font=F("bold", 34),
                   fill=(26, 22, 10, 255), anchor="mm")
    note = ease(seg(local, 2.3, 0.6))
    if note > 0:
        d.text((540, 1130), c["chips"][0], font=F("bold", 84), fill=TXT + (int(250 * note),), anchor="mm")
        d.text((540, 1210), "LICENCE  ·  ON  THE  REPO", font=F("mono", 24),
               fill=MUTED + (int(235 * note),), anchor="mm")
        bw2 = int(760 * ease(seg(local, 2.6, 1.0)))
        rr(d, [160, 1270, 920, 1284], 8, fill=(255, 255, 255, 24))
        rr(d, [160, 1270, 160 + bw2, 1284], 8, fill=CYAN + (int(210 * note),))
    return img


def scene_cta(t, img, c):
    local = t - 19.0
    img = paste_glow(img, base.GLOW_CYAN, 540, 760, 0.9, 0.5 * (1 - seg(local, 2.4, 0.6)))
    d = ImageDraw.Draw(img, "RGBA")
    k = ease(seg(local, 0.0, 0.35))
    s = int(lerp(140, 176, k))
    rr(d, [540 - s // 2, 700 - s // 2, 540 + s // 2, 700 + s // 2], 46,
       fill=(12, 18, 28, 255), outline=c["accent"] + (210,), width=4)
    d.text((540, 700), c["monogram"], font=F("bold", int(s * 0.46)), fill=TXT + (255,), anchor="mm")
    cmd = c["cmd"]
    typed = cmd[: int(len(cmd) * ease(seg(local, 0.7, 1.1)))]
    box_y = 900
    rr(d, [90, box_y, 990, box_y + 132], 26, fill=PANEL + (250,), outline=(255, 255, 255, 30), width=2)
    d.text((128, box_y + 38), "$ " + typed, font=F("monoreg", 28), fill=TXT + (245,))
    if int(local * 3) % 2 == 0 and len(typed) < len(cmd):
        wpx = d.textlength("$ " + typed, font=F("monoreg", 28))
        d.rectangle([132 + wpx, box_y + 34, 136 + wpx, box_y + 74], fill=CYAN + (230,))
    fade = seg(local, 2.55, 0.45)
    if fade > 0:
        img.alpha_composite(Image.new("RGBA", (W, H), (0, 0, 0, int(255 * fade))))
    return img


SCENES = [(0.0, scene_hook), (3.0, scene_steps), (9.0, scene_payoff),
          (15.0, scene_numbers), (19.0, scene_cta)]


def load_logo():
    if not os.path.exists(LOGO_PATH):
        print(f"warning: {LOGO_PATH} not found - rendering without the page logo", flush=True)
        return None
    im = Image.open(LOGO_PATH).convert("RGBA")
    bb = im.getbbox()
    if bb:  # drop transparent padding so the mark sits on its optical edge
        im = im.crop(bb)
    w = max(1, round(im.width * LOGO_H / im.height))
    im = im.resize((w, LOGO_H), Image.LANCZOS)
    # soften the square avatar edge so it sits as a mark, not a tile
    mask = Image.new("L", im.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle(
        (0, 0, im.width - 1, im.height - 1), radius=max(6, im.width // 5), fill=255)
    im.putalpha(ImageChops.multiply(im.split()[3], mask))
    return im


LOGO = load_logo()
LOGO_XY = (LOGO_PAD, LOGO_PAD)


def paste_logo(img):
    """Composite the page mark top-left, with a soft shadow so light marks stay legible."""
    if LOGO is None:
        return img
    x, y = LOGO_XY
    shadow = Image.new("RGBA", LOGO.size, (0, 0, 0, 0))
    shadow.putalpha(LOGO.split()[3].filter(ImageFilter.GaussianBlur(9))
                    .point(lambda v: int(v * 0.6)))
    img.alpha_composite(shadow, (x + 3, y + 5))
    img.alpha_composite(LOGO, (x, y))
    return img


def render(t, c):
    fn = SCENES[0][1]
    for start, f in SCENES:
        if t >= start:
            fn = f
    return paste_logo(fn(t, BG.copy().convert("RGBA"), c)).convert("RGB")


# ---------------------------------------------------------------- ASS
def ts(x):
    h = int(x // 3600)
    m = int(x % 3600 // 60)
    s = x % 60
    return f"{h}:{m:02d}:{s:05.2f}"


ASS_HEAD = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Head,Leelawadee UI,96,&H00FFFFFF,&H00FFFFFF,&H00101820,&H96000000,-1,0,0,0,100,100,0,0,1,4,3,5,90,90,0,1
Style: Sub,Leelawadee UI,46,&H00FFFFFF,&H00FFFFFF,&H00000000,&H5A000000,-1,0,0,0,100,100,0,0,3,16,0,2,70,70,150,1
Style: SubSmall,Leelawadee UI,40,&H00FFFFFF,&H00FFFFFF,&H00000000,&H5A000000,-1,0,0,0,100,100,0,0,3,15,0,2,60,60,150,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
SUB_MV = os.environ.get("SUB_MARGIN_V", "150")
ASS_HEAD = ASS_HEAD.replace(",70,70,150,1", f",70,70,{SUB_MV},1")
ASS_HEAD = ASS_HEAD.replace(",60,60,150,1", f",60,60,{SUB_MV},1")
ASS_HEAD = ASS_HEAD.replace("Leelawadee UI", CAP_FONT)


def build_ass(slug, c):
    os.makedirs(BUILD, exist_ok=True)
    out = [ASS_HEAD]
    for start, end, text, size, y in c["head"]:
        out.append(
            f"Dialogue: 1,{ts(start)},{ts(end)},Head,,0,0,0,,"
            f"{{\\pos(540,{y})\\fs{size}\\fad(240,220)\\fscx88\\fscy88\\t(0,380,\\fscx100\\fscy100)}}{text}"
        )
    for start, end, text in c["subs"]:
        style = "Sub" if len(text) <= 52 else "SubSmall"
        out.append(f"Dialogue: 0,{ts(start)},{ts(end)},{style},,0,0,0,,{{\\fad(170,150)}}{text}")
    path = os.path.join(BUILD, f"captions_1109_{slug}.ass")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(out) + "\n")
    return path


# ---------------------------------------------------------------- outputs
def ffmpeg_cmd(dest, ass_name):
    ensure_fontconfig()
    ass = os.path.join(BUILD, ass_name).replace("\\", "/")
    fontsdir = ":fontsdir=fonts" if os.path.isdir("fonts") else ""
    return [
        base.FF, "-y", "-hide_banner", "-loglevel", "error",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
        "-f", "lavfi", "-i", "anullsrc=channel_layout=stereo:sample_rate=44100",
        "-vf", f"subtitles={ass}{fontsdir}",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
        "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "96k",
        "-shortest", "-movflags", "+faststart", dest,
    ]


def encode(slug):
    c = CLIPS[slug]
    dest = os.environ.get("OUT_NAME") or f"{c['out']}.mp4"
    os.makedirs(BUILD, exist_ok=True)
    ass_name = os.path.basename(build_ass(slug, c))
    proc = subprocess.Popen(ffmpeg_cmd(dest, ass_name), stdin=subprocess.PIPE)
    n = int(DUR * FPS)
    for i in range(n):
        proc.stdin.write(render(i / FPS, c).tobytes())
    proc.stdin.close()
    code = proc.wait()
    print(f"[{slug}] ffmpeg exit {code} -> {dest} ({n} frames)", flush=True)
    return code


def stills(slug, times):
    c = CLIPS[slug]
    os.makedirs(BUILD, exist_ok=True)
    for t in times:
        p = os.path.join(BUILD, f"still_1109_{slug}_{t:05.2f}.png")
        render(t, c).save(p)
        print("wrote", p)


def main(argv):
    if not argv or argv[0] in ("-h", "--help") or "--list" in argv:
        print(__doc__)
        for slug, c in CLIPS.items():
            print(f"  {slug:10} {c['out']}.mp4   +{c['gained']:,} today  #{c['rank']}")
        return 0
    if "--stills" in argv:
        slug = argv[argv.index("--stills") + 1]
        times = [float(x) for x in argv[argv.index("--stills") + 2].split(",")]
        if slug not in CLIPS:
            sys.exit(f"unknown clip {slug}")
        stills(slug, times)
        return 0
    if "--render" in argv:
        rest = argv[argv.index("--render") + 1:]
        wanted = [a for a in rest if not a.startswith("-")] or list(CLIPS)
        unknown = [w for w in wanted if w not in CLIPS]
        if unknown:
            sys.exit(f"unknown clip(s): {', '.join(unknown)} — pick from {', '.join(CLIPS)}")
        bad = 0
        for slug in wanted:
            if len(wanted) > 1:
                os.environ.pop("OUT_NAME", None)  # one OUT_NAME cannot name five files
            bad |= encode(slug) != 0
        return 1 if bad else 0
    print(__doc__)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
