# เทรนด์ AI agent ที่แรงตอนนี้ · สำรวจ 10 พ.ย. 2026

> ตัวเลขทั้งหมดดึงสดจาก `github.com/trending` (daily + weekly) และ GitHub API ในวันเดียวกัน
> ใช้กติกาเดิมของช่อง: **+N ดาววันนี้/สัปดาห์นี้ + อันดับ** เท่านั้น — ไม่พูดยอดดาวรวม
> ตัวเลขพวกนี้หมดอายุเร็ว ใช้ได้ไม่เกิน 3–4 วันหลังเก็บ snapshot

## กลุ่ม A — มีสัญญาณ trending ยืนยัน ทำคลิปได้เลย

| รีโป | สัญญาณ | อายุรีโป | ไลเซนส์ | ทำไมน่าแมส |
|---|---|---|---|---|
| `vercel-labs/agent-desktop` | **+12,120 ดาวสัปดาห์นี้ · อันดับ 2 weekly** | 264 วัน | Apache-2.0 | computer-use CLI ให้ agent คุมหน้าจอคอม ไม่ใช่แค่เบราว์เซอร์ — ต่อยอดจาก agent-browser ที่เพิ่งลงไปแล้ว ทีมเดียวกัน |
| `cloudflare/security-audit-skill` | **+10,695 ดาวสัปดาห์นี้ · อันดับ 12 weekly** | 145 วัน | MIT | สกิลให้ coding agent ไล่ตรวจความปลอดภัยหลายเฟส พร้อมขั้นตรวจยืนยันแยก — คนกลัว agent แตะ prod ตรงกลุ่ม |
| `garrytan/gbrain` | **+216 ดาววันนี้ · อันดับ 6 daily** | 219 วัน | MIT | "สมอง" ส่วนตัวสาย OpenClaw/Hermes ของ Garry Tan — มุมคนมีชื่อในวงการ |
| `homeassistant-ai/ha-mcp` | **+31 ดาววันนี้ · อันดับ 10 daily** | 422 วัน | MIT | MCP ให้สั่ง Home Assistant ด้วย Claude/ChatGPT — เล็กแต่ตรงกลุ่มสมาร์ทโฮม |

**ฮุกที่ใช้ได้**

- agent-desktop: `agent ไม่ได้ถ่ายภาพหน้าจอแล้วเดาพิกเซล — มันอ่าน accessibility tree ของแอป`
- security-audit-skill: `ให้ agent ตรวจช่องโหว่แทน แล้วมีขั้นตรวจซ้ำว่าไม่ได้มั่ว`
- gbrain: `คนที่Seed สตาร์ทอัพ YC เอา agent มาเป็น "สมอง" ส่วนตัวยังไง`
- ha-mcp: `สั่งไฟในบ้านด้วยภาษาคน ผ่าน MCP — ไม่ต้องเปิดแอป Home Assistant`

## กลุ่ม B — เรื่องดี ตัวเลขยังเบา (เก็บไว้ทำ evergreen)

| รีโป | ข้อมูลรีโป | มุมเล่า |
|---|---|---|
| `nano-muse/nanoMuse` | 3,360 ดาว · 48 วัน · GPL-3.0 | personal agent ตัวเดียวคุมมือถือ+คอม ปิดแอปแล้วยังทำงานต่อ |
| `amosblomqvist/learnharness` | 7,711 ดาว · 25 วัน · AGPL-3.0 | agent harness สำหรับ "เรียนเรื่องยาก" — ตรงเทรนด์ harness |
| `ranxianglei/billion-context` | 5,740 ดาว · 96 วัน | บีบ context ให้ session ยาวเป็นเดือนไม่หลุด |
| `adongwanai/AgentGuide` | 11,801 ดาว · CC-BY-4.0 | คู่มือ agent harness / context engineering (ภาษาจีน) — ใช้เป็นแหล่งอ้างอิงได้ |

## กลุ่ม C — เพิ่งทำคลิปไปแล้ว อย่าซ้ำใน 2 สัปดาห์นี้

`anthropics/skills` (+1,038 วันนี้ · อันดับ 1) · `milind-soni/OpenMausBot` (+1,587 · อันดับ 11) ·
`vercel-labs/agent-browser` (+916 · อันดับ 7) · `meta/astryx` (+3,278 · อันดับ 2) ·
`Nutlope/hallmark` · `pingdotgg/t3code` · `D4Vinci/Scrapling` · `thedotmack/claude-mem`

## ข้อควรระวังเวลาเขียนแคปชัน

1. **ห้ามพูดยอดดาวรวม** — ใช้เฉพาะ `+N ดาววันนี้/สัปดาห์นี้` กับ `อันดับ N`
2. **AGPL-3.0 / GPL-3.0** (nanoMuse, learnharness) — ห้ามพูดว่า "ฟรีใช้เชิงพาณิชย์ได้ทุกที่" ต้องบอกว่าเป็น copyleft
3. **อย่าเคลมแทนที่ของเดิม** — agent-desktop ไม่ใช่ "แทน agent-browser" และ security-audit-skill ไม่ได้ "กันแฮกได้ทุกเคส"
4. `cloudflare/security-audit-skill` เป็นสกิล ไม่ใช่ผลิตภัณฑ์ — ต้องมี coding agent ติดตั้งก่อนจึงใช้ได้

## ถ้าจะเอาเข้าคิว 17–21 พ.ย.

- **17 พ.ย. TikTok 20:00** = `agent-desktop` (รีลวันนั้นยังเป็น MCP)
- **18 พ.ย. TikTok 20:00** = `security-audit-skill` (รีลวันนั้นยังเป็น prompt=ข้อมูล)
- สคริปต์และแคปชันเต็มอยู่ใน [`next_batch_2026-11-17_to_21.md`](next_batch_2026-11-17_to_21.md) หัวข้อ 6–7

ที่เหลือในคิวเดิม (MCP / prompt=context / คลิปเดียว 3 ชิ้น / ตั้งราคาสินค้าดิจิทัล / ตรวจงาน AI) ยังใช้ได้ ไม่ชนกับสองตัวนี้
