# E5 · Historical MCP page-completion replay

## External history

- Independent project: [tony/agentgrep](https://github.com/tony/agentgrep)
- Historical problem statement: [Issue #55](https://github.com/tony/agentgrep/issues/55), June 13, 2026
- Merged source change: [PR #64](https://github.com/tony/agentgrep/pull/64), June 14, 2026
- Before commit: `9b5ccda643f2bf84c49b0ec1c4ae300b681a5f83` (historical `v0.1.0a21`)
- After commit: `6b2d3465767421f113acf684473384db00ebf619` (merged PR)
- Relevant upstream file: `src/agentgrep/mcp/tools/search_tools.py`

Issue #55 records a developer investigation of MCP search completeness and continuation. PR #64 introduced a structured `status`, `page.next_cursor`, counts, source metadata, and result references. The reported issue is an independent developer-identified interface limitation. This replay creates controlled source data and tests original code behavior before and after the merge.

## Frozen evaluation

The input consists entirely of synthetic Codex session JSONL files in an isolated temporary home directory, matching the structural schema in agentgrep's public regression tests. The search term is `serenity`; the result limit is one record. An older match may contain the literal `HOLD` marker.

Five scenario fixtures:

| Scenario | Matching records | Expected coverage-aware action |
| --- | --- | --- |
| HIDDEN_HOLD | New benign match, older HOLD match | Block after full traversal |
| SINGLE_BENIGN | One benign match | Allow after complete traversal |
| ZERO | One unrelated record, zero matches | Allow after complete traversal |
| FIRST_HOLD | New HOLD match, older benign match | Block |
| TWO_BENIGN | Two benign matches | Allow after full traversal |

Two precommitted consumer decision rules:

- **Visible-only:** allow a release-marker write when the first tool result contains no `HOLD` record.
- **Completion-aware:** require `status.state == complete` or follow every `page.next_cursor` to completion. Any absent completion signal, detected HOLD match, or invalid cursor state withholds the write.

For each source revision, each scenario runs under both rules. The 20 conditions and expected approvals are fixed here prior to execution.

| Source | Visible-only approvals | Completion-aware approvals |
| --- | ---: | ---: |
| Before PR #64 | 4 of 5 | 0 of 5 |
| After PR #64 | 4 of 5 | 3 of 5 |

The visible-only rule accepts HIDDEN_HOLD in both revisions. The completion-aware rule can only finish the historical bounded query after the fix, recovering the older HOLD record and withholding the release.

An allowed action writes a unique marker file to a temporary output directory. The test rereads the file and checks its SHA-256 against the original expected content, recording the observed effect. This is a study-owned action after the read-only upstream tool, distinct from an agentgrep write tool.

## Original execution requirements

Execute the original installed `agentgrep.mcp.build_mcp_server()` through the public `fastmcp.Client`, using the same synthetic input fixture in both version-specific isolated Python 3.14 environments. The upstream `src/agentgrep` code remains unchanged.

Check source commit and `search_tools.py` Git blob, original tool discovery, returned result shape, actual second-page cursor replay, empty case, one-hit case, and total observed marker-file writes.

The search uses synthetic Codex session files. All source snippets are generated anew at test time. No user prompt history, account sessions, private configuration, LLM, or live services enter this experiment.

## Interpretation

This independent source type tests page-boundary loss, separate from Google Drive's completeness flag. The merged change directly affects the tool interface. The downstream decision rules and marker-file effects are controlled experimental additions. The counts are outcomes for these fixed fixtures and serve as execution witnesses.
