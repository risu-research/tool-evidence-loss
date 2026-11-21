import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import { spawn } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { Agent, MCPServerStreamableHttp, run } from '@openai/agents';
import { ScriptedModel, functionCall, assistantMessage } from '@openai/agents/testing';
import { sourceQualifiedDecision } from './oracle.mjs';

const here = path.dirname(fileURLToPath(import.meta.url));
const records = JSON.parse(fs.readFileSync(path.join(here, 'cases.json'), 'utf8')).cases;
const expected = JSON.parse(fs.readFileSync(path.join(here, 'expected.json'), 'utf8')).expected;
const caseIds = Object.keys(records).sort();
const sha256 = (v) => crypto.createHash('sha256').update(typeof v === 'string' ? v : JSON.stringify(v)).digest('hex');
const forbidden = ['incompleteSearch', 'timed_out', '_shards', '_clusters', 'indexUsed', 'deltaLink', 'authorityViewId', 'sourceEvidence'];

function projectionAllows(r3) {
  return r3?.final_empty === true &&
    r3?.exec_ok === true &&
    r3?.continuation_present === false &&
    r3?.root_request === true &&
    r3?.exact_zero === true;
}

function startServer() {
  return new Promise((resolve, reject) => {
    const child = spawn(process.execPath, [path.join(here, 'http_server.mjs')], {
      cwd: here,
      stdio: ['ignore', 'pipe', 'pipe'],
    });
    let settled = false;
    const timer = setTimeout(() => {
      if (!settled) reject(new Error('HTTP MCP server readiness timeout'));
    }, 10000);
    child.stdout.setEncoding('utf8');
    child.stderr.setEncoding('utf8');
    child.stdout.on('data', (data) => {
      process.stderr.write(`[server] ${data}`);
      if (!settled && data.includes('READY ')) {
        settled = true;
        clearTimeout(timer);
        resolve(child);
      }
    });
    child.stderr.on('data', (data) => process.stderr.write(`[server-err] ${data}`));
    child.on('exit', (code) => {
      if (!settled) {
        settled = true;
        clearTimeout(timer);
        reject(new Error(`HTTP MCP server exited before readiness: ${code}`));
      }
    });
  });
}

const child = await startServer();
const mcpServer = new MCPServerStreamableHttp({
  name: 'runtime-transport-confirm',
  url: 'http://127.0.0.1:8765/mcp',
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

const rows = [];
const projectionLedger = [];
const sourceLedger = [];
try {
  await mcpServer.connect();
  let i = 0;
  for (const caseId of caseIds) {
    const model = new ScriptedModel([
      [functionCall('query_blockers', { caseId }, { callId: `call_${String(i).padStart(2, '0')}` })],
      [assistantMessage('done')],
    ]);
    const agent = new Agent({
      name: `TransportConfirm-${i}`,
      model,
      mcpServers: [mcpServer],
      toolUseBehavior: 'run_llm_again',
    });
    const result = await run(agent, 'Call the query tool once, then finish.');
    if (model.remainingSteps !== 0) throw new Error(`Unconsumed model steps for ${caseId}: ${model.remainingSteps}`);
    const outputItems = result.newItems.filter((item) => item?.type === 'tool_call_output_item');
    if (outputItems.length !== 1) throw new Error(`Expected one tool output item for ${caseId}, got ${outputItems.length}`);
    const outputItem = outputItems[0];
    const toolOutput = outputItem.output;
    const customData = outputItem.customData;
    if (!customData || !['ACT', 'BLOCK'].includes(customData.sourceDecision)) throw new Error(`Missing source decision for ${caseId}`);

    const modelVisibleSerialized = JSON.stringify(toolOutput);
    const modelVisibleSha256 = sha256(modelVisibleSerialized);
    const secondRequest = model.calls[1]?.request;
    if (!secondRequest) throw new Error(`Missing second model call for ${caseId}`);
    const secondInputSerialized = JSON.stringify(secondRequest.input);
    const leakedKeys = forbidden.filter((key) => secondInputSerialized.includes(key));
    const expectedDecision = expected[caseId]?.expected === 'ALLOW' ? 'ACT' : 'BLOCK';
    if (customData.sourceDecision !== expectedDecision) throw new Error(`Decision mismatch for ${caseId}`);
    const projectionDecision = projectionAllows(records[caseId].visibleR3) ? 'ACT' : 'BLOCK';
    if (projectionDecision === 'ACT') projectionLedger.push({ caseId, effect: 'COMMIT', expectedDecision });
    if (customData.sourceDecision === 'ACT') sourceLedger.push({ caseId, effect: 'COMMIT', expectedDecision });
    rows.push({ caseId, modelVisibleSerialized, modelVisibleSha256, customData, expectedDecision, projectionDecision, leakedKeys, secondModelInputSha256: sha256(secondInputSerialized) });
    i += 1;
  }
} finally {
  try { await mcpServer.close(); } catch {}
  child.kill('SIGTERM');
}

const distinctVisibleHashes = [...new Set(rows.map((r) => r.modelVisibleSha256))];
const leakageCases = rows.filter((r) => r.leakedKeys.length > 0);
const projectionInvalidCommits = projectionLedger.filter((x) => x.expectedDecision === 'BLOCK').length;
const sourceInvalidCommits = sourceLedger.filter((x) => x.expectedDecision === 'BLOCK').length;
const sourceAct = rows.filter((r) => r.customData.sourceDecision === 'ACT').length;
const sourceBlock = rows.filter((r) => r.customData.sourceDecision === 'BLOCK').length;
const projectionAct = rows.filter((r) => r.projectionDecision === 'ACT').length;
const summary = {
  transport: 'official Streamable HTTP over loopback TCP',
  cases: rows.length,
  distinctModelVisibleToolOutputHashes: distinctVisibleHashes,
  modelVisibleSourceEvidenceLeakageCases: leakageCases.length,
  sourceQualifiedActCount: sourceAct,
  sourceQualifiedBlockCount: sourceBlock,
  projectionActCount: projectionAct,
  projectionInvalidCommits,
  sourceInvalidCommits,
  allExpectedMatched: rows.every((r) => r.customData.sourceDecision === r.expectedDecision),
  pass: rows.length === 16 && distinctVisibleHashes.length === 1 && leakageCases.length === 0 && sourceAct === 8 && sourceBlock === 8 && projectionAct === 16 && projectionInvalidCommits === 8 && sourceInvalidCommits === 0,
};
fs.writeFileSync(path.join(here, 'http-rows.json'), JSON.stringify(rows, null, 2));
fs.writeFileSync(path.join(here, 'http-projection-ledger.json'), JSON.stringify(projectionLedger, null, 2));
fs.writeFileSync(path.join(here, 'http-source-ledger.json'), JSON.stringify(sourceLedger, null, 2));
fs.writeFileSync(path.join(here, 'http-summary.json'), JSON.stringify(summary, null, 2));
console.log(JSON.stringify(summary, null, 2));
if (!summary.pass) process.exit(2);
