"use client";

import { useEffect, useState, useCallback } from "react";
import Link from "next/link";
import { api, streamPost } from "@/lib/api";
import type { Skill, UsageResponse, LiveSession, InboxItem, RunSummary } from "@/lib/api";
import { StatusStrip } from "@/components/dashboard/status-strip";
import { LauncherGrid } from "@/components/dashboard/launcher-grid";
import { RunOutput } from "@/components/dashboard/run-output";
import { RightRail } from "@/components/dashboard/right-rail";
import { ChatDock } from "@/components/dashboard/chat-dock";
import { CommandPalette } from "@/components/dashboard/command-palette";

export default function Home() {
  const [skills, setSkills] = useState<Skill[]>([]);
  const [usageCounts, setUsageCounts] = useState<Record<string, number>>({});
  const [usage, setUsage] = useState<UsageResponse | null>(null);
  const [sessions, setSessions] = useState<LiveSession[]>([]);
  const [inbox, setInbox] = useState<InboxItem[]>([]);
  const [runs, setRuns] = useState<RunSummary[]>([]);

  const [runLabel, setRunLabel] = useState<string | null>(null);
  const [runText, setRunText] = useState("");
  const [runPhase, setRunPhase] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    const [s, uc, u, sess, ib, r] = await Promise.allSettled([
      api.skills(),
      api.usageCounts(),
      api.usage(),
      api.sessions(),
      api.inbox(),
      api.runs(),
    ]);
    if (s.status === "fulfilled") setSkills(s.value.skills);
    if (uc.status === "fulfilled") setUsageCounts(uc.value);
    if (u.status === "fulfilled") setUsage(u.value);
    if (sess.status === "fulfilled") setSessions(sess.value.sessions);
    if (ib.status === "fulfilled") setInbox(ib.value.items);
    if (r.status === "fulfilled") setRuns(r.value.runs);
  }, []);

  useEffect(() => {
    refresh();
    const id = setInterval(refresh, 15000);
    return () => clearInterval(id);
  }, [refresh]);

  function handleRunOutput(label: string, text: string, phase: string | null) {
    setRunLabel(label);
    setRunText(text);
    if (phase) setRunPhase(phase);
  }

  return (
    <div className="flex-1 flex flex-col">
      <header className="px-6 pt-6 pb-3">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h1 className="font-display text-lg font-semibold text-fg">DX Agentic OS</h1>
            <p className="text-xs text-fg-mute">Command Center · เต้</p>
          </div>
          <nav className="flex items-center gap-1 text-xs">
            <span className="px-3 py-1.5 rounded-[var(--radius-chip)] hairline bg-bg-card text-fg">launcher</span>
            <Link
              href="/portfolio"
              className="px-3 py-1.5 rounded-[var(--radius-chip)] text-fg-dim hover:text-fg hover:bg-bg-card transition-colors"
            >
              portfolio
            </Link>
          </nav>
        </div>
        <StatusStrip usage={usage} />
      </header>

      <main className="flex-1 px-6 pb-8 flex flex-col lg:flex-row gap-6">
        <div className="flex-1 min-w-0">
          <RunOutput
            label={runLabel}
            text={runText}
            phase={runPhase}
            onClose={() => {
              setRunLabel(null);
              setRunPhase(null);
            }}
          />
          <LauncherGrid skills={skills} usageCounts={usageCounts} onRunOutput={handleRunOutput} />
        </div>
        <RightRail sessions={sessions} inbox={inbox} runs={runs} />
      </main>

      <ChatDock />
      <CommandPalette
        skills={skills}
        onSelect={async (skill) => {
          setRunLabel(skill.label);
          setRunText("");
          setRunPhase("starting");
          let text = "";
          await streamPost(
            "/api/run",
            { skill_label: skill.label, input: "" },
            {
              onPhase: (d) => setRunPhase(d.phase),
              onText: (d) => {
                text += d.chunk;
                setRunText(text);
              },
              onDone: () => refresh(),
            }
          );
        }}
      />
    </div>
  );
}
