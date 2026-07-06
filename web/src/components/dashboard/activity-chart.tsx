"use client";

import { motion } from "framer-motion";
import type { ActivitySeries } from "@/lib/api";

// ponytail: inline SVG area chart, no chart lib — same approach app.py used
// (build_activity_svg), just ported to React/TSX with a fixed viewBox.

export function ActivityChart({ data }: { data: ActivitySeries | null }) {
  if (!data || data.cumulative.length === 0) {
    return <div className="h-44 rounded-[var(--radius-card)] hairline bg-bg-card/60 animate-pulse" />;
  }

  const { cumulative, dates } = data;
  const n = cumulative.length;
  const maxC = Math.max(...cumulative, 1);
  const VB_W = 1000;
  const VB_H = 180;
  const ML = 24, MR = 24, MT = 14, MB = 6;
  const pw = VB_W - ML - MR;
  const ph = VB_H - MT - MB;

  const pts = cumulative.map((c, i) => {
    const x = ML + (i / Math.max(1, n - 1)) * pw;
    const y = MT + ph - (c / maxC) * ph;
    return [x, y] as const;
  });

  const lineD = "M " + pts.map(([x, y]) => `${x.toFixed(2)},${y.toFixed(2)}`).join(" L ");
  const areaD =
    `M ${pts[0][0].toFixed(2)},${(MT + ph).toFixed(2)} ` +
    pts.map(([x, y]) => `L ${x.toFixed(2)},${y.toFixed(2)}`).join(" ") +
    ` L ${pts[n - 1][0].toFixed(2)},${(MT + ph).toFixed(2)} Z`;

  const tickIdx = [0, Math.floor(n / 4), Math.floor(n / 2), Math.floor((3 * n) / 4), n - 1];
  const tickLabels = tickIdx.map((i) =>
    new Date(dates[i]).toLocaleDateString("en-US", { month: "short", day: "numeric" }).toLowerCase()
  );

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
      className="rounded-[var(--radius-card)] hairline bg-bg-card p-4"
    >
      <div className="flex items-baseline gap-2 mb-2 text-xs font-mono-num text-fg-dim">
        <span>agentic os · cumulative activity · 30d</span>
        <span className="text-fg-mute">
          · {data.total.toLocaleString()} total · {data.last_30d} last 30d
        </span>
      </div>
      <svg viewBox={`0 0 ${VB_W} ${VB_H}`} preserveAspectRatio="none" className="w-full h-36">
        <defs>
          <linearGradient id="activityFill" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#3d7bff" stopOpacity="0.48" />
            <stop offset="60%" stopColor="#3d7bff" stopOpacity="0.14" />
            <stop offset="100%" stopColor="#3d7bff" stopOpacity="0" />
          </linearGradient>
        </defs>
        <path d={areaD} fill="url(#activityFill)" stroke="none" />
        <path
          d={lineD}
          fill="none"
          stroke="#3d7bff"
          strokeWidth="1.6"
          strokeLinejoin="round"
          strokeLinecap="round"
          vectorEffect="non-scaling-stroke"
        />
        <circle cx={pts[n - 1][0]} cy={pts[n - 1][1]} r="3.5" fill="#b8ccff" />
      </svg>
      <div className="flex justify-between text-[10px] font-mono-num text-fg-mute mt-1">
        {tickLabels.map((l, i) => (
          <span key={i}>{l}</span>
        ))}
      </div>
    </motion.div>
  );
}
