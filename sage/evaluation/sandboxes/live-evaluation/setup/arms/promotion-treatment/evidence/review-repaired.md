# Independent review of repaired promotion candidate

Actor: `/root/live_promotion_reviewer`  
Outcome: `passed`  
Gate decision: `supported`  
Reviewed at: `2026-09-07T23:02:07Z`

The single repair resolves the actual-cue retrieval blocker without changing the scoped-fact evidence or claiming transfer. The frozen candidate is semantically supported for the Python 3.11.6 supplied fixture and is ready for coordinator-owned landing checks.

## Frozen artifacts and exact repair

- `work/proposal-repaired.json`: SHA-256 `d6ad2320f1495490238b8b801e79f4830f02f4e1c12f3fd3f32b850cfd0ab8b8`.
- `work/refutation-repaired.json`: SHA-256 `187145f60e5758944411ce0533efff322a5c9b6047c84f3204d9f76db134b857`.
- `inputs/cues.json`: SHA-256 `3734ff44664301de73a2d9a87707bbcb3d2789519301a7aa97cd26a9ebbdab8b`.
- Exact structured diff from the original candidate: only `/record/qualifier/all/environment` changed, from `["python 3 stdlib csv"]` to `[]`.

The rule still says `Python csv.reader` and `these museum CSV inputs`. The gate rationale still says the evidence covers the declared Python 3.11.6 controlled fixture and excludes other parsers, malformed CSV, dialects, and museum inputs outside the samples. Gate evidence, evidence summary, falsifier, provenance, alternatives, and `csv-old:ev-1` counterevidence are unchanged.

## Checks observed now

- `csv-old` and `csv-new` each terminal-validated: `ok=true`, `terminal=true`, `last_seq=8`.
- Repeated `python3 inputs/observe.py` under Python 3.11.6. Every supplied row returned three `csv.reader` fields. A3 returned four literal split pieces and three parser fields, firing revision 1's falsifier. The source-bound observation hashes remain `5dbbf4615b431385d733936491f09698734f7bddb689a4827a990fb30e9ea82a` (`csv-old:ev-1`) and `4e7b1ef478b480cafb7c1ed4c0320ab7538e5beaf98de145ffc6f1eb5ab9b70a` (`csv-new:ev-1`).
- The prior store validates with `current=controlled-prior`, `generation_count=1`.
- Before landing, unchanged `inputs/cues.json` retrieves `museum-csv-field-count` revision 1, status `supported`, cue fingerprint `7b4fa620a62fdf1b50210230b7792138f6b38cb6140796ecc1898567924c4d29`.
- Direct application of the installed predicate to repaired revision 2 gives `would_match=true` for the unchanged cues with no environment key. The same domain/artifact/operation cues plus a different environment also give `would_match=true`. Missing domain, missing operation, or changing artifact from CSV to TSV gives `would_match=false`.

The different-environment result describes discoverability only. It does not support the rule in that environment: retrieval exposes the rule, gate rationale, qualifier, falsifier, evidence summary, and counterevidence so the caller can observe the Python 3.11.6 supplied-sample boundary.

## Current refutation dispositions

- `rf-scope` — `accepted`. Removing environment filtering broadens discovery for absent/different environment cues. This is a nonblocking scope limitation because the unchanged retrieved content explicitly restricts semantic support to Python 3.11.6 and the supplied samples. Evidence: `csv-old:ev-1`, `csv-new:ev-1`.
- `rf-strength` — `resolved`. A3 repeats the prior falsifier; old rows and A4 establish only the stated field counts. No generic validation, escaping, dialect, malformed-input, or transfer claim was introduced. Evidence: `csv-new:ev-1`, `csv-old:ev-1`.
- `rf-retrieval-repair` — `resolved`. The unchanged task cues now satisfy all nonempty qualifiers. Domain, artifact, and operation remain mandatory. Actual revision-2 CLI retrieval remains a coordinator completion check. Evidence: `csv-old:ev-1`, `csv-new:ev-1`.

## Earlier blocker disposition

`rv-retrieval-actual-cues` — `resolved` in the frozen repaired candidate. The original predicate produced `would_match=false`; the repaired predicate produces `would_match=true` for the unchanged cue file. This is an observed in-memory predicate result, not a claim that coordinator staging, activation, or live revision-2 retrieval has happened.

## Evidence-class, lineage, and authenticity

The candidate satisfies `scoped_fact`/`supported`: a direct repeatable check establishes the field counts in the declared Python 3.11.6 supplied-fixture environment. It does not transfer beyond that scope. The `correct` action preserves stable ID `museum-csv-field-count`, advances retained revision 1 to revision 2, and retains the fired prior falsifier, source provenance, counterevidence, and alternative explanations.

The source runs, fixture provenance, and `/controlled/seed-*` actors are synthetic scaffolding, not authentic earlier Sage teams. Their attestations were not treated as live independence or semantic proof. Reviewer native actor ID is `/root/live_promotion_reviewer`; effective identity/model/effort, tokens, and money remain unobserved and are `null` in the JSON.

No additional findings remain.

## Coordinator-owned checks still unexecuted

This reviewer did not assemble the complete proposal or mutate the store. Staging, post-stage validation, activation, live revision-2 retrieval with unchanged `inputs/cues.json`, rollback, pointer-restoration validation, retained-history validation, and after-rollback retrieval remain unexecuted. No staged generation ID or manifest hash is yet known.

Writer lease: `RELEASE`.
