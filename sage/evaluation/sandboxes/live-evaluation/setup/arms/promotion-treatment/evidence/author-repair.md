# Candidate-author focused repair

## Decision

The single requested repair is justified. `work/proposal-repaired.json` preserves the `correct` action, proposer, source runs, stable ID `museum-csv-field-count`, revision `2`, `prior_revision: 1`, status, evidence class, rule, recognizer, every other qualifier, falsifier, provenance, counterevidence, alternative explanations, evidence summary, and creation time. It clears only `record.qualifier.all.environment`.

This repaired artifact remains a candidate. It contains no refutation or review actor, finding, disposition, outcome, decision, or review timestamp. The earlier passed refutation and failed review do not transfer to the changed bytes; the repaired candidate requires fresh independent review.

Native author handle: `/root/live_promotion_author`. Requested original routing was `gpt-5.6-sol` at high effort. This follow-up establishes neither effective placement nor usage: effective identity, model, effort, tokens, and money are null/unobserved.

## Exact diff and hashes

The semantic JSON diff from the frozen candidate is exactly:

```json
[
  [
    "/record/qualifier/all/environment",
    ["python 3 stdlib csv"],
    []
  ]
]
```

- Frozen `work/proposal-author.json` before repair: `0b47528af48379b92da23bacecc7aab9812564840907f3eb53ba141d94309ed9`
- Repaired `work/proposal-repaired.json`: `d6ad2320f1495490238b8b801e79f4830f02f4e1c12f3fd3f32b850cfd0ab8b8`
- Reviewed `work/review.json`: `2bcde4320c13d96ed521c5f2e36377c0feee44406ee932cf29d73838e02517a5`
- Unchanged actual-task `inputs/cues.json`: `3734ff44664301de73a2d9a87707bbcb3d2789519301a7aa97cd26a9ebbdab8b`

The frozen original candidate remained byte-identical to its supplied hash.

## Reproduced observations and retrieval predicate

Both bounded source runs terminal-validated again:

- `csv-old`: `ok=true`, `terminal=true`, `last_seq=8`
- `csv-new`: `ok=true`, `terminal=true`, `last_seq=8`

The local probe again produced three fields from `csv.reader` for every supplied line. Literal splitting also produced three for the old header and rows, the new header, and the new escaped-quote row. For `A3,"Maps, early years",6`, literal splitting produced four pieces while `csv.reader` produced the expected three.

The unchanged actual-task cues contain `domain=["museum imports"]`, `artifact=["csv"]`, and `operation=["count fields"]`, with no environment cue. A direct implementation of the documented retrieval predicate observed:

- Before repair: recognizer intersections on domain, artifact, and operation; `qualifier.all.environment=false`; `would_match=false`.
- After clearing only the environment qualifier: the same recognizer intersections; all remaining `qualifier.all` and `qualifier.none` checks true; `would_match=true`.

## Evidence boundary and scope consequence

The repair changes routing eligibility, not the evidence claim. Python 3.11.6 and the supplied controlled fictional museum samples remain explicit in `gate_evidence.environment`, `gate_evidence.repeatable_check`, `gate_rationale`, `rule`, `evidence_summary`, and `falsifier`. Mandatory domain, artifact, and operation qualifiers remain intact. The source fixtures and seed actors remain synthetic scaffolding, not evidence of prior live-team independence.

Clearing the environment qualifier means the record can be surfaced when the environment cue is absent, as in the actual task. It can also be surfaced when a different environment cue is present if domain/artifact/operation match. That is a discoverability consequence, not support for transfer: the returned record must still be judged against its explicit Python 3.11.6/supplied-sample boundary. No evidence supports alternate parsers, Python versions, CSV dialects, malformed or multiline data, or unseen museum inputs.

This consequence is not an unresolved semantic blocker for the repaired candidate because the rule itself prescribes Python `csv.reader`, the exact actual task supplies no conflicting environment, and the scoped-fact boundary remains visible in all application-bearing text. Fresh review must nevertheless verify that this distinction between retrieval and applicability is acceptable.

## Falsifiable fix check

The author-level check passes if the unchanged `inputs/cues.json` yields `would_match=true` under the documented predicate after clearing only `record.qualifier.all.environment`; it yielded true. It fails if the predicate returns false, any other candidate field changes, or the Python 3.11.6/supplied-sample limitation disappears.

After fresh independent review and coordinator-owned staging, the decisive end-to-end check is:

```sh
python3 installed/sage/bin/sage_knowledge.py retrieve --store-dir state/knowledge --cues inputs/cues.json --limit 10
```

It must return `museum-csv-field-count` revision `2`, status `supported`, and expose the supplied-sample/Python boundary. `no_match`, a different revision/status, or loss of that boundary falsifies the repair. This author did not stage, activate, retrieve from a staged generation, rollback, or modify the store.

## Commands observed

Every shell session exported:

```sh
export PYTHONDONTWRITEBYTECODE=1 TMPDIR=/Users/tuananhnguyen/Projects/notes/subagents-skill/sage/evaluation/sandboxes/live-evaluation/setup/arms/promotion-treatment/tmp
```

The substantive commands were:

```sh
python3 installed/sage/bin/sage_state.py validate --run-dir state/runs/csv-old --terminal
python3 installed/sage/bin/sage_state.py validate --run-dir state/runs/csv-new --terminal
python3 inputs/observe.py
python3 -m json.tool work/proposal-repaired.json
shasum -a 256 work/proposal-author.json work/proposal-repaired.json work/review.json inputs/cues.json
```

The predicate check loaded the frozen proposal and unchanged cues with Python's stdlib `json`, normalized cue values using whitespace collapse plus `casefold`, evaluated recognizer intersection and every `qualifier.all`/`qualifier.none` key before and after an in-memory copy cleared the environment array, and printed both results. A separate recursive JSON comparison reported only the path shown in the exact diff above.

## Remaining findings

- Fresh independent refutation/review of the repaired bytes is outstanding; prior outcomes do not transfer.
- End-to-end staged retrieval, activation, rollback, pointer restoration, retained-history validation, and reporting remain coordinator-owned and unexecuted here.
- Retrieval without an environment gate can surface the candidate in a differently named environment; the explicit scoped-fact text must govern application.
