// Run from web/: node src/lib/radar.test.mjs
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import ts from "typescript";

const source = readFileSync(new URL("./radar.ts", import.meta.url), "utf8");
const { outputText } = ts.transpileModule(source, { compilerOptions: { module: ts.ModuleKind.ESNext } });
const radar = await import(`data:text/javascript;base64,${Buffer.from(outputText).toString("base64")}`);
const project = (values = {}) => ({ status: "building", waiting: null, progress: 50, ...values });
const statuses = ["live", "building", "behind", "quiet", "planning"];
const projects = statuses.map((status) => project({ code: status, status }));

assert.deepEqual(radar.statusCounts(projects), { live: 1, building: 1, behind: 1, quiet: 1, planning: 1 });
assert.deepEqual(radar.statusCounts([]), { live: 0, building: 0, behind: 0, quiet: 0, planning: 0 });
assert.deepEqual(radar.waitingCounts([project(), project({ waiting: "tae" }), project({ waiting: "external" })]), { agent: 1, tae: 1, external: 1 });
assert.deepEqual(radar.waitingCounts([]), { agent: 0, tae: 0, external: 0 });
assert.equal(radar.waitingKey(project()), "agent");
assert.equal(radar.portfolioProgress([project({ progress: 10 }), project({ progress: 81 }), project({ progress: 0, gap: true })]), 46);
assert.equal(radar.portfolioProgress([]), 0);
assert.equal(radar.portfolioProgress([project({ gap: true })]), 0);
assert.deepEqual([
  project({ status: "behind", waiting: "tae", uncommitted: true }),
  project({ waiting: "tae", uncommitted: true }),
  project({ uncommitted: true }), project(), project({ status: "live" }),
  project({ status: "quiet" }), project({ gap: true, status: "behind" }),
].map(radar.attentionRank), [0, 1, 2, 3, 4, 5, 6]);
assert.equal(radar.attentionRank(project({ status: "planning" })), 5);
assert.deepEqual(["ALL", ...statuses, "unknown"].map((code) => radar.eventStatus({ code }, projects)), ["current", "success", "current", "danger", "warning", "default", "muted"]);
const today = new Date(2026, 0, 2);
assert.deepEqual(radar.activityStrip([{ date: "2025-12-31" }, { date: "2025-12-31" }, { date: "2026-01-02" }, { date: "2026-01-03" }], 3, today), [
  { date: "2025-12-31", count: 2 }, { date: "2026-01-01", count: 0 }, { date: "2026-01-02", count: 1 },
]);
assert.equal(radar.activityStrip([], undefined, today).length, 14);
assert.deepEqual(radar.activityStrip([], 0, today), []);
const taeIndex = radar.FILTERS.findIndex((f) => f.id === "tae");
assert.equal(radar.FILTERS[taeIndex + 1].id, "external");
assert.equal(radar.FILTERS[taeIndex + 1].f(project({ waiting: "external" })), true);
assert.equal(radar.FILTERS[taeIndex + 1].f(project()), false);
assert.equal(typeof radar.kpis, "function");
console.log("PASS radar helpers: counts, progress, attention precedence, event status, activity dates, external filter, retained kpis");
