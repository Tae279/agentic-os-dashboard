"""Pure-Python core logic — shared by app.py (Streamlit) and server.py (FastAPI).

Extracted from app.py 2026-07-06 so the new Next.js/FastAPI web UI can wrap the
SAME tested functions instead of re-implementing them. No `streamlit` import
here — that's the whole point (app.py keeps its st.cache_resource RT dict and
imports everything else from this module).

ponytail: straight lift-and-move, no behavior changes. Streamlit-only bits
(RT global, st.session_state, dialogs) stay in app.py.
"""

import json
import re
import shutil
import subprocess
import sys
import time
from datetime import date, datetime, timedelta
from pathlib import Path
from urllib.parse import quote

from config import (
    CLAUDE_CLI,
    DAILY_NOTES_DIR,
    DRAFTS_AWAITING,
    RUNS_DIR,
    SESSION_META_DIR,
    VAULT_NAME,
    VAULT_PATH,
)

CACHE_DIR = Path(__file__).parent / ".cache"
MCP_CACHE = CACHE_DIR / "mcp.json"
RATE_CACHE = CACHE_DIR / "rate_limits.json"
ROUTINES_LEDGER = CACHE_DIR / "routines.json"
QUOTA_ALERT_STATE = CACHE_DIR / "quota-alert.json"
RECOMMENDATIONS_FILE = Path(__file__).parent / "dashboard-data" / "recommendations.json"

_FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---", re.DOTALL)


# ─── formatting helpers ───

def slugify(text: str) -> str:
    text = re.sub(r"[^\w\s-]", "", text.lower())
    return re.sub(r"[\s_-]+", "-", text).strip("-")


def fmt_ago(sec: int) -> str:
    if sec < 60:
        return f"{sec}s"
    if sec < 3600:
        return f"{sec // 60}m"
    if sec < 86400:
        return f"{sec // 3600}h"
    return f"{sec // 86400}d"


def fmt_time_until(ts: int) -> str:
    if not ts:
        return "—"
    delta = int(ts - time.time())
    if delta <= 0:
        return "now"
    h = delta // 3600
    m = (delta % 3600) // 60
    if h > 24:
        d = h // 24
        h = h % 24
        return f"{d}d {h}h"
    if h > 0:
        return f"{h}h {m:02d}m"
    return f"{m}m"


def fmt_tokens(n: int) -> str:
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n / 1_000:.1f}k"
    return str(n)


def fmt_cost(c: float) -> str:
    if c >= 100:
        return f"${c:.0f}"
    if c >= 10:
        return f"${c:.1f}"
    return f"${c:.2f}"


def _to_float(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return 0.0


def _to_int(v):
    try:
        return int(v)
    except (TypeError, ValueError):
        return 0


# ─── daily notes / run logging ───

def today_daily_note() -> Path:
    return DAILY_NOTES_DIR / f"{date.today().isoformat()}.md"


def read_activity() -> str:
    note = today_daily_note()
    if not note.exists():
        return "_No activity yet today._"
    return note.read_text(encoding="utf-8", errors="replace")


def log_run(label: str, ok: bool):
    note = today_daily_note()
    note.parent.mkdir(parents=True, exist_ok=True)
    if not note.exists():
        note.write_text(f"# {date.today().isoformat()}\n\n## Runs\n\n", encoding="utf-8")
    status = "OK" if ok else "ERR"
    stamp = datetime.now().strftime("%H:%M")
    with note.open("a", encoding="utf-8") as f:
        f.write(f"- {stamp} [{status}] {label}\n")


def save_run_output(label: str, prompt: str, output: str, meta: dict | None = None) -> Path:
    today_str = date.today().isoformat()
    now = datetime.now().strftime("%H-%M")
    day_dir = RUNS_DIR / today_str
    day_dir.mkdir(parents=True, exist_ok=True)
    path = day_dir / f"{now}-{slugify(label)}.md"
    meta_block = ""
    if meta:
        for k, v in meta.items():
            if v is not None:
                meta_block += f"{k}: {v}\n"
    body = (
        f"---\nskill: {label}\ntime: {datetime.now().isoformat(timespec='seconds')}\n"
        f"{meta_block}---\n\n"
        f"**Prompt**\n\n```\n{prompt}\n```\n\n"
        f"**Output**\n\n{output}\n"
    )
    path.write_text(body, encoding="utf-8")
    return path


def obsidian_uri(vault_path: Path) -> str:
    try:
        rel = vault_path.relative_to(VAULT_PATH).as_posix()
    except ValueError:
        return f"file://{quote(str(vault_path))}"
    return f"obsidian://open?vault={quote(VAULT_NAME)}&file={quote(rel)}"


def open_claude_terminal() -> None:
    """Open an interactive claude session in the vault — cross-platform."""
    if sys.platform == "darwin":
        cmd = f'cd \\"{VAULT_PATH}\\" && \\"{CLAUDE_CLI}\\"'
        script = (
            'tell application "Terminal"\n'
            f'  do script "{cmd}"\n'
            "  activate\n"
            "end tell"
        )
        subprocess.Popen(["osascript", "-e", script])
        return
    wt = Path(r"C:\Users\Chase\AppData\Local\Microsoft\WindowsApps\wt.exe")
    if wt.exists():
        subprocess.Popen(
            [str(wt), "-d", str(VAULT_PATH), str(CLAUDE_CLI)],
            creationflags=subprocess.CREATE_NEW_CONSOLE,
        )
    else:
        subprocess.Popen(
            ["cmd.exe", "/k", f'cd /d "{VAULT_PATH}" && "{CLAUDE_CLI}"'],
            creationflags=subprocess.CREATE_NEW_CONSOLE,
        )


def list_recent_runs(limit: int = 10):
    if not RUNS_DIR.exists():
        return []
    files = sorted(RUNS_DIR.glob("*/*.md"), key=lambda p: p.stat().st_mtime, reverse=True)
    return files[:limit]


def list_awaiting_approvals():
    if not DRAFTS_AWAITING.exists():
        return []
    return sorted(DRAFTS_AWAITING.glob("*.md"), key=lambda p: p.stat().st_mtime, reverse=True)


def list_vault_pulse(limit: int = 6):
    """Recent vault .md changes, sorted by mtime desc."""
    if not VAULT_PATH.exists():
        return []
    skip_parts = {".obsidian", ".trash", "node_modules", ".git"}
    files = []
    for p in VAULT_PATH.rglob("*.md"):
        if skip_parts & set(p.parts):
            continue
        try:
            st_ = p.stat()
        except OSError:
            continue
        files.append((p, st_.st_mtime, st_.st_ctime))
    files.sort(key=lambda t: t[1], reverse=True)
    out = []
    for p, mtime, ctime in files[:limit]:
        verb = "created" if abs(mtime - ctime) < 5 else "edited"
        out.append({"path": str(p), "name": p.name, "mtime": mtime, "verb": verb})
    return out


# ─── metrics / run scanning ───

def _parse_frontmatter(path: Path) -> dict:
    text = path.read_text(encoding="utf-8", errors="replace")[:2500]
    meta = {"file": path.name, "path": str(path)}
    m = _FRONTMATTER_RE.match(text)
    if m:
        for line in m.group(1).splitlines():
            if ":" in line:
                k, _, v = line.partition(":")
                meta[k.strip()] = v.strip()
    return meta


def scan_runs(days: int = 30) -> list[dict]:
    if not RUNS_DIR.exists():
        return []
    cutoff = date.today() - timedelta(days=days)
    out = []
    for day_dir in RUNS_DIR.iterdir():
        if not day_dir.is_dir():
            continue
        try:
            d = date.fromisoformat(day_dir.name)
        except ValueError:
            continue
        if d < cutoff:
            continue
        for f in day_dir.glob("*.md"):
            meta = _parse_frontmatter(f)
            meta["date"] = d.isoformat()
            out.append(meta)
    return out


def calc_metrics() -> dict:
    runs = scan_runs(30)
    today_str = date.today().isoformat()
    month_str = date.today().strftime("%Y-%m")
    runs_today = sum(1 for r in runs if r.get("date") == today_str)
    cost_month = sum(
        _to_float(r.get("cost_usd"))
        for r in runs if (r.get("date") or "").startswith(month_str)
    )
    tokens_30d = sum(
        _to_int(r.get("tokens_in")) + _to_int(r.get("tokens_out"))
        for r in runs
    )
    approvals = len(list_awaiting_approvals())
    return {
        "runs_today": runs_today,
        "cost_month": cost_month,
        "tokens_30d": tokens_30d,
        "approvals": approvals,
    }


# ─── MCP / rate limit cache ───

def save_mcp_state(servers: list):
    CACHE_DIR.mkdir(exist_ok=True)
    try:
        MCP_CACHE.write_text(json.dumps(servers), encoding="utf-8")
    except Exception:
        pass


def load_mcp_state() -> list:
    if MCP_CACHE.exists():
        try:
            return json.loads(MCP_CACHE.read_text(encoding="utf-8"))
        except Exception:
            return []
    return []


def save_rate_limit(event: dict):
    CACHE_DIR.mkdir(exist_ok=True)
    info = event.get("rate_limit_info") or {}
    kind = info.get("rateLimitType")
    if not kind:
        return
    data = load_rate_limits()
    data[kind] = {
        "status": info.get("status"),
        "resets_at": info.get("resetsAt"),
        "overage_status": info.get("overageStatus"),
        "overage_resets_at": info.get("overageResetsAt"),
        "is_using_overage": info.get("isUsingOverage"),
        "captured_at": int(time.time()),
    }
    try:
        RATE_CACHE.write_text(json.dumps(data), encoding="utf-8")
    except Exception:
        pass


def load_rate_limits() -> dict:
    if RATE_CACHE.exists():
        try:
            return json.loads(RATE_CACHE.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def _notify_macos(title: str, message: str) -> None:
    try:
        subprocess.run(
            ["osascript", "-e", f'display notification "{message}" with title "{title}"'],
            capture_output=True, timeout=5,
        )
    except Exception:
        pass


def quota_guard_check(pct: float) -> None:
    if pct < 80:
        return
    block_key = datetime.now().replace(minute=0, second=0, microsecond=0).strftime("%Y-%m-%d-%H")
    try:
        state = json.loads(QUOTA_ALERT_STATE.read_text(encoding="utf-8")) if QUOTA_ALERT_STATE.exists() else {}
    except Exception:
        state = {}
    if state.get("block") == block_key:
        return
    _notify_macos("Agentic OS", f"⚠️ 5-hour quota at {pct:.0f}% — approaching cap")
    try:
        CACHE_DIR.mkdir(exist_ok=True)
        QUOTA_ALERT_STATE.write_text(json.dumps({"block": block_key}), encoding="utf-8")
    except Exception:
        pass


# ─── ccusage / usage windows ───

def _ccusage_metas() -> list[dict]:
    cache = CACHE_DIR / "ccusage-metas.json"
    try:
        if cache.exists() and time.time() - cache.stat().st_mtime < 300:
            return json.loads(cache.read_text(encoding="utf-8"))
    except Exception:
        pass

    ccusage_bin = shutil.which("ccusage") or str(Path.home() / ".npm-global" / "bin" / "ccusage")
    metas: list[dict] = []
    try:
        res = subprocess.run([ccusage_bin, "blocks", "--json"], capture_output=True, text=True, timeout=120)
        for b in json.loads(res.stdout).get("blocks", []):
            if b.get("isGap"):
                continue
            tc = b.get("tokenCounts", {})
            try:
                dt = datetime.fromisoformat(b["startTime"].replace("Z", "+00:00")).astimezone()
                start_local = dt.replace(tzinfo=None).isoformat()
            except Exception:
                continue
            metas.append({
                "start_time": start_local,
                "input_tokens": int(tc.get("inputTokens") or 0),
                "output_tokens": int(tc.get("outputTokens") or 0),
            })
        CACHE_DIR.mkdir(exist_ok=True)
        cache.write_text(json.dumps(metas), encoding="utf-8")
    except Exception:
        return []
    return metas


def _read_session_metas() -> list[dict]:
    out = []
    if SESSION_META_DIR.exists():
        for f in SESSION_META_DIR.glob("*.json"):
            try:
                d = json.loads(f.read_text(encoding="utf-8", errors="replace"))
                if "start_time" in d and ("input_tokens" in d or "output_tokens" in d):
                    out.append(d)
            except Exception:
                continue
    if not out:
        out = _ccusage_metas()
    return out


def _parse_session_time(d: dict) -> datetime | None:
    t = d.get("start_time")
    if not t:
        return None
    try:
        if t.endswith("Z"):
            t = t.replace("Z", "+00:00")
        dt = datetime.fromisoformat(t)
        return dt.replace(tzinfo=None)
    except Exception:
        return None


ROUTINES_LEDGER = CACHE_DIR / "routines.json"


def _load_routines_ledger() -> dict:
    if ROUTINES_LEDGER.exists():
        try:
            return json.loads(ROUTINES_LEDGER.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def _save_routines_ledger(data: dict):
    CACHE_DIR.mkdir(exist_ok=True)
    ROUTINES_LEDGER.write_text(json.dumps(data), encoding="utf-8")


def count_routines_today() -> int:
    today_str = date.today().isoformat()
    return int(_load_routines_ledger().get(today_str, 0))


def increment_routine_count():
    today_str = date.today().isoformat()
    data = _load_routines_ledger()
    data[today_str] = int(data.get(today_str, 0)) + 1
    _save_routines_ledger(data)


def calc_usage_windows() -> dict:
    """Aggregate Claude Code session token usage across 5h, 7d, today windows."""
    now = datetime.now()
    five_h_ago = now - timedelta(hours=5)
    seven_d_ago = now - timedelta(days=7)
    today_start = datetime.combine(date.today(), datetime.min.time())

    metas = _read_session_metas()

    def agg(metas_list, since):
        in_tok = out_tok = sessions = 0
        for m in metas_list:
            t = _parse_session_time(m)
            if t is None or t < since:
                continue
            in_tok += int(m.get("input_tokens") or 0)
            out_tok += int(m.get("output_tokens") or 0)
            sessions += 1
        return {"input": in_tok, "output": out_tok, "total": in_tok + out_tok, "sessions": sessions}

    runs_today = [r for r in scan_runs(2) if r.get("date") == date.today().isoformat()]
    cost_today = sum(_to_float(r.get("cost_usd")) for r in runs_today)
    routine_count = count_routines_today()

    return {
        "five_hour": agg(metas, five_h_ago),
        "weekly": agg(metas, seven_d_ago),
        "today": {
            **agg(metas, today_start),
            "routines": routine_count,
            "cost": cost_today,
            "runs": len(runs_today),
        },
    }


def ccusage_daily() -> list[dict]:
    cache = CACHE_DIR / "ccusage-daily.json"
    try:
        if cache.exists() and time.time() - cache.stat().st_mtime < 600:
            return json.loads(cache.read_text(encoding="utf-8"))
    except Exception:
        pass

    ccusage_bin = shutil.which("ccusage") or str(Path.home() / ".npm-global" / "bin" / "ccusage")
    daily: list[dict] = []
    try:
        res = subprocess.run([ccusage_bin, "daily", "--json"], capture_output=True, text=True, timeout=120)
        daily = json.loads(res.stdout).get("daily", [])
        CACHE_DIR.mkdir(exist_ok=True)
        cache.write_text(json.dumps(daily), encoding="utf-8")
    except Exception:
        return []
    return daily


# ─── recommendations.json (AI-suggested next actions) ───

def load_recommendations() -> dict:
    if not RECOMMENDATIONS_FILE.exists():
        return {"must_do": [], "nice_to_do": [], "ideas": []}
    try:
        return json.loads(RECOMMENDATIONS_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {"must_do": [], "nice_to_do": [], "ideas": []}


# ─── hermes (Telegram notify) ───

_hermes_send_cmd_cache: list | None = None


def _hermes_send_command() -> list | None:
    global _hermes_send_cmd_cache
    if _hermes_send_cmd_cache is not None:
        return _hermes_send_cmd_cache or None
    hermes_bin = shutil.which("hermes")
    if not hermes_bin:
        _hermes_send_cmd_cache = []
        return None
    try:
        res = subprocess.run([hermes_bin, "--help"], capture_output=True, text=True, timeout=10)
        help_text = res.stdout + res.stderr
    except Exception:
        _hermes_send_cmd_cache = []
        return None
    for cmd in ("send", "message", "notify"):
        if re.search(rf"^\s*{cmd}\b", help_text, re.MULTILINE):
            _hermes_send_cmd_cache = [hermes_bin, cmd]
            return _hermes_send_cmd_cache
    _hermes_send_cmd_cache = []
    return None


def notify_run_done(label: str, ok: bool, cost: float | None) -> None:
    cost_txt = fmt_cost(_to_float(cost)) if cost else "$0.00"
    message = f"✅ {label} เสร็จแล้ว · {cost_txt}" if ok else f"❌ {label} ล้มเหลว"
    _notify_macos("Agentic OS", message)
    try:
        send_cmd = _hermes_send_command()
        if send_cmd:
            subprocess.run(send_cmd + ["-t", "telegram", message, "-q"], capture_output=True, timeout=10)
    except Exception:
        pass


if __name__ == "__main__":
    # ponytail self-check: functions run without crashing, shapes are sane
    assert slugify("Hello World! 123") == "hello-world-123"
    assert fmt_ago(30) == "30s" and fmt_ago(90) == "1m"
    assert fmt_tokens(1_500_000) == "1.5M"
    assert fmt_cost(5.5) == "$5.50"
    w = calc_usage_windows()
    assert set(w.keys()) == {"five_hour", "weekly", "today"}
    m = calc_metrics()
    assert "runs_today" in m
    recs = load_recommendations()
    assert isinstance(recs.get("must_do"), list)
    print("OK — core.py self-check passed")
