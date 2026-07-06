"use client";

import { motion } from "framer-motion";
import { Circle, Inbox, FileText } from "lucide-react";
import type { LiveSession, InboxItem, RunSummary, Forecast, ValueSeries, VaultPulseItem, RunsPerDay } from "@/lib/api";
import { ForecastCard, ValueCard, VaultPulseCard } from "./side-cards";
import { MiniBarChart } from "./mini-bar-chart";

function timeAgo(ts: number) {
  const d = Math.floor(Date.now() / 1000 - ts);
  if (d < 60) return `${d}s`;
  if (d < 3600) return `${Math.floor(d / 60)}m`;
  return `${Math.floor(d / 3600)}h`;
}

const STATE_COLOR: Record<string, string> = {
  executing: "var(--accent)",
  thinking: "var(--warn)",
  idle: "var(--fg-mute)",
};

export function RightRail({
  sessions,
  inbox,
  runs,
  forecast,
  value,
  vaultPulse,
  runsPerDay,
}: {
  sessions: LiveSession[];
  inbox: InboxItem[];
  runs: RunSummary[];
  forecast: Forecast | null;
  value: ValueSeries | null;
  vaultPulse: VaultPulseItem[];
  runsPerDay: RunsPerDay | null;
}) {
  return (
    <motion.aside
      initial={{ opacity: 0, x: 12 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.35, delay: 0.1 }}
      className="w-full lg:w-80 shrink-0 rounded-[var(--radius-card)] hairline bg-bg-card/60 p-4 space-y-5 max-h-[calc(100vh-8rem)] overflow-y-auto"
    >
      <Section icon={<Circle size={13} />} title="Live sessions">
        {sessions.length === 0 && <Empty text="ไม่มี session ที่ทำงานอยู่" />}
        {sessions.map((s, i) => (
          <div key={i} className="flex items-center gap-2 text-xs py-1.5">
            <span
              className="h-1.5 w-1.5 rounded-full shrink-0"
              style={{ background: STATE_COLOR[s.state] || "var(--fg-mute)" }}
            />
            <span className="truncate flex-1 text-fg">{s.project}</span>
            <span className="text-fg-mute font-mono-num">{timeAgo(s.last)}</span>
          </div>
        ))}
      </Section>

      <Section icon={<Inbox size={13} />} title="📥 Decision inbox">
        {inbox.length === 0 && <Empty text="ไม่มีเรื่องรอตัดสินใจ" />}
        {inbox.slice(0, 8).map((item, i) => (
          <div key={i} className="text-xs py-1.5 border-b border-ring-soft last:border-0">
            <div className="text-fg-dim line-clamp-2">{item.text}</div>
            <div className="text-fg-mute font-mono-num mt-0.5">{item.source}</div>
          </div>
        ))}
      </Section>

      <Section icon={<FileText size={13} />} title="Recent runs">
        {runs.length === 0 && <Empty text="ยังไม่มีการรัน" />}
        {runs.slice(0, 8).map((r, i) => (
          <div key={i} className="text-xs py-1.5 flex items-center justify-between gap-2">
            <span className="truncate text-fg">{r.skill || r.file}</span>
            <span className="text-fg-mute font-mono-num shrink-0">{timeAgo(r.mtime)}</span>
          </div>
        ))}
      </Section>

      {runsPerDay && runsPerDay.values.length > 0 && (
        <div>
          <div className="text-[11px] text-fg-mute mb-1.5">
            last <em>seven</em> days · {runsPerDay.total} runs
          </div>
          <MiniBarChart labels={runsPerDay.labels} values={runsPerDay.values} />
        </div>
      )}

      <ForecastCard forecast={forecast} />
      <ValueCard value={value} />
      <VaultPulseCard items={vaultPulse} />
    </motion.aside>
  );
}

function Section({ icon, title, children }: { icon: React.ReactNode; title: string; children: React.ReactNode }) {
  return (
    <div>
      <div className="flex items-center gap-1.5 text-[11px] text-fg-mute mb-1.5">
        {icon}
        <span>{title}</span>
      </div>
      <div>{children}</div>
    </div>
  );
}

function Empty({ text }: { text: string }) {
  return <div className="text-xs text-fg-mute italic py-1">{text}</div>;
}
