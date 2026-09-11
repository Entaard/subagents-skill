"""Reproduce observed report and pre-creation-dispatch limitations on copies."""
import copy, json, shutil, subprocess, sys
from audit import OUT, ARMS, load, save, sha
def cmd(args):
    p=subprocess.run(args,capture_output=True,text=True); return {'command':args,'exit_code':p.returncode,'stdout':p.stdout,'stderr':p.stderr}
def main():
    results=[]
    for row in load(OUT/'state-audit.json'):
        if row['run'].endswith(('csv-new','csv-old','echo-steps')): continue
        source=__import__('pathlib').Path(row['run']); dest=OUT/'report-copies'/row['arm']; dest.parent.mkdir(exist_ok=True); shutil.copytree(source,dest,dirs_exist_ok=True)
        r=cmd([sys.executable,str(ARMS/row['arm']/'installed/sage/bin/sage_state.py'),'report','--run-dir',str(dest),'--write'])
        report=(dest/'report.md').read_text(); snapshot=load(dest/'snapshot.json')
        results.append({'arm':row['arm'],'command':r,'unknown_heading_says_none':'## Unknowns\n\n- None' in report,'untested_heading_says_none':'## Untested evidence\n\n- None' in report,'agents':snapshot['agents'],'report_path':str(dest/'report.md'),'matches_delivered_report':(source/'report.md').read_bytes()==(dest/'report.md').read_bytes()})
    a=ARMS/'creative-treatment'; dest=OUT/'failed-dispatch-copy'; shutil.copytree(a/'state/runs/echo-steps',dest,dirs_exist_ok=True)
    events=[json.loads(x) for x in (dest/'events.jsonl').read_text().splitlines()]
    task=next(t for e in events if e['type']=='plan.revised' for t in e['payload']['tasks'] if t['id']=='review')
    prior=sha(dest/'events.jsonl'); last=events[-1]
    event={'v':1,'event_id':'scorer-dispatch-failed','run_id':last['run_id'],'seq':last['seq']+1,'at':'2026-09-08T00:00:00Z','actor':'root','type':'task.result','payload':{'task_id':'review','task_revision':task['revision'],'outcome':'failed','effect_status':'none','evidence_ids':[]}}
    payload=OUT/'dispatch-failure-result.json'; payload.write_text(json.dumps(event)+'\n')
    rejection=cmd([sys.executable,str(a/'installed/sage/bin/sage_state.py'),'append','--run-dir',str(dest),'--event',str(payload)])
    assert rejection['exit_code']==2 and 'delegated result needs its recorded agent request' in rejection['stderr'] and sha(dest/'events.jsonl')==prior
    save('reporting-checks.json',{'reports':results,'precreation_failure':{'command':rejection,'exact_original_copy_unchanged':True,'task':task,'original_plan_limits':[e['payload']['revision_limit'] for e in events if e['type']=='plan.revised'],'scope':'Observed creative admitted read-review has no native handle after failed spawn. No synthetic agent request was created; a truthful failed/no-effect result is rejected.'},'historical_locator':{'event':'creative original e-6','expected':'8b5abbf89ee581a6621f65c269adb4f9971075a059b12cd3bc58b250740a8f21','preserved_copy_sha256':sha(a/'evidence/original-index.html'),'assessment':'Working-path locator now points to repaired candidate. Old bytes remain preserved and explicitly linked by final report; historical locator drift is a nonblocking evidence navigation limitation, not lost evidence or immutable-input violation.'},'scorer_method_correction':'Initial record-inspection treated arm-relative locators as unresolved; corrected resolution using explicit arm root. All such hashes match. No false missing-file finding is issued.'})
    print(json.dumps({'reports':[{k:r[k] for k in ['arm','unknown_heading_says_none','untested_heading_says_none','matches_delivered_report']} for r in results],'dispatch_result':rejection},indent=2))
if __name__=='__main__': main()
