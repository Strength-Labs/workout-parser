#!/bin/bash
# Weekly client triage — run from cron
cd ~/hoard/karl-dev/workout-parser
source .venv/bin/activate
python3 scripts/client-triage.py 2>/tmp/triage-stderr.txt
echo "Exit code: $?" >> /tmp/triage-stderr.txt
