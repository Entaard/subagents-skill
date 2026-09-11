"""Fresh round-2 review evidence; all output stays under this directory."""
import copy
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest

HERE=Path(__file__).resolve().parent
REPO=HERE.parents[3]
sys.path.insert(0,str(REPO/'sage/evaluation/tests'))
from support import opened,event,task,write_log,dump
CLI=REPO/'sage/scripts/sage_state.py'
results={}
def run(name,*args):
    cp=subprocess.run([sys.executable,str(CLI),*args],capture_output=True,text=True)
    row={'command':[str(CLI),*args],'exit_code':cp.returncode,'stdout':cp.stdout,'stderr':cp.stderr}
    try: row['output']=json.loads(cp.stdout or cp.stderr)
    except ValueError: pass
    results[name]=row
    return row
def add(rows,kind,payload): rows.append(event(len(rows)+1,kind,payload))
def plan(tasks): return dict(revision=1,reason='initial',attempt_limit=3,revision_limit=3,no_progress='same failure',trigger_event_ids=['e-1'],tasks=tasks)
def observe(rows,lifecycle,effect): add(rows,'agent.observed',dict(handle='/root/writer',lifecycle=lifecycle,effect_status=effect,effective_model=None,effective_effort=None))
def base():
    rows=[opened(),event(2,'plan.revised',plan([task('w-1','write',owner='/root/writer'),task('w-2','write')]))]
    add(rows,'task.admitted',dict(task_id='w-1',task_revision=1,plan_revision=1))
    add(rows,'agent.requested',dict(task_id='w-1',handle='/root/writer',requested_model='gpt-5.6-sol',requested_effort='high',fork_turns='none'))
    add(rows,'evidence.recorded',dict(evidence_id='ev-1',criterion_ids=['c-1'],kind='observation',locator='artifact/write',sha256=None))
    return rows
def finish(rows): add(rows,'task.result',dict(task_id='w-1',task_revision=1,outcome='passed',effect_status='reconciled',evidence_ids=['ev-1']))

# Original suites, without modifying their methods or assertions.
for name,path in [('contracts','sage/evaluation/tests/test_product_state.py'),('regressions','sage/tests/test_state.py')]:
    spec=importlib.util.spec_from_file_location(name,REPO/path); module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    stream=io.StringIO(); result=unittest.TextTestRunner(stream=stream,verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(module))
    (HERE/(name+'.txt')).write_text(stream.getvalue())
    results[name]=dict(tests=result.testsRun,failures=len(result.failures),errors=len(result.errors),skipped=len(result.skipped))

# Replay the retained critic's exact code with a fresh output location.
replay=REPO/'sage/evaluation/sandboxes/sage-a1-r2-replay'; replay.mkdir(exist_ok=True)
prior=REPO/'sage/evaluation/sandboxes/sage-a1-r1-critic/probes.py'
namespace={'__file__':str(replay/'probes.py'),'__name__':'critic_replay'}
saved=sys.stdout; sys.stdout=io.StringIO()
try: exec(compile(prior.read_text(),str(prior),'exec'),namespace)
finally: sys.stdout=saved
results['prior_replay']=str(replay/'results.json')

# A terminal lifecycle observed before the task result is not an irrevocable release.
for lifecycle in ('active','idle','interrupted','missing'):
    rows=base(); observe(rows,'completed','reconciled'); observe(rows,lifecycle,'unknown'); finish(rows)
    directory=HERE/('terminal-then-'+lifecycle); write_log(directory,rows)
    run(lifecycle+'-snapshot','snapshot','--run-dir',str(directory),'--write')
    agents=dump(directory/'agents.json',[dict(handle='/root/writer',lifecycle=lifecycle)])
    run(lifecycle+'-resume','resume','--run-dir',str(directory),'--agents',str(agents))
    admission=event(len(rows)+1,'task.admitted',dict(task_id='w-2',task_revision=1,plan_revision=1))
    event_path=dump(directory/'admission.json',admission)
    run(lifecycle+'-append-writer','append','--run-dir',str(directory),'--event',str(event_path))

# Positive control: a fresh terminal reconciliation resolves the uncertainty.
rows=base(); observe(rows,'completed','reconciled'); observe(rows,'active','unknown'); finish(rows); observe(rows,'completed','reconciled')
directory=HERE/'fresh-terminal-control'; write_log(directory,rows)
add(rows,'task.admitted',dict(task_id='w-2',task_revision=1,plan_revision=1)); write_log(directory,rows)
run('fresh-terminal-control','validate','--run-dir',str(directory))

# Correct same-handle reuse does not borrow the previous assignment's terminal fact.
rows=base(); observe(rows,'completed','reconciled'); finish(rows)
revision=copy.deepcopy(rows[1]['payload']); revision.update(revision=2,reason='evidence_change',trigger_event_ids=['e-5'])
revision['tasks'][0]['revision']=2; revision['tasks'][0]['inputs']=['changed bounded scope']
add(rows,'plan.revised',revision); add(rows,'task.admitted',dict(task_id='w-1',task_revision=2,plan_revision=2))
add(rows,'agent.requested',dict(task_id='w-1',handle='/root/writer',requested_model='gpt-5.6-sol',requested_effort='high',fork_turns='none'))
add(rows,'task.result',dict(task_id='w-1',task_revision=2,outcome='passed',effect_status='reconciled',evidence_ids=['ev-1']))
directory=HERE/'same-handle-reused'; write_log(directory,rows)
agents=dump(directory/'agents.json',[dict(handle='/root/writer',lifecycle='active')])
run('reused-handle-resume','resume','--run-dir',str(directory),'--agents',str(agents))
add(rows,'task.admitted',dict(task_id='w-2',task_revision=1,plan_revision=2)); write_log(directory/'invalid-admission',rows)
run('reused-handle-blocks-writer','validate','--run-dir',str(directory/'invalid-admission'))

# Invalid UTF-8 is a data error in every reader, including derived snapshot repair.
directory=HERE/'utf8'; write_log(directory,[opened()]); run('utf8-baseline','snapshot','--run-dir',str(directory),'--write')
bad=directory/'invalid.json'; bad.write_bytes(b'\xff')
run('utf8-append','append','--run-dir',str(directory),'--event',str(bad))
run('utf8-resume-input','resume','--run-dir',str(directory),'--agents',str(bad))
run('utf8-init','init','--run-dir',str(directory/'new-run'),'--run-id','new-run','--objective','bounded','--criteria',str(bad))
(directory/'snapshot.json').write_bytes(b'\xff'); good=dump(directory/'agents.json',[])
run('utf8-snapshot-repair','resume','--run-dir',str(directory),'--agents',str(good))

dump(HERE/'results.json',results)
print(json.dumps({key:{field:value for field,value in row.items() if field in ('exit_code','output','tests','failures','errors')} if isinstance(row,dict) else row for key,row in results.items()},indent=2))
