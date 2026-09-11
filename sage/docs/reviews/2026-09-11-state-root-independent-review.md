# Independent review and repair record

Reviewer: `/root/review`, requested Sol/xhigh with fresh artifact/request context; a separate standards actor assisted its read-only review. Effective native models/efforts were not reported. The reviewer used a frozen source/installed package and isolated probes. It did not repair its findings.

## Initial findings

| Finding | Independent reproduction | Repair |
| --- | --- | --- |
| Major: staging bypassed registered-history quarantine | A changed but terminal-valid source was quarantined by inventory but accepted by root-mode staging | Root-mode proposals bind exact selected log hashes and resolve source IDs through the same central namespace and registered bindings; checks repeat before publication |
| Major: symlinked knowledge namespace escaped the stated root | `ROOT/knowledge` pointed outside the root; validation succeeded and reported the advertised path | Namespace type is checked before path resolution; explicit-store leaf symlinks also reject |
| Major: occupied empty canonical directory was claimed | Precreated empty `runs/ID` was accepted as new | Any occupied canonical target rejects, including empty directories, files and symlinks |
| Major: released-agent projection drifted | Late missing/unknown observation rewrote the snapshot after a completed/reconciled assignment had released | Projection uses the same release facts as validation; resume omits released assignments until a new request |
| Major: impossible knowledge selection was persisted | Generation `none` and status `matched` with an invented match status passed validation | Cue types, match statuses/policy, unique IDs, generation/status/match consistency and unchanged-selection references are validated |
| Minor: explicit canonical initialization misreported discovery | Explicit `--run-dir ROOT/runs/ID` returned false while inventory discovered it | Exact canonical locations receive canonical collision checks and truthful metadata |

The root reproduced the defects with failing public-CLI regressions before applying the repairs. The resulting 15 runtime tests pass. The complete offline suite passed 120 tests after the repair wave; the final gate and focused independent recheck are recorded in the central run.

Root disposition: all six findings are **fixed**, based on the focused independent recheck of frozen `/private/tmp/sage-runtime-repaired.5ln1XI`. The reviewer passed all 56 state/knowledge tests, including 15 runtime regressions, and independently verified the following:

- Missing/stale source hashes reject before publication. A modified registered log also rejects when its proposal supplies the new hash. Unregistered external sources reject in root mode. Explicit-store compatibility and optional hash enforcement both work. A valid installed canonical-source proposal stages, activates and retrieves successfully.
- Symlinked knowledge roots and occupied canonical targets reject while preserving external targets and existing contents.
- Released assignments retain completed/reconciled projection, resume emits no stale observation, and subsequent handle reuse correctly projects the new task.
- Invalid knowledge selections reject; genuine no-match, matched and unchanged selections succeed.
- Explicit canonical initialization reports discovery accurately.

The reviewer found no material defect introduced by the repairs. All 15 frozen installed receipt entries matched source and recorded hashes. Manual probe evidence is under `/private/tmp/sage-review-repair-probe/manual`. The final root-owned offline gate passed 120 tests with no failures, errors or skips, at `sage/evaluation/sandboxes/state-root-final/report.json`.

A standards-side comment concerned the deliberately reduced review fixture omitting `evaluation/run_verification.py`; it was not a product omission. The real repository entrypoint exists and ran the complete 120-test gate. No change to that entrypoint was required.

The initial reviewer also validated both historical logs, registered them into a disposable root, checked pagination and unchanged hashes, and verified all 15 installed receipt entries and the complete relative skill-link graph. No actual user history or active knowledge generation was mutated by the reviewer.
