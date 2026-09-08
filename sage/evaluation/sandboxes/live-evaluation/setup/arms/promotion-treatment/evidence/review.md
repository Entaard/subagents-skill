# Independent promotion review

Actor: `/root/live_promotion_reviewer`  
Outcome: `failed`  
Gate decision: `focused_repair_required`  
Reviewed at: `2026-09-07T22:38:28Z`

The scoped-fact correction is semantically supported only for the supplied Python 3.11.6 fixture, but the frozen proposal is not ready to land because revision 2 would not retrieve under the unchanged cues for the actual task.

## Checks observed now

- Frozen `work/proposal-author.json` SHA-256: `0b47528af48379b92da23bacecc7aab9812564840907f3eb53ba141d94309ed9` (matched).
- Frozen `work/refutation.json` SHA-256: `e5e16eccf68afdcfeb2915c580f34170b779f7dde73d56d27aa7e34d63d6fcee` (matched).
- `csv-old` and `csv-new` terminal validation: both `ok=true`, `terminal=true`, `last_seq=8`.
- Repeated `python3 inputs/observe.py` under Python 3.11.6. Every supplied row produced three `csv.reader` fields. New row A3 produced four literal split pieces and three parser fields, directly firing revision 1's falsifier. The checked observation file hashes matched `csv-old:ev-1` and `csv-new:ev-1`.
- Prior store validation: `current=controlled-prior`, `generation_count=1`, `ok=true`.
- Actual retrieval before any landing, using unchanged `inputs/cues.json`: cue fingerprint `7b4fa620a62fdf1b50210230b7792138f6b38cb6140796ecc1898567924c4d29`; matched `museum-csv-field-count` revision 1, status `supported`.
- Direct application of the documented retrieval predicate to frozen revision 2: recognizer intersections exist for `domain=museum imports`, `artifact=csv`, and `operation=count fields`, but `qualifier.all.environment=[python 3 stdlib csv]` has no intersection with `inputs/cues.json`; therefore `would_match=false`. Using every nonempty candidate recognizer cue instead yields `would_match=true`, confirming the defect is the mismatch with the actual task cue file rather than an impossible qualifier.

## Refutation dispositions

- `rf-scope` — `resolved`. The frozen candidate retains the supplied-sample and Python 3.11.6 boundary in the rule, gate rationale, gate evidence, evidence summary, and alternatives. Selected evidence: `csv-old:ev-1`, `csv-new:ev-1`.
- `rf-strength` — `resolved`. A3 disproves literal comma counting for the supplied row; A4 and the old rows support only field-count observations. The candidate makes no broader escaping, dialect, malformed-input, or validation claim. Selected evidence: `csv-new:ev-1`, `csv-old:ev-1`.

## Additional finding

### `rv-retrieval-actual-cues`

- Severity: blocker
- Criterion: `landing-retrieval` — retrieve using the cues for the actual task and report exact revision/status behavior.
- Exact evidence: `inputs/cues.json` omits `environment`; `work/proposal-author.json#/record/qualifier/all/environment` requires `python 3 stdlib csv`; the installed retrieval contract requires every nonempty `qualifier.all` key to intersect. The observed current CLI retrieval returns revision 1, while the direct frozen-candidate predicate check gives `would_match=false` for revision 2.
- Minimal falsifiable repair: in the single allowed author repair, set `qualifier.all.environment` to an empty array while preserving the Python 3.11.6 and supplied-sample boundary in `gate_evidence`, `gate_rationale`, `rule`, and `evidence_summary`. Leave `inputs/cues.json` unchanged.
- Falsifiable fix check: after the repair is independently reviewed and coordinator-staged, retrieval with the unchanged `inputs/cues.json` must return `museum-csv-field-count` revision 2 with status `supported` and expose the supplied-sample/Python boundary. `no_match` or lost boundary text fails the repair.

## Semantic, lineage, and authenticity assessment

The `correct` action preserves stable ID `museum-csv-field-count`, advances retained revision 1 to revision 2, and retains the old observation as counterevidence. Its new falsifier remains observable. The direct, repeatable check satisfies the `scoped_fact` predicate only in the declared fixture; there is no support for other parsers, malformed CSV, dialects, or unseen museum inputs.

The source runs, fixture provenance, and `/controlled/seed-*` actors are synthetic scaffolding, not authentic prior Sage teams. Their structural attestations were not treated as live independence or semantic proof. This reviewer records only native actor ID `/root/live_promotion_reviewer`; effective identity/model/effort, token use, and money are unobserved and recorded as `null` in the JSON.

## Still unexecuted and coordinator-owned

No candidate, source, installed policy, or store bytes were changed. A focused repair and refreeze, review of the repaired artifact, staging, post-stage validation, activation, live revision-2 retrieval, rollback, pointer restoration, and retained-history validation remain unexecuted. Consequently there is no observed during-landing or after-rollback retrieval result in this review.

Writer lease: `RELEASE`.
