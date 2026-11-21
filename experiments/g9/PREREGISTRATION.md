# G9 One-shot adapter + complete-transcript + binding challenge

Date: 2026-10-14. Baseline immutable input: G8 cases.json, expected.json, oracle.mjs from uploaded Actions artifact. This round is LOCAL Node 22 protocol-replay harness, not an additional official @openai/agents binary run. Prior G8 tested official installed Agents/MCP packages.

Hypothesis H1: Provider-independent generic R3 projection calculated from SOURCE fixtures (without consulting rec.visibleR3 or expected labels) is identical in each of the eight preexisting matched pairs, despite opposite original source-qualified decisions.

Hypothesis H2: If both pair members are queried with the SAME user intent, tool name, tool arguments, tool call ID, and fresh-process, model-facing result, their COMPLETE model-visible transcript is identical pairwise. Fixture identity is selected out-of-band as source state, NEVER included in model-facing invocation arguments. This addresses the prior G8 distinct caseId call-argument confound.

Hypothesis H3: A runtime gate preserving sourceEvidence rejects all original must-block cases and admits all original licensed cases. A projection-only action policy acts on all generic R3 responses, yielding eight invalid commits in this deliberately counterfactual test set. Side effects are LOCAL ledger entries only.

Hypothesis H4: In the five scenarios with a raw source-identifiable binding field (Drive query, Drive traversal root, Algolia index, Graph delta root, Algolia authority), mismatching ONE consumer request field while preserving the original positive source response is rejected by a binding-aware gate. A missing source-evidence channel must fail closed.

Locked success conditions before running: 16 generated R3 projections match their original frozen R3 values; 8/8 same FULL transcript hashes within pairs; 8/8 original pairwise opposite semantic decisions; 16 projection ACT, 8 invalid local ledger commits; 8 qualified ACT, 8 BLOCK, 0 invalid commits; 5/5 binding-positive controls ACT and 5/5 mutated negative controls BLOCK; 16/16 missing metadata BLOCK; 0 source metadata leakage in rendered model input; no iterative repair/tuning after observing test results. Results may be labeled PASS or FAIL, with shortcomings described.

Limitations fixed before evaluation: controlled source fixtures, no live production SaaS requests, no stochastic language-model decision, original source-level schema not independently verified by an external vendor, 'exact_zero' is the frozen coarse R3 field and is not itself an assertion of source-qualified query completeness. Elasticsearch original fixture does not carry a query receipt, so no exact query-binding claim for Elasticsearch.
