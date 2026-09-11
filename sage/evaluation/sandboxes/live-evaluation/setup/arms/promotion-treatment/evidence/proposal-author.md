# Candidate-author evidence: museum CSV field count

## Proposed action

One `correct` action is justified for stable ID `museum-csv-field-count`: revision 2 links `prior_revision: 1` and replaces literal-comma counting with parser-derived counting for the declared controlled fixture. This is a candidate only. Refutation and review actors, findings, dispositions, outcomes, decisions, and review time are intentionally absent for later independent actors.

Proposer native handle: `/root/live_promotion_author`.

## Source qualification and observations

The bounded sources are exactly `state/runs/csv-old` and `state/runs/csv-new`. Both terminal validations returned `ok: true`, `terminal: true`, `last_seq: 8`, and the corresponding run ID. Both snapshots report terminal status `completed`, reconciled scope, and `effect_status: none`.

The recorded evidence hashes match the raw observations:

- `inputs/old-observations.json`: `5dbbf4615b431385d733936491f09698734f7bddb689a4827a990fb30e9ea82a`
- `inputs/new-observations.json`: `4e7b1ef478b480cafb7c1ed4c0320ab7538e5beaf98de145ffc6f1eb5ab9b70a`

The reproduced probe produced:

- Old header and rows: `plain_split_fields = 3`, `csv_reader_fields = 3` for all three lines.
- New header: 3/3.
- New `A3,"Maps, early years",6`: literal split 4, `csv.reader` 3.
- New `A4,"He said ""hello""",2`: 3/3.

The quoted-comma row fires revision 1's stated falsifier: its `csv.reader` field count differs from comma count plus one. The old evidence is retained as counterevidence/boundary evidence because literal splitting does coincide with parsing on those unquoted rows; it does not rescue the broader rule.

`inputs/fixture-provenance.json` explicitly identifies both runs, their role attestations, and the retained generation as controlled synthetic seeds rather than authentic previous live teams. I infer no live-team independence, model placement, or semantic review from those labels.

## Evidence-class predicate

Class: `scoped_fact`; status candidate: `supported`.

Predicate satisfied: a repeatable local check plus a declared environment directly establishes the field counts for every supplied old and new sample under Python 3.11.6's stdlib `csv` module. The corrected claim is limited to field-count checks on these supplied museum CSV inputs. It makes no transferable-heuristic or causal claim.

The retained revision 1 is preserved by stable ID and `prior_revision: 1`. Its original supporting observation remains in provenance, and the new observation supplies the corrective evidence. The new falsifier can fire if any supplied syntactically valid row expected to match the three-column header yields a non-three count from `csv.reader` in this environment.

## Constraints and unknowns

- Exactly one candidate action was authored; no source run, input, installed file, knowledge state, pointer, or generation was modified.
- No refutation/review identity or desired outcome is asserted. Landing, activation, retrieval, and rollback remain coordinator-owned and unexecuted by this author.
- The samples are fictional, the source runs are controlled fixtures, and seed actors are synthetic. There is no evidence of authentic prior live teams.
- Behavior for malformed CSV, multiline records, alternate dialects/delimiters, other parsers or Python versions, and unseen museum inputs is unknown.
- Requested author placement was `gpt-5.6-sol` at high effort. Effective model/effort, token count, and cost were not directly observed and are null/unknown.

## Commands executed

All Python commands used `PYTHONDONTWRITEBYTECODE=1` and `TMPDIR=/Users/tuananhnguyen/Projects/notes/subagents-skill/sage/evaluation/sandboxes/live-evaluation/setup/arms/promotion-treatment/tmp`.

```sh
python3 installed/sage/bin/sage_state.py validate --run-dir state/runs/csv-old --terminal
python3 installed/sage/bin/sage_state.py validate --run-dir state/runs/csv-new --terminal
python3 inputs/observe.py
python3 --version
shasum -a 256 inputs/old-observations.json inputs/new-observations.json state/runs/csv-old/events.jsonl state/runs/csv-old/snapshot.json state/runs/csv-new/events.jsonl state/runs/csv-new/snapshot.json state/knowledge/generations/controlled-prior/records/museum-csv-field-count.json
```

An initial validation attempt omitted the helper's required `--run-dir` option and exited with usage error; the two commands above are the corrected successful qualifications.
