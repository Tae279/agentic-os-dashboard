"use client";

import { useMemo, useState } from "react";
import { motion } from "framer-motion";
import { Loader2, Check, X, Play } from "lucide-react";
import type { Skill } from "@/lib/api";
import { streamPost } from "@/lib/api";

type RunState = "idle" | "running" | "done" | "error";

const CATEGORY_LABEL: Record<string, string> = {
  daily: "งานประจำวัน",
  content: "Content",
  loop: "Loop",
  projects: "Projects",
};

const CATEGORY_ORDER = ["daily", "loop", "content", "projects"];

export function LauncherGrid({
  skills,
  usageCounts,
  onRunOutput,
}: {
  skills: Skill[];
  usageCounts: Record<string, number>;
  onRunOutput: (label: string, text: string, phase: string | null) => void;
}) {
  const [states, setStates] = useState<Record<string, RunState>>({});
  const [expanded, setExpanded] = useState<string | null>(null);
  const [inputs, setInputs] = useState<Record<string, string>>({});

  const grouped = useMemo(() => {
    const byCat: Record<string, Skill[]> = {};
    for (const s of skills) {
      const cat = s.category || "อิสระ";
      (byCat[cat] ||= []).push(s);
    }
    for (const cat of Object.keys(byCat)) {
      byCat[cat].sort((a, b) => (usageCounts[b.id] || 0) - (usageCounts[a.id] || 0));
    }
    return byCat;
  }, [skills, usageCounts]);

  const categories = [
    ...CATEGORY_ORDER.filter((c) => grouped[c]),
    ...Object.keys(grouped).filter((c) => !CATEGORY_ORDER.includes(c)),
  ];

  async function runSkill(skill: Skill, userInput: string) {
    setStates((s) => ({ ...s, [skill.id]: "running" }));
    setExpanded(null);
    let text = "";
    await streamPost(
      "/api/run",
      { skill_label: skill.label, input: userInput },
      {
        onPhase: (d) => onRunOutput(skill.label, text, d.phase),
        onText: (d) => {
          text += d.chunk;
          onRunOutput(skill.label, text, null);
        },
        onDone: (d) => {
          setStates((s) => ({ ...s, [skill.id]: d.ok ? "done" : "error" }));
          setTimeout(() => setStates((s) => ({ ...s, [skill.id]: "idle" })), 3000);
        },
        onError: () => setStates((s) => ({ ...s, [skill.id]: "error" })),
      }
    );
  }

  function handleCardClick(skill: Skill) {
    if (states[skill.id] === "running") return;
    if (skill.input_placeholder) {
      setExpanded(expanded === skill.id ? null : skill.id);
      return;
    }
    runSkill(skill, "");
  }

  return (
    <div className="space-y-6">
      {categories.map((cat) => (
        <div key={cat}>
          <h2 className="text-xs uppercase-none tracking-wide text-fg-mute mb-2 font-mono-num">
            {CATEGORY_LABEL[cat] || cat}
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {grouped[cat].map((skill, i) => {
              const state = states[skill.id] || "idle";
              const isExpanded = expanded === skill.id;
              return (
                <motion.div
                  key={skill.id}
                  initial={{ opacity: 0, y: 12 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.3, delay: i * 0.03, ease: "easeOut" }}
                  className={`rounded-[var(--radius-card)] hairline hairline-hover bg-bg-card p-4 cursor-pointer transition-[transform,box-shadow,border-color,background-color] hover:-translate-y-0.5 ${
                    state === "running" ? "glow-focal" : ""
                  }`}
                  onClick={() => handleCardClick(skill)}
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="min-w-0">
                      <div className="font-display font-semibold text-sm text-fg truncate">{skill.label}</div>
                      <div className="text-xs text-fg-dim mt-1 line-clamp-2">{skill.description}</div>
                    </div>
                    <StatusIcon state={state} />
                  </div>

                  {isExpanded && (
                    <div
                      className="mt-3 flex items-center gap-2"
                      onClick={(e) => e.stopPropagation()}
                    >
                      <input
                        autoFocus
                        placeholder={skill.input_placeholder}
                        value={inputs[skill.id] || ""}
                        onChange={(e) => setInputs((v) => ({ ...v, [skill.id]: e.target.value }))}
                        onKeyDown={(e) => {
                          if (e.key === "Enter") runSkill(skill, inputs[skill.id] || "");
                        }}
                        className="flex-1 bg-bg-elev hairline rounded-[var(--radius-chip)] px-2.5 py-1.5 text-sm text-fg placeholder:text-fg-mute focus:outline-none focus:border-accent"
                      />
                      <button
                        onClick={() => runSkill(skill, inputs[skill.id] || "")}
                        className="p-1.5 rounded-[var(--radius-chip)] bg-accent-deep hover:bg-accent transition-colors"
                      >
                        <Play size={14} />
                      </button>
                    </div>
                  )}
                </motion.div>
              );
            })}
          </div>
        </div>
      ))}
    </div>
  );
}

function StatusIcon({ state }: { state: RunState }) {
  if (state === "running") return <Loader2 size={16} className="animate-spin text-accent shrink-0" />;
  if (state === "done") return <Check size={16} className="text-good shrink-0" />;
  if (state === "error") return <X size={16} className="text-danger shrink-0" />;
  return <span className="h-1.5 w-1.5 rounded-full bg-fg-mute shrink-0 mt-1" />;
}
