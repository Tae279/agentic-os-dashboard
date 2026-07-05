#!/bin/bash
# เปิด Agentic OS Dashboard — ดับเบิลคลิกได้เลย (python -m = move-resilient)
cd "$(dirname "$0")"
PORT=8501
if lsof -i :$PORT -sTCP:LISTEN >/dev/null 2>&1; then
    open "http://localhost:$PORT"
    echo "Dashboard รันอยู่แล้ว — เปิด browser ให้แล้ว ปิดหน้าต่างนี้ได้เลย"
    exit 0
fi
( sleep 3 && open "http://localhost:$PORT" ) &
echo "กำลังเปิด Agentic OS Dashboard... (ปิด: Ctrl+C หรือปิดหน้าต่างนี้)"
exec .venv/bin/python -m streamlit run app.py --server.port $PORT --server.headless true
