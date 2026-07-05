"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import type { UsageResponse } from "@/lib/api";

function GaugeChip({ label, pct, sub }: { label: string; pct: number; sub: string }) {
  const color = pct >= 85 ? "var(--danger)" : pct >= 60 ? "var(--warn)" : "var(--accent)";
  return (
    <div className="flex items-center gap-2 px-3 py-1.5 rounded-[var(--radius-chip)] hairline hairline-hover transition-colors">
      <div className="relative h-6 w-6 shrink-0">
        <svg viewBox="0 0 24 24" className="h-6 w-6 -rotate-90">
          <circle cx="12" cy="12" r="10" fill="none" stroke="var(--ring-soft)" strokeWidth="3" />
          <circle
            cx="12" cy="12" r="10" fill="none" stroke={color} strokeWidth="3"
            strokeDasharray={`${(pct / 100) * 62.8} 62.8`} strokeLinecap="round"
          />
        </svg>
      </div>
      <div className="leading-tight">
        <div className="text-[11px] text-fg-dim">{label}</div>
        <div className="text-xs font-mono-num text-fg">{sub}</div>
      </div>
    </div>
  );
}

export function StatusStrip({ usage }: { usage: UsageResponse | null }) {
  const [open, setOpen] = useState(false);

  if (!usage) {
    return (
      <div className="h-12 hairline rounded-[var(--radius-chip)] bg-bg-card/60 animate-pulse" />
    );
  }

  return (
    <>
      <motion.button
        initial={{ opacity: 0, y: -8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.35, ease: "easeOut" }}
        onClick={() => setOpen((o) => !o)}
        className="w-full flex items-center justify-between gap-3 px-3 py-2 rounded-[var(--radius-chip)] hairline hairline-hover bg-bg-card/60 backdrop-blur-sm text-left transition-colors"
      >
        <div className="flex items-center gap-2 flex-wrap">
          <GaugeChip label="5 ชม." pct={usage.five_hour.pct} sub={`${usage.five_hour.pct}%`} />
          <GaugeChip label="สัปดาห์" pct={usage.weekly.pct} sub={`${usage.weekly.pct}%`} />
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-[var(--radius-chip)] hairline">
            <span className="text-[11px] text-fg-dim">มูลค่าวันนี้</span>
            <span className="text-xs font-mono-num text-good">{usage.value.today_fmt}</span>
          </div>
        </div>
        <div className="flex items-center gap-1.5 text-[11px] text-fg-mute px-2">
          <span className="h-1.5 w-1.5 rounded-full bg-good" />
          <span>ว่าง</span>
        </div>
      </motion.button>

      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.2 }}
            className="overflow-hidden"
          >
            <div className="mt-2 p-4 rounded-[var(--radius-card)] hairline bg-bg-card grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
              <div>
                <div className="text-fg-dim text-[11px] mb-1">5 ชม. reset</div>
                <div className="font-mono-num">{usage.five_hour.resets_in}</div>
              </div>
              <div>
                <div className="text-fg-dim text-[11px] mb-1">สัปดาห์ reset</div>
                <div className="font-mono-num">{usage.weekly.resets_in}</div>
              </div>
              <div>
                <div className="text-fg-dim text-[11px] mb-1">มูลค่าเดือนนี้</div>
                <div className="font-mono-num text-good">{usage.value.month_fmt}</div>
              </div>
              <div>
                <div className="text-fg-dim text-[11px] mb-1">รันวันนี้</div>
                <div className="font-mono-num">{usage.metrics.runs_today}</div>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}
