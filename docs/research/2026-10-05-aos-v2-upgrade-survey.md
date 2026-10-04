# Agentic OS V2 starter — upgrade survey (input for /grill-with-docs)

Date: 2026-10-05 · Surveyed by: Claude (Fable 5.1) · Owner: Tae
Source: https://github.com/ctskool/agentic-os-starter-v2 @ `6bfc219` (2026-09-23), MIT, plugin 0.3.64 / HUD 2.0.0-preview.28
Read-only survey. Nothing was installed, started, or changed. V2 was cloned to the session scratchpad only.

## 1. The two systems are different products, not two versions of one codebase

| | Ours (DX Command Center) | V2 starter |
|---|---|---|
| Latest line | `feat/web-ui` → `feat/radar-visual-v11` (`f898282`) | `main` |
| Backend | Python FastAPI `server.py` :8787 (+ `core.py`, `registry.py`, `monitors.py`) | Node "bridge" :3219 (`obsidian-v2/runner/*.mjs`, ~80 modules) |
| Front | Next.js 16 `web/` :3000 (`/`, `/portfolio`, `/radar`), HeroUI + shadcn; legacy Streamlit :8501 | Next.js 15 HUD :3217 (Three.js core, xterm) + Obsidian plugin (Preact) |
| Extra services | VPS mirror + mobile job queue, VPS worker, LINE notify | preview :3218, speech :3220 (Python), monitor :3221 |
| Runs agents via | `claude -p --model claude-sonnet-5` (headless, SSE to UI), cwd allowlist, CSRF guard | Claude Code **or** Codex; headless workflows + real terminal conversations (node-pty) |
| Data | `dashboard-data/radar.json`, runs, vault at `~/Documents/DX/DX AI Agent OS` | everything in the vault (`system/v2/dashboard.json`, `inbox/reports/*`, daily-note schema) |
| Focus | DX project portfolio: radar, decisions, "run to finish" actions, phone access | Solo creator day: plan, priorities, YouTube/IG/TikTok metrics, research, voice |

Consequence (V2's own `setup/UPGRADE.md` §4): we are **case C "customized or unknown project"**. `node aos.mjs update` refuses us by design. There is no automatic merge; every borrowed feature is a deliberate port with its supporting pieces.

Note: this worktree's branch (`claude/agentic-os-starter-59fd02`) sits on upstream `main` (Chase's v1 Streamlit template, `origin` = `cth9191/agentic-os-dashboard`). Tae's real work is on the `tae` remote lines above. Any build work must branch from `feat/radar-visual-v11` / `feat/web-ui`, not from here.

## 2. Machine readiness (checked 2026-10-05)

| Requirement | This Mac | Status |
|---|---|---|
| Node 22+ | v26.8.2 | OK |
| Obsidian | `/Applications/Obsidian.app` | OK |
| Claude Code + Codex CLI | both on PATH | OK |
| Disk 3 GB / RAM 8 GB | 169 GB free / 64 GB | OK |
| Python 3.10–3.13 (voice only) | only 3.14.4 found | **Missing** — voice needs a 3.12 install |
| Ports 3217–3221 free | nothing listening; ours use 3000/8787/8501 | OK, no clash |
| Existing Agentic OS install | none at `~/agentic-os*` | fresh |
| macOS support | V2 docs: "macOS remains beta" | Risk |

## 3. What V2 has that we do not (borrow candidates)

| # | Capability | Where in V2 | What it needs to come along | Port effort into ours | Value for Tae |
|---|---|---|---|---|---|
| A | **Claude login expiry warning** (1 day ahead) | `runner/claude-login.mjs`, `claude-signin.mjs` (~60 lines each) | nothing else | Small | High — an expired login already killed our runs on 2026-09-03 |
| B | **Health check ("doctor") + auto-recover + start at login** | `scripts/aos/doctor.mjs`, `runner/service-supervisor.mjs`, `autostart.mjs` | per-service checks rewritten for our :8787/:3000/queue worker | Medium | High — today a dead service is found only when Tae opens the page |
| C | **Codex as second engine + usage meters for both** | `runner/adapters.mjs`, `codexUsage.mjs`, `claudeUsage.mjs`, `ProviderUsage.tsx` | provider field on every run, model lock policy (`RUN_MODEL`), UI switch | Medium | Medium-high — keeps working when Claude quota is out |
| D | **User-chosen skill buttons (≤10) + "find installed skills"** | `runner/dashboard.mjs`, `shared/dashboard.mjs`, `DashboardCustomizer.tsx`, `SkillBrowser.tsx` | config file with revision guard, skill discovery, UI editor | Medium | Medium — our launcher grid is hard-coded in `config.py` |
| E | **Live agent terminals in the browser** (persistent conversations, recover after restart) | `runner/terminals.mjs` (494 lines), `terminal-*.mjs`, `TerminalTabs.tsx`, `work-recovery.ts`; `node-pty`, `xterm` | a Node sidecar (our backend is Python), auth, process cleanup | Large | Medium — today we only have one-shot headless runs + chat dock |
| F | **Local voice** (speak → Whisper → agent → Kokoro speaks) | `runner/speech.py`, ~30 `voice-*.mjs`, hotkey helper | Python 3.12, ~1.3 GB models, mic permission, bridge | Very large to port; free if V2 runs side-by-side | **Unverified for Thai** — Whisper handles Thai input; Kokoro Thai output not confirmed. Must be tested before counting on it |
| G | **Obsidian cockpit** (daily plan, Top 3, schedule inside the vault) | `obsidian-v2/src/*` | V2 bridge, daily-note schema `system/schemas/daily-note.md`, adds folders to the vault | Not portable — only via side-by-side install | Depends on whether Tae lives in Obsidian daily |
| H | **Bundled workflow rubrics** (plan-today, morning-intel, deep-research, weekly-review, content-cascade, lead-research, inbox-brief…) | `obsidian-v2/workflow-references/*.md` (20 files) | just prompts; some need calendar/Gmail connectors | Small — reuse as prompts for our `/api/run` | Medium — several overlap skills Tae already has |
| I | Jev (paid voice router via OpenRouter) | `runner/jev.mjs` | OpenRouter key + credit | — | Low; optional even in V2 |
| J | Creator metrics (YouTube/IG/TikTok/GitHub trending) | `runner/scripts/metrics-pull/*` | API keys | Small | Low — not DX's business |

What we have that V2 lacks (must not be lost): Project Radar + decisions + checklists, portfolio, phone access via VPS mirror/queue, VPS worker, LINE notify, cwd allowlist + CSRF guard, Thai UI, DX design system.

## 4. Three routes

| Route | What happens | Touches our system? | Time | Risk |
|---|---|---|---|---|
| **1. Side-by-side** | Install stock V2 in `~/agentic-os`, point it at the existing vault (or a throwaway vault first). Use it for voice/Obsidian/HUD; ours stays the DX cockpit | No (adds folders + a plugin to the vault) | ~30–60 min + Python 3.12 | Two dashboards to keep in mind; vault gets V2 folders; autostart item; macOS beta |
| **2. Port features** | Rebuild chosen items (A, B, C, D, H…) inside our FastAPI + `web/` | Yes, on a feature branch | A+H: ~half day · B/C/D: ~1–2 days each · E: ~1 week | Normal build risk; no upstream updates for ported parts |
| **3. Hybrid** | Route 1 for F+G (things that cannot be ported cheaply) **and** port A/B/C/D into ours; later link the two (e.g. our radar card opens HUD) | Yes, small | Sum of the above, staged | Scope creep unless staged |

Not viable: replacing ours with V2 (loses radar/phone/LINE), or `aos update`/merge (refused by design).

## 5. Open decisions for the grill (the frontier)

1. **Goal** — what does Tae actually want from V2: voice, the Obsidian daily cockpit, the Jarvis look, Codex fallback, reliability, or "everything new"?
2. **One cockpit or two** — is running V2 beside ours acceptable long-term, or must everything end up in the DX Command Center?
3. **Vault** — may V2 add its folders/daily-note schema to `DX AI Agent OS`, or must it use a separate/throwaway vault?
4. **Voice** — is voice worth it if replies can only be spoken in English (pending the Thai test)?
5. **Second engine** — should Codex become selectable for runs, and does the "headless = Sonnet 5" lock still stand?
6. **Reliability first?** — do A (login warning) + B (health check/autostart) go first regardless of the rest?
7. **Buttons** — should Tae be able to change launcher buttons himself from the UI, or is editing by agent fine?
8. **Terminals in browser** — needed, given Tae already works in the Claude desktop app?
9. **Start at login** — allowed to add a login item on this Mac?
10. **Unfinished v11 work** — finish `.toh/plan.md` (radar actions refresh, all boxes open) before or after this upgrade?
11. **Where it lands** — which branch is the integration line (`feat/web-ui` vs `feat/radar-visual-v11`), and does phone/VPS mirror need any of the new features?

### Decisions made in the grill

- **D1 (2026-10-05, Tae: "ok" to the recommendation)** — Goal = reliability first: port A (Claude login expiry warning) + B (health check / auto-recover) into the DX Command Center. Voice and the Obsidian cockpit are a later side-by-side trial, not part of the first build. Resolves frontier items 1 and 6.

- **D2 (2026-10-05, Tae: "ok ลองเลย")** — Direction under trial: **stock V2 as the base, updated from the owner; our DX features live beside it as an add-on** (never edit V2 source). Verified in `obsidian-v2/scripts/aos/upgrade-checkout.mjs`: `update` only accepts a clean checkout whose origin is the official `ctskool/agentic-os-starter-v2`; a fork or edited checkout is refused. Survives updates: vault notes, `system/v2/dashboard.json`, registered personal skills. D1 is on hold: if the trial passes, A/B come from V2 instead of being ported.
- **Approved trial scope (Tae 2026-10-05):** install stock V2 at `~/agentic-os` with a **throwaway vault** (not `DX AI Agent OS`), install Python 3.12 for voice, ~3 GB download. **Not approved:** autostart at login, touching the real vault, entering any key, editing V2 source. Trial must report: doctor result, cockpit + HUD opening, Thai voice in/out, then Tae decides the main route.

## 6. Facts still to verify (agent's job, not Tae's)

- Kokoro Thai speech output; Whisper Thai accuracy on this Mac.
- Exactly which files/folders V2 setup writes into an existing vault (read `scripts/aos/vault.mjs` + `setup.mjs`).
- What `autostart on` installs on macOS (LaunchAgent name, what it starts).
- Bridge auth model (`bridge-auth.mjs`) vs our CSRF/origin guard, if terminals (E) are chosen.
- How V2 reads Claude/Codex usage (files vs API) compared with our `core.calc_usage_windows`.
