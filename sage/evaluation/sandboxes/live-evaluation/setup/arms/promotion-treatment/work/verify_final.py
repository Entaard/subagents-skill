import hashlib, json, os, pathlib, subprocess, sys
root = pathlib.Path(__file__).resolve().parents[1]
env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', TMPDIR=str(root/'tmp'))
def read(name): return json.loads((root/name).read_text())
def sha(name): return hashlib.sha256((root/name).read_bytes()).hexdigest()
baseline, staged = read('evidence/initial-checks.json'), read('evidence/staged-generation-hashes.json')
commands = read('evidence/landing-checks.json')
parsed = {x['name']: json.loads(x['stdout']) for x in commands}
before, during, after = (parsed[name] for name in ('before-retrieve', 'during-retrieve', 'after-retrieve'))
checks = {
    'all_landing_cli_exits_zero': all(x['exit_code'] == 0 for x in commands),
    'original_pointer_bytes_restored': sha('state/knowledge/current.json') == baseline['prior_store_hashes']['state/knowledge/current.json'],
    'source_run_bytes_unchanged': all(sha(f) == h for f, h in baseline['source_hashes'].items()),
    'original_store_bytes_restored': all(sha(f) == h for f, h in baseline['prior_store_hashes'].items()),
    'both_retained_generations_byte_identical': all(sha(f) == h for f, h in staged.items()),
    'exact_two_retained_generations': sorted(p.name for p in (root/'state/knowledge/generations').iterdir()) == ['controlled-prior', 'promotion-live-v2'],
    'before_after_retrieval_exactly_equal': before == after,
    'unchanged_cues_fingerprint': before['cue_fingerprint'] == during['cue_fingerprint'] == after['cue_fingerprint'],
    'actual_cues_bytes_unchanged': sha('inputs/cues.json') == '3734ff44664301de73a2d9a87707bbcb3d2789519301a7aa97cd26a9ebbdab8b',
    'during_revision_two_supported': [(m['id'],m['revision'],m['status']) for m in during['matches']] == [('museum-csv-field-count',2,'supported')],
    'after_revision_one_supported': [(m['id'],m['revision'],m['status']) for m in after['matches']] == [('museum-csv-field-count',1,'supported')],
    'new_generation_bound_to_original_parent': parsed['stage']['prior_generation_id'] == 'controlled-prior',
    'record_assembly_preserved': read('state/knowledge/generations/promotion-live-v2/records/museum-csv-field-count.json') == read('work/proposal-final.json')['record'],
}
m = during['matches'][0]
checks['retrieved_scope_and_counterevidence_intact'] = 'Python 3.11.6' in m['gate_rationale'] and 'outside these samples' in m['gate_rationale'] and 'csv-old:ev-1' in m['counterevidence'] and 'these museum CSV inputs' in m['rule']
checks['frozen_artifacts_unchanged'] = all(sha(f)==h for f,h in read('evidence/preflight-checks.json')['hashes'].items())
rechecks = []
for source in ('csv-old','csv-new'):
    args = [sys.executable,str(root/'installed/sage/bin/sage_state.py'),'validate','--run-dir',str(root/'state/runs'/source),'--terminal']
    result = subprocess.run(args,cwd=root,env=env,text=True,capture_output=True)
    rechecks.append({'command':args,'exit_code':result.returncode,'stdout':result.stdout,'stderr':result.stderr})
    checks[source+'_terminal_validation'] = result.returncode == 0 and json.loads(result.stdout)['terminal']
args = [sys.executable,str(root/'inputs/observe.py')]
result = subprocess.run(args,cwd=root,env=env,text=True,capture_output=True)
rechecks.append({'command':args,'exit_code':result.returncode,'stdout':result.stdout,'stderr':result.stderr})
observed = json.loads(result.stdout)
checks['final_observations_match_hash_bound_inputs'] = result.returncode == 0 and all(observed[k] == read('inputs/'+k+'-observations.json')['rows'] for k in ('old','new'))
checks['old_falsifier_fired'] = observed['new'][1]['plain_split_fields'] == 4 and observed['new'][1]['csv_reader_fields'] == 3
checks['parser_counts_three_for_every_supplied_row'] = all(r['csv_reader_fields'] == 3 for rows in observed.values() for r in rows)
result = {'checks':checks,'pointer':read('state/knowledge/current.json'),'pointer_sha256':sha('state/knowledge/current.json'),'generation_hashes':{f:sha(f) for f in staged},'final_proposal_sha256':sha('work/proposal-final.json'),'rechecks':rechecks}
print(json.dumps(result,indent=2))
sys.exit(0 if all(checks.values()) else 1)
