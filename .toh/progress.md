2026-09-03 03:21 survey — plan approved by Tae, loop start (Fable orchestrator, cursor-worker build)
2026-09-03 03:23 T001 done — CHECK_OK: node extract → radar.json projects 8 decisions 8 events 16 (used deterministic node eval instead of dx-cheap: zero transcription risk on Thai text)
2026-09-03 03:23 T002 running (cursor-worker) — server.py radar endpoints + cwd allowlist
2026-09-03 03:27 T003 done — CHECK_OK: radar.json actions 4 · apps 10 · checklist 11 (prompt content authored by Fable = spec; node write)
2026-09-03 03:29 T010-T013 running (cursor-worker, one session, locked spec SPEC-phase1-radar-ui.md) — HeroUI OSS not Pro (Pro artifacts need `npx heroui-pro login`, cannot auth on behalf of Tae)
2026-09-03 03:44 T002 done — CHECK_OK: _resolve_run_cwd('/tmp')=None · rms path resolves · traversal ../../.ssh=None · POST /api/run cwd=/tmp → HTTP 403 · cwd=~/.ssh → 403 · POST /api/radar/check writes radar-state.json
2026-09-03 03:44 Checkpoint 0 PASS — GET /api/radar projects=8 · real run cwd=rms-app prompt pwd → stream: phase starting pid 69752 → Bash → text "/Users/tae279/Documents/DX/Projects/bestonfx-rms-internal/rms-app" → done ok cost $1.57 · run file dashboard-data/runs/2026-09-03/03-43-radar-smoke-pwd.md
LEARNING: cursor-worker dispatcher must be told to pass Bash timeout 600000 — default 120s kills cursor-agent mid-write (exit 143)
LEARNING: never run `npm run build` while `next dev` is up on the same .next — dev breaks with "ComponentMod.handler is not a function"; verify on `next build && next start` instead
2026-09-03 03:44 T020-T022 running (cursor-worker, SPEC-phase2-radar-actions.md)
2026-09-03 03:45 Checkpoint 1 partial — /radar 1440 renders 8 rows real data · drawer opens but anchors LEFT (HeroUI .drawer__content fixed left:0 right:0 + our w-full/max-w-xl → fix: add `left-auto` after Phase 2 lands) · 390: documentElement.scrollWidth=390 (no horizontal overflow)
2026-09-03 03:46 Checkpoint 1 — home `/` at 1440 after @heroui/styles import: launcher/gauges/chart/right-rail render unchanged (screenshot .playwright-mcp/page-2026-09-02T20-46-39-470Z.png) · /radar 390: table scrolls inside container, body scrollWidth 390
2026-09-03 06:12 T020-T022 built (Cursor finished the files before its API connection dropped; dispatcher mis-reported failure) — Fable fixed 1 tsc error (lucide `title` prop → wrapped span) + drawer `left-auto`; tsc clean; next build exit 0
2026-09-03 06:12 Checkpoint 2 PARTIAL — drawer right-anchored ✓ · action bar/apps/checklist render ✓ · click "รันให้เสร็จ" → POST /api/run 200, UI shows "กำลังรัน · starting" + หยุด ✓ · checklist tick persists via API (radar-state.json) ✓ · BUT end-to-end completion of the real LINE OA plan action via UI NOT verified: attempt #1 (05:06) ended [ERR] at 05:24 (= RUN_TIMEOUT 900s) with zero tool phases; attempt #2 (05:35) same silence; direct `claude -p pwd` in that cwd completes in 8–25s so cwd itself is fine. Machine network flapped during test (ERR_NETWORK_CHANGED, Cursor API + heroui MCP DNS failures). Root cause open.
LEARNING: server.py run_skill reads proc.stdout with blocking readline inside an async generator — a silent claude blocks the whole FastAPI loop and the 900s timeout only fires when a line arrives; stderr is PIPE and never drained (64KB buffer can deadlock a chatty run). Fix candidates for T041: asyncio.create_subprocess_exec + stderr→DEVNULL/file, and `--strict-mcp-config` for cwd runs.
LEARNING: UI checklist toggle must wrap api.radarCheck in try/catch and revert on network error (optimistic tick stayed after ERR_NETWORK_CHANGED).
2026-09-03 Codex T041 running — replacing blocking run/chat subprocess IO with asyncio + per-run stderr files + deadline/cancellation termination
2026-09-03 Codex T041 code complete — py_compile clean; smoke + LINE action stream starting/text/done without hanging but both done ok:false because Claude OAuth expired; /tmp remains HTTP 403
2026-09-03 Codex T020 rollback complete — radar checklist/decision optimistic state now reverts on thrown fetch errors and non-2xx responses
2026-09-03 Codex T030-T032 running — decisions, timeline, home Radar card, and command-palette pages group wired to locked Phase 3 spec
2026-09-03 Codex T030-T032 done — npx tsc --noEmit exit 0; npm run build exit 0 (Next.js 16.2.10, 4 app routes including /radar)
2026-09-03 Codex T043 running — documenting /radar usage/data schema and v10 verification/security boundaries
2026-09-03 Codex LINE OA first 3 events — 1 `phase {phase:starting,label:Radar · ทำ visual plan HTML nav 5 งาน,pid:71532,cwd:beston-line-oa}` · 2 `text {chunk:Failed to authenticate: OAuth session expired and could not be refreshed}` · 3 `done {ok:false,error:exit 1,saved_path:null}`
2026-09-03 Codex T043 done — README /radar run/data/action guide + HANDOFF v10 verification and Security notes added
2026-09-03 Codex screenshots done — Playwright 1.61.1 with system Chrome wrote 3 tabs at exact 1440 and 390 to .cache/screenshots; document scrollWidth matched innerWidth for all 6 views
2026-09-03 Codex commits done — feat/web-ui only; server, web, and docs split into 3 conventional commits; no push or deploy; core.py excluded
