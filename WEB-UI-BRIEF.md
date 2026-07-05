# v7 Build Brief — Command Center Web UI (Next.js + HeroUI Pro)

> Owner: opus build agent · Approver: เต้ · Architect: Fable
> Repo: /Users/tae279/DEV_TAE/projects/agentic-os-dashboard · Branch: `feat/web-ui` (แตกจาก feat/agentic-os-v2 — ห้ามแตะ main)

## ทำไมย้าย (ตัดสินแล้ว อย่า re-litigate)

Tae feedback: UI Streamlit "แข็งๆ ไม่สวย" + ต้องการ one-click command center. Root cause = Streamlit:
rerun model (ไม่มี transition จริง), widget boxy, ไม่มี true overlay/hover, และเป็น Python → **ใช้ HeroUI Pro/Tailark/Aceternity (React, ซื้อ lifetime) ไม่ได้เลย** ซึ่งขัด pref-purchased-ui-libs-override-minimal-dep.
ทางแก้: **UI = Next.js 14 (App Router) + Tailwind v4 + HeroUI Pro** · **Backend = FastAPI ห่อ Python modules เดิมที่ทดสอบแล้ว** (registry.py, monitors.py, chat_backend.py, ccusage logic ใน app.py) — logic ไม่เขียนใหม่ แค่เปิดเป็น HTTP/SSE. Streamlit เดิมคงไว้ที่ :8501 จนกว่า parity จะครบ (อย่าลบ).

## Interaction model (ล็อกจาก reference Raycast + research 2026-07-05 — สรุปใน task output ad1399db61c7cfa1b)

- **GRID-FIRST ไม่ใช่ palette-first** (research ยืนยัน: ~15 workflows = สแกน grid เร็วกว่าพิมพ์ค้น): **Workflows คือหน้าแรก** ไม่ใช่ metrics — launcher grid จัดหมวด (Daily / Loop / Content / Projects / อิสระ) การ์ดละ workflow: icon สี, ชื่อ, คำอธิบาย 1 บรรทัด, **คลิกเดียว = รันเลย**
- **Recents/บ่อยสุดลอยขึ้นบน** อัตโนมัติ (เก็บ count ใน dashboard-data/usage-counts.json) — ไม่ต้อง pin เอง
- Workflow ที่ต้องกรอก (เช่น Toh, ถามคลังความรู้): คลิกแล้ว **input โผล่ inline ในการ์ดนั้น** (autofocus, Enter = รัน) — ห้าม modal ซ้อน (progressive disclosure)
- **สถานะใช้สี+motion ไม่ใช่ text**: idle/running/done/error = สี + spinner→checkmark ต่อการ์ด
- **⌘K command palette** (shadcn/cmdk) เป็น**ตัวเสริม** สำหรับ keyboard muscle-memory: ค้นทุก workflow/โปรเจค/เอกสาร, recents ขึ้นก่อน
- **สถานะเป็นแถบบาง** ด้านบน (5h gauge mini + weekly + VALUE + IDLE/RUNNING chip) — ไม่ใช่การ์ดยักษ์กินครึ่งจอ · คลิกแถบ = เปิด drawer รายละเอียด (กราฟ 30 วัน, cost, integrations)
- **Right rail**: Live sessions · 📥 Decision inbox · Recent runs (คลิกอ่าน inline) — panel เดียวเลื่อนได้
- **Run แล้วเห็นสด**: SSE stream phase/text เข้า panel ล่าง + macOS/Telegram notify เดิม (backend เดิมทำอยู่แล้ว)
- **💬 Chat dock** มุมขวาล่าง (ของเดิม port มา — multi-turn --resume ผ่าน SSE)
- **Portfolio + เอกสารตามโปรเจค + AI แนะนำ**: view ที่สอง สลับด้วย tab บนซ้าย (ไม่ใช่คนละ URL ก็ได้ แต่ /portfolio route ก็ดี)

## Visual (Design OS — direction ล็อกแล้ว)

- Raycast-soft บนแบรนด์ DX: พื้น slate เข้ม (โทนเดียวกับ theme.py: #070b14 ครอบครัว) + **accent เดียว #024ada/#3d7bff แบบ surgical**
- นุ่ม ไม่แข็ง: radius 10-14px · hairline 1px rgba · เงา glow เบาเฉพาะ focal · hover ยกเบาๆ + transition 150ms · แสง radial จางๆ หลัง header
- Typography: Space Grotesk (display) · Prompt (ไทย/body) · JetBrains Mono **เฉพาะตัวเลข/data** — เลิก UPPERCASE ทุกที่ ใช้เฉพาะ label จิ๋ว
- Motion: framer-motion mount stagger เบาๆ (initial+animate — ห้าม whileInView, verify ไม่ได้)
- **Component ladder บังคับ:** shadcn เป็นฐาน → HeroUI Pro (TW v4, compound components, onPress) → Aceternity เฉพาะ hero/motion accent · ห้าม hand-roll ของที่ lib มี · หลัง shadcn init รัน `dx-premium-ui-init` (มี PATH ที่ ~/.local/bin) เพื่อผูก @tailark-pro/@aceternity registries (components.json ต้องเป็น shadcn 3.0 keyed-object — ดู ~/.config/dx/premium-ui/AGENT-POLICY.md)

## โครงไฟล์

- `web/` — Next.js app (create-next-app, TS strict, TW v4, kebab-case files)
- `server.py` — FastAPI + uvicorn (เพิ่ม dep ใน requirements.txt): endpoints
  GET /api/usage /api/sessions /api/devservers /api/projects /api/inbox /api/artifacts /api/runs /api/reco
  POST /api/run {skill_label|prompt} → SSE stream · POST /api/chat {msg, sid?} → SSE stream · POST /api/open {path} · POST /api/kill {pid}
  ทั้งหมด**ห่อฟังก์ชันเดิม** — import จาก registry.py/monitors.py/chat_backend.py/app-side helpers (ถ้า helper ติดอยู่ใน app.py ให้ย้ายไป module กลาง เช่น core.py แล้วให้ app.py import กลับ — Streamlit เดิมต้องยังรันได้)
  bind 127.0.0.1:8787 เท่านั้น (local-only, no auth by design)
- `run.sh` อัพเดท: start uvicorn + next (production: `next build && next start -p 3000`; dev ใช้ dev server)
- Launcher .command + app bundle: ชี้ :3000 เมื่อ parity เสร็จ (ขั้นสุดท้าย)

## DoD (ทุกข้อต้อง verify จริง มี screenshot/curl พิสูจน์)

1. หน้า launcher: กดปุ่ม workflow จริง 1 ตัว (DX Status) → รันจบ → ผลโชว์ + ไฟล์ลง dashboard-data/runs เหมือนเดิม
2. ⌘K เปิด/ค้น/Enter รันได้
3. Chat dock: ping → resume จำได้ (ทดสอบสั้นสุดแบบเดิม)
4. Status strip ตัวเลขตรงกับ ccusage · sessions/inbox/runs โชว์ข้อมูลจริง
5. Portfolio 11 การ์ด + เอกสารผูกโปรเจค + AI แนะนำ (อ่าน recommendations.json เดิม)
6. ธีมผ่านเกณฑ์ "ไม่แข็ง": radius นุ่ม, hover motion, ไม่มี UPPERCASE ผนังใหญ่, accent เดียว
7. Streamlit :8501 ยังเปิดได้ (ไม่พังของเดิม)
8. commit เป็นช่วงๆ บน feat/web-ui + สรุปใน HANDOFF.md

## ข้อควรระวัง

- เต้ = non-dev: ทุก label ไทย เข้าใจง่าย · ชื่อเต้ห้ามสะกด "เต้า"
- อย่าเผา quota: ทดสอบ run จริงด้วย DX Status (สั้นสุด) ครั้งเดียว + chat ping ครั้งเดียว
- next dev บน :3000 อาจชน dev server อื่น — เช็ค lsof ก่อน ใช้ 3005 ถ้าชน
- HeroUI Pro = Tailwind v4 only + no Provider + onPress (ดู heroui-pro MCP docs ได้)
