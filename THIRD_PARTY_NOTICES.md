# Third-party components

E1 contains verbatim extracts from the search handler in [`piotr-agier/google-drive-mcp`](https://github.com/piotr-agier/google-drive-mcp/blob/9509fb8bba8ad15f7cdb79a54dbd850c13eb058b/src/tools/drive.ts) and the file-list tool in [`domdomegg/google-drive-mcp`](https://github.com/domdomegg/google-drive-mcp/blob/395971084f5d8504e5b2934dab4c2cc6e2f210b5/src/tools/files-list.ts). Both upstream projects declare MIT licensing. The exact source commits and Git blob hashes are recorded in `docs/provenance.md`.

E2 and E3 clone the original upstream server at its pinned commit during verification. Locally authored test modules supply controlled API responses and MCP client interactions.

Node.js, the OpenAI Agents SDK, the MCP SDK, TypeScript, and Google API client packages retain their respective upstream licenses. Their installed versions are fixed by source-level lockfiles and published upstream package metadata.

The target project's complete MIT license text is preserved at [`third_party/piotr-agier-google-drive-mcp-LICENSE.txt`](third_party/piotr-agier-google-drive-mcp-LICENSE.txt).
