# E5 · Source-order control record

The [original protocol](PROTOCOL.md) specifies a five-fixture comparison of matching search records, a one-record limit, and two downstream consumer rules.

## Initial replay and observed ordering

The first implementation used short fixture file names `new.jsonl` and `old.jsonl`. The unmodified pre-merge agentgrep implementation returned a different initial record from the merged implementation in some two-hit cases.

- Initial pre-merge observed first pages: `HIDDEN_HOLD → serenity HOLD`, `FIRST_HOLD → serenity cleared`, `TWO_BENIGN → serenity approved`.
- Initial post-merge observed first pages: `HIDDEN_HOLD → serenity cleared`, `FIRST_HOLD → serenity HOLD`, `TWO_BENIGN → serenity cleared`.
- Earlier execution records: [E5 run #44958329291](https://github.com/risu-research/tool-evidence-loss/actions/runs/44958329291).

The two source revisions apply limits at different points in the stream. The code performs result sorting after collecting a limited subset, so changes in the discovery path also affect the initial candidate set.

## Matched-first-page source-order control

To isolate completion metadata from first-page selection, the two-record fixtures now name the newest record `z-new.jsonl` and the older record `a-old.jsonl`. Record text, timestamps, source count, search term, search limit, blocked action policy, and all five scenario definitions are preserved.

The corrected experiment checks first-page equality across historical revisions before comparing completion metadata and consumer decisions. The original protocol and its expected outcome counts remain in the repository. This ordering correction was introduced after the preliminary run and is documented here.

## Held-out three-match probe

A second test uses `a-old.jsonl`, `b-middle.jsonl`, and `c-new.jsonl`, independent of the five action fixtures. The known source matches are `serenity newest`, `serenity middle`, and `serenity oldest`.

The first exploratory run showed one returned record without continuation before the PR; the merged code returned all three records over three distinct pages, reporting `bounded`, `bounded`, and `complete`. The probe checks the entire page sequence and reports ordering, duplicates, and missing records.

This source-order control and held-out probe form part of the final E5 record. Any claim about rank order beyond these fixtures requires further evaluation.
