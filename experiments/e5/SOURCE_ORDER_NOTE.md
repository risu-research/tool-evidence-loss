# E5 · Historical first-page selection audit

The [original protocol](PROTOCOL.md) fixed five source-data scenarios and two downstream consumer rules before execution.

## Observed selection difference

The original pre-merge version returned a different first-page record from the repaired version in three two-record cases. The actual results were:

| Scenario | Pre-merge first record | Post-merge first record |
| --- | --- | --- |
| HIDDEN_HOLD | serenity HOLD | serenity cleared |
| FIRST_HOLD | serenity cleared | serenity HOLD |
| TWO_BENIGN | serenity approved | serenity cleared |

The original source-iteration path and result limit select a different first-page candidate set from the merged implementation, which requests an additional record before sorting and slicing the page.

The initial protocol assumed the newest record would appear first under both historical versions. This assumption failed for the original implementation. A subsequent exploratory change to fixture file names did not alter the behavior, so the original file names and fixed input records were restored. The historical selection effect is retained as an observed result.

Original diagnostic run: [#44958329291](https://github.com/risu-research/tool-evidence-loss/actions/runs/44958329291). Source-order confirmation: [#44958501014](https://github.com/risu-research/tool-evidence-loss/actions/runs/44958501014).

## Revised comparison with unchanged decisions

Five scenario descriptions, search term `serenity`, limit 1, all source timestamps, and the visible-only and completion-aware decision rules remain unchanged. Total expected writes per version and consumer rule also remain unchanged.

The specific visible-only unsafe witness differs by revision:

- Pre-merge: `FIRST_HOLD/visible`, where the first record is benign and the newer HOLD record remains unseen.
- Post-merge: `HIDDEN_HOLD/visible`, where the newer benign record is first and the older HOLD record sits on the next page.
- Post-merge completion-aware: follows the cursor, sees each HOLD record, and withholds the release marker.
- Pre-merge completion-aware: lacks a completion signal and withholds the release marker.

The final cross-version verifier checks these observed differences explicitly. This adjustment is an interpretation and expected-output correction after the initial exploratory run. Its provenance remains available in the run history.

## Independent held-out three-record probe

A second fixture contains three synthetic matched records with explicit timestamps and file names: `a-old`, `b-middle`, and `c-new`. Under the original pre-merge implementation, limit 1 returned `serenity newest` and no continuation. Under the merged implementation, the same query returned `serenity newest`, `serenity middle`, and `serenity oldest` over three pages with `bounded`, `bounded`, `complete` statuses, without duplicates.

This probe provides a clean, equal-first-record comparison of source pagination capabilities. The two-record scenarios additionally document how limited source selection interacts with per-version ordering.
