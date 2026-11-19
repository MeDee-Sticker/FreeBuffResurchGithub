# RUNBOOK — ผลิตคลิป GitHub Trending รายวัน (Kopwang)

> บันทึกขั้นตอนทั้งหมดที่ใช้ทำคลิป `modern_web_guidance` (18 พ.ย. 2026) และ `claude_bughunter`
> ให้ทำซ้ำได้ทุกวันโดยไม่ต้องคิดใหม่ — ตั้งแต่ดึงบอร์ดจนถึงตั้งคิวใน Page Auto
>
> ค่าคงที่ของซีรีส์: **1080×1920 · 30 fps · 22.00 วิ (660 เฟรม) · ซับไทยเบิร์นด้วย libass · ไม่มี VO**
> รีลใช้ `<clip>_scored.mp4` (MarginV 150) · TikTok ใช้ `<clip>_tiktok_scored.mp4` (MarginV 260)
> คิวโพสต์: **รีล 19:00 · TikTok 20:00** ทุกวัน เพจ Kopwang (`page_id 1378375612029851`)

## ภาพรวมลูป 1 วัน

```
08:00  GitHub Action: ดึงบอร์ด weekly → data/trending_<วันนี้>_weekly.json + แผนวันนี้ (อัตโนมัติ)
       ↓
ในแชท  "ทำคลิปวันนี้" → เลือก repo → เขียน render_<slug>_<MMDD>.py → เรนเดอร์ 3 ไฟล์ → check_clips
       ↓
       อัปโหลดเข้า Page Auto (รีล + TikTok) → ตั้งคิวช่องว่างถัดไป 19:00/20:00 → บันทึก registry + รายงาน
```

ขั้นที่ต้องใช้สมอง (เลือก repo, เขียนแคปชัน/ซับ) ทำในแชททุกวัน; ที่เหลือเป็นคำสั่งซ้ำได้ทั้งหมด

---

## 0. เตรียมเครื่อง (ทำครั้งเดียว)

```bash
python -c "import PIL, numpy; print(PIL.__version__, numpy.__version__)"   # ต้องมีทั้งคู่
export BIN=$PWD/tools/ffmpeg-linux/ffmpeg-master-latest-linux64-gpl/bin     # ffmpeg + ffprobe ที่มี libass
export FFMPEG_BIN=$BIN/ffmpeg FFPROBE_BIN=$BIN/ffprobe
"$FFMPEG_BIN" -hide_banner -filters | grep -q ' subtitles ' || echo "ffmpeg นี้ไม่มี libass — ใช้ไม่ได้"
python scripts/prepare_fonts.py            # ถ้า fonts/ ว่าง: ก็อป TLWG มาแทน Tahoma
```

- ต้องมี `fonts/tahoma.ttf`, `tahomabd.ttf`, `consola.ttf`, `consolab.ttf` ไม่งั้นซับเป็นกล่อง (tofu)
- `ffprobe` อยู่ข้าง ๆ `ffmpeg` ไม่ได้อยู่บน PATH — `check_clips.py` หาเองจาก `FFMPEG_BIN`
- วิดีโอ/ฟอนต์/`tools/` ถูก gitignore: `*.mp4`, `build/`, `fonts/`, `tools/ffmpeg-linux/`

## 1. ดึงบอร์ด weekly (ทุกวัน)

```bash
python scripts/fetch_trending_daily.py --since weekly   # → data/trending_<วันที่>_weekly.json + .csv
python scripts/fetch_trending_daily.py                  # (ไม่บังคับ) daily ไว้หา "อันดับวันนี้" เสริม
```

**กติกาความสด: ตัวเลขใช้ได้ไม่เกิน 3 วันหลังวันที่ดึง** (`FRESH_DAYS = 3` ใน `scripts/daily_plan.py`)
ถ้าจะโพสต์ช้ากว่านั้น ต้องดึงใหม่ + แก้ตัวเลข + เรนเดอร์ซ้ำก่อนโพสต์

## 2. เลือก repo ของวันนั้น

```bash
python scripts/daily_plan.py                 # แผนวันนี้ + ตัวเลขที่ต้องใส่ในสคริปต์
python scripts/daily_plan.py --top 8 --markdown   # ตารางสำหรับแปะในรายงาน
python scripts/daily_plan.py --json          # ให้สคริปต์อื่นอ่าน
```

สคริปต์อ่าน snapshot weekly ใหม่สุด, ตัดรีโปที่อยู่ใน `data/clip_registry.json` ออกแล้ว, และ **exit 1
ถ้าบอร์ดเก่าเกิน 3 วัน** — ใช้เป็นประตูก่อนเรนเดอร์เสมอ

เกณฑ์เลือก (นอกเหนือจากอันดับ): ต้องมีมุมใหม่ที่ยังไม่ซ้ำคลิปเก่า, อ่าน README จริงแล้วอธิบายได้ว่า
"ทำอะไร · ใช้ยังไง · ผลลัพธ์ที่วัดได้", และต้องไม่ต้องพึ่งยอดดาวรวม

## 3. เขียนสคริปต์เรนเดอร์

```bash
cp render_modernweb_1118.py render_<slug>_<MMDD>.py
```

แก้เฉพาะ `CLIPS` และ `scene_numbers` (ห้ามคัดลอกโค้ดฉากใหม่ — import ระบบเดิม):

- `"out"`: `<slug>_promo_22s` (ชื่อนี้ผูกกับ `check_clips.py`, `build_audio.py`, CI)
- `"rank"` / `"gained"`: ใส่ค่าจาก `daily_plan.py` — **ห้ามพิมพ์จากความจำ**
- ฉาก 5 จังหวะคงที่: `0 hook · 3 steps · 9 payoff · 15 numbers · 19 CTA`
- ซับ `"subs"`: ทีละ 1 บรรทัด ความยาวไม่เกิน ~38 ตัวอักษร ช่วงเวลาไม่ทับกัน
- `"chips"`: 3 คำสั้น (ไลเซนส์/จำนวน/จุดเด่น) ขึ้นบนการ์ดตัวเลข
- ตัวเลขบนจอ: `+N ดาวสัปดาห์นี้` + `อันดับ N` — **ห้ามใส่ยอดดาวรวม** (ไม่ตรงกันระหว่างหน้า trending กับ API)

ตรวจว่าตัวเลขในสคริปต์ตรงกับบอร์ดจริงและยังไม่ซ้ำ:

```bash
python scripts/daily_plan.py --verify render_<slug>_<MMDD>.py
# PASS = ตัวเลขตรงบอร์ดล่าสุด · FAIL = บอร์ดเก่า / รีโปซ้ำ / ตัวเลขไม่ตรง / ชื่อคลิปซ้ำ
```

## 4. เรนเดอร์ 3 ไฟล์

```bash
python render_<slug>_<MMDD>.py --render                                   # มาสเตอร์เงียบ
python render_<slug>_<MMDD>.py --scored                                   # + สกอร์ → *_scored.mp4 (รีล)
SUB_MARGIN_V=260 python render_<slug>_<MMDD>.py --tiktok                  # → *_tiktok_scored.mp4
```

- สกอร์สร้างจาก `build_audio.py` (numpy, seeded) ครั้งแรกจะสร้าง `build/score_<slug>.wav` ให้เอง
- อย่าเรนเดอร์ TikTok ด้วยสคริปต์อื่น: ต้องเป็นภาพเดียวกัน ต่างแค่ MarginV
- ดูเฟรมด้วยตา (ตัวอักษรไทย/การ์ด/ซับ) — `--stills` ไม่มีซับ ต้องดึงจาก mp4 ที่ encode แล้ว:
  ```bash
  "$FFMPEG_BIN" -y -ss 16.5 -i <clip>_scored.mp4 -frames:v 1 -vf scale=460:-2 build/prev.png
  ```

## 5. ตรวจ spec

เพิ่ม `SPEC` ใน `scripts/check_clips.py` ก่อน (660 เฟรม · 22.0 วิ · cues `[3,9,15,19]`) แล้ว:

```bash
python scripts/check_clips.py      # ต้อง PASS: h264 · 1080x1920 · 30/1 · 660 เฟรม · 22.00 วิ
                                   #           -17.9..-17.1 LUFS · true peak ≤ -1.5 dBFS · sync ≤ 120 ms
```

`check_clips.py` จะ exit 2 ถ้ายังไม่มีไฟล์ — แปลว่ายังไม่เรนเดอร์ ไม่ใช่พัง

## 6. อัปโหลดเข้า Page Auto

แอป: `https://page-auto.kopwangth.workers.dev` (ต้องล็อกอินบัญชีเจ้าของ)

อัปโหลดต้องผ่านเบราว์เซอร์ เพราะ API ไม่มีคีย์ให้ใช้จาก CLI:

1. เปิดแท็บ Page Auto → ส่วนคลิป → `#clip-file`
2. ในแชท: `preview_upload_file` ไฟล์ในเครื่อง → `preview_playwright`:
   ```js
   await page.setInputFiles('#clip-file', '<browserPath>')
   await page.click('#btn-clip-upload')
   // รอจน #clips-upload-result ขึ้น "เข้าคลังแล้ว"
   ```
3. API ที่แอปเรียก (ไว้ตรวจ/ทำซ้ำด้วยมือ):
   - `POST /api/uploads/video` (multipart `file`, เสริม `thumb`) → `{path, thumb_path, bytes}`
   - `POST /api/clips {path, name, thumb}` → คลังคลิป (ได้ `id`)
   - ตรวจขนาดจริงด้วย Range request: ต้องได้ **206** และ `content-range` ตรงกับขนาดไฟล์ในเครื่อง
4. อัปโหลด **2 ไฟล์ต่อคลิป**: `*_scored.mp4` (รีล) และ `*_tiktok_scored.mp4` (TikTok)

## 7. ตั้งคิว

```http
POST /api/posts          {page_id, message, media_type:"reel", video_url, video_path, scheduled_at}
POST /api/tiktok/posts   {message, clip_id, scheduled_at}
GET  /api/posts?media_type=reel&limit=200     # ไล่คิวกันซ้ำ
GET  /api/tiktok/posts                        # คืน {posts:[...]}
```

- หา "ช่องว่างถัดไป" จากคิวจริงก่อนสร้างโพสต์: รีล 19:00 / TikTok 20:00
- โพสต์ภาพกับรีลเวลาเดียวกันได้ (เกิดประจำ) — เช็คเฉพาะ `media_type:'reel'` และ TikTok
- หลังสร้างแล้วไล่คิวซ้ำว่าไม่มีรายการซ้ำวัน/เวลาเดิม
- `scheduled_at` เป็นเวลาไทยแบบไม่มี offset (`2026-11-22T19:00`) ตามที่แอปรับ

## 8. บันทึกผล (ปิดลูป)

```bash
python scripts/daily_plan.py --record \
  --repo <owner/name> --out <slug>_promo_22s --renderer render_<slug>_<MMDD>.py \
  --clip-ids <id รีล>,<id tiktok> --reel-post <id> --tiktok-post <id> \
  --slot 2026-11-23T19:00,2026-11-23T20:00 --note "+N weekly #R"
```

แล้วอัปเดต `github_weekly_<วันที่>.md`: บล็อค "คลิปที่ทำจากบอร์ดนี้แล้ว" (ขนาดไฟล์ · ผล check ·
ตัวเลขบนจอ · วันหมดอายุของตัวเลข · ข้อห้ามพูด) และหัวข้อ "ทำคลิปไปแล้ว / อย่าซ้ำ"

Commit (เมื่อสั่ง): สคริปต์เรนเดอร์ + `SPEC` + registry + รายงาน + `git add -f *.mp4` ตามแบบเดิม
ก่อน commit ตรวจ `git ls-files | grep -E '\.(mp4|exe|zip|ttf|wav)$'` ต้องว่าง (mp4 อยู่ใน gitignore)

## 9. อะไรทำเองทุกวัน vs อะไรต้องสั่งในแชท

| งาน | ใครทำ | เวลา |
|---|---|---|
| ดึงบอร์ด weekly + เขียนแผนวันนี้ | GitHub Action `daily-trending.yml` | 08:00 ทุกวัน |
| เลือก repo + เขียนสคริปต์/ซับ/แคปชัน | ในแชท (สั่ง "ทำคลิปวันนี้") | ~30 นาที |
| เรนเดอร์ + check + ดูเฟรม | ในแชท / คำสั่งใน §4–5 | ~10 นาที |
| อัปโหลด + ตั้งคิว + บันทึก registry | ในแชท (ต้องล็อกอิน Page Auto) | ~10 นาที |

Action ทำได้แค่สองขั้นแรก เพราะการเรนเดอร์/อัปโหลดต้องใช้สมองเขียน copy และต้องมี session ของเจ้าของ
ถ้าอยากให้ทั้งลูปจบในคำสั่งเดียวบนเครื่องตัวเอง ใช้ `scripts/daily_plan.py` เป็นประตูแล้วต่อคำสั่ง §4–5

## 10. ข้อผิดพลาดที่เคยเจอ

- **`Failed to load fontconfig fonts!`** → `build/fonts.conf` ไม่ถูกสร้าง; ตรวจ `fonts/` และรันใหม่
- **`OSError: cannot open resource`** → ฟอนต์หาย; `python scripts/prepare_fonts.py`
- **ดึงเฟรมเป็น JPEG ไม่ได้** (`Non full-range YUV`) → ใช้ PNG เท่านั้น
- **`ffprobe: not found`** → ตั้ง `FFPROBE_BIN` หรือวางไว้ข้าง `FFMPEG_BIN`
- **true peak เกิน -1.5** → loudnorm overshoot; ลดระดับเพลงของคลิปนั้นแล้ววัดใหม่ (อย่า remux ทีละไฟล์)
- **ตัวเลขบนจอไม่ตรงบอร์ด** → `daily_plan.py --verify` จับได้ก่อนเรนเดอร์; ถ้าเลย 3 วันแล้วให้ดึงใหม่ทั้งหมด
- **ชื่อคลิปซ้ำ** → `check_clips.py`/`build_audio.py` ผูกด้วยชื่อ string; ตั้ง `out` ใหม่ทุกวัน
