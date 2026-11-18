# GitHub Trending · weekly · 2026-11-18

> ดึงสดจาก `github.com/trending?since=weekly` (บอร์ด weekly 16 รายการ) + daily 20 รายการ
> ตัวเลขที่ใช้ได้บนคลิปคือ `+N ดาวสัปดาห์นี้` และ `อันดับ N` — ห้ามใช้ยอดดาวรวม
> หมายเหตุ: GitHub API ถูกจำกัดโควตาตอนเก็บ (remaining 0) ยอดดาวรวม/อายุ/ไลเซนส์ จึงว่างไว้ — เติมได้หลังโควตารีเซ็ต (~40 นาที)

## บอร์ด weekly วันนี้

| # | รีโป | +ดาวสัปดาห์นี้ | ภาษา | สถานะกับช่องเรา | ทำอะไร |
|---|---|---|---|---|---|
| 1 | `GoogleChrome/modern-web-guidance-src` | +7,015 | TypeScript | เข้าใหม่ | Keep your coding agent up to date with the latest web best practices |
| 2 | `backnotprop/plannotator` | +2,926 | TypeScript | เข้าใหม่ | The workspace to stay in the loop and on top of agents - shape, decide, plan, annotate, review code, share wit |
| 3 | `elementalsouls/Claude-BugHunter` | +2,508 | Python | เข้าใหม่ | A Claude Code skill bundle for bug hunting and external red-team work - 82 skills, 15 slash commands, 681 disc |
| 4 | `meta/astryx` | +8,700 | TypeScript | ทำคลิปแล้ว | An open source design system that's fully customizable and agent ready |
| 5 | `we-promise/sure` | +4,786 | Ruby | เข้าใหม่ | The personal finance app for everyone (by everyone) |
| 6 | `alibaba/open-code-review` | +3,675 | Go | เข้าใหม่ | Secure, fast, efficient, battle-tested at Alibaba's scale. Hybrid architecture code review tool: deterministic |
| 7 | `google-labs-code/stitch-skills` | +1,197 | TypeScript | เข้าใหม่ | A library of Agent Skills designed to work with the Stitch MCP server. Each skill follows the Agent Skills ope |
| 8 | `tradermonty/claude-trading-skills` | +2,985 | Python | เข้าใหม่ | Claude Code skills for equity investors and traders — market analysis, technical charting, economic calendars, |
| 9 | `ChromeDevTools/chrome-devtools-mcp` | +2,948 | TypeScript | เข้าใหม่ | Chrome DevTools for coding agents |
| 10 | `anthropics/skills` | +4,847 | Python | ทำคลิปแล้ว | Public repository for Agent Skills |
| 11 | `ZhuLinsen` | +3,653 | Python | เข้าใหม่ | LLM 驱动的多市场股票智能分析系统：多源行情、实时新闻、决策看板与自动推送，支持零成本定时运行。 LLM-powered multi-market stock analysis system with multi-so |
| 12 | `mvanhorn/last30days-skill` | +1,548 | Python | เข้าใหม่ | AI agent skill that researches any topic across Reddit, X, YouTube, HN, Polymarket, and the web - then synthes |
| 13 | `ag-ui-protocol/ag-ui` | +2,773 | TypeScript | เข้าใหม่ | AG-UI: the Agent-User Interaction Protocol. Bring Agents into Frontend Applications. |
| 14 | `vercel-labs/agent-browser` | +3,429 | Rust | ทำคลิปแล้ว | Browser automation CLI for AI agents |
| 15 | `openai/codex-security` | +2,531 | TypeScript | เข้าใหม่ | OpenAI's Codex Security CLI and TypeScript SDK for finding, validating, and fixing security vulnerabilities. n |
| 16 | `dream-num/univer` | +5,845 | TypeScript | เข้าใหม่ | Build your own AI office with Univer Office SDK. Bring editing, calculation, collaboration, and file processin |

## ที่ควรทำคลิปต่อ (เรียงตามความคุ้ม)

1. **`GoogleChrome/modern-web-guidance-src`** (+7,015 · อันดับ 1) — ชุดความรู้ web best practices ที่ agent อ่านแล้วทำตาม; มุม: "ทำไมหน้าเว็บที่ agent สร้างยังช้า" ต่อเนื่องจาก astryx ได้พอดี
2. **`elementalsouls/Claude-BugHunter`** (+2,508 สัปดาห์นี้ · **+2,322 วันนี้ = อันดับ 1 daily**) — skill bundle สาย bug hunting / red team; มุม: "ให้ agent ล่าบั๊กแบบมีระเบียบ" ต่อจาก security-audit-skill แต่คนละขั้น (จับบั๊ก ≠ ตรวจช่องโหว่)
3. **`backnotprop/plannotator`** (+2,926) — workspace สำหรับคุม agent ให้อยู่ในลูป (วางแผน–ตัดสินใจ–รีวิว); มุม: "ปล่อย agent วิ่งยาวแล้วหลุด — เพราะขาดจุดรีวิว"
4. **`ChromeDevTools/chrome-devtools-mcp`** (+2,948) — MCP ให้ agent ใช้ DevTools ตรวจหน้าเว็บเอง; มุม: "agent เปิด DevTools เป็น" ต่อจาก agent-browser
5. **`openai/codex-security`** (+2,531) — CLI + SDK หา/ยืนยันช่องโหว่ของ OpenAI; มุม: เทียบกับ Cloudflare skill ที่ทำไปแล้ว (คนละแนว: rule-based vs agent)
6. **`ag-ui-protocol/ag-ui`** (+2,773) — protocol ให้ agent คุยกับ frontend; มุม: "หลังบ้าน agent แล้ว หน้าเว็บยังไม่รู้จะคุยกันยังไง"

## คลิปที่ทำจากบอร์ดนี้แล้ว

**`elementalsouls/Claude-BugHunter`** — เรนเดอร์ 18 พ.ย. 2026 (ข้อมูลบอร์ดวันเดียวกัน)
- รีล: `claude_bughunter_promo_22s_scored.mp4` (907,211 B · 22.00 วิ) · **โพสต์รีล id 189** · 18 พ.ย. 21:00
- TikTok: `claude_bughunter_promo_22s_tiktok_scored.mp4` (907,670 B · MarginV 260) · **ร่าง id 21** · clip id 81 · 18 พ.ย. 21:30
- คลังคลิป: id 80 (รีล) · 81 (TikTok) · ตรวจ Range แล้วได้ 206 ทั้งคู่
- สคริปต์เรนเดอร์: `render_bughunter_1118.py` · ผ่าน `scripts/check_clips.py` (660 เฟรม · 22.00 วิ · -17.3 LUFS · sync 25 ms)
- ตัวเลขบนจอ: +2,508 สัปดาห์นี้ อันดับ 3 · +2,322 วันนี้ daily อันดับ 1 → **ใช้ได้ถึง 21 พ.ย.** หลังนั้นต้องดึงใหม่ก่อนโพสต์ซ้ำ
- มุมที่ใช้: ตรวจโค้ดตัวเอง (security-audit-skill) ≠ ล่าจากข้างนอก (ชุดนี้) — คนละขั้นของงาน
- ห้ามพูดในแคปชัน: "ใช้แล้วเจอช่องโหว่แน่นอน" · "ยิงเป้าใครก็ได้" · รับประกันรายได้จาก bug bounty

## ทำคลิปไปแล้ว / อย่าซ้ำ
- `meta/astryx` (+8,700) · `anthropics/skills` (+4,847) · `vercel-labs/agent-browser` (+3,429)

## ของใหม่บน daily ที่น่าจับตา
- `elementalsouls/Claude-BugHunter` +2,322 (อันดับ 1) · `google-research/paper-orchestra` +1,529 (multi-agent เขียนงานวิจัย) · `NVIDIA/SkillEvaluator` +869 (ประเมิน skill ของ agent) · `mvanhorn/last30days-skill` +1,062 (สกิลค้นข้าม Reddit/X/YouTube/HN)

## หลุดจากบอร์ด weekly (เทียบ snapshot 9 พ.ย.)
`D4Vinci/Scrapling` · `Donchitos/Claude-Code-Game-Studios` · `NVIDIA/auto-ontology` · `Nutlope/hallmark` · `Renhuai123/ziwei-doushu` · `The-PR-Agent/pr-agent` · `blader/humanizer` · `github/spec-kit` · `hyprwm/Hyprland` · `jakubkrehel/skills` · `mattpocock/skills` · `max-sixty/worktrunk` · `milind-soni/OpenMausBot` · `pingdotgg/t3code` · `thedotmack/claude-mem`

อ่านคู่กับ [`ai_agent_trends_2026-11-10.md`](ai_agent_trends_2026-11-10.md) (ทริปก่อน) และ [`next_batch_2026-11-17_to_21.md`](next_batch_2026-11-17_to_21.md) (คิวที่ลงอยู่)
