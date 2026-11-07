"""Render the 45s vertical T3 Code promo: PIL frames piped to ffmpeg, Thai text via libass/ASS.

Usage:
  python render_t3code_promo.py --stills 1.2,5.5,11.0,22.5      # PNG frames (no captions)
  python render_t3code_promo.py --render                        # full 45s mp4
  python render_t3code_promo.py --test 0 9                      # short mp4 slice
"""
import math
import os
import subprocess
import sys

from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H, FPS, DUR = 1080, 1920, 30, 45.0
N = int(DUR * FPS)
OUT = "t3code_promo_45s.mp4"
BUILD = "build"
FONTS = {
    "bold": "C:/Windows/Fonts/tahomabd.ttf",
    "reg": "C:/Windows/Fonts/tahoma.ttf",
    "mono": "C:/Windows/Fonts/consolab.ttf",
    "monoreg": "C:/Windows/Fonts/consola.ttf",
}
FF = os.path.abspath("tools/_ff/ffmpeg-9.0.2-essentials_build/bin/ffmpeg.exe")

BG_TOP, BG_BOT = (6, 9, 14), (13, 19, 30)
PANEL, PANEL2 = (16, 22, 34), (22, 30, 45)
TXT = (235, 242, 250)
MUTED = (138, 155, 178)
CYAN = (34, 211, 238)
VIOLET = (129, 140, 248)
GREEN = (52, 211, 153)
RED = (248, 113, 113)
AMBER = (251, 191, 36)
ACCENTS = [CYAN, VIOLET, GREEN, AMBER, (244, 114, 182)]

_fc = {}


def F(key, size):
    k = (key, size)
    if k not in _fc:
        _fc[k] = ImageFont.truetype(FONTS[key], size)
    return _fc[k]


def clamp(x, lo=0.0, hi=1.0):
    return max(lo, min(hi, x))


def ease(t):
    t = clamp(t)
    return 1 - (1 - t) ** 3


def ease_io(t):
    t = clamp(t)
    return t * t * (3 - 2 * t)


def lerp(a, b, t):
    return a + (b - a) * t


def seg(t, start, dur):
    return clamp((t - start) / dur)


def make_bg():
    img = Image.new("RGB", (W, H))
    d = ImageDraw.Draw(img)
    for y in range(H):
        p = y / (H - 1)
        d.line([(0, y), (W, y)], fill=tuple(int(lerp(a, b, p)) for a, b in zip(BG_TOP, BG_BOT)))
    grid = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(grid)
    for x in range(0, W, 72):
        gd.line([(x, 0), (x, H)], fill=(255, 255, 255, 7))
    for y in range(0, H, 72):
        gd.line([(0, y), (W, y)], fill=(255, 255, 255, 7))
    img = Image.alpha_composite(img.convert("RGBA"), grid)
    vig = Image.new("L", (W, H), 0)
    vd = ImageDraw.Draw(vig)
    vd.ellipse([-W * 0.35, -H * 0.12, W * 1.35, H * 1.12], fill=110)
    vig = vig.filter(ImageFilter.GaussianBlur(160))
    dark = Image.new("RGBA", (W, H), (0, 0, 0, 165))
    img = Image.composite(img, Image.alpha_composite(img, dark), vig)
    return img.convert("RGB")


BG = make_bg()


def glow(size, color, alpha=255):
    g = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    gd = ImageDraw.Draw(g)
    steps = 26
    for i in range(steps, 0, -1):
        r = size / 2 * i / steps
        a = int(alpha * (1 - i / steps) ** 2.1)
        gd.ellipse([size / 2 - r, size / 2 - r, size / 2 + r, size / 2 + r], fill=color + (a,))
    return g.filter(ImageFilter.GaussianBlur(size / 14))


GLOW_CYAN = glow(900, CYAN, 190)
GLOW_VIOLET = glow(900, VIOLET, 170)


def paste_glow(img, gl, cx, cy, scale=1.0, alpha=1.0):
    s = int(gl.width * scale)
    if s < 8:
        return img
    g = gl.resize((s, s), Image.LANCZOS)
    if alpha < 1.0:
        a = g.split()[3].point(lambda v: int(v * alpha))
        g.putalpha(a)
    img.alpha_composite(g, (int(cx - s / 2), int(cy - s / 2)))
    return img


def rr(d, box, r, fill=None, outline=None, width=2):
    d.rounded_rectangle(box, radius=r, fill=fill, outline=outline, width=width)


def term_card(img, box, title, lines, accent, reveal=1.0, dim=1.0, lh=40, fs=25):
    d = ImageDraw.Draw(img, "RGBA")
    x0, y0, x1, y1 = box
    rr(d, box, 26, fill=PANEL + (int(255 * dim),), outline=(255, 255, 255, int(26 * dim)), width=2)
    d.line([(x0 + 2, y0 + 52), (x1 - 2, y0 + 52)], fill=(255, 255, 255, int(22 * dim)), width=2)
    for i, c in enumerate([(248, 113, 113), (251, 191, 36), (52, 211, 153)]):
        d.ellipse([x0 + 22 + i * 24, y0 + 19, x0 + 36 + i * 24, y0 + 33], fill=c + (int(230 * dim),))
    d.text((x0 + 110, y0 + 16), title, font=F("mono", 24), fill=MUTED + (int(235 * dim),))
    d.rounded_rectangle([x0 + 16, y0 + 74, x0 + 22, y1 - 16], radius=3, fill=accent + (int(200 * dim),))
    y = y0 + 74
    shown = reveal * len(lines)
    for i, (kind, s) in enumerate(lines):
        if i >= shown + 0.001:
            break
        frac = clamp(shown - i)
        s = s[: max(1, int(len(s) * frac))] if frac < 1 else s
        col = {"ok": GREEN, "err": RED, "cmd": accent, "dim": MUTED}.get(kind, TXT)
        d.text((x0 + 44, y), s, font=F("monoreg", fs), fill=col + (int(240 * dim),))
        y += lh
    return img


# ---------------------------------------------------------------- scenes
def scene_hook(t, img):
    img = paste_glow(img, GLOW_CYAN, 540, 1000, 0.85, 0.55 + 0.22 * math.sin(t * 2.2))
    lines = [
        ("cmd", "> claude --continue"),
        ("", "  editing src/auth/session.ts"),
        ("dim", "  ... 12 files changed"),
        ("ok", "  ok  tests passing"),
    ]
    img = term_card(img, [96, 760, 984, 1240], "~/acme-app  main", lines, CYAN,
                    reveal=ease(seg(t, 0.15, 1.9)), dim=0.62, lh=52, fs=30)
    if 0.4 < t < 0.56:
        a = int(110 * (1 - (t - 0.4) / 0.16))
        d = ImageDraw.Draw(img, "RGBA")
        d.rectangle([0, 0, W, H], fill=(255, 255, 255, a))
    return img


def scene_agents(t, img):
    local = t - 3.0
    img = paste_glow(img, GLOW_VIOLET, 860, 900, 0.7, 0.35)
    x0, w, h, gap, y0 = 90, 900, 158, 16, 640
    titles = ["agent-1  claude", "agent-2  codex", "agent-3  cursor",
              "agent-4  opencode", "agent-5  fx"]
    jobs = ["refactor cart total", "add stripe webhook", "fix flaky test",
            "migrate schema", "review PR #482"]
    st = ["running", "running", "waiting", "running", "queued"]
    for i in range(5):
        k = ease(seg(local, 0.08 + i * 0.12, 0.45))
        if k <= 0:
            continue
        oy = int((1 - k) * 60)
        top = y0 + i * (h + gap) + oy
        img = term_card(img, [x0, top, x0 + w, top + h], titles[i],
                        [("", "  " + jobs[i]), ("dim", "  " + st[i])], ACCENTS[i],
                        reveal=ease(seg(local, 0.15 + i * 0.12, 0.5)), lh=34, fs=26)
    return img


def scene_lid(t, img):
    local = t - 9.0
    close = ease_io(seg(local, 1.1, 0.7))
    lid_h = int(lerp(430, 10, close))
    top = 720
    d = ImageDraw.Draw(img, "RGBA")
    # the base rises with the lid so the laptop never breaks apart
    base_top = top + lid_h + 22
    d.polygon([(150, base_top), (930, base_top), (1000, base_top + 56), (80, base_top + 56)],
              fill=PANEL2 + (255,))
    sx0, sx1 = 190, 890
    rr(d, [sx0, top, sx1, top + lid_h], 16, fill=(10, 15, 24, 255),
       outline=(255, 255, 255, 30), width=2)
    if lid_h > 90:
        inner = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        idr = ImageDraw.Draw(inner)
        idr.rounded_rectangle([sx0 + 20, top + 20, sx1 - 20, top + lid_h - 20], radius=10,
                              fill=(8, 12, 20, 255))
        prog = seg(local, 0.0, 1.1)
        idr.text((sx0 + 48, top + 52), "$ pnpm test --watch", font=F("monoreg", 26), fill=CYAN + (240,))
        for j, s_ in enumerate(["RUN  src/cart.test.ts", "RUN  src/auth.test.ts"]):
            idr.text((sx0 + 48, top + 104 + j * 44), s_, font=F("monoreg", 24), fill=MUTED + (240,))
        idr.text((sx0 + 48, top + 200), "  PASS  42 tests", font=F("monoreg", 24), fill=GREEN + (240,))
        idr.rounded_rectangle([sx0 + 48, top + 270, sx0 + 48 + int(560 * prog), top + 278],
                              radius=4, fill=CYAN + (220,))
        img.alpha_composite(inner)
    else:
        d.rounded_rectangle([190, top + lid_h - 5, 890, top + lid_h], radius=2,
                            fill=(120, 40, 45, 225))
    if close >= 0.98:
        a = int(215 * seg(local, 1.85, 0.35))
        d.text((540, top + 150), "▌", font=F("mono", 62), fill=RED + (a,), anchor="mm")
        cw_, gap = 240, 24
        x0 = (W - (3 * cw_ + 2 * gap)) // 2
        for i, (label, col) in enumerate([("0 running", RED), ("0 queued", MUTED), ("paused", AMBER)]):
            k = ease(seg(local, 1.95 + i * 0.12, 0.4))
            if k <= 0:
                continue
            x, y = x0 + i * (cw_ + gap), 1010
            rr(d, [x, y, x + cw_, y + 84], 20, fill=PANEL + (int(250 * k),),
               outline=col + (int(140 * k),), width=2)
            d.ellipse([x + 24, y + 33, x + 42, y + 51], fill=col + (int(240 * k),))
            d.text((x + 58, y + 42), label, font=F("mono", 24), fill=TXT + (int(240 * k),), anchor="lm")
    return img


def scene_reveal(t, img):
    local = t - 13.0
    k = ease(seg(local, 0.0, 0.55))
    img = paste_glow(img, GLOW_CYAN, 540, 760, 0.85, 0.6 * k)
    d = ImageDraw.Draw(img, "RGBA")
    s = int(lerp(170, 250, k))
    rr(d, [540 - s // 2, 760 - s // 2, 540 + s // 2, 760 + s // 2], 60,
       fill=(12, 18, 28, 255), outline=CYAN + (200,), width=4)
    d.text((540, 760), "T3", font=F("bold", int(s * 0.46)), fill=TXT + (255,), anchor="mm")
    for i in range(3):
        kk = ease(seg(local, 0.75 + i * 0.16, 0.45))
        if kk <= 0:
            continue
        y = 1250 + i * 108
        x = int(lerp(1320, 150, kk))
        w = 780
        rr(d, [x, y, x + w, y + 86], 20, fill=PANEL + (int(255 * kk),),
           outline=(255, 255, 255, int(24 * kk)), width=2)
        d.ellipse([x + 26, y + 31, x + 46, y + 51], fill=ACCENTS[i] + (int(240 * kk),))
        d.text((x + 66, y + 26), ["session · main", "session · api", "session · docs"][i],
               font=F("mono", 30), fill=TXT + (int(240 * kk),))
        d.text((x + w - 124, y + 28), "live", font=F("mono", 20), fill=GREEN + (int(220 * kk),))
    return img


def scene_phone(t, img):
    local = t - 19.0
    img = paste_glow(img, GLOW_VIOLET, 190, 1100, 0.8, 0.32)
    img = paste_glow(img, GLOW_CYAN, 900, 820, 0.7, 0.28)
    d = ImageDraw.Draw(img, "RGBA")
    px0, py0, px1, py1 = 200, 570, 880, 1650
    rr(d, [px0 - 12, py0 - 12, px1 + 12, py1 + 12], 74, fill=(255, 255, 255, 26))
    rr(d, [px0, py0, px1, py1], 64, fill=(9, 13, 21, 255), outline=(255, 255, 255, 40), width=3)
    rr(d, [px0 + 12, py0 + 12, px1 - 12, py1 - 12], 54, fill=(12, 17, 26, 255))
    rr(d, [470, py0 + 26, 610, py0 + 46], 10, fill=(0, 0, 0, 255))
    d.text((px0 + 46, py0 + 80), "T3 Code", font=F("bold", 40), fill=TXT + (255,))
    d.text((px1 - 46, py0 + 92), "● 3 live", font=F("mono", 24), fill=GREEN + (230,), anchor="ra")
    for i, (name, st, col) in enumerate([("acme-app / main", "running", GREEN),
                                        ("acme-app / api", "running", GREEN),
                                        ("docs / site", "waiting", AMBER)]):
        y = py0 + 160 + i * 112
        rr(d, [px0 + 30, y, px1 - 30, y + 96], 22, fill=PANEL + (255,),
           outline=(255, 255, 255, 20), width=2)
        d.text((px0 + 56, y + 20), name, font=F("monoreg", 24), fill=TXT + (245,))
        d.text((px0 + 56, y + 56), st, font=F("monoreg", 20), fill=col + (230,))
    dlg = seg(local, 1.9, 0.4)
    tap = seg(local, 3.0, 0.45)
    hide = ease(seg(local, 3.55, 0.35))
    if dlg > 0:
        h = int(lerp(0, 320, ease(dlg)) * (1 - hide))
        if h > 4:
            y0 = py1 - 130 - h
            rr(d, [px0 + 26, y0, px1 - 26, py1 - 130], 28, fill=(24, 32, 46, 255),
               outline=CYAN + (int(180 * (1 - hide)),), width=3)
            d.text((px0 + 56, y0 + 34), "Allow file edits?", font=F("bold", 36), fill=TXT + (255,))
            d.text((px0 + 56, y0 + 88), "src/auth/session.ts  ·  3 files", font=F("monoreg", 22),
                   fill=MUTED + (240,))
            btn_y = y0 + h - 92
            rr(d, [px0 + 56, btn_y, px0 + 296, btn_y + 62], 18, fill=(255, 255, 255, 22))
            d.text((px0 + 176, btn_y + 31), "Deny", font=F("reg", 30), fill=MUTED + (240,), anchor="mm")
            rr(d, [px1 - 326, btn_y, px1 - 56, btn_y + 62], 18, fill=(34, 197, 220, 235))
            d.text((px1 - 191, btn_y + 31), "Allow", font=F("bold", 30), fill=(6, 12, 18, 255), anchor="mm")
            if 0 < tap < 1:
                rad = int(30 + 58 * tap)
                d.ellipse([px1 - 191 - rad, btn_y + 31 - rad, px1 - 191 + rad, btn_y + 31 + rad],
                          outline=(255, 255, 255, int(170 * (1 - tap))), width=5)
    diff = seg(local, 3.9, 0.9)
    if diff > 0:
        y = py1 - 330
        rows = [("+", "session.refresh()", GREEN), ("-", "session.touch()", RED), ("+", "await verify(jwt)", GREEN)]
        for i, (sign, s_, col) in enumerate(rows):
            if diff * 3 <= i:
                break
            rr(d, [px0 + 26, y + i * 62, px1 - 26, y + i * 62 + 52], 12,
               fill=(col[0] // 8, col[1] // 8, col[2] // 8, 215))
            d.text((px0 + 46, y + i * 62 + 12), sign + " " + s_, font=F("monoreg", 21), fill=col + (245,))
    return img


def scene_providers(t, img):
    local = t - 26.0
    img = paste_glow(img, GLOW_CYAN, 540, 1000, 0.75, 0.3)
    d = ImageDraw.Draw(img, "RGBA")
    chips = ["Claude Code", "Codex", "Cursor", "OpenCode", "Antigravity", "Grok Build", "fx"]
    cols, cw, ch, gap = 2, 400, 104, 28
    x_start = (W - (cols * cw + gap)) // 2
    y_start = 780
    for i, name in enumerate(chips):
        k = ease(seg(local, 0.12 + i * 0.1, 0.4))
        if k <= 0:
            continue
        r, c = divmod(i, cols)
        cx = x_start + c * (cw + gap)
        cy = y_start + r * (ch + gap)
        sc = lerp(0.9, 1.0, k)
        w2, h2 = int(cw * sc), int(ch * sc)
        cx2, cy2 = cx + (cw - w2) // 2, cy + (ch - h2) // 2
        col = ACCENTS[i % len(ACCENTS)]
        rr(d, [cx2, cy2, cx2 + w2, cy2 + h2], 24, fill=PANEL + (int(250 * k),),
           outline=col + (int(150 * k),), width=2)
        d.ellipse([cx2 + 26, cy2 + h2 / 2 - 9, cx2 + 44, cy2 + h2 / 2 + 9], fill=col + (int(245 * k),))
        d.text((cx2 + 60, cy2 + h2 / 2), name, font=F("reg", 32), fill=TXT + (int(245 * k),), anchor="lm")
    tag = ease(seg(local, 1.5, 0.5))
    if tag > 0:
        d.text((540, 1350), "already installed  ·  already logged in", font=F("mono", 26),
               fill=MUTED + (int(230 * tag),), anchor="mm")
    return img


def scene_numbers(t, img):
    local = t - 31.0
    img = paste_glow(img, GLOW_CYAN, 540, 780, 0.9, 0.45)
    d = ImageDraw.Draw(img, "RGBA")
    v = int(16235 * ease(seg(local, 0.15, 1.5)))
    d.text((540, 700), f"{v:,}", font=F("bold", 190), fill=TXT + (255,), anchor="mm")
    d.text((540, 826), "STARS  THIS  WEEK", font=F("mono", 30), fill=CYAN + (235,), anchor="mm")
    badge = ease(seg(local, 1.9, 0.5))
    if badge > 0:
        bw = int(620 * badge)
        rr(d, [540 - bw // 2, 910, 540 + bw // 2, 1000], 24, fill=(253, 224, 71, int(240 * badge)))
        if badge > 0.6:
            d.text((540, 955), "#1  GITHUB TRENDING", font=F("bold", 36), fill=(24, 24, 16, 255), anchor="mm")
    dl = ease(seg(local, 2.4, 1.6))
    if dl > 0:
        d.text((540, 1180), f"{15.1 * dl:,.1f}M", font=F("bold", 130), fill=TXT + (int(250 * dl),), anchor="mm")
        d.text((540, 1282), "RELEASE  DOWNLOADS  ·  ALL  TIME", font=F("mono", 26),
               fill=MUTED + (int(235 * dl),), anchor="mm")
        barw = int(760 * dl)
        rr(d, [160, 1330, 920, 1350], 10, fill=(255, 255, 255, 26))
        rr(d, [160, 1330, 160 + barw, 1350], 10, fill=CYAN + (int(240 * dl),))
    return img


def scene_cta(t, img):
    local = t - 37.0
    img = paste_glow(img, GLOW_CYAN, 540, 780, 0.9, 0.5 * (1 - seg(local, 6.4, 1.2)))
    d = ImageDraw.Draw(img, "RGBA")
    k = ease(seg(local, 0.0, 0.4))
    s = int(lerp(140, 180, k))
    rr(d, [540 - s // 2, 740 - s // 2, 540 + s // 2, 740 + s // 2], 46,
       fill=(12, 18, 28, 255), outline=CYAN + (210,), width=4)
    d.text((540, 740), "T3", font=F("bold", int(s * 0.46)), fill=TXT + (255,), anchor="mm")
    cmd = "curl -fsSL https://t3.codes/install.sh | sh"
    typed = cmd[: int(len(cmd) * ease(seg(local, 1.8, 1.4)))]
    box_y = 980
    rr(d, [90, box_y, 990, box_y + 140], 26, fill=PANEL + (250,), outline=(255, 255, 255, 30), width=2)
    d.text((128, box_y + 42), "$ " + typed, font=F("monoreg", 28), fill=TXT + (245,))
    if int(local * 3) % 2 == 0 and len(typed) < len(cmd):
        wpx = d.textlength("$ " + typed, font=F("monoreg", 28))
        d.rectangle([132 + wpx, box_y + 38, 136 + wpx, box_y + 78], fill=CYAN + (230,))
    q = ease(seg(local, 3.4, 0.6))
    if q > 0:
        d.text((540, 1230), "free  ·  open source  ·  MIT", font=F("mono", 28),
               fill=MUTED + (int(230 * q),), anchor="mm")
    fade = seg(local, 6.4, 1.3)
    if fade > 0:
        img.alpha_composite(Image.new("RGBA", (W, H), (0, 0, 0, int(255 * fade))))
    return img


SCENES = [
    (0.0, scene_hook),
    (3.0, scene_agents),
    (9.0, scene_lid),
    (13.0, scene_reveal),
    (19.0, scene_phone),
    (26.0, scene_providers),
    (31.0, scene_numbers),
    (37.0, scene_cta),
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


# start, end, text, font-size, y (headline sits above the graphics of its scene)
HEAD = [
    (0.5, 3.0, "โค้ดยังรันอยู่", 92, 560),
    (3.3, 8.8, "5 agents · 5 terminals", 80, 470),
    (9.3, 13.0, "ปิดฝา = งานหยุด", 88, 560),
    (13.3, 16.3, "T3 CODE", 112, 1060),
    (16.3, 19.0, "control surface", 68, 1150),
    (19.4, 26.0, "Remote · Mobile · Web", 72, 420),
    (26.3, 31.0, "ใช้ subscription เดิม", 74, 560),
    (37.6, 44.3, "t3.codes", 112, 520),
]

SUBS = [
    (0.7, 3.0, "ทั้งที่คุณไม่ได้อยู่หน้าคอม"),
    (3.4, 6.2, "คนเขียนโค้ดวันนี้ไม่ได้มี agent ตัวเดียว"),
    (6.2, 8.9, "แต่มีห้าตัว คนละหน้าต่าง"),
    (9.4, 13.0, "พอปิดฝาแล็ปท็อป งานทั้งหมดก็หยุด"),
    (13.4, 19.0, "T3 Code คือศูนย์ควบคุม agent ที่มีอยู่บนเครื่องคุณ"),
    (19.5, 22.6, "เปิดมือถือ เห็นทุกเซสชัน สั่งงาน อนุมัติสิทธิ์"),
    (22.6, 26.0, "และดู diff ได้จากที่ไหนก็ตาม"),
    (26.4, 31.0, "ใช้ Claude Code, Codex, Cursor, OpenCode ตาม subscription เดิม"),
    (31.5, 37.0, "สัปดาห์เดียว 16,235 ดาว อันดับหนึ่ง GitHub Trending"),
    (37.7, 44.2, "ฟรี โอเพนซอร์ส MIT — ติดตั้งบรรทัดเดียวที่ t3.codes"),
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


def build_ass():
    os.makedirs(BUILD, exist_ok=True)
    out = [ASS]
    for start, end, text, size, y in HEAD:
        out.append(
            f"Dialogue: 1,{ts(start)},{ts(end)},Head,,0,0,0,,"
            f"{{\\pos(540,{y})\\fs{size}\\fad(260,220)\\fscx88\\fscy88\\t(0,400,\\fscx100\\fscy100)}}{text}"
        )
    for start, end, text in SUBS:
        style = "Sub" if len(text) <= 52 else "SubSmall"
        out.append(f"Dialogue: 0,{ts(start)},{ts(end)},{style},,0,0,0,,{{\\fad(180,160)}}{text}")
    path = os.path.join(BUILD, "captions.ass")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(out) + "\n")
    return path


# ---------------------------------------------------------------- outputs
def ffmpeg_cmd(dest):
    ass = os.path.join(BUILD, "captions.ass").replace("\\", "/")
    return [
        FF, "-y", "-hide_banner", "-loglevel", "error",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
        "-f", "lavfi", "-i", "anullsrc=channel_layout=stereo:sample_rate=44100",
        "-vf", f"subtitles={ass}:fontsdir=fonts",
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
    print("ffmpeg exit", code, "->", dest, f"({n} frames)")
    return code


def stills(times):
    os.makedirs(BUILD, exist_ok=True)
    build_ass()
    for t in times:
        p = os.path.join(BUILD, f"still_{t:05.2f}.png")
        render(t).save(p)
        print("wrote", p)


if __name__ == "__main__":
    args = sys.argv[1:]
    if "--stills" in args:
        stills([float(x) for x in args[args.index("--stills") + 1].split(",")])
    elif "--test" in args:
        a, b = float(args[1]), float(args[2])
        encode(os.path.join(BUILD, "test.mp4"), a, b)
    elif "--render" in args:
        encode(OUT)
    else:
        print(__doc__)
