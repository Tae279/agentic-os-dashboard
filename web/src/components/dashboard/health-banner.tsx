"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { TriangleAlert } from "lucide-react";
import { api, type Doctor } from "@/lib/api";

const POLL_MS = 60_000;

/** Global strip: shows only when the doctor sees a FAIL (or the API itself stops answering). */
export function HealthBanner() {
  const [doc, setDoc] = useState<Doctor | null>(null);
  const [misses, setMisses] = useState(0);

  useEffect(() => {
    let alive = true;
    const tick = () =>
      api
        .doctor()
        .then((d) => alive && (setDoc(d), setMisses(0)))
        .catch(() => alive && setMisses((m) => m + 1));
    tick();
    const id = setInterval(tick, POLL_MS);
    return () => {
      alive = false;
      clearInterval(id);
    };
  }, []);

  // two missed polls in a row = the backend is really down (one miss can be a page reload)
  if (misses >= 2) {
    return <Strip title="ระบบหลังบ้านไม่ตอบ" detail="งานที่สั่งจากหน้านี้จะไม่ทำงานจนกว่าจะเปิดใหม่ — ดับเบิลคลิก 'เปิด Dashboard.command'" />;
  }
  const failed = doc?.checks.filter((c) => c.status === "fail") ?? [];
  if (failed.length === 0) return null;
  const first = failed[0];
  return (
    <Strip
      title={failed.length > 1 ? `${first.label} และอีก ${failed.length - 1} จุดมีปัญหา` : `${first.label} มีปัญหา`}
      detail={[first.detail, first.fix].filter(Boolean).join(" · ")}
    />
  );
}

function Strip({ title, detail }: { title: string; detail: string }) {
  return (
    <div
      role="alert"
      className="flex items-center gap-3 px-4 sm:px-6 py-2.5 text-xs border-b"
      style={{
        color: "var(--fg)",
        borderColor: "color-mix(in srgb, var(--danger) 45%, transparent)",
        background: "color-mix(in srgb, var(--danger) 14%, var(--bg))",
      }}
    >
      <TriangleAlert className="size-4 shrink-0" style={{ color: "var(--danger)" }} aria-hidden />
      <p className="min-w-0 flex-1">
        <span className="font-semibold">{title}</span>
        <span className="text-fg-dim"> — {detail}</span>
      </p>
      <Link
        href="/health"
        className="shrink-0 px-2.5 py-1 rounded-[var(--radius-chip)] hairline hairline-hover text-fg hover:bg-bg-card transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent/60"
      >
        ดูรายละเอียด
      </Link>
    </div>
  );
}
