"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { Tabs } from "@heroui/react";
import { api, streamPost, type DevServer, type RadarAction, type RadarProject, type RadarResponse } from "@/lib/api";
import { FILTERS, kpis, type RadarRun } from "@/lib/radar";
import { Mascot } from "@/components/dashboard/quick-nav";
import { RunOutput } from "@/components/dashboard/run-output";
import { ActionBar } from "@/components/radar/action-bar";
import { AppButtons } from "@/components/radar/app-buttons";
import { RadarKpis } from "@/components/radar/radar-kpis";
import { RadarFilters } from "@/components/radar/radar-filters";
import { RadarTable } from "@/components/radar/radar-table";
import { RadarDrawer } from "@/components/radar/radar-drawer";
import { TaeChecklist } from "@/components/radar/tae-checklist";
import { DecisionCards } from "@/components/radar/decision-cards";
import { Timeline } from "@/components/radar/timeline";

type TabKey = "projects" | "decisions" | "timeline";

export default function RadarPage() {
  const [data, setData] = useState<RadarResponse | null>(null);
  const [tab, setTab] = useState<TabKey>("projects");
  const [filter, setFilter] = useState("all");
  const [query, setQuery] = useState("");
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [run, setRun] = useState<RadarRun | null>(null);
  const [devservers, setDevservers] = useState<DevServer[]>([]);

  const refresh = useCallback(async () => {
    const [r, ds] = await Promise.allSettled([api.radar(), api.devservers()]);
    if (r.status === "fulfilled") setData(r.value);
    if (ds.status === "fulfilled") setDevservers(ds.value.servers);
  }, []);

  const startAction = useCallback(async (project: RadarProject, action: RadarAction) => {
    let blocked = false;
    setRun((current) => {
      if (current && !current.done) {
        blocked = true;
        return current;
      }
      return {
        actionId: action.id,
        label: "Radar · " + action.label,
        text: "",
        phase: "starting",
        pid: null,
        done: false,
        ok: null,
        error: null,
        cost: null,
        savedPath: null,
      };
    });
    if (blocked) return;

    await streamPost(
      "/api/run",
      { skill_label: "Radar · " + action.label, prompt: action.prompt, cwd: action.cwd },
      {
        onPhase: (d) =>
          setRun((r) =>
            r
              ? { ...r, phase: d.phase, pid: (d as { pid?: number }).pid ?? r.pid }
              : r,
          ),
        onText: (d) => setRun((r) => (r ? { ...r, text: r.text + d.chunk } : r)),
        onDone: (d) =>
          setRun((r) =>
            r
              ? {
                  ...r,
                  done: true,
                  ok: !!d.ok,
                  error: (d.error as string) ?? null,
                  cost: (d.cost_usd as number) ?? null,
                  savedPath: (d.saved_path as string) ?? null,
                }
              : r,
          ),
        onError: (e) =>
          setRun((r) => (r ? { ...r, done: true, ok: false, error: String(e) } : r)),
      },
    );

    setRun((r) =>
      r && !r.done
        ? {
            ...r,
            done: true,
            ok: false,
            error: "ไม่ได้รับอนุญาตให้รันใน cwd นี้ (403) หรือ server ตัดการเชื่อมต่อ",
          }
        : r,
    );
    void project;
  }, []);

  const stopRun = useCallback(async () => {
    setRun((current) => {
      if (current?.pid) void api.kill(String(current.pid));
      return current
        ? { ...current, done: true, ok: false, error: "หยุดโดยเต้" }
        : current;
    });
  }, []);

  const toggleCheck = useCallback(async (key: string, next: boolean) => {
    const previous = !!data?.state.checked[key];
    setData((d) => {
      if (!d) return d;
      const checked = { ...d.state.checked };
      if (next) checked[key] = true;
      else delete checked[key];
      return { ...d, state: { ...d.state, checked } };
    });
    try {
      const res = await api.radarCheck(key, next);
      if (!res.ok) throw new Error(`radar check -> ${res.status}`);
    } catch {
      setData((d) => {
        if (!d) return d;
        const checked = { ...d.state.checked };
        if (previous) checked[key] = true;
        else delete checked[key];
        return { ...d, state: { ...d.state, checked } };
      });
    }
  }, [data]);

  useEffect(() => {
    refresh();
    const id = setInterval(refresh, 30_000);
    return () => clearInterval(id);
  }, [refresh]);

  const counts = useMemo(() => {
    const projects = data?.projects ?? [];
    return Object.fromEntries(FILTERS.map((f) => [f.id, projects.filter(f.f).length]));
  }, [data]);

  const visible = useMemo(() => {
    if (!data) return [];
    const pred = FILTERS.find((f) => f.id === filter)?.f ?? (() => true);
    const q = query.trim().toLowerCase();
    return data.projects.filter((p) => {
      if (!pred(p)) return false;
      if (!q) return true;
      return [p.name, p.code, p.phase, p.next, p.statusLabel].some((s) =>
        s.toLowerCase().includes(q),
      );
    });
  }, [data, filter, query]);

  const selected = data?.projects.find((p) => p.id === selectedId) ?? null;
  const kpiItems = data ? kpis(data) : [];

  return (
    <div className="flex-1 flex flex-col overflow-x-hidden">
      <header className="px-6 pt-6 pb-3">
        <div className="flex items-center justify-between mb-4 gap-3 flex-wrap">
          <div className="flex items-center gap-3">
            <Mascot />
            <div>
              <h1 className="font-display text-lg font-semibold text-fg">DX Agentic OS</h1>
              <p className="text-xs text-fg-mute">Project Radar · เต้</p>
            </div>
          </div>
          <div className="flex items-center gap-3 flex-wrap">
            <nav className="flex items-center gap-1 text-xs">
              <Link
                href="/"
                className="inline-flex items-center min-h-10 md:min-h-0 px-3 py-1.5 rounded-[var(--radius-chip)] text-fg-dim hover:text-fg hover:bg-bg-card transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent/60"
              >
                launcher
              </Link>
              <Link
                href="/portfolio"
                className="inline-flex items-center min-h-10 md:min-h-0 px-3 py-1.5 rounded-[var(--radius-chip)] text-fg-dim hover:text-fg hover:bg-bg-card transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent/60"
              >
                portfolio
              </Link>
              <span aria-current="page" className="inline-flex items-center min-h-10 md:min-h-0 px-3 py-1.5 rounded-[var(--radius-chip)] hairline bg-bg-card text-fg">
                radar
              </span>
              <Link
                href="/health"
                className="inline-flex items-center min-h-10 md:min-h-0 px-3 py-1.5 rounded-[var(--radius-chip)] text-fg-dim hover:text-fg hover:bg-bg-card transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent/60"
              >
                ตรวจระบบ
              </Link>
            </nav>
            <span className="font-mono-num text-[11px] text-fg-dim">
              ข้อมูล verified {data?.verified ?? "—"}
            </span>
          </div>
        </div>
      </header>

      <main className="flex-1 px-6 pb-8 space-y-4 min-w-0">
        {!data ? (
          <>
            <div className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-6 gap-3">
              {Array.from({ length: 6 }).map((_, i) => (
                <div
                  key={i}
                  className="h-24 rounded-[var(--radius-card)] hairline bg-bg-card/60 animate-pulse"
                />
              ))}
            </div>
            <div className="h-64 rounded-[var(--radius-card)] hairline bg-bg-card/60 animate-pulse" />
          </>
        ) : (
          <>
            <RunOutput
              label={run ? run.label : null}
              text={run?.text ?? ""}
              phase={run?.phase ?? null}
              onClose={() => setRun(null)}
            />
            <RadarKpis
              items={kpiItems}
              activeFilter={filter}
              onPick={(k) => {
                if (k.tab) setTab(k.tab);
                if (k.filter) {
                  setFilter(k.filter);
                  setTab("projects");
                }
              }}
            />

            <Tabs
              variant="secondary"
              selectedKey={tab}
              onSelectionChange={(key) => {
                if (key === "projects" || key === "decisions" || key === "timeline") {
                  setTab(key);
                }
              }}
            >
              <Tabs.ListContainer>
                <Tabs.List aria-label="Radar views">
                  <Tabs.Tab id="projects" className="min-h-11 md:min-h-0" style={{ width: "auto" }}>
                    โปรเจกต์
                    <Tabs.Indicator />
                  </Tabs.Tab>
                  <Tabs.Tab id="decisions" className="min-h-11 md:min-h-0" style={{ width: "auto" }}>
                    {`รอเต้ตัดสินใจ (${data.decisions.length})`}
                    <Tabs.Indicator />
                  </Tabs.Tab>
                  <Tabs.Tab id="timeline" className="min-h-11 md:min-h-0" style={{ width: "auto" }}>
                    ไทม์ไลน์
                    <Tabs.Indicator />
                  </Tabs.Tab>
                </Tabs.List>
              </Tabs.ListContainer>
              <Tabs.Panel id="projects" className="space-y-3 pt-4">
                <RadarFilters
                  filter={filter}
                  onFilter={setFilter}
                  query={query}
                  onQuery={setQuery}
                  counts={counts}
                />
                <RadarTable
                  projects={visible}
                  onOpen={setSelectedId}
                  checked={data.state.checked}
                />
              </Tabs.Panel>
              <Tabs.Panel id="decisions" className="pt-4">
                <DecisionCards
                  decisions={data.decisions}
                  projects={data.projects}
                  checked={data.state.checked}
                  onToggle={toggleCheck}
                  onOpenProject={setSelectedId}
                />
              </Tabs.Panel>
              <Tabs.Panel id="timeline" className="pt-4">
                <Timeline
                  events={data.events}
                  projects={data.projects}
                  onOpenProject={setSelectedId}
                />
              </Tabs.Panel>
            </Tabs>
          </>
        )}
      </main>

      <RadarDrawer
        project={selected}
        onClose={() => setSelectedId(null)}
        footer={
          selected && selected.tae_checklist.length > 0 ? (
            <TaeChecklist
              items={selected.tae_checklist}
              checked={data?.state.checked ?? {}}
              onToggle={toggleCheck}
            />
          ) : undefined
        }
      >
        {selected && selected.actions.length > 0 ? (
          <ActionBar
            project={selected}
            run={run}
            onStart={(a) => {
              void startAction(selected, a);
            }}
            onStop={() => {
              void stopRun();
            }}
          />
        ) : null}
        {selected && selected.apps.length > 0 ? (
          <AppButtons apps={selected.apps} devservers={devservers} />
        ) : null}
      </RadarDrawer>
    </div>
  );
}
