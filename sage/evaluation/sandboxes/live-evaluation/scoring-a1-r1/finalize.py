"""Final evidence and lease-scope audit, excluding all browser profile contents."""
import json, os, re, subprocess
from pathlib import Path
from audit import OUT, BASE, load, save, sha, canonical

def main():
    integrity=load(OUT/'integrity.json'); checks=[]
    for group in ['frozen_artifacts','initial_files','installed_identity']:
        for entry in integrity[group]:
            p=Path(entry['path']); checks.append({'path':str(p),'sha256':sha(p),'unchanged_since_scorer_audit':sha(p)==entry['actual']})
    scored=[]
    for result in [load(OUT/'paired-results.json'),load(OUT/'smoke-results.json')]:
        arms=[r[a] for r in result['pairs'] for a in ['treatment','baseline']] if 'pairs' in result else [r['result'] for r in result['cases']]
        for arm in arms:
            for e in arm['execution']['evidence']: scored.append({'path':e['path'],'matches':sha(e['path'])==e['sha256']})
    docs=BASE.parents[2]/'docs/LIVE-RESULTS.md'
    links=re.findall(r'\]\(([^)]+)\)',docs.read_text())
    missing=[s for s in links if not s.startswith(('http:','https:','#')) and not (docs.parent/s.split('#')[0]).exists()]
    process=load(OUT/'process-check.json')
    p=process['result']; owned=p['output'].splitlines()
    assert all(c['unchanged_since_scorer_audit'] for c in checks)
    assert all(e['matches'] for e in scored)
    assert not missing
    assert p['exit_code']==0 and not owned
    save('final-audit.json',{'ok':True,'frozen_and_initial_entries_checked':len(checks),'entries':checks,'result_evidence_bindings_checked':len(scored),'all_result_evidence_hashes_match':True,'report_links_checked':len(links),'missing_report_links':missing,'owned_browser_process_check':process,'writes':'Scorer tree plus new sage/docs/LIVE-RESULTS.md only','pending_process_or_effect':False,'scorer_method_notes':['A first record-inspection pass did not resolve arm-relative locators; corrected using explicit arm root, all those hashes match. No missing-file issue was issued.','Added direct summary-bound/envelope assertions to the data verifier; both data checks rerun, frozen candidates unchanged.','Frozen pair validator rejection observed on both compilation invocations; same null native exit and same actual exit-2 message retained.'],'release':'RELEASE of entire scorer writer lease; no pending process/effect.'})
    files=[]
    for current, dirs, names in os.walk(OUT):
        dirs[:]=[d for d in dirs if d!='owned-profile' and d!='__pycache__']
        for name in names:
            path=Path(current)/name
            if path.name=='scoring-manifest.json': continue
            files.append({'path':str(path),'sha256':sha(path)})
    files.append({'path':str(docs),'sha256':sha(docs)})
    manifest={'schema_version':'sage-live-independent-scoring-bundle-v1','files':sorted(files,key=lambda x:x['path']),'exclusions':['Fresh scorer-owned browser profile contents are deliberately neither read nor hashed.'],'scorer':'/root/live_scorer','native_exit_code':None,'release':'Entire writer lease released; no pending process/effect.'}; manifest['manifest_sha256']=canonical(manifest); save('scoring-manifest.json',manifest)
    print(json.dumps({'ok':True,'frozen_initial_entries':len(checks),'result_evidence_bindings':len(scored),'report_links':len(links),'scoring_bundle_files':len(files),'scoring_manifest_sha256':manifest['manifest_sha256'],'owned_browser_processes':owned,'release':True},indent=2))
if __name__=='__main__': main()
