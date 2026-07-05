#!/bin/bash
# รัน dashboard — เลือกได้ 2 แบบ:
#   ./run.sh          → Streamlit เดิม (:8501, ของเก่ายังใช้ได้)
#   ./run.sh web       → v7 Command Center (Next.js :3000 + FastAPI :8787)
cd "$(dirname "$0")"

if [ "$1" = "web" ]; then
  echo "→ FastAPI  :8787"
  .venv/bin/python -m uvicorn server:app --host 127.0.0.1 --port 8787 &
  API_PID=$!
  echo "→ Next.js  :3000 (production build)"
  (cd web && npm run build && npm run start -- -p 3000) &
  WEB_PID=$!
  trap "kill $API_PID $WEB_PID 2>/dev/null" EXIT
  wait
else
  exec .venv/bin/python -m streamlit run app.py --server.port 8501 --server.headless true
fi
