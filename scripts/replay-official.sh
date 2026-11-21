#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
which node
node --version
for experiment in g7 g8; do
  (
    cd "experiments/$experiment"
    npm ci --no-audit --no-fund
    if [[ "$experiment" == "g7" ]]; then node run_agents_official.mjs; else node run_http.mjs; fi
  )
done
python3 scripts/verify_public.py --g9
