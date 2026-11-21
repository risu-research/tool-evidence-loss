'use strict';
// Runs the genuine `registerFilesList` implementation text in an isolated VM.
// All external dependencies (Zod, request, MCP registration, result serializer) are stubs.
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),assert=require('node:assert/strict'),crypto=require('node:crypto');
const ts=loadTypeScript();
const src=fs.readFileSync(path.join(__dirname,'upstream_control_files_list.ts'),'utf8');
const compiled=ts.transpileModule(src,{compilerOptions:{target:ts.ScriptTarget.ES2022,module:ts.ModuleKind.CommonJS}}).outputText;
const simpleSchema=()=>new Proxy({}, {get:(_target,field)=>field==='parse'?(v)=>v:()=>simpleSchema()});
const z={string:simpleSchema,number:simpleSchema,boolean:simpleSchema,enum:simpleSchema,object:simpleSchema,array:simpleSchema};
const results=[];
async function main() {
for(const fixture of [
 {id:'C1_complete_zero',raw:{files:[],incompleteSearch:false}},
 {id:'C2_incomplete_zero',raw:{files:[],incompleteSearch:true}},
 {id:'C3_pagination',raw:{files:[],incompleteSearch:false,nextPageToken:'another-page'}},
 {id:'C4_positive_hit',raw:{files:[{id:'1',name:'safety-review.txt',mimeType:'text/plain'}],incompleteSearch:false}}
]) {
  let callback,query=null;
  const fakeRequire = m => {
    if(m==='zod') return {z};
    if(m==='../utils/schema.js') return {strictSchemaWithAliases:()=>simpleSchema()};
    if(m==='../utils/response.js') return {jsonResult:(parsed)=>({structuredContent:parsed,content:[{type:'text',text:JSON.stringify(parsed)}]})};
    if(m==='../utils/drive-api.js') return {makeDriveApiCall:async(_method,url)=>{
      query=Object.fromEntries(new URL(url,'http://local.test').searchParams);
      const fields=query.fields||'';
      const picked={};
      for(const k of ['files','nextPageToken','incompleteSearch']) if(fields.split(',').some(part=>part.trim()===k||part.trim().startsWith(k+'('))&&k in fixture.raw) picked[k]=fixture.raw[k];
      return picked;
    }};
    throw new Error(`Unknown dependency ${m}`);
  };
  const module={exports:{}};
  const sandbox=vm.createContext({exports:module.exports,module,require:fakeRequire,URLSearchParams,URL});
  new vm.Script(compiled).runInContext(sandbox,{timeout:3000});
  module.exports.registerFilesList({registerTool:(_name,_desc,fn)=>{callback=fn}}, {token:'SYNTHETIC-ONLY'});
  assert.ok(callback);
  const response=await awaitCb(callback,{q:"name contains 'blocker'",pageSize:100,spaces:'drive',includeItemsFromAllDrives:true,supportsAllDrives:true});
  results.push({id:fixture.id,raw:fixture.raw,request_query:query,structuredContent:response.structuredContent,output:response.content[0].text});
}
function awaitCb(cb,args){return cb(args)}
  // The async callback has finished before this point.
  const a=Object.fromEntries(results.map(x=>[x.id,x]));
  const checks={
    default_fields_include_incompleteSearch:results.every(r=>r.request_query.fields.includes('incompleteSearch')),
    full_and_incomplete_visible_different:a.C1_complete_zero.output!==a.C2_incomplete_zero.output,
    incomplete_flag_retained:a.C2_incomplete_zero.structuredContent.incompleteSearch===true,
    pagination_token_retained:a.C3_pagination.structuredContent.nextPageToken==='another-page',
    positive_hit_retained:a.C4_positive_hit.structuredContent.files.length===1,
  };
  Object.entries(checks).forEach(([name,v])=>assert.equal(v,true,name));
  const summary={scope:'original third-party registration callback via VM with mocked dependencies; JSON serializer stub',upstream:{repo:'domdomegg/google-drive-mcp',commit:'395971084f5d8504e5b2934dab4c2cc6e2f210b5',path:'src/tools/files-list.ts',git_blob_sha:'8e5bba41101d24b49e299d9ef3c8bde46a047719',copied_source_sha256:crypto.createHash('sha256').update(src).digest('hex')},runtime:{node:process.version,typescript:ts.version},checks,passes:Object.values(checks).filter(Boolean).length,total_checks:Object.keys(checks).length,cases:results};
  fs.writeFileSync(path.join(__dirname,'results','control.json'),JSON.stringify(summary,null,2)+'\n');
  console.log(JSON.stringify({checks,cases:results.map(x=>({id:x.id,output:x.output,fields:x.request_query.fields}))},null,2));

}
main().catch(e=>{console.error(e);process.exitCode=1});

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
