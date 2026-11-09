"""Render the TikTok cut of every clip: same picture and score, captions lifted off the app's bottom rail.

TikTok paints its description and action rail over the bottom strip of a 9:16 frame, which is exactly
where the default MarginV 150 puts the burned subtitles. This re-renders each clip with
SUB_MARGIN_V=260, keeps the silent master in build/, then muxes the existing score so loudness and
cue timing stay identical to the Reels/YouTube cut.

Usage:
  python scripts/render_tiktok.py            # all five clips -> <clip>_tiktok_scored.mp4
  python scripts/render_tiktok.py cm t3      # named clips only
  SUB_MARGIN_V=300 python scripts/render_tiktok.py t3
"""
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
sys.path.insert(0, ROOT)

MARGIN_V = os.environ.get("SUB_MARGIN_V", "260")
# script, output basename, score, renderer args
CLIPS = {
    "cm": ("render_claude_mem_22s.py", "claude_mem_promo_22s", "score_cm.wav", ()),
    "imp": ("render_impeccable_22s.py", "impeccable_promo_22s", "score_imp.wav", ()),
    "scr": ("render_scrapling_22s.py", "scrapling_promo_22s", "score_scr.wav", ()),
    "hall": ("render_hallmark_22s.py", "hallmark_promo_22s", "score_hall.wav", ()),
    "t3": ("render_t3code_promo.py", "t3code_promo_45s", "score_t3.wav", ()),
    # 2026-11-09 series: one renderer, five specs, so each clip is picked by name
    "sherlock": ("render_trending_1109.py", "sherlock_promo_22s", "score_sh.wav", ("sherlock",)),
    "mausbot": ("render_trending_1109.py", "openmausbot_promo_22s", "score_mb.wav", ("mausbot",)),
    "astryx": ("render_trending_1109.py", "astryx_promo_22s", "score_ax.wav", ("astryx",)),
    "agentbr": ("render_trending_1109.py", "agent_browser_promo_22s", "score_ab.wav", ("agentbr",)),
    "skills": ("render_trending_1109.py", "anthropics_skills_promo_22s", "score_sk.wav", ("skills",)),
}


def render(slug):
    script, base, score, extra = CLIPS[slug]
    silent = os.path.join("build", f"{base}_tiktok.mp4")
    env = dict(os.environ, SUB_MARGIN_V=MARGIN_V, OUT_NAME=silent)
    print(f"[{slug}] render {silent} at MarginV {MARGIN_V}", flush=True)
    rc = subprocess.run([sys.executable, script, "--render", *extra], env=env).returncode
    if rc != 0:
        return rc
    score = os.path.join("build", score)
    if not os.path.exists(score):
        print(f"[{slug}] {score} missing, rebuilding the score set", flush=True)
        rc = subprocess.run([sys.executable, "build_audio.py"], env=env).returncode
        if rc != 0:
            return rc
    import build_audio  # needs FFMPEG_BIN; imported here so --help does not require ffmpeg

    out = f"{base}_tiktok_scored.mp4"
    print(f"[{slug}] mux -> {out}", flush=True)
    return build_audio.mux(silent, score, out)


if __name__ == "__main__":
    wanted = sys.argv[1:] or list(CLIPS)
    unknown = [w for w in wanted if w not in CLIPS]
    if unknown:
        sys.exit(f"unknown clip(s): {', '.join(unknown)} — pick from {', '.join(CLIPS)}")
    bad = 0
    for slug in wanted:
        bad |= render(slug) != 0
    sys.exit(1 if bad else 0)
