# Plan — DX Command Center v11 · "Radar actions refresh"

Status: in-progress
Created: 2026-09-03 · Author: Claude (Fable 5.1) · Owner: Tae
Repo: `~/DEV_TAE/projects/agentic-os-dashboard` (branch `feat/web-ui`; commit ผ่าน worktree `brave-dubinsky-b270c2`)

## Goal
`radar.json` ตรงกับความจริง ณ 3 ก.ย. — ปุ่ม "รันให้เสร็จ" ทุกใบต้องเป็นงานถัดไปจริง ไม่ใช่งานที่ทำไปแล้ว · artifact snapshot ตามให้ทัน · เก็บ 2 จุด design ที่ค้างจาก v10

## Ground truth (verify แล้ว 2026-09-03 ไม่ใช่เดา)
| โปรเจกต์ | สิ่งที่ตรวจ | ผล |
|---|---|---|
| landing | `curl -L https://bestonfx.com/` | 200 · React SPA (`<html lang="th" class="dark">`) — **ไม่ใช่ WordPress แล้ว** → blocker เดิมตาย |
| landing | artifact `2026-09-03-bestonfx-final-polish-plan.html` | มีจริง · P0 = 2 ข้อ (cookie banner บังปุ่ม /platforms /markets @390 · decrypt effect เล่นซ้ำวินาที 4.1 @1440) |
| lineoa | `gh pr view 24` | OPEN · head `feat/one-stop-shell` · Codex review ไม่จบ (เครดิตหมด) |
| lineoa | `HANDOFF-ONE-STOP-STEP4.md` @ `feat/one-stop-step3` | 🔴 งานถัดไป = รวมงานขั้น ③ ที่ทำซ้ำ 2 ตัว (เต้เคาะ 3 ก.ย.: เก็บ PR #25 เป็นหลัก ดึงส่วนดีของ `971d162` มา) · migration `0013` ต้องเหลือไฟล์เดียว |
| console | `git status --short` | สะอาด — เหลือแต่ `.serena/ deno.lock prompt_reports.txt tokens.json` ที่ห้าม add อยู่แล้ว → action "เก็บ WIP" ตายแล้ว |
| rms | `git status` + `active.md` | ยัง dirty จริง 23 ไฟล์ +1237/-378 · "ยังไม่ push" → action เดิมยังถูกต้อง คงไว้ |

## Done When
- [ ] `curl :8787/api/radar` → ทุก action label ตรงกับตารางข้างบน (quote ผลจริง)
- [ ] lineoa/landing มี `updated/next/blocker/facts/progress` ใหม่ · events มี 3 รายการของ 3 ก.ย.
- [ ] `node scripts/export-radar-artifact.mjs` สำเร็จ → publish ทับ artifact `2edbc4ec` (read ก่อน publish)
- [ ] `button.tsx` ไม่มี `transition-all` · quick-nav ไม่มี emoji เป็นไอคอน
- [ ] `cd web && npx tsc --noEmit` clean + `npm run build` exit 0 (รันใน worktree ไม่ทับ `.next` ของ dev)
- [ ] screenshot 1440 + 390 หน้า `/` และ `/radar` ส่งเต้
- [ ] commit บน `feat/web-ui` (ห้าม main · แยกจาก core.py) + HANDOFF v11 + progress.md

## Phase A — radar.json (T110 + T111)
- [ ] T110 เขียน `actions[]` ใหม่: landing → `landing-p0-fix` (แก้ P0-1 + P0-2 บน feature branch) · lineoa → `lineoa-step3-merge` (รวมงานขั้น ③ ตาม STEP4 handoff) · console → ลบ action ที่ตายแล้ว · rms → คงเดิม · ทุก prompt self-contained + HARD STOPS
- [ ] T111 อัปเดต `updated/next/blocker/facts/progress/status` ของ landing + lineoa + console · เพิ่ม 3 events ของ 3 ก.ย. · `verified` → 2026-09-03
- **Checkpoint A:** `curl :8787/api/radar` quote label ครบ

## Phase B — export + publish (T111b)
- [ ] `node scripts/export-radar-artifact.mjs` → Artifact read `2edbc4ec` → publish ทับ

## Phase C — design leftovers (T112)
- [ ] Design OS Step 0 (`_uistack.py` + `dx-design-router`) ก่อนแตะ UI
- [ ] `web/src/components/ui/button.tsx` `transition-all` → ระบุ property ตาม DESIGN.md
- [ ] `web/src/components/dashboard/quick-nav.tsx` emoji mascot → ไอคอน lucide ตาม DESIGN.md
- **Checkpoint C:** tsc clean · build exit 0 · screenshot 1440/390

## Phase D — ship
- [ ] commit บน `feat/web-ui` ผ่าน worktree · HANDOFF v11 · progress.md

## Hard stops
ห้ามแตะ main · ห้าม deploy · ห้ามแตะ .env/secrets · ห้าม revert uncommitted `core.py` · ห้าม `git add .` · ห้าม `npm run build` ทับ `.next` ที่ `next dev` ใช้อยู่
