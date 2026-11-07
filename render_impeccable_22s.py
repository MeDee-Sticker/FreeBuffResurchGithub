"""Render the 22s vertical impeccable promo (trending #3) — same visual language as the series.

Scenes follow promo_scripts_rank2to5.md § อันดับ 3:
  0-3   four pages, four models, identical look
  3-9   /impeccable bolder pricing cards, then the words it gives the agent
  9-15  the 62-rule deterministic audit
  15-19 9,303 stars / #3, 4.0M downloads
  19-22 npx impeccable install

Shares the dark grid bg, mono type, term cards and ASS caption style with
render_t3code_promo.py, so the three clips cut together as one series.

Usage:
  python render_impeccable_22s.py --stills 1.0,6.5,12.0,17.0,20.6
  python render_impeccable_22s.py --render
"""
import math
import os
import subprocess
import sys

from PIL import Image, ImageDraw

import render_t3code_promo as base

W, H, FPS, DUR = 1080, 1920, 30, 22.0
OUT = "impeccable_promo_22s.mp4"
BUILD = "build"
ASS_NAME = "captions_imp.ass"

# The base module points at C:/Windows/Fonts and a Windows ffmpeg.exe. This series is also
# rendered on a Linux host, so prefer the bundled fonts/ dir and an explicit FFMPEG_BIN.
if os.path.isdir("fonts"):
    base.FONTS.update({
        "bold": "fonts/tahomabd.ttf",
        "reg": "fonts/tahoma.ttf",
        "mono": "fonts/consolab.ttf",
        "monoreg": "fonts/consola.ttf",
    })
FF = os.environ.get("FFMPEG_BIN") or base.FF
# Leelawadee UI ships only with Windows; fall back to the bundled Tahoma elsewhere
CAP_FONT = os.environ.get("PROMO_CAPTION_FONT") or ("Leelawadee UI" if os.name == "nt" else "Tahoma")


def ensure_fontconfig():
    """libass needs a fontconfig config to see fonts/; Linux hosts here ship without one."""
    if os.name == "nt" or os.environ.get("FONTCONFIG_FILE") or not os.path.isdir("fonts"):
        return
    os.makedirs(BUILD, exist_ok=True)
    p = os.path.abspath(os.path.join(BUILD, "fonts.conf"))
    if not os.path.exists(p):
        with open(p, "w", encoding="utf-8") as f:
            f.write('<?xml version="1.0"?>\n<!DOCTYPE fontconfig SYSTEM "fonts.dtd">\n'
                    f"<fontconfig><dir>{os.path.abspath('fonts')}</dir>"
                    "<cachedir>/tmp/fccache</cachedir></fontconfig>\n")
    os.environ["FONTCONFIG_FILE"] = p

F = base.F
clamp, ease, ease_io, lerp, seg = base.clamp, base.ease, base.ease_io, base.lerp, base.seg
rr, term_card, paste_glow = base.rr, base.term_card, base.paste_glow
BG = base.BG
PANEL, PANEL2, TXT, MUTED = base.PANEL, base.PANEL2, base.TXT, base.MUTED
CYAN, VIOLET, GREEN, RED, AMBER = base.CYAN, base.VIOLET, base.GREEN, base.RED, base.AMBER
GLOW_CYAN, GLOW_VIOLET = base.GLOW_CYAN, base.GLOW_VIOLET

# the violet -> blue hero every AI-generated page arrives with
SLOP_A, SLOP_B = (129, 140, 248), (59, 130, 246)

_GRAD, _MASK = {}, {}


def grad_strip(w, h):
    k = (w, h)
    if k not in _GRAD:
        g = Image.new("RGBA", (w, h))
        gd = ImageDraw.Draw(g)
        for y in range(h):
            p = y / max(1, h - 1)
            gd.line([(0, y), (w, y)], fill=tuple(int(lerp(a, b, p)) for a, b in zip(SLOP_A, SLOP_B)) + (255,))
        _GRAD[k] = g
    return _GRAD[k]


def rmask(w, h, r):
    k = (w, h, r)
    if k not in _MASK:
        m = Image.new("L", (w, h), 0)
        ImageDraw.Draw(m).rounded_rectangle([0, 0, w - 1, h - 1], radius=r, fill=255)
        _MASK[k] = m
    return _MASK[k]


# ---------------------------------------------------------------- scenes
def mini_page(img, box, k, label):
    """One of four pages that look exactly the same: gradient hero, eyebrow, nested cards, pill."""
    x0, y0, x1, y1 = box
    oy = int((1 - k) * 44)
    y0 += oy
    y1 += oy
    a = int(255 * k)
    d = ImageDraw.Draw(img, "RGBA")
    rr(d, [x0, y0, x1, y1], 24, fill=PANEL + (a,), outline=(255, 255, 255, int(30 * k)), width=2)

    hh = 62
    head = grad_strip(x1 - x0, hh + 24).copy()
    head.putalpha(rmask(x1 - x0, hh + 24, 24))
    head = head.crop((0, 0, x1 - x0, hh))
    if k < 1:
        head.putalpha(head.split()[3].point(lambda v: int(v * k)))
    img.alpha_composite(head, (x0, y0))

    d.text((x0 + 26, y0 + 84), "NEW FEATURE", font=F("mono", 15), fill=MUTED + (int(230 * k),))
    d.rounded_rectangle([x0 + 26, y0 + 112, x0 + 316, y0 + 138], radius=6, fill=TXT + (int(210 * k),))
    d.rounded_rectangle([x0 + 26, y0 + 148, x0 + 214, y0 + 168], radius=5, fill=TXT + (int(110 * k),))
    # card inside a card
    rr(d, [x0 + 26, y0 + 190, x1 - 26, y0 + 266], 16, fill=PANEL2 + (int(240 * k),),
       outline=(255, 255, 255, int(20 * k)), width=2)
    rr(d, [x0 + 44, y0 + 204, x1 - 44, y0 + 252], 12, fill=(10, 14, 22, int(250 * k)),
       outline=(255, 255, 255, int(14 * k)), width=1)
    # pill button
    rr(d, [x0 + 26, y0 + 292, x0 + 156, y0 + 326], 17, fill=SLOP_A + (int(235 * k),))
    d.text((x0 + 91, y0 + 309), "Get started", font=F("mono", 15), fill=(255, 255, 255, int(245 * k)),
           anchor="mm")
    d.text((x1 - 26, y1 - 20), label, font=F("mono", 16), fill=MUTED + (int(200 * k),), anchor="rd")
    return img


def scene_same(t, img):
    img = paste_glow(img, GLOW_VIOLET, 540, 980, 0.9, 0.30 + 0.10 * math.sin(t * 2.2))
    x0, y0, cw, ch, gap = 108, 620, 420, 360, 28
    for i, label in enumerate(("model-1", "model-2", "model-3", "model-4")):
        k = ease(seg(t, 0.05 + i * 0.09, 0.45))
        if k <= 0:
            continue
        cx = x0 + (i % 2) * (cw + gap)
        cy = y0 + (i // 2) * (ch + gap)
        mini_page(img, [cx, cy, cx + cw, cy + ch], k, label)
    k = ease(seg(t, 1.5, 0.5))
    if k > 0:
        d = ImageDraw.Draw(img, "RGBA")
        d.rectangle([108, 1374, 108 + int(864 * k), 1376], fill=AMBER + (int(190 * k),))
    cut = seg(t, 2.5, 0.4)
    if cut > 0:
        img.alpha_composite(Image.new("RGBA", (W, H), (0, 0, 0, int(255 * cut))))
    return img


def scene_words(t, img):
    local = t - 3.0
    img = paste_glow(img, GLOW_CYAN, 540, 980, 0.85, 0.36 + 0.06 * math.sin(t * 3.0))
    cmd = "> /impeccable bolder pricing cards"
    typed = cmd[: int(len(cmd) * ease(seg(local, 0.20, 1.9)))]
    lines = [("cmd", typed)]
    if typed == cmd:
        lines += [("dim", "  rewriting the pricing block"),
                  ("ok", "  done · 6 properties changed")]
    img = term_card(img, [96, 620, 984, 962], "~/acme-app  impeccable", lines, CYAN,
                    reveal=1.0, dim=0.95, lh=56, fs=28)
    d = ImageDraw.Draw(img, "RGBA")

    # the card actually changes: flat -> bolder
    a = int(255 * ease(seg(local, 0.55, 0.45)))
    if a > 0:
        k = ease(seg(local, 2.1, 1.0))
        wdt = int(lerp(600, 690, k))
        bx0, bx1 = 540 - wdt // 2, 540 + wdt // 2
        by0, by1 = 1012, 1312
        border = VIOLET if k > 0.15 else (255, 255, 255)
        rr(d, [bx0, by0, bx1, by1], 28, fill=PANEL + (a,), outline=border + (int(200 * a / 255),),
           width=3 if k > 0.15 else 2)
        d.text((bx0 + 40, by0 + 36), "STARTER", font=F("mono", 20), fill=MUTED + (a,))
        pr = int(lerp(56, 88, k))
        d.text((bx0 + 38, by0 + 74), "฿990", font=F("bold", pr),
               fill=(MUTED if k < 0.5 else TXT) + (a,))
        d.text((bx0 + 40, by0 + 196), "per seat / month", font=F("mono", 21), fill=MUTED + (a,))
        for i in range(3):
            yy = by0 + 240 + i * 22
            d.rounded_rectangle([bx0 + 40, yy, bx0 + 40 + int(lerp(150, 240, k)), yy + 10], radius=5,
                                fill=TXT + (int((60 + 40 * k) * a / 255),))
        if k > 0.55:
            q = int(220 * ease(seg(local, 2.6, 0.5)))
            rr(d, [bx1 - 250, by0 + 30, bx1 - 32, by0 + 78], 18, fill=AMBER + (q,))
            d.text((bx1 - 141, by0 + 54), "recommended", font=F("mono", 18),
                   fill=(26, 22, 10, q), anchor="mm")

    # the words the agent was missing
    chips = ["bolder", "polish", "critique", "audit"]
    fnt = F("mono", 24)
    wpx = [int(d.textlength(c, font=fnt)) + 56 for c in chips]
    x = 540 - (sum(wpx) + 18 * (len(chips) - 1)) // 2
    for i, c in enumerate(chips):
        kk = ease(seg(local, 3.3 + i * 0.16, 0.4))
        if kk <= 0:
            x += wpx[i] + 18
            continue
        col = [CYAN, VIOLET, GREEN, AMBER][i]
        rr(d, [x, 1352, x + wpx[i], 1408], 26, fill=PANEL + (int(250 * kk),),
           outline=col + (int(180 * kk),), width=2)
        d.text((x + wpx[i] // 2, 1380), c, font=fnt, fill=col + (int(245 * kk),), anchor="mm")
        x += wpx[i] + 18
    return img


RULES = [
    "color: gradient text on white",
    "layout: card inside a card",
    "type: eyebrow above every heading",
    "color: violet → blue hero",
    "layout: three equal feature columns",
    "motion: parallax on every section",
    "button: pill with outer glow",
    "content: emoji as section icons",
    "layout: everything centered",
    "a11y: focus state missing",
]


def scene_rules(t, img):
    local = t - 9.0
    img = paste_glow(img, GLOW_CYAN, 540, 950, 0.9, 0.38)
    d = ImageDraw.Draw(img, "RGBA")
    rr(d, [96, 594, 984, 1352], 26, fill=PANEL + (250,), outline=(255, 255, 255, 26), width=2)
    d.text((128, 620), "impeccable audit src/", font=F("mono", 22), fill=MUTED + (240,))
    n = int(62 * ease(seg(local, 0.3, 2.6)))
    d.text((952, 614), f"{n} / 62", font=F("bold", 32), fill=CYAN + (245,), anchor="ra")

    y = 700
    for i, name in enumerate(RULES):
        k = ease(seg(local, 0.35 + i * 0.20, 0.4))
        if k <= 0:
            break
        d.rounded_rectangle([128, y, 156, y + 28], radius=8, fill=(255, 255, 255, int(16 * k)),
                            outline=GREEN + (int(120 * k),), width=2)
        if k > 0.7:
            d.line([(133, y + 15), (141, y + 23), (152, y + 6)], fill=GREEN + (int(245 * k),), width=3)
        d.text((178, y + 14), name, font=F("mono", 23), fill=TXT + (int(240 * k),), anchor="lm")
        d.text((952, y + 14), f"R-{i + 1:02d}", font=F("mono", 18), fill=MUTED + (int(170 * k),),
               anchor="rm")
        y += 60

    f = ease(seg(local, 2.6, 0.6))
    if f > 0:
        d.text((540, 1396), "deterministic  ·  no LLM  ·  no API key", font=F("mono", 23),
               fill=CYAN + (int(235 * f),), anchor="mm")
    return img


def scene_numbers(t, img):
    local = t - 15.0
    img = paste_glow(img, GLOW_CYAN, 540, 760, 0.9, 0.45)
    d = ImageDraw.Draw(img, "RGBA")
    v = int(9303 * ease(seg(local, 0.15, 1.3)))
    d.text((540, 700), f"{v:,}", font=F("bold", 190), fill=TXT + (255,), anchor="mm")
    d.text((540, 826), "STARS  THIS  WEEK", font=F("mono", 30), fill=CYAN + (235,), anchor="mm")
    badge = ease(seg(local, 1.6, 0.5))
    if badge > 0:
        bw = int(660 * badge)
        rr(d, [540 - bw // 2, 902, 540 + bw // 2, 994], 24, fill=AMBER + (int(240 * badge),))
        if badge > 0.6:
            d.text((540, 948), "#3  GITHUB  TRENDING", font=F("bold", 36), fill=(26, 22, 10, 255),
                   anchor="mm")
    tot = ease(seg(local, 1.6, 0.6))
    if tot > 0:
        d.text((540, 1140), "4.0M", font=F("bold", 112), fill=TXT + (int(250 * tot),), anchor="mm")
        d.text((540, 1222), "RELEASE  DOWNLOADS", font=F("mono", 26), fill=MUTED + (int(235 * tot),),
               anchor="mm")
        d.text((540, 1272), "4,015,705 total  ·  Apache-2.0  ·  Rust", font=F("mono", 21),
               fill=MUTED + (int(200 * tot),), anchor="mm")
    return img


def scene_cta(t, img):
    local = t - 19.0
    img = paste_glow(img, GLOW_CYAN, 540, 760, 0.9, 0.5 * (1 - seg(local, 2.4, 0.6)))
    d = ImageDraw.Draw(img, "RGBA")
    k = ease(seg(local, 0.0, 0.35))
    s = int(lerp(140, 176, k))
    rr(d, [540 - s // 2, 700 - s // 2, 540 + s // 2, 700 + s // 2], 46,
       fill=(12, 18, 28, 255), outline=CYAN + (210,), width=4)
    d.text((540, 700), "IM", font=F("bold", int(s * 0.42)), fill=TXT + (255,), anchor="mm")
    cmd = "npx impeccable install"
    typed = cmd[: int(len(cmd) * ease(seg(local, 0.7, 1.1)))]
    box_y = 900
    rr(d, [90, box_y, 990, box_y + 132], 26, fill=PANEL + (250,), outline=(255, 255, 255, 30), width=2)
    d.text((128, box_y + 38), "$ " + typed, font=F("monoreg", 32), fill=TXT + (245,))
    if int(local * 3) % 2 == 0 and len(typed) < len(cmd):
        wpx = d.textlength("$ " + typed, font=F("monoreg", 32))
        d.rectangle([132 + wpx, box_y + 34, 136 + wpx, box_y + 74], fill=CYAN + (230,))
    q = ease(seg(local, 1.7, 0.6))
    if q > 0:
        d.text((540, 1110), "Apache-2.0  ·  Rust  ·  impeccable.style", font=F("mono", 22),
               fill=MUTED + (int(225 * q),), anchor="mm")
    fade = seg(local, 2.55, 0.45)
    if fade > 0:
        img.alpha_composite(Image.new("RGBA", (W, H), (0, 0, 0, int(255 * fade))))
    return img


SCENES = [
    (0.0, scene_same),
    (3.0, scene_words),
    (9.0, scene_rules),
    (15.0, scene_numbers),
    (19.0, scene_cta),
]


def render(t):
    fn = SCENES[0][1]
    for start, f in SCENES:
        if t >= start:
            fn = f
    return fn(t, BG.copy().convert("RGBA")).convert("RGB")


# ---------------------------------------------------------------- ASS
def ts(x):
    h = int(x // 3600)
    m = int(x % 3600 // 60)
    s = x % 60
    return f"{h}:{m:02d}:{s:05.2f}"


HEAD = [
    (0.5, 2.9, "หน้าตาเดียวกัน", 96, 470),
    (3.15, 8.9, "คำที่ขาดหายไป", 78, 470),
    (9.3, 14.9, "62 กฎ", 110, 470),
    (19.4, 21.8, "impeccable.style", 96, 450),
]

SUBS = [
    (0.6, 2.9, "ทำไมหน้าเว็บที่ AI สร้าง ถึงดูเป็น AI สร้าง"),
    (3.4, 6.1, "impeccable ให้คำกับ agent ที่มันขาด"),
    (6.1, 8.9, "bolder · polish · critique · audit"),
    (9.4, 12.6, "ตัวตรวจ 62 กฎ ไม่ต้องเรียกโมเดล"),
    (12.6, 14.9, "ไม่ใช้ LLM ไม่ต้องใช้ API key"),
    (15.4, 18.9, "สัปดาห์เดียว 9,303 ดาว ดาวน์โหลด 4 ล้านครั้ง"),
    (19.5, 21.8, "ติดตั้งบรรทัดเดียวที่ impeccable.style"),
]

ASS = """[Script Info]
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
ASS = ASS.replace("Leelawadee UI", CAP_FONT)


def build_ass():
    os.makedirs(BUILD, exist_ok=True)
    out = [ASS]
    for start, end, text, size, y in HEAD:
        out.append(
            f"Dialogue: 1,{ts(start)},{ts(end)},Head,,0,0,0,,"
            f"{{\\pos(540,{y})\\fs{size}\\fad(240,220)\\fscx88\\fscy88\\t(0,380,\\fscx100\\fscy100)}}{text}"
        )
    for start, end, text in SUBS:
        style = "Sub" if len(text) <= 52 else "SubSmall"
        out.append(f"Dialogue: 0,{ts(start)},{ts(end)},{style},,0,0,0,,{{\\fad(170,150)}}{text}")
    path = os.path.join(BUILD, ASS_NAME)
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(out) + "\n")
    return path


# ---------------------------------------------------------------- outputs
def ffmpeg_cmd(dest):
    ensure_fontconfig()
    ass = os.path.join(BUILD, ASS_NAME).replace("\\", "/")
    fontsdir = ":fontsdir=fonts" if os.path.isdir("fonts") else ""
    return [
        FF, "-y", "-hide_banner", "-loglevel", "error",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
        "-f", "lavfi", "-i", "anullsrc=channel_layout=stereo:sample_rate=44100",
        "-vf", f"subtitles={ass}{fontsdir}",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
        "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "96k",
        "-shortest", "-movflags", "+faststart", dest,
    ]


def encode(dest, t0=0.0, t1=DUR):
    os.makedirs(BUILD, exist_ok=True)
    build_ass()
    proc = subprocess.Popen(ffmpeg_cmd(dest), stdin=subprocess.PIPE)
    n = int((t1 - t0) * FPS)
    for i in range(n):
        proc.stdin.write(render(t0 + i / FPS).tobytes())
    proc.stdin.close()
    code = proc.wait()
    print("ffmpeg exit", code, "->", dest, f"({n} frames, {t1 - t0:.2f}s)")
    return code


def stills(times):
    os.makedirs(BUILD, exist_ok=True)
    build_ass()
    for t in times:
        p = os.path.join(BUILD, f"imp_still_{t:05.2f}.png")
        render(t).save(p)
        print("wrote", p)


if __name__ == "__main__":
    args = sys.argv[1:]
    if "--stills" in args:
        stills([float(x) for x in args[args.index("--stills") + 1].split(",")])
    elif "--render" in args:
        encode(OUT)
    else:
        print(__doc__)
