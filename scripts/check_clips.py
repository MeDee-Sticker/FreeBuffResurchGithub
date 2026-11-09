"""Fail the build when a rendered clip is outside the series spec in SKILL.md.

Checks, per clip: container/codec/resolution/fps, frame count, duration, integrated loudness,
true peak, and that every effect hit lands on its picture cut.

Usage:
  python scripts/check_clips.py            # checks the *_scored.mp4 files in the repo root
"""
import json
import os
import re
import subprocess
import sys

import numpy as np

FF = os.environ.get("FFMPEG_BIN") or "ffmpeg"
FP = os.environ.get("FFPROBE_BIN") or os.path.join(os.path.dirname(FF) or ".", "ffprobe")

SR = 48000
LUFS_WINDOW = (-17.9, -17.1)   # series sits at -17.4 .. -17.6
PEAK_CEILING = -1.5            # dBFS true peak; see SKILL.md on loudnorm overshoot
SYNC_TOLERANCE_MS = 120

SPEC = {
    "t3code_promo_45s_scored.mp4": {
        "frames": 1350, "duration": 45.0, "cues": [3.55, 9.6, 13.6, 19.6, 26.6, 31.6, 37.6],
    },
    "claude_mem_promo_22s_scored.mp4": {
        "frames": 660, "duration": 22.0, "cues": [3.0, 9.0, 15.0, 19.0],
    },
    "impeccable_promo_22s_scored.mp4": {
        "frames": 660, "duration": 22.0, "cues": [3.0, 9.0, 15.0, 19.0],
    },
    "scrapling_promo_22s_scored.mp4": {
        "frames": 660, "duration": 22.0, "cues": [3.0, 9.0, 15.0, 19.0],
    },
    "hallmark_promo_22s_scored.mp4": {
        "frames": 660, "duration": 22.0, "cues": [3.0, 9.0, 15.0, 19.0],
    },
    # 2026-11-09 series
    "sherlock_promo_22s_scored.mp4": {
        "frames": 660, "duration": 22.0, "cues": [3.0, 9.0, 15.0, 19.0],
    },
    "openmausbot_promo_22s_scored.mp4": {
        "frames": 660, "duration": 22.0, "cues": [3.0, 9.0, 15.0, 19.0],
    },
    "astryx_promo_22s_scored.mp4": {
        "frames": 660, "duration": 22.0, "cues": [3.0, 9.0, 15.0, 19.0],
    },
    "agent_browser_promo_22s_scored.mp4": {
        "frames": 660, "duration": 22.0, "cues": [3.0, 9.0, 15.0, 19.0],
    },
    "anthropics_skills_promo_22s_scored.mp4": {
        "frames": 660, "duration": 22.0, "cues": [3.0, 9.0, 15.0, 19.0],
    },
}


def probe(path):
    r = subprocess.run(
        [FP, "-v", "error", "-count_frames", "-show_entries",
         "stream=codec_type,codec_name,width,height,r_frame_rate,nb_read_frames,sample_rate,channels"
         ":format=duration", "-of", "json", path],
        capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(r.stderr.strip()[:400])
    data = json.loads(r.stdout)
    v = next((s for s in data.get("streams", []) if s.get("codec_type") == "video"), {})
    a = next((s for s in data.get("streams", []) if s.get("codec_type") == "audio"), None)
    return v, a, float(data.get("format", {}).get("duration", 0.0))


def loudness(path):
    r = subprocess.run([FF, "-hide_banner", "-nostats", "-i", path, "-af", "ebur128=peak=true",
                        "-f", "null", "-"], capture_output=True, text=True)
    tail = r.stderr[r.stderr.rfind("Summary:"):] if "Summary:" in r.stderr else ""
    i = re.search(r"I:\s+(-?\d+\.\d+)\s+LUFS", tail)
    p = re.search(r"Peak:\s+(-?\d+\.\d+)\s+dBFS", tail)
    if not i or not p:
        raise RuntimeError("could not read loudness summary")
    return float(i.group(1)), float(p.group(1))


def sync_offsets(path, cues):
    raw = subprocess.run([FF, "-v", "error", "-i", path, "-ac", "1", "-ar", str(SR),
                          "-f", "s16le", "-"], capture_output=True).stdout
    x = np.frombuffer(raw, dtype="<i2").astype(np.float32) / 32768
    win = SR // 200
    n = len(x) // win
    if n == 0:
        raise RuntimeError("no audio decoded")
    env = np.sqrt((x[: n * win].reshape(n, win) ** 2).mean(1))
    offs = []
    for c in cues:
        i0 = max(0, int((c - 0.25) * 200))
        i1 = min(n, int((c + 0.25) * 200))
        if i1 <= i0:
            continue
        offs.append(((i0 + int(np.argmax(env[i0:i1]))) / 200 - c) * 1000)
    return offs


def check(name, spec):
    fails = []
    v, a, dur = probe(name)
    frames = int(v.get("nb_read_frames") or 0)
    w, h = int(v.get("width") or 0), int(v.get("height") or 0)
    fps = v.get("r_frame_rate")

    if v.get("codec_name") != "h264":
        fails.append(f"codec {v.get('codec_name')} != h264")
    if (w, h) != (1080, 1920):
        fails.append(f"{w}x{h} != 1080x1920")
    if fps != "30/1":
        fails.append(f"fps {fps} != 30/1")
    if frames != spec["frames"]:
        fails.append(f"{frames} frames != {spec['frames']}")
    if abs(dur - spec["duration"]) > 0.05:
        fails.append(f"duration {dur:.3f}s != {spec['duration']}s")
    if a is None:
        fails.append("no audio stream")
    else:
        if int(a.get("sample_rate") or 0) != SR:
            fails.append(f"audio {a.get('sample_rate')} Hz != {SR}")
        if int(a.get("channels") or 0) != 2:
            fails.append(f"audio {a.get('channels')} ch != 2")

    i_lufs, peak = loudness(name)
    if not (LUFS_WINDOW[0] <= i_lufs <= LUFS_WINDOW[1]):
        fails.append(f"{i_lufs} LUFS outside {LUFS_WINDOW[0]}..{LUFS_WINDOW[1]}")
    if peak > PEAK_CEILING:
        fails.append(f"true peak {peak} dBFS above {PEAK_CEILING}")

    offs = sync_offsets(name, spec["cues"])
    worst = max((abs(o) for o in offs), default=0.0)
    if worst > SYNC_TOLERANCE_MS:
        fails.append(f"sync {worst:.0f}ms > {SYNC_TOLERANCE_MS}ms")

    print(f"{name:<38} {frames:>5} fr  {dur:>6.2f}s  {i_lufs:>6.1f} LUFS  "
          f"{peak:>5.1f} dBFS  sync {worst:>5.0f}ms  {'PASS' if not fails else 'FAIL'}")
    for f in fails:
        print(f"    - {f}")
    return not fails


def main():
    missing = [n for n in SPEC if not os.path.exists(n)]
    if missing:
        print("missing renders: " + ", ".join(missing))
        print("run the renderers and `python build_audio.py --mux` first")
        return 2
    ok = all(check(n, s) for n, s in SPEC.items())
    print("\nall clips within spec" if ok else "\nspec violations found")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
