# Results and interpretation

## Discovery 37: source-observation ablation

Table II comes from the 37 observation records in the prepublished ClosureProbe v0.3 corpus. The source file was frozen on 2026-08-15. Thirteen trace records in the 50-case package belong to the separate boundary-trace cohort.

The independent [37-row replay](../experiments/discovery37/README.md) generates exactly:

| Rule | Local commits | Source-licensed | Source-unlicensed |
| --- | ---: | ---: | ---: |
| R0 | 36 | 9 | 27 |
| R1 | 34 | 9 | 25 |
| R2 | 23 | 9 | 14 |
| R3 | 19 | 9 | 10 |
| RQ | 9 | 9 | 0 |

The [row-level results](../experiments/discovery37/results/rows.csv) include each source identity, the five generic predicates, and all decision columns. The [aggregate JSON](../experiments/discovery37/results/table_ii.json) records profile counts and the original corpus identity. The official ClosureProbe CLI independently reproduces its 50 frozen conformance classifications.


## Frozen source cases

G7 and G8 use 16 controlled source observations in eight matched pairs. The source-qualified policy permits eight actions and blocks eight. The projected five-field output permits all 16, including eight source-disallowed local ledger commits. Both runs use the installed Agents SDK and official MCP packages with distinct transports. Their tool-call arguments select individual fixture IDs.

G9 replays the same 16 cases with an out-of-band fixture selection and identical model-visible tool calls within each matched pair. All eight pairwise full visible transcripts match. Five pre-fixed request-binding perturbations are blocked by the test policy. This stage uses a local Node protocol replay.

## Public adapter tests

E1 locates a missing `incompleteSearch` field in a public MCP search adapter and contrasts it with a second implementation that preserves the field. E2 executes the complete pinned adapter in official MCP in-memory and stdio sessions, observing identical results for complete and incomplete empty searches.

E3 runs the same full MCP implementation through stdio with a local HTTP provider. The scripted consumer calls the real `createFolder` MCP tool after the empty search result. The HTTP provider stores the folder and supplies a separate readback through `listFolder`. In five constructed cases, three writes reach the provider; one write occurs under incomplete search coverage. A source-informed test comparator withholds that write and permits the fully covered control.

## Evidence boundary

The input states use selected test fixtures. E3 writes affect a loopback test provider. The downstream decision is a fixed test rule. The observed five-case count describes this experiment. The study leaves production prevalence, model autonomy, and live Google Drive behavior open for independent measurements.

## Historical Agno repair replay (E4)

Agno [issue #7823](https://github.com/agno-agi/agno/issues/7823) documented a Google Drive `allDrives` search result that omitted `incompleteSearch`. Agno maintainers merged [PR #7824](https://github.com/agno-agi/agno/pull/7824) on May 19, 2026.

E4 executes the original `GoogleDriveTools` at the immediate pre-merge and merged commits. Five controlled provider states run under two scripted consumer rules per revision. The original `upload_file` method creates a marker through a loopback HTTP provider when the corresponding rule allows it.

| Consumer | Before fix, writes among five cases | After fix, writes among five cases |
| --- | ---: | ---: |
| Count and pagination only | 2 | 2 |
| Count, pagination, and explicit complete coverage | 0 | 1 |

Both versions of the count-only consumer upload under incomplete search coverage. The coverage-aware consumer blocks that case after repair and permits the complete-empty control. Under the pre-repair result, the completeness field is absent from the response, so the same consumer blocks both empty states. Positive-hit, next-page, and API-failure cases yield zero writes.

The [recorded provider receipts](../evidence/e4/) confirm two actual local HTTP writes before repair and three after repair. An independent run through the installed Google API Discovery v3 client verifies the exact outbound `fields` parameters and the JSON outputs. The historical Agno Google Drive unit suite passes 55 tests at the repaired commit.

The original Agno report establishes historical external relevance. The 20 source states and consumer rules remain bounded experimental fixtures. The measured counts describe replayed local effects.
