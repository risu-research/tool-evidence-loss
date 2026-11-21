#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
node run_replay.cjs >/dev/null
node run_control.cjs >/dev/null
if command -v git >/dev/null; then
  sha="$(git hash-object upstream_control_files_list.ts)"
  test "$sha" = "8e5bba41101d24b49e299d9ef3c8bde46a047719"
fi
node - <<'JS'
const fs = require('node:fs');
const a = JSON.parse(fs.readFileSync('results/results.json', 'utf8'));
const b = JSON.parse(fs.readFileSync('results/control.json', 'utf8'));
if(a.passes !== a.total_checks || b.passes !== b.total_checks) process.exit(1);
console.log(`PASS target ${a.passes}/${a.total_checks}; control ${b.passes}/${b.total_checks}`);
JS
