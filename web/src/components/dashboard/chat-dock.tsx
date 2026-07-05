"use client";

import { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { MessageCircle, X, Send } from "lucide-react";
import { streamPost } from "@/lib/api";

type ChatMsg = { role: "user" | "assistant"; text: string };

export function ChatDock() {
  const [open, setOpen] = useState(false);
  const [msgs, setMsgs] = useState<ChatMsg[]>([]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [sid, setSid] = useState<string | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight });
  }, [msgs]);

  async function send() {
    const text = input.trim();
    if (!text || sending) return;
    setInput("");
    setMsgs((m) => [...m, { role: "user", text }]);
    setSending(true);
    setMsgs((m) => [...m, { role: "assistant", text: "" }]);

    await streamPost(
      "/api/chat",
      { message: text, session_id: sid },
      {
        onText: (d) => {
          setMsgs((m) => {
            const copy = [...m];
            copy[copy.length - 1] = { role: "assistant", text: copy[copy.length - 1].text + d.chunk };
            return copy;
          });
        },
        onDone: (d) => {
          if (d.session_id) setSid(d.session_id as string);
          if (d.error) {
            setMsgs((m) => {
              const copy = [...m];
              copy[copy.length - 1] = { role: "assistant", text: `⚠️ ${d.error}` };
              return copy;
            });
          }
          setSending(false);
        },
        onError: () => setSending(false),
      }
    );
  }

  return (
    <div className="fixed bottom-5 right-5 z-40 flex flex-col items-end gap-3">
      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ opacity: 0, y: 16, scale: 0.98 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 16, scale: 0.98 }}
            transition={{ duration: 0.2 }}
            className="w-80 sm:w-96 h-[28rem] rounded-[var(--radius-card)] hairline bg-bg-card-hi shadow-2xl flex flex-col overflow-hidden"
          >
            <div className="px-4 py-3 border-b border-ring-soft flex items-center justify-between">
              <span className="font-display text-sm font-semibold">คุยกับ Claude</span>
              <button onClick={() => setOpen(false)} className="text-fg-mute hover:text-fg">
                <X size={16} />
              </button>
            </div>
            <div ref={scrollRef} className="flex-1 overflow-y-auto p-3 space-y-2">
              {msgs.length === 0 && (
                <div className="text-xs text-fg-mute italic text-center mt-8">พิมพ์อะไรก็ได้เพื่อเริ่ม…</div>
              )}
              {msgs.map((m, i) => (
                <div
                  key={i}
                  className={`text-xs rounded-[var(--radius-chip)] px-3 py-2 max-w-[85%] whitespace-pre-wrap ${
                    m.role === "user" ? "bg-accent-deep text-white ml-auto" : "bg-bg-elev text-fg"
                  }`}
                >
                  {m.text || (sending && i === msgs.length - 1 ? "…" : "")}
                </div>
              ))}
            </div>
            <div className="p-2.5 border-t border-ring-soft flex items-center gap-2">
              <input
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && send()}
                placeholder="พิมพ์ข้อความ…"
                className="flex-1 bg-bg-elev hairline rounded-[var(--radius-chip)] px-2.5 py-1.5 text-xs text-fg placeholder:text-fg-mute focus:outline-none focus:border-accent"
              />
              <button
                onClick={send}
                disabled={sending}
                className="p-1.5 rounded-[var(--radius-chip)] bg-accent-deep hover:bg-accent transition-colors disabled:opacity-40"
              >
                <Send size={14} />
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      <motion.button
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
        onClick={() => setOpen((o) => !o)}
        className="h-12 w-12 rounded-full bg-accent-deep hover:bg-accent transition-colors flex items-center justify-center shadow-lg glow-focal"
      >
        <MessageCircle size={20} className="text-white" />
      </motion.button>
    </div>
  );
}
