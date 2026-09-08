# LOCKED SPEC — Radar v11 · visual-first redesign of `/radar`

Repo (worktree root): `/Users/tae279/DEV_TAE/projects/agentic-os-dashboard/.claude/worktrees/radar-visual-v11`
Web app: `web/` (Next.js 16 App Router · React 19 · Tailwind v4 · `@heroui/react` 3.x · `@heroui-pro/react` beta · framer-motion 12 · lucide-react). `web/node_modules` is a symlink to the main checkout's node_modules — do NOT delete or re-install it wholesale; only add `recharts` (step 0).

## Why (Tae's feedback, verbatim intent)
"ดูไม่สวยเลย text เยอะ ไม่น่าใช้ ไม่มี visual เลย" — the current page is a text table + text KPI boxes. v11 must be **visual-first**: every project shows a progress ring; the top of the page is a chart bento, not six number boxes; the timeline is a real marked timeline; text is clamped to one line per card. Same data, same API, same drawer.

## Read first (conventions — keep them)
- `web/src/app/radar/page.tsx`, `web/src/lib/radar.ts`, `web/src/lib/api.ts` (types `RadarProject`, `RadarDecision`, `RadarEvent`, `RadarResponse`), `web/src/components/radar/*`, `web/src/app/globals.css` (design tokens), `web/src/components/dashboard/gauges-row.tsx` (motion idiom).
- Tokens ONLY via Tailwind classes already mapped in globals.css: `bg-bg-card`, `bg-bg-elev`, `bg-bg-card-hi`, `text-fg`, `text-fg-dim`, `text-fg-mute`, `text-accent`, `text-good`, `text-warn`, `text-danger`, `bg-accent-soft`, `border-ring-soft`, `hairline`, `hairline-hover`, `font-display`, `font-mono-num`, `rounded-[var(--radius-card)]`, `rounded-[var(--radius-chip)]`. For SVG/inline styles use `var(--accent)`, `var(--good)`, `var(--warn)`, `var(--danger)`, `var(--ring-mid)`, `var(--fg-mute)`. **Never hardcode hex.**
- `"use client"` on every component file. Icons: lucide-react only (no emoji as icons). Thai copy verbatim from this spec. No `transition-all`. No new state libraries. Keep existing `RadarDrawer`, `ActionBar`, `AppButtons`, `TaeChecklist`, `RunOutput`, `RadarFilters` unchanged unless stated.
- Status → color mapping stays `statusColor()` / `statusStripeClass()` from `lib/radar.ts` (live=good/success · building=accent · behind=danger · quiet=warn · planning=default).
- Respect reduced motion: wrap framer-motion entrance animations with `useReducedMotion()` (skip when true).

## Step 0 — dependency
`cd web && npm install recharts@^2` (HeroUI Pro charts/KPI are subpath imports that need the `recharts` peer). Commit `package.json` + `package-lock.json` changes. Nothing else in deps.

## Step 1 — `web/src/lib/radar.ts` additions (pure helpers, keep existing exports)
```ts
export type WaitingKey = "tae" | "external" | "agent";
export function waitingKey(p: RadarProject): WaitingKey   // p.waiting ?? "agent"
export const WAITING_LABEL: Record<WaitingKey, string> = { tae: "รอเต้", external: "รอภายนอก", agent: "agent ทำต่อได้" };
export function statusCounts(projects: RadarProject[]): Record<RadarStatus, number>
export function waitingCounts(projects: RadarProject[]): Record<WaitingKey, number>
export function portfolioProgress(projects: RadarProject[]): number  // mean of progress over projects with !gap, rounded
export function attentionRank(p: RadarProject): number // behind=0, waiting tae=1, uncommitted=2, building=3, live=4, quiet=5, gap=6
export function eventStatus(e: RadarEvent, projects: RadarProject[]): "default"|"current"|"success"|"warning"|"danger"|"muted"
// code "ALL" → "current"; else by project.status: behind→danger · quiet→warning · live→success · building→current · planning→default · unknown code→muted
export function activityStrip(events: RadarEvent[], days = 14, today = new Date()): { date: string; count: number }[] // oldest→newest, ISO dates
```
Add filter `{ id: "external", label: "รอภายนอก", f: p => p.waiting === "external" }` after "tae" in `FILTERS`. Keep `kpis()` exported (home page uses it) — it is no longer used by /radar.

## Step 2 — New component `web/src/components/radar/radar-overview.tsx`
Props `{ data: RadarResponse; activeFilter: string; onFilter: (id: string) => void; onTab: (t: "decisions") => void }`.
Bento grid `grid grid-cols-1 md:grid-cols-6 gap-3`:

**Card A — "ภาพรวมพอร์ต" (`md:col-span-2`)** card idiom `rounded-[var(--radius-card)] hairline bg-bg-card p-4`.
- Label `text-[11px] uppercase tracking-[0.14em] text-fg-mute` = "ภาพรวมพอร์ต".
- Center: HeroUI Pro `RadialChart` (`import {RadialChart} from "@heroui-pro/react/radial-chart"`) as a single progress ring: `data=[{ name: "ความคืบหน้ารวม", value: portfolioProgress, fill: "var(--accent)" }]`, `width={168} height={168} innerRadius="78%" outerRadius="100%" barSize={12} startAngle={90} endAngle={-270}`, children `<RadialChart.AngleAxis angleAxisId={0} domain={[0,100]} tick={false} type="number" />` and `<RadialChart.Bar background angleAxisId={0} cornerRadius={12} dataKey="value" />`. No tooltip. Overlay (absolute, pointer-events-none, centered): `font-display text-4xl font-semibold tabular-nums text-fg` = `${portfolioProgress}%` and `text-[11px] text-fg-dim` = `${projects.length} โปรเจกต์`.
- Below the ring: **segmented status bar** — a `flex h-2 rounded-full overflow-hidden bg-bg-elev` with one `div` per status having count>0, `style={{ flex: count, background: var(--good|--accent|--danger|--warn|--ring-mid) }}` in order live · building · behind · quiet · planning. Legend row under it: for each status with count>0 a button `text-[11px] text-fg-dim hover:text-fg` with a 6px dot + `${STATUS_LABEL[s]} ${count}`; click → `onFilter(s === "live" ? "live" : s === "behind" ? "behind" : s === "quiet" ? "quiet" : "all")`.

**Card B — "ติดที่ใคร" (`md:col-span-2`)**
- Label "ติดที่ใคร".
- Three horizontal bars (plain divs, no chart lib): rows for `tae`, `external`, `agent` in that order. Each row: left `text-xs text-fg` label = WAITING_LABEL, middle `h-2 rounded-full bg-bg-elev` track with fill width `count / projects.length * 100%` (fill colors: tae → `var(--warn)`, external → `var(--fg-mute)`, agent → `var(--accent)`), right `font-mono-num text-sm tabular-nums text-fg` = count. Whole row is a `button` → `onFilter("tae" | "external" | "all")`. Active filter row gets `bg-accent-soft` rounded background.
- Footer line `text-[11px] text-fg-mute`: "รอเต้ = งานที่ agent ทำแทนไม่ได้ · กดแถวเพื่อกรอง".

**Card C — three stacked mini KPIs (`md:col-span-2`, `grid grid-rows-3 gap-3` — three separate cards)**, each `button` with card idiom + `hairline-hover`, layout: left lucide icon in a 32px rounded square tinted (`bg-accent-soft`, or `bg-danger/15`, `bg-warn/15` via `style={{ background: "color-mix(in srgb, var(--danger) 15%, transparent)" }}`), middle label `text-[11px] uppercase tracking-[0.14em] text-fg-mute` + big number `font-display text-2xl font-semibold tabular-nums`, right: for the decisions card a 44px HeroUI `ProgressCircle` (`import {ProgressCircle} from "@heroui/react"`, `size="sm"`, `color="warning"`, `value = answered / decisions.length * 100`, aria-label "ตอบแล้ว") — answered = count of `data.state.checked["decision:"+id]`.
  1. `CircleHelp` icon · "รอเต้ตัดสินใจ" · value = `decisions.length - answered` · sub `text-[11px] text-fg-dim` = `${impact3} เรื่องผลกระทบสูง` · click → `onTab("decisions")`.
  2. `GitBranch` icon (warn tint) · "งานยังไม่ push" · value = uncommitted count · sub "เสี่ยงหายถ้าเครื่องพัง" · click → `onFilter("uncommitted")`.
  3. `ServerCrash` icon (danger tint) · "prod ตามหลังโค้ด" · value = behind count · sub "บั๊กที่แก้แล้วยังอยู่บนของจริง" · click → `onFilter("behind")`.
  Active filter → `ring-1 ring-accent/60`.

Entrance: `motion.div` per card, `initial={{opacity:0,y:10}} animate={{opacity:1,y:0}}` stagger 0.05s, skipped under reduced motion.

## Step 3 — New component `web/src/components/radar/project-grid.tsx` (replaces the table)
Props `{ projects: RadarProject[]; onOpen: (id: string) => void; checked: Record<string, boolean> }`.
- Sort by `attentionRank` asc, then `updated` desc (null last).
- Grid `grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-4 gap-3`.
- Empty state: reuse the existing `EmptyState` from `radar-table.tsx` (move it into this file).
- **Card** = `button type="button"` full-width text-left, `rounded-[var(--radius-card)] hairline hairline-hover bg-bg-card p-4 cursor-pointer focus-visible:ring-2 focus-visible:ring-accent/60 relative overflow-hidden`, with a 3px left status stripe (`absolute left-0 top-0 bottom-0 w-[3px]` using the status color var) and hover `-translate-y-px` via `transition-transform`.
  Layout `flex gap-3 items-start`:
  - Left: HeroUI `ProgressCircle` `size="lg"` `value={p.progress}` `color={statusColor(p.status)}` (map "default" → "default"), aria-label `${p.code} ${p.progress}%`, with custom thin track: `<ProgressCircle.Track strokeWidth={3} viewBox="0 0 36 36"><ProgressCircle.TrackCircle cx={18} cy={18} r={16} strokeWidth={3}/><ProgressCircle.FillCircle cx={18} cy={18} r={16} strokeWidth={3} strokeLinecap="round"/></ProgressCircle.Track>` wrapped in a `relative size-14` div with centered overlay `font-mono-num text-[11px] tabular-nums text-fg` = `${p.progress}%` (gap projects show "—").
  - Right (`min-w-0 flex-1`):
    - Row 1: `font-mono-num text-[10px] uppercase tracking-[0.12em] text-fg-mute` = code, then `Chip size="sm" variant="soft" color={statusColor(p.status)}` = statusLabel (truncate, `max-w-[60%]`).
    - Row 2: `font-display text-sm text-fg truncate` = name.
    - Row 3: `text-xs text-fg-dim truncate` = `p.next` (one line only; full text lives in the drawer).
    - Row 4 (`flex items-center gap-1.5 mt-2 flex-wrap`): icon-chips `inline-flex items-center gap-1 text-[10px] rounded-[var(--radius-chip)] hairline px-1.5 py-0.5`:
      - waiting tae → `User` icon + "รอเต้" (`text-warn`); external → `Globe` + "รอภายนอก" (`text-fg-dim`); agent → `Bot` + "agent" (`text-accent`).
      - uncommitted → `GitBranch` + "ยังไม่ push" (`text-warn`).
      - blocker → `AlertTriangle` icon only (`text-danger`) with `title={p.blocker}`.
      - actions.length>0 → `Play` icon + "รันได้" (`text-accent`).
      - right-aligned (`ml-auto`) `font-mono-num text-[10px] text-fg-mute` = `ageLabel(daysAgo(p.updated))`, red (`text-danger`) when age > 30 or null (and not gap).
    - Checklist progress (only if `tae_checklist.length > 0`): a 3px `h-[3px] rounded-full bg-bg-elev mt-2` track with fill `var(--good)` width = done/total where done = `checked[item.id]`; title `${done}/${total} เต้ต้องกดเอง`.
- Entrance stagger like Step 2 (0.03s per card, cap at 12).

## Step 4 — `web/src/components/radar/timeline.tsx` rewrite (same props)
- Top: **activity strip** card (`rounded-[var(--radius-card)] hairline bg-bg-card p-3`): label "14 วันล่าสุด" + a `grid grid-cols-14 gap-1` of 14 cells (`h-6 rounded-[4px]`) from `activityStrip(events, 14)`; cell background `color-mix(in srgb, var(--accent) ${min(100, 20 + count*25)}%, transparent)` when count>0 else `bg-bg-elev`; `title` = `${date} · ${count} เหตุการณ์`; first/last date labels under the strip in `font-mono-num text-[10px] text-fg-mute`.
- Then groups by date (desc) as today, but rendered with HeroUI Pro `Timeline` (`import {Timeline} from "@heroui-pro/react"`): one `<Timeline size="sm" density="compact">` per date group, `<Timeline.Item status={eventStatus(e, projects)}>` → `<Timeline.Content>` containing: code pill (same clickable pill as today; "ALL" plain) + `text-sm text-fg-dim` text (`line-clamp-2`). Date heading stays `font-mono-num text-[11px] uppercase tracking-[0.14em] text-fg-mute` = `${date} · ${ageLabel(daysAgo(date))}`. If `Timeline` from `@heroui-pro/react` is not exported at the root in the installed beta, fall back to `@heroui-pro/react/timeline`; if neither exists, keep the current hand-rolled rail but color the dot with the same status mapping — report which path you took.
- Keep the empty state.

## Step 5 — `web/src/components/radar/decision-cards.tsx` tweaks
- Add an **impact meter** next to the impact chip: three 4px×10px bars (`flex gap-0.5`), filled bars = impact, filled color danger/warn/ring-mid for 3/2/1, empty = `bg-bg-elev`.
- `why` → add `line-clamp-2`. `rec` → `line-clamp-2`. Keep everything else.

## Step 6 — `web/src/app/radar/page.tsx`
- Replace `<RadarKpis …/>` with `<RadarOverview data={data} activeFilter={filter} onFilter={(id) => { setFilter(id); setTab("projects"); }} onTab={setTab} />`.
- Replace `<RadarTable …/>` with `<ProjectGrid projects={visible} onOpen={setSelectedId} checked={data.state.checked} />`.
- Delete `web/src/components/radar/radar-table.tsx` and `web/src/components/radar/radar-kpis.tsx` (no other importers — verify with grep first; if the home page imports `RadarKpis`, keep the file).
- Skeleton block: keep, but change the first skeleton grid to `grid-cols-1 md:grid-cols-6` with 3 boxes (`md:col-span-2`, `h-56`).

## Non-goals
No backend/API changes · no radar.json changes · no changes to `/` or `/portfolio` · no new deps beyond `recharts` · no light theme · no auth.

## PROOF (run all from `web/`, paste full output)
1. `npx tsc --noEmit` → clean.
2. `npm run lint` → clean (fix warnings you introduced).
3. `npm run build` → exit 0.
4. `grep -rn "#[0-9a-fA-F]\{6\}" src/components/radar src/lib/radar.ts` → no matches (no hardcoded hex).
5. `git status --short` at worktree root → only `web/src/**`, `web/package.json`, `web/package-lock.json`.
Commit on the current branch `feat/radar-visual-v11` with conventional messages (EN), one commit per step is fine. Do not push. Do not touch `main` or `gitbutler/workspace`.
