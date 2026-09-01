# Baseline-to-contract deltas

Phase 0 leaves the existing distribution production-capable and unchanged. The new contracts intentionally describe several later-mode behaviors that the baseline does not yet implement. These are migration obligations, not claims about current behavior.

| Area | Baseline behavior at `6b657a99b799a93dab1897b349bd32c53b223190` | Phase 0 contract | First implementation phase |
| --- | --- | --- | --- |
| Runtime memory reads | Step 2 reads the journal tail after the last promotion mark, which can contain prior closed-run lines used for same-shape pricing. | Closed-run logs are promotion input only; an active run reads promoted knowledge plus its own state for coordination/recovery. | Phase 1 Light skill |
| Promotion destination | One promotion pass writes the source template and lands copies into the installed tree. | Installed-only overlay is the default; explicit global promotion writes source only and asks the user to install later. | Phase 1 promotion workflow |
| Run authority | One Markdown ledger is the durable behavioral source and the existing linter checks a subset of its integrity. | Structured artifact v1 is authoritative; Markdown is a disposable projection. | Phase 1 artifact writer/renderer |
| Lifecycle receipt | Current scripts use manifests, ownership markers, backups, and cautious removal, but not the complete receipt and recovery journal in the new schema. | One universal receipt covers distribution, structured config, runtime data, backups, preservation, and interrupted operations. | Phase 1 Light lifecycle, extended by later Managed support |
| Runtime authority | The baseline parent model owns bookkeeping; guards and probes are host-specific and partly advisory. | Managed authority uses authenticated role endpoints and one deterministic state owner; Light mode remains advisory. | Phase 1 Light labeling; Managed only after its decision gate |

The inventory points to baseline sources for provenance even when this table records an intentional delta. No generated distribution is switched to the extracted contracts in Phase 0.

