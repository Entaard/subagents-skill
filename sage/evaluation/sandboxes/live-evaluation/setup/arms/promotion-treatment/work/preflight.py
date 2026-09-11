import copy, hashlib, json, pathlib
root = pathlib.Path(__file__).resolve().parents[1]
def read(name): return json.loads((root/name).read_text())
def sha(name): return hashlib.sha256((root/name).read_bytes()).hexdigest()
baseline = read('evidence/initial-checks.json')
checks = {key: all(sha(f) == h for f, h in baseline[key].items()) for key in ('source_hashes', 'prior_store_hashes')}
expected = {
    'work/proposal-author.json': '0b47528af48379b92da23bacecc7aab9812564840907f3eb53ba141d94309ed9',
    'work/proposal-repaired.json': 'd6ad2320f1495490238b8b801e79f4830f02f4e1c12f3fd3f32b850cfd0ab8b8',
    'work/refutation.json': 'e5e16eccf68afdcfeb2915c580f34170b779f7dde73d56d27aa7e34d63d6fcee',
    'work/review.json': '2bcde4320c13d96ed521c5f2e36377c0feee44406ee932cf29d73838e02517a5',
    'work/refutation-repaired.json': '187145f60e5758944411ce0533efff322a5c9b6047c84f3204d9f76db134b857',
    'work/review-repaired.json': 'ea6f55cc43fca781cb17c197fa14056d534f062ac9b82fa76fe24d794a5f805a',
    'evidence/review-repaired.md': '1f5c5181ee47f127a02eed4404c7ad0d6a146a077a1cab497024146a523b0e6d',
    'inputs/cues.json': '3734ff44664301de73a2d9a87707bbcb3d2789519301a7aa97cd26a9ebbdab8b',
}
checks['frozen_artifact_hashes'] = all(sha(f) == h for f, h in expected.items())
candidate, original = read('work/proposal-repaired.json'), read('work/proposal-author.json')
original['record']['qualifier']['all']['environment'] = []
checks['only_one_author_repair_change'] = original == candidate
refutation, review = read('work/refutation-repaired.json'), read('work/review-repaired.json')
checks['independent_role_ids'] = len({candidate['proposer'], refutation['actor'], review['actor'], '/root/live_promotion_treatment'}) == 4
checks['actual_changed_candidate_reviewed'] = review['metadata']['candidate_sha256'] == expected['work/proposal-repaired.json'] == refutation['metadata']['candidate_sha256']
checks['gates_passed'] = refutation['outcome'] == review['outcome'] == 'passed' and review['gate_decision'] == candidate['record']['status'] == 'supported'
checks['all_findings_dispositioned'] = sorted(f['id'] for f in refutation['findings']) == sorted(d['finding_id'] for d in review['dispositions'])
checks['reviewer_terminal_release'] = read('evidence/outer-reviewer-recheck-lifecycle-observation.json')['explicit_release'] and read('evidence/outer-reviewer-recheck-lifecycle-observation.json')['status'] == 'completed'
assert all(checks.values()), checks
proposal = copy.deepcopy(candidate)
proposal['reviewer'] = review['actor']
proposal['record']['refutation'] = {k: refutation[k] for k in ('actor', 'outcome', 'findings', 'evidence')}
proposal['record']['review'] = {k: review[k] for k in ('actor', 'outcome', 'dispositions', 'gate_decision')}
proposal['record']['reviewed_at'] = review['reviewed_at']
print(json.dumps({'checks': checks, 'hashes': {f:sha(f) for f in expected}, 'proposal': proposal}, indent=2))
