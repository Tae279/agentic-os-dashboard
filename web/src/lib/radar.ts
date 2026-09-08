import type { RadarEvent, RadarProject, RadarResponse, RadarStatus } from "@/lib/api";

export type RadarRun = {
  actionId: string;
  label: string;
  text: string;
  phase: string | null;
  pid: number | null;
  done: boolean;
  ok: boolean | null;
  error: string | null;
  cost: number | null;
  savedPath: string | null;
};

export function daysAgo(d: string | null, today = new Date()): number | null {
  if (!d) return null;
  const date = new Date(d);
  if (Number.isNaN(date.getTime())) return null;
  const startToday = Date.UTC(today.getFullYear(), today.getMonth(), today.getDate());
  const startDate = Date.UTC(date.getFullYear(), date.getMonth(), date.getDate());
  return Math.round((startToday - startDate) / 86_400_000);
}

export function ageLabel(n: number | null): string {
  if (n === null) return "ไม่มีวันที่";
  if (n === 0) return "วันนี้";
  return `${n} วันก่อน`;
}

export const STATUS_LABEL: Record<RadarStatus, string> = {
  live: "ใช้งานจริง",
  building: "กำลังสร้าง",
  planning: "รอแผน",
  behind: "prod ตามหลัง",
  quiet: "เงียบ",
};

export function statusColor(
  s: RadarStatus,
): "success" | "accent" | "default" | "danger" | "warning" {
  switch (s) {
    case "live":
      return "success";
    case "building":
      return "accent";
    case "planning":
      return "default";
    case "behind":
      return "danger";
    case "quiet":
      return "warning";
  }
}

export function statusStripeClass(s: RadarStatus): string {
  switch (s) {
    case "live":
      return "border-l-good";
    case "building":
      return "border-l-accent";
    case "planning":
      return "border-l-ring-mid";
    case "behind":
      return "border-l-danger";
    case "quiet":
      return "border-l-warn";
  }
}

const ATTENTION_IDS = ["landing", "support", "lineoa"];

export type WaitingKey = "tae" | "external" | "agent";

export function waitingKey(p: RadarProject): WaitingKey {
  return p.waiting ?? "agent";
}

export const WAITING_LABEL: Record<WaitingKey, string> = {
  tae: "รอเต้",
  external: "รอภายนอก",
  agent: "agent ทำต่อได้",
};

export function statusCounts(projects: RadarProject[]): Record<RadarStatus, number> {
  const counts: Record<RadarStatus, number> = { live: 0, building: 0, behind: 0, quiet: 0, planning: 0 };
  for (const project of projects) counts[project.status]++;
  return counts;
}

export function waitingCounts(projects: RadarProject[]): Record<WaitingKey, number> {
  const counts: Record<WaitingKey, number> = { tae: 0, external: 0, agent: 0 };
  for (const project of projects) counts[waitingKey(project)]++;
  return counts;
}

export function portfolioProgress(projects: RadarProject[]): number {
  const tracked = projects.filter((p) => !p.gap);
  return tracked.length ? Math.round(tracked.reduce((sum, p) => sum + p.progress, 0) / tracked.length) : 0;
}

export function attentionRank(p: RadarProject): number {
  if (p.gap) return 6;
  if (p.status === "behind") return 0;
  if (p.waiting === "tae") return 1;
  if (p.uncommitted) return 2;
  if (p.status === "building") return 3;
  if (p.status === "live") return 4;
  return 5;
}

export function eventStatus(
  e: RadarEvent,
  projects: RadarProject[],
): "default" | "current" | "success" | "warning" | "danger" | "muted" {
  if (e.code === "ALL") return "current";
  const project = projects.find((p) => p.code === e.code);
  if (!project) return "muted";
  const color = statusColor(project.status);
  return color === "accent" ? "current" : color;
}

export function activityStrip(events: RadarEvent[], days = 14, today = new Date()): { date: string; count: number }[] {
  const counts = new Map<string, number>();
  for (const event of events) counts.set(event.date, (counts.get(event.date) ?? 0) + 1);
  const end = Date.UTC(today.getFullYear(), today.getMonth(), today.getDate());
  return Array.from({ length: days }, (_, index) => {
    const date = new Date(end - (days - 1 - index) * 86_400_000).toISOString().slice(0, 10);
    return { date, count: counts.get(date) ?? 0 };
  });
}

export const FILTERS: { id: string; label: string; f: (p: RadarProject) => boolean }[] = [
  { id: "all", label: "ทั้งหมด", f: () => true },
  {
    id: "attention",
    label: "ต้องดูวันนี้",
    f: (p) => p.status === "behind" || (p.waiting === "tae" && ATTENTION_IDS.includes(p.id)),
  },
  { id: "live", label: "ใช้งานจริง", f: (p) => !!p.prod },
  { id: "tae", label: "รอเต้", f: (p) => p.waiting === "tae" },
  { id: "external", label: "รอภายนอก", f: (p) => p.waiting === "external" },
  { id: "uncommitted", label: "ยังไม่ push", f: (p) => !!p.uncommitted },
  { id: "behind", label: "prod ตามหลัง", f: (p) => p.status === "behind" },
  {
    id: "quiet",
    label: "เงียบ",
    f: (p) => {
      const age = daysAgo(p.updated);
      return p.status === "quiet" || age === null || age > 30;
    },
  },
];

export function kpis(data: RadarResponse) {
  const gapCount = data.projects.filter((p) => p.gap).length;
  const prodCount = data.projects.filter((p) => !!p.prod).length;
  const impact3 = data.decisions.filter((d) => d.impact === 3).length;
  const behindCount = data.projects.filter((p) => p.status === "behind").length;
  const uncommittedCount = data.projects.filter((p) => p.uncommitted).length;
  const quietCount = data.projects.filter((p) => {
    const age = daysAgo(p.updated);
    return age === null || age > 30;
  }).length;

  return [
    {
      id: "tracked",
      label: "โปรเจกต์ที่ติดตาม",
      value: data.projects.length,
      sub: `${gapCount} ไม่มีไฟล์สถานะ`,
      filter: "all",
    },
    {
      id: "prod",
      label: "ใช้งานจริงบน prod",
      value: prodCount,
      sub: "มี URL ที่เปิดได้",
      tone: "good" as const,
      filter: "live",
    },
    {
      id: "decisions",
      label: "รอเต้ตัดสินใจ",
      value: data.decisions.length,
      sub: `${impact3} เรื่องผลกระทบสูง`,
      tone: "warn" as const,
      tab: "decisions" as const,
    },
    {
      id: "behind",
      label: "prod ตามหลังโค้ด",
      value: behindCount,
      sub: "บั๊กที่แก้แล้วยังอยู่บนของจริง",
      tone: "danger" as const,
      filter: "behind",
    },
    {
      id: "uncommitted",
      label: "งานยังไม่ push",
      value: uncommittedCount,
      sub: "เสี่ยงหายถ้าเครื่องพัง",
      tone: "warn" as const,
      filter: "uncommitted",
    },
    {
      id: "quiet",
      label: "เงียบ > 30 วัน",
      value: quietCount,
      sub: "ไม่มีอัปเดตในไฟล์",
      filter: "quiet",
    },
  ];
}
