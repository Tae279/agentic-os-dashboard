"use client";

import { Checkbox } from "@heroui/react";
import { Hand } from "lucide-react";
import type { RadarChecklistItem } from "@/lib/api";

export function TaeChecklist({
  items,
  checked,
  onToggle,
}: {
  items: RadarChecklistItem[];
  checked: Record<string, boolean>;
  onToggle: (key: string, next: boolean) => void;
}) {
  const done = items.filter((item) => !!checked[item.id]).length;

  return (
    <div>
      <div className="flex items-center gap-1.5 flex-wrap mb-2">
        <Hand size={14} className="text-warn" />
        <span className="text-[11px] uppercase tracking-[0.14em] text-fg-mute">เต้ต้องกดเอง</span>
        <span className="text-[11px] text-fg-mute">
          ไม่มีปุ่ม auto — ทำเสร็จแล้วติ๊กไว้ (จำไว้หลังรีเฟรช)
        </span>
      </div>
      <div className="space-y-2">
        {items.map((item) => {
          const selected = !!checked[item.id];
          return (
            <Checkbox
              key={item.id}
              isSelected={selected}
              onChange={(v) => onToggle(item.id, v)}
            >
              <Checkbox.Content>
                <Checkbox.Control>
                  <Checkbox.Indicator />
                </Checkbox.Control>
                <span className={selected ? "text-sm line-through text-fg-mute" : "text-sm"}>
                  {item.text}
                </span>
              </Checkbox.Content>
            </Checkbox>
          );
        })}
      </div>
      <div className="font-mono-num text-[11px] text-fg-dim mt-2">
        {done}/{items.length} เสร็จ
      </div>
    </div>
  );
}
