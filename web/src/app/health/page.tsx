"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { CircleCheck, CircleX, TriangleAlert, CircleMinus, RefreshCw, KeyRound } from "lucide-react";
import { api, type Doctor, type DoctorCheck, type DoctorStatus } from "@/lib/api";

const STATUS: Record<DoctorStatus, { label: string; color: string; Icon: typeof CircleCheck }> = {
  pass: { label: "ผ่าน", color: "var(--good)", Icon: CircleCheck },
  warn: { label: "ระวัง", color: "var(--warn)", Icon: TriangleAlert },
  fail: { label: "ไม่ผ่าน", color: "var(--danger)", Icon: CircleX },
  skip: { label: "ข้าม", color: "var(--fg-mute)", Icon: CircleMinus },
};

const OVERALL_TEXT: Record<string, string> = {
  pass: "ทุกอย่างปกติ",
  warn: "ปกติ แต่มีเรื่องควรรู้",
  fail: "มีจุดที่พัง ต้องแก้",
  unknown: "ยังไม่มีผลตรวจ",
};

function ago(ts: number | null | undefined): string {
  if (!ts) return "ไม่เคย";
  const s = Math.max(0, Math.floor(Date.now() / 1000 - ts));
  if (s < 90) return "เมื่อครู่";
  if (s < 5400) return `${Math.floor(s / 60)} นาทีก่อน`;
  if (s < 129600) return `${Math.floor(s / 3600)} ชม.ก่อน`;
  return `${Math.floor(s / 86400)} วันก่อน`;
}

export default function HealthPage() {
  const [doc, setDoc] = useState<Doctor | null>(null);
  const [busy, setBusy] = useState<"check" | "probe" | null>(null);
  const [err, setErr] = useState<string | null>(null);

  const load = useCallback(() => {
    api.doctor().then((d) => (setDoc(d), setErr(null))).catch(() => setErr("เชื่อมต่อระบบหลังบ้านไม่ได้ — ลองเปิด Dashboard ใหม่"));
  }, []);

  useEffect(() => {
    load();
    const id = setInterval(load, 30_000);
    return () => clearInterval(id);
  }, [load]);

  async function run(probe: boolean) {
    setBusy(probe ? "probe" : "check");
    try {
      setDoc(await api.doctorRun(probe));
      setErr(null);
    } catch {
      setErr("ตรวจไม่สำเร็จ — ระบบหลังบ้านไม่ตอบ");
    } finally {
      setBusy(null);
    }
  }

  const overall = doc?.overall ?? "unknown";
  const tone = overall === "unknown" ? "skip" : (overall as DoctorStatus);

  return (
    <div className="flex-1 max-w-3xl w-full mx-auto px-4 sm:px-6 py-6 space-y-6">
      <header className="flex items-center justify-between gap-4 flex-wrap">
        <div>
          <h1 className="font-display text-xl font-semibold text-fg">ตรวจระบบ</h1>
          <p className="text-xs text-fg-dim mt-0.5">ตรวจอัตโนมัติทุก 5 นาที · ตรวจล่าสุด {ago(doc?.ts)}</p>
        </div>
        <nav className="flex items-center gap-1">
          <Link href="/" className="text-xs text-fg-dim hover:text-fg px-3 py-1.5 rounded-[var(--radius-chip)] hairline hairline-hover transition-colors">
            ← Launcher
          </Link>
        </nav>
      </header>

      {err && (
        <p role="alert" className="text-xs rounded-[var(--radius-chip)] hairline px-3 py-2" style={{ color: "var(--danger)" }}>
          {err}
        </p>
      )}

      <section
        aria-live="polite"
        className="rounded-[var(--radius-card)] hairline bg-bg-card p-4 flex items-center gap-3"
        style={{ borderColor: `color-mix(in srgb, ${STATUS[tone].color} 40%, transparent)` }}
      >
        {(() => {
          const { Icon, color } = STATUS[tone];
          return <Icon className="size-6 shrink-0" style={{ color }} aria-hidden />;
        })()}
        <div className="min-w-0">
          <p className="font-display text-lg font-semibold text-fg">{OVERALL_TEXT[overall]}</p>
          {doc && doc.checks.length > 0 && (
            <p className="text-xs text-fg-dim">
              {doc.checks.filter((c) => c.status === "pass").length}/{doc.checks.length} จุดผ่าน
            </p>
          )}
        </div>
      </section>

      <div className="flex gap-2 flex-wrap">
        <button
          type="button"
          onClick={() => run(false)}
          disabled={busy !== null}
          className="inline-flex items-center gap-2 min-h-10 px-3.5 text-xs rounded-[var(--radius-chip)] hairline hairline-hover bg-bg-card text-fg disabled:opacity-50 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent/60"
        >
          <RefreshCw className={`size-3.5 ${busy === "check" ? "animate-spin" : ""}`} aria-hidden />
          ตรวจใหม่
        </button>
        <button
          type="button"
          onClick={() => run(true)}
          disabled={busy !== null}
          className="inline-flex items-center gap-2 min-h-10 px-3.5 text-xs rounded-[var(--radius-chip)] hairline hairline-hover bg-bg-card text-fg disabled:opacity-50 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent/60"
        >
          <KeyRound className="size-3.5" aria-hidden />
          {busy === "probe" ? "กำลังทดสอบ…" : "ทดสอบ login ตอนนี้"}
        </button>
        <span className="self-center text-[11px] text-fg-mute">ทดสอบ login = เรียก Claude 1 ครั้งสั้นๆ (ไม่ถึงสตางค์)</span>
      </div>

      <section aria-label="ผลตรวจรายจุด">
        <ul className="space-y-2">
          {(doc?.checks ?? []).map((c) => (
            <CheckRow key={c.id} c={c} />
          ))}
        </ul>
      </section>

      {doc && (doc.heal_notes.length > 0 || doc.heal_log.length > 0 || doc.last_alerts.length > 0) && (
        <section className="space-y-3">
          {(doc.heal_notes.length > 0 || doc.heal_log.length > 0) && (
            <div>
              <h2 className="text-xs text-fg-mute mb-2 font-mono-num">ซ่อมอัตโนมัติ</h2>
              <ul className="text-xs text-fg-dim space-y-1">
                {doc.heal_notes.map((n, i) => (
                  <li key={`n${i}`}>{n}</li>
                ))}
                {doc.heal_log.map((h, i) => (
                  <li key={`h${i}`}>
                    เปิด {h.target === "api" ? "ระบบหลังบ้าน" : "หน้าเว็บ"} ใหม่ — {ago(h.ts)}
                  </li>
                ))}
              </ul>
            </div>
          )}
          {doc.last_alerts.length > 0 && (
            <div>
              <h2 className="text-xs text-fg-mute mb-2 font-mono-num">แจ้งเตือนล่าสุดที่ส่ง LINE</h2>
              <ul className="text-xs text-fg-dim space-y-1">
                {doc.last_alerts.map((a, i) => (
                  <li key={i}>{a}</li>
                ))}
              </ul>
            </div>
          )}
        </section>
      )}
    </div>
  );
}

function CheckRow({ c }: { c: DoctorCheck }) {
  const { label, color, Icon } = STATUS[c.status];
  return (
    <li className="rounded-[var(--radius-card)] hairline bg-bg-card px-3.5 py-3 flex items-start gap-3">
      <Icon className="size-4 mt-0.5 shrink-0" style={{ color }} aria-hidden />
      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-2 flex-wrap">
          <span className="text-sm text-fg">{c.label}</span>
          <span className="font-mono-num text-[10px] uppercase tracking-wide px-1.5 py-0.5 rounded-[var(--radius-chip)]" style={{ color, background: `color-mix(in srgb, ${color} 14%, transparent)` }}>
            {label}
          </span>
        </div>
        <p className="text-xs text-fg-dim mt-0.5">{c.detail}</p>
        {c.fix && c.status !== "pass" && <p className="text-xs text-fg-mute mt-0.5">วิธีแก้: {c.fix}</p>}
      </div>
    </li>
  );
}
