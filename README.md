# When Tool Interfaces Lose Evidence Needed for Action

Reproducible experiments for the S2AI 2026 paper *When Tool Interfaces Lose Evidence Needed for Action*.

A Google Drive MCP adapter returns an empty result after dropping search-coverage evidence. An earlier agentgrep MCP search returned a capped page without a continuation handle. The experiments test what these tool responses expose and which downstream decisions follow.

## Results

| Experiment | Execution path | Verified result |
| --- | --- | --- |
| Discovery 37 | Pinned ClosureProbe v0.3 source corpus, independently recalculated | 37 original observations; Table II reproduced across R0–R3 and source-qualified labels |
| G7 | Official Agents SDK and MCP stdio | 16 controlled source states; 8 permitted actions and 8 blocked |
| G8 | Official Agents SDK and MCP Streamable HTTP | Same 16 source states across HTTP |
| G9 | Source-derived projection and full visible transcript replay | 8 indistinguishable pairs; 5 request-binding challenges |
| E1 | Search handlers from two public Google Drive MCP projects | Missing search-completeness evidence in one implementation; preserved in the comparison |
| E2 | Full upstream MCP server with in-memory and stdio clients | Identical MCP responses for complete and incomplete empty searches |
| E3 | Full upstream MCP server, stdio client, local HTTP provider | 3 confirmed writes across 5 conditions, including 1 write under incomplete search coverage |
| E4 | Original Agno GoogleDriveTools before and after merged repair | 20 scenarios; recovered completeness signal enables correct downstream write control |
| E5 | Original agentgrep MCP search before and after resumable-page merge | 20 source-and-consumer tests, plus three-record cursor traversal through three complete pages |

The 37-case exploratory comparison uses 37 observations from a previously published 50-case conformance corpus. G7–G9 share a separate frozen set of 16 controlled source cases. E1–E5 use pinned third-party implementation sources. E3 uses a fixed MCP client rule and verifies its test-provider write through MCP readback. E4 runs the original Agno tool before and after an independently reported repair, then validates local HTTP upload effects under two fixed consumer rules.

## Reproduce

Requires Python 3 and Node.js 22. The initial integrity, 37-row replay, and G9 replay use locally installed standard tooling.

```bash
bash scripts/verify-local.sh
python3 scripts/replay_discovery37.py --verify experiments/discovery37/results
```

E1 executes the original search-handler excerpts with the TypeScript compiler:

```bash
cd experiments/e1
bash run_all.sh
```

The official SDK experiments install their frozen npm dependencies and run in isolated directories:

```bash
bash scripts/replay-official.sh
```

The [GitHub Actions verification workflow](.github/workflows/verify.yml) also installs the complete pinned third-party MCP server, runs E2 over in-memory and stdio transports, and runs E3 through a separate local HTTP provider with recorded effects. The [E4 workflow](.github/workflows/e4-agno.yml) installs both historical Agno revisions, exercises original Google Drive tools, and checks the official Google client and upstream tests. The [E5 workflow](.github/workflows/e5-agentgrep.yml) runs the historical agentgrep FastMCP server on synthetic local prompt records and verifies the result-page continuation effects.

## Layout

- [`experiments/discovery37`](experiments/discovery37) contains the original public 50-case corpus, the 37 selected source observations, an independent replay, and row-level Table II results.
- [`experiments/g7`](experiments/g7) and [`experiments/g8`](experiments/g8) contain frozen source, fixtures, dependency locks, and original execution records.
- [`experiments/g9`](experiments/g9) contains source-derived projection, exact request-binding tests, and frozen one-shot results.
- [`experiments/e1`](experiments/e1) contains the pinned public search-handler comparisons.
- [`experiments/e2`](experiments/e2) and [`experiments/e3`](experiments/e3) contain the full-server integration tests.
- [`experiments/e4`](experiments/e4) contains the dated Agno repair comparison, fixed protocol, source locks, dependency lock, and downstream effect replay.
- [`experiments/e5`](experiments/e5) contains the independent agentgrep paging study, first-page source-order audit, and held-out three-page control.
- [`evidence`](evidence) contains captured MCP outputs, independently recorded HTTP write receipts, and the pinned E4 historical repair results.
- [`EVIDENCE_SHA256SUMS.txt`](EVIDENCE_SHA256SUMS.txt) fixes the initial publication set at the byte level.
- [`docs/provenance.md`](docs/provenance.md) records upstream commits and original public execution runs.
- [`docs/results.md`](docs/results.md) maps results to their experimental scope.

## Measurement scope

The original 16 states are controlled fixtures. E1–E3 introduce publicly authored adapter code and installed MCP runtime tests. E4 adds an external historical defect report and merged repair, validated in original Agno source across 20 controlled scenarios. Google API responses and E3 effects use local test providers. The downstream policy is deterministic. Production incidence and autonomous-agent behavior remain targets for separate empirical measurement.

## Reuse

The experiment harness and documents are shared under MIT. Third-party implementation excerpts retain their original licensing and attribution, as described in [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md).
