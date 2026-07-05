"use client";

import { motion, AnimatePresence } from "framer-motion";

export function RunOutput({
  label,
  text,
  phase,
  onClose,
}: {
  label: string | null;
  text: string;
  phase: string | null;
  onClose: () => void;
}) {
  return (
    <AnimatePresence>
      {label && (
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: 12 }}
          transition={{ duration: 0.25 }}
          className="rounded-[var(--radius-card)] hairline bg-bg-card p-4 mb-6"
        >
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2">
              <span className="font-display text-sm font-semibold">{label}</span>
              {phase && (
                <span className="text-[11px] px-2 py-0.5 rounded-full hairline text-fg-dim font-mono-num">
                  {phase}
                </span>
              )}
            </div>
            <button onClick={onClose} className="text-xs text-fg-mute hover:text-fg">
              ปิด
            </button>
          </div>
          <div className="text-xs text-fg-dim whitespace-pre-wrap max-h-64 overflow-y-auto font-mono-num">
            {text || "กำลังเริ่ม…"}
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
