"use client";

import { Chip } from "@heroui/react";
import { Check, Undo2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import type { RadarDecision, RadarProject } from "@/lib/api";

const IMPACT = {
  3: { label: "ผลกระทบสูง", color: "danger" },
  2: { label: "กลาง", color: "warning" },
  1: { label: "ต่ำ", color: "default" },
} as const;

export function DecisionCards({
  decisions,
  projects,
  checked,
  onToggle,
  onOpenProject,
}: {
  decisions: RadarDecision[];
  projects: RadarProject[];
  checked: Record<string, boolean>;
  onToggle: (key: string, next: boolean) => void;
  onOpenProject: (id: string) => void;
}) {
  if (decisions.length === 0) {
    return (
      <div className="rounded-[var(--radius-card)] hairline bg-bg-card p-4 text-fg-dim">
        ไม่มีเรื่องรอตัดสินใจ
      </div>
    );
  }

  const ordered = decisions
    .map((decision, index) => ({ decision, index }))
    .sort((a, b) => {
      const aDone = Number(!!checked[`decision:${a.decision.id}`]);
      const bDone = Number(!!checked[`decision:${b.decision.id}`]);
      return aDone - bDone || b.decision.impact - a.decision.impact || a.index - b.index;
    });

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
      {ordered.map(({ decision }) => {
        const key = `decision:${decision.id}`;
        const answered = !!checked[key];
        const project = projects.find((item) => item.id === decision.project);
        const impact = IMPACT[decision.impact];

        return (
          <article
            key={decision.id}
            className={`rounded-[var(--radius-card)] hairline bg-bg-card p-4 ${answered ? "opacity-60" : ""}`}
          >
            <div className="flex items-center gap-2">
              <Chip size="sm" variant="soft" color={impact.color}>
                {impact.label}
              </Chip>
              {project ? (
                <button
                  type="button"
                  onClick={() => onOpenProject(project.id)}
                  className="font-mono-num text-[11px] hairline rounded-[var(--radius-chip)] px-1.5 text-fg-dim hover:text-fg"
                >
                  {project.code}
                </button>
              ) : null}
              {answered ? (
                <Chip size="sm" variant="soft" color="success" className="ml-auto">
                  ตอบแล้ว
                </Chip>
              ) : null}
            </div>

            <h2 className="font-display text-base text-fg mt-2">{decision.question}</h2>
            <p className="text-xs text-fg-dim mt-1">{decision.why}</p>

            <div className="mt-3">
              <div className="text-[11px] uppercase tracking-[0.14em] text-fg-mute">แนะนำ</div>
              <p className="text-sm text-fg">{decision.rec}</p>
            </div>
            <div className="mt-3">
              <div className="text-[11px] uppercase tracking-[0.14em] text-fg-mute">ต้นทุน</div>
              <p className="font-mono-num text-[11px] text-fg-dim">{decision.cost}</p>
            </div>

            <div className="mt-4">
              <Button
                size="sm"
                variant="secondary"
                onClick={() => onToggle(key, !answered)}
              >
                {answered ? <Undo2 size={14} /> : <Check size={14} />}
                {answered ? "ยกเลิก" : "ตอบแล้ว"}
              </Button>
            </div>
          </article>
        );
      })}
    </div>
  );
}
