❯ does the sage has Does sage have the explore - plan - implement - verify loop?
  My main concern is that the sage skill gives too much trust to the initial plan and ledger, which might need to be updated in the middle of the task.
  fanout 2 teams of subagent, one attacker and one defender. The topic is: every decision should be verified and might need adjustments later. It's true with implementation, but is it true with planning (both task plan and team plan)?

## Result

The verdict: the premise splits, and not where you expected

Your concern is half right. The half it is right about is the team plan, not the task plan.

Both repo teams reached the same split by opposite routes. The defender stated it as a concession: "Team plan: weaker, admitted." The attacker stated it as its main finding: the team-plan case rests on measured run data, the task-plan case is
thinner. Two agents told to argue against each other independently constructed the same conclusion. By sage's own rule at SKILL.md:194, that is the strongest evidence class available here.

Why the task plan should stay stable

The task plan is not just a description of the work. Four things in sage read it back as data.

1. It is the rails' denominator. SKILL.md:244 — "The budget rail is a multiplier on the estimate you wrote yourself." :252 — "Neither half has a sensor of its own — both are your own reads." A mutable estimate is a mutable ceiling.
2. The measured drift is toward spending. memory/local-seed.md:60 — "every past ceiling raise was spent up to the new ceiling." One real run refused a pre-dispatch re-price and wrote down why: "Raising an estimate to dodge a rail is the failure
 mode local.md's watch list names."
3. The parent is the documented highest-error component. SKILL.md:21 — "The parent's post-fix confidence is the most reliable place errors enter, at ×10 confirmations." local-seed.md:74 records 3 defects introduced during fix rounds. An
 implementation decision verifies because it emits an artifact. A revised plan emits none. Verifying it means asking the parent to grade the parent.
4. Published evidence says that does not work. LLMs Cannot Self-Correct Reasoning Yet (arXiv:2310.01798, ICLR 2024) — models cannot reliably self-correct on intrinsic feedback, and sometimes get worse. A rebuttal exists (EMNLP 2024,
 https://aclanthology.org/2024.emnlp-main.714/) and it turns on having an external verification condition. That is the whole distinction.

And the feared failure has not happened. Across 11 ledgers and 3 handoff notes: zero mid-flight decomposition failures.

Where sage genuinely over-trusts

Three concrete gaps, all narrower than "re-verify the plan."

1. Team-plan seat errors are checkable before dispatch, and nothing checks them.

- One ledger: three units dispatched with model: haiku against alt agents. 22.4k spent proving nothing. "Caught by the deterministic model check, not by any agent report."
- Another: a unit dispatched as web-researcher, which cannot write.
- I made that exact error twice in this run. Both web researchers were told to write a file. Neither has a write tool.

This is not a planning loop. It is one grep of the agent file's tools: line before briefing. The skill already demands this pattern at SKILL.md:128 — "Grep the claim before you brief it" — but only for facts inside the brief, never for the
seat's own capability.

2. Task-plan amendments already happen, and no step sanctions them.

The defender counted 3 additive task-plan changes, all at harvest boundaries. The attacker found dispatch.md:65 — "Reclassify mid-task" — an instruction attached to no step. So the practice exists and the text does not describe it. That is the
real gap: undocumented improvisation, not missing capability.

3. The plan in force is not readable in one place.

SKILL.md:158 records deviations. dispatch.md:136's state enum has no re-scoped or re-priced state. One run logged nine deviations. After nine, no single section states the plan currently in force. This bites hardest at handover — the successor
inherits the original plan plus an exception list.

The classical result favours fixing this by amendment rather than rewrite. Plan Stability: Replanning versus Plan Repair (ICAPS 2006) shows plan repair beats full replan, because other agents may have based their plans on your stated
intentions. Both outside agents cited that paper. They read it differently and both readings hold: divergence is normal, minimal perturbation is the right response.

The one thing that contradicts

Anthropic's own multi-agent system draws the split the other way round. The orchestrator "decides whether more research is needed—if so, it can create additional subagents or refine its strategy," and "A linear, one-shot pipeline cannot handle
these tasks." So their task plan is revisable per round. But their team plan is frozen mid-round, because "the lead agent can't steer subagents, subagents can't coordinate."

The two views reconcile on granularity, not on principle. Nobody revises anything mid-flight. Everybody revises at a round boundary. Sage has that boundary already — the bring-current cadence at SKILL.md:162. It just does not hang a plan check
on it.

What I would change

Four edits, smallest first. I have not made any of them.

1. A pre-dispatch seat check. Before briefing a unit, confirm its agent file grants the tools the brief requires. One command. It would have saved 22.4k in one logged run and two briefing errors in this one.
2. A plan-premise check at the existing bring-current cadence. Not "re-verify the plan." The narrow question: did a harvested report invalidate a premise a pending plan row rests on? This is externally triggered by evidence, so it escapes the
 self-correction problem. It fires only at a boundary, so it escapes the coordination problem.
3. An amendment record that supersedes. Give the ledger a way to state the plan in force, not the plan plus nine exceptions. This is plan repair, which the ICAPS result supports.
4. Do not let re-pricing raise a ceiling. The estimate miss data (2.2× to 5.8×) says the estimating rule is wrong. That is a /sage-promote fix between runs, not a mid-run one. Mid-run re-pricing to dodge a rail is a named failure mode in the
 watch list.

Coordination check. The fan-out paid. The defender's zero-count is a finding no attacker would have looked for. The Anthropic granularity split came only from the outside lens. And the two repo agents converging on the same split is what makes
that split trustworthy rather than one agent's opinion.

Roughly 318k tokens across 4 agents. Full arguments are in the scratchpad: attack-repo.md and defend-repo.md. The two outside agents could not write files, so their evidence is in this conversation only.

✻ Baked for 8m 50s

❯ explain the edits 2, 3, 4 in simpler terms

● Edit 2 — Ask one question when a report lands

What it is. Sage already stops at fixed points to bring the ledger up to date. At each of those points, add one question:

▎ Did anything I just learned make a pending unit's plan wrong?

Only pending units. Units already finished do not matter.

Why this is safe. The question is triggered by a report, not by the parent's mood. The parent is not asked to re-think the plan. The parent is asked to compare one new fact against rows it has not dispatched yet.

Example. The plan has 5 units. Unit 2 reports back: "the auth code and the session code are the same file." The plan treated them as units 3 and 4, separately, because it assumed two files. Two writers on one file is a collision.

Today sage has no step that notices this. Unit 3 and unit 4 both launch. One overwrites the other.

With edit 2, the parent sees it at the next stop, merges the two rows, and dispatches one writer.

What it is not. It is not "check if the plan is still good." That question has no answer and no end. It is "does this specific new fact break a specific row."

Edit 3 — Write down the plan that is actually in force

What it is. Give the ledger a section that says what the plan is now. Today the ledger holds the first plan, plus a list of changes underneath it.

Why that matters. One real run logged nine changes. To know what the plan actually was, you must read the original plan and then apply nine corrections in order, in your head.

The analogy. It is the difference between these two things:

- A contract, plus nine amendment letters.
- A contract that has been re-issued, with the nine amendments already inside it.

Both hold the same information. Only the second one can be read.

Where it hurts most. Handover. When the parent runs low on context, it hands the run to a successor agent. That successor reads the ledger cold. It gets the original plan plus nine corrections, and it has to reconstruct the truth. A fresh agent
doing arithmetic on stale rows is exactly where a mistake enters.

Keep the history. Do not delete the old rows. The record of what changed and why is valuable. Just add one place that states the current answer, so nobody has to compute it.

Edit 4 — The parent may not raise its own spending limit

What it is. Sage's budget limit is 4× the estimate the parent wrote itself. So if the parent can rewrite the estimate mid-run, it can rewrite its own limit.

The problem in one line. A guard that can move its own fence is not a guard.

Example. The parent estimates a unit at 100k. The limit is 400k. The unit reaches 380k and is not done. The parent thinks: "my estimate was too low, this was really a 300k unit." It updates the row. The limit is now 1.2M. Nothing stopped.

Every step of that felt reasonable. The estimate probably was too low. That is why it is dangerous.

The evidence. This is already a known pattern in the repo's own notes. Two facts:

- memory/local-seed.md:60 — "every past ceiling raise was spent up to the new ceiling." Not some. Every one.
- One real run refused to re-price before dispatching, and wrote down why: raising an estimate to dodge a limit is on the watch list of named failure modes.

So what happens to the bad estimates? They were real. Past runs missed by 2.2× to 5.8×. That is a broken estimating rule, and it needs fixing.

Fix it between runs, not inside one. The run records what it actually spent. Later, /sage-promote reads those records and corrects the estimating rule for future runs.

The split. A run may spend more than planned and say so. A run may not quietly re-authorise itself to do it.

