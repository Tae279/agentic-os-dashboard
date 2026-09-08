# LOCKED SPEC — Phase 3 · decisions + timeline + home card (T030–T032)

Project: `/Users/tae279/DEV_TAE/projects/agentic-os-dashboard/web`. Phases 1–2 shipped `src/app/radar/page.tsx`, `src/lib/radar.ts`, `src/components/radar/*`. Read them first; keep conventions (tokens, lucide only, Thai copy verbatim, `"use client"`, no new deps, no `transition-all`, no emoji icons).

## 1. `src/components/radar/decision-cards.tsx` (T030)
Props `{ decisions: RadarDecision[]; projects: RadarProject[]; checked: Record<string, boolean>; onToggle: (key: string, next: boolean) => void; onOpenProject: (id: string) => void }`.
- Order: impact 3 → 2 → 1, stable within impact. Answered cards (`checked["decision:" + d.id]`) sink to the end.
- Grid `grid-cols-1 md:grid-cols-2 gap-3`. Card = `rounded-[var(--radius-card)] hairline bg-bg-card p-4` (answered → `opacity-60`).
- Top row: impact chip (HeroUI `Chip size="sm" variant="soft"`): 3 → "ผลกระทบสูง" `color="danger"` · 2 → "กลาง" `color="warning"` · 1 → "ต่ำ" `color="default"`; then a project pill button (`font-mono-num text-[11px]` = project `code`, click → `onOpenProject(d.project)`); right-aligned "ตอบแล้ว" chip (`color="success"`) when answered.
- `question` → `font-display text-base text-fg mt-2`.
- `why` → `text-xs text-fg-dim mt-1`.
- Block "แนะนำ" (label-sm idiom) → `rec` `text-sm text-fg`. Block "ต้นทุน" → `cost` `font-mono-num text-[11px] text-fg-dim`.
- Footer: button (existing `@/components/ui/button` `size="sm" variant="secondary"`): not answered → lucide `Check` 14px + "ตอบแล้ว" → `onToggle("decision:" + d.id, true)`; answered → lucide `Undo2` 14px + "ยกเลิก" → `onToggle(key, false)`.
- Empty state (no decisions): card with `text-fg-dim` "ไม่มีเรื่องรอตัดสินใจ".

## 2. `src/components/radar/timeline.tsx` (T031)
Props `{ events: RadarEvent[]; projects: RadarProject[]; onOpenProject: (id: string) => void }`.
- Group by `date` (desc). Each group: heading `font-mono-num text-[11px] uppercase tracking-[0.14em] text-fg-mute` = date + ` · ${ageLabel(daysAgo(date))}`.
- Rows inside a `border-l border-ring-soft pl-4 ml-1 space-y-2`: 6px dot (`absolute -left-[3px]` `bg-ring-mid`, first row of the newest date `bg-accent`) + code pill (`font-mono-num text-[11px] hairline rounded-[var(--radius-chip)] px-1.5`; clickable when a project with that `code` exists → `onOpenProject(project.id)`; "ALL" is plain text) + `text` `text-sm text-fg-dim`.

## 3. Wire tabs — `src/app/radar/page.tsx`
Replace the Phase 1 placeholders: decisions panel → `<DecisionCards …/>`; timeline panel → `<Timeline …/>`. `onOpenProject` sets `selectedId` (drawer opens on any tab). Keep KPI "รอเต้ตัดสินใจ" click → switches to the decisions tab (Phase 1 already wired `tab: "decisions"`).

## 4. Home card + command palette (T032)
- `src/components/dashboard/side-cards.tsx`: add `export function RadarCard({ radar }: { radar: RadarResponse | null })`. Skeleton pulse when null. Card idiom (`rounded-[var(--radius-card)] hairline bg-bg-card p-3.5`): header row `text-xs font-mono-num text-fg-dim` "radar · โปรเจกต์" + right `Link href="/radar"` "เปิด →" (`text-accent`). Big numeral (`font-display text-3xl font-semibold font-mono-num text-fg`) = count of projects matching the `attention` filter from `src/lib/radar.ts` `FILTERS` + label `text-xs text-fg-dim` "งานต้องดูวันนี้". Sub-line `text-[11px] text-fg-mute`: `${decisions.length} รอเต้ตัดสินใจ · ${behind} prod ตามหลัง · ${uncommitted} ยังไม่ push`. Answered decisions (`state.checked["decision:"+id]`) are excluded from the decisions count.
- `src/components/dashboard/right-rail.tsx`: accept new prop `radar: RadarResponse | null` and render `<RadarCard radar={radar} />` as the FIRST card in the rail.
- `src/app/page.tsx`: add `api.radar()` to the `Promise.allSettled` refresh → `radar` state → pass to `<RightRail radar={radar} …/>`.
- `src/components/dashboard/command-palette.tsx`: add optional prop `pages?: { label: string; description: string; href: string }[]`; render them as the first `Command.Group heading="หน้า"` (cmdk `Command.Group`), item value = label + description, `onSelect` → `window.location.assign(href)` then close. In `page.tsx` pass `pages={[{ label: "Radar", description: "สถานะทุกโปรเจกต์ + ปุ่มรันงานค้าง", href: "/radar" }, { label: "Portfolio", description: "การ์ดโปรเจกต์ + AI แนะนำ", href: "/portfolio" }]}`. Existing skills group stays under `Command.Group heading="workflow"`.
- LINE notify on action finish: NO work — backend `/api/run` already calls `core.notify_run_done` for every run (verified by orchestrator).

## Acceptance (run all, paste)
1. `cd web && npx tsc --noEmit` clean. 2. `cd web && npm run build` exit 0. 3. `git -C /Users/tae279/DEV_TAE/projects/agentic-os-dashboard status --short` → only web/src files. No dev server, no screenshots.
