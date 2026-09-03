"use client";

import { Chip, ProgressBar, Table } from "@heroui/react";
import { Play } from "lucide-react";
import type { RadarProject } from "@/lib/api";
import { ageLabel, daysAgo, statusColor, statusStripeClass } from "@/lib/radar";

function ageTone(age: number | null): string {
  if (age === null || age > 30) return "text-danger";
  if (age > 14) return "text-warn";
  return "text-fg-dim";
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
    <Table variant="secondary" className="rounded-[var(--radius-card)] hairline bg-bg-card overflow-hidden">
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
          <Table.Body
            items={projects}
            renderEmptyState={() => (
              <div className="text-sm text-fg-dim py-8 text-center">ไม่มีโปรเจกต์ที่ตรง filter</div>
            )}
          >
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
                          <span title="มีงานที่กดรันได้" className="inline-flex"><Play size={10} className="text-accent" /></span>
                        )}
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
                      aria-label="progress"
                    >
                      <ProgressBar.Track>
                        <ProgressBar.Fill />
                      </ProgressBar.Track>
                    </ProgressBar>
                    <div className="font-mono-num text-[11px] text-fg-dim">{p.progress}%</div>
                  </Table.Cell>
                  <Table.Cell>
                    <div className="text-xs text-fg-dim line-clamp-2 max-w-[320px]">{p.next}</div>
                  </Table.Cell>
                  <Table.Cell>
                    {p.blocker ? (
                      <div className="text-xs text-danger line-clamp-2">{p.blocker}</div>
                    ) : (
                      <span className="text-xs text-fg-mute">—</span>
                    )}
                  </Table.Cell>
                  <Table.Cell>
                    <div className="font-mono-num text-[11px] text-fg">{p.updated ?? "—"}</div>
                    <div className={`text-[11px] ${ageTone(age)}`}>{ageLabel(age)}</div>
                  </Table.Cell>
                </Table.Row>
              );
            }}
          </Table.Body>
        </Table.Content>
      </Table.ScrollContainer>
    </Table>
  );
}
