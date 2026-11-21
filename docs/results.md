# Results and interpretation

## Frozen source cases

G7 and G8 use 16 controlled source observations in eight matched pairs. The source-qualified policy permits eight actions and blocks eight. The projected four-field output permits all 16, including eight source-disallowed local ledger commits. Both runs use the installed Agents SDK and official MCP packages with distinct transports. Their tool-call arguments select individual fixture IDs.

G9 replays the same 16 cases with an out-of-band fixture selection and identical model-visible tool calls within each matched pair. All eight pairwise full visible transcripts match. Five pre-fixed request-binding perturbations are blocked by the test policy. This stage uses a local Node protocol replay.

## Public adapter tests

E1 locates a missing `incompleteSearch` field in a public MCP search adapter and contrasts it with a second implementation that preserves the field. E2 executes the complete pinned adapter in official MCP in-memory and stdio sessions, observing identical results for complete and incomplete empty searches.

E3 runs the same full MCP implementation through stdio with a local HTTP provider. The scripted consumer calls the real `createFolder` MCP tool after the empty search result. The HTTP provider stores the folder and supplies a separate readback through `listFolder`. In five constructed cases, three writes reach the provider; one write occurs under incomplete search coverage. A source-informed test comparator withholds that write and permits the fully covered control.

## Evidence boundary

The input states use selected test fixtures. E3 writes affect a loopback test provider. The downstream decision is a fixed test rule. The observed five-case count describes this experiment. The study leaves production prevalence, model autonomy, and live Google Drive behavior open for independent measurements.
