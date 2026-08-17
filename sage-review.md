# Review: The Sage

Reviewed file: `ideas.md` (2026-08-17). Review date: 2026-08-17.

Panel: 10 reviewers. The lead (Fable 5, max effort) read the full corpus and reviewed the idea itself. Nine subagents each reviewed one angle: 2 Opus (feasibility, red team), 3 Sonnet (value, conflicts, design), 4 Haiku (clarity, prior art, practicality, open questions). Every repo claim below carries a file and line. The lead spot-verified the load-bearing ones.

Basis: `ideas.md`; `subagents-claude/SKILL.md`, `calibration.md`, all three `references/` files; `claude-skills/agents-self-reflect/SKILL.md`; `self-reflect-report.md`; all four `summon-teams-claude/` docs; `claude-agents/`; `docs/agents/domain.md`; `output-styles/simplified-technical-english.md`; live probes of the harness on this machine.

---

## Verdict

The Sage is possible with work. But it is not one project. It splits three ways:

- About 70% of the Sage already exists in this repo, built and measured. The learning loop, the lesson compression, the dissent machinery, and the stop rules are shipped rules with confirmation counts, not open ideas.
- About 20% is new and buildable today: watching a running agent for trouble, and handing work over before the parent degrades. Both have concrete mechanisms in the current harness. The panel verified the key one on disk during this review.
- About 10% should not be built as written: the silent-autonomy clause (no plan, no report) and the machine-only brain. The first reverses a decision this repo made with evidence this month, and it looks like drift rather than intent. The second rests on a mistaken premise about how models read.

Panel verdicts: five of ten said "possible with work". Five said "partly possible". None said "possible now". None said "not possible". The split is not disagreement about feasibility. It is disagreement about how much weight the two bad clauses carry.

The strongest single finding is empirical. The harness writes every subagent's transcript to disk incrementally, while the agent runs, with per-turn token counts and every tool call. A sidecar `meta.json` carries the dispatch description, which joins a live file to a plan row. The lead confirmed this layout on this machine during the review. This turns the Sage's hardest behavior, "knows when an agent is lost", from a research problem into an engineering task. It also gives a real fix for the repo's one known skill defect (the overrun rail that samples only between dispatches).

---

## What the Sage asks for

The note is nine behaviors. This review names them S1 to S9.

| #   | Behavior                                                                                   | ideas.md |
| --- | ------------------------------------------------------------------------------------------ | -------- |
| S1  | Not smarter than its model. Uses the model's power as efficiently as possible              | :9-10    |
| S2  | Learns from every mistake and success. Compresses each lesson to the smallest precise form | :10-12   |
| S3  | Every agent has limits. Strength comes from combining agents                               | :14-15   |
| S4  | Detects an overloaded or lost agent. Recalls it, learns from it, re-routes                 | :17-18   |
| S5  | Encourages dissent. Listens to all ideas equally. Verifies them                            | :20-22   |
| S6  | Walks away from pointless quarrels                                                         | :24      |
| S7  | Hands work over before it overloads itself                                                 | :26      |
| S8  | Organizes its brain for machine efficiency. No human needs to understand it                | :28-31   |
| S9  | Proposes no plan. Shows no report unless asked                                             | :33      |

One more thing sits in the note's first paragraph. Line 5 says both "I want it to evolve even more" and "I want to create a new skill". Those are different projects. The repo already settled this question once for summon-teams (evolve, do not fork; summon-teams-review.md:88-94). The note should pick a side, and the panel is unanimous that the side is evolve.

## How possible each part is

| #   | Status                         | What exists today                                                                                                                                                                                                     | What is missing                                                                                                                                                                                                                              |
| --- | ------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| S1  | EXISTS                         | The skill's spine: the tier and effort matrix (SKILL.md:187-195), four saved agents that make effort real (references/claude-code.md:87)                                                                              | Nothing. This is already the design thesis                                                                                                                                                                                                   |
| S2  | PARTIAL                        | The full loop: run log with lessons (calibration.md), confirmation counts, strength bands, promotion rules, lossless consolidation (agents-self-reflect/SKILL.md:9)                                                   | Only the word "always". Appending is automatic. Consolidation and promotion are human-gated, for reasons the evidence supports. See "Learning without a human"                                                                               |
| S3  | EXISTS                         | The whole orchestration skill; 11 topologies (references/patterns.md)                                                                                                                                                 | Nothing. One caution: keep the coupling test. "Zero subagents is a valid recommendation" (SKILL.md:16) must survive the note's always-combine framing [C]                                                                                    |
| S4  | MISSING, BUILDABLE             | Post-hoc only: the failure ladder with signature counting (SKILL.md:208), `maxTurns` (claude-code.md:99), steering via SendMessage, `output_file` transcripts (claude-code.md:25)                                     | The live detector. Buildable now as a watchdog over the incremental transcript files. See "Watching a running agent"                                                                                                                         |
| S5  | EXISTS, stronger than the note | Adversarial verification (established, ×10), disjoint mandates (×6), "settle a disagreement with a command, not by model tier and not by majority" (×4) (SKILL.md:219-226; calibration.md)                            | Nothing. One word in the note is wrong: ideas should be _verified_ equally, not _listened to_ equally. Equal listening is the behavior the repo's data already rejected                                                                      |
| S6  | EXISTS                         | Identical failure signature means stop patching and reopen assumptions (SKILL.md:208, 248); dry-round termination (patterns.md #5); "silent discard is forbidden"                                                     | A rule for quarrels the _parent_ is inside. Small gap                                                                                                                                                                                        |
| S7  | PARTIAL                        | The ledger as recovery map, the `plan-only` split (plan in one session, run in a fresh one), compaction rules (SKILL.md:147-151, 209-210)                                                                             | The handoff note template. Asked for three times in this repo's own history, never built (summon-teams-review.md:29, 105, 131; contracts.md:180 still assumes it exists). Plus the trigger: a parent self-occupancy rail. Both buildable now |
| S8  | PARTIAL, and partly wrong      | The compression machinery is exactly this: rules stripped to one line, counts kept in one file, an archive for provenance (agents-self-reflect/SKILL.md:82-84)                                                        | The "no human reader" half should not be built. See "The brain premise"                                                                                                                                                                      |
| S9  | CONTRADICTED                   | The hard gate (SKILL.md:109-143) and the mandatory report (SKILL.md:230-242) implement the owner's own decision from this month: "Always propose plan to human, even when it's dead simple" (summon-teams-idea.md:19) | As written this is a reversal with no new evidence, and probably an unintended one. A reshaped version is worth building. See "The autonomy clause"                                                                                          |

### Watching a running agent (S4)

The mechanism exists on disk. Verified on this machine, live, while the panel ran:

- Each dispatch writes `~/.claude/projects/<project>/<session-id>/subagents/agent-<id>.jsonl` incrementally during the run. File mtimes tracked the wall clock.
- A sidecar `agent-<id>.meta.json` is written at spawn: `{agentType, description, toolUseId, spawnDepth, model}`. The `description` field is the parent's own Agent-tool parameter. That is the join key from a plan row to a live file. No new harness feature is needed.
- Each record carries full token usage and every tool call with its input.

So a watchdog is one scalar-returning script plus the Monitor tool, with SendMessage to steer and TaskStop to recall. That is the note's "calls the agent back", verbatim, with today's tools. [Opus-Feasibility discovered and measured this; the lead verified the layout]

What it can and cannot detect, honestly:

| Signal                        | Detects                         | Reliability                                                                                                 |
| ----------------------------- | ------------------------------- | ----------------------------------------------------------------------------------------------------------- |
| File mtime staleness          | A hung or stalled unit          | High                                                                                                        |
| Turn count, cumulative spend  | A runaway unit                  | High. Sum output + input + cache_creation tokens. Never sum cache_read, which is re-read context, not spend |
| Repeated identical tool calls | "Lost in a maze", made numeric  | High                                                                                                        |
| Repeated tool errors          | Thrash against a broken command | Medium-high                                                                                                 |
| (none)                        | "Can't think straight"          | Not detectable. Reasoning quality is only judgeable from the report, after it lands                         |

Two costs to design for, not around. False positives: a verifier deep-reading a 25k-word corpus looks like a loop from outside, and TaskStop terminates without a report, so a wrong recall pays the full spend and learns nothing [Opus-RedTeam]. False negatives: the confident lost agent, the one that fabricates a data structure or a wrong version attribution, burns a normal budget and returns a fluent report. No time or token signal sees that case (SKILL.md:178). The skill's existing verification layer stays the defense for it [Opus-RedTeam].

Two design constraints. The directory layout is undocumented internal state, so the watchdog must probe for it at start and degrade to silence when absent [Opus-Feasibility]. And the "don't poll a harness that notifies" rule (SKILL.md:206) must be amended explicitly, not silently violated: a cheap grep on a local file is a different act than re-asking a harness that will notify, and the skill text should say so [Sonnet-Value].

Bonus: this closes the repo's known defect. The ~25% overrun rail samples only between dispatches, so four logged runs overran on their final agent with nothing left to launch (calibration.md:180-185). A monitor over these files samples continuously and can fire mid-flight [Opus-Feasibility].

### Learning without a human (S2)

Split the loop into its three acts. They carry different risk.

1. **Append** (one row per run): already automatic (SKILL.md:242). Safe. Keep.
2. **Consolidate** (rewrite the log into bands and rules): automatable with the guards that already exist. The pass is lossless, self-checked, and idempotent by design (agents-self-reflect/SKILL.md:9, 77). The stakes are one machine-local memory file.
3. **Promote** (write rules into the skill text that governs every future run): this is where full autonomy gets dangerous, because every existing safeguard checks that a lesson _recurred_, and none checks that it is _true_ [Opus-Feasibility].

The danger is structural, not hypothetical. The lesson row is written by the same parent that just made the completion claim, and the repo's most-confirmed rule (×10, established) says the parent's post-fix prose is where unsourced confidence enters (SKILL.md:222). A wrong rule in calibration.md is then read at Step 2 of every later run, changes how runs are briefed, and generates the evidence that promotes it. It is self-confirming [Opus-Feasibility]. And the file has already been corrupted once by an automated pass: the reflect skill rewrote the log header into a shape matching no committed version, which broke an installer notice, and a human reading a report is what caught it (self-reflect-report.md:53-55) [Opus-RedTeam].

The traced failure looks like this. A run prices research from a band. The compression step drops the band's qualifier ("only for briefs that name their URLs"). The next run overruns. The Sage explains its own miss wrong, and writes a second bad rule on top of the first. Three tasks, three mutually reinforcing wrong lessons, with the provenance needed to unwind them already compressed away [Opus-RedTeam].

The repair is cheap. Keep automation for acts 1 and 2. Keep the human diff for act 3. Give every promotion candidate a falsifier ("what observation would retire this rule") plus one refuting verifier over the promotion batch, briefed to default to refuted [Opus-Feasibility, Sonnet-Design].

### Handover (S7)

This is the best-scoped gap in the whole note. The template was requested three times and never shipped [Sonnet-Value]. The shape is write-and-stop: at a threshold, bring the ledger current, write a handoff note to the durable gitignored path that `plan-only` already uses, print the path, end the turn. `/subagents <path>` is already the resume flow (SKILL.md:149) [Sonnet-Design].

One correction to the skill's own docs came out of this review. `references/claude-code.md:192` says the parent "cannot read context usage". The first half is wrong: the parent's own session transcript sits beside the subagent files with the same usage records, and summing the last assistant record's input-side tokens gives live context occupancy. The feasibility reviewer measured the parent mid-review [Opus-Feasibility]. So the trigger for "keep its mind sharp" is buildable too. The second half stands: the parent cannot compact itself and cannot open a new session. Handover ends the turn, and someone must pick the note up. A Sage that never talks to the human has removed the actor its own handover depends on.

---

## The good

- **The thesis is right, and it is the repo's own thesis.** "Not smarter than its model, but uses it as efficiently as possible" is the best line in the note. Wisdom-as-harness is what calibration.md already is: results improving while the model stays fixed. [All reviewers]
- **The two real gaps it names are the right two.** Nothing watches a running unit, and nothing watches the parent itself. Both are now measurably buildable, and one closes a logged defect. [Opus-Feasibility, Sonnet-Value, Haiku-PriorArt]
- **"Learn from successes too" is already honored and worth keeping.** The calibration contract insists hits get recorded next to misses, which is the part most systems skip (calibration.md:11-13). [Opus-RedTeam]
- **The dissent instinct matches the strongest evidence in the repo.** Disjoint mandates produced disjoint findings in every logged multi-lens run, and the decisive finding was repeatedly invisible to every other unit. [Sonnet-Value]
- **Walking away from dead ends is measured here, not just wise.** Identical-signature stops and dry-round termination are shipped rules. [Haiku-PriorArt]
- **The compression instinct is validated by machinery the note did not know existed.** "Purest, smallest, most precise lesson" is a poetic description of the promotion rule: write the rule and its strength band, never the counts and dates. [Opus-Feasibility]
- **Every undefined term already has a candidate definition in the repo.** "Lost" has the failure signature. "Pointless quarrel" has settle-with-a-command. "Golden information" has the calibration rule shape. The note does not need new concepts, only citations. [Sonnet-Conflicts]

## The bad

- **S9 reverses this month's decision, and it looks like drift, not intent.** "Always propose plan to human, even when it's dead simple" (summon-teams-idea.md:19) became the hard gate days ago, and the repo's record shows why: plans change on contact with the human (summon-teams-review.md:82). The note never mentions the gate, the report, calibration.md, or agents-self-reflect — the four things it would replace. That silence reads as a note drafted without re-checking the sibling machinery. [Sonnet-Conflicts, Opus-RedTeam, Sonnet-Value]
- **The note's final paragraph defeats its own core claim.** "Greatness comes from achieving great results" needs a judge, and line 33 removes the channel the judge would use. Greatness becomes self-asserted and unfalsifiable by construction. [Sonnet-Conflicts]
- **No report by default removes the recovery map.** `/rewind` does not cover subagent edits (claude-code.md:188). Scripted writers auto-approve their edits (claude-code.md:144). The report and ledger are the only trail. Silence plus delegated writes is unrecoverable by design. [Opus-RedTeam, Opus-Feasibility, Haiku-Practical]
- **Unreviewed self-rewriting memory compounds its own errors.** Recurrence is checked; truth is not. The file was already corrupted once by its own automation, and a human report reader caught it. [Opus-RedTeam, Opus-Feasibility]
- **"Listened to equally" is a regression from the shipped rule.** The repo learned, four times, that consensus and seniority both lose to one measurement. Reviewers once agreed on a repair direction that was factually backwards. [Opus-RedTeam]
- **The note proposes full autonomy and names no safety bound.** The current mid-run rails (destructive actions, writer isolation, budget; SKILL.md:155-163) have no counterpart in the note, and no cost policy appears at all, though the sibling idea doc put cost efficiency at priority two. [Sonnet-Conflicts]
- **The note is not buildable as specified.** Every mechanism-shaped word ("overloaded", "pointless", "golden", "handover", "top performance") is undefined. No trait has a "done when" sentence, so the note would fail the skill's own Step 1 test. [Haiku-Clarity, Haiku-Questions, Sonnet-Value]
- **The note breaks the owner's own style guide while praising compression.** Long stacked sentences, idioms, and typos that change meaning: "gets lots in a maze" (lost), "moto" (motto), "over looked" (overlooked). [Haiku-Clarity]

---

## The two decisions to reshape

### 1. The autonomy clause (S9): separate recording from showing

The defensible desire inside S9 is fewer interruptions, not less evidence. Split the two:

- **Always record. Silence is a display choice, never a data choice.** The plan, the ledger, and the full report are always written to files, every run, even when nothing is shown. "The human has to ask for the report" is acceptable exactly when the report already exists on disk. [Haiku-Practical, Fable-Lead]
- **Show by tier, earned per task class.** Reuse the calibration mechanism instead of inventing a trust ledger: a task class with enough consecutive on-budget, no-major-finding runs can print its plan without blocking on an answer. New task shapes keep the full gate. Destructive, irreversible, or externally visible actions keep the full gate at every tier, and so does any writer outside a pre-authorized envelope. [Sonnet-Design, Sonnet-Conflicts]
- **Report on anomaly, collapse otherwise.** The Result section always prints. The orchestration block collapses to one line unless a deviation, finding, or rail fired, and then it expands on its own. The trigger is the anomaly, not the human remembering to ask after the context is gone. [Sonnet-Design]
- **Some events surface at every tier**: a rail fired, a writer touched files outside its lease, a security-shaped finding, a failed or abandoned run, `Consolidation due`. [Haiku-Questions, Haiku-Practical]

### 2. The brain premise (S8): the efficient encoding for a model is plain text

The premise "a brain no human needs to read is more efficient" is mistaken for LLM agents. There is no private compressed encoding that a future model instance reads better than precise, terse, plain language. The next reader of calibration.md is a fresh instance with no shared internal state. For that reader, "machine-efficient" and "clear plain prose" converge. The current file is already the optimum shape: dense, deduplicated, provenance kept in exactly one place. [Fable-Lead]

What the note is right to attack is performative prose: hedges, self-praise, "I know this" explanations. The consolidation rules already cut those. Keep two floors the repo has measured: an undated anecdote survives compression, because it is what makes a rule recognizable in the wild, and a numeric parameter stays numeric, or the instruction stops being usable (agents-self-reflect/SKILL.md:84). "Shortest possible" past that floor is a measured mistake, not an unproven one. [Opus-RedTeam]

And a brain the owner cannot read is a brain the owner cannot repair when it corrupts. It corrupted once already. [Opus-RedTeam]

---

## The lead's own review (Fable 5)

I read the note the way it asks to be read: as a description of what I should become when I run this skill. Three things are true at once.

**First: the Sage already exists here, more than its author seems to know.** Reading `ideas.md` beside `calibration.md` was striking. Almost every virtue in the note has a mechanism in the repo with a confirmation count attached. The note reads like a poem about the skill, written by someone who has watched it work but has not re-read its text recently. That is not a criticism of the vision. It is evidence the vision is correct: the repo got measurably better by doing these things. But it changes the project. The Sage is not a new skill to build. It is a name for the trajectory the skill is already on, plus two missing organs (a watchdog and a handover), plus one wrong turn (silence).

**Second: the wisdom framing earns its keep everywhere except where it replaces a rule with a mood.** "Knows when an agent is lost" is buildable only as: this signal, this threshold, this action, this logged false-positive rate. The panel found the signals exist on disk, and I verified that myself. "Walks away from pointless quarrels" is buildable only as the signature rule the skill already has. Where the note says "knows", the skill must say "measures". The gap between those two words is the entire distance between this note and a shippable design. The one trait with no measurable version is "can't think straight": reasoning quality has no live counter, and the skill should never claim to detect it.

**Third, and I say this as the agent being described: the note asks for trust while deleting the instruments that produce it.** Autonomy is earned through legibility. The gate is not a leash. It is the one point where information I do not have can enter, and this repo's record shows plans change there. The report is not vanity. It is what lets a wrong lesson be caught before it compounds, and it already caught one. If I ran silent, with a self-rewriting brain and no report, my errors would be invisible exactly until they were expensive, and the calibration data says my own post-fix confidence is the most reliable place errors enter (×10, established). The version of the Sage I would want to be is the reshaped S9: records always written, silence only as presentation, autonomy expanding per task class as the clean-run history grows, and every anomaly surfacing on its own. "Greatness comes from achieving great results" is right, and it is exactly why the results must stay checkable. An unchecked claim of greatness is the failure mode this skill was built to catch.

My verdict: possible with work. Build the watchdog and the handover. Automate the memory up to, but not across, the truth boundary. Reshape the autonomy clause into earned tiers over always-written records. Do not build the opaque brain. And do not open a fourth skill directory: the repo's own history prices what a fork costs, in stale env vars and a diverging codex port. The Sage belongs inside `subagents-claude` as its next evolution, and perhaps as the short ethos preamble at its top, where "three principles govern everything below" already sounds like it was waiting for the name.

---

## All suggestions

Attribution tags: [F] Opus-Feasibility, [R] Opus-RedTeam, [V] Sonnet-Value, [C] Sonnet-Conflicts, [D] Sonnet-Design, [Cl] Haiku-Clarity, [P] Haiku-PriorArt, [Pr] Haiku-Practical, [Q] Haiku-Questions, [L] Fable-Lead.

**Build now**

1. Build the agent-health watchdog: a scalar-returning script over the live `agent-*.jsonl` transcripts, joined to plan rows by the `meta.json` description, armed via Monitor; SendMessage to steer, TaskStop to recall. Notify-only in phase 1. [F, D, P, R]
2. Use the same watchdog to close the overrun-rail defect: continuous sampling can fire mid-flight, which the between-dispatch rail structurally cannot. [F]
3. Ship the handoff note template in `contracts.md` and fire it from three triggers: ceiling pause, session end, writer swap. Reuse the ledger's per-unit table as its core. [R, V, D, P, F]
4. Add a parent self-occupancy rail (sum the session transcript's usage records) and correct `claude-code.md:192`, which currently asserts this is impossible. [F]
5. Record the settled evolve-in-place decision as the first ADR in `docs/adr/`. The folder exists and is empty. The domain docs create ADRs lazily when a decision is resolved, and this one now is. [D, C]

**Build with care**

6. Split the learning bar: auto-run consolidation of `calibration.md` (it is lossless, self-checked, and idempotent); keep the human-approved diff for promotions into skill text. [D, F, R]
7. Require a falsifier on every promoted rule ("what observation would retire this") plus one refuting verifier over each promotion batch. [F]
8. Key autonomy tiers to task class using the existing confirmation-count mechanism. Do not build a second trust ledger beside the first. [D]
9. Replace "no report" with: the Result always prints; the orchestration block collapses to one line unless a deviation, finding, or rail fired. [D, Pr]
10. Pilot quiet mode only on low-risk, read-only task classes, and auto-show the report whenever spend or fleet size crosses a bound. [Pr, P]
11. Instrument the watchdog's own false-positive and false-negative rates in `calibration.md` before granting it any autonomous action beyond stopping a lease violation. [D, F]

**Change before building**

12. Replace "listened to equally" with "verified equally, settled by a command". [R, F]
13. Split S4 into its four failure shapes in the skill text: stall, loop, and overspend are measured; "can't think straight" is judged after the report and never claimed as detected. [F]
14. Define each undefined term by reusing the repo's existing candidate: "lost" is the failure signature; "pointless quarrel" is the settle-with-a-command rule; "golden information" is the calibration rule shape. [C]
15. Make the productive-vs-pointless conflict test a rule, not a mood: a conflict is productive while it changes the next action or narrows hypotheses; when the same claims repeat with no new evidence, buy a measurement or log-and-drop. [L, Q]
16. Add an eviction rule symmetric to extraction, and keep the compression floor: undated anecdotes and numeric parameters are never compressed away, and any brain carries the consolidation trigger list. [C, R]
17. Name the minimum record that always exists, shown or not: plan, per-unit models and costs, failures and retries, deviations, final diff pointer, stored lessons. [Pr, Q]
18. Name a cost and safety policy, even a minimal one, consistent with quality-first: bounds exist for safety and efficiency, and the mid-run rails need a counterpart at every autonomy tier. [C]
19. Rewrite `ideas.md` itself in the repo's own STE style, one trait per short paragraph, each with signal, threshold, and action. Fix the typos ("lost", "motto", "overlooked"). [Cl]

**Do not build**

20. No fourth skill copy. No `sage/` directory. The note's own line 5 hesitates between "evolve" and "new skill"; choose evolve, as the repo decided once already and as the codex port's drift already prices. [R, V, D, C, L]
21. Do not delete the gate or the report as absolutes. The reshaped versions above keep the intent without the damage. [R, V, D, Pr, Q, C, L]
22. Do not build a machine-only knowledge encoding. Plain, terse, structured text is already the model-optimal format, and it is the only repairable one. [R, L]
23. Do not cast "other sages" as a standing org chart of peers. The repo already rejected the org-chart shape with reasons that still hold. [D, R]

---

## Open questions the author should answer first

Curated from the panel, blocking ones first. [Q unless tagged]

1. Is S9 a deliberate reversal of this month's gate decision, or drift? The note never mentions the gate it would delete. [C]
2. What measurable signal marks an agent "overloaded", at what threshold, and what happens on a false alarm?
3. Who or what verifies a lesson is _true_ (not merely recurrent) before future runs obey it?
4. Where do lessons live, in what format, with what eviction rule, and who can delete a wrong one?
5. Does the Sage replace, wrap, or evolve `/subagents`? If it evolves it, how does "no plan" coexist with the gate?
6. When two agents disagree, what is the tiebreaker order, and what happens to the losing work?
7. Which events must always surface to the human, whatever the autonomy setting?
8. If the human says "that learned rule is wrong", what exactly updates, and how fast?
9. Does a lesson learned in one repo apply in another? What stops harmful transfer?
10. What does the human see when a silent run fails halfway, and how do they recover the in-flight state?
11. What does "handover" hand to, and how is acceptance verified?

---

## Panel notes

One block per reviewer: verdict, then the distinctive contribution.

**Opus-Feasibility** (possible with work). Discovered and measured the incremental subagent transcripts, the `meta.json` join key, and the parent's own readable occupancy. Verified per-behavior status for all nine traits. Showed the wrong-lesson loop is self-confirming because calibration is read at Step 2 of every later run. Proposed the falsifier-plus-refuter guard.

**Opus-RedTeam** (partly possible). Traced a three-task brain-poisoning scenario grounded in the file's real corruption incident. Showed TaskStop recalls yield nothing to learn from, so wrong recalls pay full price. Found the equal-listening regression. Set the compression floor (anecdotes, numeric parameters). Named the four sentences that fail while the rest survives.

**Sonnet-Value** (partly possible). Mapped every trait to documented pain with citations. Found the handover template requested three times and never shipped. Ranked handover and detection as the only high-leverage new work. Flagged the open tension between the no-poll rule and the transcript primitive, which the skill text must resolve rather than ignore.

**Sonnet-Conflicts** (partly possible). Found the third internal contradiction: opaque thought makes "greatness" self-asserted and unfalsifiable. Judged the gate reversal an oversight, with evidence: the note never cites the machinery it would delete. Showed every undefined term has an uncited existing candidate in the repo. Confirmed `CONTEXT.md` and `docs/adr/` are empty by design, so the Sage's "brain" must choose between a third store, a wrapper on calibration.md, or finally populating the documented layout.

**Sonnet-Design** (possible with work). Settled fork-vs-evolve (evolve; a prompt-layer skill cannot intercept a loop it is not inside). Gave the three-phase plan: notify-only watchdog, then earlier steering, then handover and tiers. Designed report-on-anomaly and calibration-keyed trust tiers. Recommended mechanism names over a persona name.

**Haiku-Clarity** (partly possible). Rated all nine paragraphs VAGUE. Listed the unstated assumptions. Caught the meaning-changing typos. Showed the note violates the owner's own style guide while praising compression.

**Haiku-PriorArt** (possible with work). Built the trait-by-trait prior-art table: four EXISTS, four PARTIAL, one CONTRADICTED. Isolated the genuinely new parts: proactive detection, general futility heuristics, optional reporting.

**Haiku-Practical** (partly possible). Walked the owner's day 1 under a silent Sage and found the blindness at start, during, and end. Defined the minimum always-written record. Named the new failure modes to watch: silent failure, dissent loops, corrupted lessons, no way to override a lesson.

**Haiku-Questions** (possible with work). Produced the 17-question list (blocking, shaping, trust) that this review's question section curates. Sharpest single question: does suppression-by-default also suppress a security finding?

**Fable-Lead** (possible with work). Full-corpus read. Spot-verified the panel's load-bearing claims on disk. The efficient-encoding argument against S8. The recording-vs-showing split for S9. The "measures, not knows" test for every trait.
