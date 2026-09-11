# Narrow independent routing-evidence recheck

## Reviewer identity and scope

- Native handle: `/root/live_recovery_review` (observed as `running` by an exact scoped native inventory call).
- Requested model/effort: `gpt-5.6-sol` / `xhigh`.
- Observed effective model/effort: `null` / `null` (not exposed).
- Observed token usage: `null` (not exposed).
- Observed money/cost: `null` (not exposed).
- Corrected frozen candidate: `evidence/recovery-assessment-corrected.md`.
- Expected and observed corrected-candidate SHA-256: `3f9bb605067a18a042ec2bc78fef32aa573850d57bd189e1eefd88c8d0aff8cb`.
- Original candidate expected and observed SHA-256: `f5e7409048402fe24c6f8235c9de7b4ea970acd052280408c501e54144069a90`.
- Newly allowed dispatch-observation expected and observed SHA-256: `86dee3f79fbf54f7ab764cfe4daa3432f30c9c48fa090b6787c07a1092e6eca7`.

This recheck is limited to the prior review's one minor routing-evidence finding and its stated falsifiable repair check. I read the original prompt/checks, preserved original review, original and corrected candidates, and the newly allowed dispatch observation completely. I did not read repair rationale/events, coordinator journal, generated scripts/check outputs, evaluator material, or another arm. I wrote only this artifact and did not mutate source state or either candidate.

## Recheck result

### Prior severity: [minor] — original falsifiable repair check passed; the finding does not reproduce in the corrected candidate

Affected acceptance: `live-procedure` (honest routing/usage evidence), with the prior localized `evidence_quality` concern.

Exact evidence:

- The original finding required either an identity-matched dispatch record or an explicit statement that coordinator-requested routing was unknown (`evidence/independent-review.md`, “Finding”).
- `evidence/outer-coordinator-dispatch-observation.json:3-7` identifies its provenance as the outer coordinator's structured observation of its direct spawn request/result, names `/root/live_recovery_treatment`, and records requested model `gpt-6-astra`, effort `high`, and fork `none`.
- `evidence/recovery-assessment-corrected.md:27` names that exact source, handle, model, effort, and fork mode. It separately says the synthetic fixture writer's Astra/high request is not evidence of the live coordinator's request.
- The source labels itself actor-authored and not a raw native transcript (`outer-coordinator-dispatch-observation.json:3`). The corrected candidate preserves that limit and does not treat it as proof of effective identity.
- The dispatch observation records effective model, effective effort, reported tokens, and reported money as null (`outer-coordinator-dispatch-observation.json:18-21`). The corrected candidate preserves all four nulls and makes no cost or savings claim.
- A byte-level comparison found line 27 to be the only changed line. The original candidate remains unchanged at its frozen hash.

Result of the original falsifiable check: **passed**. The repaired text takes option (a): it preserves an allowed record tied to the coordinator's exact identity and matches that record without borrowing the synthetic worker's routing evidence or inventing effective identity/usage. This recheck does not disposition the finding in source state; that remains the coordinator's responsibility.

No new blocker, major, or minor finding was found within this narrow recheck.

## Focused preservation check

The corrected candidate changes only its routing-evidence paragraph, so the prior preservation and source-open conclusions remain textually unchanged. Current non-mutating checks also found:

- The original first 14 authoritative events retain SHA-256 `7371cc980d60749e758329af28d3f0e3227c6d6244c6c6e54edd57fbbee6d29b`, exactly matching the log reviewed previously.
- The original eight-event fixture history remains an exact byte prefix.
- The current snapshot is hash-bound to the current 20-event log and remains nonterminal (`terminal:null`).
- Its export and draft baselines still match the preserved files. The export remains `c309390f0eb4283f38c369a17b36cdb86e29172d3bf25f0fe7123a7822427bfd`; the draft remains `8da84d528ed97d2d43b8470da26b8b3a1294a866bba03d28daf2982e964bbbbd`.

I did not inspect the six later event payloads because repair events/rationale were excluded from this recheck. The permitted structural checks are sufficient to establish that the prior authoritative prefix, byte baselines, snapshot binding, and open source-run conclusion remain intact.

## Concise reproduced commands and outputs

All shell commands used `PYTHONDONTWRITEBYTECODE=1` and `TMPDIR=/Users/tuananhnguyen/Projects/notes/subagents-skill/sage/evaluation/sandboxes/live-evaluation/setup/arms/recovery-treatment/tmp` from the arm root.

Hash check:

```sh
PYTHONDONTWRITEBYTECODE=1 TMPDIR=/Users/tuananhnguyen/Projects/notes/subagents-skill/sage/evaluation/sandboxes/live-evaluation/setup/arms/recovery-treatment/tmp shasum -a 256 evidence/recovery-assessment-corrected.md evidence/recovery-assessment.md evidence/outer-coordinator-dispatch-observation.json evidence/independent-review.md evidence/original-events.jsonl inputs/baseline.json work/export.csv work/export.draft.csv state/runs/catalog-export/events.jsonl state/runs/catalog-export/snapshot.json
```

Exit code: `0`. Exact stdout:

```text
3f9bb605067a18a042ec2bc78fef32aa573850d57bd189e1eefd88c8d0aff8cb  evidence/recovery-assessment-corrected.md
f5e7409048402fe24c6f8235c9de7b4ea970acd052280408c501e54144069a90  evidence/recovery-assessment.md
86dee3f79fbf54f7ab764cfe4daa3432f30c9c48fa090b6787c07a1092e6eca7  evidence/outer-coordinator-dispatch-observation.json
341118f9d55c021e0b69078de144f8108eef104c115c2614b3e7a6cb246844ba  evidence/independent-review.md
453b62cdea9132afe07bf22c6ad39baea3d03cc63f06d3ac46522e8191dbd1d6  evidence/original-events.jsonl
042248522ec784d538787efbcc656d0445579d7dd4a741f566a9723b55bd9904  inputs/baseline.json
c309390f0eb4283f38c369a17b36cdb86e29172d3bf25f0fe7123a7822427bfd  work/export.csv
8da84d528ed97d2d43b8470da26b8b3a1294a866bba03d28daf2982e964bbbbd  work/export.draft.csv
d78487fe428e5b667fbebe10dea4b555b560a735657dc1d8807b49e0507375d7  state/runs/catalog-export/events.jsonl
03b31ee6127fac5f280ab56e7b48ebc7ef3123ec860067b86c5f0a8c35f9a311  state/runs/catalog-export/snapshot.json
```

Candidate comparison:

```sh
PYTHONDONTWRITEBYTECODE=1 TMPDIR=/Users/tuananhnguyen/Projects/notes/subagents-skill/sage/evaluation/sandboxes/live-evaluation/setup/arms/recovery-treatment/tmp diff -u evidence/recovery-assessment.md evidence/recovery-assessment-corrected.md
```

Expected exit code: `1` because one line differs. The substantive exact hunk was:

```diff
@@ -24,7 +24,7 @@
-Known limits: draft origin and historical writer effects unknown; no full native inventory was collected; effective model/effort, token usage and money are null when not exposed. Requested coordinator routing is Astra/high. Independent review is pending at candidate freeze and will be recorded separately with requested versus observed identity. No cost or savings claim is made.
+Known limits: draft origin and historical writer effects unknown; no full native inventory was collected; effective model/effort, token usage and money are null when not exposed. The outer coordinator's structured dispatch observation in `evidence/outer-coordinator-dispatch-observation.json` names `/root/live_recovery_treatment` and records requested model `gpt-6-astra`, effort `high`, and fork `none`. It is an actor-authored observation of the actual dispatch, not a raw native transcript or proof of effective identity. Its effective model, effective effort, reported tokens and reported money are all null. The synthetic fixture writer's separate Astra/high request is not evidence of the live coordinator's request. The initial independent review is preserved in `evidence/independent-review.md`; its minor routing-evidence finding is addressed by this one focused correction and awaits independent recheck. No cost or savings claim is made.
```

Focused machine assertions exited `0`. Exact stdout:

```json
{"changed_line_numbers": [27], "corrected_candidate_sha256": "3f9bb605067a18a042ec2bc78fef32aa573850d57bd189e1eefd88c8d0aff8cb", "current_event_count": 20, "dispatch_identity_matches_candidate": true, "dispatch_nulls_preserved_in_candidate": true, "dispatch_provenance_limit_preserved_in_candidate": true, "first_14_events_sha256": "7371cc980d60749e758329af28d3f0e3227c6d6244c6c6e54edd57fbbee6d29b", "original_8_event_prefix_exact": true, "snapshot_draft_baseline_matches": true, "snapshot_events_hash_matches": true, "snapshot_export_baseline_matches": true, "snapshot_terminal": null}
```

Native identity observation:

```text
list_agents(path_prefix="/root/live_recovery_review")
{"agents":[{"agent_name":"/root/live_recovery_review","agent_status":"running"}]}
```

## Remaining unknowns and limits

- The dispatch observation is an actor-authored structured record, not a raw native transcript. Its `packet_sha256` cannot be recomputed from the allowed sources because the packet itself was not supplied. The corrected candidate discloses the material provenance limit instead of overstating it.
- Effective coordinator and reviewer model/effort remain unobserved; reported tokens and money remain null. Requested routing is not proof of effective routing.
- Draft provenance, historical fixture-writer effects, and full native inventory remain unknown. This focused correction does not change those prior limits.
- Later authoritative event payloads and any coordinator disposition were out of scope. This recheck reports the repair-check result only and does not alter or close source state.

RELEASE: `/root/live_recovery_review` releases its sole writer lease for `evidence/independent-recheck.md`; no further mutation is pending.
