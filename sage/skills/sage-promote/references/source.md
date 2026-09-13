# Source promotion

Read when assessing, preparing, reviewing, landing, or recovering Sage source changes. An explicit `$sage-promote` invocation includes both installed knowledge and source improvement unless the user narrows its destinations. Complete the eligible work without asking again for permission to prepare an uncommitted patch. Git staging, commits, pushes, and installation into real environments remain human actions.

## Resolve the checkout

Keep three paths distinct: the installed package, the shared runtime root, and `SOURCE_ROOT`, the Sage package inside the source checkout. Resolve `SOURCE_ROOT` from the user's explicit path, then an absolute `SAGE_SOURCE_ROOT` environment setting, then the loaded source package or the installed `<target-root>/sage/receipt.json` field `source_root`. The environment setting is a skill convention, not a knowledge-helper CLI flag. A supplied invalid path is a reported error, not a reason to silently choose a different repository.

Verify the candidate contains `install.sh`, `scripts/sage-lifecycle.py`, and both active skill entrypoints. Inspect its enclosing Git repository and confirm it is the intended Sage checkout; the receipt is a location hint, not permission to edit an arbitrary path. Installed package files are never a fallback source checkout. Pin the physical source/repository paths, HEAD, staged and unstaged diffs, untracked paths, and before-bytes/hashes of files this pass may touch. Preserve pre-existing user changes and the Git index.

A moved checkout, absent Docker bind mount, or read-only source does not erase the source destination. Finish independent installed-knowledge work. If an exact baseline is readable, prepare a portable patch and review note under the coordinator's evidence directory; report source delivery as pending application with the exact path/access needed. If the baseline is unavailable, report the unresolved source work and request its checkout location. Do not claim `no_change` for a destination that could not be inspected or mark required undelivered source work complete.

## Choose the representation

Inspect current source instructions, references, helper behavior, and relevant tests alongside the eligible closed-run evidence. Classify each bounded candidate as installed knowledge, source change, both, or no change, with a reason for each requested destination. Already-landed runtime knowledge can still justify a missing source improvement. Existing source rules can be corrected or removed even when the runtime store is empty or has no matching stable ID.

- Use runtime records for selective, situation-specific guidance and its review/status history.
- Put reusable operational guidance in the relevant shipped skill or reference, retaining its qualifier and a clear loading condition. A new reference must be reachable from an installed entrypoint; a note only under source `docs/` does not change installed behavior.
- Change source helpers when a demonstrated implementation defect or missing capability warrants code, with a regression at the real behavior seam. Include affected contracts, references, and installer mapping when needed. The installer ships the two skill trees and its explicit helper allowlist; source-only scripts and tests do not ship automatically.
- Correct or remove obsolete source instructions, references, or implementation when evidence supports the change; repair callers, links, tests, and packaging. Record the old behavior and the refuting evidence or intentional `explicit_decision`, `superseded`, or `scope_obsolete` basis. Disuse alone cannot justify removal. Reconcile matching runtime records by stable ID where they exist; do not create a dummy record merely to remove a source rule.

Source changes distribute learned behavior through Git and the user's later `install.sh`. The runtime store and closed logs remain local; installation does not copy or merge them. Do not export the local store wholesale or turn one project's frozen fact into an unconditional Sage policy. Preserve provisional/contested findings as qualified evidence for further work, not supported operational defaults. Apply the shared evidence-class predicate to the actual scope of every proposed source behavior.

## Author and review exact changes

Use the three distinct live actors from the promotion procedure. The author prepares both the knowledge proposal and source patch when applicable. Refutation and review must cover the exact patch, relevant current source, qualifying evidence, counterevidence, and the knowledge/source correspondence. Material edits return to the author and receive renewed challenge and review.

Prepare changes in an isolated copy of the observed working tree when possible, including relevant uncommitted baseline edits. Record source preimages and candidate postimages, including additions/deletions, so integration can distinguish this pass's edits from the user's. Maintain one writer in each shared workspace. The coordinator retains the procedure loaded at invocation: a patch to Sage or sage-promote cannot weaken its own evidence, review, or landing gates or execute its newly authored instructions during this pass.

Exercise the changed behavior and declared qualifiers, including a realistic independent instruction scenario when guidance changes. For helper or packaging changes, run the relevant regressions and install/update/uninstall checks only in isolated temporary targets. Verify changed shipped files arrive and obsolete owned files are removed without altering unrelated files or runtime knowledge, including when package and runtime directories share a parent. Updated helpers must still validate retained pre-update generations and preserve their retrieval/status and rollback behavior; test existing-format fixtures and, when available, an isolated copy of local knowledge. A schema change must retain backward reading compatibility; any needed data migration is separate explicit work, never an implicit install effect. Tests on the current machine do not prove other operating systems; preserve platform limits and make portable fixtures runnable on another machine.

For each actual source patch, author a concise `SOURCE_ROOT/docs/promotions/<coordinator-id>.md` review note containing:

- candidate/stable IDs where available, intended behavior and exact source paths;
- closed-run IDs/log hashes, portable evidence summary, counterevidence, qualifiers, and correction/retirement reasons;
- actor identities, refutation/review dispositions, exact behavior-patch hash and baseline/postimage hashes;
- executed checks/results, reproduction commands or fixtures, and untested environments;
- corresponding installed generation/actions, or why no runtime action is needed, and the user’s manual install command with a target placeholder.

Keep source review material self-contained enough for another machine to assess the change. Include minimal sanitized reproduction fixtures when needed. Local evidence locators may supplement it but cannot be its only explanation; do not copy raw run logs, secrets, or unrelated project artifacts into the repository. The review note is evidence, not an additional always-loaded skill instruction. Freeze and review the behavior patch; the final note may attach resulting hash/check receipts without altering that patch.

## Apply, recover, and hand off

Recheck HEAD, index, touched preimages, source-log hashes, and proposal/patch hashes before integration. If the relevant baseline changed, reconcile it and renew review of any materially changed patch. Apply only the reviewed hunks and note, preserving the index and unrelated edits. Capture a diff relative to the observed working tree (including new/deleted files), run the relevant final checks, and verify the actual changed files match the reviewed postimages. A whole-repository diff may contain the user's prior work and is not by itself this pass's patch.

Treat source edits and runtime activation as separately checkpointed effects with an explicit order and any dependency in the plan. Existing installed helpers govern runtime activation; if a proposed record needs newly authored code or schema, keep that activation pending the user's installation instead of installing it or passing incompatible data to the old helper. Source-only improvements need no empty knowledge generation.

Before retrying an interrupted source write, compare each path with its recorded preimage/postimage and reconcile partial application; neither assume success nor reapply blindly. Undo only this pass's changes against still-matching postimages. Preserve overlapping user edits and report unresolved conflicts. Knowledge rollback does not undo source files, and reverting a source patch does not roll back the active knowledge pointer.

Report installed status (`activated`, `no_change`, or pending/failed with reason) and source status (`ready_for_review`, `no_change`, or pending/failed with reason) separately. Return the exact checkout, changed paths, patch/review-note paths, checks and rollback/recovery information. A verified uncommitted patch is the delivered source result; the user's later commit and real `install.sh` are outside this invocation's completion criteria. Never run those release actions as a finishing step.
