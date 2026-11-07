"""Render the 22s vertical Scrapling promo (trending #4) — same series look as #2 and #3.

Scenes follow promo_scripts_rank2to5.md § อันดับ 4:
  0-3   the page layout shifts and the scraper returns 0 rows
  3-9   adaptive element tracking finds the element again by similarity
  9-15  the agent calls it over MCP and gets a markdown table back
  15-19 7,487 stars this week, 98,721 total
  19-22 pip install scrapling

Shares BG, term cards, mono type and the ASS caption style with
render_t3code_promo.py so the clips cut together as one series.

Usage:
  python render_scrapling_22s.py --stills 1.5,5.0,12.0,17.0,20.6
  python render_scrapling_22s.py --render
"""
import math
import os
import subprocess
import sys

from PIL import Image, ImageDraw

import render_t3code_promo as base

W, H, FPS, DUR = 1080, 1920, 30, 22.0
OUT = "scrapling_promo_22s.mp4"
BUILD = "build"
ASS_NAME = "captions_scr.ass"

if os.path.isdir("fonts"):
    base.FONTS.update({
        "bold": "fonts/tahomabd.ttf",
        "reg": "fonts/tahoma.ttf",
        "mono": "fonts/consolab.ttf",
        "monoreg": "fonts/consola.ttf",
    })
FF = os.environ.get("FFMPEG_BIN") or base.FF
CAP_FONT = os.environ.get("PROMO_CAPTION_FONT") or ("Leelawadee UI" if os.name == "nt" else "Tahoma")

F = base.F
clamp, ease, ease_io, lerp, seg = base.clamp, base.ease, base.ease_io, base.lerp, base.seg
rr, term_card, paste_glow = base.rr, base.term_card, base.paste_glow
BG = base.BG
PANEL, PANEL2, TXT, MUTED = base.PANEL, base.PANEL2, base.TXT, base.MUTED
CYAN, VIOLET, GREEN, RED, AMBER = base.CYAN, base.VIOLET, base.GREEN, base.RED, base.AMBER
GLOW_CYAN, GLOW_VIOLET = base.GLOW_CYAN, base.GLOW_VIOLET
GLOW_RED = base.glow(900, RED, 160)
GLOW_GREEN = base.glow(900, GREEN, 160)


def ensure_fontconfig():
    """libass needs a fontconfig config to see fonts/; this Linux host ships without one."""
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


# ---------------------------------------------------------------- pieces
def browser_card(img, box, url, k=1.0, accent=None):
    d = ImageDraw.Draw(img, "RGBA")
    a = int(255 * k)
    x0, y0, x1, y1 = box
    rr(d, box, 24, fill=PANEL + (a,), outline=(255, 255, 255, int(28 * k)), width=2)
    d.line([(x0 + 2, y0 + 62), (x1 - 2, y0 + 62)], fill=(255, 255, 255, int(24 * k)), width=2)
    for i, c in enumerate([(248, 113, 113), (251, 191, 36), (52, 211, 153)]):
        d.ellipse([x0 + 22 + i * 24, y0 + 24, x0 + 36 + i * 24, y0 + 38],
                  fill=c + (int(230 * k),))
    d.text((x0 + 112, y0 + 21), url, font=F("mono", 22), fill=MUTED + (int(240 * k),))
    return img


def tile(d, x, y, w, h, a, accent=CYAN):
    rr(d, [x, y, x + w, y + h], 14, fill=PANEL2 + (a,), outline=(255, 255, 255, int(18 * a / 255)),
       width=2)
    d.rounded_rectangle([x + 14, y + 14, x + w - 14, y + 74], radius=8,
                        fill=(255, 255, 255, int(14 * a / 255)))
    d.rounded_rectangle([x + 14, y + 88, x + w - 46, y + 100], radius=4, fill=TXT + (int(120 * a / 255),))
    d.rounded_rectangle([x + 14, y + 110, x + 14 + 72, y + 122], radius=4, fill=accent + (int(210 * a / 255),))


def dashed(d, box, colour, width=3, dash=14, gap=9):
    x0, y0, x1, y1 = box
    for xs, ys, xe, ye in ((x0, y0, x1, y0), (x1, y0, x1, y1), (x1, y1, x0, y1), (x0, y1, x0, y0)):
        L = max(1, int(math.hypot(xe - xs, ye - ys)))
        for i in range(L // (dash + gap) + 1):
            a = i * (dash + gap) / L
            b = min(1.0, (i * (dash + gap) + dash) / L)
            d.line([(xs + (xe - xs) * a, ys + (ye - ys) * a),
                    (xs + (xe - xs) * b, ys + (ye - ys) * b)], fill=colour, width=width)


TILE_W, TILE_H, GAP = 250, 150, 26
COL_X = [136, 136 + TILE_W + GAP, 136 + 2 * (TILE_W + GAP)]
ROW_Y = [740, 740 + TILE_H + GAP]
SLOT = [(COL_X[i % 3], ROW_Y[i // 3]) for i in range(6)]
TILE_ACC = [CYAN, VIOLET, GREEN, AMBER, (244, 114, 182), (56, 189, 248)]
# ORDER[i] = which card ends up in slot i. A permutation, so the reflow never overlaps.
ORDER_BREAK = [2, 0, 4, 1, 5, 3]
ORDER_TRACK = [0, 5, 2, 3, 4, 1]
ROW_DX = [12, -12]


# ---------------------------------------------------------------- scenes
def scene_break(t, img):
    img = paste_glow(img, GLOW_RED, 540, 980, 0.85, 0.18 + 0.22 * ease(seg(t, 0.9, 1.2)))
    img = browser_card(img, [96, 600, 984, 1250], "shop.example/collection", ease(seg(t, 0.0, 0.45)))
    d = ImageDraw.Draw(img, "RGBA")
    d.text((136, 682), "$ page.query_selector_all('.product-card .price')", font=F("mono", 20),
           fill=MUTED + (235,))
    k = ease_io(seg(t, 0.85, 0.8))
    for i in range(6):
        ax, ay = SLOT[i]
        bx, by = SLOT[ORDER_BREAK[i]]
        x = int(lerp(ax, bx, k)) + (ROW_DX[0] if i < 3 else ROW_DX[1])
        y = int(lerp(ay, by, k))
        tile(d, x, y, TILE_W, TILE_H, int(245 * ease(seg(t, 0.1 + i * 0.05, 0.4))), accent=TILE_ACC[i])

    # the layout moved and the selector missed everything
    e = ease(seg(t, 1.2, 0.5))
    if e > 0:
        d.line([(136, 705), (136 + int(560 * e), 705)], fill=RED + (int(220 * e),), width=3)
        d.rounded_rectangle([136, 1086, 136 + int(560 * e), 1090], radius=2,
                            fill=RED + (int(120 * e),))
        rr(d, [136, 1104, 944, 1216], 18, fill=(38, 12, 14, int(240 * e)), outline=RED + (int(190 * e),),
           width=2)
        d.text((168, 1160), "0 rows found", font=F("mono", 40), fill=RED + (int(250 * e),), anchor="lm")
        d.text((944 - 24, 1160), "expected 1,248", font=F("mono", 22), fill=MUTED + (int(220 * e),),
               anchor="rm")
    cut = seg(t, 2.5, 0.4)
    if cut > 0:
        img.alpha_composite(Image.new("RGBA", (W, H), (0, 0, 0, int(255 * cut))))
    return img


def scene_track(t, img):
    local = t - 3.0
    img = paste_glow(img, GLOW_GREEN, 540, 980, 0.85, 0.16 + 0.22 * ease(seg(local, 0.6, 1.4)))
    img = browser_card(img, [96, 600, 984, 1250], "shop.example/collection", 1.0)
    d = ImageDraw.Draw(img, "RGBA")
    d.text((136, 682), "$ page.query_selector_all('.product-card .price')", font=F("mono", 20),
           fill=MUTED + (200,))
    for i in range(6):
        cx, cy = SLOT[i]
        cx += ROW_DX[0] if i < 3 else ROW_DX[1]
        tile(d, cx, cy, TILE_W, TILE_H, 245, accent=TILE_ACC[ORDER_TRACK[i]])

    # card 1 reflowed from slot 1 to slot 5, so its old cell is a ghost
    ox, oy = SLOT[1][0] + ROW_DX[0], SLOT[1][1]
    nx, ny = SLOT[5][0] + ROW_DX[1], SLOT[5][1]
    g = ease(seg(local, 0.5, 0.4))
    if g > 0:
        dashed(d, [ox, oy, ox + TILE_W, oy + TILE_H], (255, 255, 255, int(90 * g)), width=2, dash=12, gap=10)
        d.text((ox + 4, oy - 26), "old path", font=F("mono", 19), fill=MUTED + (int(210 * g),))

    m = ease_io(seg(local, 1.3, 1.5))
    if m > 0:
        bx = int(lerp(ox, nx, m))
        by = int(lerp(oy, ny, m))
        rr(d, [bx - 8, by - 8, bx + TILE_W + 8, by + TILE_H + 8], 18, fill=None,
           outline=GREEN + (245,), width=4)

    # similarity meter
    q = ease(seg(local, 3.2, 0.5))
    if q > 0:
        rr(d, [136, 1276, 944, 1390], 20, fill=PANEL + (int(245 * q),),
           outline=(255, 255, 255, int(24 * q)), width=2)
        d.text((168, 1306), "adaptive element tracking", font=F("mono", 24), fill=GREEN + (int(245 * q),),
               anchor="lm")
        sim = int(94 * ease(seg(local, 3.4, 1.2)))
        d.text((912, 1306), f"{sim}% match", font=F("mono", 24), fill=TXT + (int(240 * q),), anchor="rm")
        d.rounded_rectangle([168, 1346, 912, 1360], radius=7, fill=(255, 255, 255, int(26 * q)))
        d.rounded_rectangle([168, 1346, 168 + int(744 * sim / 100), 1360], radius=7,
                            fill=GREEN + (int(220 * q),))
    return img


def scene_mcp(t, img):
    local = t - 9.0
    img = paste_glow(img, GLOW_VIOLET, 540, 960, 0.85, 0.3)
    lines = [("cmd", "> agent: prices on this page")]
    if local > 1.0:
        lines.append(("dim", "  mcp: scrapling · fetch"))
    if local > 1.7:
        lines.append(("ok", "  200 OK · 1,248 rows"))
    img = term_card(img, [96, 616, 984, 900], "claude · mcp", lines, VIOLET, reveal=1.0, dim=0.95,
                    lh=54, fs=27)

    d = ImageDraw.Draw(img, "RGBA")
    k = ease(seg(local, 2.1, 0.5))
    if k > 0:
        rr(d, [96, 930, 984, 1352], 24, fill=PANEL + (int(250 * k),),
           outline=(255, 255, 255, int(26 * k)), width=2)
        d.text((132, 958), "| product     | price   |", font=F("mono", 24), fill=CYAN + (int(245 * k),))
        d.text((132, 1000), "|-------------|---------|", font=F("mono", 24), fill=MUTED + (int(180 * k),))
        rows = [("alpha desk   ", "$249"), ("beta chair   ", "$189"), ("gamma lamp   ", "$ 79"),
                ("… 1,245 more ", "")]
        for i, (a_, b_) in enumerate(rows):
            rk = ease(seg(local, 2.4 + i * 0.35, 0.4))
            if rk <= 0:
                break
            yy = 1050 + i * 62
            d.text((132, yy), f"| {a_}| {b_:<7} |", font=F("mono", 24), fill=TXT + (int(235 * rk),))
        b = ease(seg(local, 4.4, 0.5))
        if b > 0:
            rr(d, [132, 1290, 132 + int(430 * b), 1340], 16, fill=VIOLET + (int(235 * b),))
            if b > 0.7:
                d.text((347, 1315), "MCP  ·  Agent Skill", font=F("mono", 20), fill=(255, 255, 255, 250),
                       anchor="mm")
    return img


def scene_numbers(t, img):
    local = t - 15.0
    img = paste_glow(img, GLOW_CYAN, 540, 760, 0.9, 0.45)
    d = ImageDraw.Draw(img, "RGBA")
    v = int(7487 * ease(seg(local, 0.15, 1.3)))
    d.text((540, 700), f"{v:,}", font=F("bold", 190), fill=TXT + (255,), anchor="mm")
    d.text((540, 826), "STARS  THIS  WEEK", font=F("mono", 30), fill=CYAN + (235,), anchor="mm")
    badge = ease(seg(local, 1.6, 0.5))
    if badge > 0:
        bw = int(660 * badge)
        rr(d, [540 - bw // 2, 902, 540 + bw // 2, 994], 24, fill=AMBER + (int(240 * badge),))
        if badge > 0.6:
            d.text((540, 948), "#4  GITHUB  TRENDING", font=F("bold", 36), fill=(26, 22, 10, 255),
                   anchor="mm")
    tot = ease(seg(local, 1.6, 0.6))
    if tot > 0:
        d.text((540, 1140), f"{int(98721 * ease(seg(local, 1.6, 1.2))):,}", font=F("bold", 112),
               fill=TXT + (int(250 * tot),), anchor="mm")
        d.text((540, 1222), "STARS  TOTAL  ·  +8.2%  THIS  WEEK", font=F("mono", 26),
               fill=MUTED + (int(235 * tot),), anchor="mm")
        bw2 = int(760 * ease(seg(local, 1.9, 1.0)))
        rr(d, [160, 1282, 920, 1296], 8, fill=(255, 255, 255, 24))
        rr(d, [160, 1282, 160 + bw2, 1296], 8, fill=CYAN + (int(210 * tot),))
    return img


def scene_cta(t, img):
    local = t - 19.0
    img = paste_glow(img, GLOW_CYAN, 540, 760, 0.9, 0.5 * (1 - seg(local, 2.4, 0.6)))
    d = ImageDraw.Draw(img, "RGBA")
    k = ease(seg(local, 0.0, 0.35))
    s = int(lerp(140, 176, k))
    rr(d, [540 - s // 2, 700 - s // 2, 540 + s // 2, 700 + s // 2], 46,
       fill=(12, 18, 28, 255), outline=CYAN + (210,), width=4)
    d.text((540, 700), "SC", font=F("bold", int(s * 0.42)), fill=TXT + (255,), anchor="mm")
    cmd = "pip install scrapling"
    typed = cmd[: int(len(cmd) * ease(seg(local, 0.7, 1.1)))]
    box_y = 900
    rr(d, [90, box_y, 990, box_y + 132], 26, fill=PANEL + (250,), outline=(255, 255, 255, 30), width=2)
    d.text((128, box_y + 38), "$ " + typed, font=F("monoreg", 32), fill=TXT + (245,))
    if int(local * 3) % 2 == 0 and len(typed) < len(cmd):
        wpx = d.textlength("$ " + typed, font=F("monoreg", 32))
        d.rectangle([132 + wpx, box_y + 34, 136 + wpx, box_y + 74], fill=CYAN + (230,))
    q = ease(seg(local, 1.7, 0.6))
    if q > 0:
        d.text((540, 1110), "BSD-3-Clause  ·  Python  ·  scrapling.readthedocs.io", font=F("mono", 21),
               fill=MUTED + (int(225 * q),), anchor="mm")
    fade = seg(local, 2.55, 0.45)
    if fade > 0:
        img.alpha_composite(Image.new("RGBA", (W, H), (0, 0, 0, int(255 * fade))))
    return img


SCENES = [
    (0.0, scene_break),
    (3.0, scene_track),
    (9.0, scene_mcp),
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
    (0.5, 2.9, "พังทั้ง pipeline", 88, 470),
    (3.15, 8.9, "ตามกลับมาเจอ", 88, 470),
    (9.3, 14.9, "ให้ agent ดูดเอง", 78, 470),
    (19.4, 21.8, "ติดตั้งบรรทัดเดียว", 84, 450),
]

SUBS = [
    (0.6, 2.9, "เว็บเปลี่ยน DOM แล้ว scraper พังทันที"),
    (3.4, 6.1, "Scrapling ตาม element เดิมกลับมาเจอ"),
    (6.1, 8.9, "ด้วยอัลกอริทึมความคล้าย ไม่ใช่ selector ตายตัว"),
    (9.4, 12.6, "หรือให้ agent เรียกผ่าน MCP"),
    (12.6, 14.9, "ได้ตารางกลับมาเป็น Markdown เลย"),
    (15.4, 18.9, "สัปดาห์เดียว 7,487 ดาว ยอดรวม 98,721"),
    (19.5, 21.8, "ติดตั้งบรรทัดเดียว pip install scrapling"),
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
        p = os.path.join(BUILD, f"scr_still_{t:05.2f}.png")
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
