# WORK ORDER for Codex — DX Command Center v10 "Project Radar" (finish Phase 2 verify + Phase 3 + docs)

Repo: /Users/tae279/DEV_TAE/projects/agentic-os-dashboard · branch `feat/web-ui`. Read in this order before touching anything: `HANDOFF.md` (top section v10), `.toh/plan.md`, `.toh/progress.md` (lines dated 06:12 + LEARNING), `.toh/specs/SPEC-phase3-radar-decisions-timeline.md`, `server.py`, `web/src/app/radar/page.tsx`, `web/src/components/radar/*`, `web/AGENTS.md` (Next.js 16 differs from training data).

## Rules
- Work only on branch `feat/web-ui`. Do not commit to, merge into, or push `main`. No deploys. Do not read or edit `.env*`, secrets, `~/.config/dx/line-notify.json`, `~/.ssh`.
- `core.py` has a pre-existing uncommitted change that is not yours: leave it as is and exclude it from your commits (stage only files you changed; no `git add .`).
- No new npm/pip dependencies. Icons = lucide-react only. No emoji as icons. No `transition-all`. Colors via existing CSS tokens in `web/src/app/globals.css`.
- Do not run `npm run build` while a `next dev` server uses the same `.next`. Verify with `cd web && npm run build && npm run start -- -p 3000`. Backend: `.venv/bin/python -m uvicorn server:app --host 127.0.0.1 --port 8787` (may already be running; check `lsof -iTCP:8787 -sTCP:LISTEN`).

## Tasks (in order; tick boxes in `.toh/plan.md`; append one line per state change to `.toh/progress.md`)
1. Fix `server.py` `run_skill` blocking IO (root cause of UI action runs hanging at "starting"): the async generator reads `proc.stdout.readline` synchronously and `stderr=PIPE` is never drained. Rewrite with `asyncio.create_subprocess_exec` (awaited stdout readline; stderr to a per-run file under `.cache/runs-stderr/`), enforce `RUN_TIMEOUT_SEC` with a deadline that fires even when no output arrives, terminate the process on timeout and on client disconnect (`asyncio.CancelledError`). Keep the SSE event contract exactly (`phase` {phase,label,pid,cwd on "starting"}, `text` {chunk}, `done` {ok,error,cost_usd,tokens_in,tokens_out,output,saved_path}) and keep the `core.save_run_output/log_run/notify_run_done` calls. Apply the same treatment to `/api/chat`. Keep `_resolve_run_cwd` allowlist logic unchanged.
   Proof: `curl -s -N --max-time 120 -X POST 127.0.0.1:8787/api/run -H 'Content-Type: application/json' -d '{"skill_label":"Radar · smoke","prompt":"Run the shell command pwd and reply with only its output.","cwd":"/Users/tae279/DEV_TAE/Cursor Tae/beston-line-oa"}'` shows `starting` → `Bash` → text → `done ok:true`; the same body with `"cwd":"/tmp"` → HTTP 403. Then run the real LINE OA action prompt from `dashboard-data/radar.json` (projects[id=lineoa].actions[0]) the same way (do not pipe into grep — it block-buffers) and confirm phases stream and a new file appears in `dashboard-data/runs/`. Quote the first 3 events in progress.md.
2. `web/src/app/radar/page.tsx` `toggleCheck`: wrap `api.radarCheck` in try/catch and revert the optimistic tick on any failure.
3. Phase 3 — implement `.toh/specs/SPEC-phase3-radar-decisions-timeline.md` exactly (decision-cards.tsx, timeline.tsx, tab wiring, RadarCard on `/` right rail, command-palette `pages` group). Acceptance: `cd web && npx tsc --noEmit` clean, `npm run build` exit 0.
4. Docs (T043): add a "/radar" section to `README.md` (what it is, how to run, how to add a project/action in `dashboard-data/radar.json`, note the file is gitignored) and update the v10 section of `HANDOFF.md` with what you verified plus a short `## Security notes` (cwd allowlist; prompt text comes from local JSON only; the UI never executes a shell command from JSON). Skip T040/T041/T042.
5. If `npx playwright --version` works in `web/`, screenshot `/radar` 3 tabs at 1440 and 390 into `.cache/screenshots/`; otherwise say so and skip.
6. Commit on `feat/web-ui` in 2–3 conventional commits (EN): `feat(radar): …` (web), `fix(server): async subprocess for run/chat` (server.py), `docs: …`. Do not push.

## Report (last message, Thai, ≤15 lines)
ทำอะไร / ผลตรวจจริง (quote คำสั่ง + ผล) / อะไรยังไม่ผ่านและทำไม / commit hashes. Write the same to `.toh/CODEX-RESULT.md`.
