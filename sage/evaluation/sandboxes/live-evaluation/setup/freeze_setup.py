"""Freeze selected cases and exact initial sandbox bytes; no trial execution."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import os
BASE=Path(__file__).resolve().parent
SAGE=BASE.parents[3]
os.environ['PYTHONDONTWRITEBYTECODE']='1';os.environ['TMPDIR']=str(BASE/'tmp')
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def canonical(value):return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def write(path,value):path.write_text(json.dumps(value,indent=2)+'\n')
def artifact(path):return dict(path=str(path),sha256=sha(path))
if (BASE/'frozen-pairs.json').exists():raise RuntimeError('Refusing to refreeze')
arms=[('code','treatment'),('code','baseline'),('data','baseline'),('data','treatment'),('creative','treatment'),('recovery','treatment'),('promotion','treatment')]
template=(BASE/'actor-packet-template.txt').read_text()
for case,arm in arms:
    root=BASE/'arms'/f'{case}-{arm}'
    routing='Eligible worker model routing: let installed Sage choose bounded role models.' if arm=='treatment' else 'Eligible worker model routing override: request gpt-6-astra for EVERY worker, including implementer, reviewer, adviser and any scout; keep installed Sage procedure and role-appropriate effort otherwise.'
    special=''
    if case=='creative':
        shutil.copyfile(BASE/'browser-usage.txt',root/'inputs/browser-usage.txt')
        special=f'Read {root}/inputs/browser-usage.txt. The frozen evaluation harness is {BASE}/browser-harness.mjs (read/execute only).'
    if case=='recovery':special='Resume the preloaded state/runs/catalog-export fixture; authoritative append-only history may receive supported events, while original bytes must remain as the prefix. The evaluation source intentionally remains open if effects cannot be reconciled.'
    if case=='promotion':special='Explicitly invoke $sage-promote (separate from main Sage). Source runs are state/runs/csv-old and state/runs/csv-new, read-only; target store is state/knowledge. Read inputs/fixture-provenance.json. Prior seed identities are synthetic; new proposal/refutation/review identities must be actual native actors.'
    (root/'launch-packet.txt').write_text(template.format(arm_root=root,special=special,routing=routing))

environment=dict(schema_version='sage-live-environment-v1',frozen_date='2026-09-08',
 platform='macOS local evaluation sandbox',python='3.11.6',node='26.7.0',chrome='152.0.7977.82',
 native_collaboration=dict(root_model_requested='gpt-6-astra',root_effort_requested='high',effective_model=None,effective_effort=None,actors='fresh fork-none native calls, sequential delegation, one writer',raw_native_transcript_access=False,journal='actor-authored, not raw transcript',outer_capture='independently observed tool lifecycle and returned artifacts where available'),
 source_identity=artifact(BASE/'install-identity.json'),
 browser=dict(surface='isolated local owned headless; connected Browser unavailable',neutral_probe_only=True,restricted_attempt='failed',isolated_attempt_2='launch/screenshot succeeded; Enter failed',isolated_attempt_3='Tab focus and Enter activation observed at both viewports',harness=artifact(BASE/'browser-harness.mjs'),usage=artifact(BASE/'browser-usage.txt'),probe=artifact(BASE/'probe/attempt-3/observations.json'),permissions='sandbox escalation may be required; no personal profiles or remote assets'),
 metrics=dict(tokens=None,money=None,wall='limited local operational observation, not cost',calls='observed native actor invocations including coordinator and workers; tool calls reported separately if available'),
 order=[f'{c}-{a}' for c,a in arms],scope='Two routing pairs plus three single-arm smokes; no population quality or savings inference')
write(BASE/'environment.json',environment)
selection=dict(schema_version='sage-case-selection-v1',rubric='../../../rubric.json',protocol='../../../live-protocol.md',environment='environment.json',root_model='gpt-6-astra',root_procedure='installed_sage',cases=[])
for case,kind in [('code','code'),('data','evidence_data')]:
    inputs=[str(p.relative_to(BASE)) for p in sorted((BASE/'cases'/case).iterdir()) if p.name not in ('prompt.txt','checks.json')]
    inputs+=['install-identity.json','actor-packet-template.txt']
    inputs += [f'arms/{case}-{arm}/launch-packet.txt' for arm in ('treatment','baseline')]
    selection['cases'].append(dict(case_id='LIVE-'+case.upper()+'-01',kind=kind,prompt=f'cases/{case}/prompt.txt',inputs=inputs,checks=f'cases/{case}/checks.json'))
write(BASE/'selection.json',selection)
completed=subprocess.run(['python3',str(SAGE/'evaluation/pairing.py'),'prepare',str(BASE/'selection.json'),'--output',str(BASE/'frozen-pairs.json')],capture_output=True,text=True,env=os.environ)
if completed.returncode:raise RuntimeError(completed.stderr)

# Immutable baseline copies let later actors append state without changing frozen inputs.
single_cases=[]
for case,kind in [('creative','creative_interaction_smoke'),('recovery','recovery'),('promotion','promotion')]:
    root=BASE/'arms'/f'{case}-treatment';frozen=BASE/'initial'/f'{case}-treatment'
    shutil.copytree(root,frozen)
    files=[artifact(p) for p in sorted(frozen.rglob('*')) if p.is_file()]
    single_cases.append(dict(case_id='LIVE-'+case.upper()+'-01',kind=kind,arm='treatment',root_model_requested='gpt-6-astra',root_procedure='installed_sage',prompt=artifact(BASE/'cases'/case/'prompt.txt'),checks=artifact(BASE/'cases'/case/'checks.json'),initial_input_tree=files,working_arm=str(root),launch_packet=artifact(root/'launch-packet.txt')))
smokes=dict(schema_version='sage-single-smokes-v1',scoring='Every applicable frozen rubric dimension must receive an independently evidenced 0-10 score after actual execution; no alteration to anchors/gate.',order=[c['case_id'] for c in single_cases],rubric=artifact(SAGE/'evaluation/rubric.json'),protocol=artifact(SAGE/'evaluation/live-protocol.md'),environment=artifact(BASE/'environment.json'),cases=single_cases)
smokes['manifest_sha256']=canonical(smokes);write(BASE/'frozen-smokes.json',smokes)
inventory=[]
for case,arm in arms:
    root=BASE/'arms'/f'{case}-{arm}'
    inventory.append(dict(arm=f'{case}-{arm}',root=str(root),initial_files=[artifact(p) for p in sorted(root.rglob('*')) if p.is_file()]))
write(BASE/'initial-arm-hashes.json',inventory)
setup=dict(schema_version='sage-live-setup-freeze-v1',kind='setup only; no live outcomes or scores',pairs=artifact(BASE/'frozen-pairs.json'),smokes=artifact(BASE/'frozen-smokes.json'),initial_arm_hashes=artifact(BASE/'initial-arm-hashes.json'),setup_sources=[artifact(BASE/name) for name in ['prepare_setup.py','freeze_setup.py','checks-spec.json','actor-packet-template.txt','browser-harness.mjs','browser-usage.txt']],limitations=['STATUS was initially read too broadly and contains prior embedded review history; it was not used to shape live prompts or actor packets.','The evaluator authored task setup and controlled fixtures, not any live task output.','Neutral browser probe and fixture structural validation are setup evidence only.','Raw native transcript is unavailable; actor journals must retain provenance and cannot stand in as raw harness recordings.'])
setup['manifest_sha256']=canonical(setup);write(BASE/'setup-freeze.json',setup)
print(json.dumps(dict(pairs=json.loads((BASE/'frozen-pairs.json').read_text())['manifest_sha256'],smokes=smokes['manifest_sha256'],setup=setup['manifest_sha256']),indent=2))
