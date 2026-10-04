"use client";

import { CalendarClock } from "lucide-react";
// beta.6's root import loads unrelated optional peers (including shiki).
import { Timeline as ProTimeline } from "@heroui-pro/react/timeline";
import type { RadarEvent, RadarProject } from "@/lib/api";
import { activityStrip, ageLabel, daysAgo, eventStatus } from "@/lib/radar";

export function Timeline({
  events,
  projects,
  onOpenProject,
}: {
  events: RadarEvent[];
  projects: RadarProject[];
  onOpenProject: (id: string) => void;
}) {
  const activity = activityStrip(events, 14);
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
      <div className="rounded-[var(--radius-card)] hairline bg-bg-card p-6">
        <CalendarClock size={28} aria-hidden className="text-fg-mute" />
        <p className="text-sm text-fg mt-2">ยังไม่มีเหตุการณ์</p>
        <p className="text-xs text-fg-dim mt-1">เหตุการณ์จะขึ้นที่นี่เมื่อไฟล์สถานะโปรเจกต์ถูกอัปเดต</p>
      </div>
    );
  }

  return (
    <div className="space-y-5">
      <div className="rounded-[var(--radius-card)] hairline bg-bg-card p-3">
        <h2 className="text-[11px] uppercase tracking-[0.14em] text-fg-mute mb-2">14 วันล่าสุด</h2>
        <div className="grid grid-cols-14 gap-1">
          {activity.map(({ date, count }) => (
            <div key={date} className="h-6 rounded-[4px] bg-bg-elev" title={`${date} · ${count} เหตุการณ์`} style={count > 0 ? { background: `color-mix(in srgb, var(--accent) ${Math.min(100, 20 + count * 25)}%, transparent)` } : undefined} />
          ))}
        </div>
        <div className="flex justify-between mt-1 font-mono-num text-[10px] text-fg-mute">
          <span>{activity[0].date}</span><span>{activity[activity.length - 1].date}</span>
        </div>
      </div>
      {groups.map(([date, items]) => (
        <section key={date}>
          <h2 className="font-mono-num text-[11px] uppercase tracking-[0.14em] text-fg-mute mb-2">
            {date} · {ageLabel(daysAgo(date))}
          </h2>
          <ProTimeline size="sm" density="compact">
            {items.map((event, itemIndex) => {
              const project = projects.find((item) => item.code === event.code);
              const codeClass = "font-mono-num text-[11px] hairline rounded-[var(--radius-chip)] px-1.5";
              return (
                <ProTimeline.Item key={`${event.code}-${itemIndex}`} status={eventStatus(event, projects)}>
                  <ProTimeline.Content>
                    <div className="flex items-start gap-2">
                      {project && event.code !== "ALL" ? (
                        <button
                          type="button"
                          onClick={() => onOpenProject(project.id)}
                          className={`${codeClass} py-0.5 text-fg-dim hover:text-fg shrink-0 cursor-pointer transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent/60`}
                        >
                          {event.code}
                        </button>
                      ) : (
                        <span className={`${codeClass} text-fg-mute shrink-0`}>{event.code}</span>
                      )}
                      <span className="text-sm text-fg-dim line-clamp-2">{event.text}</span>
                    </div>
                  </ProTimeline.Content>
                </ProTimeline.Item>
              );
            })}
          </ProTimeline>
        </section>
      ))}
    </div>
  );
}
