# Source and execution provenance

| ID | Source pin | Original execution |
| --- | --- | --- |
| Discovery 37 | [`closureprobe` rc3 commit `12fae2c`](https://github.com/risu-research/closureprobe/commit/12fae2c0cb0909a43f487323fb00e7372b1f3377), `corpus/v0.3/cases.json` | 2026-08-15 original 50-case release, 37 source observations; [row replay](../experiments/discovery37/README.md) |
| G7 | [`formal-exec-2609` commit `8ad25af`](https://github.com/risu-research/formal-exec-2609/commit/8ad25af26a2f6d78f98a5c5c0b280220377254e8), `runs/s2ai-official-runtime/` | [Actions run 36913980536](https://github.com/risu-research/formal-exec-2609/actions/runs/36913980536) |
| G8 | [`stc-exec-2609` commit `dadb941`](https://github.com/risu-research/stc-exec-2609/commit/dadb9417bec502ba620b8b081343325f99b48cbb), `transport-confirm/` | [Actions run 36917142435](https://github.com/risu-research/stc-exec-2609/actions/runs/36917142435) |
| G9 | Original frozen G8 fixtures plus local one-shot scripts, 2026-10-14 | `experiments/g9/preexecution-manifest.sha256` and original result JSON |
| E1 target | [`piotr-agier/google-drive-mcp` commit `9509fb8`](https://github.com/piotr-agier/google-drive-mcp/commit/9509fb8bba8ad15f7cdb79a54dbd850c13eb058b) | E1 handler tests, 10 passing assertions |
| E1 control | [`domdomegg/google-drive-mcp` commit `3959710`](https://github.com/domdomegg/google-drive-mcp/commit/395971084f5d8504e5b2934dab4c2cc6e2f210b5) | E1 registration tests, 5 passing assertions |
| E2 | `piotr-agier/google-drive-mcp` @ `9509fb8`, original full server | [Actions run 44942276579](https://github.com/risu-research/stc-exec-2609/actions/runs/44942276579), 6 passing tests |
| E4 | [`agno-agi/agno` before `bc563b7`, after `9ff6d91`](https://github.com/agno-agi/agno/pull/7824) | [Original Actions run 44956374734](https://github.com/risu-research/tool-evidence-loss/actions/runs/44956374734), 20 fixed cases; original Google Drive suite 55 tests |
| E5 | [`tony/agentgrep` before `9b5ccda`, after `6b2d346`](https://github.com/tony/agentgrep/pull/64) | [Original E5 run 44958664499](https://github.com/risu-research/tool-evidence-loss/actions/runs/44958664499), 20 controlled decisions and independent three-page traversal |
| E3 | `piotr-agier/google-drive-mcp` @ `9509fb8`, original full server | [Actions run 44943185337](https://github.com/risu-research/stc-exec-2609/actions/runs/44943185337), 6 passing tests |

E2 tests originate from [commit `75f3038`](https://github.com/risu-research/stc-exec-2609/commit/75f3038e59383807f0b43ad22466e66000ad4d56). E3 tests originate from [commit `529a220`](https://github.com/risu-research/stc-exec-2609/commit/529a2209b274d637fea273020c15cc7dd4a52633). The external MCP server source remains at its upstream pin; the separate experiment modules are copied into the test directory during compilation.

## Discovery 37 historical input identity

- Original corpus SHA-256: `f1d0fd842738a74eb30978164cd68500fa11a30af2d7899a50ef0dd23f19e70a`
- Original corpus Git blob: `f262f6150d8fc97249e88f01d6db1f914d7d1b82`
- Original schema SHA-256: `b872ffc88a3f0e32b1af8eb2370279aeadfef305488bfc577b8cda3746a91934`
- Original license SHA-256: `7d8fb569801df15ded2684780ee4f3c7135dd72d3d504b9b4957b2ec95a13ead`
- Full original corpus: 50 cases, including 37 source observations and 13 trace records
- Original licensed source observations: 9
- Original producer-profile verification: `node dist/src/cli.js corpus verify corpus/v0.3/cases.json` at the pinned historical commit
- Independent Table II row and aggregate replay: `scripts/replay_discovery37.py`

## E4 external repair identity

- Independent defect report: [Agno #7823](https://github.com/agno-agi/agno/issues/7823), opened 2026-05-06
- Merged repair: [Agno PR #7824](https://github.com/agno-agi/agno/pull/7824), merged 2026-05-19
- First-parent source: `bc563b724c2ea39368ca99b6cd45d36a64a7b1c5`
- Merged source: `9ff6d911131768470f91620ba40878a1f9372b61`
- Source file: `libs/agno/agno/tools/google/drive.py`
- Original before blob: `e7bf38548f561d3a5264a8da7e29b4905f17cea4`
- Original after blob: `654c4c4697191612f3cd72e32627c3e1a564eeba`
- Original before file SHA-256: `61d188540a7a0c2876e3633c803c9cc5c3b1ba33d4d50f5fb0c8230b85602e4f`
- Original after file SHA-256: `b0d8a8e9c69cc03c1537e0864c435b6fc5e5ef9db38b647f2a1e3deed7152c9e`
- Published results: [`evidence/e4`](../evidence/e4/)
- Original successful run and raw execution logs: [Actions #44956374734](https://github.com/risu-research/tool-evidence-loss/actions/runs/44956374734)
- GitHub Actions artifact ID: `14727329325`, SHA-256: `aa54e9cd963c212fbcf616cb1e0a542db304f6bed7948a84e850c2ba0a050934`
- Installed library versions: [`requirements.lock`](../experiments/e4/requirements.lock)

## Artifact hashes

- G7 original hosted ZIP: `1c322f91c083d6bbb3f65b8432203d1cb36f22e9f6987b2152e78818dafbd406`
- G8 original hosted ZIP: `290ff375e52f341be68e052475d47533cb654be4d7b7f9f3fe64d0fd1bb7f63c`
- G9 original one-shot ZIP: `1192610553db32b10abc97b19840a0c9a91ebc58b16a5f9202251994fbbacc15`
- E2 final GitHub artifact: `ef7aba03deaa61aa7c1210c27745ec7490d3a16c7f6a7f7202f196ef8554d46c`
- E3 final GitHub artifact: `49837a369881a2059e399c038053910ae94bb74ca9912843eeffb478b2e4ac8e`

## Third-party source

[Google Drive files.list](https://developers.google.com/workspace/drive/api/reference/rest/v3/files/list) documents `incompleteSearch`. The [target MIT license](https://github.com/piotr-agier/google-drive-mcp/blob/9509fb8bba8ad15f7cdb79a54dbd850c13eb058b/LICENSE) and [control project package metadata](https://github.com/domdomegg/google-drive-mcp/blob/395971084f5d8504e5b2934dab4c2cc6e2f210b5/package.json) identify the upstream licensing terms. The two upstream source snippets under `experiments/e1/` preserve their original content.

## E5 external paging source identity

- Original independent issue: [tony/agentgrep #55](https://github.com/tony/agentgrep/issues/55), opened 2026-06-13
- Merged change: [PR #64](https://github.com/tony/agentgrep/pull/64), merged 2026-06-14
- Before revision: `9b5ccda643f2bf84c49b0ec1c4ae300b681a5f83`
- After revision: `6b2d3465767421f113acf684473384db00ebf619`
- Historical source file: `src/agentgrep/mcp/tools/search_tools.py`
- Before Git blob: `61d8f7837bef4ab35b91044b46e78e3f8e3fa197`
- After Git blob: `14da30d259562549038e805de760359a9120e7b5`
- Reproduction: original Python 3.14 FastMCP server and frozen upstream `uv.lock` in each checkout
- First full successful E5 run: [Actions #44958664499](https://github.com/risu-research/tool-evidence-loss/actions/runs/44958664499)
- Runner artifact ID: `14727624289`, SHA-256: `6e11463b7299b619d9f80f125aa7c677d0a717999525761c6237b5b4eefd4735`
- Public result files: [`evidence/e5`](../evidence/e5/)
