# Source and execution provenance

| ID | Source pin | Original execution |
| --- | --- | --- |
| G7 | [`formal-exec-2609` commit `8ad25af`](https://github.com/risu-research/formal-exec-2609/commit/8ad25af26a2f6d78f98a5c5c0b280220377254e8), `runs/s2ai-official-runtime/` | [Actions run 36913980536](https://github.com/risu-research/formal-exec-2609/actions/runs/36913980536) |
| G8 | [`stc-exec-2609` commit `dadb941`](https://github.com/risu-research/stc-exec-2609/commit/dadb9417bec502ba620b8b081343325f99b48cbb), `transport-confirm/` | [Actions run 36917142435](https://github.com/risu-research/stc-exec-2609/actions/runs/36917142435) |
| G9 | Original frozen G8 fixtures plus local one-shot scripts, 2026-10-14 | `experiments/g9/preexecution-manifest.sha256` and original result JSON |
| E1 target | [`piotr-agier/google-drive-mcp` commit `9509fb8`](https://github.com/piotr-agier/google-drive-mcp/commit/9509fb8bba8ad15f7cdb79a54dbd850c13eb058b) | E1 handler tests, 10 passing assertions |
| E1 control | [`domdomegg/google-drive-mcp` commit `3959710`](https://github.com/domdomegg/google-drive-mcp/commit/395971084f5d8504e5b2934dab4c2cc6e2f210b5) | E1 registration tests, 5 passing assertions |
| E2 | `piotr-agier/google-drive-mcp` @ `9509fb8`, original full server | [Actions run 44942276579](https://github.com/risu-research/stc-exec-2609/actions/runs/44942276579), 6 passing tests |
| E3 | `piotr-agier/google-drive-mcp` @ `9509fb8`, original full server | [Actions run 44943185337](https://github.com/risu-research/stc-exec-2609/actions/runs/44943185337), 6 passing tests |

E2 tests originate from [commit `75f3038`](https://github.com/risu-research/stc-exec-2609/commit/75f3038e59383807f0b43ad22466e66000ad4d56). E3 tests originate from [commit `529a220`](https://github.com/risu-research/stc-exec-2609/commit/529a2209b274d637fea273020c15cc7dd4a52633). The external MCP server source remains at its upstream pin; the separate experiment modules are copied into the test directory during compilation.

## Artifact hashes

- G7 original hosted ZIP: `1c322f91c083d6bbb3f65b8432203d1cb36f22e9f6987b2152e78818dafbd406`
- G8 original hosted ZIP: `290ff375e52f341be68e052475d47533cb654be4d7b7f9f3fe64d0fd1bb7f63c`
- G9 original one-shot ZIP: `1192610553db32b10abc97b19840a0c9a91ebc58b16a5f9202251994fbbacc15`
- E2 final GitHub artifact: `ef7aba03deaa61aa7c1210c27745ec7490d3a16c7f6a7f7202f196ef8554d46c`
- E3 final GitHub artifact: `49837a369881a2059e399c038053910ae94bb74ca9912843eeffb478b2e4ac8e`

## Third-party source

[Google Drive files.list](https://developers.google.com/workspace/drive/api/reference/rest/v3/files/list) documents `incompleteSearch`. The [target MIT license](https://github.com/piotr-agier/google-drive-mcp/blob/9509fb8bba8ad15f7cdb79a54dbd850c13eb058b/LICENSE) and [control project package metadata](https://github.com/domdomegg/google-drive-mcp/blob/395971084f5d8504e5b2934dab4c2cc6e2f210b5/package.json) identify the upstream licensing terms. The two upstream source snippets under `experiments/e1/` preserve their original content.
