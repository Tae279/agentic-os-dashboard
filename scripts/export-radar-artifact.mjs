#!/usr/bin/env node
// Export dashboard-data/radar.json → single-file read-only HTML snapshot (same look as the v1 artifact).
// Usage: node scripts/export-radar-artifact.mjs [out.html]
// Template = the v1 artifact; we swap its inline P / DECISIONS / EVENTS arrays for radar.json data.
import { readFileSync, writeFileSync } from "node:fs";
import { homedir } from "node:os";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const root = join(dirname(fileURLToPath(import.meta.url)), "..");
const TEMPLATE = join(homedir(), "Documents/DX/artifacts/2026-09-02-dx-project-radar.html");
const today = new Date().toISOString().slice(0, 10);
const out = process.argv[2] ?? join(homedir(), `Documents/DX/artifacts/${today}-dx-project-radar.html`);

const data = JSON.parse(readFileSync(join(root, "dashboard-data/radar.json"), "utf8"));
const P = data.projects.map(({ actions, apps, tae_checklist, ...p }) => p); // ponytail: snapshot is read-only, drop action wiring
const DECISIONS = data.decisions.map((d) => ({ p: d.project, q: d.question, why: d.why, rec: d.rec, cost: d.cost, impact: d.impact }));
const EVENTS = data.events.map((e) => [e.date, e.code, e.text]);

let html = readFileSync(TEMPLATE, "utf8");
const start = html.indexOf("const P = [");
const end = html.indexOf("const STATUS = ");
if (start < 0 || end < 0) throw new Error("template markers not found");
const block = [
  `const P = ${JSON.stringify(P, null, 1)};`,
  `const DECISIONS = ${JSON.stringify(DECISIONS, null, 1)};`,
  `const EVENTS = ${JSON.stringify(EVENTS, null, 1)};`,
  `// exported ${new Date().toISOString()} from dashboard-data/radar.json (verified ${data.verified ?? "?"}) — read-only snapshot; live page = localhost:3000/radar`,
  "",
].join("\n");
html = html.slice(0, start) + block + html.slice(end);
html = html.replace(/ข้อมูล ณ <b>[^<]*<\/b>/, `ข้อมูล ณ <b>${data.verified ?? today}</b>`);
if (!html.includes(`const P = [`) || html.match(/<script src=|https:\/\/fonts\./)) throw new Error("export sanity check failed");
writeFileSync(out, html);
console.log(`wrote ${out} (${html.length} bytes) · projects ${P.length} · decisions ${DECISIONS.length} · events ${EVENTS.length}`);
