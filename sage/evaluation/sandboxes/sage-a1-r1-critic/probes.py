"""Independent adversarial CLI probes. Writes only beside this script."""
import copy
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
sys.path.insert(0, str(REPO / 'sage/evaluation/tests'))
from support import event, opened, task, complete_read_run

results = {}
def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + '\n')
def log(name, rows):
    path = HERE / name
    path.mkdir(parents=True, exist_ok=True)
    (path / 'events.jsonl').write_text(''.join(json.dumps(row) + '\n' for row in rows))
    return path
def call(name, command, rows=None, agents=None):
    run = log(name, rows) if rows is not None else HERE / name
    args = [sys.executable, str(REPO / 'sage/scripts/sage_state.py'), command, '--run-dir', str(run)]
    if command in ('snapshot', 'report'): args += ['--write']
    if agents is not None:
        save(run / 'agents-input.json', agents)
        args += ['--agents', str(run / 'agents-input.json')]
    cp = subprocess.run(args, capture_output=True, text=True)
    record = dict(command=args, exit_code=cp.returncode, stdout=cp.stdout, stderr=cp.stderr)
    try: record['output'] = json.loads(cp.stdout or cp.stderr)
    except ValueError: pass
    results[name + ':' + command] = record
    return record
def plan(tasks, revision=1, reason='initial', triggers=None):
    return dict(revision=revision, reason=reason, attempt_limit=3, revision_limit=3,
                no_progress='same failure', trigger_event_ids=triggers or ['e-1'], tasks=tasks)
def push(rows, kind, payload):
    rows.append(event(len(rows)+1, kind, payload))
def evidence(rows):
    push(rows, 'evidence.recorded', dict(evidence_id='ev-1', criterion_ids=['c-1'], kind='observation', locator='artifact/observed', sha256=None))
def admitted(rows, tid='t-1', rev=1, pr=1):
    push(rows, 'task.admitted', dict(task_id=tid, task_revision=rev, plan_revision=pr))
def request(rows, handle='agent-a'):
    push(rows, 'agent.requested', dict(task_id='t-1', handle=handle, requested_model='gpt-5.6-sol', requested_effort='high', fork_turns='none'))
def observed(rows, handle='agent-a', lifecycle='completed', effect='reconciled'):
    push(rows, 'agent.observed', dict(handle=handle, lifecycle=lifecycle, effect_status=effect, effective_model=None, effective_effort=None))
def result(rows, rev=1, outcome='passed', effect='none', refs=None):
    push(rows, 'task.result', dict(task_id='t-1', task_revision=rev, outcome=outcome, effect_status=effect, evidence_ids=refs if refs is not None else ['ev-1']))

# Capture the original suites, with only the regression output root redirected.
for suite_name, file in [('contracts', 'sage/evaluation/tests/test_product_state.py'), ('regressions', 'sage/tests/test_state.py')]:
    spec=importlib.util.spec_from_file_location(suite_name, REPO / file)
    module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    if suite_name == 'regressions':
        def root(self, name):
            path=HERE / 'regression-suite' / name; path.mkdir(parents=True, exist_ok=True); return path
        module.StateRegressionTests.root=root
    stream=io.StringIO()
    outcome=unittest.TextTestRunner(stream=stream, verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(module))
    (HERE / (suite_name+'.txt')).write_text(stream.getvalue())
    results[suite_name]=dict(tests=outcome.testsRun, failures=len(outcome.failures), errors=len(outcome.errors), skipped=len(outcome.skipped))

# Resume must preserve release barriers even when a result's outcome is known.
rows=[opened(), event(2, 'plan.revised', plan([task('t-1','write',owner='agent-a')]))]
admitted(rows); request(rows); evidence(rows); result(rows,effect='reconciled')
call('resume-writer-result-no-terminal', 'resume', rows, agents=[])
call('resume-writer-result-no-terminal', 'validate')
root_rows=[opened(), event(2, 'plan.revised', plan([task('t-1','write')]))]
admitted(root_rows); result(root_rows,outcome='failed',effect='unknown',refs=[])
call('resume-root-failed-unknown','resume',root_rows,agents=[])
call('resume-root-failed-unknown','validate')
reconciled=copy.deepcopy(root_rows); evidence(reconciled); result(reconciled,outcome='failed',effect='reconciled')
call('root-failed-unknown-reconciliation','validate',reconciled)
# Control: a released root writer allows admission.
control=copy.deepcopy(root_rows[:-1]); evidence(control); result(control,effect='reconciled')
call('resume-root-released','resume',control,agents=[])
# Merely planned root work should not invent an active writer.
call('resume-planned-root','resume',root_rows[:2],agents=[])

# A second handle for one task bypasses one-actor release checks.
rows=[opened(), event(2,'plan.revised',plan([task('t-1','write',owner='agent-a'),task('t-2','write')]))]
admitted(rows); request(rows); request(rows,'agent-b')
observed(rows,'agent-a'); observed(rows,'agent-b','active','unknown')
evidence(rows); result(rows,effect='reconciled'); admitted(rows,'t-2')
call('two-handles-one-active','validate',rows)
single=copy.deepcopy(rows)
single=[row for row in single if not (row['type']=='agent.requested' and row['payload']['handle']=='agent-b') and not (row['type']=='agent.observed' and row['payload']['handle']=='agent-b')]
for n,row in enumerate(single,1): row['seq']=n; row['event_id']=f'e-{n}'
call('single-released-handle-control','validate',single)

# A late result for a retired task revision must not update the current revision.
rows=[opened(),event(2,'plan.revised',plan([task('t-1')]))]
admitted(rows); evidence(rows)
changed=task('t-1'); changed['revision']=2; changed['inputs']=['new requested scope']
push(rows,'plan.revised',plan([changed],2,'evidence_change',['e-4']))
result(rows,rev=1)
call('late-old-result','snapshot',rows)
call('late-old-result','report')

# Malformed JSON types are data errors, not uncaught Python failures.
for name, mutate in [
    ('enum-array', lambda r: r[0].update(type=[])),
    ('version-bool', lambda r: r[0].update(v=True)),
    ('sequence-float', lambda r: r[0].update(seq=1.0)),
    ('timestamp-invalid', lambda r: r[0].update(at='2026-99-99T99:99:99Z')),
]:
    rows=[opened()]; mutate(rows); call(name,'validate',rows)
rows=[opened(),event(2,'run.amended',dict(kind='objective',value='corrected objective',reason='correction',corrects_event_id='missing'))]
call('dangling-amendment','snapshot',rows)
rows[-1]['payload']['corrects_event_id']='e-1'
call('valid-amendment-control','snapshot',rows)
# New graph node is an operational change, even if old nodes stay intact.
rows=[opened(),event(2,'plan.revised',plan([task('t-1')]))]; evidence(rows)
push(rows,'plan.revised',plan([task('t-1'),task('t-2')],2,'evidence_change',['e-3']))
call('new-task-only','validate',rows)
rows[-1]['payload']['no_progress']='bounded expanded graph'
call('new-task-with-bound-control','validate',rows)
# A retry labeled initial bypasses failure cause/evidence fields.
rows=complete_read_run()[:5]; rows[-1]['payload']['outcome']='failed'
changed=task('t-1'); changed['revision']=2; changed['inputs']=['retry']
push(rows,'plan.revised',plan([changed],2,'initial',['e-5']))
admitted(rows,rev=2,pr=2)
call('retry-initial-reason','validate',rows)

# A criterion must reference an observation associated with that criterion.
rows=complete_read_run(); rows[3]['payload']['criterion_ids']=[]
call('closure-unassociated-evidence','validate',rows)
# A required check cannot pass with no evidence.
rows=complete_read_run(); rows[5]['payload']['evidence_ids']=[]
call('closure-empty-check-evidence','validate',rows)
# A later observed failed check should remain visible at closure/report.
rows=complete_read_run()[:-1]
push(rows,'check.recorded',dict(check_id='final-integration',criterion_ids=['c-1'],outcome='failed',evidence_ids=['ev-1']))
push(rows,'run.closed',dict(status='completed',criterion_evidence={'c-1':['ev-1']},scope_reconciled=True,remaining_human_items=[]))
call('closure-later-failed-check','validate',rows)
call('closure-later-failed-check','report')

# Reports should retain untested evidence, accepted residuals and terminal outcome.
rows=complete_read_run()[:-1]
push(rows,'evidence.recorded',dict(evidence_id='ev-not-tested',criterion_ids=['c-1'],kind='untested',locator='mobile viewport not exercised',sha256=None))
push(rows,'finding.opened',dict(finding_id='f-minor',severity='minor',summary='narrow-screen label overlap',evidence_ids=['ev-1']))
push(rows,'finding.dispositioned',dict(finding_id='f-minor',disposition='accepted',evidence_ids=['ev-1'],verification_check_id=None))
push(rows,'run.closed',dict(status='stopped',criterion_evidence={},scope_reconciled=False,remaining_human_items=[]))
call('report-omissions','report',rows)

# Execute the documented example exactly, with the run id it declares.
source=(REPO/'sage/skills/sage/references/state.md').read_text()
sample=source.split('```jsonl\n')[1].split('```')[0]
example_root=HERE/'tiny-example'; example_root.mkdir(exist_ok=True)
example=Path(tempfile.mkdtemp(dir=example_root))
save(example/'criteria.json',[{'id':'c-1','text':'The bounded read is observed and checked.'}])
cp=subprocess.run([sys.executable,str(REPO/'sage/scripts/sage_state.py'),'init','--run-dir',str(example/'run'),'--run-id','tiny-1','--objective','bounded read','--criteria',str(example/'criteria.json')],capture_output=True,text=True)
(example/'wave.jsonl').write_text(sample)
wave=subprocess.run([sys.executable,str(REPO/'sage/scripts/sage_state.py'),'append','--run-dir',str(example/'run'),'--events',str(example/'wave.jsonl')],capture_output=True,text=True)
results['tiny-example']={'init_exit':cp.returncode,'append_exit':wave.returncode,'append_stderr':wave.stderr}
save(HERE/'results.json',results)
print(json.dumps({key: {field:value for field,value in row.items() if field in ('exit_code','output','tests','failures','errors','init_exit','append_exit')} for key,row in results.items()},indent=2))
