"use client";

import { useEffect, useRef } from "react";
import { Input } from "@/components/ui/input";
import { FILTERS } from "@/lib/radar";

export function RadarFilters({
  filter,
  onFilter,
  query,
  onQuery,
  counts,
}: {
  filter: string;
  onFilter: (id: string) => void;
  query: string;
  onQuery: (q: string) => void;
  counts: Record<string, number>;
}) {
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      const el = e.target as HTMLElement | null;
      const typing =
        el?.tagName === "INPUT" || el?.tagName === "TEXTAREA" || el?.isContentEditable;
      if (e.key === "/" && !typing) {
        e.preventDefault();
        inputRef.current?.focus();
      }
      if (e.key === "Escape") {
        onQuery("");
        inputRef.current?.blur();
      }
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onQuery]);

  return (
    <div className="flex items-center justify-between gap-3 flex-wrap">
      <div className="flex items-center gap-1.5 flex-wrap">
        {FILTERS.map((f) => {
          const active = filter === f.id;
          return (
            <button
              key={f.id}
              type="button"
              onClick={() => onFilter(f.id)}
              aria-pressed={active}
              className={`inline-flex items-center min-h-10 md:min-h-0 px-3 md:px-2.5 py-1 rounded-[var(--radius-chip)] hairline hairline-hover text-[11px] tabular-nums cursor-pointer transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent/60 ${
                active
                  ? "bg-accent-soft text-fg border-accent/50"
                  : "text-fg-dim hover:text-fg"
              }`}
            >
              {f.label} · {counts[f.id] ?? 0}
            </button>
          );
        })}
      </div>
      <Input
        ref={inputRef}
        value={query}
        onChange={(e) => onQuery(e.target.value)}
        placeholder="ค้นหา · กด /"
        className="h-10 md:h-8 text-xs w-full sm:max-w-xs"
      />
    </div>
  );
}
