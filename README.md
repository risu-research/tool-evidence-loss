# When Tool Interfaces Lose Evidence Needed for Action

Reproducible research artifact for the S2AI 2026 paper *When Tool Interfaces Lose Evidence Needed for Action*.

A tool response can report an empty result after the provider has searched only part of the requested scope. We test how this missing coverage information travels through MCP interfaces and how a downstream write behaves when the caller relies on the displayed result.

## Experiments

| ID | Test | Recorded observation |
| --- | --- | --- |
| G7 | OpenAI Agents SDK and MCP over stdio | 16 controlled source cases; 8 source-qualified actions; 8 blocked |
| G8 | OpenAI Agents SDK and MCP over Streamable HTTP | Same 16 source cases across a second transport |
| G9 | Source-derived tool projection and matched visible transcripts | 8 matching pairs, 8 identical full visible transcripts, 5 request-binding challenges |
| E1 | Two public Google Drive MCP search implementations | Search-completeness field lost in one implementation and retained in the comparison |
| E2 | Full upstream MCP server over in-memory and stdio transports | Identical MCP outputs for complete and incomplete search conditions |
| E3 | Full upstream MCP search, follow-up write, and independent readback | 3 local provider writes in 5 scenarios, including one unsupported release marker |

G7 through G9 use the same original set of 16 controlled source cases. E1 through E3 extend the study with pinned third-party implementations. Each result identifies its exact execution boundary.

## Reproduce

Run the independently pinned experiments through GitHub Actions under **Actions**. The release workflow also publishes source files, frozen fixtures, compact evidence, and script-level commands inside this repository.

After the artifact import completes, use:

```bash
bash scripts/verify-local.sh
```

The GitHub Actions workflows run fresh installations for the official SDK and the full upstream MCP server tests.

## Scope

- G7 and G8: installed SDKs, controlled provider fixtures, deterministic consumers, local effect ledgers.
- G9: independent local Node.js replay with pre-fixed cases and a full visible-transcript comparison.
- E1: source-level replay of two externally authored implementations.
- E2: installed third-party MCP server with official MCP clients and two transports.
- E3: installed third-party MCP server, stdio client, loopback HTTP test provider, actual mocked write operation, and state readback.
- Production frequency: unmeasured. Provider data and follow-up policies are controlled test conditions.

## Source provenance

G7 and G8 are recovered from pinned public research-execution commits. E1, E2, and E3 record source commits of the external Google Drive MCP implementations. Each experiment carries its run links and origin checks in [docs/provenance.md](docs/provenance.md).

## Article and artifact status

The article and this runnable artifact have separate publication records. The repository contains experimental source, input fixtures, execution receipts, and reproduction instructions. Citation and archival identifiers can be added when a versioned artifact release is prepared.
