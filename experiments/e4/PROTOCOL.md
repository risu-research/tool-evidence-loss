# E4 historical repair replay: frozen protocol

Historical external source: Agno issue [#7823](https://github.com/agno-agi/agno/issues/7823), fixed by merged PR [#7824](https://github.com/agno-agi/agno/pull/7824) on May 19, 2026.

## Source identity
- Before: Agno first-parent commit `bc563b724c2ea39368ca99b6cd45d36a64a7b1c5`
- After: merged Agno commit `9ff6d911131768470f91620ba40878a1f9372b61`
- Target: `libs/agno/agno/tools/google/drive.py`
- Before Git blob: `e7bf38548f561d3a5264a8da7e29b4905f17cea4`
- After Git blob: `654c4c4697191612f3cd72e32627c3e1a564eeba`

The historical fix adds `incompleteSearch` to the requested Google Drive fields and the returned search JSON. The execution checks both changes using the original imported `GoogleDriveTools` class at each historical commit.

## Locked evaluation
Five deterministic provider states:

| ID | Provider state | Search result |
| --- | --- | --- |
| COMPLETE_EMPTY | Complete coverage, zero hits | 0 files, explicit `incompleteSearch=false` |
| INCOMPLETE_EMPTY | Partial coverage, zero hits | 0 files, explicit `incompleteSearch=true` |
| POSITIVE_HIT | Complete coverage, one hit | 1 named file |
| NEXT_PAGE | Complete current page, continuation token | 0 files, `nextPageToken` present |
| API_FAILURE | Provider `files.list` raises an error | An error response |

Two consumer rules are frozen here before running the experiment.

- Projection consumer: allow a follow-up write after a successful response with `count=0` and an exhausted page token.
- Coverage-aware consumer: apply the same rule and require `incompleteSearch is False` explicitly in the Agno tool JSON.

Each rule runs against both commits and all five provider states: 20 scenarios in total. Expected write counts across five states:

| Source revision | Projection consumer | Coverage-aware consumer |
| --- | ---: | ---: |
| Before repair | 2 | 0 |
| After repair | 2 | 1 |

The E4 post-repair consumer's successful write for COMPLETE_EMPTY demonstrates positive availability; its blocked INCOMPLETE_EMPTY write demonstrates coverage-sensitive action control. A projection-only consumer is expected to write on an incomplete search even after the upstream repair. The pre-repair coverage-aware consumer is expected to block both empty states because the relevant field is absent.

## Effect evidence
A real `GoogleDriveTools.upload_file` method invocation sends `files.create` through a fake Google service to an independent loopback HTTP provider. The provider updates an in-memory file collection, writes a JSONL receipt at request time, and returns the updated collection on a separate readback call. The test checks the actual upload call, receipt, and readback.

The same fake service receives the original `search_files` request and respects its Google API field mask when constructing the response. A provider `incompleteSearch` signal is returned only when explicitly requested. The original GoogleDriveTools class and methods remain untouched.

Other controls: `list_files` delegation, asynchronous `asearch_files`, result-field presence, source Git blob checks, API request mask, page-token handling, positive hit handling, error handling, and a missing-field default check. Each run records generated search responses and provider calls.

## Evidence interpretation
The issue and merged repair are independent, dated historical records. The controlled provider states and consumer rules are part of this experiment. Reconstructed software execution tests a documented defect and its repair under pinned original implementations. The state changes occur in a local HTTP provider. Model-driven choices and live Google Drive operations remain separate empirical targets.

Reproducibility requires installing Agno from the historical source checkout. GitHub Actions builds this environment with Python 3.12 and records the interpreter and source commits.
