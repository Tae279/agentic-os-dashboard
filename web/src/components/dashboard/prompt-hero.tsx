"use client";

import { useState } from "react";
import { streamPost } from "@/lib/api";

export function PromptHero({
  onRunOutput,
}: {
  onRunOutput: (label: string, text: string, phase: string | null) => void;
}) {
  const [prompt, setPrompt] = useState("");
  const [running, setRunning] = useState(false);

  async function run() {
    const text0 = prompt.trim();
    if (!text0 || running) return;
    setRunning(true);
    onRunOutput("Quick Prompt", "", "starting");
    let text = "";
    await streamPost(
      "/api/run",
      { prompt: text0 },
      {
        onPhase: (d) => onRunOutput("Quick Prompt", text, d.phase),
        onText: (d) => {
          text += d.chunk;
          onRunOutput("Quick Prompt", text, null);
        },
        onDone: () => setRunning(false),
        onError: () => setRunning(false),
      }
    );
  }

  return (
    <div className="rounded-[var(--radius-card)] hairline bg-bg-card p-5 mb-4">
      <div className="text-[11px] font-mono-num uppercase tracking-wide text-fg-mute mb-1">ready</div>
      <h2 className="font-display text-2xl font-semibold text-fg mb-3">
        run a <span className="text-accent">skill</span> to begin
      </h2>
      <textarea
        value={prompt}
        onChange={(e) => setPrompt(e.target.value)}
        placeholder="พิมพ์อะไรก็ได้ หรือกดการ์ดข้างล่าง…"
        rows={4}
        disabled={running}
        className="w-full bg-bg-elev hairline rounded-[var(--radius-chip)] px-3.5 py-3 text-sm text-fg placeholder:text-fg-mute focus:outline-none focus:border-accent resize-none disabled:opacity-60"
      />
      <div className="flex items-center gap-2 mt-3">
        <button
          onClick={run}
          disabled={running || !prompt.trim()}
          className="flex-1 py-2.5 rounded-[var(--radius-chip)] font-semibold text-sm text-white transition-all disabled:opacity-40 disabled:cursor-not-allowed"
          style={{
            background: "linear-gradient(135deg, var(--accent), var(--accent-deep))",
            boxShadow: running ? "none" : "0 0 24px -4px rgba(61,123,255,0.55)",
          }}
        >
          {running ? "กำลังรัน…" : "run →"}
        </button>
        <button
          onClick={() => setPrompt("")}
          disabled={running}
          className="px-4 py-2.5 rounded-[var(--radius-chip)] hairline hairline-hover text-sm text-fg-dim hover:text-fg transition-colors disabled:opacity-40"
        >
          เคลียร์
        </button>
      </div>
    </div>
  );
}
