# Discovery 37: frozen source observations

The S2AI paper's Table II uses 37 observations drawn from the 50-case ClosureProbe v0.3 corpus. The remaining 13 cases contain cross-boundary traces and sit outside the source-observation comparison.

The original corpus was released on 2026-08-15 at [ClosureProbe commit `12fae2c`](https://github.com/risu-research/closureprobe/commit/12fae2c0cb0909a43f487323fb00e7372b1f3377). Its original file is preserved under [`source/cases.json`](source/cases.json) with the original corpus schema and license. SHA-256 and Git blob identities are checked on each replay.

## Reproduce Table II

Requires Python 3.10 or later.

```bash
python3 scripts/replay_discovery37.py --verify experiments/discovery37/results
```

Run from the repository root. This command independently derives the five decision columns from each source request and response, compares every generated CSV row and JSON aggregate with the frozen outputs, and checks five controlled mutations.

For newly generated results:

```bash
python3 scripts/replay_discovery37.py --write /tmp/discovery37-replay
```

The [public CI workflow](../../.github/workflows/discovery37.yml) also checks out the historical ClosureProbe commit, builds its original source, runs its 50-case conformance verification, and compares the historical input corpus to this archive.

## Decision columns

| Rule | Input conditions |
| --- | --- |
| R0 | Returned visible container is empty |
| R1 | R0 and successful execution |
| R2 | R1 and initial request with a final returned segment |
| R3 | R2 and a reported zero result count |
| RQ | Historical source-qualified verdict from the frozen corpus |

R2 checks initial and final segment indicators. Intermediate page-token continuity, incomplete search coverage, service timeouts, skipped shards, and effective source scope remain available in the full source records. R3 checks a zero-valued observed count. Each source profile uses its native result fields to derive these generic predicates.

For multi-page Google Drive, DynamoDB, and Microsoft Graph records, R0 reads the last returned page. R3 counts the observations across supplied pages. Elasticsearch R0 reads the returned hit list; R3 reads `hits.total`. This distinction matters for empty pages following earlier matches and requests with `size=0`.

RQ reads the archived `expected.negativeLicense` field of each case. ClosureProbe's separate official replay checks the historical source-profile classifications. The new R0–R3 script reads the response records and applies its five generic conditions independently of these labels.

## Frozen result

| Rule | Commits | Licensed | Unlicensed |
| --- | ---: | ---: | ---: |
| R0 | 36 | 9 | 27 |
| R1 | 34 | 9 | 25 |
| R2 | 23 | 9 | 14 |
| R3 | 19 | 9 | 10 |
| RQ | 9 | 9 | 0 |

The [37-row CSV](results/rows.csv) records each predicate, rule decision, source profile, and archived source verdict. The [aggregate JSON](results/table_ii.json) records the six source-profile breakdowns and the source identity.

The 37 cases form a curated conformance corpus. Counts describe the specified test states and their locally simulated action decisions. The eight G7–G9 matched pairs and E1–E3 adapter tests are separate experiments.

## Fixed comparison checks

The replay adds five internal validation conditions: three metadata-loss invariance tests (Drive incomplete-search status, Elasticsearch timeout, Graph delta completion marker) and two result-count sensitivity tests. They validate the code path used to compute the published table.

This source dataset and the frozen source-qualified labels originate in ClosureProbe. The additional Python replay reconstructs the S2AI comparison rules.
