"""Build the CSV that appends every clip script to the 'Prompt Content' tab.

Column order copies the tab's existing header (A-Q) so an "append rows" import lands in the
right columns instead of shifting everything left. No header row: the tab already has one.
"""
import csv
import hashlib
import importlib
import io
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
sys.path.insert(0, ROOT)

FLOW = "Hook เปิดด้วยอาการ → 3 ขั้นตอนที่ทำตามได้ → ผลลัพธ์ที่วัดได้ → สรุป → CTA"
VOICE = "ไม่มีเสียงบรรยาย — ใช้สกอร์จาก build_audio.py (ไม่มีลิขสิทธิ์)"

# title, module, slug, page-auto reference, channel/date, duration, caption
CLIPS = [
    ("sherlock — หนึ่งชื่อ หลายบัญชี", "render_trending_1109", "sherlock", "รีล 157 · TikTok 6", "10 พ.ย. 19:00/20:00", 22, ""),
    ("OpenMausBot — บอทละเครื่อง", "render_trending_1109", "mausbot", "รีล 158 · TikTok 7", "12 พ.ย. 19:00/20:00", 22, ""),
    ("agent-browser — เบราว์เซอร์ที่ agent สั่งได้", "render_trending_1109", "agentbr", "รีล 160 · TikTok 9", "11 พ.ย. 19:00/20:00", 22, ""),
    ("astryx — design system สำหรับ agent", "render_trending_1109", "astryx", "รีล 159 · TikTok 8", "13 พ.ย. 19:00/20:00", 22, ""),
    ("anthropics/skills — โฟลเดอร์ที่สอนงาน agent", "render_trending_1109", "skills", "รีล 161 · TikTok 10", "14 พ.ย. 19:00/20:00", 22, ""),
    ("agent-desktop — agent เห็นหน้าจอคอม", "render_aiagents_1117", "ade", "TikTok 15", "17 พ.ย. 20:00", 22,
     "agent ที่คุมหน้าจอคอมได้ ไม่จำเป็นต้องถ่ายภาพจอแล้วเดาพิกเซล\n\nagent-desktop อ่านต้นไม้ accessibility ของแอป คืนมาเป็น JSON\nทุกปุ่ม ทุกช่องกรอก มี ref ให้สั่งตรงตัว\n1 ใช้ได้ทั้ง macOS Windows Linux\n2 ตัวมันไม่มีโมเดล ลูปตัดสินใจอยู่ที่ agent ของคุณ\n3 เรียกผ่าน CLI หรือ C library ก็ได้\n\nตัวรีโปเตือนเอง: snapshot กับคลิปบอร์ดมีข้อมูลส่วนตัวได้ อย่าเอาลงล็อกสาธารณะ\n\n#AIagent #ComputerUse #Vercel #คอนเทนต์ไทย #Kopwang"),
    ("security-audit-skill — ให้ agent ตรวจช่องโหว่", "render_aiagents_1117", "sec", "TikTok 16", "18 พ.ย. 20:00", 22,
     "ปล่อยให้ agent เขียนโค้ดเร็วขึ้น แล้วใครเป็นคนตรวจว่าโค้ดนั้นปลอดภัย\n\nsecurity-audit-skill สั่งให้ coding agent ตรวจเป็นเฟส ไม่ใช่ยิงคำถามเดียว\n1 แมปสถาปัตยกรรมก่อน แล้วแบ่งงานให้นักล่าแยกกันหลายตัว\n2 ข้อสงสัยทุกข้อ ต้องผ่านคนตรวจใหม่ที่พยายามหักล้างมัน\n3 ผลแยกเป็น ยืนยันแล้ว / ยังต้องตรวจ / ตกไป พร้อมรายงานที่อ้างถึงโค้ดจริง\n\nมันคือสกิลที่งอกจาก harness หาช่องโหว่ของ Cloudflare เอง ไม่ใช่โปรแกรมกดใช้\n\n#Security #AIagent #Cloudflare #คอนเทนต์ไทย #Kopwang"),
    ("MCP — ปลั๊กที่ทำให้ agent เห็นเครื่องมือ", "render_evergreen_1117", "mcp", "รีล 174", "17 พ.ย. 19:00", 22,
     "ทำไม agent ของคุณเห็นแค่ไฟล์ในโฟลเดอร์ แต่ไม่เห็นปฏิทิน ในอีเมล หรือในฐานข้อมูล\n\nเพราะมันไม่ได้ขาดความฉลาด — มันขาดทางคุยกับเครื่องมือเหล่านั้น\nMCP คือข้อตกลงกลางที่ให้แต่ละเครื่องมือประกาศความสามารถของตัวเอง\nแล้ว agent เลือกเรียกได้ตามงานที่เจอ\n\nผลลัพธ์ที่ต่าง: จาก \"ช่วยสรุปไฟล์นี้\" เป็น \"ช่วยดูตารางว่างสัปดาห์หน้าแล้วร่างนัดให้หน่อย\"\nเริ่มจากเครื่องมือที่คุณเปิดบ่อยที่สุด 1 ตัวก่อน\n\n#MCP #AIagent #Automation #คอนเทนต์ไทย #Kopwang"),
    ("prompt ที่ดีคือข้อมูล ไม่ใช่คำสั่ง", "render_evergreen_1117", "prompt", "รีล 175", "18 พ.ย. 19:00", 22,
     "เขียน prompt ยาวขึ้นแล้วผลแย่ลง — ปัญหาไม่ใช่ความยาว แต่เป็นข้อมูลที่ขาด\n\nโมเดลไม่ได้อ่านใจคุณ มันอ่านแค่สิ่งที่คุณเขียน\nถ้าไม่บอกว่าผลลัพธ์หน้าตาเป็นอย่างไร ไม่ให้ตัวอย่างที่ดี 1 ชิ้น\nและไม่บอกว่า \"ถูก\" หมายถึงอะไร — มันจะเดา แล้วคุณจะได้งานที่ต้องแก้ทั้งชิ้น\n\nก่อนเพิ่มประโยคใหม่ ถามก่อนว่า \"นี่คือข้อมูล หรือแค่ความหวัง\"\n\n#Prompt #AIทำงาน #Productivity #คอนเทนต์ไทย #Kopwang"),
    ("คลิปเดียว ทำได้ 3 ชิ้นงาน", "render_evergreen_1117", "three", "รีล 186", "19 พ.ย. 19:00", 22,
     "ถ่ายคลิปเดียวแล้วจบ แปลว่าคุณจ่ายค่าไอเดียแพงกว่าคนอื่น 3 เท่า\n\nคลิปที่ดีไม่ควรจบที่ปุ่มโพสต์\nตัด 15 วิแรกที่คนดูจบมากที่สุด เอาไปเป็น hook ของคลิปหน้า\nถอดเสียงเป็นข้อความ ก็ได้โพสต์ยาวทั้งอัน\nจับภาพนิ่ง 3 เฟรม ก็ได้ carousel สอนทีละขั้น\n\nทั้งหมดนี้ทำได้ใน 15 นาที ถ้าเลือกเฉพาะสิ่งที่ \"ไม่ต้องถ่ายใหม่\"\n\n#ทำคอนเทนต์ #Repurpose #Creatorไทย #คอนเทนต์ไทย #Kopwang"),
    ("ตั้งราคาสินค้าดิจิทัล", "render_evergreen_1117", "price", "รีล 187", "20 พ.ย. 19:00", 22,
     "ตั้งราคา 99 บาท เพราะกลัวไม่มีคนซื้อ\nแล้วคุณต้องขาย 100 คน เพื่อได้เท่ากับที่คนอื่นขายครั้งเดียว\n\nราคาไม่ใช่ตัวเลขที่ตั้งจากความกลัว\nคิดจากผลลัพธ์ที่ลูกค้าได้ คิดจากเวลาที่คุณประหยัดให้เขา\nแล้วแบ่งเป็น 3 ชั้น ให้คนเลือกตามกำลัง\n\nถ้าราคาต่ำจนต้องขายจำนวนมาก นั่นแปลว่าคุณกำลังซื้อความเหนื่อยมาทำงาน\n\n#ตั้งราคา #DigitalProduct #รายได้เสริม #คอนเทนต์ไทย #Kopwang"),
    ("ตรวจงาน AI 3 นาทีก่อนส่งลูกค้า", "render_evergreen_1117", "audit", "รีล 188", "21 พ.ย. 19:00", 22,
     "ลูกค้าไม่ได้เลิกจ้างเพราะคุณทำช้า\nเขาเลิกเพราะคุณส่งงานที่ยังไม่ได้ตรวจ\n\nAI ทำให้งานเสร็จเร็วขึ้น แต่ไม่ได้ทำให้งานถูกขึ้น\n3 นาทีก่อนกดส่ง: เช็กตัวเลขกับชื่อเฉพาะ กดลิงก์จริงทุกอัน\nดูภาพที่มือเพี้ยน และตัดประโยคที่โมเดลเติมเกินความจริง\nสุดท้าย อ่านออกเสียง — ถ้าฟังไม่เหมือนคุณ ให้แก้\n\nเช็กลิสต์ 1 หน้านี้ ใช้ซ้ำได้ทุกงาน และกันความผิดพลาดที่แพงที่สุดไว้\n\n#ตรวจงาน #AIforWork #Freelanceไทย #คอนเทนต์ไทย #Kopwang"),
]

OLDER = [
    ("t3code — พิมพ์หัวข้อ ได้คลิป", "render_t3code_promo", "t3code_promo_45s_scored.mp4", 45),
    ("claude-mem — context ข้าม session", "render_claude_mem_22s", "claude_mem_promo_22s_scored.mp4", 22),
    ("impeccable — คำสั่งแต่งงาน", "render_impeccable_22s", "impeccable_promo_22s_scored.mp4", 22),
    ("Scrapling — scraper ที่ทน anti-bot", "render_scrapling_22s", "scrapling_promo_22s_scored.mp4", 22),
    ("hallmark — กันงานหน้าตา AI", "render_hallmark_22s", "hallmark_promo_22s_scored.mp4", 22),
]


def clip_code(date, key):
    h = hashlib.sha1(key.encode("utf-8")).hexdigest().upper()[:6]
    return f"SET-{date}-{h}"


def spec_of(module, slug):
    mod = importlib.import_module(module)
    for key, c in mod.CLIPS.items():
        if isinstance(c, dict) and ("subs" in c) and (slug is None or key == slug):
            return key, c
    return slug, None


def script_of(spec):
    lines = []
    for start, end, text in spec["subs"]:
        lines.append(f"[{start:.1f}-{end:.1f} วิ] {text}")
    return "\n".join(lines)


def hooks_of(spec):
    return [h[2] for h in spec.get("head", [])][:3]


def main():
    rows = []
    for title, module, slug, ref, when, dur, caption in CLIPS:
        key, spec = spec_of(module, slug)
        if not spec:
            print("missing", module, slug)
            continue
        hooks = hooks_of(spec)
        rows.append([
            clip_code("20261116", key), "2026-11-16 15:10", f"{title} ({when})",
            hooks[0] if hooks else "", hooks[1] if len(hooks) > 1 else "", hooks[2] if len(hooks) > 2 else "",
            script_of(spec), "", FLOW, VOICE, caption, dur, ref, "", "", f"{key}_@{when}", "",
        ])

    for title, module, fname, dur in OLDER:
        try:
            mod = importlib.import_module(module)
        except Exception as exc:
            print("skip", module, exc)
            continue
        subs = getattr(mod, "SUBS", []) or []
        head = getattr(mod, "HEAD", []) or []
        script = "\n".join(f"[{s[0]:.1f}-{s[1]:.1f} วิ] {s[2]}" for s in subs if len(s) > 2)
        hooks = [h[2] for h in head if len(h) > 2][:3]
        rows.append([
            clip_code("20261106", fname), "2026-11-06 18:00", title,
            hooks[0] if hooks else "", hooks[1] if len(hooks) > 1 else "", hooks[2] if len(hooks) > 2 else "",
            script, "", FLOW, VOICE, "", dur, "", "", "", fname, "",
        ])

    with io.open("sheet_import_prompt_content.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerows(rows)
    print(f"{len(rows)} data rows, {len(rows[0])} columns -> sheet_import_prompt_content.csv")
    for r in rows[:3]:
        print(" |", r[0], "|", r[2][:40], "| hooks:", r[3][:18], "| script lines:", r[6].count(chr(10)) + 1)


if __name__ == "__main__":
    main()
