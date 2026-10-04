"use client";

import { Chip, ProgressCircle } from "@heroui/react";
import { motion, useReducedMotion } from "framer-motion";
import { AlertTriangle, Bot, GitBranch, Globe, Play, SearchX, User } from "lucide-react";
import type { RadarProject } from "@/lib/api";
import { ageLabel, attentionRank, daysAgo, statusColor, statusStripeClass, waitingKey } from "@/lib/radar";

function EmptyState() {
  return (
    <div className="p-6">
      <SearchX size={28} aria-hidden className="text-fg-mute" />
      <p className="text-sm text-fg mt-2">ไม่มีโปรเจกต์ที่ตรง filter</p>
      <p className="text-xs text-fg-dim mt-1">ลองเลือก “ทั้งหมด” หรือล้างคำค้นหา (กด Esc)</p>
    </div>
  );
}

const chipClass = "inline-flex items-center gap-1 text-[10px] rounded-[var(--radius-chip)] hairline px-1.5 py-0.5";
const WAITING = {
  tae: { Icon: User, label: "รอเต้", tone: "text-warn" },
  external: { Icon: Globe, label: "รอภายนอก", tone: "text-fg-dim" },
  agent: { Icon: Bot, label: "agent", tone: "text-accent" },
};

export function ProjectGrid({ projects, onOpen, checked }: {
  projects: RadarProject[];
  onOpen: (id: string) => void;
  checked: Record<string, boolean>;
}) {
  const reducedMotion = useReducedMotion();
  const ordered = [...projects].sort((a, b) => attentionRank(a) - attentionRank(b) || (b.updated ?? "").localeCompare(a.updated ?? ""));

  if (ordered.length === 0) {
    return <div className="rounded-[var(--radius-card)] hairline bg-bg-card"><EmptyState /></div>;
  }

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-4 gap-3">
      {ordered.map((p, index) => {
        const age = daysAgo(p.updated);
        const { Icon, label, tone } = WAITING[waitingKey(p)];
        const total = p.tae_checklist.length;
        const done = p.tae_checklist.filter((item) => checked[item.id]).length;
        return (
          <motion.div key={p.id} initial={reducedMotion ? false : { opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: reducedMotion ? 0 : 0.4, delay: reducedMotion ? 0 : Math.min(index, 12) * 0.03, ease: "easeOut" }} className="min-w-0">
            <button type="button" onClick={() => onOpen(p.id)} className="w-full h-full text-left rounded-[var(--radius-card)] hairline hairline-hover bg-bg-card p-4 cursor-pointer focus-visible:ring-2 focus-visible:ring-accent/60 relative overflow-hidden transition-transform motion-safe:hover:-translate-y-px motion-reduce:transition-none">
              <span aria-hidden className={`absolute left-0 top-0 bottom-0 w-[3px] border-l-[3px] ${statusStripeClass(p.status)}`} />
              <span className="flex gap-3 items-start">
                <span className="relative size-14 shrink-0">
                  <ProgressCircle size="lg" value={p.progress} color={statusColor(p.status)} aria-label={`${p.code} ${p.progress}%`} className="size-14">
                    <ProgressCircle.Track className="size-full" strokeWidth={3} viewBox="0 0 36 36">
                      <ProgressCircle.TrackCircle cx={18} cy={18} r={16} strokeWidth={3} />
                      <ProgressCircle.FillCircle cx={18} cy={18} r={16} strokeWidth={3} strokeLinecap="round" />
                    </ProgressCircle.Track>
                  </ProgressCircle>
                  <span className="absolute inset-0 flex items-center justify-center pointer-events-none font-mono-num text-[11px] tabular-nums text-fg">{p.gap ? "—" : `${p.progress}%`}</span>
                </span>
                <span className="min-w-0 flex-1">
                  <span className="flex items-center justify-between gap-2">
                    <span className="font-mono-num text-[10px] uppercase tracking-[0.12em] text-fg-mute truncate">{p.code}</span>
                    <Chip size="sm" variant="soft" color={statusColor(p.status)} className="truncate max-w-[60%] [&_[data-slot=chip-label]]:truncate">{p.statusLabel}</Chip>
                  </span>
                  <span className="block font-display text-sm text-fg truncate mt-1">{p.name}</span>
                  <span className="block text-xs text-fg-dim truncate mt-1">{p.next}</span>
                  <span className="flex items-center gap-1.5 mt-2 flex-wrap">
                    <span className={`${chipClass} ${tone}`}><Icon size={10} aria-hidden />{label}</span>
                    {p.uncommitted && <span className={`${chipClass} text-warn`}><GitBranch size={10} aria-hidden />ยังไม่ push</span>}
                    {p.blocker && <span className={`${chipClass} text-danger`} title={p.blocker} role="img" aria-label={p.blocker}><AlertTriangle size={10} aria-hidden /></span>}
                    {p.actions.length > 0 && <span className={`${chipClass} text-accent`}><Play size={10} aria-hidden />รันได้</span>}
                    <span className={`ml-auto font-mono-num text-[10px] ${!p.gap && (age === null || age > 30) ? "text-danger" : "text-fg-mute"}`}>{ageLabel(age)}</span>
                  </span>
                  {total > 0 && (
                    <span className="block h-[3px] rounded-full bg-bg-elev mt-2 overflow-hidden" title={`${done}/${total} เต้ต้องกดเอง`}>
                      <span className="block h-full rounded-full" style={{ width: `${done / total * 100}%`, background: "var(--good)" }} />
                    </span>
                  )}
                </span>
              </span>
            </button>
          </motion.div>
        );
      })}
    </div>
  );
}
