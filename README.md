# trending-content-pipeline

A small, reproducible pipeline that turns a weekly GitHub Trending snapshot into short vertical
promo clips (9:16, 1080x1920, 30 fps), burned-in Thai captions, and a fully synthetic score.

Everything here was built for the 2026-11-06 snapshot. The scripts are generic enough to re-run on a
new snapshot, but the numbers baked into the clips are from that one.

Agent-facing instructions — render steps, expected measurements per clip, sync and spectrum targets,
and the pitfalls — live in [SKILL.md](SKILL.md).

## Watch the result

The clips themselves are not in Git (see `.gitignore`). They ride as release assets:
[**snapshot-2026-11-06**](https://github.com/MeDee-Sticker/FreeBuffResurchGithub/releases/tag/snapshot-2026-11-06)
has all five scored encodes — 1080x1920, Thai captions burned in, about 7.3 MB in total — so you can
watch them without rendering anything.

## What is in here

| Path | What it does |
|---|---|
| `fetch_trending.py` | Builds the weekly workbook rows, downloading the trending page when `trending.html` is absent. |
| `scripts/fetch_trending_daily.py` | Fetches the live trending page and writes a dated snapshot to `data/` (`trending_<date>_<window>.json` plus a CSV twin) with its metadata. No hand-downloaded HTML needed. |
| `ai_content_radar.py` | Scores/ranks the snapshot (growth, age, language mix). |
| `render_t3code_promo.py` | Shared visual system: dark grid background, mono type, terminal cards, glow, ASS captions, ffmpeg command. Also renders the 45 s T3 Code clip. |
| `render_claude_mem_22s.py` | 22 s clip for #2 (claude-mem), imports the shared system above. |
| `render_impeccable_22s.py` | 22 s clip for #3 (impeccable), imports the shared system above. |
| `render_scrapling_22s.py` | 22 s clip for #4 (Scrapling), imports the shared system above. |
| `render_hallmark_22s.py` | 22 s clip for #5 (hallmark), imports the shared system above. |
| `render_trending_1109.py` | 2026-11-09 series: five 22 s clips for that day's trending top five, one data-driven spec per repo. |
| `tiktok_drafts_2026-11-09.md` | 2026-11-09 copy paired per clip: TikTok caption, hashtags, pinned comment and the claims each clip may not make. |
| `reels_captions_2026-11-09.md` | Same five clips for Reels, opened from a different angle, with cover text and first comment. |
| `captions_clip_library_2026-11-09.md` | Captions for the two library clips outside that series (Freebuff topic-to-clip, E-book), TikTok and Reels. |
| `build_audio.py` | Procedural music bed + SFX for every clip, then muxes and loudness-normalises. No samples, no licences to clear. |
| `scripts/render_tiktok.py` | Platform cut: re-renders all five with the burned captions lifted to `MarginV 260`, clear of TikTok's bottom UI. |
| `promo_scripts_rank2to5.md` | Shot-by-shot scripts for ranks 2-5, with the facts each clip may and may not claim. |
| `promo_t3code_script.md` | Script for the 45 s flagship clip. |
| `social_posts_2026-11-06.md` | X / LinkedIn / TikTok post set for the snapshot. |
| `short_video_posts_2026-11-06.md` | TikTok and Reels copy for all five clips, with a 7-day posting order. |
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
python scripts/fetch_trending_daily.py   # live snapshot -> data/trending_<date>_daily.json
python scripts/fetch_trending_daily.py --since weekly   # same, weekly window
python fetch_trending.py                 # weekly workbook rows (fetches the page if trending.html is missing)
python ai_content_radar.py               # ranking used by the scripts
python render_claude_mem_22s.py --render # 22 s clip, #2
python render_impeccable_22s.py --render # 22 s clip, #3
python render_scrapling_22s.py --render  # 22 s clip, #4
python render_hallmark_22s.py --render   # 22 s clip, #5
python render_t3code_promo.py --render   # 45 s clip
python build_audio.py --mux              # score + mux every clip
```

Add `--stills 1.0,6.5,12.0` to any renderer to dump PNG frames instead of encoding.

Every frame of the 2026-11-09 series carries the page mark in the top-left corner: 96 px tall, 60 px
in from both edges, with rounded corners and a soft shadow so it reads on the dark grid.
`render_trending_1109.py` loads it from `assets/logo.png`; set `PAGE_LOGO` to use another file, or
`PAGE_LOGO_HEIGHT` / `PAGE_LOGO_PAD` to resize and move it. A missing file only warns and renders
without the mark, so CI stays green if the asset is dropped.

Every renderer honours two env vars on top of `FFMPEG_BIN`: `SUB_MARGIN_V` (bottom margin for the
burned subtitles, default 150) and `OUT_NAME` (output path). `python scripts/render_tiktok.py` uses
them to produce `<clip>_tiktok_scored.mp4` at `MarginV 260` — same picture, same score, captions
lifted clear of TikTok's bottom overlay.

## Delivery numbers we hold ourselves to

- 1080x1920, 30 fps, H.264 + AAC 48 kHz stereo, `-movflags +faststart`.
- Integrated loudness around **-17.5 LUFS**, true peak at or below **-1.5 dBFS** (most clips land at
  -3.4 or lower; loudness normalisation can overshoot on some beds — see SKILL.md).
- Effect hits land within ~2 frames of the picture cut.
- Music is instrumental only and dipped ~1.6 dB across 500-1800 Hz, so nothing competes with reading
  the captions, and a voice-over still has room.

## Fact guardrails

These are written into the scripts on purpose:

- On-screen numbers are `+N stars this week` and `#position` only. Total-star figures disagree
  between the trending page and the live API, so totals are not used as claims. The 2026-11-09
  series uses `+N stars today` with the daily rank instead, because two of those repos are missing
  from that day's weekly list and mixing the two windows would misstate both.
- No "production-ready" / "stable" claims, and no "free" claims about claude-mem (it has a hosted
  tier and self-hosted key options).
- impeccable's audit is reported as 62 deterministic rules, not as a WCAG pass guarantee.
- Re-run `fetch_trending.py` if you publish more than 3-4 days after the snapshot, and update the
  on-screen numbers, voice-over and captions together.
