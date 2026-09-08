# Independent adversarial pass

Outcome: **passed**. The proposed stable-ID correction survives this bounded challenge. This does not approve the retained comma-count rule: the new A3 row fires that rule's falsifier. No semantic blocker or required repair was found. The reviewer must independently disposition both findings in `work/refutation.json`.

Native task handle: `/root/live_promotion_refuter`, as delivered in the native task envelope. Requested placement: `gpt-6-astra`, `high`, fresh (`none`) fork. Effective model/effort, tokens and money are unobserved and recorded as null. No nested delegation occurred.

Frozen candidate: `work/proposal-author.json`, SHA256 `0b47528af48379b92da23bacecc7aab9812564840907f3eb53ba141d94309ed9`. The hash was independently checked before and after analytical checks; the candidate was not modified. Inputs were the original prompt and checks, installed promotion/knowledge/delegation instructions, raw fixture provenance/samples/probe/observations, exactly `csv-old` and `csv-new`, the named retained revision-1 record and the frozen candidate. No builder narrative, coordinator journal, other arm, other run, network or package source was used.

## Observed checks

All Python commands ran with `PYTHONDONTWRITEBYTECODE=1` and `TMPDIR` set to this arm's `tmp`. Commands were run from the arm root.

- `python3 installed/sage/bin/sage_state.py validate --run-dir <ARM_ROOT>/state/runs/csv-old --terminal`: exit 0, `{"last_seq":8,"ok":true,"run_id":"csv-old","terminal":true}`.
- Equivalent terminal validation for `csv-new`: exit 0, last sequence 8 and terminal true.
- Both logs close as `completed`, with `scope_reconciled: true`; each sole task has `effect_status: none` (`csv-old:e-5`, `csv-old:e-8`, `csv-new:e-5`, `csv-new:e-8`). These facts establish valid controlled terminal fixtures, not historical live-team authenticity.
- `python3 inputs/observe.py`: exit 0. A separate read-only assertion compared every emitted old/new row to the respective hash-bound observations and to the supplied sample lines; every comparison passed (`csv-old:ev-1`, `csv-new:ev-1`).
- Actual interpreter: Python `3.11.6 (v3.11.6:8b6ee5ba3b, Oct 2 2023, 11:18:21)`, Clang 13.0.0. This matches the declared environment.
- The record ID remains `museum-csv-field-count`, revision becomes 2 and `prior_revision` is 1, matching the supplied retained revision. This pass did not mutate or validate the whole knowledge store; the coordinator must validate all retained lineage before staging.

The reproduced counts are:

| Supplied row | Literal split | csv.reader |
| --- | ---: | ---: |
| Old header | 3 | 3 |
| A1 | 3 | 3 |
| A2 | 3 | 3 |
| New header | 3 | 3 |
| A3 with quoted comma | 4 | 3 |
| A4 with escaped quote | 3 | 3 |

Direct parsing of the supplied A3 line produced `['A3', 'Maps, early years', '6']`; A4 produced `['A4', 'He said "hello"', '2']`. These observations support the field-count claim in this fixture. The header and supplied row forms support the stated three-column expectation; no external museum schema or production importer was inspected.

Hash checks resolved the selected evidence to its logged bytes:

| Path | SHA256 |
| --- | --- |
| `state/runs/csv-old/events.jsonl` | `f1794020c3650775d3d87b1ce6dcd288be75181fb74f44a2aeedcfacaa68943d` |
| `state/runs/csv-new/events.jsonl` | `70511264eee2e393953fc2fccd5749c7d600dc003816d0ba156d63b69921aa80` |
| `inputs/old-observations.json` | `5dbbf4615b431385d733936491f09698734f7bddb689a4827a990fb30e9ea82a` |
| `inputs/new-observations.json` | `4e7b1ef478b480cafb7c1ed4c0320ab7538e5beaf98de145ffc6f1eb5ab9b70a` |

The event hashes match the snapshots, and observation hashes match the `ev-1` evidence payloads. Candidate provenance and counterevidence refer to those actual selected IDs. No source role label is treated as a live actor.

## Challenge and findings

`rf-scope` is a nonblocking boundary finding. The machine qualifier requires museum imports, CSV, Python 3 stdlib CSV and field counting, but does not itself require exact sample identity or version. Thus retrieval eligibility is broader than the empirical scope. The candidate's gate rationale explicitly excludes museum inputs outside these samples, other parsers, malformed CSV and dialects; its gate environment names the actual sample file and Python version. Its rule says "these museum CSV inputs" and its evidence summary repeats the fixture boundary. Since retrieval includes this explanatory material, the current supported scoped fact is defensible. Review must preserve and disposition that restriction; these two sources cannot justify widening it. This is not a claim that unseen CSV inputs fail.

`rf-strength` is a nonblocking inference finding. Old unquoted rows fit both methods and therefore cannot establish the old universal museum-row rule. The candidate retains that evidence as counterevidence and explains its lack of discrimination. A3 contains a literal comma within the second parsed field, which directly explains the extra literal-split piece in this observed row; no prompt/model change is being claimed as a causal factor. This local observation is compatible with the scoped-fact class. It is not controlled cross-context transfer evidence, and no such predicate is asserted. A4's count agreement does not establish full parsing correctness or error detection; the proposed rule is bounded to field counting.

The old falsifier is preserved in retained revision 1 and its firing example is explicitly preserved in the correction's evidence summary and source provenance. The replacement falsifier can fire if a supplied syntactically valid three-column row returns a different parser count under the declared environment. All current supplied rows were checked and do not fire it. Immutable sample scope makes this a regression-style falsifier, not evidence for an unrestricted parser recommendation.

The supplied provenance expressly calls earlier completion and seed role attestations synthetic, and the proposal makes no authenticity claim about them. The author artifact's absent refutation/reviewer fields are expected at this phase; this pass neither fabricates a reviewer nor supplies a review decision. Full proposal schema assembly, independent review, final retained-history validation, expected-pointer checks, retrieval, activation and rollback remain the coordinator/reviewer's work.

## Completion and limits

Only `work/refutation.json` and this report were written. Candidate, source runs, observations, installed policy and knowledge store were left unchanged. Required falsifiable repair checks: none for this frozen candidate; review checks for both nonblocking findings are recorded in JSON. The passed outcome is conditional on retaining the already-declared scope, and is not a claim that landing or rollback has occurred.

Writer lease: **RELEASE** after the reconciled two-artifact result. Stop after this single adversarial pass.
