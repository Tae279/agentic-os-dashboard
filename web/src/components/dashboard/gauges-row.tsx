"use client";

import { motion } from "framer-motion";
import type { UsageResponse } from "@/lib/api";

function gaugeClass(pct: number, dangerAt?: number) {
  if (dangerAt !== undefined && pct >= dangerAt) return "var(--danger)";
  if (pct >= 90) return "var(--danger)";
  if (pct >= 70) return "var(--warn)";
  return "var(--accent)";
}

function GaugeCard({
  label,
  resetLabel,
  pct,
  statPrimary,
  statMax,
  statSub,
  dangerAt,
  delay,
}: {
  label: string;
  resetLabel: string;
  pct: number;
  statPrimary: string;
  statMax: string;
  statSub: string;
  dangerAt?: number;
  delay: number;
}) {
  const color = gaugeClass(pct, dangerAt);
  const isDanger = dangerAt !== undefined && pct >= dangerAt;
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay, ease: "easeOut" }}
      className={`rounded-[var(--radius-card)] hairline bg-bg-card p-4 ${isDanger ? "glow-focal" : ""}`}
      style={isDanger ? { boxShadow: "0 0 0 1px rgba(229,72,77,0.4), 0 8px 30px -12px rgba(229,72,77,0.35)" } : undefined}
    >
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs font-mono-num text-fg-dim">{label}</span>
        <span className="text-[10px] font-mono-num text-fg-mute">{resetLabel}</span>
      </div>
      <div className="h-1.5 rounded-full bg-bg-elev overflow-hidden mb-2">
        <motion.div
          className="h-full rounded-full"
          style={{ background: color }}
          initial={{ width: 0 }}
          animate={{ width: `${Math.min(100, pct)}%` }}
          transition={{ duration: 0.6, ease: "easeOut" }}
        />
      </div>
      <div className="flex items-baseline gap-1.5 flex-wrap">
        <span className="text-lg font-display font-semibold text-fg">{statPrimary}</span>
        <span className="text-xs text-fg-mute">/ {statMax}</span>
        <span className="text-[11px] text-fg-dim ml-auto">{statSub}</span>
      </div>
    </motion.div>
  );
}

export function GaugesRow({ usage }: { usage: UsageResponse | null }) {
  if (!usage) {
    return (
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        {[0, 1, 2].map((i) => (
          <div key={i} className="h-24 rounded-[var(--radius-card)] hairline bg-bg-card/60 animate-pulse" />
        ))}
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
      <GaugeCard
        label="5-hour window"
        resetLabel={`resets · ${usage.five_hour.resets_in}`}
        pct={usage.five_hour.pct}
        statPrimary={usage.five_hour.tokens.toLocaleString()}
        statMax={usage.five_hour.limit_fmt}
        statSub={`· ${usage.five_hour.sessions} sessions`}
        dangerAt={80}
        delay={0}
      />
      <GaugeCard
        label="weekly window"
        resetLabel={`resets · ${usage.weekly.resets_in}`}
        pct={usage.weekly.pct}
        statPrimary={usage.weekly.tokens.toLocaleString()}
        statMax={usage.weekly.limit_fmt}
        statSub=""
        delay={0.08}
      />
      <GaugeCard
        label="routines · max"
        resetLabel="resets · midnight"
        pct={(usage.today.routines / 15) * 100}
        statPrimary={String(usage.today.routines)}
        statMax="15"
        statSub={`${usage.value.today_fmt} today`}
        delay={0.16}
      />
    </div>
  );
}
