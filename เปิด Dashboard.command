#!/bin/bash
# เปิด DX Agentic OS — v7 Command Center (Next.js :3000 + FastAPI :8787)
# ดับเบิลคลิกได้เลย · รันซ้ำ = เปิด browser เฉยๆ ไม่รันซ้อน
cd "$(dirname "$0")"

API=8787
WEB=3000

if ! lsof -i :$API -sTCP:LISTEN >/dev/null 2>&1; then
    nohup .venv/bin/python -m uvicorn server:app --host 127.0.0.1 --port $API >> .cache/uvicorn.log 2>&1 &
fi
if ! lsof -i :$WEB -sTCP:LISTEN >/dev/null 2>&1; then
    ( cd web && nohup npm run start -- -p $WEB -H 127.0.0.1 >> ../.cache/next.log 2>&1 & )
fi

echo "กำลังเปิด DX Agentic OS (v7)..."
for _ in $(seq 1 40); do
    curl -s -o /dev/null "http://localhost:$WEB" && break
    sleep 0.5
done
open "http://localhost:$WEB"
echo "เปิดแล้ว ✅ — ปิดหน้าต่างนี้ได้เลย (server รันต่อเบื้องหลัง)"
