"""Independent read-only frozen-input and run audit; writes only beside this script."""
import hashlib, json, os, subprocess, sys
from pathlib import Path

OUT = Path(__file__).resolve().parent
BASE = OUT.parent
SETUP = BASE / 'setup'
ARMS = SETUP / 'arms'
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'
os.environ['TMPDIR'] = str(OUT / 'tmp')
(OUT / 'tmp').mkdir(exist_ok=True)
def load(p): return json.loads(Path(p).read_text())
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(name, data): (OUT / name).write_text(json.dumps(data, indent=2) + '\n')
def canonical(x): return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def walk(x):
    if isinstance(x,dict):
        if 'path' in x and 'sha256' in x: yield x
        for v in x.values(): yield from walk(v)
    elif isinstance(x,list):
        for v in x: yield from walk(v)

def main():
    manifests=[]; artifacts={}
    for name in ['setup-freeze.json','frozen-pairs.json','frozen-smokes.json']:
        x=load(SETUP/name)
        manifests.append({'name':name,'expected':x['manifest_sha256'],'actual':canonical({k:v for k,v in x.items() if k!='manifest_sha256'})})
        for a in walk(x): artifacts[a['path']]=a['sha256']
    for name in ['environment.json']:
        for a in walk(load(SETUP/name)): artifacts[a['path']]=a['sha256']
    bound=[{'path':p,'expected':h,'actual':sha(p) if Path(p).is_file() else None} for p,h in artifacts.items()]
    initial=[]
    for arm in load(SETUP/'initial-arm-hashes.json'):
        for item in arm['initial_files']:
            p=Path(item['path']); rel=p.relative_to(arm['root']); actual=sha(p) if p.is_file() else None
            allowed=None
            if arm['arm']=='recovery-treatment' and str(rel).startswith('state/runs/catalog-export/'):
                prior=SETUP/'initial'/arm['arm']/rel
                if p.name=='events.jsonl': allowed='append-only original prefix preserved' if p.read_bytes().startswith(prior.read_bytes()) else None
                elif p.name in ['snapshot.json','report.md']: allowed='derived recovery projection'
            initial.append({'arm':arm['arm'],'path':str(p),'relative':str(rel),'expected':item['sha256'],'actual':actual,'allowed_change':allowed,'ok':actual==item['sha256'] or allowed is not None})
    identity=[]
    for arm in load(SETUP/'install-identity.json')['installations']:
        for f in arm['files']:
            p=ARMS/arm['arm']/'installed'/f['path']
            identity.append({'arm':arm['arm'],'path':str(p),'expected':f['sha256'],'actual':sha(p)})
    results=[]
    for arm in ARMS.iterdir():
        state=arm/'state'
        for event in sorted(state.glob('**/events.jsonl')):
            helper=arm/'installed/sage/bin/sage_state.py'
            cmd=[sys.executable,str(helper),'validate','--run-dir',str(event.parent)]
            r=subprocess.run(cmd,capture_output=True,text=True)
            rt=subprocess.run(cmd+['--terminal'],capture_output=True,text=True)
            events=[json.loads(line) for line in event.read_text().splitlines() if line.strip()]
            results.append({'arm':arm.name,'run':str(event.parent),'validate':{'exit_code':r.returncode,'stdout':r.stdout,'stderr':r.stderr},'terminal':{'exit_code':rt.returncode,'stdout':rt.stdout,'stderr':rt.stderr},'events':events})
    save('integrity.json',{'manifest_selfhashes':manifests,'frozen_artifacts':bound,'initial_files':initial,'installed_identity':identity,'ok':all(x['expected']==x['actual'] for x in manifests+bound+identity) and all(x['ok'] for x in initial)})
    save('state-audit.json',results)
    save('process-provenance.json',{'scorer':'/root/live_scorer','requested_model':'gpt-6-astra','requested_effort':'high','effective_model':None,'effective_effort':None,'tokens':None,'money':None,'interruption':{'source':'root followup task','observation':'Prior native scorer turn errored with usage-limit message; root found no produced files or scores; resumed same task and lease.'},'writes':'scoring-a1-r1 plus new docs/LIVE-RESULTS.md only','native_exit_code':None})
    print(json.dumps({'integrity_ok':load(OUT/'integrity.json')['ok'],'artifact_count':len(bound),'initial_count':len(initial),'installed_count':len(identity),'runs':[{k:r[k] for k in ['arm','run','validate','terminal']} for r in results]},indent=2))
if __name__=='__main__': main()
