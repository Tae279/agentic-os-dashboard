"use client";

import { ProgressCircle } from "@heroui/react";
import { RadialChart } from "@heroui-pro/react/radial-chart";
import { motion, useReducedMotion } from "framer-motion";
import { CircleHelp, GitBranch, ServerCrash } from "lucide-react";
import type { RadarResponse, RadarStatus } from "@/lib/api";
import { portfolioProgress, statusCounts, waitingCounts, STATUS_LABEL, WAITING_LABEL, type WaitingKey } from "@/lib/radar";

const STATUS_FILL: Record<RadarStatus, string> = {
  live: "var(--good)", building: "var(--accent)", behind: "var(--danger)", quiet: "var(--warn)", planning: "var(--ring-mid)",
};
const WAITING_FILL: Record<WaitingKey, string> = { tae: "var(--warn)", external: "var(--fg-mute)", agent: "var(--accent)" };
const labelClass = "text-[11px] uppercase tracking-[0.14em] text-fg-mute";
const cardClass = "rounded-[var(--radius-card)] hairline bg-bg-card p-4";

export function RadarOverview({ data, activeFilter, onFilter, onTab }: {
  data: RadarResponse;
  activeFilter: string;
  onFilter: (id: string) => void;
  onTab: (t: "decisions") => void;
}) {
  const reducedMotion = useReducedMotion();
  const { projects, decisions } = data;
  const progress = portfolioProgress(projects);
  const statuses = statusCounts(projects);
  const waiting = waitingCounts(projects);
  const answered = decisions.filter((d) => data.state.checked[`decision:${d.id}`]).length;
  const impact3 = decisions.filter((d) => d.impact === 3).length;
  const entrance = (index: number) => ({
    initial: reducedMotion ? false as const : { opacity: 0, y: 10 },
    animate: { opacity: 1, y: 0 },
    transition: { duration: reducedMotion ? 0 : 0.4, delay: reducedMotion ? 0 : index * 0.05, ease: "easeOut" as const },
  });
  const metrics = [
    { id: "decisions", Icon: CircleHelp, label: "รอเต้ตัดสินใจ", value: decisions.length - answered, sub: `${impact3} เรื่องผลกระทบสูง`, tone: "var(--accent)" },
    { id: "uncommitted", Icon: GitBranch, label: "งานยังไม่ push", value: projects.filter((p) => p.uncommitted).length, sub: "เสี่ยงหายถ้าเครื่องพัง", tone: "var(--warn)" },
    { id: "behind", Icon: ServerCrash, label: "prod ตามหลังโค้ด", value: statuses.behind, sub: "บั๊กที่แก้แล้วยังอยู่บนของจริง", tone: "var(--danger)" },
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-6 gap-3">
      <motion.div {...entrance(0)} className={`${cardClass} md:col-span-2 min-w-0`}>
        <h2 className={labelClass}>ภาพรวมพอร์ต</h2>
        <div className="relative size-[168px] mx-auto my-3" role="img" aria-label={`ความคืบหน้ารวม ${progress}% · ${projects.length} โปรเจกต์`}>
          <RadialChart data={[{ name: "ความคืบหน้ารวม", value: progress, fill: "var(--accent)" }]} width={168} height={168} innerRadius="78%" outerRadius="100%" barSize={12} startAngle={90} endAngle={-270}>
            <RadialChart.AngleAxis angleAxisId={0} domain={[0, 100]} tick={false} type="number" />
            <RadialChart.Bar background={{ fill: "var(--ring-mid)" }} angleAxisId={0} cornerRadius={12} dataKey="value" isAnimationActive={!reducedMotion} />
          </RadialChart>
          <div className="absolute inset-0 pointer-events-none flex flex-col items-center justify-center">
            <span className="font-display text-4xl font-semibold tabular-nums text-fg">{progress}%</span>
            <span className="text-[11px] text-fg-dim">{projects.length} โปรเจกต์</span>
          </div>
        </div>
        <div className="flex h-2 rounded-full overflow-hidden bg-bg-elev">
          {(Object.keys(STATUS_FILL) as RadarStatus[]).filter((s) => statuses[s] > 0).map((s) => (
            <div key={s} style={{ flex: statuses[s], background: STATUS_FILL[s] }} title={`${STATUS_LABEL[s]} ${statuses[s]}`} />
          ))}
        </div>
        <div className="flex flex-wrap gap-x-3 gap-y-1 mt-2">
          {(Object.keys(STATUS_FILL) as RadarStatus[]).filter((s) => statuses[s] > 0).map((s) => (
            <button key={s} type="button" onClick={() => onFilter(s === "live" || s === "behind" || s === "quiet" ? s : "all")} className="inline-flex items-center gap-1.5 text-[11px] text-fg-dim hover:text-fg cursor-pointer focus-visible:ring-2 focus-visible:ring-accent/60">
              <span className="size-1.5 rounded-full" style={{ background: STATUS_FILL[s] }} />
              {STATUS_LABEL[s]} {statuses[s]}
            </button>
          ))}
        </div>
      </motion.div>

      <motion.div {...entrance(1)} className={`${cardClass} md:col-span-2 min-w-0 flex flex-col`}>
        <h2 className={labelClass}>ติดที่ใคร</h2>
        <div className="flex-1 flex flex-col justify-center gap-3 my-4">
          {(["tae", "external", "agent"] as const).map((key) => {
            const filter = key === "agent" ? "all" : key;
            return (
              <button key={key} type="button" onClick={() => onFilter(filter)} aria-pressed={activeFilter === filter} className={`grid grid-cols-[auto_1fr_auto] items-center gap-3 p-2 min-h-11 rounded-[var(--radius-chip)] text-left cursor-pointer focus-visible:ring-2 focus-visible:ring-accent/60 ${activeFilter === filter ? "bg-accent-soft" : ""}`}>
                <span className="text-xs text-fg">{WAITING_LABEL[key]}</span>
                <span className="h-2 rounded-full bg-bg-elev overflow-hidden">
                  <span className="block h-full rounded-full" style={{ width: `${projects.length ? waiting[key] / projects.length * 100 : 0}%`, background: WAITING_FILL[key] }} />
                </span>
                <span className="font-mono-num text-sm tabular-nums text-fg">{waiting[key]}</span>
              </button>
            );
          })}
        </div>
        <p className="text-[11px] text-fg-mute">รอเต้ = งานที่ agent ทำแทนไม่ได้ · กดแถวเพื่อกรอง</p>
      </motion.div>

      <div className="md:col-span-2 grid grid-rows-3 gap-3 min-w-0">
        {metrics.map(({ id, Icon, label, value, sub, tone }, index) => (
          <motion.div key={id} {...entrance(index + 2)} className="min-w-0">
            <button type="button" onClick={() => id === "decisions" ? onTab("decisions") : onFilter(id)} className={`${cardClass} hairline-hover flex items-center gap-3 w-full h-full text-left cursor-pointer focus-visible:ring-2 focus-visible:ring-accent/60 ${activeFilter === id ? "ring-1 ring-accent/60" : ""}`}>
              <span className="size-8 rounded-[var(--radius-chip)] flex items-center justify-center shrink-0" style={{ background: `color-mix(in srgb, ${tone} 15%, transparent)`, color: tone }}><Icon size={16} aria-hidden /></span>
              <span className="min-w-0 flex-1">
                <span className={`block ${labelClass}`}>{label}</span>
                <span className="block font-display text-2xl font-semibold tabular-nums text-fg">{value}</span>
                <span className="block text-[11px] text-fg-dim truncate">{sub}</span>
              </span>
              {id === "decisions" && (
                <ProgressCircle size="sm" color="warning" value={decisions.length ? answered / decisions.length * 100 : 0} aria-label="ตอบแล้ว" className="size-11 shrink-0">
                  <ProgressCircle.Track className="size-full"><ProgressCircle.TrackCircle /><ProgressCircle.FillCircle /></ProgressCircle.Track>
                </ProgressCircle>
              )}
            </button>
          </motion.div>
        ))}
      </div>
    </div>
  );
}
