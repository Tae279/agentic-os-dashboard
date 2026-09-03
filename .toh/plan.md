# Plan — DX Command Center v10 · "Project Radar" page + action buttons

Status: building
Created: 2026-09-02 · Author: Claude (Fable 5.1) · Owner: Tae
Repo: `~/DEV_TAE/projects/agentic-os-dashboard` (branch `feat/web-ui`, v7 Command Center = FastAPI `server.py` :8787 + Next.js `web/` :3000 HeroUI Pro)

## Goal
เต้เปิด Command Center (localhost:3000) แล้วเห็นสถานะทุกโปรเจกต์ DX ในหน้าเดียว · กดปุ่ม "รันให้เสร็จ" ที่งานค้าง → Claude Code รันจริงบน repo นั้น (ผ่าน `POST /api/run` ที่มีอยู่แล้ว) เห็น output สดในหน้าเดิม · กดปุ่ม "เปิดแอป" → เปิด prod / local dev ของโปรเจกต์นั้น · งานที่ต้องเต้กดเอง (deploy prod, ชี้โดเมน) เป็น checklist ไม่ใช่ปุ่ม auto
**ไม่สร้างของใหม่** — ต่อยอด v7 ที่มี run engine, SSE, HeroUI Pro, DESIGN.md (Voltura) อยู่แล้ว · artifact v1 (claude.ai) กลายเป็น snapshot read-only ที่ export จากข้อมูลชุดเดียวกัน

## Stack (มีอยู่แล้ว — ห้ามเพิ่ม dep ใหม่)
Next.js 16 + React 19 + Tailwind 4 + `@heroui-pro/react` + `@heroui/react` + framer-motion + lucide · FastAPI `server.py` · data = JSON ใน `dashboard-data/` · design identity = `DESIGN.md` (Voltura: dark citrine/acid-lime — locked แล้ว ไม่ต้อง T000)

## Data source
`dashboard-data/radar.json` — ย้ายจาก array `P` / `DECISIONS` / `EVENTS` ใน `~/Documents/DX/artifacts/2026-09-02-dx-project-radar.html` (8 โปรเจกต์ · 8 decisions · 16 events · ข้อมูล verified 2026-09-02) + เพิ่มต่อโปรเจกต์: `actions[]` (prompt self-contained + `cwd` repo + label) · `apps[]` (prod URL · local dev {port, start cmd}) · `tae_checklist[]`

## Pages
- `/radar` (ใหม่) — KPI row · ตาราง 8 โปรเจกต์ (stripe สถานะ / เฟส+progress / ขั้นต่อไป / ติดอะไร / อัปเดต) · filter chips + search · drawer รายละเอียด (facts · rules · links · **action buttons** · open-app buttons · Tae checklist) · tab รอเต้ตัดสินใจ · tab ไทม์ไลน์
- `/` (เดิม) — เพิ่ม card "Radar: N งานต้องดูวันนี้" ลิงก์ไป `/radar` + entry ใน command palette

## Done When
- [x] `GET /api/radar` คืน 8 โปรเจกต์จาก `radar.json` · `curl` แสดง JSON จริง
- [x] `localhost:3000/radar` แสดงครบ 3 tab · screenshot 1440 + 390 ไม่มี overflow แนวนอน
- [ ] กดปุ่ม action ของ RMS → มี run จริงใน `runs/` + output stream ในหน้า (quote บรรทัดแรกของ stream)
- [x] `POST /api/run` รับ `cwd` เฉพาะ path ใน allowlist (registry) — path นอก allowlist → 403 (ทดสอบจริง)
- [ ] ปุ่มเปิดแอป: prod เปิด URL · local เปิด/สตาร์ท dev server ผ่าน `/api/devservers` + `/api/open`
- [ ] Tae checklist ติ๊กแล้วรีเฟรชยังอยู่ (`dashboard-data/radar-state.json`)
- [x] `cd web && npm run build` exit 0 · `curl :8787/api/health` 200
- [ ] design-reviewer Mode B ผ่าน DESIGN.md · Codex review ผ่านสำหรับ `server.py` (cwd allowlist = security-sensitive)

## Routing
Fable = spec/review/verify · **cursor-worker (Grok 4.5)** = build ทุก T0xx–T3xx · **Codex** = review T041 · dx-cheap = T001 (mechanical extract) · Kimi research = **ไม่จำเป็น** (ข้อเท็จจริง verify ครบจาก Explore sweep 2026-09-02)

---

## Phase 0 — Data + API (≈30 นาที)
- [x] T001 `dx-cheap` — extract `P/DECISIONS/EVENTS` จาก v1 HTML → `dashboard-data/radar.json` (schema ด้านบน; Thai คงเดิม; เพิ่ม `actions/apps/tae_checklist` ว่างไว้ก่อน)
- [x] T002 `cursor-worker` — `server.py`: `GET /api/radar` (อ่าน json) · `POST /api/radar/check` (เขียน `radar-state.json`) · แก้ `run_skill()` รับ `cwd` optional + allowlist จาก `registry.py` paths (default เดิม = VAULT_PATH) ✅ Checkpoint 0 code OK
- [x] T003 [P] `cursor-worker` — เติม `actions[]` 4 งาน (prompt จาก `~/Documents/DX/artifacts/2026-09-02-dx-project-radar-HANDOFF.md` + chips: RMS push P1.6 · Console WIP branch · LINE OA visual plan · BestonFX polish plan) + `apps[]` (prod URL ทุกโปรเจกต์ที่มี · local: line-oa :8081/:8091, console vite, rms next) + `tae_checklist[]` (deploy Support AI · ชี้โดเมน · C-book · MT5 access · Google creds · Resend)
- **Checkpoint 0:** ✅ radar.json: 8 projects + data populated · ✅ server.py: GET/POST /api/radar{,/check}, cwd allowlist with 403 · ⏳ Runtime test pending (start server)

## Phase 1 — UI shell (≈45 นาที) — เต้เห็นหน้าจอเร็วสุด
- [x] T010 `cursor-worker` — `web/src/app/radar/page.tsx` + `web/src/lib/api.ts` (fetchRadar) + ลิงก์ใน `components/dashboard/quick-nav.tsx` และ `command-palette.tsx`
- [x] T011 `cursor-worker` — `web/src/components/radar/radar-table.tsx` (HeroUI Pro Table · Chip สถานะ 5 สี semantic จาก DESIGN.md `positive/negative/cat-*` · progress bar · stripe) + `radar-kpis.tsx`
- [x] T012 [P] `cursor-worker` — `components/radar/radar-filters.tsx` (chips + search `/`)
- [x] T013 [P] `cursor-worker` — `components/radar/radar-drawer.tsx` (HeroUI Drawer/Sheet: facts · rules · links · ที่มา)
- **Checkpoint 1:** Playwright screenshot `/radar` 1440 + 390 → เทียบ DESIGN.md · ไม่มี horizontal overflow · Tae ดู

## Phase 2 — Action buttons (≈45 นาที) — หัวใจของงานนี้
- [x] T020 `cursor-worker` — `components/radar/action-bar.tsx`: ปุ่ม "รันให้เสร็จ" ต่อ action → `POST /api/run {skill:"radar-action", prompt, cwd}` → stream เข้า `run-output.tsx` เดิม · disabled + spinner ขณะรัน · ปุ่ม "หยุด" → `/api/kill`
- [x] T021 [P] `cursor-worker` — ปุ่ม "เปิดแอป": prod → `window.open` · local → อ่าน `/api/devservers` (running?) → ถ้าไม่รัน `POST /api/open` start แล้วเปิด
- [x] T022 [P] `cursor-worker` — `tae-checklist.tsx`: ติ๊ก → `POST /api/radar/check` · ป้าย "เต้ต้องกดเอง" ชัดเจน ห้ามมีปุ่ม auto
- **Checkpoint 2:** กด action RMS จริง → run file ใหม่ใน `runs/` + stream ขึ้นจอ (quote 3 บรรทัดแรก) · กด "เปิดแอป" console → เปิด netlify URL · checklist persist หลัง reload

## Phase 3 — Decisions + Timeline (≈30 นาที)
- [x] T030 `cursor-worker` — `components/radar/decision-cards.tsx` (8 ใบ เรียง impact · rec + cost · ปุ่ม "ตอบแล้ว" → เขียน state)
- [x] T031 [P] `cursor-worker` — `components/radar/timeline.tsx` (16 events group ตามวัน)
- [x] T032 [P] `cursor-worker` — card "Radar" บนหน้า `/` (side-cards.tsx) + LINE notify เมื่อ action run จบ (ใช้ `core.notify_run_done` เดิม)
- **Checkpoint 3:** screenshot 3 tab · `npm run build` exit 0

## Phase 4 — Review + export (≈30 นาที)
- [ ] T040 `design-reviewer` Mode B — review `/radar` vs DESIGN.md + AVOID-LIST · แก้เอง
- [ ] T041 `codex:review` — `server.py` diff (cwd allowlist, path traversal, prompt injection จาก json) **ก่อนประกาศเสร็จ**
- [ ] T042 [P] `cursor-worker` — `scripts/export-radar-artifact.mjs`: radar.json → single-file HTML read-only (โครงจาก v1) → Fable publish ทับ artifact `https://claude.ai/code/artifact/2edbc4ec-d7f8-49f0-9862-fe13c70e26a8`
- [x] T043 อัปเดต `HANDOFF.md` (v10 section) + `README.md` (หน้า /radar + วิธีเพิ่มโปรเจกต์ใน radar.json)
- **Checkpoint 4 (final):** ทุก Done When ติ๊กพร้อม quoted output · screenshot ส่งเต้ · commit บน `feat/web-ui` (ห้าม main)

## Risks / assumptions (log)
- `run_skill` ปัจจุบัน `cwd=VAULT_PATH` เสมอ → ต้องเพิ่ม `cwd` param; allowlist กัน path แปลก (T041 review)
- Permission mode ของ run = `PERMISSION_MODE` ใน config — งาน push branch ต้องไม่โดน prompt ค้าง → prompt ระบุ hard stops เอง (ห้าม main / deploy)
- ข้อมูล radar.json เป็น snapshot มือ — auto-refresh จาก HANDOFF เป็นงานถัดไป (`dx-loop-me`) ไม่อยู่ใน scope นี้
- `core.py` มี uncommitted change อยู่ก่อนแล้ว — ห้ามแตะ/ห้าม revert; commit แยกของเราเอง
