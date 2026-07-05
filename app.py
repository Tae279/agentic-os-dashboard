import subprocess
import sys
import threading
import queue
import re
import json
import time
import shutil
import base64
from datetime import date, datetime, timedelta
from pathlib import Path
from urllib.parse import quote
from itertools import groupby

import streamlit as st
import altair as alt
import pandas as pd

from config import (
    VAULT_PATH,
    VAULT_NAME,
    CLAUDE_CLI,
    DAILY_NOTES_DIR,
    RUNS_DIR,
    DRAFTS_AWAITING,
    SKILLS,
    RUN_TIMEOUT_SEC,
    PERMISSION_MODE,
    LIMITS,
    SESSION_META_DIR,
    CLAUDE_PLAN,
    QUICK_ROUTES,
)

st.set_page_config(page_title="Agentic OS", page_icon="◆", layout="wide")

# ═══════════════════════════════════════════════════════════
# GLOBAL RUNTIME (shared across reruns, lives in module scope)
# ═══════════════════════════════════════════════════════════


@st.cache_resource
def get_runtime():
    return {
        "proc": None,
        "buffer": [],           # raw stdout text chunks
        "text": "",             # accumulated assistant text (parsed)
        "phases": [],           # tool_use phase log
        "current_phase": None,  # latest phase label
        "cost_usd": None,
        "tokens_in": None,
        "tokens_out": None,
        "done": False,
        "cancelled": False,
        "error": None,
        "start_time": None,
    }


RT = get_runtime()


def reset_runtime():
    RT["proc"] = None
    RT["buffer"] = []
    RT["text"] = ""
    RT["phases"] = []
    RT["current_phase"] = None
    RT["cost_usd"] = None
    RT["tokens_in"] = None
    RT["tokens_out"] = None
    RT["done"] = False
    RT["cancelled"] = False
    RT["error"] = None
    RT["start_time"] = None
    RT["last_event_time"] = None
    RT["stall_notified"] = False


# ═══════════════════════════════════════════════════════════
# STYLES
# ═══════════════════════════════════════════════════════════

from theme import PREMIUM_CSS  # noqa: F401 — shared cockpit theme


# ═══════════════════════════════════════════════════════════
# BOOT ANIMATION CSS — injected only on first render of a session.
# Prevents animations replaying on every Streamlit rerun (button clicks etc).
# ═══════════════════════════════════════════════════════════
BOOT_ANIMATION_CSS = """
<style>
@keyframes boot-rise {
    0%   { opacity: 0; transform: translateY(28px) scale(0.96); }
    100% { opacity: 1; transform: translateY(0) scale(1); }
}
@keyframes boot-slide-l {
    0%   { opacity: 0; transform: translateX(-40px); }
    100% { opacity: 1; transform: translateX(0); }
}
@keyframes boot-slide-r {
    0%   { opacity: 0; transform: translateX(40px); }
    100% { opacity: 1; transform: translateX(0); }
}
.title-row {
    animation: boot-rise 0.75s cubic-bezier(0.22, 1, 0.36, 1) 0s both;
}
.quicknav {
    animation: boot-rise 0.75s cubic-bezier(0.22, 1, 0.36, 1) 0.18s both;
}
[data-testid="stColumn"]:nth-of-type(1) .gauge-card,
[data-testid="column"]:nth-of-type(1) .gauge-card {
    animation: boot-slide-l 1.45s cubic-bezier(0.22, 1, 0.36, 1) 0.55s both;
}
[data-testid="stColumn"]:nth-of-type(2) .gauge-card,
[data-testid="column"]:nth-of-type(2) .gauge-card {
    animation: boot-rise 1.45s cubic-bezier(0.22, 1, 0.36, 1) 0.80s both;
}
[data-testid="stColumn"]:nth-of-type(3) .gauge-card,
[data-testid="column"]:nth-of-type(3) .gauge-card {
    animation: boot-slide-r 1.45s cubic-bezier(0.22, 1, 0.36, 1) 0.55s both;
}
.chart-card {
    animation: boot-rise 0.85s cubic-bezier(0.22, 1, 0.36, 1) 0.55s both;
}
.mcp-strip {
    animation: boot-rise 0.55s cubic-bezier(0.22, 1, 0.36, 1) 0.95s both;
}
</style>
"""

import webbrowser
import monitors
import theme
import chat_backend
from registry import scan_decision_inbox
theme.inject()

st.markdown("""<style>
.peek-card{background:var(--bg-card);border:1px solid var(--ring-soft);border-radius:8px;padding:.7rem .9rem;margin-top:.9rem}
.peek-card .cat-label{font-family:'JetBrains Mono',monospace;font-size:.66rem;letter-spacing:.12em;text-transform:uppercase;color:var(--fg-dim);margin-bottom:.4rem}
.peek-row{display:flex;align-items:center;gap:.5rem;font-size:.8rem;padding:.18rem 0;color:var(--fg)}
.peek-dot{width:7px;height:7px;border-radius:50%;flex:none}
.peek-dot.executing{background:var(--accent);box-shadow:0 0 6px var(--accent)}
.peek-dot.thinking{background:#5c8dff}
.peek-dot.idle{background:var(--fg-mute)}
.peek-meta{color:var(--fg-mute);font-family:'JetBrains Mono',monospace;font-size:.68rem;margin-left:auto}
.peek-port{font-family:'JetBrains Mono',monospace;color:#8fb3ff;font-size:.78rem}
.qroute-row .stButton>button{font-size:.66rem!important;padding:.3rem .2rem!important}
</style>""", unsafe_allow_html=True)


# Boot animations only on fresh page mount — not on every Streamlit rerun (button clicks).
# Session state persists per tab; fresh Ctrl+R creates a new session → animation replays.
if not st.session_state.get("_boot_animated"):
    st.session_state._boot_animated = True
    st.markdown(BOOT_ANIMATION_CSS, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════


def html_escape(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


# ═══════════════════════════════════════════════════════════
# RUN HISTORY VIEWER — @st.dialog rendering a run .md in-app
# ═══════════════════════════════════════════════════════════


@st.dialog("📖 Run detail", width="large")
def render_run_dialog(run_path: Path):
    meta = _parse_frontmatter(run_path)
    header_bits = [f"{k}: {v}" for k, v in meta.items() if k not in ("file", "path")]
    st.markdown(
        f'<div class="caption-mono" style="color:var(--fg-dim);margin-bottom:.6rem">'
        f'{html_escape(" · ".join(header_bits))}</div>',
        unsafe_allow_html=True,
    )
    try:
        body = run_path.read_text(encoding="utf-8", errors="replace")
    except OSError as e:
        body = f"(อ่านไฟล์ไม่ได้: {e})"
    st.markdown(body)


# ─── Floating 💬 chat button (fixed bottom-right, both pages via theme.py CSS) ───
# ponytail: a real st.button in a container CSS pins via .fab-chat-anchor
# (theme.py) — more reliable across Streamlit versions than an anchor +
# query-param trick (no page reload, no extra rerun to detect it).
with st.container():
    st.markdown('<div class="fab-chat-anchor"></div>', unsafe_allow_html=True)
    if st.button("💬", key="fab_chat_btn", help="คุยกับ Claude"):
        chat_backend.render_chat_dialog(html_escape)


@st.cache_resource
def _asset_data_url(filename: str) -> str:
    p = Path(__file__).parent / "assets" / filename
    if not p.exists():
        return ""
    b64 = base64.b64encode(p.read_bytes()).decode("ascii")
    return f"data:image/png;base64,{b64}"


MASCOT_IDLE_URL = _asset_data_url("robot-idle-normalized.png")
MASCOT_RUN_URL = _asset_data_url("robot-run-normalized.png")
# 7 frames per row, 12×32 px each → sheet is 84×32 native.
MASCOT_FRAMES = 7
MASCOT_FRAME_W = 12
MASCOT_FRAME_H = 32
MASCOT_SCALE = 3  # rendered at 36×96 px (scaled 3×)


PHASE_LABELS = {
    "Read": "reading file",
    "Write": "writing file",
    "Edit": "editing file",
    "MultiEdit": "editing file",
    "Bash": "running command",
    "Glob": "finding files",
    "Grep": "searching code",
    "Task": "delegating subagent",
    "Agent": "spawning agent",
    "TodoWrite": "tracking tasks",
    "WebFetch": "fetching page",
    "WebSearch": "searching web",
    "NotebookEdit": "editing notebook",
    "Skill": "invoking skill",
    "ToolSearch": "searching tools",
    "EnterPlanMode": "entering plan mode",
    "ExitPlanMode": "exiting plan mode",
    "EnterWorktree": "entering worktree",
    "ExitWorktree": "exiting worktree",
    "ScheduleWakeup": "scheduling wakeup",
    "SendMessage": "sending message",
    "TaskCreate": "creating task",
    "TaskUpdate": "updating task",
    "TaskGet": "reading task",
    "TaskList": "listing tasks",
    "TaskStop": "stopping task",
    "TaskOutput": "reading task output",
    "AskUserQuestion": "asking question",
    "PushNotification": "sending notification",
    "RemoteTrigger": "triggering remote",
    "Monitor": "monitoring process",
    "CronCreate": "creating schedule",
    "CronDelete": "deleting schedule",
    "CronList": "listing schedules",
    "TeamCreate": "creating team",
    "TeamDelete": "deleting team",
}


def pretty_phase(name: str) -> str:
    if not name:
        return "starting"
    if name in PHASE_LABELS:
        return PHASE_LABELS[name]
    if name.startswith("mcp__"):
        parts = name.split("__")
        if len(parts) >= 3:
            service = parts[1].replace("_", " ")
            action = "__".join(parts[2:]).replace("_", " ")
            return f"{service} · {action}"
    # CamelCase → spaced, lowercase
    spaced = re.sub(r"(?<!^)(?=[A-Z])", " ", name).lower()
    return spaced or name


def slugify(text: str) -> str:
    s = re.sub(r"[^a-zA-Z0-9]+", "-", text).strip("-").lower()
    return s or "run"


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
    # Dashboard-local files (daily notes, runs, drafts under DASHBOARD_DATA)
    # live OUTSIDE the Obsidian vault — link those as file:// instead of
    # crashing on relative_to().
    try:
        rel = vault_path.relative_to(VAULT_PATH).as_posix()
    except ValueError:
        return f"file://{quote(str(vault_path))}"
    return f"obsidian://open?vault={quote(VAULT_NAME)}&file={quote(rel)}"


def open_claude_terminal() -> None:
    """Open an interactive claude session in the vault — cross-platform.
    Original code was Windows-only (CREATE_NEW_CONSOLE doesn't exist on macOS)."""
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
    """Recent vault .md changes, sorted by mtime desc. Verb inferred from mtime-vs-ctime delta."""
    if not VAULT_PATH.exists():
        return []
    skip_parts = {".obsidian", ".trash", "node_modules", ".git"}
    files = []
    for p in VAULT_PATH.rglob("*.md"):
        if any(part in skip_parts for part in p.parts):
            continue
        try:
            st_ = p.stat()
        except OSError:
            continue
        files.append((p, st_))
    files.sort(key=lambda t: t[1].st_mtime, reverse=True)
    files = files[:limit]

    now = time.time()
    out = []
    for p, st_ in files:
        age = now - st_.st_mtime
        # verb inference: created if mtime ~= ctime (within 2 min),
        # linked if file contains wiki-links and was touched recently,
        # appended if touched in last 10 min, else updated.
        created_delta = abs(st_.st_mtime - st_.st_ctime)
        has_wikilink = False
        if age < 900:
            try:
                has_wikilink = "[[" in p.read_text(encoding="utf-8", errors="replace")[:4000]
            except OSError:
                pass
        if created_delta < 120:
            verb = "created"
        elif has_wikilink and age < 300:
            verb = "linked"
        elif age < 600:
            verb = "appended"
        else:
            verb = "updated"
        try:
            rel = p.relative_to(VAULT_PATH).as_posix()
        except ValueError:
            rel = p.name
        directory = str(Path(rel).parent).replace("\\", "/")
        if directory == ".":
            directory = "vault"
        out.append({
            "verb": verb,
            "name": p.stem,
            "dir": directory,
            "age_sec": int(age),
            "path": p,
        })
    return out


def fmt_ago(sec: int) -> str:
    if sec < 60:
        return f"{sec}s"
    if sec < 3600:
        return f"{sec // 60}m"
    if sec < 86400:
        return f"{sec // 3600}h"
    return f"{sec // 86400}d"


# ─── Metrics / chart data / MCP cache ───

CACHE_DIR = Path(__file__).parent / ".cache"
MCP_CACHE = CACHE_DIR / "mcp.json"
RATE_CACHE = CACHE_DIR / "rate_limits.json"

_FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---", re.DOTALL)


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


def runs_per_day(days: int = 14) -> pd.DataFrame:
    today = date.today()
    counts = {(today - timedelta(days=i)).isoformat(): 0 for i in range(days - 1, -1, -1)}
    for r in scan_runs(days):
        if r.get("date") in counts:
            counts[r["date"]] += 1
    df = pd.DataFrame([{"date": k, "runs": v} for k, v in counts.items()])
    df["date"] = pd.to_datetime(df["date"])
    return df


def tokens_per_day(days: int = 14) -> pd.DataFrame:
    today = date.today()
    buckets = {(today - timedelta(days=i)).isoformat(): 0 for i in range(days - 1, -1, -1)}
    for m in _read_session_metas():
        t = _parse_session_time(m)
        if t is None:
            continue
        k = t.date().isoformat()
        if k in buckets:
            buckets[k] += int(m.get("input_tokens") or 0) + int(m.get("output_tokens") or 0)
    df = pd.DataFrame([{"date": k, "tokens": v} for k, v in buckets.items()])
    df["date"] = pd.to_datetime(df["date"])
    return df


def compute_delta(current: float, prior: float, threshold_pct: float = 5.0) -> tuple[str, float, str]:
    if prior <= 0 and current <= 0:
        return ("·", 0.0, "neutral")
    if prior <= 0:
        return ("▲", 100.0, "up")
    pct = (current - prior) / prior * 100.0
    if abs(pct) < threshold_pct:
        return ("·", pct, "neutral")
    return (("▲", pct, "up") if pct > 0 else ("▼", pct, "down"))


def activity_cumulative(days: int = 30, backfill_demo: bool = True) -> pd.DataFrame:
    """Daily count of (scan_runs + routines ledger) → cumulative sum.

    backfill_demo seeds synthetic activity on empty early days so the cumulative
    curve ramps smoothly instead of flatlining at 0 until recent spike.
    """
    import random
    today = date.today()
    per_day = {(today - timedelta(days=i)).isoformat(): 0 for i in range(days - 1, -1, -1)}
    for r in scan_runs(days):
        d = r.get("date")
        if d in per_day:
            per_day[d] += 1
    ledger = _load_routines_ledger()
    for d in per_day:
        per_day[d] += int(ledger.get(d, 0))

    # Real Claude Code sessions (via session-meta or ccusage fallback)
    for m in _read_session_metas():
        t = _parse_session_time(m)
        if t is not None:
            k = t.date().isoformat()
            if k in per_day:
                per_day[k] += 1

    # Only seed synthetic demo data when there is NO real activity at all —
    # a founder dashboard must not show fake history on top of real usage.
    if backfill_demo and sum(per_day.values()) == 0:
        keys = list(per_day.keys())
        n = len(keys)
        rng = random.Random(0xA6E8)
        for i, k in enumerate(keys):
            if per_day[k] == 0 and i < n - 3:
                t = i / max(1, n - 1)
                base = 1.8 + t * 6.0
                jitter = rng.uniform(-1.2, 1.6)
                per_day[k] = max(1, int(round(base + jitter)))

    df = pd.DataFrame(
        [{"date": k, "day_count": v} for k, v in per_day.items()]
    )
    df["date"] = pd.to_datetime(df["date"])
    df["cumulative"] = df["day_count"].cumsum()
    return df


def delta_window(metas: list[dict], cur_start: datetime, cur_end: datetime,
                 pri_start: datetime, pri_end: datetime) -> tuple[int, int]:
    cur = pri = 0
    for m in metas:
        t = _parse_session_time(m)
        if t is None:
            continue
        tot = int(m.get("input_tokens") or 0) + int(m.get("output_tokens") or 0)
        if cur_start <= t < cur_end:
            cur += tot
        elif pri_start <= t < pri_end:
            pri += tot
    return cur, pri


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
    """Persist latest rate_limit_info keyed by rateLimitType."""
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


def _notify_macos(title: str, message: str) -> None:
    """Fire a macOS notification. Best-effort — never raises."""
    try:
        subprocess.run(
            ["osascript", "-e", f'display notification "{message}" with title "{title}"'],
            capture_output=True, timeout=5,
        )
    except Exception:
        pass


QUOTA_ALERT_STATE = CACHE_DIR / "quota-alert.json"


def _quota_guard_check(pct: float) -> None:
    """Fire one macOS notification per 5h block once usage crosses 80%.

    De-dupe key = the current block's start hour (floor to 5h boundary from
    midnight), so a rerun-heavy Streamlit session doesn't spam notifications.
    """
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


def _check_stuck_run() -> None:
    """เตือน macOS ถ้า run ที่กำลังรันเงียบ >3 นาที (reuse pattern quota guard dedupe)."""
    if not RT.get("proc") or RT.get("done"):
        return
    last = RT.get("last_event_time") or RT.get("start_time")
    if last is None:
        return
    gap = time.time() - last
    if gap < 180:
        RT["stall_notified"] = False
        return
    if RT.get("stall_notified"):
        return
    _notify_macos("Agentic OS", f"⚠️ run ค้าง — เงียบมา {int(gap // 60)} นาที")
    RT["stall_notified"] = True


def _ccusage_metas() -> list[dict]:
    """Fallback usage source: derive session-meta-shaped dicts from ccusage.

    Newer Claude Code versions don't write ~/.claude/usage-data/session-meta/.
    ccusage streams the real transcripts (~/.claude/projects/**.jsonl) and
    returns 5-hour billing blocks; each block maps to one pseudo-session.
    Cached 5 minutes — ccusage takes a few seconds on large histories.
    """
    cache = CACHE_DIR / "ccusage-metas.json"
    try:
        if cache.exists() and time.time() - cache.stat().st_mtime < 300:
            return json.loads(cache.read_text(encoding="utf-8"))
    except Exception:
        pass

    ccusage_bin = shutil.which("ccusage") or str(
        Path.home() / ".npm-global" / "bin" / "ccusage"
    )
    metas: list[dict] = []
    try:
        res = subprocess.run(
            [ccusage_bin, "blocks", "--json"],
            capture_output=True, text=True, timeout=120,
        )
        for b in json.loads(res.stdout).get("blocks", []):
            if b.get("isGap"):
                continue
            tc = b.get("tokenCounts", {})
            try:
                # startTime is UTC ISO; store as naive LOCAL time so the
                # existing _parse_session_time comparison stays correct.
                dt = datetime.fromisoformat(
                    b["startTime"].replace("Z", "+00:00")
                ).astimezone()
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
    """Read all Claude Code per-session usage meta files."""
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
        return dt.replace(tzinfo=None)  # naive local
    except Exception:
        return None


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

    # Local dashboard button runs (manual)
    runs_today = [r for r in scan_runs(2) if r.get("date") == date.today().isoformat()]
    cost_today = sum(_to_float(r.get("cost_usd")) for r in runs_today)

    # Routine runs today — cloud routines, tracked via local ledger
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


# ─── Routine run ledger ───
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


def _ccusage_daily() -> list[dict]:
    """Fetch `ccusage daily --json` (real AI spend), cached 10 minutes.

    Shape verified live: {"daily": [{"period": "YYYY-MM-DD", "totalCost": float,
    "totalTokens": int, ...}], "totals": {...}}. Empty list on any failure —
    caller renders a graceful empty state.
    """
    cache = CACHE_DIR / "ccusage-daily.json"
    try:
        if cache.exists() and time.time() - cache.stat().st_mtime < 600:
            return json.loads(cache.read_text(encoding="utf-8"))
    except Exception:
        pass

    ccusage_bin = shutil.which("ccusage") or str(
        Path.home() / ".npm-global" / "bin" / "ccusage"
    )
    daily: list[dict] = []
    try:
        res = subprocess.run(
            [ccusage_bin, "daily", "--json"],
            capture_output=True, text=True, timeout=120,
        )
        daily = json.loads(res.stdout).get("daily", [])
        CACHE_DIR.mkdir(exist_ok=True)
        cache.write_text(json.dumps(daily), encoding="utf-8")
    except Exception:
        return []
    return daily


# ═══════════════════════════════════════════════════════════
# BACKGROUND RUNNER — parses stream-json events from claude CLI
# ═══════════════════════════════════════════════════════════


def _parse_event(evt: dict):
    """Mutate RT based on one stream-json event."""
    t = evt.get("type")
    if t == "assistant":
        msg = evt.get("message", {})
        for block in msg.get("content", []):
            btype = block.get("type")
            if btype == "text":
                RT["text"] += block.get("text", "")
            elif btype == "tool_use":
                name = block.get("name", "tool")
                RT["phases"].append(name)
                RT["current_phase"] = name
    elif t == "user":
        # tool results; don't need full content
        pass
    elif t == "result":
        RT["cost_usd"] = evt.get("total_cost_usd") or evt.get("cost_usd")
        usage = evt.get("usage", {})
        RT["tokens_in"] = usage.get("input_tokens")
        RT["tokens_out"] = usage.get("output_tokens")
        if evt.get("subtype") != "success":
            RT["error"] = evt.get("result") or evt.get("subtype")
    elif t == "system":
        sub = evt.get("subtype")
        if sub == "init":
            RT["current_phase"] = "initializing"
            servers = evt.get("mcp_servers")
            if servers:
                save_mcp_state(servers)
    elif t == "rate_limit_event":
        save_rate_limit(evt)


def _run_skill_bg(prompt: str):
    """Subprocess runner (runs in background thread). Populates RT."""
    try:
        proc = subprocess.Popen(
            [
                str(CLAUDE_CLI),
                "-p",
                prompt,
                "--permission-mode",
                PERMISSION_MODE,
                "--output-format",
                "stream-json",
                "--verbose",
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=str(VAULT_PATH),
            text=True,
            bufsize=1,
            encoding="utf-8",
            errors="replace",
        )
        RT["proc"] = proc

        for line in iter(proc.stdout.readline, ""):
            line = line.strip()
            if not line:
                continue
            RT["buffer"].append(line)
            RT["last_event_time"] = time.time()
            try:
                evt = json.loads(line)
                _parse_event(evt)
            except json.JSONDecodeError:
                # plaintext line (maybe error before JSON starts)
                RT["text"] += line + "\n"

        proc.wait(timeout=RUN_TIMEOUT_SEC)
        if proc.returncode != 0 and not RT.get("error"):
            stderr_text = proc.stderr.read() if proc.stderr else ""
            RT["error"] = f"exit {proc.returncode}: {stderr_text[:500]}"
    except Exception as e:
        RT["error"] = str(e)
    finally:
        RT["done"] = True
        RT["proc"] = None


def start_skill_run(label: str, prompt: str):
    reset_runtime()
    RT["start_time"] = time.time()
    thread = threading.Thread(target=_run_skill_bg, args=(prompt,), daemon=True)
    thread.start()
    st.session_state.running = True
    st.session_state.active_skill = label
    st.session_state.active_prompt = prompt
    st.session_state.last_error = None


def cancel_current_run():
    proc = RT.get("proc")
    if proc:
        try:
            proc.terminate()
            time.sleep(0.2)
            if proc.poll() is None:
                proc.kill()
        except Exception:
            pass
    RT["cancelled"] = True
    RT["error"] = "cancelled by user"
    RT["done"] = True


_hermes_send_cmd_cache: list | None = None  # None = not probed yet, [] = no send command found


def _hermes_send_command() -> list | None:
    """Probe `hermes --help` once for a message/send/notify subcommand.

    Cached in a module-level global for the process lifetime — ponytail:
    one process = one probe, restart the dashboard to re-probe.
    """
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

    # Look for a clear send/message/notify subcommand in the listed commands.
    for cmd in ("send", "message", "notify"):
        if re.search(rf"^\s*{cmd}\b", help_text, re.MULTILINE):
            _hermes_send_cmd_cache = [hermes_bin, cmd]
            return _hermes_send_cmd_cache
    _hermes_send_cmd_cache = []
    return None


def _notify_run_done(label: str, ok: bool, cost: float | None) -> None:
    """Notify on skill-run completion: macOS notification (always) + Telegram
    via hermes (best-effort). Never let notification failures break the run flow.
    """
    cost_txt = fmt_cost(_to_float(cost)) if cost else "$0.00"
    if ok:
        message = f"✅ {label} เสร็จแล้ว · {cost_txt}"
    else:
        message = f"❌ {label} ล้มเหลว"
    _notify_macos("Agentic OS", message)

    try:
        send_cmd = _hermes_send_command()
        if send_cmd:
            subprocess.run(send_cmd + ["-t", "telegram", message, "-q"], capture_output=True, timeout=10)
    except Exception:
        pass


def finalize_run_if_done(label: str, prompt: str):
    """Called when RT['done']==True. Persists output, resets session state."""
    if RT.get("cancelled"):
        st.session_state.last_output = "(cancelled)"
        st.session_state.last_saved_path = None
        st.session_state.last_error = None
    elif RT.get("error"):
        st.session_state.last_error = str(RT["error"])
        st.session_state.last_output = RT.get("text", "").strip()
        st.session_state.last_saved_path = None
        log_run(label, ok=False)
        _notify_run_done(label, ok=False, cost=None)
    else:
        output = RT.get("text", "").strip() or "(no text output)"
        st.session_state.last_output = output
        meta = {
            "cost_usd": RT.get("cost_usd"),
            "tokens_in": RT.get("tokens_in"),
            "tokens_out": RT.get("tokens_out"),
            "phases": ", ".join(RT.get("phases", [])) or None,
        }
        saved = save_run_output(label, prompt, output, meta=meta)
        st.session_state.last_saved_path = str(saved)
        st.session_state.last_cost = RT.get("cost_usd")
        st.session_state.last_tokens = (RT.get("tokens_in"), RT.get("tokens_out"))
        log_run(label, ok=True)
        _notify_run_done(label, ok=True, cost=RT.get("cost_usd"))

    st.session_state.running = False
    st.session_state.active_skill = None


# ═══════════════════════════════════════════════════════════
# FIRST-RUN WIZARD
# ═══════════════════════════════════════════════════════════

if not VAULT_PATH.exists():
    st.markdown('<h1 class="hero-title">Agentic <em>OS</em></h1>', unsafe_allow_html=True)
    st.error(f"Vault not found: `{VAULT_PATH}`")
    st.markdown(
        "**Setup required.** Edit `config.py` and set:\n\n"
        "- `VAULT_PATH` → your Obsidian vault directory\n"
        "- `VAULT_NAME` → vault name as Obsidian shows it\n"
        "- `CLAUDE_CLI` → path to `claude.exe`\n\n"
        "Then reload this page."
    )
    st.stop()

if not CLAUDE_CLI.exists():
    st.error(f"Claude CLI not found at `{CLAUDE_CLI}`. Check config.py.")
    st.stop()


# ═══════════════════════════════════════════════════════════
# SESSION STATE
# ═══════════════════════════════════════════════════════════

defaults = {
    "running": False,
    "last_output": "",
    "last_label": "",
    "last_saved_path": None,
    "last_prompt": None,
    "last_cost": None,
    "last_tokens": None,
    "last_error": None,
    "active_skill": None,
    "active_prompt": None,
    "skill_search": "",
    "output_view_md": True,
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v


# ═══════════════════════════════════════════════════════════
# HEADER
# ═══════════════════════════════════════════════════════════

st.markdown('<div class="cpt-header-marker"></div>', unsafe_allow_html=True)

# Terminal launch via query-param (claude code pill in quicknav)
_action_q = st.query_params.get("action")
if _action_q == "terminal":
    try:
        open_claude_terminal()
        st.toast("Terminal opened at vault.", icon="✅")
    except Exception as e:
        st.toast(f"Failed: {e}", icon="⚠️")
    st.query_params.clear()

if MASCOT_IDLE_URL:
    _mascot_html = (
        f'<span class="mascot" '
        f'style="--idle:url({MASCOT_IDLE_URL}); '
        f'--run:url({MASCOT_RUN_URL});"></span>'
    )
else:
    _mascot_html = ""
st.markdown(
    '<div class="title-row">'
    '<h1 class="hero-title">'
    f'{_mascot_html}'
    '<span class="hero-word">Agentic</span>'
    '<em>OS</em>'
    '</h1>'
    f'<div class="caption-mono title-crumb">vault · {VAULT_PATH.name} · plan · {CLAUDE_PLAN} · permission · {PERMISSION_MODE}</div>'
    '</div>',
    unsafe_allow_html=True,
)


# ═══════════════════════════════════════════════════════════
# QUICK-NAV PILLS  (claude code · vault · daily · runs · drafts · [status])
# ═══════════════════════════════════════════════════════════

today_note = today_daily_note()
today_runs_dir = RUNS_DIR / date.today().isoformat()

vault_uri = f"obsidian://open?vault={quote(VAULT_NAME)}"
daily_note_uri = obsidian_uri(today_note) if today_note.exists() else vault_uri
runs_folder_uri = f"obsidian://open?vault={quote(VAULT_NAME)}&file={quote('dashboard-runs')}"
drafts_folder_uri = f"obsidian://open?vault={quote(VAULT_NAME)}&file={quote('drafts/awaiting')}"

if st.session_state.running:
    _active = st.session_state.active_skill or "skill"
    _status_html = (
        f'<div class="status-chip running qn-status">'
        f'<span class="pulse-dot small"></span>{_active}</div>'
    )
else:
    _status_html = (
        '<div class="status-chip qn-status">'
        '<span class="pulse-dot idle small"></span>idle</div>'
    )

_inbox_count = len(scan_decision_inbox(str(Path(__file__).parent / "HANDOFF.md")))
_inbox_label = f"📥 inbox {_inbox_count}" if _inbox_count else "📥 inbox"

st.markdown(
    f"""
    <div class="quicknav">
        <a class="qn-claude" href="?action=terminal" target="_self">
            <span class="qn-icon">◆</span>claude code<span class="qn-arrow">↗</span>
        </a>
        <a href="{vault_uri}" target="_blank"><span class="qn-icon">✱</span>vault</a>
        <a href="{daily_note_uri}" target="_blank"><span class="qn-icon">§</span>daily note</a>
        <a href="{runs_folder_uri}" target="_blank"><span class="qn-icon">¶</span>runs folder</a>
        <a href="{drafts_folder_uri}" target="_blank"><span class="qn-icon">※</span>drafts</a>
        <a href="/portfolio" target="_self"><span class="qn-icon">⌗</span>portfolio</a>
        <a href="/portfolio" target="_self">{_inbox_label}</a>
        {_status_html}
    </div>
    """,
    unsafe_allow_html=True,
)


# ═══════════════════════════════════════════════════════════
# USAGE GAUGES + APPROVALS
# ═══════════════════════════════════════════════════════════

usage = calc_usage_windows()
rate_limits = load_rate_limits()
metrics = calc_metrics()


def _gauge_class(pct: float) -> str:
    if pct >= 90:
        return "danger"
    if pct >= 70:
        return "warning"
    return ""


def render_gauge(
    label: str,
    reset_label: str,
    used: float,
    limit: float,
    stat_primary: str,
    stat_max: str,
    stat_sub: str,
    delta: tuple[str, float, str] | None = None,
    danger_threshold_pct: float | None = None,
) -> str:
    pct = min(100.0, (used / limit * 100.0) if limit else 0.0)
    # danger_threshold_pct overrides the default 90/70 _gauge_class bands —
    # used by the 5-hour quota guard, which alerts earlier (80%).
    klass = "danger" if danger_threshold_pct is not None and pct >= danger_threshold_pct else _gauge_class(pct)
    delta_html = ""
    if delta is not None:
        arrow, pct_d, dklass = delta
        dtxt = f'{arrow} {abs(pct_d):.0f}%' if dklass != "neutral" else '· flat'
        delta_html = f'<span class="gauge-delta {dklass}">{dtxt}</span>'
    return (
        f'<div class="gauge-card">'
        f'<div class="gauge-header">'
        f'<span class="gauge-label">{label}</span>'
        f'<span class="gauge-reset">{reset_label}</span>'
        f'</div>'
        f'<div class="gauge-track">'
        f'<div class="gauge-fill {klass}" style="width:{pct:.1f}%"></div>'
        f'</div>'
        f'<div class="gauge-stats">'
        f'<span>{stat_primary}</span>'
        f'<span class="gauge-max">/ {stat_max}</span>'
        f'<span class="gauge-sub">{stat_sub}</span>'
        f'{delta_html}'
        f'</div>'
        f'</div>'
    )


five_h_reset = (rate_limits.get("five_hour") or {}).get("resets_at")
week_reset = (rate_limits.get("weekly") or {}).get("resets_at")

five_h_tokens = usage["five_hour"]["total"]
week_tokens = usage["weekly"]["total"]
routines_today = usage["today"]["routines"]
today_runs = usage["today"]["runs"]
today_cost = usage["today"]["cost"]

_metas_cache = _read_session_metas()
_now = datetime.now()
_5h_cur, _5h_pri = delta_window(
    _metas_cache,
    _now - timedelta(hours=5), _now,
    _now - timedelta(hours=10), _now - timedelta(hours=5),
)
_wk_cur, _wk_pri = delta_window(
    _metas_cache,
    _now - timedelta(days=7), _now,
    _now - timedelta(days=14), _now - timedelta(days=7),
)
_rt_ledger = _load_routines_ledger()
_rt_today = int(_rt_ledger.get(date.today().isoformat(), 0))
_rt_yday = int(_rt_ledger.get((date.today() - timedelta(days=1)).isoformat(), 0))
_5h_delta = compute_delta(_5h_cur, _5h_pri)
_wk_delta = compute_delta(_wk_cur, _wk_pri)
_rt_delta = compute_delta(_rt_today, _rt_yday)

_five_h_pct = min(100.0, (five_h_tokens / LIMITS["five_hour_tokens"] * 100.0) if LIMITS["five_hour_tokens"] else 0.0)
_quota_guard_check(_five_h_pct)  # fires ≤1 macOS notification per 5h block at ≥80%

m1, m2, m3 = st.columns(3, gap="small")
with m1:
    st.markdown(
        render_gauge(
            "5-hour window",
            f"resets · {fmt_time_until(five_h_reset)}",
            five_h_tokens,
            LIMITS["five_hour_tokens"],
            fmt_tokens(five_h_tokens),
            fmt_tokens(LIMITS["five_hour_tokens"]),
            f"· {usage['five_hour']['sessions']} sessions",
            delta=_5h_delta,
            danger_threshold_pct=80,
        ),
        unsafe_allow_html=True,
    )
with m2:
    st.markdown(
        render_gauge(
            "weekly window",
            f"resets · {fmt_time_until(week_reset)}",
            week_tokens,
            LIMITS["weekly_tokens"],
            fmt_tokens(week_tokens),
            fmt_tokens(LIMITS["weekly_tokens"]),
            f"· {usage['weekly']['sessions']} sessions",
            delta=_wk_delta,
        ),
        unsafe_allow_html=True,
    )
with m3:
    st.markdown(
        render_gauge(
            f"routines · {CLAUDE_PLAN}",
            "resets · midnight",
            routines_today,
            LIMITS["daily_routine_runs"],
            str(routines_today),
            str(LIMITS["daily_routine_runs"]),
            f"{fmt_cost(today_cost)} today",
            delta=_rt_delta,
        ),
        unsafe_allow_html=True,
    )

st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════
# RUNS-PER-DAY CHART
# ═══════════════════════════════════════════════════════════

import plotly.graph_objects as go

df_cum = activity_cumulative(30)
_cum_total = int(df_cum["cumulative"].iloc[-1]) if not df_cum.empty else 0
_cum_30d = int(df_cum["day_count"].sum())


def _build_activity_svg(df: pd.DataFrame) -> str:
    if df.empty:
        return ""
    cum = df["cumulative"].tolist()
    dates = df["date"].tolist()
    n = len(cum)
    max_c = max(cum) or 1
    VB_W, VB_H = 1000, 180
    ML, MR, MT, MB = 24, 24, 14, 6
    pw = VB_W - ML - MR
    ph = VB_H - MT - MB

    pts = []
    for i, c in enumerate(cum):
        x = ML + (i / max(1, n - 1)) * pw
        y = MT + ph - (c / max_c) * ph
        pts.append((x, y))

    line_d = "M " + " L ".join(f"{x:.2f},{y:.2f}" for x, y in pts)
    area_d = (
        f"M {pts[0][0]:.2f},{MT + ph:.2f} "
        + " ".join(f"L {x:.2f},{y:.2f}" for x, y in pts)
        + f" L {pts[-1][0]:.2f},{MT + ph:.2f} Z"
    )
    # Closed-loop motion path: trace line forward then back along baseline.
    # Pulse "does a loop" instead of teleporting back to start.
    loop_d = (
        "M " + " L ".join(f"{x:.2f},{y:.2f}" for x, y in pts)
        + f" L {pts[-1][0]:.2f},{MT + ph:.2f}"
        + f" L {pts[0][0]:.2f},{MT + ph:.2f} Z"
    )

    tick_idx = [0, n // 4, n // 2, (3 * n) // 4, n - 1]
    tick_labels = [dates[i].strftime("%b %d").lower() for i in tick_idx]

    svg = f'''
<div class="activity-chart-wrap">
  <svg class="activity-svg" viewBox="0 0 {VB_W} {VB_H}"
       preserveAspectRatio="none" xmlns="http://www.w3.org/2000/svg">
    <defs>
      <linearGradient id="activityFill" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0%"   stop-color="#3d7bff" stop-opacity="0.48"/>
        <stop offset="60%"  stop-color="#3d7bff" stop-opacity="0.14"/>
        <stop offset="100%" stop-color="#3d7bff" stop-opacity="0"/>
      </linearGradient>
      <filter id="pulseGlow" x="-200%" y="-200%" width="500%" height="500%">
        <feGaussianBlur stdDeviation="2.4" result="b1"/>
        <feGaussianBlur stdDeviation="5.5" result="b2"/>
        <feMerge>
          <feMergeNode in="b2"/>
          <feMergeNode in="b1"/>
          <feMergeNode in="SourceGraphic"/>
        </feMerge>
      </filter>
      <filter id="lineGlow" x="-50%" y="-50%" width="200%" height="200%">
        <feGaussianBlur stdDeviation="1.2" result="lg"/>
        <feMerge>
          <feMergeNode in="lg"/>
          <feMergeNode in="SourceGraphic"/>
        </feMerge>
      </filter>
    </defs>
    <path d="{area_d}" fill="url(#activityFill)" stroke="none">
      <animate attributeName="opacity" values="0.85;1;0.85"
               dur="6s" repeatCount="indefinite"/>
    </path>
    <path id="activityPath" d="{line_d}" fill="none"
          stroke="#3d7bff" stroke-width="1.6"
          stroke-linejoin="round" stroke-linecap="round"
          vector-effect="non-scaling-stroke"
          filter="url(#lineGlow)"/>
    <path id="activityLoop" d="{loop_d}" fill="none" stroke="none"/>
    <circle r="4.2" fill="#b8ccff" filter="url(#pulseGlow)" opacity="0.95">
      <animateMotion dur="7s" repeatCount="indefinite" rotate="auto">
        <mpath href="#activityLoop"/>
      </animateMotion>
      <animate attributeName="opacity" values="0.35;1;0.35"
               dur="1.4s" repeatCount="indefinite"/>
    </circle>
    <circle r="2" fill="#e8efff">
      <animateMotion dur="7s" repeatCount="indefinite" rotate="auto">
        <mpath href="#activityLoop"/>
      </animateMotion>
    </circle>
  </svg>
  <div class="activity-axis">
    {"".join(f"<span>{lbl}</span>" for lbl in tick_labels)}
  </div>
</div>
'''
    return svg


st.markdown(
    '<div class="chart-card parchment">'
    '<div class="chart-title">agentic OS · cumulative activity · 30d '
    f'<span>· {_cum_total:,} total · {_cum_30d} last 30d</span></div>'
    + _build_activity_svg(df_cum)
    + '</div>',
    unsafe_allow_html=True,
)


# ═══════════════════════════════════════════════════════════
# MCP HEALTH STRIP
# ═══════════════════════════════════════════════════════════

mcp_servers = load_mcp_state()
if mcp_servers:
    items_html = '<span class="mcp-label">integrations</span>'
    for s in mcp_servers:
        name = s.get("name", "?").replace("claude.ai ", "").replace("plugin:", "")
        status = (s.get("status") or "unknown").lower().replace("-", "_")
        items_html += (
            f'<span class="mcp-item">'
            f'<span class="mcp-dot {status}"></span>'
            f'{html_escape(name)}'
            f'</span>'
        )
    st.markdown(f'<div class="mcp-strip">{items_html}</div>', unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════
# LAYOUT
# ═══════════════════════════════════════════════════════════

st.markdown('<hr class="chapter" />', unsafe_allow_html=True)

_check_stuck_run()  # watchdog: notify if active run stalls

col_main, col_side = st.columns([2.6, 1], gap="large")


# ——— SIDEBAR COLUMN: recent runs ———
with col_side:
    runs = list_recent_runs(8)
    card_html = '<div class="runs-card"><div class="cat-label">recent runs</div>'
    if not runs:
        card_html += '<div style="color: var(--text-mute); font-size: 0.8rem; padding: 0.4rem 0 0.5rem 0;">no runs yet</div>'
    else:
        card_html += '<div class="run-list">'
        for r in runs:
            mtime = datetime.fromtimestamp(r.stat().st_mtime)
            label = r.stem.split("-", 2)[-1].replace("-", " ")
            uri = obsidian_uri(r)
            card_html += (
                f'<div class="run-row">'
                f'<span class="run-time">{mtime.strftime("%H:%M")}</span>'
                f'<span class="run-label">{html_escape(label)}</span>'
                f'<a href="{uri}" target="_blank">open ↗</a>'
                f'</div>'
            )
        card_html += '</div>'
    card_html += '</div>'
    st.markdown(card_html, unsafe_allow_html=True)

    # ——— Decision Inbox: pending decisions from HANDOFF.md files ———
    _inbox = scan_decision_inbox(str(Path(__file__).parent / "HANDOFF.md"))
    inbox_html = '<div class="runs-card"><div class="cat-label">📥 decision inbox</div>'
    if not _inbox:
        inbox_html += '<div style="color: var(--text-mute); font-size: 0.8rem; padding: 0.4rem 0 0.5rem 0;">ไม่มี decision ค้าง</div>'
    else:
        inbox_html += '<div class="run-list">'
        for i, it in enumerate(_inbox[:8], 1):
            text = it["text"]
            short = text[:120] + ("…" if len(text) > 120 else "")
            inbox_html += (
                f'<div class="run-row">'
                f'<span class="run-time">{i}.</span>'
                f'<span class="run-label">'
                f'<span style="color:var(--accent);font-size:.68rem;text-transform:uppercase">{html_escape(it["source"])}</span> '
                f'{html_escape(short)}</span>'
                f'</div>'
            )
        inbox_html += '</div>'
    inbox_html += '</div>'
    st.markdown(inbox_html, unsafe_allow_html=True)

    # ——— AgentPeek: live sessions ———
    _sessions = monitors.scan_live_sessions()
    if _sessions:
        sh = '<div class="peek-card"><div class="cat-label">◆ live sessions</div>'
        for se in _sessions:
            tag = " · runner" if se["cwd"] == str(VAULT_PATH) else ""
            sh += (
                f'<div class="peek-row"><span class="peek-dot {se["state"]}"></span>'
                f'{html_escape(se["project"])}{tag}'
                f'<span class="peek-meta">{se["state"]} · {monitors.humanize_ago(se["last"])}</span></div>'
            )
        sh += '</div>'
        st.markdown(sh, unsafe_allow_html=True)

    # ——— AgentPeek: dev servers ———
    _servers = monitors.scan_dev_servers()
    if _servers:
        st.markdown('<div class="peek-card"><div class="cat-label">▸ dev servers</div></div>', unsafe_allow_html=True)
        for sv in _servers:
            folder = Path(sv["cwd"]).name if sv["cwd"] else "?"
            r1, r2, r3 = st.columns([3, 1, 1])
            with r1:
                st.markdown(
                    f'<div class="peek-row"><span class="peek-port">:{sv["port"]}</span> '
                    f'{html_escape(sv["framework"])}<span class="peek-meta">{html_escape(folder)}</span></div>',
                    unsafe_allow_html=True,
                )
            with r2:
                if st.button("open", key=f"srv_open_{sv['pid']}", use_container_width=True):
                    webbrowser.open(f"http://localhost:{sv['port']}")
            with r3:
                _ck = f"confirm_kill_{sv['pid']}"
                if st.session_state.get(_ck):
                    if st.button("✓ kill", key=f"srv_kill2_{sv['pid']}", use_container_width=True):
                        monitors.kill_server(sv["pid"])
                        st.session_state[_ck] = False
                        st.rerun()
                else:
                    if st.button("kill", key=f"srv_kill_{sv['pid']}", use_container_width=True):
                        st.session_state[_ck] = True
                        st.rerun()

    # ——— AgentPeek: quick routes ———
    st.markdown('<div class="peek-card"><div class="cat-label">⌗ quick routes</div></div>', unsafe_allow_html=True)
    st.markdown('<div class="qroute-row">', unsafe_allow_html=True)
    _qcols = st.columns(len(QUICK_ROUTES))
    for _qc, (_qname, _qpath) in zip(_qcols, QUICK_ROUTES):
        with _qc:
            if st.button(_qname, key=f"qr_{_qname}", use_container_width=True):
                monitors._run(["open", str(_qpath)])
    st.markdown('</div>', unsafe_allow_html=True)

    # Mini 7-day runs bar chart (bottom-right "dead space" filler)
    df_7 = activity_cumulative(7)
    _bar_labels = df_7["date"].dt.strftime("%a").tolist()
    _bar_vals = df_7["day_count"].tolist()
    _bar_total = int(sum(_bar_vals))

    st.markdown(
        '<div class="chart-card mini-chart">'
        '<div class="chart-title">last <em>seven</em> days '
        f'<span>· {_bar_total} runs</span></div>',
        unsafe_allow_html=True,
    )
    _barfig = go.Figure()
    _barfig.add_trace(
        go.Bar(
            x=_bar_labels,
            y=_bar_vals,
            marker=dict(color="#3d7bff", line=dict(width=0)),
            hovertemplate="<b>%{x}</b><br>%{y} runs<extra></extra>",
        )
    )
    _barfig.update_layout(
        height=120,
        margin=dict(l=20, r=20, t=10, b=28),
        paper_bgcolor="#0f1726",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="JetBrains Mono, monospace", size=9, color="#94a3b8"),
        showlegend=False,
        bargap=0.32,
        hoverlabel=dict(
            bgcolor="#070b14",
            bordercolor="#3d7bff",
            font=dict(family="JetBrains Mono, monospace", color="#e6edf7", size=10),
        ),
        xaxis=dict(
            showgrid=False, zeroline=False, showline=False,
            tickfont=dict(color="#94a3b8", size=9),
        ),
        yaxis=dict(
            showgrid=False, zeroline=False, showline=False, showticklabels=False,
        ),
    )
    st.plotly_chart(_barfig, use_container_width=True, config={"displayModeBar": False})
    st.markdown("</div>", unsafe_allow_html=True)

    # ——— Forecast card (5-hour burn projection) ———
    _cap = LIMITS["five_hour_tokens"]
    _used = five_h_tokens
    _remaining = max(0, _cap - _used)
    _reset_in_sec = max(0, int(five_h_reset - time.time())) if five_h_reset else 0
    _reset_in_min = _reset_in_sec // 60
    _window_min = 300  # 5h
    _elapsed_min = max(1, _window_min - _reset_in_min) if _reset_in_min else 1
    _burn_per_min = (_used / _elapsed_min) if _elapsed_min > 0 else 0
    _exhaust_in_min = int(_remaining / _burn_per_min) if _burn_per_min > 0 else None
    _will_exhaust = _exhaust_in_min is not None and _exhaust_in_min < _reset_in_min

    _elapsed_pct = min(100, _elapsed_min / _window_min * 100)
    if _will_exhaust and _exhaust_in_min is not None:
        _proj_end_min = _elapsed_min + _exhaust_in_min
    else:
        _proj_end_min = _window_min
    _proj_pct = max(_elapsed_pct, min(100, _proj_end_min / _window_min * 100))
    _proj_left = _elapsed_pct
    _proj_width = max(0, _proj_pct - _elapsed_pct)
    _now_pct = _elapsed_pct

    if _will_exhaust and _exhaust_in_min is not None:
        _hit = (datetime.now() + timedelta(minutes=_exhaust_in_min)).strftime("%H:%M")
        _headline = f'cap at <em>{_hit}</em>'
    else:
        _headline = 'under cap <em>this window</em>'
    _sub = (
        f'burn · {fmt_tokens(int(_burn_per_min))}/min'
        if _burn_per_min > 0 else 'burn · idle'
    )

    # Next scheduled routines — hardcoded schedule until real cron wired in
    _scheduled = [
        ("17:00", "evening digest"),
        ("22:00", "vault compact"),
        ("09:00", "morning brief"),
    ]
    _now_dt = datetime.now()
    _sched_rows = []
    for hhmm, label in _scheduled:
        _h, _m = [int(x) for x in hhmm.split(":")]
        _next = _now_dt.replace(hour=_h, minute=_m, second=0, microsecond=0)
        if _next <= _now_dt:
            _next = _next + timedelta(days=1)
        _sched_rows.append((_next, hhmm, label))
    _sched_rows.sort(key=lambda r: r[0])
    _sched_html = '<div class="cpt-sched">'
    for dt, hhmm, label in _sched_rows[:2]:
        _sched_html += (
            '<div class="cpt-sched-row">'
            f'<span class="cpt-sched-time">{hhmm}</span>'
            f'<span class="cpt-sched-label">{label}</span>'
            f'<span class="cpt-sched-in">in {fmt_time_until(int(dt.timestamp()))}</span>'
            '</div>'
        )
    _sched_html += '</div>'

    st.markdown(
        '<div class="cpt-forecast">'
        f'<div class="cpt-forecast-head">forecast · 5h'
        f'<span class="cpt-forecast-sub">{_sub}</span></div>'
        f'<div class="cpt-forecast-head" '
        'style="font-size:0.7rem;color:var(--fg-dim);margin-bottom:0;">'
        f'{_headline}</div>'
        '<div class="cpt-forecast-track">'
        f'<div class="cpt-forecast-elapsed" style="width:{_elapsed_pct:.1f}%"></div>'
        f'<div class="cpt-forecast-proj" '
        f'style="left:{_proj_left:.1f}%;width:{_proj_width:.1f}%"></div>'
        f'<div class="cpt-forecast-now" style="left:{_now_pct:.1f}%"></div>'
        '</div>'
        '<div class="cpt-forecast-legend">'
        '<span><em>█</em> elapsed</span>'
        '<span><em>▨</em> projected</span>'
        '<span><em>│</em> now</span>'
        f'<span>resets · {fmt_time_until(five_h_reset)}</span>'
        '</div>'
        f'{_sched_html}'
        '</div>',
        unsafe_allow_html=True,
    )

    # ——— Cost card (real AI spend via ccusage) ———
    _daily_usage = _ccusage_daily()
    if _daily_usage:
        _by_date = {d.get("period"): _to_float(d.get("totalCost")) for d in _daily_usage}
        _today_key = date.today().isoformat()
        _yday_key = (date.today() - timedelta(days=1)).isoformat()
        _cost_today = _by_date.get(_today_key, 0.0)
        _cost_yday = _by_date.get(_yday_key, 0.0)

        _last7 = [date.today() - timedelta(days=i) for i in range(6, -1, -1)]
        _cost_labels = [d.strftime("%a") for d in _last7]
        _cost_vals = [_by_date.get(d.isoformat(), 0.0) for d in _last7]
        _cost_7d_total = sum(_cost_vals)

        st.markdown(
            '<div class="cpt-forecast">'
            '<div class="cpt-forecast-head">value · <em>api-equivalent</em></div>'
            '<div class="gauge-stats" style="margin:0.3rem 0 0.1rem;">'
            f'<span>{fmt_cost(_cost_today)}</span>'
            '<span class="gauge-sub">today</span>'
            '</div>'
            '<div class="cpt-forecast-legend">'
            f'<span>yesterday · {fmt_cost(_cost_yday)}</span>'
            f'<span>7d · {fmt_cost(_cost_7d_total)}</span>'
            '</div>'
            # Max plan = flat monthly fee; this shows what the same usage
            # WOULD cost on API pricing (value extracted), not actual spend.
            '<div class="gauge-sub" style="margin-top:0.25rem;">'
            'มูลค่างานเทียบราคา API — จ่ายจริงคือค่า Max รายเดือน</div>'
            '</div>',
            unsafe_allow_html=True,
        )
        _costfig = go.Figure()
        _costfig.add_trace(
            go.Bar(
                x=_cost_labels,
                y=_cost_vals,
                marker=dict(color="#3d7bff", line=dict(width=0)),
                hovertemplate="<b>%{x}</b><br>$%{y:.2f}<extra></extra>",
            )
        )
        _costfig.update_layout(
            height=90,
            margin=dict(l=20, r=20, t=6, b=22),
            paper_bgcolor="#0f1726",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(family="JetBrains Mono, monospace", size=9, color="#94a3b8"),
            showlegend=False,
            bargap=0.32,
            hoverlabel=dict(
                bgcolor="#070b14",
                bordercolor="#3d7bff",
                font=dict(family="JetBrains Mono, monospace", color="#e6edf7", size=10),
            ),
            xaxis=dict(
                showgrid=False, zeroline=False, showline=False,
                tickfont=dict(color="#94a3b8", size=9),
            ),
            yaxis=dict(
                showgrid=False, zeroline=False, showline=False, showticklabels=False,
            ),
        )
        st.plotly_chart(_costfig, use_container_width=True, config={"displayModeBar": False})
    else:
        st.markdown(
            '<div class="cpt-forecast">'
            '<div class="cpt-forecast-head">value · <em>api-equivalent</em></div>'
            '<div class="gauge-sub" style="margin-top:0.3rem;">ccusage unavailable</div>'
            '</div>',
            unsafe_allow_html=True,
        )

    # ——— Vault pulse ———
    pulse_items = list_vault_pulse(6)
    if pulse_items:
        pulse_html = '<div class="cpt-pulse-card"><div class="cpt-cat">vault pulse</div>'
        for it in pulse_items:
            try:
                uri = obsidian_uri(it["path"])
            except Exception:
                uri = "#"
            pulse_html += (
                '<div class="cpt-pulse">'
                f'<span class="cpt-verb {it["verb"]}">{it["verb"]}</span>'
                '<div class="cpt-pulse-main">'
                f'<div class="cpt-pulse-name">'
                f'<a href="{uri}" target="_blank" '
                'style="color:inherit;text-decoration:none;">'
                f'{html_escape(it["name"])}</a></div>'
                f'<div class="cpt-pulse-dir">{html_escape(it["dir"])}</div>'
                '</div>'
                f'<span class="cpt-pulse-ago">{fmt_ago(it["age_sec"])}</span>'
                '</div>'
            )
        pulse_html += '</div>'
        st.markdown(pulse_html, unsafe_allow_html=True)



# ——— MAIN COLUMN ———
with col_main:
    hero_slot = st.empty()

    def render_hero_error():
        err = st.session_state.last_error or "unknown error"
        label = (st.session_state.last_label or "skill").lower()
        hero_slot.markdown(
            f'<div class="hero-card error">'
            f'<div class="hero-label">failed · {html_escape(label)}</div>'
            f'<h2 class="hero-headline">run failed <em>·</em></h2>'
            f'<pre class="error-detail">{html_escape(err)}</pre>'
            f'<div class="error-hint">check logs or click ↻ rerun below</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    def render_hero_idle():
        if st.session_state.last_output:
            last = st.session_state.last_label
            saved_link = ""
            if st.session_state.last_saved_path:
                saved = Path(st.session_state.last_saved_path)
                uri = obsidian_uri(saved)
                rel = saved.relative_to(VAULT_PATH).as_posix()
                saved_link = (
                    f'<a class="obsidian-link" href="{uri}" target="_blank">◆ open in obsidian · {rel}</a>'
                )

            meta_html = ""
            if st.session_state.last_cost is not None:
                cost = st.session_state.last_cost
                tok_in, tok_out = st.session_state.last_tokens or (None, None)
                parts = [f'<span class="meta-val">${cost:.4f}</span>']
                if tok_in is not None:
                    parts.append(f'<span class="meta-val">{tok_in} in</span>')
                if tok_out is not None:
                    parts.append(f'<span class="meta-val">{tok_out} out</span>')
                meta_html = f'<div class="meta-row">{" · ".join(parts)}</div>'

            hero_slot.markdown(
                f'<div class="hero-card">'
                f'<div class="hero-label">last run · {last.lower()}</div>'
                f'<h2 class="hero-headline">complete <em>·</em></h2>'
                f'{saved_link}'
                f'{meta_html}'
                f'</div>',
                unsafe_allow_html=True,
            )
        else:
            hero_slot.markdown(
                '<div class="hero-card">'
                '<div class="hero-label">ready</div>'
                '<h2 class="hero-headline">run a <em>skill</em> to begin'
                '<span class="cursor-blink">█</span></h2>'
                '<div style="color: var(--text-mute); font-size: 0.85rem; margin-top: 0.6rem;">'
                'click a skill · press run · or type any prompt'
                '</div></div>',
                unsafe_allow_html=True,
            )

    def _clear_output():
        st.session_state.last_output = ""
        st.session_state.last_error = None
        st.session_state.last_saved_path = None
        st.session_state.last_cost = None
        st.session_state.last_tokens = None
        st.session_state.last_label = ""
        st.session_state.last_prompt = None

    # Rendered output (markdown) for last run
    def render_last_output():
        has_content = st.session_state.last_output or st.session_state.last_error
        if has_content and not st.session_state.running:
            with st.container():
                col_view, col_rerun, col_toggle, col_clear = st.columns([3, 1, 0.7, 0.7])
                with col_view:
                    st.markdown(
                        '<div class="caption-mono" style="margin-top:0.8rem;">output</div>',
                        unsafe_allow_html=True,
                    )
                with col_rerun:
                    if st.session_state.last_prompt and st.button(
                        "↻ rerun", key="btn_rerun", use_container_width=True
                    ):
                        start_skill_run(st.session_state.last_label, st.session_state.last_prompt)
                        st.rerun()
                with col_toggle:
                    view_toggle = st.toggle(
                        "md",
                        value=st.session_state.output_view_md,
                        key="view_toggle",
                        help="toggle markdown / raw",
                    )
                    st.session_state.output_view_md = view_toggle
                with col_clear:
                    st.button(
                        "✕",
                        key="btn_clear_output",
                        use_container_width=True,
                        help="clear output",
                        on_click=_clear_output,
                    )

                st.markdown('<div class="output-body">', unsafe_allow_html=True)
                if st.session_state.output_view_md:
                    st.markdown(st.session_state.last_output)
                else:
                    st.code(st.session_state.last_output, language="markdown")
                st.markdown('</div>', unsafe_allow_html=True)

    # ——— RUNNING STATE: live fragment ———
    if st.session_state.running:
        @st.fragment(run_every=0.4)
        def live_hero_fragment():
            elapsed = int(time.time() - (RT.get("start_time") or time.time()))
            phase = RT.get("current_phase") or "starting"
            text_preview = RT.get("text", "")[-2500:]
            phase_log = RT.get("phases", [])
            phase_log_html = ""
            if phase_log:
                last_phases = phase_log[-6:]
                phase_log_html = (
                    f'<div class="phase-line">phases · '
                    + " → ".join(
                        f'<span class="phase-name">{html_escape(pretty_phase(p))}</span>'
                        for p in last_phases
                    )
                    + "</div>"
                )

            preview_html = (
                f'<pre class="stream-output">{html_escape(text_preview)}</pre>'
                if text_preview else ""
            )

            label = st.session_state.active_skill or "skill"
            hero_slot.markdown(
                f'<div class="hero-card running">'
                f'<div class="hero-label"><span class="pulse-dot small"></span>'
                f'running · {elapsed}s · {html_escape(pretty_phase(phase))}</div>'
                f'<h2 class="hero-headline">{html_escape(label.lower())} <em>·</em></h2>'
                f'{phase_log_html}'
                f'{preview_html}'
                f'</div>',
                unsafe_allow_html=True,
            )

            if RT.get("done"):
                finalize_run_if_done(
                    st.session_state.active_skill or "skill",
                    st.session_state.active_prompt or "",
                )
                st.rerun(scope="app")

        live_hero_fragment()

        # Cancel button
        st.markdown('<div class="cancel-btn">', unsafe_allow_html=True)
        if st.button("✕ cancel run", key="btn_cancel", use_container_width=False):
            cancel_current_run()
            finalize_run_if_done(
                st.session_state.active_skill or "skill",
                st.session_state.active_prompt or "",
            )
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    else:
        if st.session_state.last_error:
            render_hero_error()
        else:
            render_hero_idle()
        render_last_output()

    # ——— UNIFIED PROMPT + SKILL CHIPS (hidden during run — takeover UX) ———
    if "prompt_input_widget" not in st.session_state:
        st.session_state.prompt_input_widget = ""
    if "last_chip_label" not in st.session_state:
        st.session_state.last_chip_label = None

    def _load_chip(template: str, label: str):
        st.session_state.prompt_input_widget = template
        st.session_state.last_chip_label = label

    def _clear_prompt():
        st.session_state.prompt_input_widget = ""
        st.session_state.last_chip_label = None

    clicked = None

    # Query-param chip loader: <a href="?skill=Label"> → load template
    _skill_q = st.query_params.get("skill")
    if _skill_q and not st.session_state.running:
        for _s in SKILLS:
            if _s["label"] == _skill_q:
                st.session_state.prompt_input_widget = _s["prompt_template"]
                st.session_state.last_chip_label = _s["label"]
                break
        st.query_params.clear()

    if not st.session_state.running:
        st.markdown("<div style='height:0.6rem'></div>", unsafe_allow_html=True)
        st.markdown('<div class="cpt-cat">prompt</div>', unsafe_allow_html=True)
        with st.form(key="form_unified", clear_on_submit=False, border=False):
            prompt_val = st.text_area(
                "prompt",
                placeholder="type any prompt, or pick a skill below to load a template…",
                label_visibility="collapsed",
                key="prompt_input_widget",
                height=120,
            )
            b1, b2 = st.columns([3, 1])
            with b1:
                submit = st.form_submit_button(
                    "run →",
                    use_container_width=True,
                    type="primary",
                )
            with b2:
                cleared = st.form_submit_button(
                    "clear",
                    use_container_width=True,
                    on_click=_clear_prompt,
                )
            if submit:
                text = (prompt_val or "").strip()
                if not text:
                    st.warning("prompt empty")
                elif "{input}" in text:
                    st.warning("replace {input} placeholder before running")
                else:
                    label = st.session_state.last_chip_label or "Ad-hoc"
                    clicked = {"label": label, "prompt": text}

        # Skill chips — cpt-skill anchor grid grouped by category
        st.markdown("<div style='height:0.4rem'></div>", unsafe_allow_html=True)
        skills_sorted = sorted(SKILLS, key=lambda s: s.get("category", "other"))
        _active = st.session_state.last_chip_label
        for category, group in groupby(skills_sorted, key=lambda s: s.get("category", "other")):
            group_list = list(group)
            grid_html = (
                f'<div class="cpt-cat chip-cat">{html_escape(category)}</div>'
                '<div class="cpt-skill-grid">'
            )
            for skill in group_list:
                loaded = " loaded" if skill["label"] == _active else ""
                grid_html += (
                    f'<a class="cpt-skill{loaded}" '
                    f'href="?skill={quote(skill["label"])}" target="_self" '
                    f'title="{html_escape(skill["description"])}">'
                    f'<span class="cpt-skill-name">{html_escape(skill["label"])}</span>'
                    f'<span class="cpt-skill-desc">{html_escape(skill["description"])}</span>'
                    '</a>'
                )
            grid_html += '</div>'
            st.markdown(grid_html, unsafe_allow_html=True)

        # Trigger run
        if clicked:
            st.session_state.last_label = clicked["label"]
            st.session_state.last_prompt = clicked["prompt"]
            start_skill_run(clicked["label"], clicked["prompt"])
            st.rerun()
