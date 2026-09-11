"""Round-3 independent replay, explicit assertions and neighboring CLI controls."""
import copy
import io
import json
import os
from pathlib import Path
import subprocess
import sys

HERE=Path(__file__).resolve().parent
REPO=HERE.parents[3]
source=REPO/'sage/evaluation/sandboxes/sage-a1-r2-critic/probes.py'
# Redirect both destinations, including the historical runner's hard-coded nested replay.
code=source.read_text().replace("sage/evaluation/sandboxes/sage-a1-r2-replay", "sage/evaluation/sandboxes/sage-a1-r3-replay")
namespace={'__file__':str(HERE/'probes.py'),'__name__':'critic_replay'}
stream=io.StringIO(); saved=sys.stdout; sys.stdout=stream
try: exec(compile(code,str(source),'exec'),namespace)
finally: sys.stdout=saved
(HERE/'replay-output.txt').write_text(stream.getvalue())
observed=json.loads((HERE/'results.json').read_text())
assertions=[]
def expect(name,actual,expected):
    assertions.append({'name':name,'actual':actual,'expected':expected,'passed':actual==expected})
for lifecycle in ('active','idle','interrupted','missing'):
    expect(lifecycle+' resume',observed[lifecycle+'-resume']['output']['admission_allowed'],False)
    expect(lifecycle+' writer rejection',observed[lifecycle+'-append-writer']['exit_code'],2)
    expect(lifecycle+' writer rejection code',observed[lifecycle+'-append-writer']['output']['code'],'writer_busy')
expect('fresh terminal control',observed['fresh-terminal-control']['exit_code'],0)
expect('fresh same-handle assignment',observed['reused-handle-resume']['output']['admission_allowed'],False)
expect('same-handle writer rejection',observed['reused-handle-blocks-writer']['output']['code'],'writer_busy')
for name in ('utf8-append','utf8-resume-input','utf8-init'):
    expect(name+' exit',observed[name]['exit_code'],2)
    expect(name+' code',observed[name]['output']['code'],'invalid_json')
expect('UTF-8 projection recovery',observed['utf8-snapshot-repair']['exit_code'],0)
expect('frozen suite',observed['contracts'],{'tests':9,'failures':0,'errors':0,'skipped':0})
expect('regression suite',observed['regressions'],{'tests':16,'failures':0,'errors':0,'skipped':0})

sys.path.insert(0,str(REPO/'sage/evaluation/tests'))
from support import event,opened,task,write_log,dump
CLI=REPO/'sage/scripts/sage_state.py'
commands=[]
def call(name,*args):
    cp=subprocess.run([sys.executable,str(CLI),*args],capture_output=True,text=True)
    commands.append({'name':name,'args':args,'exit_code':cp.returncode,'stdout':cp.stdout,'stderr':cp.stderr})
    return cp
def add(rows,kind,payload): rows.append(event(len(rows)+1,kind,payload))
def observation(rows,lifecycle,effect): add(rows,'agent.observed',{'handle':'/root/worker','lifecycle':lifecycle,'effect_status':effect,'effective_model':None,'effective_effort':None})
def result(rows,outcome,effect,evidence=True): add(rows,'task.result',{'task_id':'t-1','task_revision':1,'outcome':outcome,'effect_status':effect,'evidence_ids':['ev-1'] if evidence else []})

# Valid unknown-to-known reconciliation across effect classes and both fact orders.
for effect in ('read','write','external','unknown'):
  for owner in ('root','/root/worker'):
    for outcome in ('passed','failed'):
      for first in ('observation','result'):
        name='matrix-'+effect+'-'+('root' if owner=='root' else 'agent')+'-'+outcome+'-'+first
        rows=[opened(),event(2,'plan.revised',{'revision':1,'reason':'initial','attempt_limit':1,'revision_limit':1,'no_progress':'one bounded attempt','trigger_event_ids':['e-1'],'tasks':[task('t-1',effect,owner=owner)]})]
        add(rows,'task.admitted',{'task_id':'t-1','task_revision':1,'plan_revision':1})
        if owner!='root': add(rows,'agent.requested',{'task_id':'t-1','handle':owner,'requested_model':'gpt-5.6-sol','requested_effort':'high','fork_turns':'none'})
        result(rows,'unknown','unknown',False)
        add(rows,'evidence.recorded',{'evidence_id':'ev-1','criterion_ids':['c-1'],'kind':'observation','locator':'artifact/reconciled','sha256':None})
        if owner!='root' and first=='observation': observation(rows,'completed','reconciled')
        result(rows,outcome,'none' if effect=='read' else 'reconciled')
        if owner!='root' and first=='result': observation(rows,'completed','reconciled')
        add(rows,'run.closed',{'status':'stopped','criterion_evidence':{},'scope_reconciled':False,'remaining_human_items':[]})
        directory=HERE/name; write_log(directory,rows)
        cp=call(name,'validate','--run-dir',str(directory),'--terminal')
        expect(name,cp.returncode,0)

# Full installed-reference tiny example command sequence.
example=HERE/'full-example';example.mkdir(exist_ok=True)
criteria=dump(example/'criteria.json',[{'id':'c-1','text':'The bounded read is observed and checked.'}])
wave=(REPO/'sage/skills/sage/references/state.md').read_text().split('```jsonl\n')[1].split('```')[0]
(example/'wave.jsonl').write_text(wave)
steps=[('init','--run-dir',str(example/'run'),'--run-id','tiny-1','--objective','bounded read','--criteria',str(criteria)),('append','--run-dir',str(example/'run'),'--events',str(example/'wave.jsonl')),('snapshot','--run-dir',str(example/'run'),'--write'),('validate','--run-dir',str(example/'run'),'--terminal'),('report','--run-dir',str(example/'run'),'--write')]
for step in steps: expect('example '+step[0],call('example '+step[0],*step).returncode,0)
dump(HERE/'assertions.json',{'assertions':assertions,'commands':commands,'passed':sum(x['passed'] for x in assertions),'failed':sum(not x['passed'] for x in assertions)})
print(json.dumps({'assertions':len(assertions),'passed':sum(x['passed'] for x in assertions),'failed':sum(not x['passed'] for x in assertions)}))
sys.exit(0 if all(x['passed'] for x in assertions) else 1)
