#!/bin/bash
# Routine self-report: bump today's count in dashboard ledger.
# Called as the last step of every Claude scheduled-task (routine) run.
LEDGER="$(dirname "$0")/../.cache/routines.json"
mkdir -p "$(dirname "$LEDGER")"
python3 - "$LEDGER" <<'PY'
import json, sys, datetime
p = sys.argv[1]
try:
    data = json.load(open(p))
except Exception:
    data = {}
today = datetime.date.today().isoformat()
data[today] = int(data.get(today, 0)) + 1
json.dump(data, open(p, "w"))
print(f"routine ledger: {today} -> {data[today]}")
PY
