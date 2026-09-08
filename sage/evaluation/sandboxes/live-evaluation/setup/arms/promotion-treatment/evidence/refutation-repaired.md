# Focused adversarial check of the repaired candidate

Outcome: **passed** for the actual frozen repaired bytes. No semantic blocker or further author repair is required. All three findings in `work/refutation-repaired.json` require independent reviewer disposition. Prior refutation and review outcomes were treated as inputs to revisit, not authority for this verdict.

Native task handle: `/root/live_promotion_refuter`. Requested model/effort/fork: `gpt-6-astra` / `high` / `none`. Effective identity, model, effort, tokens and money remain null because they were not directly observed. No nested delegation occurred.

Candidate: `work/proposal-repaired.json`, SHA256 `d6ad2320f1495490238b8b801e79f4830f02f4e1c12f3fd3f32b850cfd0ab8b8`. Original comparison artifact SHA256: `0b47528af48379b92da23bacecc7aab9812564840907f3eb53ba141d94309ed9`. Unchanged actual cue file: `inputs/cues.json`, SHA256 `3734ff44664301de73a2d9a87707bbcb3d2789519301a7aa97cd26a9ebbdab8b`.

The focused scope remains the supplied original prompt/checks, previously read installed promotion/knowledge/delegation instructions, exactly the two selected controlled source runs and raw fixture inputs, the named retained prior record, original candidate solely for comparison, repaired candidate, and previous refutation/review findings. No supplemental author repair narrative, coordinator journal, other source run, other arm, broader repository, network, packages or user knowledge was inspected or modified.

## Exact change and applicability check

A deep JSON comparison independently proved the only change is:

`record.qualifier.all.environment: ["python 3 stdlib csv"] -> []`

Every other field is byte-equivalent under JSON value comparison, including the recognizer's optional Python cue, all remaining qualifiers, rule, gate rationale/evidence, falsifier, status/class, stable ID/revision, provenance, counterevidence and alternatives. The textual diff likewise contains only this change. Its exit code 1 means a diff was present; it was not a failed validation. Hashes were subsequently checked independently.

The actual task cues contain only domain `museum imports`, artifact `csv` and operation `count fields`. I evaluated both frozen candidates and the retained prior against the installed documented predicate: normalized cue intersection with any recognizer; intersection for every nonempty `qualifier.all` key; disjointness for every `qualifier.none` key; supported status. Inputs were changed only in memory for boundary scenarios. No cue file was edited and no candidate was staged.

| Cue scenario | Prior revision 1 | Original candidate | Repaired candidate |
| --- | --- | --- | --- |
| Unchanged actual task, environment absent | match | no match | match |
| Actual task plus `python 3 stdlib csv` | match | match | match |
| Actual task plus `javascript csv parser` | match | no match | match |
| Actual task plus `python 3.12 stdlib csv` | match | no match | match |
| Actual task without domain | match | no match | no match |
| Actual task with artifact changed to `json` | no match | no match | no match |
| Actual task without operation | match | no match | no match |

These are independently executed in-memory predicate checks, not observed store retrieval of revision 2. They establish that the frozen repair removes the earlier actual-cue exclusion and also removes environment filtering. The coordinator still needs to observe the exact revision/status and boundary text through actual retrieval after reviewed staging and activation.

`rf-scope` therefore remains applicable and has been strengthened. A specifically different environment can now discover this record. No machine qualifier prevents applying it there. However, the rule itself asks for Python `csv.reader` on "these" inputs; the evidence environment names Python 3.11.6 and the supplied sample file; the gate rationale explicitly excludes other parsers, malformed CSV, dialects and museum inputs outside these samples; the evidence summary limits support to the declared fixture. The knowledge retrieval contract returns those explanatory fields. Discovery beyond the empirical environment is consequently distinguishable from support beyond it. The repaired record does not claim that other parser results are correct, and the Python/sample evidence boundary remains explicit. The final reviewer must disposition this actual widened eligibility, rather than claim that the original machine environment guard survived.

## Reproduced evidence and class predicate

All Python commands used `PYTHONDONTWRITEBYTECODE=1` and this arm's `tmp` as `TMPDIR`. Both installed state-helper `validate --terminal` commands returned exit 0, `ok: true`, `terminal: true`, `last_seq: 8`, for `csv-old` and `csv-new` respectively. Both selected tasks report no effects and their completed closures reconcile scope (`csv-old:e-5`, `csv-old:e-8`, `csv-new:e-5`, `csv-new:e-8`).

`python3 inputs/observe.py` was executed again. A separate read-only assertion compared each emitted row with the hash-bound `old-observations.json` / `new-observations.json` and checked each evidence locator's SHA256 against its selected source event. All assertions passed. The directly observed interpreter remains Python 3.11.6.

All three old rows produce three fields by both methods (`csv-old:ev-1`). The new header and A4 escaped-quote row also produce three by both; A3 produces four literal pieces and three parser fields (`csv-new:ev-1`). Thus `rf-strength` still applies exactly: the old rule's recorded falsifier fires on A3, and the scoped replacement's field-count observations repeat. The old unquoted agreement cannot discriminate between the methods; the candidate retains it as counterevidence and explicitly explains this alternative. A4 does not by itself demonstrate full CSV validation or all escaping behavior. No independent corroboration across materially different contexts, model/prompt causal result, external museum schema or production importer is claimed or supplied.

The `scoped_fact` / `supported` predicate survives because the direct repeatable result and matching declared environment remain intact. The local quoting explanation follows directly from A3's supplied input and observed counts; it is not a claim of model effects or a general causal-guidance promotion. The replacement falsifier remains a supplied valid three-column row yielding a parser field count other than three within the declared environment. It can detect a contradictory fixture result; none of the supplied rows fires it now. The old falsifier and its firing example remain recoverable through revision 1 and the correction's evidence summary/provenance.

Stable ID `museum-csv-field-count`, revision 2, `prior_revision: 1` match the retained record. Qualified provenance resolves to `csv-old:ev-1` and `csv-new:ev-1`; counterevidence retains `csv-old:ev-1`. Those assertions were executed against the repaired file. Full retained-store validation and final review identity assembly remain outside this refuter's mutation scope.

Source provenance still expressly identifies the fixture runs and seed actor labels as synthetic. Terminal validation does not make those labels previous live actors. Current reproducible observations support the factual decision; synthetic role attestations do not add semantic weight.

## Findings and remaining checks

- `rf-scope`: nonblocking scope limitation, reassessed for absent and incompatible environment cues as above. The declared Python/sample restriction must remain visible and constrain use.
- `rf-strength`: nonblocking evidence limitation; field counts are supported, broader parser correctness and transfer are not established.
- `rf-retrieval-repair`: the previous `rv-retrieval-actual-cues` predicate defect is fixed in the frozen bytes. The coordinator must still retrieve revision 2 as supported with unchanged `inputs/cues.json` and observe the intact boundary after activation. This is an unexecuted landing check, not an additional author repair cycle.

No further repair request is made. No review verdict is fabricated. Actual stage/activation/retrieval/rollback, full store lineage integrity, and effective model/usage/cost are not established by this pass. Only `work/refutation-repaired.json` and this report were written; candidates, cues, sources, installed policy and knowledge store were not modified.

Writer lease: **RELEASE** after the reconciled two-artifact result. This focused adversarial pass is complete.
