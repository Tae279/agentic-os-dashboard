"use client";

import { useState } from "react";
import { Copy, ExternalLink } from "lucide-react";
import { api, type DevServer, type RadarApp } from "@/lib/api";

const PILL =
  "inline-flex items-center gap-1 min-h-10 md:min-h-0 px-2.5 py-1 rounded-[var(--radius-chip)] hairline hairline-hover text-[11px] text-fg-dim hover:text-fg transition-colors cursor-pointer focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent/60";

export function AppButtons({
  apps,
  devservers,
}: {
  apps: RadarApp[];
  devservers: DevServer[];
}) {
  const [copied, setCopied] = useState<string | null>(null);

  function copyCmd(cmd: string) {
    void navigator.clipboard.writeText(cmd);
    setCopied(cmd);
    window.setTimeout(() => {
      setCopied((c) => (c === cmd ? null : c));
    }, 1500);
  }

  return (
    <div>
      <div className="text-[11px] uppercase tracking-[0.14em] text-fg-mute mb-1.5">เปิดแอป</div>
      <div className="flex flex-wrap gap-1.5">
        {apps.map((app) => {
          if (app.kind === "prod") {
            return (
              <a
                key={`${app.kind}-${app.label}`}
                href={app.url}
                target="_blank"
                rel="noreferrer"
                className={PILL}
              >
                <ExternalLink size={12} />
                {app.label}
              </a>
            );
          }

          const running = devservers.some((s) => s.port === app.port);
          return (
            <span
              key={`${app.kind}-${app.label}-${app.port ?? ""}`}
              className="inline-flex flex-wrap items-center gap-1 min-w-0 max-w-full"
            >
              {running ? (
                <a href={app.url} target="_blank" rel="noreferrer" className={PILL}>
                  <span className="size-1.5 rounded-full bg-good" aria-hidden />
                  <span className="whitespace-nowrap">{app.label} · :{app.port}</span>
                </a>
              ) : (
                <button
                  type="button"
                  onClick={() => {
                    if (app.cwd) void api.open(app.cwd);
                  }}
                  title="เปิดโฟลเดอร์ใน Finder"
                  className={PILL}
                >
                  <span className="size-1.5 rounded-full bg-fg-mute" aria-hidden />
                  <span className="whitespace-nowrap">{app.label} · ยังไม่รัน</span>
                </button>
              )}
              {!running && app.cmd ? (
                <span className="inline-flex items-center gap-1 min-w-0 max-w-full px-2 py-1 rounded-[var(--radius-chip)] hairline font-mono-num text-[11px] text-fg-dim">
                  <span className="truncate min-w-0">{app.cmd}</span>
                  <button
                    type="button"
                    onClick={() => copyCmd(app.cmd!)}
                    className={"inline-flex items-center justify-center size-10 md:size-6 shrink-0 rounded-[var(--radius-chip)] text-fg-mute hover:text-fg cursor-pointer transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent/60"}
                    aria-label="คัดลอกคำสั่ง"
                    title="คัดลอกคำสั่ง"
                  >
                    {copied === app.cmd ? "คัดลอกแล้ว" : <Copy size={12} aria-hidden />}
                  </button>
                </span>
              ) : null}
            </span>
          );
        })}
      </div>
    </div>
  );
}
