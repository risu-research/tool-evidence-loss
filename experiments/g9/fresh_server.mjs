/** Controlled independent source-side process.
 * CASE_ID is selected out-of-band, NEVER supplied as model-visible tool argument.
 * JSON-RPC style wire, with source evidence in runtime-only _meta.
 * This is a local protocol REPLAY, not a new official MCP/Agents SDK execution.
 */
import fs from 'node:fs';
import {projectFromSource} from './adapter.mjs';
const records = JSON.parse(fs.readFileSync(new URL('./cases.json', import.meta.url),'utf8')).cases;
const rec = records[process.env.S2AI_SOURCE_CASE];
if (!rec) throw Error('unknown controlled source state');
let request = '';
for await (const chunk of process.stdin) request += chunk.toString('utf8');
const data = JSON.parse(request);
if (data.method !== 'tools/call' || data.params?.name !== 'query_blockers' || !data.params?.arguments) throw Error('invalid tool invocation');
const visible = projectFromSource(rec.sourceEvidence);
const response = {jsonrpc:'2.0', id:data.id, result:{content:[{type:'text',text:JSON.stringify(visible)}], _meta:{sourceEvidence:rec.sourceEvidence}}};
process.stdout.write(JSON.stringify(response));
