"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import { api, type Project, type Recommendations } from "@/lib/api";

const PRIORITY_COLOR: Record<string, string> = {
  High: "var(--danger)",
  Medium: "var(--warn)",
  Low: "var(--fg-mute)",
};

export default function PortfolioPage() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [recs, setRecs] = useState<Recommendations | null>(null);

  useEffect(() => {
    api.projects().then((d) => setProjects(d.projects)).catch(() => {});
    api.artifacts().then((d) => setRecs(d.recommendations)).catch(() => {});
  }, []);

  return (
    <div className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 py-6 space-y-8">
      <header className="flex items-center justify-between gap-4">
        <div>
          <h1 className="font-display text-xl font-semibold text-fg">Portfolio</h1>
          <p className="text-xs text-fg-dim mt-0.5">{projects.length} โปรเจคที่กำลังดูแล</p>
        </div>
        <nav className="flex items-center gap-1">
          <Link
            href="/"
            className="text-xs text-fg-dim hover:text-fg px-3 py-1.5 rounded-[var(--radius-chip)] hairline hairline-hover transition-colors"
          >
            ← Launcher
          </Link>
          <Link
            href="/radar"
            className="text-xs text-fg-dim hover:text-fg px-3 py-1.5 rounded-[var(--radius-chip)] hairline hairline-hover transition-colors"
          >
            radar
          </Link>
          <Link
            href="/health"
            className="text-xs text-fg-dim hover:text-fg px-3 py-1.5 rounded-[var(--radius-chip)] hairline hairline-hover transition-colors"
          >
            ตรวจระบบ
          </Link>
        </nav>
      </header>

      {recs && (
        <section>
          <h2 className="text-xs text-fg-mute mb-2 font-mono-num">AI แนะนำ — ต้องทำ</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mb-4">
            {recs.must_do.map((r, i) => (
              <div key={i} className="rounded-[var(--radius-card)] hairline bg-bg-card p-3 text-xs">
                <div className="text-fg">{r.text}</div>
                <div className="text-fg-mute font-mono-num mt-1">{r.project}</div>
              </div>
            ))}
          </div>
        </section>
      )}

      <section>
        <h2 className="text-xs text-fg-mute mb-2 font-mono-num">โปรเจคทั้งหมด</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-3">
          {projects.map((p, i) => (
            <motion.div
              key={p.tag}
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3, delay: i * 0.02 }}
              className="rounded-[var(--radius-card)] hairline hairline-hover bg-bg-card p-4"
            >
              <div className="flex items-start justify-between gap-2 mb-2">
                <div className="font-display font-semibold text-sm text-fg">{p.name}</div>
                <span
                  className="text-[10px] px-2 py-0.5 rounded-full hairline font-mono-num shrink-0"
                  style={{ color: PRIORITY_COLOR[p.priority] || "var(--fg-mute)" }}
                >
                  {p.priority}
                </span>
              </div>
              <div className="text-xs text-fg-dim mb-2 line-clamp-2">
                {p.latest_entry?.summary || p.notes}
              </div>
              {p.latest_entry && (
                <div className="text-[11px] text-fg-mute font-mono-num">
                  อัพเดทล่าสุด: {p.latest_entry.date}
                </div>
              )}
            </motion.div>
          ))}
        </div>
      </section>
    </div>
  );
}
