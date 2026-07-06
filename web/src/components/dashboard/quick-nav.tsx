"use client";

import Image from "next/image";
import { api } from "@/lib/api";

const OBSIDIAN_VAULT = "DX AI Agent OS";

function obsidianUri(file: string) {
  return `obsidian://open?vault=${encodeURIComponent(OBSIDIAN_VAULT)}&file=${encodeURIComponent(file)}`;
}

export function Mascot() {
  return (
    <div
      className="h-9 w-9 shrink-0 rounded-[var(--radius-chip)] hairline bg-bg-card flex items-center justify-center overflow-hidden"
      style={{ imageRendering: "pixelated" }}
    >
      <Image src="/robot-idle.png" alt="" width={24} height={24} style={{ imageRendering: "pixelated" }} unoptimized />
    </div>
  );
}

export function QuickNavPills({ quickRoutes }: { quickRoutes: { label: string; path: string }[] }) {
  return (
    <div className="flex items-center gap-1.5 flex-wrap">
      <button
        onClick={() => api.openTerminal()}
        className="px-2.5 py-1 rounded-[var(--radius-chip)] hairline hairline-hover text-[11px] text-fg-dim hover:text-fg transition-colors"
      >
        claude code
      </button>
      <a
        href={obsidianUri("")}
        target="_blank"
        rel="noreferrer"
        className="px-2.5 py-1 rounded-[var(--radius-chip)] hairline hairline-hover text-[11px] text-fg-dim hover:text-fg transition-colors"
      >
        vault
      </a>
      <a
        href={obsidianUri(`raw/${new Date().toISOString().slice(0, 10)}.md`)}
        target="_blank"
        rel="noreferrer"
        className="px-2.5 py-1 rounded-[var(--radius-chip)] hairline hairline-hover text-[11px] text-fg-dim hover:text-fg transition-colors"
      >
        daily note
      </a>
      {quickRoutes.map((qr) => (
        <button
          key={qr.label}
          onClick={() => api.open(qr.path)}
          className="px-2.5 py-1 rounded-[var(--radius-chip)] hairline hairline-hover text-[11px] text-fg-dim hover:text-fg transition-colors"
        >
          {qr.label}
        </button>
      ))}
    </div>
  );
}
