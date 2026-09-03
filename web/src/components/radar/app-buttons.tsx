"use client";

import { useState } from "react";
import { Copy, ExternalLink } from "lucide-react";
import { api, type DevServer, type RadarApp } from "@/lib/api";

const PILL =
  "inline-flex items-center gap-1 px-2.5 py-1 rounded-[var(--radius-chip)] hairline hairline-hover text-[11px] text-fg-dim hover:text-fg transition-colors";

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
            <span key={`${app.kind}-${app.label}-${app.port ?? ""}`} className="inline-flex items-center gap-1">
              {running ? (
                <a href={app.url} target="_blank" rel="noreferrer" className={PILL}>
                  <span className="size-1.5 rounded-full bg-good" />
                  {app.label} · :{app.port}
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
                  <span className="size-1.5 rounded-full bg-fg-mute" />
                  {app.label} · ยังไม่รัน
                </button>
              )}
              {!running && app.cmd ? (
                <span className="inline-flex items-center gap-1 px-2 py-1 rounded-[var(--radius-chip)] hairline font-mono-num text-[11px] text-fg-dim">
                  {app.cmd}
                  <button
                    type="button"
                    onClick={() => copyCmd(app.cmd!)}
                    className="text-fg-mute hover:text-fg"
                    title="คัดลอกคำสั่ง"
                  >
                    {copied === app.cmd ? "คัดลอกแล้ว" : <Copy size={12} />}
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
