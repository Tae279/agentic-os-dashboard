"use client";

import { Chip, Drawer } from "@heroui/react";
import { ExternalLink } from "lucide-react";
import type { RadarProject } from "@/lib/api";
import { ageLabel, daysAgo, statusColor } from "@/lib/radar";

function Section({
  label,
  hide,
  children,
}: {
  label: string;
  hide?: boolean;
  children: React.ReactNode;
}) {
  if (hide) return null;
  return (
    <div>
      <div className="text-[11px] uppercase tracking-[0.14em] text-fg-mute mb-1.5">{label}</div>
      {children}
    </div>
  );
}

export function RadarDrawer({
  project,
  onClose,
  children,
  footer,
}: {
  project: RadarProject | null;
  onClose: () => void;
  children?: React.ReactNode;
  footer?: React.ReactNode;
}) {
  const age = daysAgo(project?.updated ?? null);

  return (
    <Drawer.Backdrop
      isOpen={!!project}
      onOpenChange={(o) => {
        if (!o) onClose();
      }}
      variant="blur"
    >
      <Drawer.Content placement="right" className="w-full sm:max-w-xl left-auto">
        <Drawer.Dialog className="bg-bg-elev text-fg">
          {project && (
            <>
              <Drawer.Header className="flex items-start justify-between gap-3">
                <div className="min-w-0">
                  <div className="flex items-center gap-1.5 flex-wrap mb-1">
                    <span className="font-mono-num text-[11px] text-fg-mute uppercase">
                      {project.code}
                    </span>
                    <Chip size="sm" variant="soft" color={statusColor(project.status)}>
                      {project.statusLabel}
                    </Chip>
                    {project.waiting === "tae" && (
                      <Chip size="sm" variant="soft" color="warning">
                        รอเต้
                      </Chip>
                    )}
                    {project.waiting === "external" && (
                      <Chip size="sm" variant="soft" color="default">
                        รอภายนอก
                      </Chip>
                    )}
                    {project.uncommitted && (
                      <Chip size="sm" variant="secondary" color="danger">
                        ยังไม่ push
                      </Chip>
                    )}
                  </div>
                  <Drawer.Heading className="font-display text-lg font-semibold">
                    {project.name}
                  </Drawer.Heading>
                  <div className="text-[11px] text-fg-dim font-mono-num mt-1">
                    {project.phase} · {project.progress}% · {project.updated ?? "—"} ({ageLabel(age)})
                  </div>
                </div>
                <Drawer.CloseTrigger />
              </Drawer.Header>
              <Drawer.Body className="space-y-4">
                {children}
                <Section label="ขั้นต่อไป" hide={!project.next}>
                  <p className="text-sm text-fg">{project.next}</p>
                </Section>
                <Section label="ติดอะไร" hide={!project.blocker}>
                  <p className="text-sm text-danger">{project.blocker}</p>
                </Section>
                <Section label="ข้อเท็จจริง" hide={project.facts.length === 0}>
                  <ul className="list-disc pl-4 text-xs text-fg-dim space-y-1">
                    {project.facts.map((item) => (
                      <li key={item}>{item}</li>
                    ))}
                  </ul>
                </Section>
                <Section label="กติกา" hide={project.rules.length === 0}>
                  <ul className="list-disc pl-4 text-xs text-fg-dim space-y-1">
                    {project.rules.map((item) => (
                      <li key={item}>{item}</li>
                    ))}
                  </ul>
                </Section>
                <Section label="ลำดับงาน" hide={project.steps.length === 0}>
                  <ol className="list-decimal pl-4 text-xs text-fg-dim space-y-1">
                    {project.steps.map((item) => (
                      <li key={item}>{item}</li>
                    ))}
                  </ol>
                </Section>
                <Section label="ลิงก์" hide={project.links.length === 0}>
                  <div className="flex flex-wrap gap-1.5">
                    {project.links.map((link) => (
                      <a
                        key={link.url}
                        href={link.url}
                        target="_blank"
                        rel="noreferrer"
                        className="inline-flex items-center gap-1 px-2.5 py-1 rounded-[var(--radius-chip)] hairline hairline-hover text-[11px] text-fg-dim hover:text-fg"
                      >
                        {link.label}
                        <ExternalLink size={12} />
                      </a>
                    ))}
                  </div>
                </Section>
                <Section label="ที่มา" hide={!project.src}>
                  <p className="font-mono-num text-[11px] text-fg-mute">{project.src}</p>
                </Section>
                {footer ? (
                  <div className="border-t border-ring-soft pt-4 mt-4">{footer}</div>
                ) : null}
              </Drawer.Body>
            </>
          )}
        </Drawer.Dialog>
      </Drawer.Content>
    </Drawer.Backdrop>
  );
}
