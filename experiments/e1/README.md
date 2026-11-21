# E1 · Public search-handler replay

The original search branch from `piotr-agier/google-drive-mcp` requests `corpora=allDrives` and omits the Google Drive `incompleteSearch` field. The independent implementation from `domdomegg/google-drive-mcp` requests and returns the field by default.

`run_replay.cjs` executes the first project's fixed search branch with controlled API responses. `run_control.cjs` executes the second project's fixed registration callback. Recorded results are under [`../../evidence/e1`](../../evidence/e1/).

```bash
node run_replay.cjs
node run_control.cjs
```

The scripts use TypeScript for compilation. The source files are attributed in [`../../docs/provenance.md`](../../docs/provenance.md).

E1 tests source-level handlers. E2 follows the same upstream search implementation through a complete installed MCP server and two client transports.
