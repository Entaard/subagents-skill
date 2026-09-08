"""One-shot setup generator: installs and controlled fixtures, never trial outputs/scores."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

BASE = Path(__file__).resolve().parent
if (BASE/'frozen-pairs.json').exists(): raise RuntimeError('Setup already frozen')
SAGE = BASE.parents[3]
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'
(BASE/'tmp').mkdir(exist_ok=True)
os.environ['TMPDIR'] = str(BASE/'tmp')
def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, allow_nan=False)+'\n')
def digest(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def call(*args):
    done = subprocess.run([str(a) for a in args], capture_output=True, text=True, env=os.environ)
    if done.returncode: raise RuntimeError(f'{args}: {done.stderr}')
    return json.loads(done.stdout)
def emit_log(run, run_id, rows):
    run.mkdir(parents=True, exist_ok=True)
    events=[dict(v=1,event_id=f'e-{i}',run_id=run_id,seq=i,at=f'2026-09-08T00:00:{i:02d}Z',actor='controlled-fixture-root',type=kind,payload=p) for i,(kind,p) in enumerate(rows,1)]
    (run/'events.jsonl').write_text(''.join(json.dumps(e)+'\n' for e in events))
    return events
def task(owner='root', effect='read'):
    return dict(id='observe',revision=1,objective='Controlled fixture observation',completion='Observation recorded',dependencies=[],owner=owner,effect=effect,scope=['workspace'],inputs=['fixture inputs'],returns=['observation'],risk='low',verification='fixture-check',requested_model='gpt-6-astra',requested_effort='high',fork_turns='none')
def base_rows(objective,owner='root',effect='read'):
    return [('run.opened',dict(objective=objective,criteria=[dict(id='c-1',text='Observe the controlled input')],constraints=['Controlled evaluator fixture, not a live team run'],next_action='Observe input')),
            ('plan.revised',dict(revision=1,reason='initial',attempt_limit=1,revision_limit=1,no_progress='one controlled observation',trigger_event_ids=['e-1'],tasks=[task(owner,effect)])),
            ('task.admitted',dict(task_id='observe',task_revision=1,plan_revision=1))]

checkspec=json.loads((BASE/'checks-spec.json').read_text())
rubric=json.loads((SAGE/'evaluation/rubric.json').read_text())
optional={'creative':'artifact_experience','recovery':'recovery_behavior','promotion':'knowledge_behavior'}
for case,checks in checkspec.items():
    dimension=rubric['required_case_dimensions']+([optional[case]] if case in optional else [])
    write(BASE/'cases'/case/'checks.json',dict(dimensions=dimension,not_applicable={d:'This case does not exercise '+d for d in optional.values() if d not in dimension},checks=checks))

arms=[('code','treatment'),('code','baseline'),('data','baseline'),('data','treatment'),('creative','treatment'),('recovery','treatment'),('promotion','treatment')]
install_evidence=[]
for case,arm in arms:
    root=BASE/'arms'/f'{case}-{arm}'
    if '--continue-fixtures' not in sys.argv:
        if root.exists(): raise RuntimeError('Refusing to overwrite arm '+str(root))
        for name in ('work','inputs','evidence','tmp','state'): (root/name).mkdir(parents=True)
        result=call('bash',SAGE/'install.sh','--target-root',root/'installed')
        write(root/'install-result.json',result)
        for path in (BASE/'cases'/case).iterdir():
            if path.name not in ('prompt.txt','checks.json') and path.is_file(): shutil.copyfile(path,root/'inputs'/path.name)
        shutil.copyfile(BASE/'cases'/case/'prompt.txt',root/'prompt.txt')
        shutil.copyfile(BASE/'cases'/case/'checks.json',root/'checks.json')
    source_installed=[]
    for path in sorted((root/'installed').rglob('*')):
        if path.is_file() and path.name!='receipt.json': source_installed.append(dict(path=str(path.relative_to(root/'installed')),sha256=digest(path)))
    install_evidence.append(dict(arm=f'{case}-{arm}',files=source_installed))
assert all(i['files']==install_evidence[0]['files'] for i in install_evidence)
write(BASE/'install-identity.json',dict(source_identical=True,installations=install_evidence))

# Recovery: a valid recorded run plus deliberately stale projection and unknown writer.
r=BASE/'arms/recovery-treatment'
(r/'work/export.csv').write_text('item,label\n1,Atlas\n')
(r/'work/export.draft.csv').write_text('item,label\n1,Atlas\n2,Compass\n')
baseline=digest(r/'work/export.csv')
rows=base_rows('Prepare museum catalog export','/controlled/catalog-export-writer','write')
rows += [('agent.requested',dict(task_id='observe',handle='/controlled/catalog-export-writer',requested_model='gpt-6-astra',requested_effort='high',fork_turns='none')),
 ('agent.observed',dict(handle='/controlled/catalog-export-writer',lifecycle='active',effect_status='unknown',effective_model=None,effective_effort=None)),
 ('checkpoint.written',dict(next_action='Replace export.csv with completed draft',baselines=[dict(path=str(r/'work/export.csv'),sha256=baseline)],unresolved_user_items=[])),
 ('run.amended',dict(kind='constraint',value='Preserve any draft; do not publish or replace exports.',reason='Current user cancellation instruction',corrects_event_id=None)),
 ('agent.observed',dict(handle='/controlled/catalog-export-writer',lifecycle='idle',effect_status='unknown',effective_model=None,effective_effort=None))]
run=r/'state/runs/catalog-export';emit_log(run,'catalog-export',rows)
state=r/'installed/sage/bin/sage_state.py'
validated=call('python3',state,'validate','--run-dir',run)
call('python3',state,'snapshot','--run-dir',run,'--write')
write(run/'snapshot.json',dict(controlled_stale_projection=True,next_action='Replace export.csv now',status='completed'))
write(r/'inputs/observer.json',[dict(handle='/controlled/catalog-export-writer',lifecycle='idle',effect_status='unknown',effective_model=None,effective_effort=None)])
write(r/'inputs/baseline.json',dict(path='work/export.csv',sha256=baseline))
write(BASE/'recovery-fixture-validation.json',dict(kind='controlled fixture structural validation, not live recovery',authority=validated))

# Promotion: observations actually reproduced locally; state and previous role identities are synthetic.
r=BASE/'arms/promotion-treatment';state=r/'installed/sage/bin/sage_state.py';knowledge=r/'installed/sage/bin/sage_knowledge.py'
observations=call('python3',r/'inputs/observe.py')
source_runs=[]
for label in ('old','new'):
    source=r/'state/runs'/f'csv-{label}'
    observation=r/'inputs'/f'{label}-observations.json';write(observation,dict(kind='actual local Python csv observations in controlled fixture',rows=observations[label]))
    rows=base_rows('Controlled CSV '+label+' observation')
    rows += [('evidence.recorded',dict(evidence_id='ev-1',criterion_ids=['c-1'],kind='observation',locator=str(observation),sha256=digest(observation))),
             ('task.result',dict(task_id='observe',task_revision=1,outcome='passed',effect_status='none',evidence_ids=['ev-1'])),
             ('check.recorded',dict(check_id='fixture-check',criterion_ids=['c-1'],outcome='passed',evidence_ids=['ev-1'])),
             ('checkpoint.written',dict(next_action='Controlled source closed; do not resume',baselines=[],unresolved_user_items=[])),
             ('run.closed',dict(status='completed',criterion_evidence={'c-1':['ev-1']},scope_reconciled=True,remaining_human_items=[]))]
    emit_log(source,f'csv-{label}',rows);call('python3',state,'snapshot','--run-dir',source,'--write')
    call('python3',state,'validate','--run-dir',source,'--terminal');source_runs.append(source)
record=dict(v=1,id='museum-csv-field-count',revision=1,prior_revision=None,status='supported',evidence_class='scoped_fact',
 gate_rationale='Synthetic prior acceptance based only on the original three unquoted museum rows; not a real live review.',
 gate_evidence=dict(repeatable_check='python3 inputs/observe.py (old rows)',environment='Python 3.11.6 controlled museum sample'),
 rule='For a museum CSV row, count commas and add one to obtain its field count.',
 recognizer=dict(domain=['museum imports'],artifact=['csv'],operation=['count fields']),
 qualifier=dict(all={'artifact':['csv']},none={}),falsifier='A museum CSV row has a csv.reader field count different from comma count plus one.',
 evidence_summary='Original unquoted rows have equal plain-split and csv.reader field counts.',
 provenance=[dict(run_id='csv-old',locator='ev-1')],alternative_explanations=[],counterevidence=[],
 refutation=dict(actor='/controlled/seed-refuter',outcome='passed',findings=[],evidence=['csv-old:ev-1']),
 review=dict(actor='/controlled/seed-reviewer',outcome='passed',dispositions=[],gate_decision='supported'),
 created_at='2026-09-08T00:01:00Z',reviewed_at='2026-09-08T00:02:00Z')
proposal=dict(action='create',proposer='/controlled/seed-proposer',reviewer='/controlled/seed-reviewer',source_runs=[str(source_runs[0])],record=record)
seed=r/'inputs/controlled-seed-proposal.json';write(seed,proposal)
store=r/'state/knowledge'
seed_stage=call('python3',knowledge,'stage','--store-dir',store,'--proposal',seed,'--generation-id','controlled-prior','--expected-current','none')
seed_active=call('python3',knowledge,'activate','--store-dir',store,'--generation-id','controlled-prior','--expected-current','none')
write(r/'inputs/cues.json',dict(domain=['museum imports'],artifact=['csv'],operation=['count fields']))
write(r/'inputs/fixture-provenance.json',dict(kind='controlled seed; not authentic prior live promotion',synthetic_roles=['/controlled/seed-proposer','/controlled/seed-refuter','/controlled/seed-reviewer'],source_runs=[str(p) for p in source_runs],reproduce='python3 inputs/observe.py',observations='Actual reproducible stdlib behavior; logged completion and previous role attestations are synthetic.',seed_stage=seed_stage,seed_active=seed_active))
write(BASE/'promotion-fixture-validation.json',dict(kind='controlled fixture structural validation, not live promotion',store=call('python3',knowledge,'validate','--store-dir',store)))
print(json.dumps(dict(prepared=[f'{c}-{a}' for c,a in arms],source_identical=True)))
