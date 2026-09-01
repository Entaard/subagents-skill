# Universal installation lifecycle contract

Canonical owner: `codex_experience`

One repository-root `install.sh` is the only install and update entrypoint. One repository-root `uninstall.sh` is the only complete-removal entrypoint. Phase 0 specifies the contract; implementation and migration of the current scripts occur later.

## Ownership receipt

Each installation has one versioned receipt conforming to [`../../artifacts/schemas/ownership-receipt-v1.schema.json`](../../artifacts/schemas/ownership-receipt-v1.schema.json). It records:

- installation ID, mode, source repository and source revision/hash, installer version, and destination roots;
- every owned path as a root-relative canonical path, entry class, expected type, ownership marker, content hash where stable, and cleanup order;
- every structured configuration or hook entry by configuration file, stable entry ID, exact selector, installed digest, and prior-content backup;
- displaced user content, its unique owner entry/config ID, backup locator, original path, source and destination identities, type, mode, and integrity hash;
- protected source/project roots that installation and removal may never own;
- runtime-owned data classes, per-class retention policy, the exact retained entry set, and whether `--keep-data` applies;
- the active lifecycle operation and durable recovery journal.

Every absolute and relative receipt path is a Unicode-NFC lexical canonical path: no parent, dot, empty, repeated-separator, trailing-separator, or NUL component. `/` is not a valid owned root. Lexical paths alone never prove separation.

`ResourceIdentity/v1` is the filesystem/provider-resolved physical identity: provider, volume, object ID, ordered ancestor object IDs, case-sensitivity and Unicode-normalization semantics, and the resolved canonical-path hash. Protected source/project paths, owned roots, every owned entry target, structured configuration targets, backup sources, and backup storage targets all record it. Each destination root names its approved destination-policy entry. An entry or backup storage target must physically descend from its declared root on the same provider/volume, not merely share a lexical prefix. Reject equal or ancestor/descendant physical identities, nested owned roots, duplicate resolved targets, case/Unicode aliases, and any physical overlap between an owned/config/backup target or restoration destination and a protected source checkout or project root.

Each owned entry records an installation-time target `ResourceIdentity/v1`, `lstat` identity, link count, ancestor no-follow proof, and symlink-target hash when applicable. It also records the immediate parent's canonical-path-bound resource and filesystem identities; an absence claim is valid only when observed through that exact parent. A replacement records a durable verified backup. Every backup names exactly one entry or configuration owner and a purpose (`displaced_user`, `config_prior`, or `operation_rollback`); its original path must equal that owner's canonical target, and no second owner or unreferenced backup is valid. A structured edit distinguishes the prior selector state from whether the containing file existed and, for a present prior file, records its identity, digest, and backup. Immediately before every update, restoration, or deletion, the implementation rechecks canonical root, ancestor no-follow proof, target resource identity, `lstat` identity, expected type, link state, ownership marker, and content digest where stable, then journals a hash of that precondition proof. Before restoration it also rechecks and journals the exact live backup storage identity and content digest. A symlink or hardlink ambiguity, unexpected type, changed identity/marker, digest mismatch, root-ancestry failure, or owner/path mismatch makes ownership unproven and blocks mutation of that entry.

### Receipt intent digest

`ReceiptIntent/v1` is the exact projection hashed before mutation. It contains receipt version, installation ID, mode, installer version, source, protected paths, roots, entries, configuration entries, backups, preservation, retention policies, and operation ID/kind/prior-receipt hash. It excludes operation state, the intended-receipt hash itself, and the recovery journal. Normalize strings to Unicode NFC and LF newlines, sort object keys, preserve array order, and serialize UTF-8 JSON with no insignificant whitespace as `sage-json-v1`; hash those bytes with SHA-256.

Every journal row repeats the operation ID, intended digest, and prior-receipt digest and carries separate precondition and postcondition `StateProof/v2` values plus their digests. Each row has separate entry, configuration, and backup ID sets. A present subject binds its evidence basis, target-specific resolved resource identity, ancestor-chain digest, `lstat` device/inode/link count, expected and observed type, ownership-marker digest, content digest, and symlink target. An absent subject carries no target identity; it binds the target-path hash and the exact live parent resource/filesystem identity through which absence was observed. Configuration proof uses the installed selector/digest as its ownership marker and records selector presence separately from file presence.

Preconditions prove the actual state immediately before mutation: a prior committed receipt for update/uninstall, a verified backup original for displaced content, or parent-anchored absence for a newly created target. They may never copy the intended post-state. Postconditions prove the exact state produced: the intended installed target, restored original, parent-anchored absence after deletion, durable backup creation, or backup-storage absence after cleanup. A restoration row carries one live backup subject for each referenced owner in both proofs, binding backup ID, storage `ResourceIdentity/v1`, `lstat` identity/type, content digest, and symlink target. A missing, changed, aliased, or extra subject blocks the operation. Proofs are serialized with `sage-json-v1` and SHA-256; the checker recomputes each digest and compares the complete subject sets, not only their hashes.

Update and uninstall resolve the immediately preceding receipt externally, recompute its canonical full-receipt SHA-256, and require the operation's prior-receipt digest and installation ID to match. A receipt cannot authenticate its own claimed predecessor. Every inherited backup ID and all immutable backup fields must exactly match that predecessor; update cannot drop one, and uninstall permits only the recorded `restored: false → true` transition for displaced-user or prior-config content. Restoration proof is derived from the predecessor and then compared with the live backup, never trusted from a rewritten current record. Every changed pre-existing update target has exactly one newly durable `operation_rollback` backup whose source identity and digest exactly match that prior receipt; a new target may instead need one displaced-user or prior-config backup. Receipt v1 update cannot silently drop a prior target; removals require the uninstall contract.

`JournalEntryProjection/v1` is the row without its own hash, including the preceding row hash; it uses the same canonicalization and SHA-256. The first preceding hash is null, and every later row must link to the exact prior row. A mismatched projection, precondition, journal binding, or hash-chain link is corruption, not a recoverable alias.

## Install and update

Before mutation, preflight every hard dependency, source, destination, conflicting path, structured configuration file, and available space. Calculate the complete intended receipt and preservation set first.

Stage generated files and configuration edits outside the live tree. Verify manifests, source hashes, permissions, schemas, and health checks. Back up conflicting pre-existing user content before replacement. Never silently overwrite a same-named path whose ownership is unproven.

Replace staged units atomically where the platform permits. Preserve run history, current-run recovery state, installed-only promoted knowledge, user-selected retention settings, and receipt-owned backups on every update. The receipt must name all five preservation classes; an empty or implicit preservation set is invalid. Reconcile stable promoted-knowledge IDs under the promotion contract.

The same version and same receipt is a clean no-op. An interrupted operation is resumed from its recovery journal or rolled back to verified backups; re-running converges without duplicate config entries or lost user data. A verified final receipt is committed only after installed skill, promotion workflow, optional clients, and any configured managed process pass their health checks.

## Failure recovery journal

Install/update journals record monotonically ordered phases: preflight complete, backups durable when backups exist, stage verified, each replacement applied, structured edits applied, health verified, receipt committed, and cleanup complete. Replacement and structured-edit phases may repeat.

Uninstall journals instead record: preflight complete, admissions stopped, processes stopped, each displaced user-content restoration, each structured-configuration restoration, each owned-entry removal, retention receipt committed when `--keep-data` applies, removal verified, ownership receipt removed, and cleanup complete. Restoration and owned-entry-removal phases may repeat. An uninstall never mislabels deletion as replacement or commits a new ownership receipt.

Every row binds the operation ID, intended receipt hash, prior receipt hash, exact affected entry/configuration/backup IDs, and both immediate state proofs. Proof times are causal and monotonic: precondition no later than postcondition, postcondition no later than the journal row, and a later row's precondition no earlier than the preceding postcondition. For a committed operation, the union of the relevant phase rows must equal the exact calculated target set; a phase name with empty proxy evidence is not completion. Install/update cover every changed entry, changed configuration, and newly durable backup. Uninstall covers every displaced-user restoration, configuration restoration, removable owned entry, and backup cleanup. An entry whose displaced user content was restored is deliberately excluded from owned-entry removal; deleting it would destroy the restored content. Operation-specific required phases and exact coverage make an interrupted install, update, or removal independently recoverable.

Recovery checks actual filesystem and configuration state before repeating an operation. An ambiguous replacement is reconciled by hashes and backups, never blindly replayed. If recovery cannot prove either the old or new state, preserve both, leave the receipt pending, and report the manual decision required.

## Complete removal

Complete removal requires explicit confirmation because it includes learned knowledge and run history. `--keep-data` is the deliberate exception; the receipt names every retained entry and produces a retention receipt with policy, expiry or legal hold, and new export owner where ownership transfers.

Removal first prevents new admissions and stops managed processes, then restores displaced user content and exact prior structured configuration, and only then removes receipt-owned executables, skills, clients, hooks, stores, leases, caches, logs, run history, installed-only overlays, receipts, and empty installer-owned backup roots.

Delete only entries proven by the receipt plus their expected ownership marker, type, and identity. Never delete the source checkout, project deliverables, unrelated configuration bytes, or a same-named user path. If a backup cannot be restored safely, preserve and report it. A changed or unprovable entry is left standing and reported.

`--dry-run` performs every proof and prints the ordered actions without changing bytes. Repeated removal after a partial failure is idempotent. Successful complete removal leaves no receipt-owned entry or structured configuration record; successful `--keep-data` removal leaves only the explicitly retained data and a retention receipt.

## Required lifecycle fixtures

Phase 0 includes a hash-valid install → update → uninstall receipt chain plus adversarial semantic mutations. The checker rejects missing exact phase coverage, duplicate restoration-purpose backups, an intended post-state copied into a precondition, noncausal proof times, a mismatched externally resolved predecessor, mutated/dropped inherited backups, a rollback backup that differs from the predecessor, a target identity smuggled into an absence claim, a target equal to its approved root, changed live backup content, and backup aliases. Later executable lifecycle tests cover repeated install, interrupted update at every journal phase, installed-only promotion, later global duplicate reconciliation, changed user configuration, paths with spaces, ancestor symlinks and hardlinks, process shutdown, dry-run, repeated uninstall, every supported prior receipt version, and byte-identical unrelated files.
