"use client";

import { useEffect, useState } from "react";
import { Command } from "cmdk";
import type { Skill } from "@/lib/api";

export function CommandPalette({
  skills,
  onSelect,
  pages = [],
}: {
  skills: Skill[];
  onSelect: (skill: Skill) => void;
  pages?: { label: string; description: string; href: string }[];
}) {
  const [open, setOpen] = useState(false);

  useEffect(() => {
    const down = (e: KeyboardEvent) => {
      if (e.key === "k" && (e.metaKey || e.ctrlKey)) {
        e.preventDefault();
        setOpen((o) => !o);
      }
      if (e.key === "Escape") setOpen(false);
    };
    document.addEventListener("keydown", down);
    return () => document.removeEventListener("keydown", down);
  }, []);

  if (!open) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-start justify-center pt-[15vh] bg-black/60 backdrop-blur-sm"
      onClick={() => setOpen(false)}
    >
      <div onClick={(e) => e.stopPropagation()} className="w-full max-w-lg">
        <Command
          className="rounded-[var(--radius-card)] hairline bg-bg-card-hi overflow-hidden shadow-2xl"
          shouldFilter
        >
          <Command.Input
            autoFocus
            placeholder="ค้นหา workflow…"
            className="w-full px-4 py-3 bg-transparent text-fg placeholder:text-fg-mute focus:outline-none border-b border-ring-soft text-sm"
          />
          <Command.List className="max-h-80 overflow-y-auto p-2">
            <Command.Empty className="text-xs text-fg-mute px-3 py-4 text-center">
              ไม่พบ workflow ที่ตรงกัน
            </Command.Empty>
            <Command.Group heading="หน้า">
              {pages.map((page) => (
                <Command.Item
                  key={page.href}
                  value={`${page.label} ${page.description}`}
                  onSelect={() => {
                    window.location.assign(page.href);
                    setOpen(false);
                  }}
                  className="px-3 py-2 rounded-[var(--radius-chip)] text-sm text-fg cursor-pointer data-[selected=true]:bg-accent-soft flex items-center justify-between gap-2"
                >
                  <span className="font-display">{page.label}</span>
                  <span className="text-[11px] text-fg-mute truncate">{page.description}</span>
                </Command.Item>
              ))}
            </Command.Group>
            <Command.Group heading="workflow">
              {skills.map((skill) => (
                <Command.Item
                  key={skill.id}
                  value={`${skill.label} ${skill.description}`}
                  onSelect={() => {
                    onSelect(skill);
                    setOpen(false);
                  }}
                  className="px-3 py-2 rounded-[var(--radius-chip)] text-sm text-fg cursor-pointer data-[selected=true]:bg-accent-soft flex items-center justify-between gap-2"
                >
                  <span className="font-display">{skill.label}</span>
                  <span className="text-[11px] text-fg-mute truncate">{skill.description}</span>
                </Command.Item>
              ))}
            </Command.Group>
          </Command.List>
        </Command>
      </div>
    </div>
  );
}
