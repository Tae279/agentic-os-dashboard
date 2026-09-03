"use client";

import { kpis } from "@/lib/radar";

type KpiItem = ReturnType<typeof kpis>[number];

const TONE_CLASS = {
  good: "text-good",
  warn: "text-warn",
  danger: "text-danger",
} as const;

export function RadarKpis({
  items,
  onPick,
  activeFilter,
}: {
  items: ReturnType<typeof kpis>;
  onPick: (k: KpiItem) => void;
  activeFilter: string;
}) {
  return (
    <div className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-6 gap-3">
      {items.map((item) => {
        const active = item.filter === activeFilter;
        const tone = item.tone ? TONE_CLASS[item.tone] : "text-fg";
        return (
          <button
            key={item.id}
            type="button"
            onClick={() => onPick(item)}
            aria-pressed={active}
            className={`rounded-[var(--radius-card)] hairline bg-bg-card p-3.5 text-left hairline-hover cursor-pointer transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent/60 ${
              active ? "ring-1 ring-accent/60" : ""
            }`}
          >
            <div className="text-[11px] uppercase tracking-[0.14em] text-fg-mute">{item.label}</div>
            <div className={`font-display text-3xl font-semibold tabular-nums ${tone}`}>
              {item.value}
            </div>
            <div className="text-[11px] text-fg-dim">{item.sub}</div>
          </button>
        );
      })}
    </div>
  );
}
