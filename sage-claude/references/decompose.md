# Decompose

Whether the task was worth agents is settled — the invocation settled it. What is open, and answered per unit rather than per task: **which units are safe to hand out, and which the parent keeps.** Split the work first, then test each unit against the criteria below. Read this file when the invocation lands, and `topologies.md` right after it.

Delegation is spending. Spend it where parallelism, context protection, or independent verification genuinely pays. Three principles follow from that:

1. **The parent owns the state machine.** Goals, risk calls, delegation decisions, triage, integration, and the final completion claim stay with you. Subagents propose; you decide.
2. **Every delegation is a falsifiable contract.** Bounded objective, explicit inputs, explicit boundaries, defined return format. A brief that cannot fail is not a brief.
3. **Zero subagents is a valid conclusion** — and for tightly coupled work, the correct one. Record it as the plan and run it; never fan out to look busy. A skill that must always delegate will delegate ritually.

**Scout before you study.** Splitting needs a map, and reading the corpus raw to build one spends the bulk reading this skill exists to keep out of parent context. Where the map takes more than a few targeted reads, dispatch **scouts**: `explorer` agents, each briefed with a checklist and distilling back, the wave sized to the task's surfaces. Three bounds hold: a saved reader type whose file enforces read-only with no shell and no network — `explorer`, or `explorer-alt` where it is installed, whose tool scope is identical (neither installed → no scouts; study inline); at most two rounds, the second only for follow-ups the first surfaced; and the **actual** cost recorded on the ledger's `### Unit table` as spend that has already happened. Scouts are units like any other. A task you can decompose from what you already know gets none.

Split rules:

- Split by independence: each unit is separately checkable, and no two units exchange information mid-flight. Two units that keep passing data to each other get merged or serialized.
- **Split by context boundary, not by problem type** — where context must not cross, and where you would want to inspect or intervene. The phases of one deliverable belong to one agent: slicing production work into sequential phases handed agent-to-agent loses fidelity at every step, and a ten-step job does not need ten units. Review and verification stages are the deliberate exception — they exist *because* the split drops the writer's context.
- Classify every unit **reader** or **writer**. Partition write scopes up front: **one writer per working tree.** Parallel writers only in isolated worktrees with disjoint deliverables and a named integration owner. "Different files" is not isolation — generated files, lockfiles, registries, and shared tests still collide.
- Choose the flow per stage: a **barrier** (wave) only when the next stage needs *all* prior results or a shared tree must stabilize; otherwise **pipeline per item** — verify each finding as its review lands rather than waiting for all reviews.
- Size units so a competent agent finishes in one focused session without asking questions.

Then test each unit twice. It is **safe** to delegate only if **all** of these hold:

1. Bounded deliverable with a one-sentence "done when" — if that sentence will not write, the unit is too big: split it and test the pieces.
2. Useful progress possible without frequent decisions from you.
3. Required context can be packaged explicitly — files, briefs; the agent starts blank.
4. The result can be checked or falsified from evidence.
5. Workspace effects are read-only, sequential, or isolated.

It is **worth** delegating only if at least **one** of these benefits is material:

- Parallelism shortens the real critical path.
- It keeps noisy exploration, logs, or bulk reading out of your context.
- It supplies a genuinely independent lens or evidence source.
- It is a large, cohesive unit that benefits from a dedicated owner.

**A unit that fails either test is work the parent keeps, not work to skip.** Keep it inline when it needs rapid back-and-forth judgment, touches files you are editing, is cheaper to do than to explain, or cannot be verified independently. Parent-kept units are parent-owned rows in the plan like any other; they never disappear from it. Delegated coupled work is a quality failure, not a cost one.

**A parent-kept row that writes or changes code loads `clean-code` before its first edit.** That row's `evidence` cell records the load. One invocation covers every inline edit that follows, so this is a per-session act rather than a per-edit one. The `implementer` agent's `skills:` preload is the only other way those rules reach a writer, so a writer you keep for yourself gets nothing unless you load it. On the parent path one run wrote 25 lines of doc comment over a one-line body; every `implementer` dispatch over the same corpus wrote one-line summaries instead. It matters most for comments. The coding guidance in your own system prompt tells you to match the surrounding file's comment density, and an output style may tell you the same. `clean-code` rule 32 overrides both. Do not assume the active style has been corrected: a style is a per-machine file and any other one may still say match. A row that edits prose rather than code needs no load. Write that in the cell rather than leaving it blank.

Scale the fleet to the task. Over-spawning is the classic failure mode, and the floor matters as much as the ceiling: every dispatch pays a boot cost before it does any work (the dispatch-floor band KI in `../memory/local/` holds the measured figures), so several small lookups in one area are **one** explorer with a checklist, not N agents.

| Task class | Agents |
| --- | --- |
| Single fact / single source | 0–1 |
| Comparison, a few independent unknowns | 2–4 |
| Broad sweep: research, review, audit | 4–8, distinct non-overlapping angles |
| Migration / repo-wide transform | pipeline over units, concurrency-capped |

Little or nothing delegable is a finished decomposition, not a failed one. Record it, run it mostly solo, and let Step 6's coordination check speak for it.

Pick a topology from `topologies.md` when one fits — research sweep, implement–review–fix, migration pipeline, bake-off, loop-until-dry, adversarial verification, quarantined deep read, competing hypotheses, completeness critic, blind acceptance suite, pre-write plan critic, blind behavioural lens. Pick it by risk, not by size (`dispatch.md`, `## Risk rubric`).
