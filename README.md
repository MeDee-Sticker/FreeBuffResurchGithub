# trending-content-pipeline

A small, reproducible pipeline that turns a weekly GitHub Trending snapshot into short vertical
promo clips (9:16, 1080x1920, 30 fps), burned-in Thai captions, and a fully synthetic score.

Everything here was built for the 2026-11-06 snapshot. The scripts are generic enough to re-run on a
new snapshot, but the numbers baked into the clips are from that one.

Agent-facing instructions — render steps, expected measurements per clip, sync and spectrum targets,
and the pitfalls — live in [SKILL.md](SKILL.md).

## What is in here

| Path | What it does |
|---|---|
| `fetch_trending.py` | Pulls the weekly trending snapshot. |
| `ai_content_radar.py` | Scores/ranks the snapshot (growth, age, language mix). |
| `render_t3code_promo.py` | Shared visual system: dark grid background, mono type, terminal cards, glow, ASS captions, ffmpeg command. Also renders the 45 s T3 Code clip. |
| `render_claude_mem_22s.py` | 22 s clip for #2 (claude-mem), imports the shared system above. |
| `render_impeccable_22s.py` | 22 s clip for #3 (impeccable), imports the shared system above. |
| `render_scrapling_22s.py` | 22 s clip for #4 (Scrapling), imports the shared system above. |
| `build_audio.py` | Procedural music bed + SFX for every clip, then muxes and loudness-normalises. No samples, no licences to clear. |
| `promo_scripts_rank2to5.md` | Shot-by-shot scripts for ranks 2-5, with the facts each clip may and may not claim. |
| `promo_t3code_script.md` | Script for the 45 s flagship clip. |
| `social_posts_2026-11-06.md` | X / LinkedIn / TikTok post set for the snapshot. |
| `build_workbook.py` | Builds the delivery spreadsheet rows. |

## Render requirements

- Python 3.10+ with `Pillow` (with FreeType) and `numpy`.
- An `ffmpeg` build with **libass** (for burned Thai captions) and `loudnorm`/`ebur128`.
  Set `FFMPEG_BIN` to its path, e.g. `export FFMPEG_BIN=/usr/bin/ffmpeg`.
  `build_audio.py` and `render_impeccable_22s.py` both honour that variable; the default is the
  Windows build under `tools/_ff/`.
- Thai fonts in `fonts/` (not committed - the bundled MS fonts are proprietary):
  `tahoma.ttf`, `tahomabd.ttf`, `consola.ttf`, `consolab.ttf`.
  Drop them in and libass picks them up via the generated `build/fonts.conf`.

Thai text is burned with libass, never with Pillow: Pillow builds without raqm break Thai vowel and
tone-mark positioning.

## Reproduce

```bash
python fetch_trending.py                 # snapshot -> data
python ai_content_radar.py               # ranking used by the scripts
python render_claude_mem_22s.py --render # 22 s clip, #2
python render_impeccable_22s.py --render # 22 s clip, #3
python render_scrapling_22s.py --render  # 22 s clip, #4
python render_t3code_promo.py --render   # 45 s clip
python build_audio.py --mux              # score + mux every clip
```

Add `--stills 1.0,6.5,12.0` to any renderer to dump PNG frames instead of encoding.

## Delivery numbers we hold ourselves to

- 1080x1920, 30 fps, H.264 + AAC 48 kHz stereo, `-movflags +faststart`.
- Integrated loudness around **-17.4 LUFS**, true peak at or below **-2 dBFS**.
- Effect hits land within ~2 frames of the picture cut.
- Music is instrumental only and dipped ~1.6 dB across 500-1800 Hz, so nothing competes with reading
  the captions, and a voice-over still has room.

## Fact guardrails

These are written into the scripts on purpose:

- On-screen numbers are `+N stars this week` and `#position` only. Total-star figures disagree
  between the trending page and the live API, so totals are not used as claims.
- No "production-ready" / "stable" claims, and no "free" claims about claude-mem (it has a hosted
  tier and self-hosted key options).
- impeccable's audit is reported as 62 deterministic rules, not as a WCAG pass guarantee.
- Re-run `fetch_trending.py` if you publish more than 3-4 days after the snapshot, and update the
  on-screen numbers, voice-over and captions together.
