# E5 · Cross-source MCP page-completion replay

E5 evaluates [agentgrep](https://github.com/tony/agentgrep), a local search tool for agent prompt and conversation records. Its developer documented missing page-completion and continuation information in [Issue #55](https://github.com/tony/agentgrep/issues/55) on June 13, 2026, then merged the [resumable MCP pages implementation in PR #64](https://github.com/tony/agentgrep/pull/64) on June 14.

The experiment executes the **original FastMCP server** from both historical commits, using only synthetic Codex session JSONL files in temporary directories. The original upstream source is fetched by commit, installed from its frozen `uv.lock` with Python 3.14, and verified against the published Git blob of its `search_tools.py` file.

## Fixed source revisions

| | Source commit | Original `search_tools.py` blob |
| --- | --- | --- |
| Before the merge | `9b5ccda643f2bf84c49b0ec1c4ae300b681a5f83` | `61d8f7837bef4ab35b91044b46e78e3f8e3fa197` |
| After the merge | `6b2d3465767421f113acf684473384db00ebf619` | `14da30d259562549038e805de760359a9120e7b5` |

The [original protocol](PROTOCOL.md) fixes five source fixtures, two consumer rules, and one-result pages. The [first-page selection audit](SOURCE_ORDER_NOTE.md) records a source-order difference discovered during execution, with the original diagnostic runs and the interpretation correction.

## Observed downstream decisions

| Consumer rule | Pre-merge approvals | Post-merge approvals |
| --- | ---: | ---: |
| Read the first returned page | 4 of 5 | 4 of 5 |
| Require a complete search, traversing result cursors | 0 of 5 | 3 of 5 |

The completion-aware rule blocks unverified results in the original interface. With the merged page metadata, it follows the cursor and approves the three synthetic workloads with complete benign evidence. The two HOLD fixtures result in blocked actions.

In the first-page-only tests, one fixture per revision leads to a test marker write despite a HOLD match elsewhere in the source set. The exact fixture varies across historical revisions because their first-page candidate selection differs. The original source ordering and the corresponding observed outputs are recorded verbatim.

The test writes a small local release-marker file when a fixed consumer permits the action, then reopens and hashes the file. The original agentgrep tool remains read-only; action writes belong to the study-owned test harness.

## Held-out three-record traversal

A second fixture contains three matching prompts: `serenity newest`, `serenity middle`, and `serenity oldest`. This case is separate from the five source fixtures.

- Pre-merge, the original MCP search returns `serenity newest` with one-result limit and no continuation handle.
- Post-merge, the actual cursor sequence returns all three records with `bounded`, `bounded`, `complete` status, no duplicates, and newest-first order.

The [pair verifier](verify_pair.py) checks this held-out case in addition to the 20 consumer conditions.

## Reproduce from an empty environment

The [E5 GitHub Actions workflow](../../.github/workflows/e5-agentgrep.yml) downloads the two original Git commits, installs Python 3.14 through `uv`, uses the upstream revision-specific `uv.lock` files, runs the original FastMCP server, and independently validates both outputs.

Commands from the repository root, after fetching `agentgrep-before` and `agentgrep-after` at the commits above:

```bash
uv python install 3.14
(cd agentgrep-before && uv sync --frozen --no-dev --python 3.14)
(cd agentgrep-after && uv sync --frozen --no-dev --python 3.14)

agentgrep-before/.venv/bin/python experiments/e5/replay_agentgrep.py --source agentgrep-before --revision before --output results/e5_before.json
agentgrep-after/.venv/bin/python experiments/e5/replay_agentgrep.py --source agentgrep-after --revision after --output results/e5_after.json

agentgrep-before/.venv/bin/python experiments/e5/probe_long_pages.py --source agentgrep-before --revision before --output results/e5_probe_before.json
agentgrep-after/.venv/bin/python experiments/e5/probe_long_pages.py --source agentgrep-after --revision after --output results/e5_probe_after.json

python3 experiments/e5/verify_pair.py results/e5_before.json results/e5_after.json --probe-before results/e5_probe_before.json --probe-after results/e5_probe_after.json --output results/e5_pair.json
```

The successful first full run is [Actions #44958664499](https://github.com/risu-research/tool-evidence-loss/actions/runs/44958664499), which passed the original-source and independent cross-version comparisons.

## Evidence and scope

[`evidence/e5/`](../../evidence/e5/) preserves the five validated result JSON files, the source/run identity, and their SHA-256 hashes. Reports list synthetic prompt texts, tool result conditions, page status, and test marker outcomes. Real agent histories and local filesystem path details are absent from the archived reports.

E5 tests a separate source type and separate evidence-loss mechanism from E4. The external issue describes an interface investigation, and PR #64 is an independently merged feature and repair. These controlled fixtures show page-completion information affecting downstream test decisions. They record software behavior under an original public implementation, with no measured deployment incident or model-agent success rate.

The original [agentgrep source is MIT-licensed](https://github.com/tony/agentgrep/blob/6b2d3465767421f113acf684473384db00ebf619/LICENSE).
