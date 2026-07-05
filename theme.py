"""Shared cockpit theme — imported by app.py (Command) and pages/portfolio.py.
Single source of design tokens; edit :root here, both pages follow.
"""

import streamlit as st


PREMIUM_CSS = r"""
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600&family=Space+Grotesk:wght@500;600;700&family=Prompt:wght@400;500;600&display=swap');

:root {
    --bg:         #070b14;
    --bg-elev:    #0b1120;
    --bg-card:    #0f1726;
    --bg-card-hi: #16213a;
    --ring-soft:  rgba(148, 163, 184, 0.18);
    --ring-mid:   rgba(148, 163, 184, 0.30);
    --ring-hard:  #94a3b8;
    --fg:         #e6edf7;
    --fg-dim:     #94a3b8;
    --fg-mute:    #5b6b82;
    --accent:     #3d7bff;
    --accent-deep: #024ada;   /* DX brand anchor — solid fills / gradients */
    --accent-soft: rgba(61, 123, 255, 0.12);
    --warn:       #e0b35c;
    --danger:     #e5484d;
    --good:       #46c07a;

    /* legacy aliases (keep existing class selectors resolving) */
    --text:          var(--fg);
    --text-dim:      var(--fg-dim);
    --text-mute:     var(--fg-mute);
    --border:        var(--ring-soft);
    --border-strong: var(--ring-mid);
    --ring-warm:     var(--ring-soft);
    --ring-deep:     var(--ring-mid);
    --accent-glow:   rgba(61, 123, 255, 0.32);
    --coral:         #5c8dff;
    --amber:         var(--warn);
}

html, body, [class*="css"] {
    /* Mono leads (cockpit identity); Prompt catches Thai glyphs */
    font-family: 'JetBrains Mono', 'Prompt', 'SF Mono', Menlo, Consolas, monospace;
    color: var(--fg);
}

.stApp { background: var(--bg); }
body   { background: var(--bg); }

h1, h2, h3, h4, h5, h6 {
    font-family: 'JetBrains Mono', monospace;
    font-weight: 500;
    letter-spacing: 0.02em;
    color: var(--fg);
    text-transform: uppercase;
}

.hero-title {
    font-family: 'Space Grotesk', 'JetBrains Mono', monospace !important;
    font-size: 2.8rem !important;
    font-weight: 700;
    letter-spacing: -0.01em;
    line-height: 1;
    color: var(--fg);
    margin: 0 0 0.5rem 0;
    text-transform: uppercase;
    display: flex;
    align-items: center;
    gap: 0.8rem;
}
.hero-title em {
    font-style: normal;
    color: var(--accent);
    font-weight: 600;
    margin-left: 0;
}
.hero-title .hero-word { display: inline-block; }

.title-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 1.2rem;
    flex-wrap: wrap;
    margin-bottom: 0.3rem;
}
.title-crumb {
    margin: 0;
    text-align: right;
    max-width: 60%;
}

/* Sprite-sheet mascot: 7 frames × 12x32, scaled 2× → 24x64 rendered */
.hero-title .mascot {
    display: inline-block;
    width: 24px;
    height: 64px;
    background-image: var(--idle);
    background-repeat: no-repeat;
    background-position: 0 0;
    background-size: 168px 64px;
    image-rendering: pixelated;
    image-rendering: crisp-edges;
    -ms-interpolation-mode: nearest-neighbor;
    vertical-align: middle;
    margin-right: 0.2em;
    margin-top: 0;
    filter: none;
    animation: robot-idle 0.85s steps(7) infinite;
    will-change: background-position, transform;
    transition: filter 0.2s ease;
    transform: translateY(-14px);
    /* sprite art is terracotta; shift to DX blue without re-drawing pixels */
    filter: hue-rotate(200deg) saturate(1.15);
}
@keyframes robot-idle {
    from { background-position:    0  0; }
    to   { background-position: -168px 0; }
}
.hero-title .mascot:hover {
    background-image: var(--run);
    animation: robot-run 0.55s steps(7) infinite;
    filter: hue-rotate(200deg) saturate(1.15);
    transform: translateY(0);
}
@keyframes robot-run {
    from { background-position:    0  0; }
    to   { background-position: -168px 0; }
}

.caption-mono {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.62rem;
    color: var(--fg-mute);
    letter-spacing: 0.08em;
    text-transform: uppercase;
}

[data-testid="stStatusWidget"], [data-testid="stToolbar"],
#MainMenu, footer, [data-testid="stDecoration"],
[data-testid="stHeader"], header[data-testid="stHeader"] {
    display: none !important;
    height: 0 !important;
}

.block-container {
    padding-top: 1rem !important;
    padding-bottom: 1rem !important;
    max-width: 1480px;
}

.cat-label, .chip-cat, .cpt-cat {
    color: var(--accent);
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.62rem;
    letter-spacing: 0.2em;
    font-weight: 500;
    text-transform: uppercase;
    margin: 0.8rem 0 0.5rem 0;
    padding: 0.35rem 0 0.35rem 0;
    border-bottom: 1px solid var(--ring-soft);
    display: flex;
    align-items: center;
    gap: 0.5rem;
}
.cat-label::before, .cat-label::after,
.cpt-cat::before, .cpt-cat::after { content: none; }
.chip-cat, .cpt-cat.chip-cat {
    margin: 0.8rem 0 0.4rem 0;
    font-size: 0.58rem;
    letter-spacing: 0.22em;
}
.brand-ico {
    width: 12px;
    height: 12px;
    vertical-align: middle;
    margin-right: 0.35rem;
    display: inline-block;
    flex-shrink: 0;
}
.header-link-btn,
.header-link-btn:link,
.header-link-btn:visited {
    display: inline-flex;
    align-items: center;
    gap: 0.3rem;
    background: var(--bg-card);
    color: var(--fg-dim) !important;
    border: none;
    border-radius: 2px;
    padding: 0.4rem 0.7rem;
    font-family: 'JetBrains Mono', monospace;
    font-weight: 500;
    font-size: 0.66rem;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    text-align: left;
    text-decoration: none !important;
    cursor: pointer;
    transition: box-shadow 0.12s, color 0.12s;
    box-shadow: 0 0 0 1px var(--ring-soft);
}
.header-link-btn:hover,
.header-link-btn:focus,
.header-link-btn:active {
    color: var(--accent) !important;
    text-decoration: none !important;
    outline: none;
    box-shadow: 0 0 0 1px var(--accent);
}
.header-link-btn * { text-decoration: none !important; }

/* Chip buttons (compact) */
[data-testid="stButton"] > button[kind="secondary"] {
    padding: 0.45rem 0.6rem;
    font-size: 0.72rem;
}
.stTextArea textarea {
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.82rem !important;
    background: #0f1726 !important;
    color: var(--fg) !important;
    border: none !important;
    border-radius: 3px !important;
    line-height: 1.6 !important;
    padding: 0.75rem 0.9rem !important;
    box-shadow:
        0 0 0 1px var(--ring-mid),
        inset 0 1px 0 rgba(255, 255, 255, 0.03),
        0 6px 20px rgba(0, 0, 0, 0.35) !important;
    transition: box-shadow 0.15s ease !important;
}
.stTextArea textarea:hover {
    box-shadow:
        0 0 0 1px rgba(61, 123, 255, 0.45),
        inset 0 1px 0 rgba(255, 255, 255, 0.04),
        0 6px 22px rgba(0, 0, 0, 0.4) !important;
}
.stTextArea textarea:focus {
    background: #121a2e !important;
    box-shadow:
        0 0 0 1px var(--accent),
        0 0 0 4px rgba(61, 123, 255, 0.12),
        inset 0 1px 0 rgba(255, 255, 255, 0.04),
        0 8px 28px rgba(0, 0, 0, 0.45) !important;
    outline: none !important;
}

.stButton > button, .stFormSubmitButton > button {
    background: var(--bg-card);
    color: var(--fg-dim);
    border: none;
    border-radius: 2px;
    padding: 0.5rem 0.7rem;
    font-family: 'JetBrains Mono', monospace;
    font-weight: 500;
    font-size: 0.72rem;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    transition: box-shadow 0.12s, color 0.12s;
    text-align: left;
    height: auto;
    white-space: normal;
    box-shadow: 0 0 0 1px var(--ring-soft);
}
.stButton > button:hover, .stFormSubmitButton > button:hover {
    color: var(--accent);
    box-shadow: 0 0 0 1px var(--accent);
}

/* RUN → is the single luminous focal control (Voltura language).
   Scoped to the FIRST form column so CLEAR (second column) stays quiet. */
.stFormSubmitButton > button[kind="primaryFormSubmit"] {
    background: linear-gradient(180deg, #2261f0, var(--accent-deep)) !important;
    color: #fff !important;
    text-align: center !important;
    font-weight: 600 !important;
    letter-spacing: 0.12em !important;
    box-shadow: 0 0 0 1px rgba(61, 123, 255, 0.45), 0 6px 22px rgba(2, 74, 218, 0.35) !important;
}
.stFormSubmitButton > button[kind="primaryFormSubmit"]:hover {
    background: linear-gradient(180deg, #3d7bff, #1254e8) !important;
    color: #fff !important;
    box-shadow: 0 0 0 1px rgba(120, 163, 255, 0.7), 0 8px 26px rgba(2, 74, 218, 0.5) !important;
}
.stButton > button:active, .stFormSubmitButton > button:active {
    background: rgba(61, 123, 255, 0.1) !important;
    color: var(--accent) !important;
    box-shadow: 0 0 0 1px var(--accent) !important;
}
.stButton > button:disabled, .stFormSubmitButton > button:disabled {
    opacity: 0.35;
    color: var(--fg-mute);
    cursor: not-allowed;
}

.stTextInput > div > div > input {
    background: var(--bg-elev);
    color: var(--fg);
    border: none;
    border-radius: 3px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.8rem;
    padding: 0.5rem 0.75rem;
    box-shadow: 0 0 0 1px var(--ring-soft);
}
.stTextInput > div > div > input:focus {
    box-shadow: 0 0 0 1px var(--accent);
    outline: none;
}
.stTextInput > div > div > input::placeholder { color: var(--fg-mute); }

pre, code, [data-testid="stCodeBlock"] {
    font-family: 'JetBrains Mono', 'SF Mono', Menlo, Consolas, monospace !important;
    font-size: 0.76rem !important;
    background: var(--bg-elev) !important;
    border: none !important;
    border-radius: 3px !important;
    color: var(--fg-dim) !important;
    line-height: 1.55 !important;
    box-shadow: 0 0 0 1px var(--ring-soft) !important;
}

hr {
    border: none !important;
    border-top: 1px solid var(--ring-soft) !important;
    margin: 0.9rem 0 !important;
}
hr.chapter {
    border: none !important;
    border-top: 1px solid var(--ring-soft) !important;
    height: 0 !important;
    background: none !important;
    margin: 1rem 0 !important;
    position: relative;
    overflow: visible;
}
hr.chapter::after { content: none; }

.hero-card {
    background: var(--bg-card);
    border: none;
    border-radius: 3px;
    padding: 0.75rem 0.9rem;
    box-shadow: 0 0 0 1px var(--ring-soft);
    min-height: 80px;
    position: relative;
    overflow: hidden;
}
.hero-card::before { content: none; }
.hero-card.running {
    box-shadow: 0 0 0 1px var(--accent);
    animation: hero-pulse 2.4s ease-in-out infinite;
}
.hero-card.error {
    background: rgba(229, 72, 77, 0.05);
    box-shadow: 0 0 0 1px rgba(229, 72, 77, 0.55);
}
.hero-card.error .hero-label { color: var(--danger); }
.hero-card.error .hero-headline em { color: var(--danger); }
.error-detail {
    background: var(--bg-elev);
    border: none;
    border-radius: 2px;
    padding: 0.55rem 0.75rem;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.72rem;
    color: #f0b6ba;
    box-shadow: 0 0 0 1px rgba(229, 72, 77, 0.35);
    white-space: pre-wrap;
    word-break: break-word;
    max-height: 200px;
    overflow-y: auto;
    margin: 0.4rem 0;
    line-height: 1.5;
}
.error-hint {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.62rem;
    color: var(--fg-mute);
    letter-spacing: 0.08em;
    text-transform: uppercase;
}
.skill-desc {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.62rem;
    color: var(--fg-mute);
    margin: -0.1rem 0 0.4rem 0.1rem;
    letter-spacing: 0.02em;
    line-height: 1.35;
    text-transform: uppercase;
}
@keyframes hero-pulse {
    0%, 100% { box-shadow: 0 0 0 1px var(--accent); }
    50%      { box-shadow: 0 0 0 1px var(--accent), 0 0 18px rgba(61, 123, 255, 0.28); }
}

.hero-label {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.62rem;
    text-transform: uppercase;
    letter-spacing: 0.15em;
    color: var(--fg-mute);
    margin-bottom: 0.3rem;
}
.hero-headline {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.95rem;
    font-weight: 500;
    color: var(--fg);
    letter-spacing: 0.04em;
    text-transform: uppercase;
    line-height: 1.2;
    margin: 0 0 0.3rem 0;
}
.hero-headline em { font-style: normal; color: var(--accent); }

.cursor-blink {
    display: inline-block;
    color: var(--accent);
    font-family: 'JetBrains Mono', monospace;
    font-weight: 400;
    margin-left: 0.35rem;
    line-height: 1;
    animation: cursor-blink 1.05s steps(2) infinite;
}
@keyframes cursor-blink {
    0%, 49%   { opacity: 1; }
    50%, 100% { opacity: 0; }
}

@keyframes pulse {
    0%, 100% { opacity: 0.4; }
    50%      { opacity: 1.0; }
}
.pulse-dot {
    width: 8px; height: 8px;
    background: var(--accent);
    border-radius: 50%;
    display: inline-block;
    margin-right: 0.5rem;
    vertical-align: middle;
    animation: pulse 1.1s ease-in-out infinite;
}
.pulse-dot.idle {
    background: var(--warn);
    animation: idle-pulse 2.8s ease-in-out infinite;
}
@keyframes idle-pulse {
    0%, 100% { opacity: 0.5; }
    50%      { opacity: 1; }
}
.pulse-dot.small { width: 6px; height: 6px; }

.status-chip {
    display: inline-flex;
    align-items: center;
    gap: 0.35rem;
    padding: 0.35rem 0.7rem;
    background: transparent;
    border: none;
    border-radius: 2px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.62rem;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: var(--fg-dim);
    box-shadow: 0 0 0 1px var(--ring-soft);
    float: right;
    margin-top: 0.55rem;
}
.status-chip.running {
    color: var(--accent);
    background: rgba(61, 123, 255, 0.06);
    box-shadow: 0 0 0 1px var(--accent);
    animation: chip-pulse 2.4s ease-in-out infinite;
}
@keyframes chip-pulse {
    0%, 100% { box-shadow: 0 0 0 1px var(--accent); }
    50%      { box-shadow: 0 0 0 1px var(--accent), 0 0 10px rgba(61, 123, 255, 0.3); }
}

.activity-feed {
    background: var(--bg-card);
    border: none;
    border-radius: 3px;
    padding: 0.6rem 0.8rem;
    box-shadow: 0 0 0 1px var(--ring-soft);
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.74rem;
    color: var(--fg-dim);
    max-height: 500px;
    overflow-y: auto;
    line-height: 1.6;
}
.activity-feed h1, .activity-feed h2, .activity-feed h3 {
    font-family: 'JetBrains Mono', monospace;
    color: var(--fg);
    text-transform: uppercase;
    letter-spacing: 0.04em;
}
.activity-feed p { margin: 0.2rem 0 !important; }
.activity-feed ul { padding-left: 1rem; }

.obsidian-link, .meta-link {
    display: inline-block;
    color: var(--accent);
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.66rem;
    text-decoration: none;
    padding: 0.25rem 0.55rem;
    margin: 0.2rem 0.3rem 0.1rem 0;
    border: none;
    border-radius: 2px;
    background: rgba(61, 123, 255, 0.05);
    box-shadow: 0 0 0 1px rgba(61, 123, 255, 0.3);
    letter-spacing: 0.06em;
    text-transform: uppercase;
    transition: box-shadow 0.12s, background 0.12s;
}
.obsidian-link:hover, .meta-link:hover {
    background: rgba(61, 123, 255, 0.1);
    box-shadow: 0 0 0 1px var(--accent);
}
.meta-link {
    color: var(--fg-dim);
    background: transparent;
    box-shadow: 0 0 0 1px var(--ring-soft);
}

[data-testid="stForm"] {
    background: transparent !important;
    border: none !important;
    padding: 0 !important;
}

::-webkit-scrollbar { width: 8px; height: 8px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: rgba(148, 163, 184, 0.12); border-radius: 0; }
::-webkit-scrollbar-thumb:hover { background: rgba(148, 163, 184, 0.22); }

.stream-output {
    background: var(--bg-elev);
    border: none;
    border-radius: 3px;
    padding: 0.7rem 0.9rem;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.72rem;
    color: var(--fg-dim);
    box-shadow: 0 0 0 1px var(--ring-soft);
    max-height: 340px;
    overflow-y: auto;
    white-space: pre-wrap;
    word-break: break-word;
    margin-top: 0.7rem;
    line-height: 1.6;
    letter-spacing: 0.005em;
}

/* Body-copy treatment for rendered markdown output (cockpit mono) */
.output-body + [data-testid="stMarkdownContainer"] p,
.output-body ~ [data-testid="stMarkdownContainer"] p {
    line-height: 1.55;
    font-size: 0.82rem;
    color: var(--fg);
    font-family: 'JetBrains Mono', monospace;
}
.output-body + [data-testid="stMarkdownContainer"] h1,
.output-body + [data-testid="stMarkdownContainer"] h2,
.output-body + [data-testid="stMarkdownContainer"] h3 {
    font-family: 'JetBrains Mono', monospace;
    letter-spacing: 0.04em;
    text-transform: uppercase;
    color: var(--fg-dim);
    margin-top: 1rem;
    margin-bottom: 0.4rem;
}
.output-body + [data-testid="stMarkdownContainer"] li {
    line-height: 1.5;
    margin-bottom: 0.25rem;
    font-family: 'JetBrains Mono', monospace;
}
.output-body + [data-testid="stMarkdownContainer"] blockquote {
    border-left: 2px solid var(--accent);
    padding-left: 0.8rem;
    font-family: 'JetBrains Mono', monospace;
    font-style: normal;
    color: var(--fg-dim);
    margin: 0.7rem 0;
}

.phase-line {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.68rem;
    color: var(--fg-dim);
    margin-top: 0.4rem;
    letter-spacing: 0.04em;
}
.phase-line .phase-name { color: var(--accent); }

.meta-row {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.66rem;
    color: var(--fg-mute);
    margin-top: 0.5rem;
    letter-spacing: 0.06em;
    text-transform: uppercase;
}
.meta-row .meta-val { color: var(--fg-dim); }

/* Recent runs card wrapper */
.runs-card {
    background: var(--bg-card);
    border: none;
    border-radius: 3px;
    padding: 0.55rem 0.75rem;
    box-shadow: 0 0 0 1px var(--ring-soft);
}
.runs-card .cat-label {
    margin: 0 0 0.35rem 0;
    padding: 0 0 0.35rem 0;
    border-bottom: 1px solid var(--ring-soft);
}
.run-list {
    display: flex;
    flex-direction: column;
    padding: 0;
    margin: 0;
}
.run-row {
    display: grid;
    grid-template-columns: 3.2rem 1fr auto;
    align-items: center;
    column-gap: 0.6rem;
    padding: 0.4rem 0.1rem;
    border-top: 1px solid var(--ring-soft);
    background: transparent;
}
.run-row:first-child { border-top: none; }
.run-row .run-time {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.62rem;
    color: var(--fg-mute);
    letter-spacing: 0.04em;
}
.run-row .run-label {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.76rem;
    font-weight: 500;
    letter-spacing: 0.02em;
    text-transform: uppercase;
    color: var(--fg);
    line-height: 1.25;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}
.run-row:hover .run-label { color: var(--accent); }
.run-row a {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.6rem;
    color: var(--fg-mute);
    text-decoration: none;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    transition: color 0.12s;
}
.run-row a:hover { color: var(--accent); }

.approval-card {
    background: var(--bg-card);
    border: none;
    border-radius: 3px;
    padding: 0.6rem 0.8rem;
    margin-bottom: 0.5rem;
    box-shadow: 0 0 0 1px var(--ring-soft);
}
.approval-card h4 {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.8rem;
    margin: 0 0 0.3rem 0;
    letter-spacing: 0.04em;
    text-transform: uppercase;
}
.approval-card .approval-meta {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.64rem;
    color: var(--fg-mute);
    letter-spacing: 0.06em;
    margin-bottom: 0.4rem;
}

/* Danger button variant (cancel) */
.cancel-btn .stButton > button {
    background: rgba(229, 72, 77, 0.06) !important;
    box-shadow: 0 0 0 1px rgba(229, 72, 77, 0.35) !important;
    color: var(--danger) !important;
}
.cancel-btn .stButton > button:hover {
    background: rgba(229, 72, 77, 0.14) !important;
    box-shadow: 0 0 0 1px var(--danger) !important;
    color: #fff !important;
}

/* Quick-nav pill bar */
.quicknav {
    display: flex;
    gap: 0.35rem;
    flex-wrap: wrap;
    align-items: center;
    margin: 0 0 0.7rem 0;
}
.quicknav a {
    display: inline-flex;
    align-items: center;
    gap: 0.35rem;
    padding: 0.35rem 0.7rem;
    background: transparent;
    border: none;
    border-radius: 2px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.66rem;
    font-weight: 500;
    color: var(--fg-dim);
    text-decoration: none;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    box-shadow: 0 0 0 1px var(--ring-soft);
    transition: box-shadow 0.12s, color 0.12s;
}
.quicknav a:hover {
    color: var(--accent);
    background: transparent;
    box-shadow: 0 0 0 1px var(--accent);
}
.quicknav a em, .quicknav .qn-icon {
    font-family: 'JetBrains Mono', monospace;
    font-style: normal;
    font-weight: 500;
    color: var(--accent);
    font-size: 0.7rem;
    letter-spacing: 0.06em;
}

/* Claude code pill — terracotta-tinted + traveling-dot border pulse */
.quicknav a.qn-claude {
    position: relative;
    overflow: visible;
    padding: 0.4rem 0.85rem;
    color: var(--fg);
    box-shadow: 0 0 0 1px var(--accent), 0 0 0 3px rgba(61, 123, 255, 0.08);
    background: rgba(61, 123, 255, 0.04);
}
.quicknav a.qn-claude:hover {
    background: rgba(61, 123, 255, 0.09);
    box-shadow: 0 0 0 1px var(--accent), 0 0 12px rgba(61, 123, 255, 0.35);
}
.quicknav a.qn-claude .qn-arrow {
    color: var(--accent);
    margin-left: 0.15rem;
    font-size: 0.66rem;
    opacity: 0.85;
}
.quicknav a.qn-claude > span { position: relative; z-index: 1; }
.qn-pulse-svg {
    position: absolute;
    inset: 0;
    width: 100%;
    height: 100%;
    pointer-events: none;
    overflow: visible;
    z-index: 0;
}

/* Status chip when embedded in quicknav — push to right edge */
.quicknav .qn-status {
    float: none !important;
    margin: 0 0 0 auto !important;
}

/* Metric tiles */
.metric-tile {
    background: var(--bg-card);
    border: none;
    border-radius: 3px;
    padding: 0.55rem 0.75rem;
    min-height: 64px;
    box-shadow: 0 0 0 1px var(--ring-soft);
}
.metric-tile::before { content: none; }
.metric-label {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.58rem;
    text-transform: uppercase;
    letter-spacing: 0.15em;
    color: var(--fg-mute);
    margin-bottom: 0.3rem;
}
.metric-value {
    font-family: 'JetBrains Mono', monospace;
    font-size: 1.1rem;
    font-weight: 500;
    color: var(--fg);
    letter-spacing: 0.02em;
    line-height: 1.1;
}
.metric-value .unit {
    font-size: 0.72rem;
    color: var(--fg-mute);
    margin-left: 0.2rem;
}
.metric-value.highlight { color: var(--accent); }

/* MCP health strip */
.mcp-strip {
    display: flex;
    gap: 0.9rem;
    align-items: center;
    flex-wrap: wrap;
    margin: 0.4rem 0 0.8rem 0;
    padding: 0.45rem 0.75rem;
    background: var(--bg-card);
    border: none;
    border-radius: 3px;
    box-shadow: 0 0 0 1px var(--ring-soft);
}
.mcp-label {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.58rem;
    text-transform: uppercase;
    letter-spacing: 0.22em;
    color: var(--accent);
    margin-right: 0.3rem;
    padding-right: 0.75rem;
    border-right: 1px solid var(--ring-soft);
}
.mcp-item {
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.66rem;
    font-weight: 500;
    color: var(--fg-dim);
    letter-spacing: 0.04em;
    text-transform: uppercase;
    transition: color 0.12s;
}
.mcp-item:hover { color: var(--accent); }
.mcp-dot {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: var(--fg-mute);
    flex-shrink: 0;
}
.mcp-dot.ready, .mcp-dot.connected {
    background: var(--accent);
    box-shadow: 0 0 4px rgba(61, 123, 255, 0.55);
}
.mcp-dot.needs_auth, .mcp-dot.needs-auth { background: var(--warn); }
.mcp-dot.failed, .mcp-dot.error { background: var(--danger); }
.mcp-dot.connecting {
    background: var(--fg-dim);
    animation: mcp-pulse 1.4s ease-in-out infinite;
}
@keyframes mcp-pulse {
    0%, 100% { opacity: 0.5; }
    50%      { opacity: 1; }
}

/* Chart container */
.chart-card, .cpt-chart-card {
    background: var(--bg-card);
    border: none;
    border-radius: 3px;
    padding: 0.5rem 0.7rem 0.3rem;
    margin-bottom: 0.7rem;
    box-shadow: 0 0 0 1px var(--ring-soft);
}
/* Parchment variant — stripped in cockpit (kept as no-op for compatibility) */
.chart-card.parchment {
    background: var(--bg-card);
    backdrop-filter: none;
    -webkit-backdrop-filter: none;
    padding: 0.5rem 0.7rem 0.3rem;
    border-radius: 3px;
    box-shadow: 0 0 0 1px var(--ring-soft);
    margin: 0.3rem 0 0.7rem 0;
}
.chart-card.parchment .chart-title,
.chart-card.parchment .cpt-chart-title { color: var(--fg-dim); }
.chart-card.parchment .chart-title span,
.chart-card.parchment .cpt-chart-title span { color: var(--fg-mute) !important; }
.chart-card.mini-chart, .cpt-chart-card.mini-chart {
    padding: 0.4rem 0.6rem 0.25rem;
    border-radius: 3px;
    margin-top: 0.6rem;
}
.chart-title, .cpt-chart-title {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.66rem;
    font-weight: 500;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: var(--fg-dim);
    margin-bottom: 0.3rem;
    display: flex;
    justify-content: space-between;
    align-items: baseline;
}
.chart-title em, .cpt-chart-title em {
    font-family: 'JetBrains Mono', monospace;
    font-style: normal;
    font-weight: 500;
    color: var(--accent);
    letter-spacing: 0.08em;
    text-transform: uppercase;
    font-size: 0.66rem;
}
.chart-title span, .cpt-chart-title span {
    color: var(--fg-mute);
    font-size: 0.6rem;
    letter-spacing: 0.06em;
}

/* Inline SVG cumulative activity chart (replaces plotly) */
.activity-chart-wrap {
    position: relative;
    margin: 0.2rem 0 0.1rem;
    isolation: isolate;
}
.activity-chart-wrap::before {
    content: "";
    position: absolute;
    inset: 0;
    pointer-events: none;
    z-index: 0;
    background-image:
        radial-gradient(ellipse 78% 62% at 50% 55%, rgba(61, 123, 255, 0.055) 0%, rgba(61, 123, 255, 0) 72%),
        linear-gradient(180deg, rgba(0, 0, 0, 0) 55%, rgba(0, 0, 0, 0.18) 100%),
        repeating-linear-gradient(90deg, transparent 0 59px, rgba(148, 163, 184, 0.05) 59px 60px),
        repeating-linear-gradient(0deg,  transparent 0 39px, rgba(148, 163, 184, 0.05) 39px 40px),
        repeating-linear-gradient(90deg, transparent 0 11px, rgba(148, 163, 184, 0.022) 11px 12px),
        repeating-linear-gradient(0deg,  transparent 0 7px,  rgba(148, 163, 184, 0.022) 7px 8px);
}
.activity-svg {
    display: block;
    width: 100%;
    height: 170px;
    overflow: visible;
    position: relative;
    z-index: 1;
}
.activity-axis {
    display: flex;
    justify-content: space-between;
    padding: 0.25rem 0.1rem 0.15rem;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.56rem;
    color: var(--fg-mute);
    letter-spacing: 0.1em;
    text-transform: uppercase;
}

/* Gauge cards — htop-style hatched block bars */
.gauge-card, .cpt-gauge {
    background: var(--bg-card);
    border: none;
    border-radius: 3px;
    padding: 0.55rem 0.75rem;
    min-height: 64px;
    position: relative;
    overflow: hidden;
    box-shadow: 0 0 0 1px var(--ring-soft);
    transition: box-shadow 0.12s;
}
.gauge-card:hover, .cpt-gauge:hover { box-shadow: 0 0 0 1px var(--ring-mid); }
.gauge-card::before, .cpt-gauge::before { content: none; }
.gauge-header, .cpt-gauge-head {
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.58rem;
    text-transform: uppercase;
    letter-spacing: 0.15em;
    margin-bottom: 0.28rem;
}
.gauge-label, .cpt-gauge-label { color: var(--fg-dim); }
.gauge-reset, .cpt-gauge-reset { color: var(--fg-mute); font-size: 0.56rem; letter-spacing: 0.08em; }
.gauge-track, .cpt-gauge-track {
    height: 10px;
    background: rgba(148, 163, 184, 0.08);
    border-radius: 0;
    overflow: hidden;
    margin-bottom: 0.35rem;
    position: relative;
}
.gauge-track::before, .cpt-gauge-track::before {
    content: "";
    position: absolute;
    inset: 0;
    background: repeating-linear-gradient(90deg, transparent 0 4px, var(--bg-card) 4px 5px);
    pointer-events: none;
    z-index: 2;
}
.gauge-fill, .cpt-gauge-fill {
    height: 100%;
    background: var(--accent);
    border-radius: 0;
    transition: width 0.4s cubic-bezier(0.16, 1, 0.3, 1);
    box-shadow: none;
}
.gauge-fill.warning, .cpt-gauge-fill.warning,
.cpt-gauge-fill.warn { background: var(--warn); box-shadow: none; }
.gauge-fill.danger, .cpt-gauge-fill.danger  { background: var(--danger); box-shadow: none; }
.gauge-stats, .cpt-gauge-stats {
    display: flex;
    align-items: baseline;
    gap: 0.3rem;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.9rem;
    letter-spacing: 0.02em;
    color: var(--fg);
}
.gauge-max, .cpt-gauge-max {
    font-size: 0.7rem;
    color: var(--fg-mute);
    font-family: 'JetBrains Mono', monospace;
}
.gauge-sub, .cpt-gauge-sub {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.6rem;
    color: var(--fg-mute);
    margin-left: auto;
    letter-spacing: 0.06em;
    text-transform: uppercase;
}
.gauge-delta, .cpt-gauge-delta {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.58rem;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    margin-left: auto;
    padding: 0.1rem 0.45rem;
    border-radius: 2px;
    border: none;
    color: var(--fg-mute);
    background: transparent;
    box-shadow: 0 0 0 1px var(--ring-soft);
}
.gauge-delta.up, .cpt-gauge-delta.up         { color: var(--accent); box-shadow: 0 0 0 1px rgba(61, 123, 255, 0.40); background: rgba(61, 123, 255, 0.06); }
.gauge-delta.down, .cpt-gauge-delta.down     { color: var(--fg-dim); box-shadow: 0 0 0 1px var(--ring-soft); background: transparent; }
.gauge-delta.neutral, .cpt-gauge-delta.neutral { color: var(--fg-mute); }

/* ─── Cockpit forecast card ─── */
.cpt-forecast {
    background: var(--bg-card);
    border: none;
    border-radius: 3px;
    padding: 0.6rem 0.8rem;
    margin-top: 0.6rem;
    box-shadow: 0 0 0 1px var(--ring-soft);
}
.cpt-forecast-head {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.78rem;
    color: var(--fg);
    text-transform: uppercase;
    letter-spacing: 0.04em;
    margin-bottom: 0.25rem;
    display: flex;
    justify-content: space-between;
    align-items: baseline;
}
.cpt-forecast-head em { font-style: normal; color: var(--accent); }
.cpt-forecast-sub {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.58rem;
    color: var(--fg-mute);
    letter-spacing: 0.08em;
    text-transform: uppercase;
}
.cpt-forecast-track {
    height: 18px;
    background: rgba(148, 163, 184, 0.06);
    box-shadow: inset 0 0 0 1px var(--ring-soft);
    position: relative;
    margin: 0.5rem 0 0.3rem;
}
.cpt-forecast-elapsed {
    position: absolute;
    left: 0; top: 0; bottom: 0;
    background: rgba(61, 123, 255, 0.35);
    border-right: 1px solid var(--accent);
}
.cpt-forecast-proj {
    position: absolute;
    top: 0; bottom: 0;
    background: repeating-linear-gradient(45deg,
        rgba(61, 123, 255, 0.12) 0 5px,
        rgba(61, 123, 255, 0.28) 5px 10px);
    border-right: 1px dashed var(--accent);
}
.cpt-forecast-now {
    position: absolute;
    top: -2px; bottom: -2px;
    width: 2px;
    background: var(--fg);
}
.cpt-forecast-legend {
    display: flex;
    gap: 0.9rem;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.56rem;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: var(--fg-mute);
    margin-top: 0.3rem;
    flex-wrap: wrap;
}

/* Scheduled-routine rows under forecast */
.cpt-sched {
    margin-top: 0.7rem;
    padding-top: 0.55rem;
    border-top: 1px solid var(--ring-soft);
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
}
.cpt-sched-row {
    display: grid;
    grid-template-columns: 3.2rem 1fr auto;
    align-items: baseline;
    column-gap: 0.6rem;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.66rem;
    letter-spacing: 0.04em;
}
.cpt-sched-time {
    color: var(--accent);
    font-weight: 500;
}
.cpt-sched-label {
    color: var(--fg);
    text-transform: uppercase;
    letter-spacing: 0.06em;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}
.cpt-sched-in {
    color: var(--fg-mute);
    font-size: 0.58rem;
    letter-spacing: 0.06em;
    text-transform: uppercase;
}
.cpt-forecast-legend em { font-style: normal; color: var(--fg-dim); }

/* ─── Cockpit vault pulse ─── */
.cpt-pulse-card {
    background: var(--bg-card);
    border: none;
    border-radius: 3px;
    padding: 0.55rem 0.75rem;
    margin-top: 0.6rem;
    box-shadow: 0 0 0 1px var(--ring-soft);
}
.cpt-pulse-card > .cpt-cat {
    margin: 0 0 0.35rem 0;
    padding-top: 0;
}
.cpt-pulse {
    display: grid;
    grid-template-columns: 4.6rem 1fr auto;
    gap: 0.5rem;
    align-items: center;
    padding: 0.35rem 0.1rem;
    border-top: 1px solid var(--ring-soft);
    font-family: 'JetBrains Mono', monospace;
}
.cpt-pulse:first-of-type { border-top: none; }
.cpt-pulse-main { min-width: 0; }
.cpt-verb {
    font-size: 0.56rem;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    padding: 0.12rem 0.4rem;
    border-radius: 2px;
    text-align: center;
    box-shadow: 0 0 0 1px var(--ring-soft);
    color: var(--fg-dim);
    font-weight: 500;
    display: inline-block;
}
.cpt-verb.created {
    color: var(--accent);
    box-shadow: 0 0 0 1px rgba(61, 123, 255, 0.35);
    background: rgba(61, 123, 255, 0.08);
}
.cpt-verb.appended {
    color: var(--warn);
    box-shadow: 0 0 0 1px rgba(224, 179, 92, 0.35);
    background: rgba(224, 179, 92, 0.06);
}
.cpt-verb.updated { color: var(--fg-dim); }
.cpt-verb.linked {
    color: var(--good);
    box-shadow: 0 0 0 1px rgba(143, 185, 122, 0.35);
    background: rgba(143, 185, 122, 0.06);
}
.cpt-pulse-name {
    color: var(--fg);
    font-size: 0.74rem;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    letter-spacing: 0.02em;
}
.cpt-pulse-dir {
    color: var(--fg-mute);
    font-size: 0.56rem;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}
.cpt-pulse-ago {
    color: var(--fg-mute);
    font-size: 0.58rem;
    letter-spacing: 0.06em;
    text-transform: uppercase;
}

/* ─── Header bar — wraps the col row via :has() + hidden marker ─── */
[data-testid="stVerticalBlock"]:has(> div > .cpt-header-marker),
[data-testid="stHorizontalBlock"]:has(.cpt-header-marker) {
    padding: 0.3rem 0.7rem !important;
    box-shadow: 0 0 0 1px var(--ring-soft);
    border-radius: 3px;
    background: var(--bg-card);
    margin-bottom: 0.7rem !important;
    align-items: center;
}
.cpt-header-marker { display: none; }

/* ─── Skill chips (anchor-based, 4-column grid) ─── */
.cpt-skill-grid {
    display: grid;
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: 0.45rem;
    margin: 0 0 0.55rem 0;
}
@media (max-width: 1100px) {
    .cpt-skill-grid { grid-template-columns: repeat(3, minmax(0, 1fr)); }
}
@media (max-width: 800px) {
    .cpt-skill-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
}
.cpt-skill {
    background: var(--bg-card);
    box-shadow: 0 0 0 1px var(--ring-soft);
    border-radius: 2px;
    padding: 0.45rem 0.6rem;
    font-family: 'JetBrains Mono', monospace;
    text-align: left;
    cursor: pointer;
    display: flex;
    flex-direction: column;
    gap: 0.12rem;
    transition: box-shadow 0.12s, color 0.12s;
    text-decoration: none !important;
    color: inherit;
    min-width: 0;
}
.cpt-skill:hover {
    box-shadow: 0 0 0 1px var(--accent);
    text-decoration: none !important;
}
.cpt-skill.loaded { box-shadow: 0 0 0 1px var(--accent); }
.cpt-skill-name {
    color: var(--fg);
    font-size: 0.72rem;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    font-weight: 500;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}
.cpt-skill:hover .cpt-skill-name { color: var(--accent); }
.cpt-skill-desc {
    color: var(--fg-mute);
    font-size: 0.6rem;
    letter-spacing: 0.02em;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    line-height: 1.3;
}

/* Reveal body after PREMIUM_CSS parses — overrides pre-hide from earlier inline style. */
body { opacity: 1; transition: opacity 0.18s ease-out; }

/* ─── Floating 💬 chat button (fixed bottom-right, both pages) ───
   ponytail: the .fab-chat-anchor marker + button share one st.container(),
   so the *element container* that :has() the marker gets pinned — the
   button inside it just fills that fixed box. Simpler than cross-sibling
   selectors, which break across Streamlit DOM-wrapper version changes. */
div[data-testid="stVerticalBlock"]:has(> div > .fab-chat-anchor) {
    position: fixed; bottom: 1.6rem; right: 1.6rem; z-index: 999;
    width: auto !important;
}
div[data-testid="stVerticalBlock"]:has(> div > .fab-chat-anchor) [data-testid="stButton"] button {
    width: 52px; height: 52px; border-radius: 50%;
    background: linear-gradient(160deg, var(--accent), var(--accent-deep));
    border: 1px solid rgba(255,255,255,.15);
    box-shadow: 0 6px 24px rgba(2,74,218,.45);
    font-size: 1.3rem; padding: 0;
}
div[data-testid="stVerticalBlock"]:has(> div > .fab-chat-anchor) [data-testid="stButton"] button:hover {
    transform: scale(1.06);
}
</style>
"""


HIDE_CHROME = (
    "<style>"
    "body{opacity:0}"
    '[data-testid="stToolbar"],[data-testid="stStatusWidget"],[data-testid="stHeader"],'
    '[data-testid="stDecoration"],#MainMenu,footer,header{display:none!important;height:0!important}'
    '[data-testid="stSidebar"],[data-testid="stSidebarCollapsedControl"]{display:none!important}'
    "</style>"
)


def inject():
    st.markdown(HIDE_CHROME, unsafe_allow_html=True)
    st.markdown(PREMIUM_CSS, unsafe_allow_html=True)
