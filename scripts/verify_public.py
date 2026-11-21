#!/usr/bin/env python3
"""Frozen evidence, source provenance, and repository disclosure audit."""
from pathlib import Path
import hashlib, json, re, sys, subprocess, tempfile, shutil

ROOT=Path(__file__).resolve().parents[1]

def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def require(x,msg):
    if not x: raise RuntimeError(msg)
def check_lines(base,manifest,optional=()):
    lines=(base/manifest).read_text(encoding='utf8').splitlines()
    checked=[]
    for line in lines:
        expected,relative=line.strip().split(None,1)
        target=(base/relative.strip()).resolve()
        if relative.strip() in optional and not target.exists(): continue
        require(target.is_relative_to(base.resolve()) and target.is_file(),f'missing manifest target: {relative}')
        require(digest(target)==expected,f'hash mismatch: {relative}')
        checked.append(relative)
    return len(checked)

def frozen_audit():
    checks={}
    checks['public-file-manifest']=check_lines(ROOT,'EVIDENCE_SHA256SUMS.txt')
    for name,manifest in [('g7','pre-run-source.sha256'),('g8','expected-pre-run.sha256'),('g9','preexecution-manifest.sha256')]:
        checks[name+'-input']=check_lines(ROOT/'experiments'/name,manifest)
    for name,manifest in [('g7','final-files.sha256'),('g8','final-files.sha256'),('g9','postexecution-output-manifest.sha256')]:
        checks[name+'-original-output']=check_lines(ROOT/'experiments'/name,manifest,optional=('REPORT.md','PAPER_READY_RESULT.md') if name=='g9' else ())
    summaries=[json.loads((ROOT/'experiments'/name/f).read_text()) for name,f in [('g7','official-runtime-summary.json'),('g8','http-summary.json'),('g9','result_summary.json')]]
    for idx,s in enumerate(summaries):
        require(s.get('pass') is True,f'g{7+idx} original recorded result failed')
    for s in summaries[:2]:
        require(s['cases']==16 and s['sourceQualifiedActCount']==8 and s['sourceQualifiedBlockCount']==8,'G7/G8 case counts')
        require(s['projectionInvalidCommits']==8 and s['sourceInvalidCommits']==0,'G7/G8 invalid ledger counts')
        require(s['distinctModelVisibleToolOutputHashes']==['870939faf69d719bb49732ef03c46638aab9df8e77996899bf91fa272eae94ee'],'G7/G8 identical output hash')
    g9=summaries[2]
    require(g9['pairs']==8 and g9['identicalCompleteVisibleTranscriptPairs']==8,'G9 transcript pair count')
    require(g9['bindingPositiveControlsACT']==5 and g9['bindingMismatchControlsBLOCK']==5,'G9 request binding')
    e1=json.loads((ROOT/'evidence/e1/checks.json').read_text())
    require(e1['result_summary']=={'passes':10,'total_checks':10},'E1 recorded assertions')
    e2a=json.loads((ROOT/'evidence/e2/s2ai_full_runtime.json').read_text())
    e2b=json.loads((ROOT/'evidence/e2/s2ai_stdio_runtime.json').read_text())
    require(e2a['checks'].get('tools_call_equal') and e2b['checks'].get('tools_call_result_equal'),'E2 transport checks')
    require(e2a['observations'][1]['hash_a']==e2b['sha256'],'E2 cross-transport hash')
    e3=json.loads((ROOT/'evidence/e3/e3_downstream_report.json').read_text())
    require(e3['summary']=={'count':5,'writes':3,'unlicensed_writes':1},'E3 outcome counts')
    receipts=[json.loads(x) for x in (ROOT/'evidence/e3/e3_provider_writes.jsonl').read_text().splitlines()]
    require(len(receipts)==3 and len(e3['provider_writes'])==3,'E3 write receipts')
    for a,b in zip(receipts,e3['provider_writes']):require(a==b,'E3 independent write receipt')
    e4base=ROOT/'evidence/e4'
    e4=json.loads((e4base/'e4_verification.json').read_text())
    require(e4['pass'] is True and e4['scenario_count']==20,'E4 scenario count')
    require(e4['results']=={'before':{'projection':2,'coverage':0},
                              'after':{'projection':2,'coverage':1}},'E4 effect outcomes')
    require(e4['provider_receipts']=={'before':2,'after':3},'E4 provider write receipts')
    for rev,sha in [('before','bc563b724c2ea39368ca99b6cd45d36a64a7b1c5'),
                    ('after','9ff6d911131768470f91620ba40878a1f9372b61')]:
        record=json.loads((e4base/f'e4_{rev}.json').read_text())
        require(record['source']['commit']==sha and len(record['rows'])==10,
                'E4 source pin / scenarios '+rev)
        receipts=[json.loads(x) for x in (e4base/f'e4_{rev}_http_receipts.jsonl').read_text().splitlines()]
        require(receipts==record['receipts'],'E4 independent receipt equality '+rev)
        require(len(receipts)==e4['provider_receipts'][rev],'E4 receipt count '+rev)
        discovery=json.loads((e4base/f'e4_discovery_{rev}.json').read_text())
        require(discovery['pass'] and len(discovery['states'])==2,'E4 original discovery-client control '+rev)
        results=[x['tool_result'] for x in discovery['states']]
        require((results[0]==results[1])==(rev=='before'),
                'E4 completeness distinction '+rev)
    checks['E4-historical-repair']='20 cases; 5 recorded writes; original Google API Discovery controls'
    checks['recorded-cases']='G7 16; G8 16; G9 8 pairs; E1 10 checks; E2 2 transports; E3 5 scenarios'
    return checks

def git_hash(path):
    b=path.read_bytes();return hashlib.sha1(b'blob '+str(len(b)).encode()+b'\x00'+b).hexdigest()

def source_hashes():
    pins={
        'experiments/e1/upstream_control_files_list.ts':'8e5bba41101d24b49e299d9ef3c8bde46a047719',
        'experiments/e2/s2ai_mcp_full_runtime.test.ts':'e90eae67262b8cf9a988cb6a74e049deac8c8d24',
        'experiments/e2/s2ai_stdio_client.test.ts':'4a31eeb543d7508260816da2d23a6ec944c77588',
        'experiments/e2/s2ai_stdio_server.ts':'3c4881bc1aa33e0ee1b39bc91b2093e86dc60396',
        'experiments/e3/e3_downstream_effect.test.ts':'b297253a7021f887a87a4b01114584c22503d40c',
        'experiments/e3/e3_stdio_upstream_server.ts':'17a0b11731ec2b5ce2e6f54ad76b4fe64174c50c',
    }
    for path,sha in pins.items():require(git_hash(ROOT/path)==sha,f'external execution source mismatch {path}')
    return len(pins)

def disclosure_scan():
    forbidden_file=re.compile(r'(^|/)(\.env(?:\.|$)|\.git/|raw_history|manuscript|submission\.pdf|reviewer_response|private|handoff)(/|$)',re.I)
    patterns={
      'personal identifiers':r'(?i)moon.{0,2}1002|hotmail\.com|312[-.]363[-.]8596|1500(?:\s+)Massachusetts(?:\s+)Ave',
      'local private paths':r'(?i)C:\\Users\\moon|/home/[^/]+/|/mnt/(?:data|secure)/',
      'secret formats':r'(?i)ghp_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{30,}|sk-proj-[A-Za-z0-9_-]{20,}|-----BEGIN (RSA |OPENSSH )?PRIVATE KEY-----',
      'private study authority':r'(?i)safe.{0,2}tool.{0,2}compression|(?:reviewer\s*#\s*[123])',
    }
    # Include tracked files, including experiments and docs. The metadata and
    # deterministic test fixtures use explicit allower files and checked bytes.
    if (ROOT/'.git').exists():
        tracked=subprocess.check_output(['git','ls-files','-z'],cwd=ROOT).decode().split('\x00')
        candidates=[ROOT/x for x in tracked if x and (ROOT/x).is_file()]
    else:candidates=[p for p in ROOT.rglob('*') if p.is_file()]
    for p in candidates:
        rel=p.relative_to(ROOT).as_posix()
        if rel=='scripts/verify_public.py':continue
        require(not forbidden_file.search(rel),'unexpected file path '+rel)
        content=p.read_text(encoding='utf8')
        for label,regex in patterns.items():
            require(re.search(regex,content) is None,f'{label} in {rel}')
    return len(candidates)

def replay_g9():
    src=ROOT/'experiments/g9'
    with tempfile.TemporaryDirectory(prefix='s2ai-g9-') as tmp:
        dst=Path(tmp)/'g9';shutil.copytree(src,dst)
        output=subprocess.run(['node','run_one_round.mjs'],cwd=dst,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=120)
        require(output.returncode==0,'G9 replay failed: '+output.stderr[:1200])
        for name in ['result_summary.json','result_rows.json','result_pairs.json','result_challenges.json','result_projection_ledger.json','result_qualified_ledger.json']:
            require(digest(dst/name)==digest(src/name),'G9 rerun differs: '+name)
        require(json.loads(output.stdout)['pass'] is True,'G9 replay summary')
    return '6 frozen output hashes matched'

if __name__=='__main__':
    checks=frozen_audit()
    checks['source-git-blobs']=source_hashes() if '--preupload' not in sys.argv else 'verified on public CI'
    checks['disclosure-scanned-files']=disclosure_scan()
    if '--g9' in sys.argv:checks['G9 fresh replay']=replay_g9()
    print(json.dumps({'pass':True,'checks':checks},indent=2))
