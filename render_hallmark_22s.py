"""Render the 22s vertical hallmark promo (trending #5) — the fourth 22s clip in the series.

Scenes follow promo_scripts_rank2to5.md § อันดับ 5:
  0-3   three pages, three prompts, one look
  3-9   three themes drawn from fifty, the page rebuilt in that material
  9-15  sloplint checks eight widths, then Floor / Reflex / Finish gate it
  15-19 6,994 stars this week, 16.5% growth
  19-22 npx skills add nutlope/hallmark -g

Imports the shared look from render_t3code_promo.py; see SKILL.md for the conventions.

Usage:
  python render_hallmark_22s.py --stills 1.5,6.0,12.0,17.0,20.6
  python render_hallmark_22s.py --render
"""
import math
import os
import subprocess
import sys

from PIL import Image, ImageDraw

import render_t3code_promo as base

W, H, FPS, DUR = 1080, 1920, 30, 22.0
OUT = os.environ.get("OUT_NAME") or "hallmark_promo_22s.mp4"
BUILD = "build"
ASS_NAME = "captions_hall.ass"

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
GLOW_AMBER = base.glow(900, AMBER, 150)
GLOW_GREEN = base.glow(900, GREEN, 150)


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


def tint(c, k=255):
    return tuple(int(v) for v in c) + (int(k),)


def mixc(a, b, k):
    return tuple(int(lerp(x, y, k)) for x, y in zip(a, b))


def lum(c):
    return 0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2]


# ---------------------------------------------------------------- scenes
SLOP = (129, 140, 248)


def same_page(d, x, y, w, h, k, accent=SLOP):
    rr(d, [x, y, x + w, y + h], 22, fill=PANEL + (int(250 * k),),
       outline=(255, 255, 255, int(26 * k)), width=2)
    d.rounded_rectangle([x + 18, y + 18, x + w - 18, y + 52], radius=8, fill=accent + (int(220 * k),))
    d.text((x + 20, y + 74), "EYEBROW", font=F("mono", 13), fill=MUTED + (int(220 * k),))
    d.rounded_rectangle([x + 20, y + 104, x + w - 40, y + 126], radius=5, fill=TXT + (int(200 * k),))
    d.rounded_rectangle([x + 20, y + 138, x + w - 110, y + 156], radius=5, fill=TXT + (int(100 * k),))
    rr(d, [x + 20, y + 186, x + w - 20, y + 288], 14, fill=PANEL2 + (int(240 * k),),
       outline=(255, 255, 255, int(16 * k)), width=1)
    rr(d, [x + 34, y + 200, x + w - 34, y + 274], 10, fill=(10, 14, 22, int(245 * k)))
    rr(d, [x + 20, y + 318, x + 132, y + 352], 17, fill=accent + (int(230 * k),))
    d.text((x + 76, y + 335), "get started", font=F("mono", 13), fill=(255, 255, 255, int(240 * k)),
           anchor="mm")


def scene_same(t, img):
    img = paste_glow(img, GLOW_VIOLET, 540, 980, 0.9, 0.26 + 0.08 * math.sin(t * 2.0))
    d = ImageDraw.Draw(img, "RGBA")
    # three pages fanned, identical content, right to left so the left cards sit on top
    for i in (2, 1, 0):
        k = ease(seg(t, 0.05 + (2 - i) * 0.10, 0.45))
        if k <= 0:
            continue
        x = 96 + i * 268
        y = int(640 + i * 52 + (1 - k) * 40)
        same_page(d, x, y, 360, 392, k)
    k = ease(seg(t, 1.6, 0.5))
    if k > 0:
        d.text((540, 1290), "3 pages · 3 prompts · same look", font=F("mono", 20),
               fill=AMBER + (int(220 * k),), anchor="mm")
    cut = seg(t, 2.5, 0.4)
    if cut > 0:
        img.alpha_composite(Image.new("RGBA", (W, H), (0, 0, 0, int(255 * cut))))
    return img


THEMES = [
    ("Dusk", (34, 28, 38), (52, 44, 58), (244, 164, 96)),
    ("Cobalt", (12, 24, 44), (22, 40, 68), (86, 156, 255)),
    ("Studio", (238, 232, 220), (250, 246, 238), (32, 32, 32)),
]
BASE_BG, BASE_CARD, BASE_ACC = (22, 28, 38), (30, 38, 50), (120, 130, 150)


def scene_themes(t, img):
    local = t - 3.0
    img = paste_glow(img, GLOW_AMBER, 540, 980, 0.85, 0.14 + 0.2 * ease(seg(local, 1.6, 1.6)))
    d = ImageDraw.Draw(img, "RGBA")

    for i, (name, bgc, cardc, acc) in enumerate(THEMES):
        k = ease(seg(local, 0.15 + i * 0.28, 0.45))
        if k <= 0:
            continue
        x = 150 + i * 268
        y = int(600 + (1 - k) * 34)
        rr(d, [x, y, x + 240, y + 104], 18, fill=PANEL + (int(250 * k),),
           outline=acc + (int(200 * k),), width=2)
        for j, c in enumerate((bgc, cardc, acc)):
            d.ellipse([x + 20 + j * 30, y + 18, x + 42 + j * 30, y + 40], fill=tint(c, 245 * k))
        d.text((x + 20, y + 58), name, font=F("mono", 26), fill=TXT + (int(245 * k),))
        d.text((x + 20, y + 90), "material", font=F("mono", 13), fill=MUTED + (int(200 * k),))

    # the page being rebuilt out of each material
    bg, card, acc = BASE_BG, BASE_CARD, BASE_ACC
    for i, (_, tbg, tcard, tacc) in enumerate(THEMES):
        k = ease_io(seg(local, 1.7 + i * 1.45, 0.85))
        bg, card, acc = mixc(bg, tbg, k), mixc(card, tcard, k), mixc(acc, tacc, k)
    k = ease(seg(local, 1.5, 0.5))
    if k > 0:
        dark = lum(bg) < 140
        ink = (255, 255, 255) if dark else (24, 24, 24)
        sub = (160, 170, 185) if dark else (95, 95, 95)
        rr(d, [96, 760, 984, 1330], 24, fill=bg + (int(250 * k),),
           outline=(255, 255, 255, int(30 * k)), width=2)
        rr(d, [120, 784, 960, 830], 10, fill=mixc(bg, ink, 0.10) + (int(240 * k),))
        d.text((132, 807), "hallmark.app", font=F("mono", 18), fill=sub + (int(230 * k),), anchor="lm")
        d.rounded_rectangle([132, 858, 500, 890], radius=6, fill=ink + (int(220 * k),))
        d.rounded_rectangle([132, 906, 700, 924], radius=5, fill=sub + (int(180 * k),))
        rr(d, [132, 946, 470, 1000], 24, fill=acc + (int(240 * k),))
        d.text((301, 973), "start free", font=F("mono", 18),
               fill=(20, 20, 20) if lum(acc) > 150 else (255, 255, 255), anchor="mm")
        for i in range(3):
            x = 132 + i * 272
            rr(d, [x, 1040, x + 232, 1290], 16, fill=card + (int(245 * k),),
               outline=mixc(card, ink, 0.16) + (int(200 * k),), width=1)
            d.rounded_rectangle([x + 18, 1060, x + 90, 1078], radius=5, fill=acc + (int(220 * k),))
            d.rounded_rectangle([x + 18, 1104, x + 200, 1118], radius=4, fill=ink + (int(150 * k),))
            d.rounded_rectangle([x + 18, 1134, x + 150, 1146], radius=4, fill=sub + (int(140 * k),))
            d.rounded_rectangle([x + 18, 1216, x + 214, 1268], radius=10,
                                fill=mixc(card, ink, 0.12) + (int(220 * k),))
    return img


WIDTHS = [360, 390, 414, 480, 600, 768, 834, 1024]


def scene_gate(t, img):
    local = t - 9.0
    img = paste_glow(img, GLOW_GREEN, 540, 980, 0.85, 0.16 + 0.2 * ease(seg(local, 0.8, 1.4)))
    d = ImageDraw.Draw(img, "RGBA")
    rr(d, [96, 596, 984, 1160], 24, fill=PANEL + (250,), outline=(255, 255, 255, 26), width=2)
    d.text((128, 622), "sloplint --render", font=F("mono", 22), fill=MUTED + (240,))
    done = int(8 * ease(seg(local, 0.3, 1.9)))
    d.text((952, 616), f"{done} / 8 widths", font=F("bold", 26), fill=CYAN + (245,), anchor="ra")

    for i, v in enumerate(WIDTHS):
        k = ease(seg(local, 0.35 + i * 0.22, 0.4))
        if k <= 0:
            break
        y = 676 + i * 58
        d.text((128, y + 11), f"{v}", font=F("mono", 21), fill=MUTED + (int(230 * k),), anchor="lm")
        wdt = int((v / 1024) * 590 * k)
        d.rounded_rectangle([212, y, 212 + wdt, y + 22], radius=6,
                            fill=mixc(PANEL2, GREEN, 0.35) + (int(230 * k),))
        ok = ease(seg(local, 0.55 + i * 0.22, 0.3))
        if ok > 0:
            d.line([(838, y + 11), (848, y + 21), (866, y - 1)], fill=GREEN + (int(245 * ok),), width=3)

    layers = [("Floor", "must pass", RED), ("Reflex", "defaults, may waive", AMBER),
              ("Finish", "polish on top", GREEN)]
    for i, (name, note, col) in enumerate(layers):
        k = ease(seg(local, 3.0 + i * 0.28, 0.45))
        if k <= 0:
            continue
        y = 1216 + i * 66 - int((1 - k) * 26)
        rr(d, [96, y, 500, y + 54], 16, fill=PANEL + (int(250 * k),), outline=col + (int(200 * k),),
           width=2)
        d.text((124, y + 27), name, font=F("mono", 24), fill=col + (int(245 * k),), anchor="lm")
        d.text((520, y + 27), note, font=F("mono", 20), fill=MUTED + (int(215 * k),), anchor="lm")
    return img


def scene_numbers(t, img):
    local = t - 15.0
    img = paste_glow(img, GLOW_AMBER, 540, 760, 0.9, 0.45)
    d = ImageDraw.Draw(img, "RGBA")
    v = int(6994 * ease(seg(local, 0.15, 1.3)))
    d.text((540, 700), f"{v:,}", font=F("bold", 190), fill=TXT + (255,), anchor="mm")
    d.text((540, 826), "STARS  THIS  WEEK", font=F("mono", 30), fill=CYAN + (235,), anchor="mm")
    badge = ease(seg(local, 1.6, 0.5))
    if badge > 0:
        bw = int(660 * badge)
        rr(d, [540 - bw // 2, 902, 540 + bw // 2, 994], 24, fill=AMBER + (int(240 * badge),))
        if badge > 0.6:
            d.text((540, 948), "#5  GITHUB  TRENDING", font=F("bold", 36), fill=(26, 22, 10, 255),
                   anchor="mm")
    tot = ease(seg(local, 1.6, 0.6))
    if tot > 0:
        d.text((540, 1128), "16.5%", font=F("bold", 118), fill=GREEN + (int(250 * tot),), anchor="mm")
        d.text((540, 1206), "GROWTH  THIS  WEEK  ·  HIGHEST  IN  THE  TOP  5", font=F("mono", 23),
               fill=MUTED + (int(235 * tot),), anchor="mm")
        d.text((540, 1268), "49,404 stars total  ·  193 days old", font=F("mono", 21),
               fill=MUTED + (int(200 * tot),), anchor="mm")
    return img


def scene_cta(t, img):
    local = t - 19.0
    img = paste_glow(img, GLOW_AMBER, 540, 760, 0.9, 0.5 * (1 - seg(local, 2.4, 0.6)))
    d = ImageDraw.Draw(img, "RGBA")
    k = ease(seg(local, 0.0, 0.35))
    s = int(lerp(140, 176, k))
    rr(d, [540 - s // 2, 700 - s // 2, 540 + s // 2, 700 + s // 2], 46,
       fill=(12, 18, 28, 255), outline=AMBER + (210,), width=4)
    d.text((540, 700), "HM", font=F("bold", int(s * 0.42)), fill=TXT + (255,), anchor="mm")
    cmd = "npx skills add nutlope/hallmark -g"
    typed = cmd[: int(len(cmd) * ease(seg(local, 0.7, 1.25)))]
    box_y = 900
    rr(d, [90, box_y, 990, box_y + 132], 26, fill=PANEL + (250,), outline=(255, 255, 255, 30), width=2)
    d.text((128, box_y + 38), "$ " + typed, font=F("monoreg", 28), fill=TXT + (245,))
    if int(local * 3) % 2 == 0 and len(typed) < len(cmd):
        wpx = d.textlength("$ " + typed, font=F("monoreg", 28))
        d.rectangle([132 + wpx, box_y + 34, 136 + wpx, box_y + 74], fill=AMBER + (230,))
    q = ease(seg(local, 1.8, 0.6))
    if q > 0:
        d.text((540, 1110), "MIT  ·  50 themes  ·  usehallmark.com", font=F("mono", 23),
               fill=MUTED + (int(225 * q),), anchor="mm")
    fade = seg(local, 2.55, 0.45)
    if fade > 0:
        img.alpha_composite(Image.new("RGBA", (W, H), (0, 0, 0, int(255 * fade))))
    return img


SCENES = [
    (0.0, scene_same),
    (3.0, scene_themes),
    (9.0, scene_gate),
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
    (0.5, 2.9, "เหมือนกันหมด", 88, 470),
    (3.15, 8.9, "3 จาก 50 ธีม", 80, 470),
    (9.3, 14.9, "ตรวจ 8 ความกว้าง", 70, 470),
    (19.4, 21.8, "usehallmark.com", 76, 450),
]

SUBS = [
    (0.6, 2.9, "AI ทำหน้าเว็บทุกวัน แต่ทำไมยังดูเหมือนกันหมด"),
    (3.4, 6.1, "hallmark จั่ว 3 ธีมจาก 50 แล้วสร้างจากวัสดุของธีมนั้น"),
    (6.1, 8.9, "Dusk · Cobalt · Studio — คนละวัสดุ คนละหน้าตา"),
    (9.4, 12.6, "sloplint ตรวจในเบราว์เซอร์จริง 8 ความกว้าง"),
    (12.6, 14.9, "ผ่าน Floor ก่อนถึงจะปล่อยได้"),
    (15.4, 18.9, "สัปดาห์เดียว 6,994 ดาว โต 16.5% สูงสุดในห้าอันดับ"),
    (19.5, 21.8, "ติดตั้งคำสั่งเดียว npx skills add nutlope/hallmark"),
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
# MarginV 150 is the 16:9-safe default; TikTok's bottom overlay covers that strip on 9:16.
SUB_MV = os.environ.get("SUB_MARGIN_V", "150")
ASS = ASS.replace(",70,70,150,1", f",70,70,{SUB_MV},1").replace(",60,60,150,1", f",60,60,{SUB_MV},1")


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
        p = os.path.join(BUILD, f"hall_still_{t:05.2f}.png")
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
