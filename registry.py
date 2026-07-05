"""Shared project-registry parser — used by pages/portfolio.py and the
Decision Inbox (app.py + pages/portfolio.py). Single source, avoids two
copies of the same regex/table-parsing drifting apart.
"""

import re
from pathlib import Path

import streamlit as st

REGISTRY = Path.home() / "Documents" / "DX" / "agent-context" / "project-registry.md"
LONG_TERM = Path.home() / ".dx-claude-config" / "memory" / "long-term.md"


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

# bridge registry tag → memory tags ที่ entry ใช้จริง (memory เขียนคนละ tag กับ registry)
# ป้องกัน false-match ข้ามโปรเจค (bestonfx family). ตัวแรกที่เจอ = ชนะ, list เรียงเฉพาะ→กว้าง
MATCH_TAGS = {
    "bestonfx-mt5-ops": ["bestonfx-rms", "phase0-complete", "ddl-rls"],
    "bestonfx-v2":      ["v2-fresh-start", "pannawat", "trade-smarter", "whole-site-redesign", "bestonfx-revamp"],
    "bestonfx-promos":  ["bestonfx-test", "hyperframes", "remotion-promo"],
    "beston-line-oa":   ["beston-line", "line-oa", "liff"],
    "hermes-local":     ["hermes-triple", "hermes-workspace", "hermes-prompts", "m1-workspace"],
    "dx-design-os":     ["design-os-hardening", "design-os-audit", "dx-plan-renderer"],
    "dx-academy":       ["dx-academy", "cfd-academy", "dx-content-system"],
    "ai-agent-os":      ["ai-agent-os"],
    "aibm":             ["aibm"],
    "centroid-rms":     ["centroid-rms", "c24-obsidian"],
    "dx-hub-2026":      ["dx-hub"],
}


def newest_entry_for(proj: dict, entries: list[dict]) -> dict | None:
    """match ผ่าน MATCH_TAGS (canonical bridge) → tag → alias ที่ไม่กว้างเกิน.
    entries เรียงใหม่→เก่า. ไม่เจอ=None → การ์ดใช้ registry notes (ดีกว่าโชว์ผิด)."""
    tag = proj["tag"].lower()
    keys = MATCH_TAGS.get(tag, []) + [tag]
    for e in entries:
        if any(k in e["blob"] for k in keys):
            return e
    aliases = [a.strip().lower() for a in proj["aliases"].split(",")
               if len(a.strip()) > 4 and a.strip().lower() not in _GENERIC]
    for e in entries:
        if any(a in e["blob"] for a in aliases):
            return e
    return None


# ─── Decision Inbox — parse "Decision Queue"/"รอ Tae"/"รอเต้" sections ───

_DECISION_HEADING_RE = re.compile(
    r"(decision queue|รอ\s*tae|รอเต้)", re.IGNORECASE
)


def _extract_decision_lines(text: str, source_label: str) -> list[dict]:
    """Pull bullet/numbered lines under a Decision-Queue-shaped heading."""
    lines = text.splitlines()
    items = []
    in_section = False
    section_heading_level = 0
    for line in lines:
        heading_match = re.match(r"^(#{1,6})\s+(.*)$", line)
        if heading_match:
            level = len(heading_match.group(1))
            title = heading_match.group(2)
            if _DECISION_HEADING_RE.search(title):
                in_section = True
                section_heading_level = level
                continue
            if in_section and level <= section_heading_level:
                in_section = False
            continue
        if in_section:
            stripped = line.strip()
            if not stripped:
                continue
            # accept markdown bullets/numbers ("- ", "1.") AND circled-number
            # style ("① ", "②") used in this repo's own HANDOFF.md
            m = re.match(r"^(?:[-*]|\d+[.)]|[①-⑳])\s*(.*)$", stripped)
            if m:
                items.append({"text": m.group(1).strip(), "source": source_label})
    return items


@st.cache_data(ttl=600)
def scan_decision_inbox(handoff_path: str) -> list[dict]:
    """Scan this repo's HANDOFF.md + every registry project's Code/Docs Path
    HANDOFF.md for pending decision-queue items. Read-only, cached 10 min."""
    items: list[dict] = []

    paths_to_scan: list[tuple[Path, str]] = []
    hp = Path(handoff_path)
    if hp.exists():
        paths_to_scan.append((hp, "agentic-os-dashboard"))

    for proj in parse_registry():
        for field in ("code", "docs"):
            raw = proj.get(field, "")
            if not raw:
                continue
            base = Path(raw).expanduser()
            if not base.exists():
                continue
            candidate = base / "HANDOFF.md" if base.is_dir() else base
            if candidate.exists() and candidate.is_file():
                paths_to_scan.append((candidate, proj["tag"]))

    seen_paths = set()
    for path, tag in paths_to_scan:
        key = str(path)
        if key in seen_paths:
            continue
        seen_paths.add(key)
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for item in _extract_decision_lines(text, tag):
            item["file"] = str(path)
            items.append(item)

    return items
