# Light-mode guarantees

Phase 1 is the complete Codex-native Sage workflow. Policy judgments and structured evidence are useful without an external scheduler, but deterministic coordination remains advisory.

| Property | Light-mode status | Honest claim |
| --- | --- | --- |
| explicit activation | native metadata | Codex may invoke Sage only through explicit `$sage` selection when it honors `agents/openai.yaml`. |
| worker effect boundary | brief plus inherited sandbox | The brief limits effects; actual isolation is only as strong as the effective parent sandbox, approvals, and tool surface. |
| one active writer | policy-actor bookkeeping plus native snapshot | Required by admission discipline, counting the root as a writer; no external lease prevents a model from violating it. |
| mutation baseline and review freeze | deterministic hashes plus policy bookkeeping | Hashes prove the captured bytes or tree, while scope completeness and review judgment remain advisory. |
| plan and attempt bounds | immutable artifact plus policy bookkeeping | Rewrites and illegal transitions are rejected by the state command; timing and admission decisions remain root judgments. |
| dependency admission | policy-actor bookkeeping | Advisory; a model could omit or misrecord a gate. |
| fresh child context | capability-dependent | Claimed only when the live start schema accepts and applies an explicit fork control. |
| model and effort | requested value plus observation | Effective identity is `unknown` unless a supported result or event reports it. |
| worker lifecycle | native snapshot | Snapshot-reconcilable where list/inspection is available; a visible transcript is not a replayable lifecycle sensor. |
| root-context threshold | policy always present | Automatic 30-percent detection requires a supported numerator and denominator; explicit handover remains available. |
| run and handoff artifacts | deterministic local tools | Run JSON and mandatory `handoff.json` hashes/bindings are machine-checked; run Markdown and optional `handoff.md` are deterministic projections. Evidence persuasiveness remains policy judgment. |
| current-run facts | append-only command surface | Only allowlisted factual events are accepted and terminal logs freeze; filesystem authority still follows the sandbox. |
| fact privacy and report classification | deterministic validation plus policy judgment | Explicit classification, obvious credential/raw-payload rejection, confidential pointer-only facts, and strictest-class report inheritance are checked; semantic redaction still depends on the policy actor. |
| promoted runtime knowledge | validated index | Active runs can read active indexed records, never raw closed-run logs. No mid-run extraction or consolidation occurs. |
| root-loss recovery | capability-dependent | Unknown starts are reconciled when native evidence proves identity or absence; otherwise pause without blind retry. |
| leases and durable approval transactions | unavailable | Light mode makes no Managed-mode guarantee for external leases, scheduler authority, or approval enforcement. |

Record availability, authority, scope, delivery, durability, and failure behavior for each capability used in a run. Missing evidence narrows the claim; it never becomes a default pass.
