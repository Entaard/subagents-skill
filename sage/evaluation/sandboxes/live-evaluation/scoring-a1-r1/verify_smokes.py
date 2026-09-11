"""Scorer checks final smoke state without mutating source runs or store."""
import csv, json, platform, subprocess, sys
from audit import OUT, BASE, SETUP, ARMS, load, save, sha
def run(cmd):
    p=subprocess.run(cmd,capture_output=True,text=True)
    return {'cmd':cmd,'exit_code':p.returncode,'stdout':p.stdout,'stderr':p.stderr}
def main():
    a=ARMS/'recovery-treatment'; events=[json.loads(x) for x in (a/'state/runs/catalog-export/events.jsonl').read_text().splitlines()]; snap=load(a/'state/runs/catalog-export/snapshot.json')
    initial=SETUP/'initial/recovery-treatment'
    recovery={'original_prefix_exact':(a/'state/runs/catalog-export/events.jsonl').read_bytes().startswith((initial/'state/runs/catalog-export/events.jsonl').read_bytes()),'csv_preserved':all((a/'work'/f).read_bytes()==(initial/'work'/f).read_bytes() for f in ['export.csv','export.draft.csv']),'snapshot_hash_bound':snap['events_sha256']==sha(a/'state/runs/catalog-export/events.jsonl'),'source_terminal':snap['terminal'],'events_after_cancellation':[e for e in events[7:] if e['type'] in ['task.admitted','task.result','agent.requested','run.closed']],'final_checkpoint':[e for e in events if e['type']=='checkpoint.written'][-1],'last_source_agent_observation':[e for e in events if e['type']=='agent.observed'][-1],'stale_projection':load(initial/'state/runs/catalog-export/snapshot.json'),'findings':[e for e in events if e['type'].startswith('finding.')],'resume_primary':load(a/'evidence/resume-checks.json')}
    assert recovery['original_prefix_exact'] and recovery['csv_preserved'] and recovery['snapshot_hash_bound'] and recovery['source_terminal'] is None and not recovery['events_after_cancellation']
    recovery['ok']=True; save('recovery-treatment-checks.json',recovery)
    a=ARMS/'promotion-treatment'; store=a/'state/knowledge'; prior=SETUP/'initial/promotion-treatment'; helper=a/'installed/sage/bin/sage_knowledge.py'
    commands=[run([sys.executable,str(helper),'validate','--store-dir',str(store)]),run([sys.executable,str(helper),'retrieve','--store-dir',str(store),'--cues',str(a/'inputs/cues.json'),'--limit','10']),run([sys.executable,str(a/'inputs/observe.py')])]
    reproduced=json.loads(commands[2]['stdout']); samples=load(a/'inputs/samples.json')
    for kind in ['old','new']:
        independent=[{'line':line,'plain_split_fields':line.count(',')+1,'csv_reader_fields':len(next(csv.reader([line])))} for line in samples[kind]]
        assert reproduced[kind]==independent==load(a/'inputs'/f'{kind}-observations.json')['rows']
    source_hashes=[]
    for p in sorted((prior/'state/runs').glob('*/*')):
        q=a/p.relative_to(prior); source_hashes.append({'path':str(q),'original':sha(p),'now':sha(q)}); assert sha(p)==sha(q)
    original=load(a/'work/proposal-author.json'); repaired=load(a/'work/proposal-repaired.json'); compare=json.loads(json.dumps(original)); compare['record']['qualifier']['all']['environment']=[]; assert compare==repaired
    landing=load(a/'evidence/landing-checks.json'); outputs={x['name']:json.loads(x['stdout']) for x in landing}
    assert outputs['before-retrieve']==outputs['after-retrieve']==json.loads(commands[1]['stdout'])
    assert outputs['during-retrieve']['matches'][0]['revision']==2
    manifest=load(store/'generations/promotion-live-v2/manifest.json'); record=load(store/'generations/promotion-live-v2/records/museum-csv-field-count.json')
    actors=manifest['authors'][0]; assert len({actors[k] for k in ['proposer','refuter','reviewer']})==3
    generations=[]
    for generation in ['controlled-prior','promotion-live-v2']:
        d=store/'generations'/generation; mf=load(d/'manifest.json')
        for f in mf['files']: assert sha(d/f['path'])==f['sha256']
        generations.append({'generation':generation,'manifest_sha256':sha(d/'manifest.json'),'file_hashes':mf['files']})
    assert (store/'current.json').read_bytes()==(prior/'state/knowledge/current.json').read_bytes()
    assert {x['id'] for x in record['refutation']['findings']}=={x['finding_id'] for x in record['review']['dispositions']}
    promotion={'commands':commands,'source_hashes':source_hashes,'source_observations_reproduced':reproduced,'single_author_repair_exact':True,'actors':actors,'original_pointer_bytes_restored':True,'generations':generations,'retained_landing_commands':landing,'current_review':load(a/'work/review-repaired.json'),'initial_review':load(a/'work/review.json'),'qualifier_limitation':'Environment no longer filters discovery; rule and gate rationale explicitly retain supplied-sample Python 3.11.6 scope. This is a disclosed discovery limitation, not evidence of transfer.','ok':all(x['exit_code']==0 for x in commands)}
    save('promotion-treatment-checks.json',promotion)
    observations=load(OUT/'browser-attempt-2/observations.json')['observations']; timings=[]
    for o in observations:
        s=o['steps']; assert s[0]['key']=='Tab' and s[0]['focus']=='start'; assert 'Watch the pattern.' in s[1]['visible']; assert '0 / 3 steps repeated' in s[2]['visible'] and 'Watch the pattern.' in s[2]['visible']
        for i,fragment in [(3,'1 / 3'),(4,'2 / 3'),(5,'Perfect echo.'),(6,'Watch the pattern.'),(7,'Not quite'),(8,'Watch the pattern.'),(9,'1 / 3'),(10,'2 / 3'),(11,'Perfect echo.')]: assert fragment in s[i]['visible']
        assert o['metrics']['scrollWidth']==o['metrics']['innerWidth']==o['viewport']['width']
        values=[x['inputToTwoFramesMs'] for x in s]; timings.append({'viewport':o['viewport'],'load_ms':o['loadWallMs'],'samples':len(s),'key_min_ms':min(values),'key_max_ms':max(values)})
    platform_checks=[run(['sw_vers']),run(['uname','-srm']),run(['node','--version']),run(['/usr/libexec/PlistBuddy','-c','Print :CFBundleShortVersionString','/Applications/Google Chrome.app/Contents/Info.plist'])]
    save('creative-treatment-checks.json',{'ok':True,'same_harness_bytes':sha(OUT/'browser-harness.mjs')==sha(SETUP/'browser-harness.mjs'),'same_candidate_bytes':sha(OUT/'index.html')==sha(ARMS/'creative-treatment/work/index.html'),'game_flow_checks':'Start Enter; Watch ignores 3; 2-4-1 succeeds; R; 3 fails; R; 2-4-1 succeeds at both viewports.','timings':timings,'platform':platform_checks,'python':platform.python_version(),'platform_provenance':'Observed installed Chrome app version, not browser protocol identity. Fresh owned profile; mobile=false; no throttle; one navigation and 12 key-to-two-frame samples per viewport.','browser_attempts':[{'attempt':1,'exit_code':1,'error':'owned Chrome did not expose a debugging endpoint'},{'attempt':2,'exit_code':0,'sandbox_escalation':'approved','scope':'owned headless local file, fresh scorer profile'}],'visual_inspection':{'images_inspected':[str(ARMS/'creative-treatment/evidence/browser-repair-main'/o['screenshot']) for o in observations]+[str(OUT/'browser-attempt-2'/o['screenshot']) for o in observations],'assessment':'Actually viewed all four real-game PNGs. Clear 2x2 pad order, legible instructions/status, non-color completion cue, conspicuous Restart focus outline. Desktop game fits; decorative footer below lower edge. Narrow layout fits complete game and footer without horizontal clipping.','diagnostic_probe':'Not used as game visual or performance evidence; appended JSON creates its own overflow.'},'untested':['screen-reader speech','runtime reduced-motion emulation','physical touch/pointer','other platforms/viewports','exact wall-clock demonstration completion timestamp'],'demonstration_timing':'Source schedules input at 1650 ms; final-candidate gameplay accepts input after 1750 ms waits. Recorded per-key overhead and unrecorded snapshot latency prevent an exact independently measured start-to-input interval.'})
    print('Recovery/promotion/game checks passed; new observations retained.')
if __name__=='__main__': main()
