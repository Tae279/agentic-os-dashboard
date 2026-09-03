// API client for the FastAPI backend at 127.0.0.1:8787.
// Thin fetch wrappers + SSE helper — no state management here.

export const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "http://127.0.0.1:8787";

export type Skill = {
  id: string;
  label: string;
  description: string;
  category: string;
  input_placeholder?: string;
};

export type UsageResponse = {
  five_hour: { tokens: number; pct: number; limit: number; limit_fmt: string; sessions: number; resets_in: string };
  weekly: { tokens: number; pct: number; limit: number; limit_fmt: string; resets_in: string };
  today: { input: number; output: number; total: number; sessions: number; routines: number; cost: number; runs: number };
  value: { today_usd: number; month_usd: number; today_fmt: string; month_fmt: string };
  metrics: { runs_today: number; cost_month: number; tokens_30d: number; approvals: number };
};

export type LiveSession = { project: string; cwd: string; state: string; last: number; alive: boolean };
export type DevServer = { pid: string; port: number; cmd: string; cwd: string; framework: string };
export type Project = {
  name: string; tag: string; aliases: string; docs: string; code: string;
  priority: string; notes: string;
  latest_entry: { date: string; title: string; summary: string; tags: string; next: string } | null;
};
export type InboxItem = { text: string; source: string; file: string };
export type Recommendations = {
  must_do: { text: string; project: string }[];
  nice_to_do: { text: string; project: string }[];
  ideas: { text: string; why: string }[];
};
export type RunSummary = { file: string; path: string; skill: string | null; time: string | null; cost_usd: string | null; mtime: number };
export type Forecast = {
  burn_per_min: number; burn_fmt: string; elapsed_pct: number; proj_pct: number;
  state: "over_cap" | "under_cap"; headline: string; resets_in: string;
  schedule: { time: string; label: string; in: string }[];
};
export type ValueSeries = {
  today: number; yesterday: number; week_total: number;
  series: { label: string; value: number }[]; available: boolean;
};
export type Integration = { name: string; status: string };
export type VaultPulseItem = { verb: string; name: string; dir: string; age_sec: number; age_fmt: string; obsidian_uri: string };
export type ActivitySeries = { dates: string[]; day_counts: number[]; cumulative: number[]; total: number; last_30d: number };
export type RunsPerDay = { labels: string[]; values: number[]; total: number };

async function getJSON<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, { cache: "no-store" });
  if (!res.ok) throw new Error(`${path} -> ${res.status}`);
  return res.json();
}

export const api = {
  usage: () => getJSON<UsageResponse>("/api/usage"),
  sessions: () => getJSON<{ sessions: LiveSession[] }>("/api/sessions"),
  devservers: () => getJSON<{ servers: DevServer[] }>("/api/devservers"),
  projects: () => getJSON<{ projects: Project[] }>("/api/projects"),
  inbox: () => getJSON<{ items: InboxItem[] }>("/api/inbox"),
  artifacts: () => getJSON<{ recommendations: Recommendations }>("/api/artifacts"),
  runs: () => getJSON<{ runs: RunSummary[] }>("/api/runs"),
  skills: () => getJSON<{ skills: Skill[]; quick_routes: { label: string; path: string }[] }>("/api/skills"),
  usageCounts: () => getJSON<Record<string, number>>("/api/usage-counts"),
  runDetail: (file: string) => getJSON<{ content: string }>(`/api/runs/${encodeURIComponent(file)}`),
  open: (path: string) => fetch(`${API_BASE}/api/open`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ path }) }),
  kill: (pid: string) => fetch(`${API_BASE}/api/kill`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ pid }) }),
  forecast: () => getJSON<Forecast>("/api/forecast"),
  value: () => getJSON<ValueSeries>("/api/value"),
  integrations: () => getJSON<{ integrations: Integration[] }>("/api/integrations"),
  vaultPulse: () => getJSON<{ items: VaultPulseItem[] }>("/api/vault-pulse"),
  activity: () => getJSON<ActivitySeries>("/api/activity"),
  runsPerDay: () => getJSON<RunsPerDay>("/api/runs-per-day"),
  openTerminal: () => fetch(`${API_BASE}/api/open-terminal`, { method: "POST" }),
  radar: () => getJSON<RadarResponse>("/api/radar"),
  radarCheck: (key: string, checked: boolean) => fetch(`${API_BASE}/api/radar/check`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ key, checked }) }),
};

export type RadarStatus = "live" | "building" | "planning" | "behind" | "quiet";
export type RadarLink = { label: string; url: string };
export type RadarAction = { id: string; label: string; cwd: string; kind: "plan" | "git"; prompt: string };
export type RadarApp = { label: string; kind: "prod" | "local"; url: string; port?: number; cwd?: string; cmd?: string };
export type RadarChecklistItem = { id: string; text: string };
export type RadarProject = {
  id: string; code: string; name: string; status: RadarStatus; statusLabel: string;
  phase: string; progress: number; updated: string | null; next: string;
  waiting: "tae" | "external" | null; blocker: string | null; uncommitted?: boolean; gap?: boolean;
  prod: string | null; facts: string[]; rules: string[]; steps: string[]; links: RadarLink[]; src: string;
  actions: RadarAction[]; apps: RadarApp[]; tae_checklist: RadarChecklistItem[];
};
export type RadarDecision = { id: string; project: string; question: string; why: string; rec: string; cost: string; impact: 1 | 2 | 3 };
export type RadarEvent = { date: string; code: string; text: string };
export type RadarResponse = {
  version: number; verified: string; projects: RadarProject[]; decisions: RadarDecision[]; events: RadarEvent[];
  state: { checked: Record<string, boolean> };
};

export type SSEHandlers = {
  onPhase?: (data: { phase: string; label?: string }) => void;
  onText?: (data: { chunk: string }) => void;
  onTool?: (data: { name: string }) => void;
  onDone?: (data: Record<string, unknown>) => void;
  onError?: (err: unknown) => void;
};

/** Minimal SSE-over-fetch reader (EventSource can't POST, so we parse manually). */
export async function streamPost(path: string, body: Record<string, unknown>, handlers: SSEHandlers) {
  try {
    const res = await fetch(`${API_BASE}${path}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    if (!res.body) throw new Error("no response body");
    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buf = "";
    const dispatch = (raw: string) => {
      let event = "message";
      let data = "";
      for (const line of raw.split("\n")) {
        if (line.startsWith("event:")) event = line.slice(6).trim();
        if (line.startsWith("data:")) data += line.slice(5).trim();
      }
      if (!data) return;
      try {
        const parsed = JSON.parse(data);
        if (event === "phase") handlers.onPhase?.(parsed);
        else if (event === "text") handlers.onText?.(parsed);
        else if (event === "tool") handlers.onTool?.(parsed);
        else if (event === "done") handlers.onDone?.(parsed);
      } catch {
        /* ignore malformed chunk */
      }
    };
    for (;;) {
      const { done, value } = await reader.read();
      if (done) break;
      // sse-starlette separates lines with \r\n — normalise so the "\n\n" event split below works
      // (without this every event sat in `buf` until the stream closed → UI stuck on "starting").
      buf += decoder.decode(value, { stream: true }).replace(/\r\n/g, "\n");
      const events = buf.split("\n\n");
      buf = events.pop() || "";
      events.forEach(dispatch);
    }
    if (buf.trim()) dispatch(buf);
  } catch (err) {
    handlers.onError?.(err);
  }
}
