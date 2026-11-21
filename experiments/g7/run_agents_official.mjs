import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import { fileURLToPath } from 'node:url';
import { Agent, MCPServerStdio, run } from '@openai/agents';
import { ScriptedModel, functionCall, assistantMessage } from '@openai/agents/testing';
import { sourceQualifiedDecision } from './source_oracle.mjs';

const here = path.dirname(fileURLToPath(import.meta.url));
const serverCases = JSON.parse(fs.readFileSync(path.join(here, 'server_cases.json'), 'utf8')).cases;
const expected = JSON.parse(fs.readFileSync(path.join(here, 'expected_sealed.json'), 'utf8')).expected;
const caseIds = Object.keys(serverCases).sort();
const sha256 = (v) => crypto.createHash('sha256').update(typeof v === 'string' ? v : JSON.stringify(v)).digest('hex');
const forbidden = ['incompleteSearch', 'timed_out', '_shards', '_clusters', 'indexUsed', 'deltaLink', 'authorityViewId', 'sourceEvidence'];

function projectionAllows(r3) {
  return r3?.final_empty === true &&
    r3?.exec_ok === true &&
    r3?.continuation_present === false &&
    r3?.root_request === true &&
    r3?.exact_zero === true;
}

const mcpServer = new MCPServerStdio({
  name: 's2ai-official-runtime-fixture',
  command: process.execPath,
  args: [path.join(here, 'mcp_server_official.mjs')],
  cwd: here,
  cacheToolsList: false,
  customDataExtractor: (context) => {
    const sourceEvidence = context.resultMeta?.sourceEvidence;
    return {
      sourceDecision: sourceQualifiedDecision(sourceEvidence) ? 'ACT' : 'BLOCK',
      sourceEvidenceSha256: sha256(sourceEvidence ?? null),
      modelVisibleOutputSha256: sha256(context.toolOutput ?? null),
    };
  },
});

await mcpServer.connect();
const rows = [];
const projectionLedger = [];
const sourceLedger = [];
try {
  let i = 0;
  for (const caseId of caseIds) {
    const model = new ScriptedModel([
      [functionCall('query_blockers', { caseId }, { callId: `call_${String(i).padStart(2, '0')}` })],
      [assistantMessage('done')],
    ]);
    const agent = new Agent({
      name: `S2AIConfirmatory-${i}`,
      model,
      mcpServers: [mcpServer],
      toolUseBehavior: 'run_llm_again',
    });

    const result = await run(agent, 'Check the blocker-query tool once, then finish.');
    if (model.remainingSteps !== 0) throw new Error(`Unconsumed model steps for ${caseId}: ${model.remainingSteps}`);

    const outputItems = result.newItems.filter((item) => item?.type === 'tool_call_output_item');
    if (outputItems.length !== 1) throw new Error(`Expected exactly one tool output item for ${caseId}, got ${outputItems.length}`);
    const outputItem = outputItems[0];
    const toolOutput = outputItem.output;
    const customData = outputItem.customData;
    if (!customData || !['ACT', 'BLOCK'].includes(customData.sourceDecision)) {
      throw new Error(`Missing sourceDecision customData for ${caseId}`);
    }

    const modelVisibleSerialized = JSON.stringify(toolOutput);
    const modelVisibleSha256 = sha256(modelVisibleSerialized);
    const secondRequest = model.calls[1]?.request;
    if (!secondRequest) throw new Error(`Missing second model call for ${caseId}`);
    const secondInputSerialized = JSON.stringify(secondRequest.input);
    const leakedKeys = forbidden.filter((key) => secondInputSerialized.includes(key));

    const expectedDecision = expected[caseId]?.expected === 'ALLOW' ? 'ACT' : 'BLOCK';
    if (customData.sourceDecision !== expectedDecision) {
      throw new Error(`Source-qualified decision mismatch for ${caseId}: ${customData.sourceDecision} vs ${expectedDecision}`);
    }

    const projectionDecision = projectionAllows(serverCases[caseId].visibleR3) ? 'ACT' : 'BLOCK';
    if (projectionDecision === 'ACT') projectionLedger.push({ caseId, effect: 'COMMIT', expectedDecision });
    if (customData.sourceDecision === 'ACT') sourceLedger.push({ caseId, effect: 'COMMIT', expectedDecision });

    rows.push({
      caseId,
      modelVisibleSerialized,
      modelVisibleSha256,
      customData,
      expectedDecision,
      projectionDecision,
      leakedKeys,
      secondModelInputSha256: sha256(secondInputSerialized),
    });
    i += 1;
  }
} finally {
  await mcpServer.close();
}

const distinctVisibleHashes = [...new Set(rows.map((r) => r.modelVisibleSha256))];
const leakageCases = rows.filter((r) => r.leakedKeys.length > 0);
const projectionInvalidCommits = projectionLedger.filter((x) => x.expectedDecision === 'BLOCK').length;
const sourceInvalidCommits = sourceLedger.filter((x) => x.expectedDecision === 'BLOCK').length;
const summary = {
  runtime: 'official @openai/agents npm package + official @modelcontextprotocol/server npm package',
  cases: rows.length,
  distinctModelVisibleToolOutputHashes: distinctVisibleHashes,
  modelVisibleSourceEvidenceLeakageCases: leakageCases.length,
  sourceQualifiedActCount: rows.filter((r) => r.customData.sourceDecision === 'ACT').length,
  sourceQualifiedBlockCount: rows.filter((r) => r.customData.sourceDecision === 'BLOCK').length,
  projectionActCount: rows.filter((r) => r.projectionDecision === 'ACT').length,
  projectionInvalidCommits,
  sourceInvalidCommits,
  allExpectedMatched: rows.every((r) => r.customData.sourceDecision === r.expectedDecision),
  pass:
    rows.length === 16 &&
    distinctVisibleHashes.length === 1 &&
    leakageCases.length === 0 &&
    rows.filter((r) => r.customData.sourceDecision === 'ACT').length === 8 &&
    rows.filter((r) => r.customData.sourceDecision === 'BLOCK').length === 8 &&
    rows.filter((r) => r.projectionDecision === 'ACT').length === 16 &&
    projectionInvalidCommits === 8 &&
    sourceInvalidCommits === 0,
};

fs.writeFileSync(path.join(here, 'official-runtime-rows.json'), JSON.stringify(rows, null, 2));
fs.writeFileSync(path.join(here, 'projection-ledger.json'), JSON.stringify(projectionLedger, null, 2));
fs.writeFileSync(path.join(here, 'source-ledger.json'), JSON.stringify(sourceLedger, null, 2));
fs.writeFileSync(path.join(here, 'official-runtime-summary.json'), JSON.stringify(summary, null, 2));
console.log(JSON.stringify(summary, null, 2));
if (!summary.pass) process.exit(2);
