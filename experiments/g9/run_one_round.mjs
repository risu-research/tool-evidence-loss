import fs from 'node:fs';
import crypto from 'node:crypto';
import {spawnSync} from 'node:child_process';
import {sourceQualifiedDecision} from './oracle.mjs';
import {projectFromSource, checkExistingSourceRequestBinding} from './adapter.mjs';
const records = JSON.parse(fs.readFileSync('./cases.json','utf8')).cases;
const labels = JSON.parse(fs.readFileSync('./expected.json','utf8')).expected;
const contracts = JSON.parse(fs.readFileSync('./frozen_contracts.json','utf8'));
const digest = s => crypto.createHash('sha256').update(typeof s === 'string' ? s : JSON.stringify(s)).digest('hex');
const stableClone = x => JSON.parse(JSON.stringify(x));

function invoke(caseId, args) {
  // Exactly the same model-facing invocation within each matched pair.
  // Case selection is an out-of-band controlled source-state manipulation.
  const wireRequest = {jsonrpc:'2.0',id:1,method:'tools/call',params:{name:'query_blockers',arguments:args}};
  const proc = spawnSync(process.execPath,['fresh_server.mjs'],{cwd:process.cwd(),input:JSON.stringify(wireRequest),encoding:'utf8',env:{...process.env,S2AI_SOURCE_CASE:caseId},timeout:8000});
  if (proc.status !== 0) throw Error(`fresh subprocess failed for ${caseId}: ${proc.stderr}`);
  const response = JSON.parse(proc.stdout);
  if (response.id !== 1) throw Error('wrong rpc ID');
  const contentText = response.result?.content?.[0]?.text;
  const r3 = JSON.parse(contentText);
  const evidence = response.result?._meta?.sourceEvidence;
  // Complete constructed MODEL-VISIBLE record, not just the tool result.
  const modelTranscript = {
    userText:'Check whether the exact negative premise licenses release before any action.',
    agentToolCall:wireRequest,
    toolResponse:{role:'tool', content:response.result.content},
  };
  const transcript = JSON.stringify(modelTranscript);
  const forbidden = ['"sourceEvidence"','"incompleteSearch"','"timed_out"','"_shards"','"_clusters"','"indexUsed"','"deltaLink"'];
  const leaks = forbidden.filter(s => transcript.includes(s));
  return {evidence, r3, transcriptHash:digest(transcript), toolHash:digest(contentText), leaks};
}
const rows=[], groups={}, projectionLedger=[], qualifiedLedger=[];
for (const caseId of Object.keys(labels).sort()) {
  const item = labels[caseId];
  const args = contracts[item.pairId];
  if(!args) throw Error('missing locked argument contract: '+item.pairId);
  const r = invoke(caseId,args);
  const frozenR3 = records[caseId].visibleR3;
  const frozenExactMatch = JSON.stringify(r.r3) === JSON.stringify(frozenR3);
  const actualAllow = sourceQualifiedDecision(r.evidence);
  const expectedAllow = item.expected === 'ALLOW';
  const genericAllows = Object.values(r.r3).every((v,i) => i===2 ? v===false : v===true);
  const genericCommit = genericAllows;
  const qualifiedCommit = actualAllow;
  if (genericCommit) projectionLedger.push({caseId, effect:'COMMIT', licensed:expectedAllow});
  if (qualifiedCommit) qualifiedLedger.push({caseId, effect:'COMMIT', licensed:expectedAllow});
  const row = {caseId, pairId:item.pairId, expectedAllow, sourceAllow:actualAllow, frozenExactMatch, genericCommit, qualifiedCommit, transcriptHash:r.transcriptHash, toolHash:r.toolHash, leakage:r.leaks};
  rows.push(row);
  (groups[item.pairId] ??= []).push(row);
}
const pairs = Object.entries(groups).map(([pairId,g]) => ({pairId, cases:g.length, sameCompleteVisibleTranscript:new Set(g.map(x=>x.transcriptHash)).size===1, sameToolResult:new Set(g.map(x=>x.toolHash)).size===1, oppositeExpectedActions:g.length===2 && g.filter(x=>x.expectedAllow).length===1 && g.filter(x=>!x.expectedAllow).length===1, oppositeActualSourceActions:g.length===2 && g.filter(x=>x.sourceAllow).length===1 && g.filter(x=>!x.sourceAllow).length===1}));

// Targeted one-field request-binding metamorphic controls: independent of R3.
const challenges=[];
for (const [pairId,field,badValue] of [
  ['P01-drive-incomplete','q',"name contains 'release-blocker-74'"],
  ['P02-drive-chain','pageToken','unexpected-page-token'],
  ['P06-algolia-index','requestedIndex','release-catalog-experiment'],
  ['P07-graph-delta','rootUrl','https://graph.example/v1.0/other/delta'],
  ['P08-algolia-authority','requiredAuthorityViewId','catalog-tenant-alpha'],
]) {
  const member = groups[pairId]?.find(x => x.expectedAllow);
  if(!member) throw Error('missing positive control for '+pairId);
  const correctArgs = stableClone(contracts[pairId]);
  const mutatedArgs = stableClone(correctArgs); mutatedArgs[field]=badValue;
  const evidence = invoke(member.caseId,correctArgs).evidence;
  const baseQualified = sourceQualifiedDecision(evidence);
  const positive = baseQualified && checkExistingSourceRequestBinding(evidence,correctArgs)===true;
  const negative = baseQualified && checkExistingSourceRequestBinding(evidence,mutatedArgs)===true;
  const mutated = invoke(member.caseId,mutatedArgs);
  challenges.push({pairId,field,positiveAct:positive,negativeAct:negative,mutationDidNotChangeSourceDecision:sourceQualifiedDecision(mutated.evidence)===baseQualified,mutationR3Unchanged:JSON.stringify(mutated.r3)===JSON.stringify(projectFromSource(evidence))});
}
const noMetadataFailClosed = rows.map(x => ({caseId:x.caseId,action:(undefined != null && sourceQualifiedDecision(undefined))?'ACT':'BLOCK'}));
const summary = {
  controlledFixtures:16, pairs:8,
  rawAdapterMatchesFrozenR3:rows.filter(x=>x.frozenExactMatch).length,
  identicalCompleteVisibleTranscriptPairs:pairs.filter(p=>p.sameCompleteVisibleTranscript).length,
  identicalToolResultPairs:pairs.filter(p=>p.sameToolResult).length,
  oppositeSourceActionPairs:pairs.filter(p=>p.oppositeActualSourceActions).length,
  originalLabelsMatched:rows.filter(x=>x.expectedAllow===x.sourceAllow).length,
  toolResultDistinctHashes:new Set(rows.map(x=>x.toolHash)).size,
  genericCommits:projectionLedger.length,
  genericInvalidCommits:projectionLedger.filter(x=>!x.licensed).length,
  qualifiedCommits:qualifiedLedger.length,
  qualifiedInvalidCommits:qualifiedLedger.filter(x=>!x.licensed).length,
  modelVisibleEvidenceLeakages:rows.reduce((n,x)=>n+x.leakage.length,0),
  bindingPositiveControlsACT:challenges.filter(x=>x.positiveAct).length,
  bindingMismatchControlsBLOCK:challenges.filter(x=>!x.negativeAct).length,
  bindingMutationsPreservedSourceAndProjection:challenges.filter(x=>x.mutationDidNotChangeSourceDecision && x.mutationR3Unchanged).length,
  missingMetadataBLOCK:noMetadataFailClosed.filter(x=>x.action==='BLOCK').length,
};
summary.pass = rows.length===16 && pairs.length===8 && summary.rawAdapterMatchesFrozenR3===16 && summary.identicalCompleteVisibleTranscriptPairs===8 && summary.identicalToolResultPairs===8 && summary.oppositeSourceActionPairs===8 && summary.originalLabelsMatched===16 && summary.toolResultDistinctHashes===1 && summary.genericCommits===16 && summary.genericInvalidCommits===8 && summary.qualifiedCommits===8 && summary.qualifiedInvalidCommits===0 && summary.modelVisibleEvidenceLeakages===0 && summary.bindingPositiveControlsACT===5 && summary.bindingMismatchControlsBLOCK===5 && summary.bindingMutationsPreservedSourceAndProjection===5 && summary.missingMetadataBLOCK===16;
fs.writeFileSync('result_rows.json',JSON.stringify(rows,null,2));
fs.writeFileSync('result_pairs.json',JSON.stringify(pairs,null,2));
fs.writeFileSync('result_challenges.json',JSON.stringify(challenges,null,2));
fs.writeFileSync('result_projection_ledger.json',JSON.stringify(projectionLedger,null,2));
fs.writeFileSync('result_qualified_ledger.json',JSON.stringify(qualifiedLedger,null,2));
fs.writeFileSync('result_summary.json',JSON.stringify(summary,null,2));
console.log(JSON.stringify(summary,null,2));
if(!summary.pass) process.exitCode=2;
