"""Multi-turn chat backend — spawns `claude -p` (+ `--resume`) and parses
stream-json events. Shared by the AI Chat dialog in app.py / pages/*.py.

ponytail: blocking subprocess call per turn (no background thread) — chat is
request/response, not a long skill run, so st.spinner + blocking read is the
simplest correct thing. Upgrade to streaming-in-UI only if turns start feeling slow.
"""

import json
import subprocess
from pathlib import Path

import streamlit as st

from config import CLAUDE_CLI


def _default_escape(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def send_chat_message(message: str, session_id: str | None) -> dict:
    """Run one chat turn. Returns dict: text, tool_names, cost_usd, session_id, error."""
    cmd = [str(CLAUDE_CLI), "-p", message, "--output-format", "stream-json", "--verbose"]
    if session_id:
        cmd += ["--resume", session_id]

    out = {"text": "", "tool_names": [], "cost_usd": None, "session_id": session_id, "error": None}
    try:
        proc = subprocess.run(
            cmd, cwd=str(Path.home()), capture_output=True, text=True,
            timeout=300, encoding="utf-8", errors="replace",
        )
    except Exception as e:
        out["error"] = str(e)
        return out

    for line in proc.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            evt = json.loads(line)
        except json.JSONDecodeError:
            continue
        sid = evt.get("session_id")
        if sid:
            out["session_id"] = sid
        t = evt.get("type")
        if t == "assistant":
            for block in evt.get("message", {}).get("content", []):
                if block.get("type") == "text":
                    out["text"] += block.get("text", "")
                elif block.get("type") == "tool_use":
                    out["tool_names"].append(block.get("name", "tool"))
        elif t == "result":
            out["cost_usd"] = evt.get("total_cost_usd") or evt.get("cost_usd")
            if evt.get("subtype") != "success":
                out["error"] = evt.get("result") or evt.get("subtype")

    if proc.returncode != 0 and not out["error"]:
        out["error"] = f"exit {proc.returncode}: {proc.stderr[:300]}"
    return out


def _ensure_state():
    if "chat_msgs" not in st.session_state:
        st.session_state.chat_msgs = []  # list[{"role", "text", "tools"}]
    if "chat_sid" not in st.session_state:
        st.session_state.chat_sid = None
    if "chat_cost_total" not in st.session_state:
        st.session_state.chat_cost_total = 0.0


@st.dialog("💬 คุยกับ Claude", width="large")
def render_chat_dialog(html_escape=None):
    """Shared chat modal — called from both app.py and pages/portfolio.py.
    session_state persists across Streamlit's native multipage nav, so history
    and session_id survive switching pages / closing+reopening the dialog.
    """
    escape = html_escape or _default_escape
    _ensure_state()

    for m in st.session_state.chat_msgs:
        with st.chat_message(m["role"]):
            st.markdown(m["text"])
            for tool_name in m.get("tools", []):
                st.markdown(
                    f'<span style="font-family:\'JetBrains Mono\',monospace;font-size:.68rem;'
                    f'padding:1px 7px;border-radius:99px;border:1px solid var(--ring-soft);'
                    f'color:var(--fg-dim);margin-right:.3rem">⚙ {escape(tool_name)}</span>',
                    unsafe_allow_html=True,
                )

    st.markdown(
        f'<div class="caption-mono" style="color:var(--fg-mute);margin:.4rem 0">'
        f'รวม ${st.session_state.chat_cost_total:.2f}</div>',
        unsafe_allow_html=True,
    )
    if st.session_state.chat_cost_total > 2.0:
        st.warning(f"ใช้ไปแล้ว ${st.session_state.chat_cost_total:.2f} ในแชทนี้ — เกิน $2")

    msg = st.chat_input("พิมพ์ข้อความ…")
    if msg:
        st.session_state.chat_msgs.append({"role": "user", "text": msg, "tools": []})
        with st.spinner("Claude กำลังตอบ…"):
            result = send_chat_message(msg, st.session_state.chat_sid)
        if result["session_id"]:
            st.session_state.chat_sid = result["session_id"]
        if result["cost_usd"]:
            st.session_state.chat_cost_total += float(result["cost_usd"])
        reply_text = result["text"] or (f"⚠️ error: {result['error']}" if result["error"] else "(ไม่มีคำตอบ)")
        st.session_state.chat_msgs.append({
            "role": "assistant", "text": reply_text, "tools": result["tool_names"],
        })
        st.rerun()

    c1, c2 = st.columns(2)
    with c1:
        if st.button("เริ่มแชทใหม่", use_container_width=True, key="chat_new_btn"):
            st.session_state.chat_msgs = []
            st.session_state.chat_sid = None
            st.session_state.chat_cost_total = 0.0
            st.rerun()
    with c2:
        last_user_msg = next(
            (m["text"] for m in reversed(st.session_state.chat_msgs) if m["role"] == "user"), None
        )
        if st.button("ส่งเข้า RUN →", use_container_width=True, disabled=not last_user_msg, key="chat_to_run_btn"):
            st.session_state.prompt_input_widget = last_user_msg
            st.switch_page("app.py")
