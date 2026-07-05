"""FastAPI backend for the v7 Command Center web UI (Next.js frontend).

Wraps EXISTING tested Python modules — core.py, registry.py, monitors.py,
config.py — as HTTP/SSE endpoints. No business logic is reimplemented here;
this is a thin adapter layer. Streamlit (:8501) keeps running unmodified.

Local-only by design: binds 127.0.0.1:8787, no auth (matches WEB-UI-BRIEF.md).

Run: uvicorn server:app --host 127.0.0.1 --port 8787
"""

import json
import subprocess
import threading
import time
from datetime import date, timedelta
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sse_starlette.sse import EventSourceResponse

import core
import monitors
from config import (
    CLAUDE_CLI,
    LIMITS,
    PERMISSION_MODE,
    QUICK_ROUTES,
    RUN_TIMEOUT_SEC,
    SKILLS,
    VAULT_PATH,
)

# registry.py imports streamlit for @st.cache_data — stub it out so we can
# reuse parse_registry()/scan_decision_inbox() without pulling in Streamlit.
import sys
import types

if "streamlit" not in sys.modules:
    _st_stub = types.ModuleType("streamlit")
    _st_stub.cache_data = lambda *a, **k: (lambda fn: fn) if not a or callable(a[0]) is False else a[0]

    def _cache_data(*args, **kwargs):
        # supports both @st.cache_data and @st.cache_data(ttl=600)
        if args and callable(args[0]):
            return args[0]
        return lambda fn: fn

    _st_stub.cache_data = _cache_data
    sys.modules["streamlit"] = _st_stub

import registry  # noqa: E402  (must come after the streamlit stub above)

app = FastAPI(title="Agentic OS Command Center API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3005", "http://127.0.0.1:3000", "http://127.0.0.1:3005"],
    allow_methods=["*"],
    allow_headers=["*"],
)

HANDOFF_PATH = Path(__file__).parent / "HANDOFF.md"
USAGE_COUNTS_FILE = Path(__file__).parent / "dashboard-data" / "usage-counts.json"


# ═══════════════════════════════════════════════════════════
# GET endpoints — read-only, wrap core/monitors/registry
# ═══════════════════════════════════════════════════════════


@app.get("/api/usage")
def get_usage():
    windows = core.calc_usage_windows()
    five_h_tokens = windows["five_hour"]["total"]
    week_tokens = windows["weekly"]["total"]
    five_h_pct = min(100.0, five_h_tokens / LIMITS["five_hour_tokens"] * 100.0) if LIMITS["five_hour_tokens"] else 0.0
    week_pct = min(100.0, week_tokens / LIMITS["weekly_tokens"] * 100.0) if LIMITS["weekly_tokens"] else 0.0
    core.quota_guard_check(five_h_pct)

    daily = core.ccusage_daily()
    today_str = date.today().isoformat()
    value_today = next((d.get("totalCost", 0.0) for d in daily if d.get("period") == today_str), 0.0)
    value_month = sum(
        d.get("totalCost", 0.0) for d in daily if (d.get("period") or "").startswith(date.today().strftime("%Y-%m"))
    )

    rate_limits = core.load_rate_limits()

    return {
        "five_hour": {
            "tokens": five_h_tokens,
            "pct": round(five_h_pct, 1),
            "limit": LIMITS["five_hour_tokens"],
            "limit_fmt": core.fmt_tokens(LIMITS["five_hour_tokens"]),
            "sessions": windows["five_hour"]["sessions"],
            "resets_at": (rate_limits.get("five_hour") or {}).get("resets_at"),
            "resets_in": core.fmt_time_until((rate_limits.get("five_hour") or {}).get("resets_at") or 0),
        },
        "weekly": {
            "tokens": week_tokens,
            "pct": round(week_pct, 1),
            "limit": LIMITS["weekly_tokens"],
            "limit_fmt": core.fmt_tokens(LIMITS["weekly_tokens"]),
            "resets_at": (rate_limits.get("weekly") or {}).get("resets_at"),
            "resets_in": core.fmt_time_until((rate_limits.get("weekly") or {}).get("resets_at") or 0),
        },
        "today": windows["today"],
        "value": {
            "today_usd": round(value_today, 2),
            "month_usd": round(value_month, 2),
            "today_fmt": core.fmt_cost(value_today),
            "month_fmt": core.fmt_cost(value_month),
        },
        "metrics": core.calc_metrics(),
    }


@app.get("/api/sessions")
def get_sessions():
    return {"sessions": monitors.scan_live_sessions()}


@app.get("/api/devservers")
def get_devservers():
    return {"servers": monitors.scan_dev_servers()}


@app.get("/api/projects")
def get_projects():
    rows = registry.parse_registry()
    entries = registry.parse_long_term()
    out = []
    for proj in rows:
        newest = registry.newest_entry_for(proj, entries)
        out.append({**proj, "latest_entry": newest})
    return {"projects": out}


@app.get("/api/inbox")
def get_inbox():
    items = registry.scan_decision_inbox(str(HANDOFF_PATH))
    return {"items": items}


@app.get("/api/artifacts")
def get_artifacts():
    return {"recommendations": core.load_recommendations()}


@app.get("/api/runs")
def get_runs(limit: int = 20):
    files = core.list_recent_runs(limit=limit)
    out = []
    for f in files:
        meta = core._parse_frontmatter(f)
        out.append({
            "file": f.name,
            "path": str(f),
            "skill": meta.get("skill"),
            "time": meta.get("time"),
            "cost_usd": meta.get("cost_usd"),
            "mtime": f.stat().st_mtime,
        })
    return {"runs": out}


@app.get("/api/runs/{run_file}")
def get_run_detail(run_file: str):
    for day_dir in (core.RUNS_DIR.iterdir() if core.RUNS_DIR.exists() else []):
        candidate = day_dir / run_file
        if candidate.exists():
            return {"content": candidate.read_text(encoding="utf-8", errors="replace")}
    return JSONResponse({"error": "not found"}, status_code=404)


@app.get("/api/skills")
def get_skills():
    """The 13 launcher cards + quick routes, straight from config.py."""
    return {
        "skills": [
            {k: v for k, v in s.items() if k != "prompt_template"} | {"id": core.slugify(s["label"])}
            for s in SKILLS
        ],
        "quick_routes": [{"label": name, "path": str(p)} for name, p in QUICK_ROUTES],
    }


@app.get("/api/usage-counts")
def get_usage_counts():
    if USAGE_COUNTS_FILE.exists():
        try:
            return json.loads(USAGE_COUNTS_FILE.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def _bump_usage_count(skill_id: str):
    USAGE_COUNTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    data = {}
    if USAGE_COUNTS_FILE.exists():
        try:
            data = json.loads(USAGE_COUNTS_FILE.read_text(encoding="utf-8"))
        except Exception:
            data = {}
    data[skill_id] = int(data.get(skill_id, 0)) + 1
    USAGE_COUNTS_FILE.write_text(json.dumps(data), encoding="utf-8")


# ═══════════════════════════════════════════════════════════
# POST /api/run — SSE stream of a skill run (subprocess claude -p)
# ═══════════════════════════════════════════════════════════


def _resolve_prompt(skill_label: str | None, prompt: str | None, user_input: str) -> tuple[str, str]:
    if skill_label:
        skill = next((s for s in SKILLS if s["label"] == skill_label), None)
        if skill:
            template = skill["prompt_template"]
            filled = template.replace("{input}", user_input) if "{input}" in template else template
            return skill_label, filled
    return (skill_label or "Quick Prompt", prompt or user_input or "")


@app.post("/api/run")
async def run_skill(request: Request):
    body = await request.json()
    skill_label = body.get("skill_label")
    user_input = body.get("input", "")
    prompt_override = body.get("prompt")
    label, prompt = _resolve_prompt(skill_label, prompt_override, user_input)

    if not prompt.strip():
        return JSONResponse({"error": "empty prompt"}, status_code=400)

    async def event_gen():
        proc = subprocess.Popen(
            [
                str(CLAUDE_CLI), "-p", prompt,
                "--permission-mode", PERMISSION_MODE,
                "--output-format", "stream-json",
                "--verbose",
            ],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            cwd=str(VAULT_PATH), text=True, bufsize=1,
            encoding="utf-8", errors="replace",
        )
        accumulated_text = ""
        phases: list[str] = []
        cost_usd = None
        tokens_in = tokens_out = None
        error = None
        start = time.time()

        yield {"event": "phase", "data": json.dumps({"phase": "starting", "label": label})}

        try:
            for line in iter(proc.stdout.readline, ""):
                line = line.strip()
                if not line:
                    continue
                try:
                    evt = json.loads(line)
                except json.JSONDecodeError:
                    accumulated_text += line + "\n"
                    continue
                t = evt.get("type")
                if t == "assistant":
                    for block in evt.get("message", {}).get("content", []):
                        if block.get("type") == "text":
                            chunk = block.get("text", "")
                            accumulated_text += chunk
                            yield {"event": "text", "data": json.dumps({"chunk": chunk})}
                        elif block.get("type") == "tool_use":
                            name = block.get("name", "tool")
                            phases.append(name)
                            yield {"event": "phase", "data": json.dumps({"phase": name})}
                elif t == "result":
                    cost_usd = evt.get("total_cost_usd") or evt.get("cost_usd")
                    usage = evt.get("usage", {})
                    tokens_in = usage.get("input_tokens")
                    tokens_out = usage.get("output_tokens")
                    if evt.get("subtype") != "success":
                        error = evt.get("result") or evt.get("subtype")
                elif t == "system" and evt.get("subtype") == "init":
                    servers = evt.get("mcp_servers")
                    if servers:
                        core.save_mcp_state(servers)
                elif t == "rate_limit_event":
                    core.save_rate_limit(evt)

                if time.time() - start > RUN_TIMEOUT_SEC:
                    proc.kill()
                    error = "timeout"
                    break

            proc.wait(timeout=10)
            if proc.returncode != 0 and not error:
                stderr_text = proc.stderr.read() if proc.stderr else ""
                error = f"exit {proc.returncode}: {stderr_text[:500]}"
        except Exception as e:
            error = str(e)

        ok = error is None
        output = accumulated_text.strip() or "(no text output)"
        saved_path = None
        if ok:
            meta = {
                "cost_usd": cost_usd, "tokens_in": tokens_in, "tokens_out": tokens_out,
                "phases": ", ".join(phases) or None,
            }
            saved = core.save_run_output(label, prompt, output, meta=meta)
            saved_path = str(saved)
            core.log_run(label, ok=True)
            core.notify_run_done(label, ok=True, cost=cost_usd)
            if skill_label:
                _bump_usage_count(core.slugify(skill_label))
        else:
            core.log_run(label, ok=False)
            core.notify_run_done(label, ok=False, cost=None)

        yield {
            "event": "done",
            "data": json.dumps({
                "ok": ok, "error": error, "cost_usd": cost_usd,
                "tokens_in": tokens_in, "tokens_out": tokens_out,
                "output": output, "saved_path": saved_path,
            }),
        }

    return EventSourceResponse(event_gen())


# ═══════════════════════════════════════════════════════════
# POST /api/chat — SSE stream, multi-turn via --resume (reuses chat_backend logic)
# ═══════════════════════════════════════════════════════════


@app.post("/api/chat")
async def chat(request: Request):
    body = await request.json()
    message = body.get("message", "")
    session_id = body.get("session_id")

    if not message.strip():
        return JSONResponse({"error": "empty message"}, status_code=400)

    async def event_gen():
        cmd = [str(CLAUDE_CLI), "-p", message, "--output-format", "stream-json", "--verbose"]
        if session_id:
            cmd += ["--resume", session_id]

        proc = subprocess.Popen(
            cmd, cwd=str(Path.home()), stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, bufsize=1, encoding="utf-8", errors="replace",
        )
        text = ""
        tool_names: list[str] = []
        cost_usd = None
        sid = session_id
        error = None

        try:
            for line in iter(proc.stdout.readline, ""):
                line = line.strip()
                if not line:
                    continue
                try:
                    evt = json.loads(line)
                except json.JSONDecodeError:
                    continue
                new_sid = evt.get("session_id")
                if new_sid:
                    sid = new_sid
                t = evt.get("type")
                if t == "assistant":
                    for block in evt.get("message", {}).get("content", []):
                        if block.get("type") == "text":
                            chunk = block.get("text", "")
                            text += chunk
                            yield {"event": "text", "data": json.dumps({"chunk": chunk})}
                        elif block.get("type") == "tool_use":
                            name = block.get("name", "tool")
                            tool_names.append(name)
                            yield {"event": "tool", "data": json.dumps({"name": name})}
                elif t == "result":
                    cost_usd = evt.get("total_cost_usd") or evt.get("cost_usd")
                    if evt.get("subtype") != "success":
                        error = evt.get("result") or evt.get("subtype")
            proc.wait(timeout=300)
            if proc.returncode != 0 and not error:
                stderr_text = proc.stderr.read() if proc.stderr else ""
                error = f"exit {proc.returncode}: {stderr_text[:300]}"
        except Exception as e:
            error = str(e)

        yield {
            "event": "done",
            "data": json.dumps({
                "text": text or None, "tool_names": tool_names,
                "cost_usd": cost_usd, "session_id": sid, "error": error,
            }),
        }

    return EventSourceResponse(event_gen())


# ═══════════════════════════════════════════════════════════
# POST /api/open — reveal a path in Finder · POST /api/kill — kill a dev server
# ═══════════════════════════════════════════════════════════


@app.post("/api/open")
async def open_path(request: Request):
    body = await request.json()
    path = body.get("path")
    if not path or not Path(path).exists():
        return JSONResponse({"error": "path not found"}, status_code=404)
    subprocess.Popen(["open", "-R", path] if Path(path).is_file() else ["open", path])
    return {"ok": True}


@app.post("/api/kill")
async def kill_pid(request: Request):
    body = await request.json()
    pid = str(body.get("pid", ""))
    if not pid:
        return JSONResponse({"error": "pid required"}, status_code=400)
    ok = monitors.kill_server(pid)
    return {"ok": ok}


@app.get("/api/health")
def health():
    return {"ok": True, "ts": time.time()}
