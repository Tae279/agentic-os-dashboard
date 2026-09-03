"use client";

import type { RadarEvent, RadarProject } from "@/lib/api";
import { ageLabel, daysAgo } from "@/lib/radar";

export function Timeline({
  events,
  projects,
  onOpenProject,
}: {
  events: RadarEvent[];
  projects: RadarProject[];
  onOpenProject: (id: string) => void;
}) {
  const groups = Array.from(
    events.reduce((map, event) => {
      const group = map.get(event.date) ?? [];
      group.push(event);
      map.set(event.date, group);
      return map;
    }, new Map<string, RadarEvent[]>()),
  ).sort(([a], [b]) => b.localeCompare(a));

  if (groups.length === 0) {
    return (
      <div className="rounded-[var(--radius-card)] hairline bg-bg-card p-4 text-fg-dim">
        ยังไม่มีเหตุการณ์
      </div>
    );
  }

  return (
    <div className="space-y-5">
      {groups.map(([date, items], groupIndex) => (
        <section key={date}>
          <h2 className="font-mono-num text-[11px] uppercase tracking-[0.14em] text-fg-mute mb-2">
            {date} · {ageLabel(daysAgo(date))}
          </h2>
          <div className="border-l border-ring-soft pl-4 ml-1 space-y-2">
            {items.map((event, itemIndex) => {
              const project = projects.find((item) => item.code === event.code);
              const codeClass = "font-mono-num text-[11px] hairline rounded-[var(--radius-chip)] px-1.5";
              return (
                <div key={`${event.code}-${itemIndex}`} className="relative flex items-start gap-2">
                  <span
                    className={`absolute -left-[19px] top-1.5 size-[6px] rounded-full ${
                      groupIndex === 0 && itemIndex === 0 ? "bg-accent" : "bg-ring-mid"
                    }`}
                  />
                  {project ? (
                    <button
                      type="button"
                      onClick={() => onOpenProject(project.id)}
                      className={`${codeClass} text-fg-dim hover:text-fg shrink-0`}
                    >
                      {event.code}
                    </button>
                  ) : (
                    <span className={`${codeClass} text-fg-mute shrink-0`}>{event.code}</span>
                  )}
                  <span className="text-sm text-fg-dim">{event.text}</span>
                </div>
              );
            })}
          </div>
        </section>
      ))}
    </div>
  );
}
