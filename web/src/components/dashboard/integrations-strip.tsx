"use client";

import type { Integration } from "@/lib/api";

const STATUS_COLOR: Record<string, string> = {
  connected: "var(--good)",
  pending: "var(--warn)",
  needs_auth: "var(--warn)",
  failed: "var(--danger)",
  unknown: "var(--fg-mute)",
};

export function IntegrationsStrip({ integrations }: { integrations: Integration[] }) {
  if (integrations.length === 0) return null;
  return (
    <div className="rounded-[var(--radius-chip)] hairline bg-bg-card/60 px-3 py-2 flex items-center gap-3 overflow-x-auto">
      <span className="text-[10px] font-mono-num uppercase tracking-wide text-fg-mute shrink-0">integrations</span>
      {integrations.map((s, i) => (
        <span key={i} className="flex items-center gap-1.5 text-xs text-fg-dim shrink-0">
          <span
            className="h-1.5 w-1.5 rounded-full shrink-0"
            style={{ background: STATUS_COLOR[s.status] || STATUS_COLOR.unknown }}
          />
          {s.name}
        </span>
      ))}
    </div>
  );
}
