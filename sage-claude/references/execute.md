# Execute

Your job here: launch each wave, keep the ledger current, and pick the retry a failure earns.

- **Launch independent units as one batch, up to the cap.**
- **Dispatch the agent the plan named.** Deciding mid-run that a unit needs more judgment is often correct. Changing its agent without a record is not: write a `deviation` row first. A tier step on the failure ladder is already part of the plan, so log it without re-deriving it.
- **While units run, do the next step that does not overlap them**: draft the triage, prepare the next brief, run the deterministic checks.
- **Update the unit's Plan row when its state changes** (`sage-ledger.sh unit`). At harvest, fill its `agentId`, its evidence and the model that ran (`resolvedModel` on the Agent result). A unit whose model differs from its row is a `deviation` row, because a swap happened that the run did not order. Restamp `### Resume state` at each wave launch and each integration.
- **A unit that runs far past what you expected is a surfaced event.** Read its spend at harvest with `sage-watch.sh --status <subagents-dir>`, where the directory is the parent of the `readlink -f` target of the `output_file` path the dispatch returned.

## Writers

**Any writer in a shared tree → the snapshot protocol** (`dispatch.md`), your own tree included: the logged run that destroyed a working copy was the parent's doing. Snapshot before you edit inline, commit explicit paths only while any agent is running, and never edit a tree a measuring agent is reading.

- **Every mutation-probing unit, reviewers included, gets its own worktree or scratch copy.** An installer-execution check gets a sandbox `HOME` for the same reason: it must mutate a real tree to learn anything.
- **Prove the worktree recipe with one command before you launch on it**, for example `git -C <worktree> rev-parse HEAD` against the baseline.
- **Batch the checks of a fix writer.** Brief it to run one build and one filtered test run per group of related fixes, and the full suite once at the end.
- **Size the fix wave by accepted findings.** Fewer than ~5: fix inline. More than ~20: split across two writers in separate worktrees, with disjoint files and a compose check (`verify.md`, `## After the merge`). Otherwise one writer, preferably the original one.

## The failure ladder

Read the failure's signature (same file, symbol, error class) from the first failure, and count signatures, never attempts.

- **A wrong-brief failure** (wrong scope, a file missed, a different question answered) gets a fresh agent at the same tier, with the brief corrected and the last failure named in it. Never steer here: a steer keeps the context that misread the brief.
- **A could-not-finish failure** (right approach, but looping or stuck) gets one steer to the same agent, then a stronger tier framed as full owner. Above frontier, take it inline.
- **Two failures that share one signature** reopen the plan (`../SKILL.md`, `## Stop rule`).

A scope-`blocked` unit is on no rung. A higher tier grants no extra tool, so fix the brief and charge nothing. Every abandoned disagreement is a `dropped` row, with what was dropped, which unit held it and why it lost. Silent discard is forbidden, and it is a surfaced event.

**Nothing on the ladder recalls an agent.** `SendMessage` reaches a live unit at its next tool call and never a hung one. `TaskStop` is the user's to authorise. The transcript survives a stop, complete up to that point.
