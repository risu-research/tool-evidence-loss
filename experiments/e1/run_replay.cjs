'use strict';
// Executes the verbatim source of the upstream `search` switch branch, extracted
// from piotr-agier/google-drive-mcp @ 9509fb8bba8ad15f7cdb79a54dbd850c13eb058b
// src/tools/drive.ts, lines 846-944. Dependencies and Google API are test stubs.
// It is NOT a full installed MCP or live Google API test.
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const ts = loadTypeScript();

const basedir = __dirname;
const branch = fs.readFileSync(path.join(basedir, 'upstream_search_case.ts'), 'utf8');
const sha256 = x => crypto.createHash('sha256').update(x).digest('hex');
const branchHash = sha256(branch);
const surrounding = `async function handleTool(toolName, args, ctx) { switch(toolName) {\n${branch}\n} }\nhandleTool;`;
const code = ts.transpileModule(surrounding, {
  compilerOptions: {target: ts.ScriptTarget.ES2022, module: ts.ModuleKind.None}
}).outputText;

const SearchSchema = {
  safeParse(args) {
    if(!args || typeof args.query !== 'string' || args.query.length === 0)
      return {success: false, error:{errors:[{message: 'Search query is required'}]}};
    return {success:true, data:{...args,orderBy:args.orderBy||'modifiedTime desc'}};
  },
};
const context = vm.createContext({
  SearchSchema,
  errorResponse: message => ({content:[{type:'text',text:`Error: ${message}`}],isError:true}),
  escapeDriveQuery: s => s.replace(/\\/g,'\\\\').replace(/'/g,"\\'"),
  withRetry: async (callback) => callback({}),
  ALL_DRIVES_LIST_PARAMS: {corpora:'allDrives',includeItemsFromAllDrives:true,supportsAllDrives:true},
});
const handleTool = vm.runInContext(code, context, {timeout:5000});

function projectGoogleFields(data, fields) {
  // Faithfully models Google partial-response field selection for this fixture.
  // Only top-level files and nextPageToken need projection in this experiment.
  const allow = fields.split(',').map(s=>s.trim());
  const out = {};
  for(const key of ['files','nextPageToken','incompleteSearch']) {
    if(allow.some(x=>x===key || x.startsWith(key+'(')) && key in data)
      out[key]=data[key];
  }
  return out;
}

const fixtures = [
  {id:'E1_complete_zero',response:{files:[],incompleteSearch:false},projection:true},
  {id:'E2_incomplete_zero',response:{files:[],incompleteSearch:true},projection:true},
  {id:'E3_complete_zero_overshare',response:{files:[],incompleteSearch:false},projection:false},
  {id:'E4_incomplete_zero_overshare',response:{files:[],incompleteSearch:true},projection:false},
  {id:'E5_more_pages',response:{files:[],incompleteSearch:false,nextPageToken:'token-next'},projection:true},
  {id:'E6_hit_count',response:{files:[{id:'file-1',name:'safety-review.txt',mimeType:'text/plain'}],incompleteSearch:false},projection:true},
  {id:'E7_incomplete_with_hit',response:{files:[{id:'file-1',name:'safety-review.txt',mimeType:'text/plain'}],incompleteSearch:true},projection:true},
  {id:'E8_error',error:'mock upstream transport failure',projection:true}
];

(async () => {
  let outputs = [];
  for(const fixture of fixtures) {
    const received=[];
    const ctx = {
      runtimeConfig:{}, log(){},
      getDrive:()=>({files:{list: async (params)=>{
        received.push({...params});
        if(fixture.error) throw new Error(fixture.error);
        return {data:fixture.projection
          ? projectGoogleFields(fixture.response,params.fields)
          : structuredClone(fixture.response)};
      }}})
    };
    let output, raised=null;
    try {output=await handleTool('search',{query:'deployment blocker',rawQuery:false},ctx);} catch(e){raised=e.message;}
    outputs.push({id:fixture.id,
      upstream_raw:fixture.response||null,
      injected_API_behavior:fixture.projection?'respect_fields_selection':'overshare_for_robustness',
      requested_params:received[0]||null,
      provider_returned_fields: received[0] && !fixture.error
        ? Object.keys(fixture.projection?projectGoogleFields(fixture.response,received[0].fields):fixture.response):null,
      model_facing_result:output||null,
      model_facing_sha256:output?sha256(JSON.stringify(output)):null,
      raised
    });
  }
  const byId = Object.fromEntries(outputs.map(o=>[o.id,o]));
  const checks = {
    requests_all_drives: outputs.filter(o=>o.requested_params).every(o=>o.requested_params.corpora==='allDrives'),
    sends_expected_query: outputs.filter(o=>o.requested_params).every(o=>o.requested_params.q === "fullText contains 'deployment blocker' and trashed = false"),
    requests_pagination_evidence: outputs.filter(o=>o.requested_params).every(o=>o.requested_params.fields.includes('nextPageToken')),
    omits_incompleteSearch: outputs.filter(o=>o.requested_params).every(o=>!o.requested_params.fields.includes('incompleteSearch')),
    complete_incomplete_equal_under_fields:byId.E1_complete_zero.model_facing_sha256===byId.E2_incomplete_zero.model_facing_sha256,
    complete_incomplete_equal_even_if_extra_field_returned:byId.E3_complete_zero_overshare.model_facing_sha256===byId.E4_incomplete_zero_overshare.model_facing_sha256,
    reports_nextPageToken:byId.E5_more_pages.model_facing_result.content[0].text.includes('token-next'),
    reports_positive_file:byId.E6_hit_count.model_facing_result.content[0].text.includes('safety-review.txt'),
    incomplete_with_hit_indistinguishable:byId.E6_hit_count.model_facing_sha256===byId.E7_incomplete_with_hit.model_facing_sha256,
    transport_error_not_turned_into_zero:!!byId.E8_error.raised
  };
  const result = {
    scope:'isolated execution of verbatim upstream search branch, synthetic Google API stub',
    upstream:{repo:'piotr-agier/google-drive-mcp',commit:'9509fb8bba8ad15f7cdb79a54dbd850c13eb058b',file:'src/tools/drive.ts',upstream_git_blob_sha:'a32a46a470d1ee14a5fa9a81a3885eb8dbd29739',extracted_branch_sha256:branchHash},
    runtime:{node:process.version,typescript:ts.version},
    checks,passes:Object.values(checks).filter(Boolean).length,total_checks:Object.keys(checks).length,
    cases:outputs
  };
  fs.mkdirSync(path.join(basedir,'results'),{recursive:true});
  fs.writeFileSync(path.join(basedir,'results','results.json'),JSON.stringify(result,null,2)+'\n');
  fs.writeFileSync(path.join(basedir,'results','checks.json'),JSON.stringify({checks,result_summary:{passes:result.passes,total_checks:result.total_checks}},null,2)+'\n');
  for(const [k,v] of Object.entries(checks)) assert.equal(v,true,`FAIL ${k}`);
  console.log(JSON.stringify({passes:result.passes,total_checks:result.total_checks,checks,outputs:outputs.map(x=>({id:x.id,output:x.model_facing_result?.content?.[0]?.text||null,raised:x.raised}))},null,2));
})();

function loadTypeScript() {
  try { return require('typescript'); } catch (_) {
    const {execFileSync}=require('node:child_process');
    const path=require('node:path');
    const {createRequire}=require('node:module');
    try {
      const npmRoot=execFileSync('npm',['root','-g'],{encoding:'utf8'}).trim();
      return require(path.join(npmRoot,'typescript'));
    } catch (e) {
      throw new Error('TypeScript is required: npm install -g typescript');
    }
  }
}
