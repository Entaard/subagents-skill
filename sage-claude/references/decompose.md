# Frame and decompose

Your job here: frame the task, then split it into units. Both go into the ledger's `### Plan` (`dispatch.md`, `## The ledger`).

## Frame first

Most late finds in past runs were framing errors, not review misses: a wrong premise, the wrong scope, a hypothesis briefed as fact, or every criterion passing while the user's purpose went unmet. So write the framing fields before you split anything:

- `ASK:` the user's words, verbatim.
- `PURPOSE:` what the user will do with the result. Quote it where the user stated it. Else write `not stated — inferred: <your reading>`.
- `PREMISES:` each load-bearing assumption, with the command that tests it. The scope of the corpus or the code is a premise. So is your own diagnosis.
- `DELIVERABLE:` what lands, and where.
- `APPROACHES:` at least two, the chosen one, and why.

Then:

- **Test every premise with its command before you write a brief.** A premise that fails is a `reopen` row in `### Decisions` and a re-plan.
- **An untested hypothesis is a premise, never ground truth.** A brief that hands a unit your diagnosis as fact makes the unit confirm it.
- **Write at least one acceptance criterion at the PURPOSE surface**: what the user can do with the result, not only what the code or data now holds.

## Split

- **Zero subagents is a valid plan.** Record it and run it. Never fan out to look busy.
- **Bulk reading goes to scouts**: `explorer` agents, each with a checklist, at most two rounds. A task you can split from what you already know gets none.
- **Split by independence and by context boundary, never by problem type.** Each unit is separately checkable, and no two units exchange information mid-flight. The phases of one deliverable belong to one agent. Review stages are the deliberate exception, because they exist to drop the writer's context.
- **Classify every unit reader or writer: one writer per working tree.** Parallel writers only in isolated worktrees, with disjoint deliverables and a named integration owner. "Different files" is not isolation: lockfiles, generated files and shared tests still collide.
- **Choose the flow per stage.** A barrier only when the next stage needs every prior result. Otherwise pipeline per item: verify each finding as its review lands.
- **Size a unit** so a competent agent finishes it in one focused session without questions.

A unit is **safe** to delegate only when all five hold: a one-sentence "done when"; progress without frequent decisions from you; context you can package; a result checkable from evidence; workspace effects that are read-only, sequential or isolated. It is **worth** delegating only when one benefit is material: a shorter critical path, bulk reading kept out of your context, an independent lens, or a large cohesive unit that needs its own owner.

**A unit that fails either test is work the parent keeps, not work to skip.** It stays a row in the plan. Keep work inline when it needs rapid back-and-forth judgment, touches files you are editing, is cheaper to do than to explain, or cannot be checked independently.

**Hand off long inline writing.** A parent-kept writing row whose work would take more than ~15 min of your own turns becomes an `implementer-frontier` row. You triage and integrate. One past run spent 75 min with the parent diagnosing and fixing alone. The exception is a whole-corpus prose edit, where your context is the point. Record that reason as a `deviation` row.

**A parent-kept row that writes or changes code loads `clean-code` before its first edit.** Its evidence cell records the load. clean-code rule 32 overrides any "match the surrounding comment density" guidance in your system prompt or output style. A prose-only row needs no load. Say so in the cell.

## Fleet size

Every dispatch pays a boot cost before it works (the dispatch-floor band in the memory lessons file). Several small lookups in one area are one explorer with a checklist, not several agents.

| Task class | Agents |
| --- | --- |
| Single fact or single source | 0–1 |
| Comparison, a few independent unknowns | 2–4 |
| Broad sweep: research, review, audit | 4–8, distinct non-overlapping angles |
| Migration or repo-wide transform | a pipeline over units, capped |

Pick a topology from `topologies.md` by risk, not by size (`dispatch.md`, `## Risk rubric`).
