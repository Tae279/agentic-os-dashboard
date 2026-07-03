"""AgentPeek-style monitors — pure functions (no Streamlit render here).

Data sources verified on this machine (Plan agent 2026-07-03):
- lsof -iTCP -sTCP:LISTEN -P -n  → listening ports (next:3000 + self:8501 seen)
- lsof -a -p PID -d cwd -Fn      → process cwd
- ~/.claude/projects/*/*.jsonl   → session transcripts (1.8GB — mtime-filter FIRST)
- fields in JSONL: type, cwd, timestamp, sessionId, message.content

ponytail: stdlib + native lsof/ps only, no new deps. Whole-file reads banned
(1.8GB dir) — dir-mtime prefilter then tail-read 8KB.
"""

import getpass
import json
import os
import re
import subprocess
import time
from pathlib import Path

CLAUDE_BIN = str(Path.home() / ".npm-global" / "bin" / "claude")
PROJECTS = Path.home() / ".claude" / "projects"
SELF_PORT = 8501
USER = getpass.getuser()


def _run(cmd: list[str], timeout: int = 5) -> str:
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout).stdout
    except Exception:
        return ""


def _lsof_cwd(pid: str) -> str:
    for line in _run(["lsof", "-a", "-p", pid, "-d", "cwd", "-Fn"]).splitlines():
        if line.startswith("n"):
            return line[1:]
    return ""


# ── Feature 2: dev servers ──
def scan_dev_servers() -> list[dict]:
    seen: dict[str, dict] = {}
    for line in _run(["lsof", "-iTCP", "-sTCP:LISTEN", "-P", "-n"]).splitlines()[1:]:
        parts = line.split()
        if len(parts) < 9:
            continue
        cmd, pid, user = parts[0], parts[1], parts[2]
        m = re.search(r":(\d+)$", parts[-1])
        if not m:
            continue
        port = int(m.group(1))
        if not (3000 <= port <= 9999) or port == SELF_PORT or user != USER:
            continue
        if pid in seen:
            continue
        cwd = _lsof_cwd(pid)
        seen[pid] = {
            "pid": pid, "port": port, "cmd": cmd, "cwd": cwd,
            "framework": _guess_framework(cmd, cwd),
        }
    return sorted(seen.values(), key=lambda s: s["port"])


def _guess_framework(cmd: str, cwd: str) -> str:
    if cwd:
        pkg = Path(cwd) / "package.json"
        if pkg.exists():
            try:
                deps = json.loads(pkg.read_text())
                all_deps = {**deps.get("dependencies", {}), **deps.get("devDependencies", {})}
                for fw in ("next", "vite", "astro", "react-scripts", "@remix-run/dev", "wrangler"):
                    if fw in all_deps:
                        return fw.replace("@remix-run/dev", "remix")
            except Exception:
                pass
        if list(Path(cwd).glob("*.py")):
            return "python"
    return cmd.lower()


def kill_server(pid: str) -> bool:
    """SIGTERM หลัง re-verify ว่า process เป็นของ user เอง (กัน pid reuse)"""
    owner = _run(["ps", "-p", pid, "-o", "user="]).strip()
    if owner != USER:
        return False
    try:
        os.kill(int(pid), 15)
        return True
    except Exception:
        return False


# ── Feature 4: live sessions ──
def _tail_jsonl(path: Path, n_bytes: int = 8192, max_lines: int = 3) -> list[dict]:
    try:
        size = path.stat().st_size
        with path.open("rb") as f:
            f.seek(max(0, size - n_bytes))
            chunk = f.read()
    except OSError:
        return []
    lines = chunk.split(b"\n")
    if size > n_bytes:
        lines = lines[1:]  # ทิ้งบรรทัดแรกที่อาจขาด
    out = []
    for ln in lines[-max_lines:]:
        ln = ln.strip()
        if not ln:
            continue
        try:
            out.append(json.loads(ln))
        except Exception:
            continue
    return out


def _claude_pids_by_cwd() -> dict[str, str]:
    out = {}
    for line in _run(["ps", "-eo", "pid=,command="]).splitlines():
        line = line.strip()
        if CLAUDE_BIN not in line:
            continue
        pid = line.split(None, 1)[0]
        cwd = _lsof_cwd(pid)
        if cwd:
            out[cwd] = pid
    return out


def _decode_dir(name: str) -> str:
    # -Users-tae279-DEV-TAE-Fable-5 → /Users/tae279/DEV_TAE/Fable 5 (lossy fallback)
    return name.replace("-", "/")


def scan_live_sessions(window_min: int = 20, limit: int = 6) -> list[dict]:
    if not PROJECTS.exists():
        return []
    cutoff = time.time() - window_min * 60
    pids = _claude_pids_by_cwd()
    sessions = []
    for pdir in PROJECTS.iterdir():
        if not pdir.is_dir():
            continue
        # macOS: appending to a file does NOT bump parent-dir mtime, so we can't
        # skip whole dirs by dir mtime. stat per-file (cheap) and only tail-READ
        # survivors — reading 1.8GB is the expensive part we still avoid.
        for jf in pdir.glob("*.jsonl"):
            try:
                stt = jf.stat()
            except OSError:
                continue
            if stt.st_mtime < cutoff or stt.st_size == 0:
                continue
            evs = _tail_jsonl(jf)
            if not evs:
                continue
            last = evs[-1]
            cwd = last.get("cwd") or _decode_dir(pdir.name)
            state = _infer_state(evs, cwd in pids)
            if state is None:
                continue
            sessions.append({
                "project": Path(cwd).name or cwd,
                "cwd": cwd,
                "state": state,
                "last": stt.st_mtime,
                "alive": cwd in pids,
            })
    sessions.sort(key=lambda s: s["last"], reverse=True)
    return sessions[:limit]


def _infer_state(evs: list[dict], has_pid: bool) -> str | None:
    last = evs[-1]
    t = last.get("type")
    # assistant + tool_use ท้าย = กำลังรันเครื่องมือ
    if t == "assistant":
        content = last.get("message", {}).get("content", [])
        if isinstance(content, list) and any(b.get("type") == "tool_use" for b in content):
            return "executing"
        return "thinking" if has_pid else "idle"
    if t == "user":  # tool_result รอ assistant ตอบ
        return "thinking" if has_pid else "idle"
    return "idle" if has_pid else None


def humanize_ago(ts: float) -> str:
    d = int(time.time() - ts)
    if d < 60:
        return f"{d}s"
    if d < 3600:
        return f"{d // 60}m"
    return f"{d // 3600}h {(d % 3600) // 60}m"


if __name__ == "__main__":
    # ponytail self-check: functions รันได้ไม่ crash + shape ถูก
    servers = scan_dev_servers()
    assert isinstance(servers, list)
    for s in servers:
        assert s["port"] != SELF_PORT and 3000 <= s["port"] <= 9999
    sess = scan_live_sessions()
    assert isinstance(sess, list) and len(sess) <= 6
    for s in sess:
        assert s["state"] in ("executing", "thinking", "idle")
    print(f"OK — {len(servers)} dev servers, {len(sess)} live sessions")
    for s in servers:
        print(f"  :{s['port']} {s['framework']} · {Path(s['cwd']).name if s['cwd'] else '?'}")
    for s in sess:
        print(f"  ● {s['project']} · {s['state']} · {humanize_ago(s['last'])} ago")
