#!/bin/bash
# เปิด Agentic OS Dashboard — ดับเบิลคลิกไฟล์นี้ได้เลย
# ถ้า dashboard รันอยู่แล้ว จะเปิด browser ให้เฉยๆ ไม่รันซ้ำ

cd "$(dirname "$0")"

PORT=8501

# ถ้ามีตัวเก่ารันอยู่แล้ว → แค่เปิด browser
if lsof -i :$PORT -sTCP:LISTEN >/dev/null 2>&1; then
    open "http://localhost:$PORT"
    echo "Dashboard รันอยู่แล้ว — เปิด browser ให้แล้วครับ ปิดหน้าต่างนี้ได้เลย"
    exit 0
fi

# ยังไม่รัน → เปิด browser รอไว้ แล้วสตาร์ท server
( sleep 3 && open "http://localhost:$PORT" ) &

echo "กำลังเปิด Agentic OS Dashboard..."
echo "ปิด dashboard: กลับมาหน้าต่างนี้แล้วกด Ctrl+C หรือปิดหน้าต่าง Terminal"
echo

exec ./.venv/bin/streamlit run app.py --server.port $PORT --server.headless true
