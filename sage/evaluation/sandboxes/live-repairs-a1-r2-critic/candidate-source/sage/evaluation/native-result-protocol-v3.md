# Native scored-result protocol v3

This successor result encoding applies when a paired arm runs through native Codex collaboration. It does not change the frozen v2 protocol, manifest, rubric, cases, scores, or acceptance criteria. A historical v2 result adapted into this shape is an **informed diagnostic**, never a pristine trial pass or a retroactive v2 pass.

Validate it through the public CLI:

```text
python3 sage/evaluation/pairing.py validate-native RESULTS_V3.json --manifest FROZEN_MANIFEST.json
```

The result and each entry in its `pairs` array are JSON objects. It has `schema_version: "sage-live-native-scored-results-v3"`, the original `frozen_manifest_sha256`, and the same ordered pair/arm, routing, check, score, scorer, and operational fields as v2. Every arm and its `execution` value are also JSON objects. `execution.run_id`, `execution.started_at`, and `execution.finished_at` are nonblank JSON strings; this structural validator does not parse timestamp syntax or order. Each arm replaces v2 `execution.status` and `execution.exit_code` with:

```json
{
  "mode": "native_collaboration",
  "run_id": "/root/worker",
  "started_at": "2026-09-08T00:00:00Z",
  "finished_at": "2026-09-08T00:01:00Z",
  "completion": {
    "lifecycle": "completed",
    "native_exit_code": null,
    "evidence_refs": ["outer-lifecycle"],
    "exit_evidence_refs": []
  },
  "commands": [
    {"id": "verification", "exit_code": 0, "evidence_refs": ["verification-output"]}
  ],
  "evidence": []
}
```

`completion.evidence_refs` must bind one or more `native_observation` evidence entries with explicit provenance. The structural declaration for native completion is `lifecycle: completed`; a different declaration, absent reference, or reference to another evidence kind is rejected. `native_exit_code` is null when the native surface exposes no OS exit, and then `exit_evidence_refs` is empty. A native integer exit is accepted structurally only with bound `native_observation` exit evidence. It is never borrowed from a verifier or other subprocess.

Actual subprocess results live only in `commands`, where each entry has its own integer `exit_code` and bound evidence. A `journal` is explicitly authored evidence with provenance; it is not a raw transcript and cannot prove native lifecycle completion. Every arm retains an `artifact`, `journal`, and `native_observation`. Hash, frozen identity, routing, checks, scoring, and operational-reference validation remain in force.

The validator proves structural and hash binding. The independent evaluator remains responsible for authenticity, behavioral independence, evidence meaning, and the unchanged acceptance judgments.
