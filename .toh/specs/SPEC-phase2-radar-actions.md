# LOCKED SPEC — Phase 2 · `/radar` action buttons (T020–T022)

Project: `/Users/tae279/DEV_TAE/projects/agentic-os-dashboard/web`. Phase 1 already shipped `src/app/radar/page.tsx`, `src/lib/radar.ts`, `src/components/radar/{radar-kpis,radar-filters,radar-table,radar-drawer}.tsx` and radar types in `src/lib/api.ts` — read them first and keep their conventions. Also read `src/components/dashboard/run-output.tsx` (reuse it, do not fork it) and `streamPost` in `src/lib/api.ts`.
Backend contract (already live on :8787):
- `POST /api/run` body `{ skill_label: string, prompt: string, cwd: string }` → SSE events: `phase` `{phase:"starting", label, pid, cwd}` then `phase` `{phase:<tool name>}`…, `text` `{chunk}`, `done` `{ok, error, cost_usd, tokens_in, tokens_out, output, saved_path}`. HTTP 403 JSON `{error:"cwd not allowed"}` if cwd is outside the allowlist (streamPost's `onError` will NOT fire for a 403 — the body is JSON, not SSE — so before calling streamPost do a normal `fetch` check? No: keep it simple — call `streamPost`; if no `starting` phase arrives within the `done`… simpler rule: streamPost resolves with no events on 403. Treat "resolved without any `done` event" as an error and show `ไม่ได้รับอนุญาตให้รันใน cwd นี้ (403)`.)
- `POST /api/kill` body `{pid}` → `{ok}` (existing `api.kill(pid)`).
- `GET /api/devservers` → `{servers: DevServer[]}` (existing `api.devservers()`), `DevServer.port` is a number.
- `POST /api/open` body `{path}` → reveals the folder in Finder (existing `api.open(path)`).
- `POST /api/radar/check` body `{key, checked}` (existing `api.radarCheck(key, checked)`).

## Rules
Same as Phase 1: no new deps · lucide-react icons only · no emoji-as-icon · no `transition-all` · tokens only · Thai copy verbatim · `"use client"` · `npx tsc --noEmit` clean · `npm run build` exit 0.
**Safety copy rule:** anything under "เต้ต้องกดเอง" is a checklist ONLY. Never render a run button for checklist items.

## 1. Page-level run state — `src/app/radar/page.tsx`
Add state:
```ts
type RadarRun = { actionId: string; label: string; text: string; phase: string | null; pid: number | null; done: boolean; ok: boolean | null; error: string | null; cost: number | null; savedPath: string | null };
const [run, setRun] = useState<RadarRun | null>(null);
const [devservers, setDevservers] = useState<DevServer[]>([]);
```
- Poll `api.devservers()` together with `api.radar()` in the existing 30 s refresh.
- `startAction(project: RadarProject, action: RadarAction)`: if `run && !run.done` → ignore (one run at a time). Set `run = {actionId: action.id, label: "Radar · " + action.label, text: "", phase: "starting", pid: null, done: false, ok: null, error: null, cost: null, savedPath: null}`; then `await streamPost("/api/run", { skill_label: "Radar · " + action.label, prompt: action.prompt, cwd: action.cwd }, { onPhase: d => setRun(r => r && ({...r, phase: d.phase, pid: (d as {pid?: number}).pid ?? r.pid})), onText: d => append chunk, onDone: d => setRun(r => r && ({...r, done: true, ok: !!d.ok, error: (d.error as string) ?? null, cost: (d.cost_usd as number) ?? null, savedPath: (d.saved_path as string) ?? null})), onError: e => setRun(r => r && ({...r, done: true, ok: false, error: String(e)})) })`. After streamPost resolves, if `run` is still not done (no `done` event arrived) mark it done with `ok:false, error:"ไม่ได้รับอนุญาตให้รันใน cwd นี้ (403) หรือ server ตัดการเชื่อมต่อ"`.
- `stopRun()`: if `run?.pid` → `await api.kill(String(run.pid))`; set `done:true, ok:false, error:"หยุดโดยเต้"`.
- `toggleCheck(key, next)`: optimistic — update `data.state.checked` locally, then `api.radarCheck(key, next)`; if the response is not ok, revert.
- Render `<RunOutput label={run ? run.label : null} text={run?.text ?? ""} phase={run?.phase ?? null} onClose={() => setRun(null)} />` directly above the KPI row (same placement idiom as home page). When `run.done`, append a status line inside the RunOutput text area is not possible (component is fixed) — instead show the result in the ActionBar (below).
- Pass to `<RadarDrawer>`: `children={<><ActionBar …/><AppButtons …/></>}` and new prop `footer={<TaeChecklist …/>}` (render each only when the project has items).

## 2. `src/components/radar/radar-drawer.tsx` — add `footer?: React.ReactNode`
Render `footer` as the LAST block of `Drawer.Body`, separated by a top hairline (`border-t border-ring-soft pt-4 mt-4`). `children` stays right after the header meta line.

## 3. `src/components/radar/action-bar.tsx`
Props `{ project: RadarProject; run: RadarRun | null; onStart: (a: RadarAction) => void; onStop: () => void }` (export the `RadarRun` type from `src/lib/radar.ts` and import it in both files).
Section label: `งานที่ agent รันเองได้` (label-sm idiom). One row per action:
- Left: `action.label` (`text-sm text-fg`) + tiny chip: kind `plan` → "ทำแผน" (HeroUI `Chip size="sm" variant="soft" color="accent"`), `git` → "git" (`color="default"`); under it mono 11px mute `cwd` basename (`action.cwd.split("/").pop()`).
- Right: primary button **"รันให้เสร็จ"** (lucide `Play` 14px) — existing `@/components/ui/button` `size="sm"`; while `run && run.actionId === action.id && !run.done` → replace with disabled button `Loader2` spinning + "กำลังรัน · {run.phase}" and a secondary **"หยุด"** button (lucide `Square`) → `onStop()`. While ANY other run is active, all run buttons are disabled with title `รอ run ปัจจุบันจบก่อน`.
- Result line (only when `run.actionId === action.id && run.done`): ok → `text-good` "เสร็จแล้ว" + ` · $${cost.toFixed(2)}` if cost + saved file basename (mono) ; not ok → `text-danger` `ล้มเหลว · ${error}`.
- `<details>` collapsible `ดู prompt ที่จะรัน` → `<pre class="text-[11px] text-fg-dim whitespace-pre-wrap font-mono-num max-h-48 overflow-y-auto">{prompt}</pre>` (transparency: Tae sees exactly what runs).

## 4. `src/components/radar/app-buttons.tsx`
Props `{ apps: RadarApp[]; devservers: DevServer[] }`. Section label `เปิดแอป`. Pills row (`flex flex-wrap gap-1.5`), reuse the quick-nav pill classes:
- `kind === "prod"` → `<a href={url} target="_blank" rel="noreferrer">` with lucide `ExternalLink` 12px + label.
- `kind === "local"`: `running = devservers.some(s => s.port === app.port)`.
  - running → `<a href={url} target="_blank">` with a 6px `bg-good` dot + `{label} · :{port}`.
  - not running → `<button onClick={() => api.open(app.cwd!)}>` with 6px `bg-fg-mute` dot + `{label} · ยังไม่รัน` and `title="เปิดโฟลเดอร์ใน Finder"`; next to it a tiny mono chip showing `cmd` with a lucide `Copy` 12px button → `navigator.clipboard.writeText(cmd)` (show "คัดลอกแล้ว" for 1.5 s).
No auto-start of dev servers (by design — a shell command from JSON must not be executed by the UI).

## 5. `src/components/radar/tae-checklist.tsx`
Props `{ items: RadarChecklistItem[]; checked: Record<string, boolean>; onToggle: (key: string, next: boolean) => void }`.
Header row: lucide `Hand` 14px `text-warn` + label `เต้ต้องกดเอง` + hint `text-[11px] text-fg-mute` "ไม่มีปุ่ม auto — ทำเสร็จแล้วติ๊กไว้ (จำไว้หลังรีเฟรช)". List of HeroUI `Checkbox` (controlled `isSelected={!!checked[item.id]}` `onChange={(v) => onToggle(item.id, v)}`) with `Checkbox.Content > Checkbox.Control > Checkbox.Indicator` + text (`text-sm`, checked → `line-through text-fg-mute`). Count line at the bottom mono: `{done}/{items.length} เสร็จ`.

## 6. Table hint
In `radar-table.tsx` "สถานะ" cell: if `project.actions.length > 0` add a tiny lucide `Play` 10px `text-accent` after the chips with `title="มีงานที่กดรันได้"`. Nothing else changes.

## Acceptance (run all, paste)
1. `cd web && npx tsc --noEmit` clean. 2. `cd web && npm run build` exit 0. 3. `git -C /Users/tae279/DEV_TAE/projects/agentic-os-dashboard status --short` shows only web/src files.
Do not run the dev server, do not press any run button, do not take screenshots — the orchestrator does the live run test.
