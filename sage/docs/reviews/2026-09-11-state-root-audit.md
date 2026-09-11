# Sage runtime-history audit and repair

Completed in the source package and active `/Users/tuananhnguyen/.agents` installation. Both historical runs are now discoverable from `/Users/tuananhnguyen/.codex/sage`, with their original event bytes unchanged. Final verification: 120 automated tests passed, a separate 56-test independent repair check passed, and a live isolated skill-execution test successfully persisted and rediscovered a tiny task. See [independent review](2026-09-11-state-root-independent-review.md), [behavioral verification](2026-09-11-state-root-forward-test.md) and [installed hashes/history](2026-09-11-state-root-install.json).

## Verified issue

The reported discovery failure was real. History existed, but normal operation had no executable root-selection or inventory seam. Promotion could work when given exact source directories; it was not intrinsically a no-op. The documented default could not discover the two reported histories.

Baseline observations on 2026-09-11:

- `/Users/tuananhnguyen/.codex/sage` did not exist before this repair run.
- `reviews/2026-09-11-sage-major-issues/run` validates as terminal `major-issues-review`, 39 events. Its event-log SHA-256 is `826655b2cb33e94696d6fda8cdb52a0d89aab701d3316a00a29f67954b2c164b`.
- `.sage-state/major-issues-fix/run` validates as terminal `major-issues-fix`, 41 events. Its event-log SHA-256 is `f5892f0709bca82d0f6ce62285940ea882bc395e9e37d20716f906b6ad214684`.
- The installed package matched the source baseline. Its receipt contained no runtime-root configuration. The state helper required arbitrary `--run-dir` values; the knowledge helper required a store and already-known source paths.
- `init --state-root ...` failed with exit 2, requiring `--run-dir`. The six initial workflow regression tests all failed against the baseline.

## Audit scope and resulting changes

The root and an independent read-only auditor inspected the active entrypoints, linked references, state and knowledge helpers, lifecycle installer, requirements, architecture, public contracts and tests. Archived implementations and disposable sandbox copies were excluded from product conclusions.

| Gap | Repair and decisive check |
| --- | --- |
| Root configuration existed only as ambiguous prose | Both helpers share `runtime_paths`; precedence is explicit root, `SAGE_STATE_ROOT`, `CODEX_HOME/sage`, then `~/.codex/sage`. Absolute roots eliminate cwd-dependent configuration. `paths` exposes the selection without creating state. |
| New runs could be placed arbitrarily | Normal `init --run-id` creates `ROOT/runs/ID`. All state operations resolve root plus ID. The low-level explicit-directory compatibility path reports that it bypasses discovery. |
| Promotion required already-known source paths | `list-runs` discovers direct canonical and registered history, with bounded log validation, pagination, hashes, eligibility and individual quarantine reasons. |
| Existing scattered history was invisible | `register` binds a valid closed run's ID, absolute path and exact log hash without moving artifacts or rewriting events. Conflicting IDs and changed source bindings reject. |
| Inline tasks could skip recording | The skill now opens a discoverable run for every work invocation, with zero delegation still supported. An explicit user prohibition on persistence wins and is disclosed. |
| Recovery and knowledge paths could diverge | Report/resume use the shared inventory and ID resolution; every knowledge command defaults to the same root's `knowledge` directory. Normal instructions pin the selected root throughout the invocation. |
| Missing knowledge helper could silently skip retrieval | Missing helpers and rejected retrievals are reported failures, distinct from a successful empty-store query. |
| Empty discovery could masquerade as learning `no_change` | Promotion distinguishes `no_sources`, active-only history, quarantine and actual review yielding no reusable candidate; inspected pages and exclusions are reported. |
| Documentation could recreate the defect | Both skill graphs, README, architecture, requirements and public contracts use one linked runtime procedure. Explicit user-authorized history inspection/Sage maintenance is distinguished from automatic task-time learning. |
| State argument errors violated the JSON error contract | State parser errors now return structured exit-2 JSON, as the knowledge parser already did. |
| Staging could bypass inventory quarantine or use changed source bytes | Root-mode proposals require exact selected source hashes and central ID/path bindings, checked before mutation and again before publication. |
| A knowledge namespace symlink could redirect outside the announced root | Shared namespaces and explicit-store leaf types are checked before resolution hides symlinks. |
| Occupied empty canonical IDs and explicit-path metadata disagreed with the contract | Occupied canonical targets reject, and explicit canonical locations receive the same checks and truthful discovery metadata. |
| Snapshot/resume disagreed with frozen assignment-release facts | Projection and resume use the validator's release facts; subsequent handle reuse starts a new assignment normally. |
| Impossible knowledge-helper selections were accepted | Cue shapes, statuses, policy, match uniqueness and generation/status/match consistency now reject impossible records. |

## Verification

The regression suite `sage/tests/test_state_root.py` covers two project directories creating, appending, snapshotting and closing centrally discoverable runs; root precedence; empty read-only roots; visible legacy bypass; invalid and ambiguous targets; duplicate/mismatched IDs; invalid, missing and changed references; pagination; and installed discovery through stage, activate, retrieve, revalidate, rollback, report, resume and uninstall. Synthetic promotion fixtures are test data and do not promote this user's history.

The first complete repaired offline gate passed 114 tests with zero failures, errors or skips. Its retained result is `sage/evaluation/sandboxes/state-root-fix-full/report.json`. The original explicit-store knowledge response shapes remain compatible. The prior missing-store argument test now checks an unknown option because an omitted store intentionally resolves the shared root.

Final gate: `sage/evaluation/sandboxes/state-root-final/report.json`, 120 tests passed. All six findings from the independent frozen-candidate review were independently verified fixed. The installed receipt's 15 file hashes match source, all 24 local reference links resolve, and both historical runs validate by ID through the installed helper. Behavioral test logs also validate under the final tightened state contract. No blocker or major finding remains open.

## Boundaries

Registration is a central reference, not an archival copy: original run directories and external evidence must remain available. Moving or deleting a registered source produces visible quarantine; re-registering a different path does not silently replace its original binding. Canonical new runs are independent of the task repository's location, but externally referenced task artifacts still need retention.

Discovery enumerates direct entry names to paginate and validates only the selected page. It is a point-in-time observation; promotion revalidates sources. The existing single-writer/cooperative integrity model remains, without a physical lease or crash-atomic multi-file transaction. Helpers validate structure, not semantic truth or whether an agent actually followed a prose instruction.

No real knowledge generation is staged or activated by this repair. No claim is made that unrelated home directories contain no other historical runs; recovery scope is the two user-supplied locations.
