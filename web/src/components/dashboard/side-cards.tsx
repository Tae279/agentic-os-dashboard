"use client";

import type { Forecast, ValueSeries, VaultPulseItem } from "@/lib/api";
import { MiniBarChart } from "./mini-bar-chart";

export function ForecastCard({ forecast }: { forecast: Forecast | null }) {
  if (!forecast) return <div className="h-32 rounded-[var(--radius-card)] hairline bg-bg-card/60 animate-pulse" />;
  const isOverCap = forecast.state === "over_cap";
  return (
    <div className="rounded-[var(--radius-card)] hairline bg-bg-card p-3.5">
      <div className="flex items-baseline justify-between text-xs font-mono-num text-fg-dim mb-1">
        <span>forecast · 5h</span>
        <span className="text-fg-mute">{forecast.burn_fmt}</span>
      </div>
      <div className={`text-xs mb-2 ${isOverCap ? "text-danger" : "text-fg-dim"}`}>{forecast.headline}</div>
      <div className="relative h-2 rounded-full bg-bg-elev overflow-hidden mb-2">
        <div className="absolute inset-y-0 left-0 bg-accent-deep" style={{ width: `${forecast.elapsed_pct}%` }} />
        <div
          className="absolute inset-y-0 bg-accent-soft"
          style={{ left: `${forecast.elapsed_pct}%`, width: `${Math.max(0, forecast.proj_pct - forecast.elapsed_pct)}%` }}
        />
        <div className="absolute inset-y-0 w-px bg-fg" style={{ left: `${forecast.elapsed_pct}%` }} />
      </div>
      <div className="flex items-center gap-2 text-[10px] text-fg-mute mb-2">
        <span>█ elapsed</span>
        <span>▨ projected</span>
        <span className="ml-auto">resets · {forecast.resets_in}</span>
      </div>
      <div className="space-y-1 border-t border-ring-soft pt-2">
        {forecast.schedule.map((s, i) => (
          <div key={i} className="flex items-center justify-between text-[11px]">
            <span className="font-mono-num text-fg-dim">{s.time}</span>
            <span className="text-fg-dim">{s.label}</span>
            <span className="font-mono-num text-fg-mute">in {s.in}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

export function ValueCard({ value }: { value: ValueSeries | null }) {
  if (!value) return <div className="h-32 rounded-[var(--radius-card)] hairline bg-bg-card/60 animate-pulse" />;
  if (!value.available) {
    return (
      <div className="rounded-[var(--radius-card)] hairline bg-bg-card p-3.5">
        <div className="text-xs font-mono-num text-fg-dim mb-1">value · api-equivalent</div>
        <div className="text-[11px] text-fg-mute">ccusage unavailable</div>
      </div>
    );
  }
  return (
    <div className="rounded-[var(--radius-card)] hairline bg-bg-card p-3.5">
      <div className="text-xs font-mono-num text-fg-dim mb-1">value · api-equivalent</div>
      <div className="flex items-baseline gap-2 mb-2">
        <span className="text-lg font-display font-semibold text-good">${value.today.toFixed(2)}</span>
        <span className="text-[11px] text-fg-mute">today</span>
      </div>
      <div className="flex items-center gap-3 text-[11px] text-fg-mute mb-2">
        <span>yesterday · ${value.yesterday.toFixed(2)}</span>
        <span>7d · ${value.week_total.toFixed(2)}</span>
      </div>
      <MiniBarChart labels={value.series.map((s) => s.label)} values={value.series.map((s) => s.value)} height={56} />
      <div className="text-[10px] text-fg-mute mt-2">มูลค่างานเทียบราคา API — จ่ายจริงคือค่า Max รายเดือน</div>
    </div>
  );
}

const VERB_COLOR: Record<string, string> = {
  created: "var(--good)",
  linked: "var(--accent)",
  appended: "var(--warn)",
  updated: "var(--fg-mute)",
};

export function VaultPulseCard({ items }: { items: VaultPulseItem[] }) {
  return (
    <div className="rounded-[var(--radius-card)] hairline bg-bg-card p-3.5">
      <div className="text-xs font-mono-num text-fg-dim mb-2">vault pulse</div>
      {items.length === 0 && <div className="text-[11px] text-fg-mute italic">ยังไม่มีการเปลี่ยนแปลง</div>}
      <div className="space-y-1.5">
        {items.map((it, i) => (
          <a
            key={i}
            href={it.obsidian_uri}
            target="_blank"
            rel="noreferrer"
            className="flex items-center gap-2 text-[11px] hover:bg-bg-elev -mx-1.5 px-1.5 py-0.5 rounded transition-colors"
          >
            <span
              className="px-1.5 py-0.5 rounded text-[9px] uppercase shrink-0"
              style={{ color: VERB_COLOR[it.verb] || "var(--fg-mute)", background: "rgba(148,163,184,0.08)" }}
            >
              {it.verb}
            </span>
            <span className="truncate text-fg flex-1">{it.name}</span>
            <span className="text-fg-mute shrink-0">{it.age_fmt}</span>
          </a>
        ))}
      </div>
    </div>
  );
}
