# E4 · Historical Agno repair and follow-up write

Agno [issue #7823](https://github.com/agno-agi/agno/issues/7823) reported missing Google Drive `incompleteSearch` evidence on May 6, 2026. The maintainers merged [PR #7824](https://github.com/agno-agi/agno/pull/7824) on May 19, 2026. The change adds `incompleteSearch` to the `files.list` field mask and the returned tool JSON.

This experiment runs the historical `GoogleDriveTools` class at both original commits, using identical provider states and downstream upload rules. The [protocol](PROTOCOL.md) fixes the source versions, input states, decision rules, and expected outcomes.

## Historical versions

| Revision | Exact source commit | Original `drive.py` Git blob |
| --- | --- | --- |
| Before the repair | [`bc563b7`](https://github.com/agno-agi/agno/commit/bc563b724c2ea39368ca99b6cd45d36a64a7b1c5) | `e7bf38548f561d3a5264a8da7e29b4905f17cea4` |
| After the repair | [`9ff6d91`](https://github.com/agno-agi/agno/commit/9ff6d911131768470f91620ba40878a1f9372b61) | `654c4c4697191612f3cd72e32627c3e1a564eeba` |

Agno `2.6.7` is installed directly from its pinned source checkout. The replay checks both Git commits and both original source-file blobs before importing the tool.

## What runs

Five states are tested against two consumer rules and both source revisions, producing **20 fixed run conditions**. The provider returns complete-empty, incomplete-empty, positive-hit, next-page, and API-failure responses.

The original `search_files` method issues `files.list` through a local HTTP-backed Google service stub. When a consumer's fixed rule allows a follow-up action, the original Agno `upload_file` method sends `files.create` to that service. The HTTP provider writes a receipt at the time of the request. A separate state readback verifies the uploaded marker file and its SHA-256.

| Consumer | Before: complete empty | Before: incomplete empty | After: complete empty | After: incomplete empty |
| --- | --- | --- | --- | --- |
| Count and pagination only | Upload | Upload | Upload | Upload |
| Count, pagination, and complete coverage | Block | Block | Upload | Block |

The second rule reads `incompleteSearch` from the actual tool JSON. Its ability to allow a complete search and block a partial search depends on the external repair. A count-only consumer continues to upload under partial coverage after the repair.

Positive-hit, next-page, and API-failure controls block the upload in both revisions. Every run also checks the passed `allDrives` API arguments and correct field masks. The original `list_files` and asynchronous `asearch_files` routes are independently checked.

## Independent HTTP client control

[`replay_discovery_http.py`](replay_discovery_http.py) uses the installed `google-api-python-client` Discovery v3 client, with mocked HTTP responses. It captures the real outgoing REST request, including the encoded `fields` parameter, across both commits and both completeness states.

The original Agno Google Drive unit test module also runs after installing the historical source. The archived successful run passed **55 tests**.

## Reproduce

Use the pinned [GitHub Actions workflow](../../.github/workflows/e4-agno.yml) for the complete build and replay. It retrieves the two original commits, installs Python 3.12 dependencies, executes the 20-case study, checks the official Google client, compares the original outputs, and runs the upstream Google Drive unit tests.

The exact successful dependency environment is stored in [`requirements.lock`](requirements.lock). After preparing both historical checkouts:

```bash
python -m pip install -e ./agno-after/libs/agno -r experiments/e4/requirements.lock

python experiments/e4/replay_agno.py --source agno-before --version before --output results/e4_before.json
python experiments/e4/replay_agno.py --source agno-after --version after --output results/e4_after.json

python experiments/e4/verify_pair.py results/e4_before.json results/e4_after.json --output results/e4_verification.json
python experiments/e4/replay_discovery_http.py --source agno-before --version before --output results/e4_discovery_before.json
python experiments/e4/replay_discovery_http.py --source agno-after --version after --output results/e4_discovery_after.json
python experiments/e4/publish_results.py --source results --dest evidence/e4 --check
```

The final [archived results](../../evidence/e4/) contain both original run JSON files, all five provider write receipts, the Google Discovery HTTP observations, exact execution provenance, and file hashes. The original successful [GitHub Actions run](https://github.com/risu-research/tool-evidence-loss/actions/runs/44956374734) retains the full test logs.

## Research boundary

The source-level defect and its repair are independently documented in Agno's public history. The study executes unmodified Agno search and upload methods using controlled API states and a local HTTP provider. The downstream consumer is a fixed test rule. Results describe the conditional effect of preserving and consuming a source completeness signal. Live Google Drive writes and model-driven decisions belong to separate evaluation settings.

Agno's source retains its original [Apache-2.0 license](https://github.com/agno-agi/agno/blob/9ff6d911131768470f91620ba40878a1f9372b61/libs/agno/LICENSE). The replay fetches original source by commit and stores study-owned test code in this repository.
