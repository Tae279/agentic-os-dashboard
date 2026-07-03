"""Portfolio page — รวมผลงาน DX ทุกโปรเจค (การ์ด + สถานะ + เอกสาร + AI แนะนำ)

Native Streamlit multipage: ไฟล์นี้อยู่ใน pages/ → URL /portfolio อัตโนมัติ
app.py ไม่ต้องแก้ (เป็นหน้าหลักเอง) — แชร์ธีมผ่าน theme.inject()

ponytail: parser อ่าน registry+memory ตรงๆ ไม่มี DB; AI reco = blocking subprocess
call เดียวตอนกดปุ่ม (ไม่ async เพราะ manual refresh พอ) — อัปเป็น routine เช้าได้ทีหลัง
"""

import json
import re
import subprocess
import time
from datetime import datetime, date
from pathlib import Path

import streamlit as st

import theme
from config import CLAUDE_CLI, DASHBOARD_DATA

st.set_page_config(page_title="Portfolio · Agentic OS", page_icon="⌗", layout="wide")
theme.inject()

REGISTRY = Path.home() / "Documents" / "DX" / "agent-context" / "project-registry.md"
LONG_TERM = Path.home() / ".dx-claude-config" / "memory" / "long-term.md"
ARTIFACTS = Path.home() / "Documents" / "DX" / "artifacts"
RECO_FILE = DASHBOARD_DATA / "recommendations.json"

# ── สถานะ: เดาจากคำใน entry ล่าสุดของโปรเจค ──
_DONE = ("complete", "closed", "done", "100%", "shipped", "เสร็จ")
_PAUSE = ("pause", "paused", "pending", "declined", "rejected", "หยุด", "พัก")


def _status(text: str) -> tuple[str, str]:
    low = text.lower()
    if any(w in low for w in _PAUSE):
        return "⏸️", "pause"
    if any(w in low for w in _DONE):
        return "✅", "done"
    return "🔵", "active"


@st.cache_data(ttl=600)
def parse_registry() -> list[dict]:
    """อ่านตาราง 'Core active workstreams' จาก project-registry.md"""
    if not REGISTRY.exists():
        return []
    rows = []
    in_core = False
    for line in REGISTRY.read_text(encoding="utf-8").splitlines():
        if line.startswith("## Core active"):
            in_core = True
            continue
        if in_core and line.startswith("## "):
            break
        if in_core and line.startswith("|") and "---" not in line:
            cells = [c.strip() for c in line.strip("|").split("|")]
            if len(cells) < 8 or cells[0] in ("Project", ""):
                continue
            rows.append({
                "name": cells[0],
                "tag": cells[1].strip("`"),
                "aliases": cells[2],
                "docs": cells[3].strip("`"),
                "code": cells[4].strip("`"),
                "priority": cells[6],
                "notes": cells[7],
            })
    return rows


@st.cache_data(ttl=600)
def parse_long_term() -> list[dict]:
    """แตก long-term.md เป็น entry: date, title, summary, tags, next"""
    if not LONG_TERM.exists():
        return []
    text = LONG_TERM.read_text(encoding="utf-8")
    # ตัด Archive ทิ้ง — เอาเฉพาะบันทึกล่าสุด
    text = text.split("## Archive")[0]
    entries = []
    parts = re.split(r"^### \[(\d{4}-\d{2}-\d{2})\] (.+)$", text, flags=re.M)
    # parts = [pre, date1, title1, body1, date2, title2, body2, ...]
    for i in range(1, len(parts) - 2, 3):
        d, title, body = parts[i], parts[i + 1], parts[i + 2]
        if title.startswith("YYYY"):  # ตัวอย่าง format ในหัวไฟล์
            continue
        tags = ""
        summary = ""
        nxt = ""
        for m in re.finditer(r"\*\*(สรุป|Tags|Next):\*\*\s*(.+)", body):
            if m.group(1) == "สรุป":
                summary = m.group(2)
            elif m.group(1) == "Tags":
                tags = m.group(2)
            elif m.group(1) == "Next":
                nxt = m.group(2)
        entries.append({
            "date": d, "title": title.strip(),
            "summary": summary, "tags": tags, "next": nxt,
            "blob": (title + " " + tags).lower(),
        })
    return entries


_GENERIC = {"os", "ai", "line", "hub", "rms", "centroid", "mt5", "c24", "academy", "agent"}


def newest_entry_for(proj: dict, entries: list[dict]) -> dict | None:
    """match tag ก่อน (แม่น) แล้วค่อย alias ที่ไม่กว้างเกิน. ไม่เจอ=None → ใช้ registry notes."""
    tag = proj["tag"].lower()
    for e in entries:
        if tag in e["blob"]:
            return e
    aliases = [a.strip().lower() for a in proj["aliases"].split(",")
               if len(a.strip()) > 4 and a.strip().lower() not in _GENERIC]
    for e in entries:
        if any(a in e["blob"] for a in aliases):
            return e
    return None


@st.cache_data(ttl=600)
def artifacts_index() -> list[tuple[str, str, float]]:
    """(ชื่อไฟล์, path, mtime) ของ *.html ใน artifacts เรียงใหม่สุดก่อน"""
    if not ARTIFACTS.exists():
        return []
    out = []
    for f in ARTIFACTS.glob("*.html"):
        if "backup" in f.name.lower():
            continue
        out.append((f.name, str(f), f.stat().st_mtime))
    return sorted(out, key=lambda x: x[2], reverse=True)


def artifacts_for(proj: dict, arts: list) -> list[tuple[str, str]]:
    """map artifact เข้าโปรเจคด้วย keyword ในชื่อไฟล์"""
    keys = [proj["tag"].split("-")[0].lower()]
    keys += [a.strip().lower().split()[0] for a in proj["aliases"].split(",") if a.strip()]
    keys = list({k for k in keys if len(k) > 3})
    hits = []
    for name, path, _ in arts:
        low = name.lower()
        if any(k in low for k in keys):
            hits.append((name, path))
    return hits[:6]


def open_path(p: str):
    try:
        subprocess.run(["open", p], timeout=5)
    except Exception:
        pass


# ═══════════════════════════════════════════════════════════
# HEADER
# ═══════════════════════════════════════════════════════════
st.markdown(
    """
    <style>
    .pf-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(320px,1fr));gap:1rem;margin-top:0.5rem}
    .pf-card{background:linear-gradient(160deg,var(--bg-card-hi),var(--bg-card));
        border:1px solid var(--ring-soft);border-radius:10px;padding:0;overflow:hidden;
        transition:box-shadow .15s,transform .15s}
    .pf-card:hover{box-shadow:0 0 0 1px var(--accent),0 10px 30px rgba(2,74,218,.25);transform:translateY(-2px)}
    .pf-thumb{height:96px;display:flex;align-items:center;justify-content:center;
        font-family:'Space Grotesk',monospace;font-weight:700;font-size:1.5rem;letter-spacing:-.02em;
        color:#fff;text-shadow:0 2px 12px rgba(0,0,0,.4)}
    .pf-body{padding:0.9rem 1.1rem 1.1rem}
    .pf-name{font-family:'Space Grotesk',monospace;font-weight:600;font-size:1.05rem;color:var(--fg);margin-bottom:.15rem}
    .pf-badge{font-family:'JetBrains Mono',monospace;font-size:.66rem;letter-spacing:.08em;text-transform:uppercase;
        padding:1px 8px;border-radius:99px;display:inline-block;margin-bottom:.5rem}
    .pf-badge.done{color:var(--good);border:1px solid rgba(70,192,122,.4)}
    .pf-badge.active{color:var(--accent);border:1px solid rgba(61,123,255,.4)}
    .pf-badge.pause{color:var(--warn);border:1px solid rgba(224,179,92,.4)}
    .pf-last{font-size:.82rem;color:var(--fg-dim);line-height:1.5;margin-bottom:.5rem;
        display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
    .pf-date{font-family:'JetBrains Mono',monospace;font-size:.68rem;color:var(--fg-mute)}
    .pf-docs a{display:block;font-size:.76rem;color:#8fb3ff;text-decoration:none;padding:2px 0;
        white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
    .pf-docs a:hover{color:var(--accent)}
    .reco-sec{border-left:2px solid var(--accent);padding-left:.9rem;margin:.7rem 0}
    .reco-sec h4{font-family:'JetBrains Mono',monospace;font-size:.72rem;letter-spacing:.1em;
        text-transform:uppercase;color:var(--accent);margin:0 0 .3rem}
    .reco-sec li{font-size:.86rem;color:var(--fg);margin:.2rem 0}
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="quicknav"><a href="/" target="_self"><span class="qn-icon">◆</span>← command</a>'
    '<span class="qn-status" style="margin-left:auto">portfolio</span></div>',
    unsafe_allow_html=True,
)
st.markdown('<div class="cpt-cat">ผลงาน · portfolio</div>', unsafe_allow_html=True)

projects = parse_registry()
entries = parse_long_term()
arts = artifacts_index()

# ═══════════════════════════════════════════════════════════
# AI RECOMMENDATION
# ═══════════════════════════════════════════════════════════
RECO_PROMPT = (
    "Act autonomously. Read ~/.dx-claude-config/memory/long-term.md (top 12 entries) "
    "and ~/Documents/DX/agent-context/project-registry.md. For each project, look at its "
    "newest entry's Next/Decisions. Then output STRICT JSON only (no prose, no markdown fence) "
    'with keys: must_do (array of {text, project}), nice_to_do (array of {text, project}), '
    "ideas (array of {text, why}). must_do = reminders/decisions waiting or overdue next-steps. "
    "nice_to_do = opportunities visible from current state. ideas = new project ideas fitting "
    "DX direction (fintech/BestonFX, AI agents, content, DX Academy). Thai language for all text. "
    "Max 5 items each. Write the JSON to "
    f"{RECO_FILE} and also print it."
)

with st.container():
    c1, c2 = st.columns([4, 1])
    with c1:
        st.markdown('<div class="cpt-cat">✱ FABLE แนะนำ</div>', unsafe_allow_html=True)
    with c2:
        refresh = st.button("↻ refresh", use_container_width=True, key="reco_refresh")

    if refresh:
        with st.spinner("Fable กำลังอ่าน memory + คิดว่ามีอะไรน่าทำ… (~1 นาที)"):
            try:
                subprocess.run(
                    [str(CLAUDE_CLI), "-p", RECO_PROMPT, "--permission-mode", "bypassPermissions"],
                    capture_output=True, text=True, timeout=240, cwd=str(Path.home()),
                )
            except Exception as e:
                st.warning(f"refresh ไม่สำเร็จ: {e}")

    reco = {}
    if RECO_FILE.exists():
        try:
            raw = RECO_FILE.read_text(encoding="utf-8")
            m = re.search(r"\{.*\}", raw, re.S)
            reco = json.loads(m.group(0) if m else raw)
        except Exception:
            reco = {}

    if reco:
        for key, label in [("must_do", "ต้องทำ / reminder"),
                           ("nice_to_do", "น่าทำ"),
                           ("ideas", "project ideas ใหม่")]:
            items = reco.get(key) or []
            if not items:
                continue
            lis = "".join(
                f"<li>{it.get('text','')}"
                + (f" <span style='color:var(--fg-mute);font-size:.75rem'>· {it.get('project') or it.get('why','')}</span>"
                   if (it.get('project') or it.get('why')) else "")
                + "</li>"
                for it in items
            )
            st.markdown(
                f'<div class="reco-sec"><h4>{label}</h4><ul style="margin:0;padding-left:1.1rem">{lis}</ul></div>',
                unsafe_allow_html=True,
            )
        if RECO_FILE.exists():
            ts = datetime.fromtimestamp(RECO_FILE.stat().st_mtime).strftime("%d %b %H:%M")
            st.markdown(f'<div class="pf-date">อัปเดตล่าสุด · {ts}</div>', unsafe_allow_html=True)
    else:
        st.caption("ยังไม่มีคำแนะนำ — กด ↻ refresh ให้ Fable อ่าน memory แล้วเสนอว่ามีอะไรน่าทำ")

st.markdown("<div style='height:1.2rem'></div>", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════
# PROJECT CARDS
# ═══════════════════════════════════════════════════════════
if not projects:
    st.warning("อ่าน project-registry.md ไม่ได้")
else:
    # gradient เดียวธีม DX แต่ไล่เฉดตาม index
    grads = [
        "linear-gradient(135deg,#024ada,#3d7bff)",
        "linear-gradient(135deg,#1254e8,#2261f0)",
        "linear-gradient(135deg,#0b3aa8,#3d7bff)",
        "linear-gradient(135deg,#2261f0,#5c8dff)",
    ]
    cols = st.columns(3, gap="medium")
    for i, proj in enumerate(projects):
        e = newest_entry_for(proj, entries)
        icon, cls = _status(f"{e['title']} {e['summary']}" if e else proj["notes"])
        last = (e["summary"][:110] + "…") if e and len(e["summary"]) > 110 else (e["summary"] if e else proj["notes"])
        dt = e["date"] if e else "—"
        initials = "".join(w[0] for w in re.findall(r"[A-Za-z]+", proj["name"])[:3]).upper() or proj["name"][:2].upper()
        docs = artifacts_for(proj, arts)
        doc_links = "".join(
            f'<a href="#" onclick="return false">{n.replace(".html","")}</a>' for n, _ in docs[:3]
        )

        with cols[i % 3]:
            st.markdown(
                f'''<div class="pf-card">
                <div class="pf-thumb" style="background:{grads[i % len(grads)]}">{initials}</div>
                <div class="pf-body">
                    <div class="pf-name">{proj["name"]}</div>
                    <span class="pf-badge {cls}">{icon} {cls}</span>
                    <div class="pf-last">{last}</div>
                    <div class="pf-date">ล่าสุด · {dt} · {proj["priority"]}</div>
                </div></div>''',
                unsafe_allow_html=True,
            )
            b1, b2 = st.columns(2)
            with b1:
                if st.button("▶ ทำต่อ", key=f"resume_{proj['tag']}", use_container_width=True):
                    st.session_state.prompt_input_widget = (
                        "Act autonomously. Read ~/.dx-claude-config/memory/long-term.md and find the "
                        f"newest entry for project '{proj['name']}' (tag {proj['tag']}, aliases: {proj['aliases']}). "
                        f"Read its resume/HANDOFF files under {proj['docs']}. Produce a Thai brief: current "
                        "state, ordered next steps, decisions waiting on Tae. Brief only — do NOT edit project "
                        "code (this dashboard runs Claude in the vault, not the project repo)."
                    )
                    st.session_state.last_chip_label = f"{proj['name']} — ทำต่อ"
                    st.switch_page("app.py")
            with b2:
                if st.button("📂 เปิด", key=f"open_{proj['tag']}", use_container_width=True):
                    open_path(proj["code"] if proj["code"] not in ("TBD", "N/A") else proj["docs"])

            if docs:
                with st.expander(f"📄 เอกสาร {len(docs)}"):
                    for n, p in docs:
                        if st.button(n.replace(".html", ""), key=f"doc_{proj['tag']}_{n}", use_container_width=True):
                            open_path(p)

# ═══════════════════════════════════════════════════════════
# UNMATCHED ARTIFACTS — "ทั่วไป"
# ═══════════════════════════════════════════════════════════
matched = set()
for proj in projects:
    for n, _ in artifacts_for(proj, arts):
        matched.add(n)
unmatched = [(n, p) for n, p, _ in arts if n not in matched][:20]
if unmatched:
    st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
    with st.expander(f"📁 เอกสารทั่วไป (ยังไม่ผูกโปรเจค) · {len(unmatched)}"):
        for n, p in unmatched:
            if st.button(n.replace(".html", ""), key=f"gen_{n}", use_container_width=True):
                open_path(p)
