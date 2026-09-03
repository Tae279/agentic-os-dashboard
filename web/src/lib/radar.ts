import type { RadarProject, RadarResponse, RadarStatus } from "@/lib/api";

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

export const FILTERS: { id: string; label: string; f: (p: RadarProject) => boolean }[] = [
  { id: "all", label: "ทั้งหมด", f: () => true },
  {
    id: "attention",
    label: "ต้องดูวันนี้",
    f: (p) => p.status === "behind" || (p.waiting === "tae" && ATTENTION_IDS.includes(p.id)),
  },
  { id: "live", label: "ใช้งานจริง", f: (p) => !!p.prod },
  { id: "tae", label: "รอเต้", f: (p) => p.waiting === "tae" },
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
