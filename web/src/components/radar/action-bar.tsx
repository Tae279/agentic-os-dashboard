"use client";

import { Chip } from "@heroui/react";
import { ChevronRight, Loader2, Play, Square } from "lucide-react";
import type { RadarAction, RadarProject } from "@/lib/api";
import type { RadarRun } from "@/lib/radar";
import { Button } from "@/components/ui/button";

export function ActionBar({
  project,
  run,
  onStart,
  onStop,
}: {
  project: RadarProject;
  run: RadarRun | null;
  onStart: (a: RadarAction) => void;
  onStop: () => void;
}) {
  const busy = !!(run && !run.done);

  return (
    <div>
      <div className="text-[11px] uppercase tracking-[0.14em] text-fg-mute mb-1.5">
        งานที่ agent รันเองได้
      </div>
      <div className="space-y-3">
        {project.actions.map((action) => {
          const isThis = run?.actionId === action.id;
          const thisBusy = !!(isThis && run && !run.done);
          const thisDone = !!(isThis && run?.done);
          const cwdBase = action.cwd.split("/").pop() ?? action.cwd;

          return (
            <div key={action.id} className="space-y-1.5">
              <div className="flex items-start justify-between gap-3">
                <div className="min-w-0">
                  <div className="flex items-center gap-1.5 flex-wrap">
                    <span className="text-sm text-fg">{action.label}</span>
                    {action.kind === "plan" ? (
                      <Chip size="sm" variant="soft" color="accent">
                        ทำแผน
                      </Chip>
                    ) : (
                      <Chip size="sm" variant="soft" color="default">
                        git
                      </Chip>
                    )}
                  </div>
                  <div className="font-mono-num text-[11px] text-fg-mute">{cwdBase}</div>
                </div>
                <div className="flex items-center gap-1.5 shrink-0">
                  {thisBusy ? (
                    <>
                      <Button size="sm" className="min-h-11 md:min-h-0" disabled>
                        <Loader2 size={14} className="animate-spin" />
                        กำลังรัน · {run.phase}
                      </Button>
                      <Button size="sm" variant="secondary" className="min-h-11 md:min-h-0" onClick={onStop}>
                        <Square size={14} />
                        หยุด
                      </Button>
                    </>
                  ) : (
                    <Button
                      size="sm"
                      className="min-h-11 md:min-h-0"
                      disabled={busy}
                      title={busy ? "รอ run ปัจจุบันจบก่อน" : undefined}
                      onClick={() => onStart(action)}
                    >
                      <Play size={14} />
                      รันให้เสร็จ
                    </Button>
                  )}
                </div>
              </div>
              {thisDone && run && (
                <div className={run.ok ? "text-good text-xs" : "text-danger text-xs"}>
                  {run.ok ? (
                    <>
                      เสร็จแล้ว
                      {run.cost != null ? ` · $${run.cost.toFixed(2)}` : ""}
                      {run.savedPath ? (
                        <span className="font-mono-num">
                          {" "}
                          {run.savedPath.split("/").pop()}
                        </span>
                      ) : null}
                    </>
                  ) : (
                    <>ล้มเหลว · {run.error}</>
                  )}
                </div>
              )}
              <details className="group">
                <summary className="inline-flex items-center gap-1 min-h-11 md:min-h-0 text-[11px] text-fg-mute cursor-pointer rounded-[var(--radius-chip)] list-none [&::-webkit-details-marker]:hidden focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent/60">
                  <ChevronRight
                    size={12}
                    aria-hidden
                    className="transition-transform group-open:rotate-90"
                  />
                  ดู prompt ที่จะรัน
                </summary>
                <pre className="text-[11px] text-fg-dim whitespace-pre-wrap font-mono-num max-h-48 overflow-y-auto">
                  {action.prompt}
                </pre>
              </details>
            </div>
          );
        })}
      </div>
    </div>
  );
}
