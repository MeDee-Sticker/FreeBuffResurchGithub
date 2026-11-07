---
name: rerender-trending-promo
description: Re-render the vertical promo clips from the GitHub Trending pipeline (9:16, burned Thai captions, synthetic score) and prove the output is correct against measured targets. Use when asked to re-render or rebuild a clip, score a clip, add a new clip to the series, check loudness/sync/caption problems, or verify a render before publishing.
---

# Re-render the trending promo clips

Four clips live here: `t3code_promo_45s` (flagship), `claude_mem_promo_22s` (#2),
`impeccable_promo_22s` (#3), `scrapling_promo_22s` (#4). Each has a silent master and a
`*_scored.mp4` with the music and effects muxed in.

All four are rendered by scripts that import one shared module, `render_t3code_promo.py`. That module
holds the look: dark grid background, mono type, rounded terminal cards, glow, the ASS caption styles
and the ffmpeg command. **Never copy scene code into a new file** — import the base and add scenes,
or the series drifts apart.

## 1. Setup

```bash
export FFMPEG_BIN=/path/to/ffmpeg     # build_audio.py falls back to the bundled Windows exe
python -c "import PIL, numpy; print(PIL.__version__, numpy.__version__)"
```

Requirements:

- `ffmpeg` built with **libass** (burned Thai captions), plus `loudnorm` and `ebur128`. A build
  without libass cannot run the `subtitles=` filter.
- `Pillow` and `numpy`. Pillow's raqm support is **not** required and must not be relied on — Thai
  shaping is done by libass.
- Thai fonts in `fonts/`: `tahoma.ttf`, `tahomabd.ttf`, `consola.ttf`, `consolab.ttf`. They are not
  in the repo (proprietary). Without them libass renders tofu boxes and the scene text raises
  `OSError: cannot open resource`.
- On Linux with no system fontconfig config, the renderer writes `build/fonts.conf` and exports
  `FONTCONFIG_FILE` itself. If you see `Failed to load fontconfig fonts!` in the ffmpeg log, that
  generation step did not run.

## 2. Render

```bash
python render_impeccable_22s.py --stills 1.0,6.5,12.0,17.0,20.6   # PNG frames, NO captions
python render_impeccable_22s.py --render                          # full mp4, captions burned
```

`--stills` writes scene frames only; captions are applied by ffmpeg at encode time, so stills can
never prove caption layout. To inspect captions, extract frames **from the encoded mp4**:

```bash
"$FFMPEG_BIN" -y -ss 6.5 -i impeccable_promo_22s.mp4 -frames:v 1 -vf scale=460:-2 build/prev.png
```

Use PNG. JPEG fails here with `Non full-range YUV is non-standard ... Could not open encoder`.

## 3. Score and mux

```bash
python build_audio.py --build   # writes build/score_{cm,t3,imp,scr}.wav
python build_audio.py --mux     # builds every score, then muxes all clips
```

`--mux` re-muxes all four clips and is deterministic, so it is safe to run when only one clip changed.
Music is synthesised with numpy (seeded), so there are no samples or licences to clear.

Cue sheets are the source of truth for hits: `CM_CUTS`, `T3_CUTS`, `IMP_CUTS`, `SCR_CUTS`. The three
22 s clips share the same grid — whoosh at 3.0, impact at 9.0, riser 13.9→impact 15.0, whoosh +
typing at 19.0, bell at 21.05, fade 20.9–22.0. `SERIES_22` selects the series music level and duck
depth; a new 22 s clip must be added there or it will be louder and less ducked than its siblings.

## 4. Accept the render

Expected values, measured from the shipped files:

| clip | frames | silent | scored | I (LUFS) | LRA | true peak |
|---|---|---|---|---|---|---|
| `t3code_promo_45s` | 1350 | 2,571,745 B | 3,279,523 B | -17.6 | 1.4 LU | -3.5 dBFS |
| `claude_mem_promo_22s` | 660 | 581,969 B | 927,359 B | -17.4 | 1.9 LU | -3.6 dBFS |
| `impeccable_promo_22s` | 660 | 679,198 B | 1,024,656 B | -17.5 | 1.9 LU | -3.4 dBFS |
| `scrapling_promo_22s` | 660 | 708,825 B | 1,054,403 B | -17.5 | 1.7 LU | -1.8 dBFS |
| `hallmark_promo_22s` | 660 | 714,606 B | 1,060,301 B | -17.4 | 2.0 LU | -2.9 dBFS |

```bash
BIN=$(dirname "$FFMPEG_BIN")
"$BIN/ffprobe" -v error -select_streams v:0 -count_frames \
  -show_entries stream=codec_name,width,height,r_frame_rate,nb_read_frames \
  -of default=nw=1 out.mp4
"$FFMPEG_BIN" -hide_banner -nostats -i out.mp4 -af ebur128=peak=true -f null - 2>&1 \
  | sed -n '/Summary/,$p' | grep -E "I:|LRA:|Peak:"
```

Pass conditions: 1080x1920, `h264`, `30/1`, the frame count above, `-17.6 .. -17.4 LUFS`, and a
true peak at or below `-1.5 dBFS`.

The mux targets `loudnorm=...:TP=-3.0`, but **TP is not a hard ceiling**. `ebur128` reports true peak
(4x oversampled inter-sample peak), which sits above the sample peak, and single-pass `loudnorm`
overshoots its own target on some beds: `scrapling` measures -1.8 dBFS against a -3.0 target while its
siblings land at -3.4 or lower. A sample-peak `alimiter` and `linear=false` do not fix it — both were
tried and changed nothing. Accept anything at or below -1.5 dBFS; if you need a harder ceiling, lower
the music level for that clip and re-measure. Never re-mux one clip in isolation: `--mux` regenerates
all five, so measure all five.

Spectral balance of the score (share of energy, `build/score_*.wav`):

| band | target |
|---|---|
| 0–200 Hz | 36–42 % |
| 200–500 Hz | 34–39 % |
| 500–2000 Hz | 17–19 % |
| 2000–7500 Hz | ~3 % |
| 7500 Hz+ | 5–6 % |

Anything above ~45 % below 200 Hz means the mix is inaudible on phone speakers; under ~15 % in
500–2000 Hz means it has no presence to survive a phone. Measure with:

```python
import wave, numpy as np
SR = 48000
with wave.open("build/score_imp.wav") as w:
    d = np.frombuffer(w.readframes(w.getnframes()), dtype="<i2").astype(np.float32) / 32768
d = d[::2]
S = np.abs(np.fft.rfft(d)) ** 2
f = np.fft.rfftfreq(len(d), 1 / SR)
tot = S.sum()
print(" ".join(f"{a}-{b}:{S[(f >= a) & (f < b)].sum() / tot * 100:.0f}%"
               for a, b in [(0, 200), (200, 500), (500, 2000), (2000, 7500), (7500, 20000)]))
```

Sync: every cut's effect peak must land within ~80 ms (2.5 frames) of the cut.

```python
import numpy as np, subprocess, os
SR, FF = 48000, os.environ["FFMPEG_BIN"]
cues = [3.0, 9.0, 15.0, 19.0]
x = np.frombuffer(subprocess.run([FF, "-v", "error", "-i", "impeccable_promo_22s_scored.mp4",
                                  "-ac", "1", "-ar", str(SR), "-f", "s16le", "-"],
                                capture_output=True).stdout, dtype="<i2").astype(np.float32) / 32768
w = SR // 200
n = len(x) // w
env = np.sqrt((x[:n * w].reshape(n, w) ** 2).mean(1))
print([round((max(0, int((c - .25) * 200)) + int(np.argmax(
    env[max(0, int((c - .25) * 200)):int((c + .25) * 200)]))) / 200 - c, 3) * 1000 for c in cues])
```

A pluck or SFX landing on the same frame can win the peak detector and report a 50–80 ms offset even
when the whoosh is placed correctly; whooshes are authored at `cut - 0.24 s` so their apex sits on the
cut. Cross-check the picture cut before moving audio.

## 5. Adding a clip to the series

1. Copy the shape of `render_impeccable_22s.py`: import the base module, override `base.FONTS` to
   `fonts/`, take `FF` from `FFMPEG_BIN`, reuse the ASS header verbatim (Head 96, Sub 46,
   SubSmall 40, MarginV 150).
2. Keep the 5-scene spine at 0/3/9/15/19 s so the shared cue grid still lines up.
3. Add a `*_CUTS` list and a `build(...)` call in `build_audio.py`, add the name to `SERIES_22`, add
   the `mux(...)` line.
4. Re-run the acceptance checks above and compare against its siblings, not just against zero.
5. Add the clip to three places that do not update themselves: the acceptance table in this file,
the renderer table and the reproduce block in `README.md`, and the `mux(...)` list in
`build_audio.py`. A clip that renders but is missing from the table looks verified when it is not.

## 6. Fact guardrails

These are product rules, not style preferences:

- On-screen numbers are `+N stars this week` and `#position` only. Total-star figures disagree between
  the trending page and the live API.
- No "production-ready" / "stable" claims; no "free" claim about claude-mem (hosted tier plus
  bring-your-own-key options).
- impeccable is "62 deterministic rules", never "passes WCAG".
- Scrapling is not "bypasses anti-bot everywhere" and the description must tell viewers to check
  robots.txt and the target site's terms.
- Re-run `fetch_trending.py` if publishing more than 3–4 days after the snapshot, and update
  on-screen numbers, voice-over and captions together.

## 7. Publishing

`*.mp4`, `build/`, `fonts/` and the ffmpeg builds are gitignored. Before any commit run
`git ls-files | grep -E '\.(mp4|exe|zip|ttf|wav)$'` — it must print nothing. Renders stay out of the
repo; attach them as release assets if they need to be shared.
