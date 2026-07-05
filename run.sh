#!/bin/bash
# รัน dashboard ผ่าน python -m (กัน .venv shebang พังเวลาย้าย repo)
cd "$(dirname "$0")"
exec .venv/bin/python -m streamlit run app.py --server.port 8501 --server.headless true
