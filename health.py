"""Doctor — service health checks, Claude login watch, LINE alerts, capped auto-restart.

Stdlib only, no Streamlit/FastAPI imports, so it runs from three places with the same code:
  - server.py        : background loop every 5 min + GET /api/doctor
  - CLI (launchd)    : `python health.py --heal` — works even when the API server is dead
  - tests

Claude login: `claude auth status` only says loggedIn true/false and does NOT expose an
expiry time (and reported loggedIn:true on 2026-09-03 while runs were already failing with
"OAuth session expired"). So we do not trust it alone. Signals used instead:
  1. a cheap real probe (`claude -p --model haiku`) every PROBE_EVERY_SEC
  2. auth errors seen in real runs (server.py reports them via record_run_result)
  3. `claude auth status` loggedIn == false
We never read ~/.claude/.credentials.json or the Keychain.

State lives in .cache/health.json (gitignored).
"""

from __future__ import annotations

import argparse
import fcntl
import json
import os
import re
import shutil
import subprocess
import sys
import time
import urllib.request
from contextlib import contextmanager
from pathlib import Path

ROOT = Path(__file__).parent
CACHE_DIR = ROOT / ".cache"
STATE_FILE = CACHE_DIR / "health.json"
LOCK_FILE = CACHE_DIR / "health.lock"
LINE_CONFIG = Path.home() / ".config" / "dx" / "line-notify.json"

API_PORT = int(os.environ.get("DOCTOR_API_PORT", 8787))
WEB_PORT = int(os.environ.get("DOCTOR_WEB_PORT", 3000))
LAUNCH_AGENTS = {
    "com.dx.agentic-os-queue-worker": "ตัวประมวลผลคิวงานมือถือ",
    "com.dx.agentic-os-snapshot": "ตัวส่งสแนปช็อตขึ้น VPS",
}

PROBE_EVERY_SEC = 6 * 3600       # real login probe cadence
PROBE_STALE_SEC = 26 * 3600      # warn if no probe result for this long
REMIND_EVERY_SEC = 6 * 3600      # re-send an unresolved FAIL alert at most this often
HEAL_MAX_PER_HOUR = 3            # restart budget per service
STATE_MAX_AGE_SEC = 90           # GET /api/doctor recomputes if the saved result is older

AUTH_ERROR_RE = re.compile(
    r"oauth|authenticat|not logged in|please run /login|/login|invalid.{0,20}(token|credential)|"
    r"session.{0,12}expired|\b401\b",
    re.I,
)

_CLAUDE_FALLBACKS = (
    Path.home() / ".local" / "bin" / "claude",
    Path("/opt/homebrew/bin/claude"),
    Path("/usr/local/bin/claude"),
)


# ─── small helpers ───────────────────────────────────────────

def _now() -> float:
    return time.time()


def _ago(ts: float | None, now: float | None = None) -> str:
    if not ts:
        return "ไม่เคย"
    secs = int((now or _now()) - ts)
    if secs < 90:
        return "เมื่อครู่"
    if secs < 5400:
        return f"{secs // 60} นาทีก่อน"
    if secs < 129600:
        return f"{secs // 3600} ชม.ก่อน"
    return f"{secs // 86400} วันก่อน"


def _check(cid: str, label: str, status: str, detail: str, fix: str = "") -> dict:
    return {"id": cid, "label": label, "status": status, "detail": detail, "fix": fix}


def _run(cmd: list[str], timeout: float, cwd: Path | None = None) -> subprocess.CompletedProcess | None:
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, cwd=cwd)
    except Exception:
        return None


def _find_claude() -> str | None:
    found = shutil.which("claude")
    if found:
        return found
    for p in _CLAUDE_FALLBACKS:
        if p.exists():
            return str(p)
    return None


def load_state() -> dict:
    try:
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_state(state: dict) -> None:
    CACHE_DIR.mkdir(exist_ok=True)
    tmp = STATE_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(state, ensure_ascii=False, indent=1), encoding="utf-8")
    tmp.replace(STATE_FILE)


@contextmanager
def _lock():
    """Non-blocking cross-process lock so the server loop and the launchd CLI never overlap."""
    CACHE_DIR.mkdir(exist_ok=True)
    fh = open(LOCK_FILE, "w")
    try:
        try:
            fcntl.flock(fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            yield False
            return
        yield True
    finally:
        fh.close()


# ─── individual checks ───────────────────────────────────────

def _http_ok(url: str, timeout: float = 3) -> tuple[bool, str]:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            return resp.status < 500, f"HTTP {resp.status}"
    except Exception as e:
        return False, type(e).__name__


def check_api(in_server: bool) -> dict:
    if in_server:  # we are the API — answering this request proves it's up
        return _check("api", "ระบบหลังบ้าน (API :8787)", "pass", "ทำงานปกติ")
    ok, detail = _http_ok(f"http://127.0.0.1:{API_PORT}/api/health")
    if ok:
        return _check("api", "ระบบหลังบ้าน (API :8787)", "pass", "ทำงานปกติ")
    return _check("api", "ระบบหลังบ้าน (API :8787)", "fail", f"ไม่ตอบ ({detail})",
                  "ดับเบิลคลิก 'เปิด Dashboard.command'")


def check_web() -> dict:
    ok, detail = _http_ok(f"http://127.0.0.1:{WEB_PORT}/")
    if ok:
        return _check("web", "หน้าเว็บ Dashboard (:3000)", "pass", "ทำงานปกติ")
    return _check("web", "หน้าเว็บ Dashboard (:3000)", "fail", f"ไม่ตอบ ({detail})",
                  "ดับเบิลคลิก 'เปิด Dashboard.command'")


def check_web_exposure() -> dict:
    """Informational: is :3000 reachable from other machines on the network?"""
    res = _run(["lsof", f"-iTCP:{WEB_PORT}", "-sTCP:LISTEN", "-P", "-n"], 5)
    out = res.stdout if res else ""
    if not out.strip():
        return _check("exposure", "ความเป็นส่วนตัวของหน้าเว็บ", "skip", "ไม่พบหน้าเว็บที่เปิดอยู่")
    if re.search(rf"(\*|0\.0\.0\.0):{WEB_PORT}\b", out):
        return _check("exposure", "ความเป็นส่วนตัวของหน้าเว็บ", "warn",
                      "หน้าเว็บเปิดให้เครื่องอื่นในวงเน็ตเดียวกันเข้าได้ (ฝั่ง API ปิดอยู่เครื่องเดียว)",
                      "ยังไม่ได้แก้ — รอเจ้าของตัดสินใจ (วิธีแก้: เริ่มหน้าเว็บด้วย -H 127.0.0.1)")
    return _check("exposure", "ความเป็นส่วนตัวของหน้าเว็บ", "pass", "เปิดเฉพาะเครื่องนี้")


def check_launch_agents() -> list[dict]:
    res = _run(["launchctl", "list"], 5)
    if not res or res.returncode != 0:
        return [_check("launchd", "ตัวรันอัตโนมัติ", "skip", "อ่านสถานะ launchctl ไม่ได้")]
    rows: dict[str, str] = {}
    for line in res.stdout.splitlines():
        parts = line.split("\t")
        if len(parts) == 3:
            rows[parts[2]] = parts[1]
    out = []
    for label, thai in LAUNCH_AGENTS.items():
        cid = "agent-" + label.rsplit(".", 1)[-1]
        if label not in rows:
            out.append(_check(cid, thai, "fail", "ไม่ได้โหลดอยู่", "ต้องโหลดตัวรันอัตโนมัติกลับ (ถามผู้ช่วยให้ทำ)"))
        elif rows[label] not in ("0", "-"):
            out.append(_check(cid, thai, "warn", f"รอบล่าสุดจบด้วยรหัส {rows[label]}", "ดู log ใน .cache/"))
        else:
            out.append(_check(cid, thai, "pass", "โหลดอยู่ ทำงานตามรอบ"))
    return out


def check_disk() -> dict:
    free_gb = shutil.disk_usage(ROOT).free / 1e9
    logs_mb = sum(f.stat().st_size for f in CACHE_DIR.glob("*.log")) / 1e6 if CACHE_DIR.exists() else 0
    if free_gb < 2:
        return _check("disk", "พื้นที่ดิสก์", "fail", f"เหลือ {free_gb:.1f} GB", "ล้างไฟล์ก่อน งานอาจล้ม")
    if logs_mb > 500:
        return _check("disk", "พื้นที่ดิสก์", "warn", f"log ใหญ่ {logs_mb:.0f} MB", "ล้าง .cache/*.log")
    return _check("disk", "พื้นที่ดิสก์", "pass", f"เหลือ {free_gb:.0f} GB")


# ─── Claude login ────────────────────────────────────────────

def auth_status() -> dict | None:
    """Parsed `claude auth status` (JSON is its default output), or None if unavailable."""
    claude = _find_claude()
    if not claude:
        return None
    res = _run([claude, "auth", "status"], 8)
    if not res:
        return None
    try:
        return json.loads(res.stdout)
    except Exception:
        return None


def run_probe(timeout: float = 90) -> dict:
    """One tiny real Claude call (haiku). Costs a fraction of a cent; also exercises token refresh."""
    claude = _find_claude()
    if not claude:
        return {"ts": _now(), "ok": False, "auth_error": False, "detail": "ไม่พบโปรแกรม claude"}
    res = _run([claude, "-p", "--model", "haiku", "Reply with exactly: OK"], timeout, cwd=CACHE_DIR if CACHE_DIR.exists() else ROOT)
    if res is None:
        return {"ts": _now(), "ok": False, "auth_error": False, "detail": "ไม่ตอบภายในเวลาที่กำหนด"}
    text = (res.stdout + "\n" + res.stderr).strip()
    if res.returncode == 0 and "OK" in res.stdout:
        return {"ts": _now(), "ok": True, "auth_error": False, "detail": "ตอบกลับปกติ"}
    return {"ts": _now(), "ok": False, "auth_error": bool(AUTH_ERROR_RE.search(text)), "detail": text[:200] or f"exit {res.returncode}"}


def record_run_result(ok: bool, error: str | None) -> None:
    """Called by server.py after every real run. A login failure in a real run is the strongest signal."""
    try:
        state = load_state()
        if ok:
            if "run_auth_error" in state:
                del state["run_auth_error"]
                save_state(state)
        elif error and AUTH_ERROR_RE.search(error):
            state["run_auth_error"] = {"ts": _now(), "detail": error[:200]}
            save_state(state)
    except Exception:
        pass


def evaluate_login(state: dict, status: dict | None, now: float | None = None) -> dict:
    now = _now() if now is None else now
    label = "Claude login"
    fix_login = "เปิด Terminal พิมพ์ claude แล้วพิมพ์ /login"
    probe = state.get("probe") or {}
    run_err = state.get("run_auth_error")

    if status is not None and status.get("loggedIn") is False:
        return _check("login", label, "fail", "ยังไม่ได้ login (หรือถูกออกจากระบบ)", fix_login)
    if run_err:  # cleared by record_run_result(ok) or a passing probe
        return _check("login", label, "fail",
                      f"งานล่าสุดล้มเพราะ login หมดอายุ ({_ago(run_err['ts'], now)})", fix_login)
    if probe and not probe.get("ok") and probe.get("auth_error"):
        return _check("login", label, "fail", f"ทดสอบ login ไม่ผ่าน ({_ago(probe.get('ts'), now)})", fix_login)
    if probe and not probe.get("ok"):
        return _check("login", label, "warn",
                      f"ทดสอบ login ไม่สำเร็จด้วยสาเหตุอื่น: {probe.get('detail', '')[:80]}", "ตรวจอินเทอร์เน็ต แล้วกด 'ทดสอบ login'")
    if not probe or now - probe.get("ts", 0) > PROBE_STALE_SEC:
        return _check("login", label, "warn", "ยังไม่ได้ทดสอบ login ในรอบ 24 ชม.", "กด 'ทดสอบ login ตอนนี้'")
    return _check("login", label, "pass", f"ทดสอบล่าสุด {_ago(probe['ts'], now)} — ใช้งานได้")


# ─── LINE alerts ─────────────────────────────────────────────

def _line_push(text: str) -> bool:
    # Persistent off switch: `touch .cache/notify-off` (survives restarts the doctor itself spawns)
    if os.environ.get("DOCTOR_NOTIFY", "1") == "0" or (CACHE_DIR / "notify-off").exists():
        print(f"[doctor] (notify off) {text}", file=sys.stderr)
        return False
    try:
        cfg = json.loads(LINE_CONFIG.read_text(encoding="utf-8"))
        body = json.dumps({"to": cfg["user_id"], "messages": [{"type": "text", "text": text[:900]}]}).encode()
        req = urllib.request.Request(
            "https://api.line.me/v2/bot/message/push",
            data=body,
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {cfg['channel_access_token']}"},
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status == 200
    except Exception:
        return False  # alerts must never crash the doctor


def plan_alerts(state: dict, checks: list[dict], now: float | None = None, hold: set[str] | None = None) -> list[str]:
    """Pure: decide which LINE messages to send, and update state['alerts'] (open incidents).
    `hold` = check ids we just tried to restart; give them a cycle before alerting."""
    now = _now() if now is None else now
    open_alerts: dict = state.setdefault("alerts", {})
    msgs: list[str] = []
    by_id = {c["id"]: c for c in checks}
    for c in checks:
        if c["status"] == "fail" and c["id"] not in (hold or set()):
            prev = open_alerts.get(c["id"])
            if prev is None or now - prev["sent"] > REMIND_EVERY_SEC:
                head = "🔴" if prev is None else "🔴 (ยังไม่แก้)"
                fix = f"\nวิธีแก้: {c['fix']}" if c.get("fix") else ""
                msgs.append(f"{head} DX Command Center: {c['label']} — {c['detail']}{fix}")
                open_alerts[c["id"]] = {"sent": now, "since": prev["since"] if prev else now}
    for cid in list(open_alerts):
        c = by_id.get(cid)
        if c and c["status"] != "fail":
            msgs.append(f"🟢 DX Command Center: {c['label']} กลับมาปกติแล้ว")
            del open_alerts[cid]
    return msgs


# ─── auto-restart (capped) ───────────────────────────────────

def _heal_allowed(state: dict, target: str, now: float) -> bool:
    recent = [h for h in state.get("heal_log", []) if h["target"] == target and now - h["ts"] < 3600]
    return len(recent) < HEAL_MAX_PER_HOUR


def _spawn(cmd: list[str], logname: str, cwd: Path) -> None:
    CACHE_DIR.mkdir(exist_ok=True)
    log = open(CACHE_DIR / logname, "ab")
    subprocess.Popen(cmd, cwd=cwd, stdout=log, stderr=log, stdin=subprocess.DEVNULL, start_new_session=True)


def heal(state: dict, checks: list[dict], now: float | None = None) -> list[str]:
    """Restart a dead API / web server exactly the way 'เปิด Dashboard.command' does. Returns log lines."""
    now = _now() if now is None else now
    notes: list[str] = []
    log = state.setdefault("heal_log", [])
    by_id = {c["id"]: c for c in checks}

    if by_id.get("api", {}).get("status") == "fail":
        py = ROOT / ".venv" / "bin" / "python"
        if not _heal_allowed(state, "api", now):
            notes.append("api: ถึงเพดานรีสตาร์ท 3 ครั้ง/ชม. แล้ว — หยุดลองเอง")
        elif not py.exists():
            notes.append("api: ไม่พบ .venv — รีสตาร์ทเองไม่ได้")
        else:
            _spawn([str(py), "-m", "uvicorn", "server:app", "--host", "127.0.0.1", "--port", str(API_PORT)], "uvicorn.log", ROOT)
            log.append({"ts": now, "target": "api"})
            notes.append("api: สั่งเปิดใหม่แล้ว")

    if by_id.get("web", {}).get("status") == "fail":
        if not (ROOT / "web" / ".next" / "BUILD_ID").exists():
            notes.append("web: ยังไม่เคย build หน้าเว็บ — รีสตาร์ทเองไม่ได้")
        elif not _heal_allowed(state, "web", now):
            notes.append("web: ถึงเพดานรีสตาร์ท 3 ครั้ง/ชม. แล้ว — หยุดลองเอง")
        else:
            npm = shutil.which("npm") or "/opt/homebrew/bin/npm"
            _spawn([npm, "run", "start", "--", "-p", str(WEB_PORT)], "next.log", ROOT / "web")
            log.append({"ts": now, "target": "web"})
            notes.append("web: สั่งเปิดใหม่แล้ว")

    state["heal_log"] = [h for h in log if now - h["ts"] < 86400][-50:]
    return notes


# ─── orchestration ───────────────────────────────────────────

def collect_checks(state: dict, in_server: bool) -> list[dict]:
    checks = [check_api(in_server), check_web(), evaluate_login(state, auth_status())]
    checks += check_launch_agents()
    checks += [check_disk(), check_web_exposure()]
    return checks


def overall(checks: list[dict]) -> str:
    sts = {c["status"] for c in checks}
    return "fail" if "fail" in sts else "warn" if "warn" in sts else "pass"


def run_cycle(*, in_server: bool = False, probe: bool | None = None, do_heal: bool = True, notify: bool = True) -> dict:
    """One full doctor pass. probe=None → probe only if the last one is older than PROBE_EVERY_SEC."""
    with _lock() as got:
        if not got:
            return snapshot(load_state())
        state = load_state()
        now = _now()
        if probe is None:
            probe = now - (state.get("probe") or {}).get("ts", 0) > PROBE_EVERY_SEC
        if probe:
            state["probe"] = run_probe()
            if state["probe"]["ok"]:
                state.pop("run_auth_error", None)
        checks = collect_checks(state, in_server)
        heal_notes = heal(state, checks, now) if do_heal and os.environ.get("DOCTOR_AUTOHEAL", "1") != "0" else []
        if heal_notes:
            time.sleep(8)  # give the restarted service a moment before we judge it again
            checks = collect_checks(state, in_server)
        held = {n.split(":")[0] for n in heal_notes if "สั่งเปิดใหม่แล้ว" in n}
        msgs = plan_alerts(state, checks, now, hold=held)
        if notify:
            for m in msgs:
                _line_push(m)
        state.update(ts=now, checks=checks, overall=overall(checks), heal_notes=heal_notes,
                     last_alerts=(msgs + state.get("last_alerts", []))[:10])
        save_state(state)
        return snapshot(state)


def snapshot(state: dict) -> dict:
    probe = state.get("probe") or {}
    return {
        "ts": state.get("ts"),
        "overall": state.get("overall", "unknown"),
        "checks": state.get("checks", []),
        "probe": {"ts": probe.get("ts"), "ok": probe.get("ok"), "detail": probe.get("detail")} if probe else None,
        "heal_notes": state.get("heal_notes", []),
        "heal_log": state.get("heal_log", [])[-5:],
        "last_alerts": state.get("last_alerts", [])[:5],
    }


def get_snapshot(in_server: bool = True) -> dict:
    """What GET /api/doctor returns: the saved result, recomputed (cheap checks only) if stale."""
    state = load_state()
    if not state.get("ts") or _now() - state["ts"] > STATE_MAX_AGE_SEC:
        return run_cycle(in_server=in_server, probe=False, do_heal=False, notify=False)
    return snapshot(state)


def main() -> int:
    ap = argparse.ArgumentParser(description="DX Command Center doctor")
    ap.add_argument("--probe", action="store_true", help="force a real Claude login probe now")
    ap.add_argument("--heal", action="store_true", help="restart dead services (capped)")
    ap.add_argument("--no-notify", action="store_true", help="do not send LINE")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    snap = run_cycle(probe=True if args.probe else None, do_heal=args.heal, notify=not args.no_notify)
    if args.json:
        print(json.dumps(snap, ensure_ascii=False, indent=1))
    else:
        icon = {"pass": "PASS", "warn": "WARN", "fail": "FAIL", "skip": "SKIP"}
        for c in snap["checks"]:
            print(f"[{icon.get(c['status'], '?')}] {c['label']}: {c['detail']}")
        for n in snap["heal_notes"]:
            print(f"  ↻ {n}")
    return 1 if snap["overall"] == "fail" else 0


if __name__ == "__main__":
    sys.exit(main())
