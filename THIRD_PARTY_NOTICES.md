# Third-party components

E1 contains verbatim extracts from the search handler in [`piotr-agier/google-drive-mcp`](https://github.com/piotr-agier/google-drive-mcp/blob/9509fb8bba8ad15f7cdb79a54dbd850c13eb058b/src/tools/drive.ts) and the file-list tool in [`domdomegg/google-drive-mcp`](https://github.com/domdomegg/google-drive-mcp/blob/395971084f5d8504e5b2934dab4c2cc6e2f210b5/src/tools/files-list.ts). Both upstream projects declare MIT licensing. The exact source commits and Git blob hashes are recorded in `docs/provenance.md`.

E2 and E3 clone the original upstream server at its pinned commit during verification. Locally authored test modules supply controlled API responses and MCP client interactions.

Node.js, the OpenAI Agents SDK, the MCP SDK, TypeScript, and Google API client packages retain their respective upstream licenses. Their installed versions are fixed by source-level lockfiles and published upstream package metadata.

The target project's complete MIT license text is preserved at [`third_party/piotr-agier-google-drive-mcp-LICENSE.txt`](third_party/piotr-agier-google-drive-mcp-LICENSE.txt).

## ClosureProbe corpus

The 37-case exploratory comparison uses the original public [ClosureProbe corpus](https://github.com/risu-research/closureprobe/blob/12fae2c0cb0909a43f487323fb00e7372b1f3377/corpus/v0.3/cases.json), originally released on 2026-08-15.

The complete frozen 50-case JSON, its schema, and the original Apache-2.0 notice are preserved under [`experiments/discovery37/source/`](experiments/discovery37/source/). The archived source and its original license retain their original copyright and attribution.

The R0–R3 replay script was separately authored for the S2AI Table II comparison, using the pinned source observations and their published source-qualified labels.

## Agno historical repair

E4 checks out [Agno](https://github.com/agno-agi/agno) at two fixed commits and executes its original `GoogleDriveTools` implementation. The original source is retrieved from the upstream repository during each replay and retains its [Apache-2.0 license](https://github.com/agno-agi/agno/blob/9ff6d911131768470f91620ba40878a1f9372b61/libs/agno/LICENSE).

The repository stores the separately authored replay code, original issue and repair identifiers, source-file hashes, and controlled execution results. The `google-api-python-client` dependencies are installed from their pinned package versions.

## agentgrep historical result pages

E5 checks out the original [agentgrep](https://github.com/tony/agentgrep) MCP implementation at its June 2026 pre-merge and merged commits. It runs the unmodified upstream search code in separate Python environments, using generated Codex session fixtures.

agentgrep retains the [original MIT license](https://github.com/tony/agentgrep/blob/6b2d3465767421f113acf684473384db00ebf619/LICENSE). The published experiment contains separately authored test programs, source pins, and synthetic results. Python runtime dependencies follow each upstream revision's `uv.lock`.
