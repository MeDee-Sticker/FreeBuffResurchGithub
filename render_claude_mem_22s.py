"""Render the 22s vertical claude-mem promo (trending #2) — same visual language as the T3 Code clip.

Reuses the shared look (dark grid bg, mono type, term cards) from render_t3code_promo.py so the
series stays consistent. Thai text is burned via libass/ASS because Pillow here has no raqm.

Usage:
  python render_claude_mem_22s.py --stills 1.5,5.2,11.0,17.0,20.6   # PNG frames
  python render_claude_mem_22s.py --render                          # full 22s mp4
"""
import os
import subprocess
import sys

from PIL import Image, ImageDraw

import render_t3code_promo as base

W, H, FPS, DUR = 1080, 1920, 30, 22.0
OUT = os.environ.get("OUT_NAME") or "claude_mem_promo_22s.mp4"
BUILD = "build"
ASS_NAME = "captions_cm.ass"
FF = base.FF
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


# ---------------------------------------------------------------- scenes
def scene_forget(t, img):
    """0-3s: a fresh session that remembers nothing."""
    img = paste_glow(img, GLOW_CYAN, 540, 980, 0.8, 0.35 + 0.15 * base.math.sin(t * 2.4))
    lines = [
        ("cmd", "> claude"),
        ("dim", "  session 001 · 0 messages"),
        ("err", "  ? what are we building?"),
        ("err", "  ? which files matter?"),
        ("dim", "  no context carried over"),
    ]
    img = term_card(img, [96, 700, 984, 1272], "~/acme-app  new session", lines, RED,
                    reveal=ease(seg(t, 0.1, 1.15)), dim=0.72, lh=62, fs=29)
    d = ImageDraw.Draw(img, "RGBA")
    k = seg(t, 2.45, 0.4)
    if k > 0:  # cut to black before the memory beat
        img.alpha_composite(Image.new("RGBA", (W, H), (0, 0, 0, int(255 * k))))
    return img


def _pipeline_card(img, box, title, sub, accent, k, local, idx):
    d = ImageDraw.Draw(img, "RGBA")
    x0, y0 = box[0], int(box[1] + (1 - k) * 70)
    x1, y1 = box[2], y0 + (box[3] - box[1])
    rr(d, [x0, y0, x1, y1], 26, fill=PANEL + (int(250 * k),),
       outline=accent + (int(120 * k),), width=2)
    d.rounded_rectangle([x0 + 18, y0 + 18, x0 + 26, y1 - 18], radius=4, fill=accent + (int(210 * k),))
    d.text((x0 + 52, y0 + 34), title, font=F("mono", 30), fill=accent + (int(245 * k),))
    d.text((x0 + 52, y0 + 92), sub, font=F("monoreg", 25), fill=TXT + (int(225 * k),))
    # step badge
    d.text((x1 - 52, y0 + 40), f"0{idx}", font=F("bold", 40), fill=(255, 255, 255, int(70 * k)), anchor="ra")
    return img


def scene_memory(t, img):
    """3-9s: capture -> compress -> inject."""
    local = t - 3.0
    img = paste_glow(img, GLOW_VIOLET, 540, 980, 0.85, 0.4)
    steps = [
        ("capture", "tool calls · edits · decisions", CYAN),
        ("compress", "semantic summaries, not raw logs", VIOLET),
        ("inject", "relevant context → the next session", GREEN),
    ]
    y0, ch, gap = 620, 196, 84
    for i, (title, sub, col) in enumerate(steps):
        k = ease(seg(local, -0.12 + i * 0.32, 0.42))
        if k <= 0:
            continue
        box = [96, y0 + i * (ch + gap), 984, y0 + i * (ch + gap) + ch]
        img = _pipeline_card(img, box, title, sub, col, k, local, i + 1)
        if i < 2:  # connector
            kk = ease(seg(local, 0.2 + i * 0.32, 0.36))
            if kk > 0:
                d = ImageDraw.Draw(img, "RGBA")
                cx = 540
                top = box[3] + 14
                bot = top + int((gap - 28) * kk)
                d.line([(cx, top), (cx, bot)], fill=(255, 255, 255, int(50 * kk)), width=3)
                ay = bot - 4
                d.line([(cx - 13, ay - 12), (cx, ay + 2)], fill=MUTED + (int(200 * kk),), width=3)
                d.line([(cx + 13, ay - 12), (cx, ay + 2)], fill=MUTED + (int(200 * kk),), width=3)
    return img


def scene_restore(t, img):
    """9-15s: the next session already knows the project."""
    local = t - 9.0
    img = paste_glow(img, GLOW_CYAN, 540, 1000, 0.85, 0.45)
    lines = [
        ("cmd", "> claude --continue"),
        ("dim", "  12 sessions loaded"),
        ("ok", "  acme-app · src/auth/session.ts"),
        ("ok", "  last decision: verify(jwt) before touch()"),
        ("", "  no re-explaining"),
    ]
    img = term_card(img, [96, 690, 984, 1320], "~/acme-app  session 002", lines, GREEN,
                    reveal=ease(seg(local, 0.2, 1.7)), dim=0.95, lh=64, fs=26)
    d = ImageDraw.Draw(img, "RGBA")
    k = ease(seg(local, 2.1, 0.5))
    if k > 0:
        rr(d, [96, 1358, 96 + int(500 * k), 1428], 20, fill=PANEL + (int(245 * k),),
           outline=GREEN + (int(150 * k),), width=2)
        d.ellipse([126, 1380, 144, 1398], fill=GREEN + (int(240 * k),))
        d.text((164, 1393), "0 prompts wasted", font=F("mono", 24), fill=TXT + (int(240 * k),), anchor="lm")
    return img


def scene_numbers(t, img):
    """15-19s: 9,318 stars this week, #2."""
    local = t - 15.0
    img = paste_glow(img, GLOW_CYAN, 540, 760, 0.9, 0.45)
    d = ImageDraw.Draw(img, "RGBA")
    v = int(9318 * ease(seg(local, 0.15, 1.3)))
    d.text((540, 700), f"{v:,}", font=F("bold", 190), fill=TXT + (255,), anchor="mm")
    d.text((540, 826), "STARS  THIS  WEEK", font=F("mono", 30), fill=CYAN + (235,), anchor="mm")
    badge = ease(seg(local, 1.7, 0.5))
    if badge > 0:
        bw = int(660 * badge)
        rr(d, [540 - bw // 2, 902, 540 + bw // 2, 994], 24, fill=(251, 191, 36, int(240 * badge)))
        if badge > 0.6:
            d.text((540, 948), "#2  GITHUB  TRENDING", font=F("bold", 36), fill=(26, 22, 10, 255), anchor="mm")
    tot = ease(seg(local, 2.3, 0.6))
    if tot > 0:
        d.text((540, 1170), f"{int(113882 * ease(seg(local, 2.3, 1.1))):,}", font=F("bold", 96),
               fill=TXT + (int(250 * tot),), anchor="mm")
        d.text((540, 1252), "STARS  TOTAL  ·  +8.9%  THIS  WEEK", font=F("mono", 25),
               fill=MUTED + (int(235 * tot),), anchor="mm")
        bw2 = int(760 * ease(seg(local, 2.6, 1.0)))
        rr(d, [160, 1312, 920, 1326], 8, fill=(255, 255, 255, 24))
        rr(d, [160, 1312, 160 + bw2, 1326], 8, fill=CYAN + (int(210 * tot),))
    return img


def scene_cta(t, img):
    """19-22s: install command."""
    local = t - 19.0
    img = paste_glow(img, GLOW_CYAN, 540, 760, 0.9, 0.5 * (1 - seg(local, 2.4, 0.6)))
    d = ImageDraw.Draw(img, "RGBA")
    k = ease(seg(local, 0.0, 0.35))
    s = int(lerp(140, 176, k))
    rr(d, [540 - s // 2, 700 - s // 2, 540 + s // 2, 700 + s // 2], 46,
       fill=(12, 18, 28, 255), outline=CYAN + (210,), width=4)
    d.text((540, 700), "CM", font=F("bold", int(s * 0.46)), fill=TXT + (255,), anchor="mm")
    cmd = "npx claude-mem install"
    typed = cmd[: int(len(cmd) * ease(seg(local, 0.7, 1.1)))]
    box_y = 900
    rr(d, [90, box_y, 990, box_y + 132], 26, fill=PANEL + (250,), outline=(255, 255, 255, 30), width=2)
    d.text((128, box_y + 38), "$ " + typed, font=F("monoreg", 32), fill=TXT + (245,))
    if int(local * 3) % 2 == 0 and len(typed) < len(cmd):
        wpx = d.textlength("$ " + typed, font=F("monoreg", 32))
        d.rectangle([132 + wpx, box_y + 34, 136 + wpx, box_y + 74], fill=CYAN + (230,))
    q = ease(seg(local, 1.7, 0.6))
    if q > 0:
        d.text((540, 1110), "Apache-2.0  ·  Claude Code, Codex, Copilot, OpenCode",
               font=F("mono", 21), fill=MUTED + (int(225 * q),), anchor="mm")
    fade = seg(local, 2.55, 0.45)
    if fade > 0:
        img.alpha_composite(Image.new("RGBA", (W, H), (0, 0, 0, int(255 * fade))))
    return img


SCENES = [
    (0.0, scene_forget),
    (3.0, scene_memory),
    (9.0, scene_restore),
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
    (0.5, 2.9, "ลืมทุกครั้ง", 100, 540),
    (3.15, 8.9, "เก็บ · สรุป · ดึงกลับ", 78, 486),
    (9.3, 14.9, "จำได้เอง", 100, 500),
    (19.4, 21.8, "claude-mem.ai", 104, 460),
]

SUBS = [
    (0.6, 2.9, "ปิด session ปุ๊บ agent ลืมทุกอย่าง"),
    (3.4, 6.1, "claude-mem เก็บสิ่งที่ agent ทำ"),
    (6.1, 8.9, "สรุปให้ แล้วดึงกลับมาให้ session ถัดไป"),
    (9.4, 12.6, "เปิดใหม่กี่ครั้ง ก็ไม่ต้องเล่าโปรเจกต์ซ้ำ"),
    (12.6, 14.9, "มันจำได้เอง"),
    (15.4, 18.9, "สัปดาห์เดียว 9,318 ดาว อันดับ 2 ของ trending"),
    (19.5, 21.8, "ติดตั้งบรรทัดเดียวที่ claude-mem.ai"),
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
# MarginV 150 is the 16:9-safe default; TikTok's bottom overlay covers that strip on 9:16.
SUB_MV = os.environ.get("SUB_MARGIN_V", "150")
ASS = ASS.replace(",70,70,150,1", f",70,70,{SUB_MV},1").replace(",60,60,150,1", f",60,60,{SUB_MV},1")
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
        p = os.path.join(BUILD, f"cm_still_{t:05.2f}.png")
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
