# When Tool Interfaces Lose Evidence Needed for Action

Reproducible experiments for the S2AI 2026 paper *When Tool Interfaces Lose Evidence Needed for Action*.

A search can return zero files after covering only part of its requested scope. The experiments below measure how this distinction survives tool adapters and MCP transports, then test its effect on a follow-up write.

## Results

| Experiment | Execution path | Verified result |
| --- | --- | --- |
| G7 | Official Agents SDK and MCP stdio | 16 controlled source states; 8 permitted actions and 8 blocked |
| G8 | Official Agents SDK and MCP Streamable HTTP | Same 16 source states across HTTP |
| G9 | Source-derived projection and full visible transcript replay | 8 indistinguishable pairs; 5 request-binding challenges |
| E1 | Search handlers from two public Google Drive MCP projects | Missing search-completeness evidence in one implementation; preserved in the comparison |
| E2 | Full upstream MCP server with in-memory and stdio clients | Identical MCP responses for complete and incomplete empty searches |
| E3 | Full upstream MCP server, stdio client, local HTTP provider | 3 confirmed writes across 5 conditions, including 1 write under incomplete search coverage |

G7–G9 share a frozen set of 16 controlled source cases. E1–E3 use pinned third-party implementation sources. The E3 client follows a fixed decision rule; the write reaches a local HTTP test provider and is independently read back through MCP.

## Reproduce

Requires Python 3 and Node.js 22. The initial integrity and G9 replay use Node built-ins.

```bash
bash scripts/verify-local.sh
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

The [GitHub Actions verification workflow](.github/workflows/verify.yml) also installs the complete pinned third-party MCP server, runs E2 over in-memory and stdio transports, and runs E3 through a separate local HTTP provider with recorded effects.

## Layout

- [`experiments/g7`](experiments/g7) and [`experiments/g8`](experiments/g8) contain frozen source, fixtures, dependency locks, and original execution records.
- [`experiments/g9`](experiments/g9) contains source-derived projection, exact request-binding tests, and frozen one-shot results.
- [`experiments/e1`](experiments/e1) contains the pinned public search-handler comparisons.
- [`experiments/e2`](experiments/e2) and [`experiments/e3`](experiments/e3) contain the full-server integration tests.
- [`evidence`](evidence) contains captured MCP outputs and independent HTTP write receipts.
- [`EVIDENCE_SHA256SUMS.txt`](EVIDENCE_SHA256SUMS.txt) fixes the initial publication set at the byte level.
- [`docs/provenance.md`](docs/provenance.md) records upstream commits and original public execution runs.
- [`docs/results.md`](docs/results.md) maps results to their experimental scope.

## Measurement scope

The original 16 states are controlled fixtures. E1–E3 introduce publicly authored adapter code and installed MCP runtime tests. Google API responses and E3 effects use local test providers. The downstream policy is deterministic. Production incidence and autonomous-agent behavior remain targets for separate empirical measurement.

## Reuse

The experiment harness and documents are shared under MIT. Third-party implementation excerpts retain their original licensing and attribution, as described in [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md).
