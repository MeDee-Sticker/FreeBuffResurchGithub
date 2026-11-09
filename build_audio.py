"""Procedural score + sound design for the two promo clips (no downloads, no licences to clear).

Design intent ("must not fight the subtitles"):
  - instrumental only, no vocals, nothing that reads as words
  - mid-range (500-2000 Hz, the speech band) pulled back ~2.5 dB so it leaves room for a VO later
  - low-passed at 7.5 kHz: no bright hiss over Thai text
  - music sits ~6-8 dB under the effect hits, which land on the picture cuts

Usage:
  python build_audio.py --build            # writes build/score_*.wav
  python build_audio.py --mux              # muxes the scored mp4s
"""
import os
import subprocess
import sys
import wave

import numpy as np

SR = 48000
# subprocess on Windows needs an absolute path here; set FFMPEG_BIN to override (e.g. on Linux)
FF = os.environ.get("FFMPEG_BIN") or os.path.abspath(
    "tools/_ff/ffmpeg-9.0.2-essentials_build/bin/ffmpeg.exe")
rng = np.random.default_rng(20261106)

# ------------------------------------------------------------------ helpers
def filt(x, fc, kind="lp", order=2):
    """Zero-phase FFT shelf/one-pole-style filter (no scipy needed)."""
    n = len(x)
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(n, 1 / SR)
    f = np.maximum(f, 1e-6)
    if kind == "lp":
        m = 1 / np.sqrt(1 + (f / fc) ** (2 * order))
    elif kind == "hp":
        m = 1 / np.sqrt(1 + (fc / f) ** (2 * order))
    else:  # band dip
        lo, hi, depth_db = fc
        c = np.sqrt(lo * hi)
        w = np.log2(f / c) / (np.log2(hi / lo) / 2)
        m = 1 - (1 - 10 ** (-depth_db / 20)) * np.exp(-(w**2) / 0.6)
    return np.fft.irfft(X * m, n)


def adsr(n, a, rel, curve=2.0):
    e = np.ones(n)
    na = max(1, int(a * SR))
    e[:na] = np.sin(np.linspace(0, np.pi / 2, na)) ** 2
    nr = max(1, int(rel * SR))
    nr = min(nr, n // 2)
    e[-nr:] *= np.cos(np.linspace(0, np.pi / 2, nr)) ** curve
    return e


def pad_note(f, dur, gain):
    n = int(dur * SR)
    t = np.arange(n) / SR
    sig = np.zeros(n)
    for h in range(1, 10):
        amp = 1.0 / (h**1.15)
        for det, dg in ((-0.0035, 0.5), (0.0035, 0.5)):
            sig += amp * dg * np.sin(2 * np.pi * f * h * (1 + det) * t + rng.uniform(0, 6.28))
    sig *= adsr(n, 0.30, 0.55) * gain
    return sig


def kick(dur=0.34, gain=1.0):
    n = int(dur * SR)
    t = np.arange(n) / SR
    # 46 Hz is inaudible on a phone speaker; 62 Hz keeps the thump on small drivers
    f = 62 + 70 * np.exp(-t / 0.030)
    ph = 2 * np.pi * np.cumsum(f) / SR
    body = np.sin(ph) * np.exp(-t / 0.12)
    click = rng.standard_normal(n) * np.exp(-t / 0.004) * 0.25
    return filt((body + click) * gain, 220)


def hat(gain=1.0):
    n = int(0.055 * SR)
    t = np.arange(n) / SR
    s = rng.standard_normal(n) * np.exp(-t / 0.014)
    return filt(s, 6500, "hp") * gain


def pluck(f, dur=0.55, gain=1.0):
    """Short mid-register motif note: the part a phone speaker can actually reproduce."""
    n = int(dur * SR)
    t = np.arange(n) / SR
    s = np.zeros(n)
    for h, a in ((1, 1.0), (2, 0.45), (3, 0.22), (4, 0.1)):
        s += a * np.sin(2 * np.pi * f * h * t) * np.exp(-t / (0.22 / h))
    s += 0.12 * rng.standard_normal(n) * np.exp(-t / 0.004)
    return filt(s, 6000) * gain


def bass_note(f, dur, gain):
    n = int(dur * SR)
    t = np.arange(n) / SR
    s = np.sin(2 * np.pi * f * t) + 0.18 * np.sin(4 * np.pi * f * t)
    return s * adsr(n, 0.02, 0.16) * gain


def whoosh(dur=0.62, gain=1.0):
    n = int(dur * SR)
    t = np.arange(n) / SR
    nz = rng.standard_normal(n)
    body = filt(nz, 900) + 0.5 * filt(nz, 2600, "hp")
    env = np.exp(-((t - dur * 0.42) ** 2) / (2 * (dur * 0.19) ** 2))
    return body * env * gain


def impact(dur=1.0, gain=1.0):
    n = int(dur * SR)
    t = np.arange(n) / SR
    sub = np.sin(2 * np.pi * (70 * t - 6 * t**2)) * np.exp(-t / 0.28)
    thump = rng.standard_normal(n) * np.exp(-t / 0.05)
    crack = rng.standard_normal(n) * np.exp(-t / 0.012)
    s = sub + 0.40 * filt(thump, 1200) + 0.22 * filt(crack, (700, 3200, 0.0), "dip") * 0
    s = s + 0.30 * filt(crack, 3000, "hp")
    return filt(s, 4200) * gain


def riser(dur=1.5, gain=1.0):
    n = int(dur * SR)
    t = np.arange(n) / SR
    p = t / dur
    nz = rng.standard_normal(n)
    sweep = filt(nz, 1800) * 0.6 + np.sin(2 * np.pi * np.cumsum(180 + 720 * p**2) / SR) * 0.4
    env = p**2.2
    return filt(sweep * env, 5000) * gain


def tick(f=1750, gain=1.0):
    n = int(0.05 * SR)
    t = np.arange(n) / SR
    s = np.sin(2 * np.pi * f * t) * np.exp(-t / 0.012)
    s += 0.3 * rng.standard_normal(n) * np.exp(-t / 0.003)
    return filt(s, 6000) * gain


def click(gain=1.0):
    n = int(0.035 * SR)
    t = np.arange(n) / SR
    s = rng.standard_normal(n) * np.exp(-t / 0.006)
    return (filt(s, 2400, "hp") * 0.8 + filt(s, 700) * 0.5) * gain


def bell(f=880, dur=1.1, gain=1.0):
    n = int(dur * SR)
    t = np.arange(n) / SR
    s = np.zeros(n)
    for h, a, d in ((1, 1.0, 0.55), (2.01, 0.42, 0.32), (3.02, 0.18, 0.2)):
        s += a * np.sin(2 * np.pi * f * h * t) * np.exp(-t / d)
    return s * gain


def add(buf, sig, t, gain=1.0):
    i = int(round(t * SR))
    if i < 0:
        sig = sig[-i:]
        i = 0
    n = min(len(sig), buf.shape[0] - i)
    if n > 0:
        buf[i:i + n, 0] += sig[:n] * gain
        buf[i:i + n, 1] += sig[:n] * gain


# ------------------------------------------------------------------ music bed
CHORDS = {
    "Am": ([220.00, 261.63, 329.63], 55.00),
    "F":  ([174.61, 220.00, 261.63], 43.65),
    "C":  ([261.63, 329.63, 392.00], 65.41),
    "G":  ([196.00, 246.94, 293.66], 49.00),
}
PROG = ["Am", "F", "C", "G"]


def bed(dur, bpm, kick_beats, hat_div, level=1.0):
    n = int(dur * SR)
    out = np.zeros((n, 2))
    beat = 60.0 / bpm
    bar = beat * 4
    nb = int(np.ceil(dur / bar))
    padL = np.zeros(n)
    padR = np.zeros(n)
    for b in range(nb):
        name = PROG[b % len(PROG)]
        notes, root = CHORDS[name]
        t0 = b * bar
        for i, f in enumerate(notes):
            g = 0.52 if i == 0 else 0.36
            note = pad_note(f, bar * 1.08, g)
            j = int(t0 * SR)
            m = min(len(note), n - j)
            padL[j:j + m] += note[:m] * (1.0 + 0.06 * (i % 2))
            padR[j:j + m] += note[:m] * (1.0 - 0.06 * (i % 2))
        # bass on beat 1 and 3
        for kb in (0, 2):
            add(out, bass_note(root, beat * 0.9, 0.17), t0 + kb * beat)
        # soft kick
        if kick_beats:
            for kb in kick_beats:
                add(out, kick(0.34, 0.42), t0 + kb * beat)
        # hats
        if hat_div:
            for h in range(hat_div):
                tt = t0 + h * bar / hat_div
                add(out, hat(0.55 if h % 2 == 0 else 0.35), tt)
        # sparse motif an octave above the chord: gives mid presence without words
        for bi, off in enumerate((1.5, 3.0)):
            f_ = notes[(bi + b) % len(notes)] * 2
            add(out, pluck(f_, 0.55, 0.30), t0 + off * beat)
    # pad treatment: low-pass, speech-band dip, gentle stereo width
    padL = filt(padL, 4200)
    padR = filt(padR, 4200)
    # 250-450 Hz is the boxy zone on phone speakers; 500-1800 Hz is the speech band
    padL = filt(padL, (250, 450, 1.6), "dip")
    padR = filt(padR, (250, 450, 1.6), "dip")
    padL = filt(padL, (500, 1800, 1.6), "dip")
    padR = filt(padR, (500, 1800, 1.6), "dip")
    out[:, 0] += padL * 0.46
    out[:, 1] += padR * 0.46
    out = filt(out[:, 0], 7500), filt(out[:, 1], 7500)
    out = np.stack(out, axis=1)
    out = filt(out[:, 0], 45, "hp"), filt(out[:, 1], 45, "hp")
    return np.stack(out, axis=1) * level


def duck(mix, times, depth=0.55, pre=0.22, hold=0.10, rel=0.35):
    """Side-chain style: pull the music down just before each hit."""
    n = mix.shape[0]
    t = np.arange(n) / SR
    g = np.ones(n)
    for tt in times:
        g *= 1 - depth * np.exp(-((t - (tt - pre * 0.5)) ** 2) / (2 * (pre * 0.8) ** 2))
        g *= 1 - depth * np.exp(-((t - (tt + hold)) ** 2) / (2 * (rel * 0.7) ** 2))
    g = np.clip(g, 0.1, 1.0)
    return mix * g[:, None]


# ------------------------------------------------------------------ cue sheets
CM_CUTS = [(3.0, "whoosh"), (9.0, "impact"), (13.9, "riser"), (15.0, "impact"),
           (19.0, "whoosh"), (19.75, "typing"), (21.05, "bell")]
T3_CUTS = [(3.55, "whoosh"), (9.6, "whoosh"), (13.6, "impact"), (19.6, "whoosh"),
           (26.6, "whoosh"), (31.0, "riser"), (31.6, "impact"), (37.6, "impact"),
           (39.4, "typing")]
# impeccable (#3): same 22s shape as claude-mem so the cues read as one series
IMP_CUTS = [(3.0, "whoosh"), (9.0, "impact"), (13.9, "riser"), (15.0, "impact"),
            (19.0, "whoosh"), (19.5, "typing"), (21.05, "bell")]
# scrapling (#4): same cue grid so the 22s clips stay interchangeable
SCR_CUTS = [(3.0, "whoosh"), (9.0, "impact"), (13.9, "riser"), (15.0, "impact"),
            (19.0, "whoosh"), (19.5, "typing"), (21.05, "bell")]
# hallmark (#5)
HALL_CUTS = [(3.0, "whoosh"), (9.0, "impact"), (13.9, "riser"), (15.0, "impact"),
             (19.0, "whoosh"), (19.5, "typing"), (21.05, "bell")]
# 2026-11-09 series: five more 22s clips on the same beat sheet, so the cue grid is identical
D1109 = {
    "sh": "sherlock_promo_22s",
    "mb": "openmausbot_promo_22s",
    "ax": "astryx_promo_22s",
    "ab": "agent_browser_promo_22s",
    "sk": "anthropics_skills_promo_22s",
}
SERIES_22 = ("cm", "imp", "scr", "hall", *D1109)


def build(name, dur, bpm, cuts, kick_beats, hat_div, ticks=None, end_fade=None):
    music = bed(dur, bpm, kick_beats, hat_div)
    hit_times = [c[0] for c in cuts if c[1] in ("whoosh", "impact")]
    mix = duck(music, hit_times, depth=0.6 if name in SERIES_22 else 0.5)
    n = mix.shape[0]
    music_lvl = 0.55 if name in SERIES_22 else 0.62
    mix *= music_lvl

    for t0, kind in cuts:
        if kind == "whoosh":  # apex lands on the cut, tail follows it
            add(mix, whoosh(0.62, 1.0), t0 - 0.24, 0.55)
        elif kind == "impact":
            add(mix, impact(1.0, 1.0), t0, 0.62)
        elif kind == "riser":  # crescendo that lands on the cut
            add(mix, riser(1.45, 1.0), t0 - 1.45, 0.42)
        elif kind == "typing":
            for i in range(21):
                add(mix, click(1.0), t0 + i * 0.048, 0.075 + 0.02 * (i % 3))
        elif kind == "bell":
            add(mix, bell(880, 1.2, 1.0), t0, 0.35)
            add(mix, bell(1320, 0.9, 0.5), t0 + 0.02, 0.16)

    if ticks:
        ts, te, step = ticks
        i = 0
        tt = ts
        while tt < te:
            add(mix, tick(1500 + 26 * i, 1.0), tt, 0.085)
            tt += step
            i += 1

    if end_fade:
        a, b = end_fade
        t = np.arange(n) / SR
        g = np.clip((b - t) / (b - a), 0, 1) ** 1.4
        mix *= g[:, None]

    peak = np.abs(mix).max()
    mix *= 0.68 / peak  # headroom; loudnorm does the final level
    path = f"build/score_{name}.wav"
    data = (np.clip(mix, -1, 1) * 32767).astype("<i2")
    with wave.open(path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(data.tobytes())
    print(f"wrote {path}  {dur:.2f}s  peak_norm=0.68")
    return path


def mux(video, audio, out, target_i="-17"):
    cmd = [FF, "-y", "-hide_banner", "-loglevel", "error",
           "-i", video, "-i", audio,
           "-map", "0:v:0", "-map", "1:a:0",
           "-c:v", "copy",
           # ebur128 reports true peak (inter-sample), which runs ~0.5-1 dB above the sample peak,
           # so a TP=-3.0 target is what actually lands true peak at or below -2 dBFS.
           "-af", f"loudnorm=I={target_i}:TP=-3.0:LRA=11",
           "-c:a", "aac", "-b:a", "128k", "-ar", "48000", "-ac", "2",
           "-shortest", "-movflags", "+faststart", out]
    r = subprocess.run(cmd)
    print("mux", out, "exit", r.returncode)
    return r.returncode


if __name__ == "__main__":
    args = sys.argv[1:]
    cm = build("cm", 22.0, 100, CM_CUTS, (0, 2), 8, ticks=(15.15, 16.45, 0.08),
               end_fade=(20.9, 22.0))
    t3 = build("t3", 45.0, 120, T3_CUTS, (0, 2), 8, ticks=(31.6, 33.1, 0.06),
               end_fade=(43.4, 45.0))
    imp = build("imp", 22.0, 100, IMP_CUTS, (0, 2), 8, ticks=(15.15, 16.45, 0.08),
                end_fade=(20.9, 22.0))
    scr = build("scr", 22.0, 100, SCR_CUTS, (0, 2), 8, ticks=(15.15, 16.45, 0.08),
                end_fade=(20.9, 22.0))
    hall = build("hall", 22.0, 100, HALL_CUTS, (0, 2), 8, ticks=(15.15, 16.45, 0.08),
                 end_fade=(20.9, 22.0))
    for slug in D1109:
        build(slug, 22.0, 100, IMP_CUTS, (0, 2), 8, ticks=(15.15, 16.45, 0.08),
              end_fade=(20.9, 22.0))
    if "--mux" in args:
        mux("claude_mem_promo_22s.mp4", cm, "claude_mem_promo_22s_scored.mp4")
        mux("t3code_promo_45s.mp4", t3, "t3code_promo_45s_scored.mp4")
        mux("impeccable_promo_22s.mp4", imp, "impeccable_promo_22s_scored.mp4")
        mux("scrapling_promo_22s.mp4", scr, "scrapling_promo_22s_scored.mp4")
        mux("hallmark_promo_22s.mp4", hall, "hallmark_promo_22s_scored.mp4")
        for slug, base_name in D1109.items():
            mux(f"{base_name}.mp4", f"build/score_{slug}.wav", f"{base_name}_scored.mp4")
