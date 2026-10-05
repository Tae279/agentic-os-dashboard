# Agentic OS Dashboard

A local visual cockpit for your Claude Code usage. Shows rate limits, daily activity, routine runs, and one-click buttons to launch your Claude Code skills.

Runs entirely on your machine. Reads data from your local `~/.claude/` folder. Nothing ships to the cloud.

---

## What you're getting

- Three **gauges** at the top — your 5-hour token window, weekly token window, and daily routine cap
- A **cumulative activity chart** showing token usage over time with a live pulse animation
- **MCP server status strip** — which MCP servers are connected
- **Skill buttons** — click to run any Claude Code skill (configurable)
- **Activity feed** — tail of what Claude has been doing today

Everything styled like a cockpit/terminal readout. Dark Claude-warm palette.

---

## Prerequisites

Before you touch the code, make sure you have:

1. **Python 3.10+** installed — [download here](https://www.python.org/downloads/). During install on Windows, **check the box that says "Add Python to PATH"**.
2. **Git** installed — [download here](https://git-scm.com/downloads).
3. **Claude Code CLI** installed and signed in — if you haven't, follow [the official install guide](https://docs.claude.com/claude-code). You need to have run Claude Code at least once so it generates session data.
4. **A terminal** you're comfortable opening:
   - Windows: PowerShell or Command Prompt
   - Mac: Terminal.app or iTerm
   - Linux: whatever shell you use

Verify everything works:

```bash
python --version      # should say 3.10 or higher
git --version         # any recent version
claude --version      # confirms Claude Code is installed
```

If any of those fail, fix that first.

---

## Step 1 — Clone the repo

Open your terminal and run:

```bash
git clone https://github.com/YOUR-USERNAME/agentic-os-dashboard.git
cd agentic-os-dashboard
```

(Replace `YOUR-USERNAME` with the actual GitHub URL you were given.)

---

## Step 2 — Install dependencies

Still inside the `agentic-os-dashboard` folder, run:

```bash
pip install -r requirements.txt
```

This installs Streamlit and the other Python libraries the dashboard needs. Takes about a minute.

**If you get permission errors on Mac/Linux**, try `pip install --user -r requirements.txt` instead.

---

## Step 3 — Create your `config.py`

The repo ships a template called `config.example.py`. Your personal config lives in `config.py`, which is gitignored so your paths and skills stay on your machine.

Copy the template:

```bash
# Windows PowerShell / CMD
copy config.example.py config.py

# Mac / Linux
cp config.example.py config.py
```

Now open `config.py` in any text editor (VS Code, Notepad, TextEdit, whatever) and edit these fields at the top:

- **`VAULT_PATH`** — the folder where Claude Code should run. For most people, this is their Obsidian vault or a project folder. Example on Mac: `Path("/Users/yourname/Documents/my-vault")`.
- **`VAULT_NAME`** — display name shown in the dashboard header. Just a label.
- **`CLAUDE_CLI`** — the full path to the `claude` executable. Find it by running `where claude` (Windows) or `which claude` (Mac/Linux) in your terminal.
- **`CLAUDE_PLAN`** — set to `"pro"`, `"max"`, or `"team"` depending on your Anthropic plan. Controls the daily routine cap on the third gauge.

The `SKILLS` list at the bottom defines the buttons. See the next section for how to customize it.

**Don't overthink this step.** If a path looks wrong, the dashboard will show an empty state instead of crashing. You can iterate.

### Adding your own skills

The `SKILLS` list in `config.py` is where the dashboard buttons come from. Each entry is a Python dict with these fields:

```python
{
    "label": "Morning Brief",                    # button text
    "prompt_template": (                         # what gets sent to claude -p "<here>"
        "Act autonomously. Do not ask for confirmation. "
        "Do not use AskUserQuestion. Run the /morning skill"
    ),
    "description": "AI news briefing",           # subtitle under the label
    "category": "daily",                         # "daily" or "content"
}
```

For skills that need input (a research topic, a URL, a video description), add `{input}` inside `prompt_template` and include `input_placeholder`:

```python
{
    "label": "Deep Research",
    "prompt_template": (
        "Act autonomously. Do not ask for confirmation. "
        "Do not use AskUserQuestion. Run /deep-research on: {input}"
    ),
    "description": "Multi-source research",
    "category": "content",
    "input_placeholder": "topic to research",
}
```

**Tips:**
- Start every `prompt_template` with `"Act autonomously. Do not ask for confirmation. Do not use AskUserQuestion."` — stops Claude from blocking the run mid-way to ask questions.
- `category: "daily"` groups the button with routines (counted against your daily routine cap). `category: "content"` groups with content/creative buttons.
- You can add as many or as few as you want. Delete the examples you don't use.
- Not sure what to add? See `PROMPTS.md` for prompts you can give Claude Code to build your `SKILLS` list for you.

---

## Step 4 — Run it

```bash
streamlit run app.py
```

Streamlit opens a browser tab at `http://localhost:8501`. If it doesn't open automatically, paste that URL into your browser.

**First-run expectations:**

- If you've been using Claude Code for a while, gauges and chart populate immediately.
- If you're brand new to Claude Code, you'll see empty gauges. Run a Claude Code session or two, then refresh the dashboard. Data appears once your `~/.claude/usage-data/session-meta/` folder has files.

**To stop the dashboard:** go back to the terminal and press `Ctrl+C`.

---

## Project Radar (`/radar`)

Project Radar is the Next.js Command Center view for tracking project status, decisions, timeline events, and approved agent actions from one page.

Run the FastAPI backend and production web app together:

```bash
./run.sh web
```

Then open `http://localhost:3000/radar`. Both the backend (`127.0.0.1:8787`) and the web app (`-H 127.0.0.1`) listen on this machine only.

Radar data lives in `dashboard-data/radar.json`. This file is gitignored because it contains machine-local project paths and prompts. To add a project, append an object to `projects` with the existing fields (`id`, `code`, `name`, status, progress, next step, facts, rules, links, and optional actions/apps/checklist). To add a runnable action, add an item to that project's `actions` array:

```json
{
  "id": "prepare-release-plan",
  "label": "เตรียมแผน release",
  "kind": "plan",
  "cwd": "/absolute/path/to/allowed/project",
  "prompt": "Read the project handoff and prepare the approved release plan."
}
```

The action `cwd` must resolve inside the backend allowlist. JSON actions provide Claude prompts only; the UI does not execute shell commands stored in Radar data.

Runs started from Radar (and every `POST /api/run`) are locked to **Claude Sonnet 5** (`RUN_MODEL` in `server.py`) so headless work never spends Opus/Fable quota. The backend also rejects browser POSTs that do not come from the dashboard origin or are not `application/json`, so a random web page cannot start a run on your machine.

To share a read-only snapshot of Radar (no action buttons), run `node scripts/export-radar-artifact.mjs` — it writes a single self-contained HTML file to `~/Documents/DX/artifacts/<date>-dx-project-radar.html` from `radar.json`.

---

## Step 5 — Adapt it to you (with Claude Code)

This is the fun part. The dashboard was built with Claude Code and it's built to be modified with Claude Code.

Open a terminal in the `agentic-os-dashboard` folder and run `claude`. Then try prompts like:

> "Look at this dashboard. I want to swap the terracotta accent for a cool blue palette. Show me the changes before applying."

> "Add a fourth gauge at the top that tracks my GitHub commits today by reading `git log`."

> "Rename the skill buttons and replace them with my own Claude Code skills. Here are the ones I want: [list]."

> "Change the header text from 'AGENTIC OS' to my brand name. Update the favicon too."

See `PROMPTS.md` for a longer list of tested starter prompts.

---

## Making it "always on" (optional)

Running `streamlit run app.py` in a terminal every day is annoying. Here are four ways to upgrade, from easiest to most polished.

### Option A — Double-click launcher (simplest)

A desktop shortcut that starts the server and opens the browser. One click, no terminal.

**Windows:** create `start-dashboard.bat` with this content:

```bat
@echo off
cd /d C:\path\to\agentic-os-dashboard
start "" http://localhost:8501
streamlit run app.py
```

Right-click → "Send to → Desktop (create shortcut)".

**Mac:** create `start-dashboard.command` with this content:

```bash
#!/bin/bash
cd /path/to/agentic-os-dashboard
open http://localhost:8501
streamlit run app.py
```

Then run `chmod +x start-dashboard.command`. Double-click to launch.

### Option B — Autostart on login (always available at localhost:8501)

Dashboard runs in the background 24/7. You bookmark `http://localhost:8501` and open it anytime.

Easiest path: ask Claude Code to set this up for you.

> "Set up this Streamlit app to auto-launch on Windows login using Task Scheduler. Run in the background with no visible terminal. Open at localhost:8501."

Mac version:

> "Set up this Streamlit app to auto-launch on macOS login using launchd. Log output to a file. I want to visit localhost:8501 anytime and have it load."

Claude Code will generate the config file, tell you where to put it, and walk through the install.

### Option C — System tray icon

Dashboard lives as a tray/menubar icon. Click → opens dashboard in browser. Quit from the tray.

> "Wrap this Streamlit app in a Python system tray app using `pystray`. Icon in the tray starts/stops the server and opens the browser."

### Option D — Native desktop app (most polished)

Ship as a real app with its own window. No browser tab. Users don't know Streamlit exists under the hood.

Options: Tauri, Electron, or Pake. Heavier build.

> "Wrap this Streamlit app in a Tauri desktop shell. On launch, start the Streamlit server in the background and open a native window pointing at localhost:8501."

This is the path if you're productizing for others, not just yourself.

---

## Troubleshooting

**"streamlit: command not found"**
Python installed but scripts folder not on PATH. On Windows, reinstall Python with "Add to PATH" checked. On Mac: `export PATH="$HOME/.local/bin:$PATH"` in your `~/.zshrc`.

**Dashboard loads but gauges are empty**
Your `~/.claude/usage-data/session-meta/` folder has no data yet. Run a Claude Code session. Refresh.

**"Permission denied" when running skills**
`PERMISSION_MODE` in `config.py` is set to `bypassPermissions`. If that's too risky for you, change to `"default"` — Claude will prompt per-tool.

**Dashboard shows my paths not yours**
You're running the original `config.py`. Go back to Step 3 and edit the paths.

**Port 8501 already in use**
Another Streamlit app is running. Kill it, or start this one on a different port: `streamlit run app.py --server.port 8502`.

---

## What happens when you change the code

Streamlit auto-reloads when you save a `.py` file. Browser tab updates live. No restart needed.

**Exception:** `.streamlit/config.toml` changes require a full restart (Ctrl+C, then `streamlit run app.py` again).

---

## File map

- `app.py` — the whole dashboard (one big Streamlit file)
- `config.example.py` — template config. Copy to `config.py` and edit.
- `config.py` — **gitignored**. Your personal paths, plan, and skills. Never pushed to GitHub.
- `requirements.txt` — Python dependencies
- `.streamlit/config.toml` — Streamlit theme + server settings
- `assets/` — images, robot mascot sprites
- `PROMPTS.md` — starter prompts for customizing with Claude Code

---

## License

MIT. Do whatever you want with it.

## Doctor — ตรวจระบบ + เตือน login หมดอายุ

`health.py` (stdlib ล้วน) ตรวจ API :8787, หน้าเว็บ :3000, Claude login, LaunchAgents 2 ตัว, ดิสก์ และเตือนถ้าหน้าเว็บเปิดให้เครื่องอื่นเข้าได้
- ดูผล: หน้า `/health` + แถบแดงบนสุดทุกหน้าเมื่อมีจุดที่พัง · เตือนเข้า LINE (`~/.config/dx/line-notify.json`) ครั้งเดียวต่อเหตุการณ์ + เตือนซ้ำทุก 6 ชม. + แจ้งเมื่อกลับมาปกติ
- เซิร์ฟเวอร์รันลูปตรวจทุก 5 นาที (`server.py`) · ทดสอบ login จริง (haiku 1 ครั้ง) ทุก 6 ชม.
- login ไม่มีวันหมดอายุให้อ่านตรงๆ (`claude auth status` ไม่บอก และเราไม่แตะไฟล์ credentials) จึงจับจาก: probe ล้ม / งานจริงล้มด้วย OAuth error / `loggedIn:false`
- ซ่อมเอง: `python health.py --heal` เปิด API/web ที่ตายใหม่แบบเดียวกับ `เปิด Dashboard.command` (สูงสุด 3 ครั้ง/ชม./บริการ) — ต่อเข้า LaunchAgent เดิม (`queue-worker`, ทุก 60 วิ) ด้วยบรรทัดเดียวใน `queue_worker.py` เพื่อให้ทำงานแม้ API ตาย
- ปิดแต่ละส่วนด้วย env: `DOCTOR_AUTOHEAL=0`, `DOCTOR_NOTIFY=0` · เทสต์: `.venv/bin/python -m unittest tests.test_health`
