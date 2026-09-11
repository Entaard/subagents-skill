# Knowledge CLI and proposal schema

Read when retrieving, drafting, staging, activating, validating, or rolling back knowledge. Resolve and pin `ROOT` using the shared [runtime procedure](../../sage/references/runtime.md). CLI success emits one JSON object and exits 0; contract/data rejection emits `{ok:false,code,message}` to stderr and exits 2; unexpected I/O exits 3. JSON is strict UTF-8 with duplicate keys and non-finite numbers rejected.

## Commands and store

```text
python3 SAGE_KNOWLEDGE validate --state-root ROOT
python3 SAGE_KNOWLEDGE retrieve --state-root ROOT --cues CUES_JSON --limit N
python3 SAGE_KNOWLEDGE revalidate --state-root ROOT --previous PREVIOUS_JSON --cues CUES_JSON
python3 SAGE_KNOWLEDGE stage --state-root ROOT --proposal PROPOSAL_JSON --generation-id ID --expected-current ID_OR_NONE
python3 SAGE_KNOWLEDGE activate --state-root ROOT --generation-id ID --expected-current ID_OR_NONE
python3 SAGE_KNOWLEDGE rollback --state-root ROOT --generation-id PRIOR_ID --expected-current CURRENT_ID
```

`STORE/current.json` points to one immutable `STORE/generations/<id>` directory. The real generation ID `none` is reserved: a truly absent pointer is the valid empty state, while a dangling pointer symlink is invalid. Every manifest binds its staged parent, exact sorted file paths/hashes, and proposer/refuter/reviewer identities. Validation rejects extra paths (including empty directories), symlinks, partial generations, bad hashes, dangling/cyclic parents, duplicate stable IDs, and conflicting retained `(id,revision)` bytes.

Unpublished work lives separately in `STORE/.staging/stage-<8-character-token>/`. Partial regular JSON files and the helper's atomic-write scratch files may remain there after abrupt termination. Validation checks recognized path shapes and rejects symlinks, special files, and unknown paths, while committed generations still receive full content and lineage validation. Staging names identify scratch format, not proof of ownership or permission to delete it. Both parents share a filesystem and are fsynced after publication by rename. Existing stores without `.staging` remain valid.

`STORE` is `ROOT/knowledge`. Omitting the root uses the shared resolver. An explicit `--store-dir STORE` is retained for legacy or isolated stores and is mutually exclusive with `--state-root`; its existing response shape is preserved. Root-based commands also return the resolved `store_dir`.

## Retrieval

A cue file has these array keys; omitted keys become empty arrays. Values are Unicode-NFC, whitespace-normalized, case-folded, deduplicated, and sorted. The optional boolean changes retrieval policy and is included in the fingerprint.

```json
{"task":["repository repair"],"domain":["software"],"artifact":["jsonl state"],"environment":["python 3.11"],"risk":["corrupt projection"],"operation":["resume"],"failure":["stale snapshot"],"include_non_supported":false}
```

A recognizer matches when any cue value intersects. Every nonempty `qualifier.all` key must intersect; every `qualifier.none` key must remain disjoint. Results are ordered by intersection count, status, stable ID, and revision, then bounded by `--limit` (1–100). Ordinary retrieval returns `supported`; explicit non-supported retrieval may also return `provisional` and `contested`. `refuted` and `retired` never return.

The result is `{generation_id,cue_fingerprint,retrieval_status,matches}`. Empty storage returns `generation_id: "none"`, `no_match`, and `[]`. Each match includes exact ID/revision/status/reason plus evidence class, gate rationale, rule, qualifier, falsifier, evidence summary, and counterevidence—enough to judge application without loading raw runs.

`revalidate` accepts an array of at most 128 distinct `{id,revision,generation_id}` prior selections (positive revisions and real generation IDs). It reads only the validated active generation and returns `{generation_id,manifest_sha256,cue_fingerprint,diagnostics}`. Each diagnostic preserves the supplied identity and reports `current_revision`, `current_status`, `qualifier`, `eligible`, `diagnostic`, and `reason`; present records also report recognizer and qualifier matches. Status diagnostics (`refuted`, `retired`, `contested`, `provisional`) take precedence over scope mismatch, then `out_of_scope`, then `revised` or `unchanged_applicable`. Absent IDs return `not_present_in_active_generation`. Revision changes in either direction are valid diagnostics. This uncached channel is independent of ranking and never emits usable `matches`; supplied prior identities are caller observations, not authenticated historical application. See main Sage's [revalidation procedure](../../sage/references/knowledge.md) for cumulative inventory, batching, evidence and decision review.

## Complete proposal

Replace the absolute run path, log hash and evidence IDs with references from validated selected runs. Root-mode staging requires `source_hashes` to map every selected run ID to its exact `events_sha256` from discovery; the zeros below are a placeholder to replace. It also resolves each ID through the central namespace and registered hash binding. All bindings are checked before mutation and again before publishing a generation. Explicit legacy `--store-dir` staging may omit the map for backward compatibility; when supplied, the hashes are enforced there too. Actor values are the opaque native IDs returned by live collaboration; they are not Sage artifact IDs.

```json
{
  "action": "create",
  "proposer": "/root/candidate-author",
  "reviewer": "/root/reviewer",
  "source_runs": ["/absolute/codex-state/sage/runs/run-1"],
  "source_hashes": {"run-1": "0000000000000000000000000000000000000000000000000000000000000000"},
  "record": {
    "v": 1,
    "id": "validate-log-before-snapshot",
    "revision": 1,
    "prior_revision": null,
    "status": "supported",
    "evidence_class": "scoped_fact",
    "gate_rationale": "A repeatable check establishes this ordering in the declared fixture environment.",
    "gate_evidence": {"repeatable_check": "python3 -m unittest test_state_snapshot", "environment": "Python 3.11 fixture sandbox"},
    "rule": "Validate the authoritative event log before regenerating its snapshot.",
    "recognizer": {"task": [], "domain": [], "artifact": ["jsonl state"], "environment": [], "risk": ["corrupt projection"], "operation": ["resume"], "failure": ["stale snapshot"]},
    "qualifier": {
      "all": {"task": [], "domain": [], "artifact": [], "environment": [], "risk": [], "operation": ["resume"], "failure": []},
      "none": {"task": [], "domain": [], "artifact": [], "environment": ["remote managed authority"], "risk": [], "operation": [], "failure": []}
    },
    "falsifier": "A corrupt authoritative log safely regenerates a valid snapshot.",
    "evidence_summary": "The repeatable fixture rejects the corrupt log and preserves the prior projection.",
    "provenance": [{"run_id": "run-1", "locator": "events.jsonl#e-6"}],
    "alternative_explanations": [],
    "counterevidence": [],
    "refutation": {"actor": "/root/refuter", "outcome": "passed", "findings": [], "evidence": ["run-1:e-6"]},
    "review": {"actor": "/root/reviewer", "outcome": "passed", "dispositions": [], "gate_decision": "supported"},
    "created_at": "2026-09-08T00:00:00Z",
    "reviewed_at": "2026-09-08T00:10:00Z"
  }
}
```

All listed top-level and record fields are required. Record status is `provisional`, `supported`, `contested`, `refuted`, or `retired`; evidence class is `scoped_fact`, `transferable_heuristic`, or `causal_guidance`. Revision 1 has null `prior_revision`; later revisions name the immediately preceding retained revision. Creation and review timestamps are UTC instants compared across every accepted fractional digit, with trailing zeros equivalent; review cannot precede creation.

Supported gate shapes, in class order, are:

```jsonl
{"repeatable_check":"COMMAND","environment":"DECLARED ENVIRONMENT"}
{"contexts":["material context A","material context B"],"corroboration":["run-1:e-6"],"confounder_dispositions":["DISPOSITION"],"counterexample_dispositions":["DISPOSITION"]}
{"method":"controlled","evidence":["run-1:e-6"],"alternative_cause_dispositions":["DISPOSITION"]}
```

The transferable shape may use nonempty `comparison` instead of or alongside `corroboration`. Causal `method` is `controlled`, `counterfactual`, or `direct_mechanism`. The helper checks shape and references, not whether contexts are materially different or causality is real.

A refutation finding is `{"id":"rf-1","summary":"...","evidence":["run-1:e-6"]}`. Review must contain exactly one disposition per finding: `{"finding_id":"rf-1","disposition":"resolved|accepted|rejected","rationale":"...","evidence":["run-1:e-6"]}`. Any action that can land requires passed refutation and review. `passed` describes the proposed action surviving challenge.

For `correct`, `contest`, or `refute`, preserve counterevidence and use the next retained revision. `contest` sets `contested`; `refute` sets `refuted`. An existing record enters `retired` only through `retire`, which adds `retirement_basis` (`explicit_decision`, `superseded`, or `scope_obsolete`) plus `retirement_reason` to `review`. Create may import a new historical status, including retired, at revision 1; it does not mutate an existing ID.

Every provenance item names a selected run and resolves to a bare event/evidence ID, a documented local `events.jsonl#ID`, or the exact hash-bound external locator recorded there. Qualified evidence uses `run-id:event-or-evidence-id` or `run-id:exact-external-locator`. A URI fragment never aliases a local ID. Refutation, finding, disposition, counterevidence, supported comparison/corroboration, and causal references must resolve. Missing source evidence fails before store mutation.
