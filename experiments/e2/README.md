# E2 · Full MCP runtime replay

Source: `piotr-agier/google-drive-mcp` commit `9509fb8bba8ad15f7cdb79a54dbd850c13eb058b`.

The test modules run the installed upstream server through the original SDK's in-memory transport and through independent stdio child processes.

The complete and incomplete empty-search inputs produce identical MCP `tools/call` outputs. A page token, a returned file, and an upstream error remain observable.

Original [successful Actions run](https://github.com/risu-research/stc-exec-2609/actions/runs/44942276579). Frozen JSON results appear in [evidence/e2](../../evidence/e2/).
