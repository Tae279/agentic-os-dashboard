"use client";

import { Chip, ProgressBar, Table } from "@heroui/react";
import { AlertTriangle, Play, SearchX } from "lucide-react";
import type { RadarProject } from "@/lib/api";
import { ageLabel, daysAgo, statusColor, statusStripeClass } from "@/lib/radar";

function ageTone(age: number | null): string {
  if (age === null || age > 30) return "text-danger";
  if (age > 14) return "text-warn";
  return "text-fg-dim";
}

function StatusChips({ p }: { p: RadarProject }) {
  return (
    <>
      {p.waiting === "tae" && (
        <Chip size="sm" variant="soft" color="warning">
          รอเต้
        </Chip>
      )}
      {p.waiting === "external" && (
        <Chip size="sm" variant="soft" color="default">
          รอภายนอก
        </Chip>
      )}
      {p.uncommitted && (
        <Chip size="sm" variant="secondary" color="danger">
          ยังไม่ push
        </Chip>
      )}
      {p.actions.length > 0 && (
        <span
          role="img"
          aria-label="มีงานที่กดรันได้"
          title="มีงานที่กดรันได้"
          className="inline-flex items-center"
        >
          <Play size={10} aria-hidden className="text-accent" />
        </span>
      )}
    </>
  );
}

function EmptyState() {
  return (
    <div className="p-6">
      <SearchX size={28} aria-hidden className="text-fg-mute" />
      <p className="text-sm text-fg mt-2">ไม่มีโปรเจกต์ที่ตรง filter</p>
      <p className="text-xs text-fg-dim mt-1">ลองเลือก “ทั้งหมด” หรือล้างคำค้นหา (กด Esc)</p>
    </div>
  );
}

export function RadarTable({
  projects,
  onOpen,
  checked,
}: {
  projects: RadarProject[];
  onOpen: (id: string) => void;
  checked: Record<string, boolean>;
}) {
  void checked;
  return (
    <>
      {/* mobile: the 6-column table cannot fit 390px — same data as cards */}
      <div className="md:hidden">
        {projects.length === 0 ? (
          <div className="rounded-[var(--radius-card)] hairline bg-bg-card">
            <EmptyState />
          </div>
        ) : (
          <ul className="space-y-2">
            {projects.map((p) => {
              const age = daysAgo(p.updated);
              return (
                <li key={p.id}>
                  <button
                    type="button"
                    onClick={() => onOpen(p.id)}
                    className={`w-full text-left rounded-[var(--radius-card)] hairline hairline-hover bg-bg-card p-3 border-l-[3px] cursor-pointer transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent/60 ${statusStripeClass(
                      p.status,
                    )}`}
                  >
                    <div className="flex flex-wrap items-center gap-1">
                      <Chip size="sm" variant="soft" color={statusColor(p.status)}>
                        {p.statusLabel}
                      </Chip>
                      <StatusChips p={p} />
                    </div>
                    <div className="font-mono-num text-[11px] text-fg-mute uppercase mt-2">
                      {p.code}
                    </div>
                    <div className="font-display text-sm text-fg">{p.name}</div>
                    <div className="flex items-center gap-2 mt-1.5">
                      <ProgressBar
                        size="sm"
                        color={statusColor(p.status)}
                        value={p.progress}
                        aria-label="ความคืบหน้า"
                        className="flex-1"
                      >
                        <ProgressBar.Track>
                          <ProgressBar.Fill />
                        </ProgressBar.Track>
                      </ProgressBar>
                      <span className="tabular-nums text-[11px] text-fg-dim shrink-0">
                        {p.progress}%
                      </span>
                    </div>
                    <p className="text-xs text-fg-dim line-clamp-2 mt-1.5">{p.next}</p>
                    {p.blocker ? (
                      <p className="flex items-start gap-1.5 text-xs text-danger line-clamp-2 mt-1">
                        <AlertTriangle size={12} aria-hidden className="mt-0.5 shrink-0" />
                        <span>{p.blocker}</span>
                      </p>
                    ) : null}
                    <div className="flex items-center gap-2 mt-2 text-[11px] tabular-nums">
                      <span className="text-fg-dim">{p.updated ?? "—"}</span>
                      <span className={ageTone(age)}>{ageLabel(age)}</span>
                    </div>
                  </button>
                </li>
              );
            })}
          </ul>
        )}
      </div>

      <Table
        variant="secondary"
        className="hidden md:block rounded-[var(--radius-card)] hairline bg-bg-card overflow-hidden"
      >
        <Table.ScrollContainer>
          <Table.Content
            aria-label="โปรเจกต์"
            selectionMode="single"
            selectedKeys={new Set<string>()}
            onSelectionChange={(keys) => {
              const k = keys === "all" ? null : [...keys][0];
              if (k) onOpen(String(k));
            }}
            className="min-w-[960px]"
          >
            <Table.Header>
              <Table.Column isRowHeader>สถานะ</Table.Column>
              <Table.Column>โปรเจกต์</Table.Column>
              <Table.Column>เฟส</Table.Column>
              <Table.Column>ขั้นต่อไป</Table.Column>
              <Table.Column>ติดอะไร</Table.Column>
              <Table.Column>อัปเดต</Table.Column>
            </Table.Header>
            <Table.Body items={projects} renderEmptyState={() => <EmptyState />}>
              {(p) => {
                const age = daysAgo(p.updated);
                return (
                  <Table.Row id={p.id} className="cursor-pointer">
                    <Table.Cell>
                      <div className={`border-l-[3px] pl-2 ${statusStripeClass(p.status)}`}>
                        <Chip size="sm" variant="soft" color={statusColor(p.status)}>
                          {p.statusLabel}
                        </Chip>
                        <div className="flex flex-wrap gap-1 mt-1">
                          <StatusChips p={p} />
                        </div>
                      </div>
                    </Table.Cell>
                    <Table.Cell>
                      <div className="font-mono-num text-[11px] text-fg-mute uppercase">{p.code}</div>
                      <div className="font-display text-sm text-fg">{p.name}</div>
                    </Table.Cell>
                    <Table.Cell>
                      <div className="text-xs text-fg">{p.phase}</div>
                      <ProgressBar
                        size="sm"
                        color={statusColor(p.status)}
                        value={p.progress}
                        aria-label="ความคืบหน้า"
                      >
                        <ProgressBar.Track>
                          <ProgressBar.Fill />
                        </ProgressBar.Track>
                      </ProgressBar>
                      <div className="tabular-nums text-[11px] text-fg-dim">{p.progress}%</div>
                    </Table.Cell>
                    <Table.Cell>
                      <div className="text-xs text-fg-dim line-clamp-2 max-w-[320px]">{p.next}</div>
                    </Table.Cell>
                    <Table.Cell>
                      {p.blocker ? (
                        <div className="flex items-start gap-1.5 text-xs text-danger max-w-[280px]">
                          <AlertTriangle size={12} aria-hidden className="mt-0.5 shrink-0" />
                          <span className="line-clamp-2">{p.blocker}</span>
                        </div>
                      ) : (
                        <span className="text-xs text-fg-mute">—</span>
                      )}
                    </Table.Cell>
                    <Table.Cell>
                      <div className="tabular-nums text-[11px] text-fg whitespace-nowrap">
                        {p.updated ?? "—"}
                      </div>
                      <div className={`text-[11px] tabular-nums whitespace-nowrap ${ageTone(age)}`}>
                        {ageLabel(age)}
                      </div>
                    </Table.Cell>
                  </Table.Row>
                );
              }}
            </Table.Body>
          </Table.Content>
        </Table.ScrollContainer>
      </Table>
    </>
  );
}
