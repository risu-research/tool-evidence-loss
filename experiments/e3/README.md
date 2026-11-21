# E3 · Downstream write and independent readback

Source: `piotr-agier/google-drive-mcp` commit `9509fb8bba8ad15f7cdb79a54dbd850c13eb058b`.

The upstream MCP server runs in an independent stdio process. A local HTTP provider serves controlled Drive-style responses. The client calls `search`, conditionally calls `createFolder`, then calls `listFolder` to read the stored result.

Five conditions produce three local HTTP writes. The projection-only rule writes after an incomplete empty search. A source-informed test comparator withholds that write.

Original [successful Actions run](https://github.com/risu-research/stc-exec-2609/actions/runs/44943185337). The local HTTP write receipts appear in [evidence/e3](../../evidence/e3/).
