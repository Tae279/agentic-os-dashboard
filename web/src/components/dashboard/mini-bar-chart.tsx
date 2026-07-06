"use client";

// ponytail: tiny inline SVG bar chart — reused for 7-day runs + value series,
// no chart lib needed for 7 bars.
export function MiniBarChart({ labels, values, height = 70 }: { labels: string[]; values: number[]; height?: number }) {
  const max = Math.max(...values, 1);
  const w = 100 / values.length;
  return (
    <div>
      <div className="flex items-end gap-1" style={{ height }}>
        {values.map((v, i) => (
          <div key={i} className="flex-1 flex flex-col justify-end h-full" style={{ width: `${w}%` }}>
            <div
              className="rounded-t-sm bg-accent"
              style={{ height: `${Math.max(2, (v / max) * 100)}%` }}
              title={String(v)}
            />
          </div>
        ))}
      </div>
      <div className="flex text-[9px] font-mono-num text-fg-mute mt-1">
        {labels.map((l, i) => (
          <span key={i} className="flex-1 text-center">
            {l}
          </span>
        ))}
      </div>
    </div>
  );
}
