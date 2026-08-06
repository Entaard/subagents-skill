# Improvements to the /subagents skill — 2026-08-06

What changed, why, and what was deliberately **not** changed. Evidence and citations live in
`research-2026-08-agent-orchestration.md`. Findings are keyed to their source: **A1/A2** external
research, **B** harness fact-check, **C** blind critique of the corpus, **P** found by the parent
from in-context tool schemas.

**40 findings: 36 accepted, 3 rejected with evidence, 1 deferred.** Twelve of those came from the two
reviewers who read the finished change set, and **three of their findings were defects introduced by
this work rather than by the original skill** — see *What the review caught in my own fixes*, below.

| File | Before | After |
| --- | --- | --- |
| `SKILL.md` (loaded on every invocation) | 4,120 w / 224 ln | **4,111 w / 216 ln** |
| `description` (always in context) | 56 w | 54 w, changelog removed |
| `references/claude-code.md` (read at Step 3 on any orchestrating run) | 2,769 w | **3,204 w** |
| `references/contracts.md` | 1,608 w | 1,633 w |
| `references/patterns.md` | 929 w | 929 w |
| `claude-agents/web-researcher.md` | budget note quoting one run's average | self-contained, brief-style lesson |
| `calibration.md` (repo seed + local copy) | 7 seed rows | + this run's row and a split of the "fetch-heavy" band |

---

## Major fixes

### 1. The headline cost figure was unsourced (A1)

**Before:** *"a subagent costs roughly 4× a direct turn, and fanning out costs roughly **3–10× what
one agent would spend on the same task**."*

**After (final):** *"Anthropic's published telemetry puts agents at ~4× the tokens of a chat turn and
multi-agent systems at ~15×. Those are aggregates over mixed workloads, not a controlled same-task
comparison, so treat them as an order of magnitude rather than a conversion rate."*

No source states 3–10×. The figure sat in the skill's opening paragraph and anchors every delegation
decision the gate makes — a wrong denominator there distorts the whole procedure. The 4× figure was
also conflated: Anthropic measured agents against *chat*, not a subagent against a direct turn.

**This fix took two attempts, and the first was nearly as bad as the defect.** My first replacement
divided the two published ratios (15÷4≈3.75), rounded to "roughly 4× what one agent spends **on the
same task**", and stated it flatly. The adversarial reviewer refuted it: the ratios are aggregate
telemetry over different workloads, so dividing them compares incommensurable baselines; "on the same
task" appears in no source; and the sentence then contained two different "4×" figures, inviting a
reader to take both as one measurement. The research doc hedged the derivation and the skill did not —
which is laundering, not sourcing. The final wording gives the two measured numbers and refuses to
manufacture a third.

### 2. A rail invoked three times and defined nowhere (C2)

The corpus told the model to fall back on "the agent-count and wall-clock rails" when token counts
aren't visible — the common case — and never defined a wall-clock number anywhere.

**This one also took two attempts.** My first fix invented a flat "~45 min per task". The adversarial
reviewer checked it against `calibration.md`, where every recorded wall clock runs from under a minute
to ~25 minutes, and found no source for 45 anywhere — a number conjured to close a finding, then
printed in the Defaults table with the same authority as rails that trace to data. It would never have
fired.

**Final:** the rail is now relative to the plan's own printed estimate — *"or once the run passes the
plan's printed wall-clock estimate by ~25%"* — reusing the overrun rule the token rail already uses. No
invented constant, and it scales with the task instead of pretending all tasks are the same size.

### 3. A brief-level request described as an enforced cap (C3)

**Before:** *"the savings are small (reports are capped at 1–2k each)"* — nothing caps a subagent's
return size. The skill has a whole discipline about not confusing constraints with requests, and had
broken it in a line that argues the Workflow-vs-hand-batched tradeoff. If a runaway agent returns 15k,
the context-savings argument reverses.

**After:** reports are *asked* for at 1–2k, *"and nothing enforces it, so a runaway one is yours to
truncate on arrival."*

### 4. The nested-delegation claim was wrong in both directions (C4)

**Before:** *"the global spawn-depth cap is the sole enforcement"* of nested-delegation-off.

A cap of 3 **permits** two levels of nesting — it enforces nothing about a default of "off". And it
is not the sole mechanism: all three shipped agents carry a `tools:` allow-list with no Agent tool,
which is real, hard enforcement the text denied existed.

**After:** brief text only on a plain dispatch; a saved agent whose `tools:` omits the Agent tool
enforces it for real; the depth cap bounds runaway recursion rather than implementing "off".

### 5. "Never sequential phases" forbade two shipped patterns (C1)

*"Never slice one task into sequential phases handed agent-to-agent"* is absolute, and
implement→review→fix and the migration pipeline are exactly that. A model applying it literally would
refuse to dispatch a reviewer. Now scoped to *production* phases of one deliverable, with review and
verification named as the deliberate exception — they exist **because** the handoff drops the writer's
context.

---

## Additions (each paid for by a cut)

### 6. Reviewer-eagerness bias (A2)

New rule in Step 6: *"Reviewers report what you ask them to look for. One told to find gaps will find
some even when the work is sound... Scope the mandate to correctness and the stated criteria, and make
'no findings' an explicitly valid answer — otherwise you buy rework on defects that were never
there."*

Documented in Claude Code's best practices, and corroborated locally: `calibration.md` row 7 records a
checker overcounting a finding, 4 against a real 3.

### 7. Briefs must carry decisions, not just files (A1/Cognition, MAST)

Cognition's case is that subagents make conflicting *implicit* decisions when context is fragmented;
MAST's largest failure category is specification. The brief contract named files, boundaries and
output shape but never the decisions already taken. Now: *"an agent that wasn't told a decision will
make its own, and two units deciding differently is how coupled work fails."*

This is the narrow, defensible half of Cognition's position — see the rejection below for the half
that was not adopted.

### 8. Effort under a model override (C8)

The skill tells you to vary the model between maker and checker, and separately warns that overriding
a saved agent's model can invalidate its frontmatter `effort`. Both were true; nothing said which
wins. Now: write that row's Effort cell as **unverified** rather than claiming the file's level. This
run hit the problem directly — plan row 6 had to carry an asterisk.

### 9. `agent({schema})` — the one enforced return shape (P1, tempered by A2)

`references/claude-code.md` documented the Workflow backend without mentioning the option that makes a
return shape **binding** rather than requested. Added — with the hedge the evidence requires: response
format measurably affects performance and there is *"no one-size-fits-all solution"*, so impose a
schema where you need the guarantee, not everywhere.

---

## Harness corrections (B)

- `permissionMode`: `manual` is an **alias** for `default` (v2.1.200+), not a peer value.
- Limits table now carries a **`Since` column** and the drift history — spawn depth went 5 → 1 → 3
  across releases, which is the concrete argument for the file's own "verify at runtime" rule.
  Header updated to the verified date and local build (v2.1.222).
- `availableModels` fallback: the skip-and-inherit is documented verbatim; **"no notice" was an
  inference** and is now labelled as one.
- The `CLAUDE_CODE_SUBAGENT_MODEL` echo check no longer claims to convert the Model column *"from a
  hope into a fact"* — it catches the loud override only, so it buys a verified column, not a
  guaranteed one (C5).
- New: there is **no per-agent switch for auto-delegation alone**; `permissions.deny:
  ["Agent(<name>)"]` is the only hard lever and it blocks explicit dispatch too.
- New: `maxTurns` is documented to stop a unit, but nothing documents whether the caller learns the
  cap was the reason — so "treat it as blocked" is this skill's policy for an ambiguous signal, not a
  status the harness reports.
- New: Workflow scripts are JavaScript, and `Date.now()` / `new Date()` / `Math.random()` **throw**.
  A run that dies on line one costs the whole wave.

## Consistency and conformance fixes

- Sweep width was 4–8 in SKILL.md and 3–8 in patterns.md (C9) — unified to 4–8.
- The inline return-format list dropped `recommended next action`, a contract field (C10) — restored.
- Two spellings of the no-effort placeholder (C11) — unified to `— (no control)`.
- The Defaults row on report size now carries the exception for units that cannot write (C12).
- `contracts.md` had the corpus's one bare imperative with no reason attached; it now explains why a
  renamed field is worse than a trimmed one.
- The plan template's Budget line now has a slot for the calibration row backing the estimate — Step 3
  required citing one and the template had nowhere to put it.
- `references/contracts.md` was the only reference cited without a *when to read it* trigger; the
  References section now gives all four.
- **Description:** 17 of 56 always-in-context words were maintainer changelog ("Trigger phrases were
  removed along with auto-invocation..."). Replaced with a use-when clause, which the authoring
  standard asks for and this had lacked.

## Deletions

The **Anti-patterns section** (57 words) was removed entirely. All four items negated rules stated
earlier in the file — ritual fan-out is covered by the gate and "over-spawning is the classic failure
mode", reviewer consensus by Step 6's triage rule, silent model swaps by Step 5, and
keep-reviewing-until-perfect by the Stop rule. Anthropic's guidance flags exactly this shape
(restating rules as a rigid structure), and over-specification *causes rules to be ignored*.

Also cut: ~370 words of restatement across Steps 3–7, chiefly the `maxTurns` paragraph (duplicated in
full by `claude-code.md`, which Step 3 makes mandatory reading one step earlier) and the Workflow
backend material, which was spread across four sections in the body for a path that only applies at
≥8 units. The mechanics now live in the reference; the body keeps the decision and the tradeoff.

**On the word budget, honestly — corrected after review:** the acceptance criterion was "SKILL.md ≤
4,120 words *and* corpus not larger". SKILL.md passes. The corpus does not; it grew, almost entirely in
`references/claude-code.md`.

My first draft of this section defended that as progressive disclosure — body always loaded, references
on demand. **The compliance reviewer showed that defence is partly false.** SKILL.md Step 3 makes
`references/claude-code.md` *mandatory* reading before drafting any plan, so on every run that actually
orchestrates it is always-loaded too. Measured properly, always-loaded words **rose** by roughly 280 on
an orchestrating run rather than falling by 100.

The accurate statement of the trade: cost moved off the *decline* path (a run that fails the gate at
Step 1 or 2 reads only SKILL.md, and that path did get cheaper) and onto the *orchestrate* path, which
got more expensive in exchange for correcting harness facts the skill uses to make promises to users.
That may still be the right trade. It is not the trade I originally claimed, and "references load on
demand" was a rationalisation about the one file that grew.

**Final measured position:** SKILL.md 4,120 → **4,111** (passes its rail, but only just — the fix round
put it *over* at 4,154 and three editorial asides had to come out to get back under). Corpus 9,426 →
**9,877**, a 451-word increase, all of it correcting or completing `references/claude-code.md`. The
honest summary is: **the body held its size and the reference grew.** If a future round wants the
corpus flat, `claude-code.md` is where to look, and it has never had a reviewed cut list — this run
only ever commissioned one for SKILL.md.

---

## Changes the first draft of this log failed to mention

The compliance reviewer found three hunks in the diff with no entry here at all. Documented now:

- **`claude-agents/web-researcher.md`** — the whole "Note for the parent" was rewritten, and the file
  was missing from the table above. It had told the parent to budget 70–120k per fetch-heavy agent,
  quoting one past run's average as if it were a constant — which `calibration.md` explicitly warns
  against, and which this run disproved twice over (13.7k and 33.7k, because the briefs named their
  URLs). See the cross-file defect below for the second half of this fix.
- **SKILL.md — the `verifier` exception** (from C7). The skill warns that *"an agent that can't write
  source but can still fetch URLs and run shell is not contained"*, and then ships a `verifier` with
  exactly that shape. Rather than pretend otherwise, the text now names it as the deliberate
  exception: verification has to run and check things, so the narrowing happens in the brief.
- **SKILL.md — previewing two `go` variants** (from C6). The gate said to attach the plan table to
  "the `go` option", but the backend block offers *two* `go` options and nothing said which. Now:
  preview each with what differs between them.

Also undocumented in the first draft, and both from the adversarial pass:

- **The "80% of the variance" edit.** I sharpened "most of the measured variance" into "80%" without
  logging it — and without carrying the scope. In the source that figure belongs to a specific
  analysis (Anthropic's research system, on BrowseComp); I had stated it as a general property of
  multi-agent outcomes. Making a number more precise while leaving it over-generalised makes it more
  wrong, not less. Now scoped to the analysis it came from.
- **A deleted rule that was not covered elsewhere.** I cut the Anti-patterns section claiming all four
  items were restated earlier. Three were. The fourth — treating reviewer *consensus or silence* as
  done — was not: `grep -n "consensus"` returned zero hits across the whole post-change corpus. The
  rule is restored in Step 6: *"Consensus is not evidence and silence is not a pass."* Notably the two
  reviewers **disagreed** here, one certifying the deletion safe and the other disproving it; one grep
  settled it, and the standard-tier reviewer was the correct one.

## A cross-file defect only a fresh install would hit

The rewritten `web-researcher.md` originally told the parent to "quote the **corrected band**" from
`calibration.md` and cited 14–62k. Those figures live in calibration rows 8–9 — which exist **only in
the local installed copy**. `install.sh` deliberately excludes `calibration.md` from its sync, so a
fresh install seeds the *repo* copy, whose rows say the opposite: *"Fetch-heavy web research runs
70–120k per agent."* The agent file pointed at data that does not ship, and contradicted data that
does.

Fixed in both directions: `web-researcher.md` now states the brief-style lesson self-containedly
instead of deferring to a band it cannot guarantee is present, and the repo's seed `calibration.md`
gained this run's row plus a note splitting "fetch-heavy" into *briefs that name their sources* versus
*briefs that must find them*.

This is the second consecutive run where the worst defect involved `install.sh` treating a file
specially. Row 7 of the calibration log records the first. The pattern is worth naming: **a reviewer
reading a diff cannot see what an installer does to it.**

## Smaller corrections from review

- Restored the sentence explaining that Workflow leading the option list is a consequence of reaching
  that block, not a recommendation — cutting it left the ordering reading as an endorsement.
- Restored *"No `Workflow` tool in this session → say so once and plan hand-batched"*, which had been
  cut along with the surrounding compression.
- `references/claude-code.md` still quoted the pre-change budget rail verbatim after the rail changed;
  the C2 fix had not swept for restatements.
- **New, and safety-relevant:** Workflow-spawned subagents *"always run in `acceptEdits`"* regardless
  of the session's permission mode, so file edits are auto-approved. Nothing in the corpus said this.
  A user approving "go — via Workflow" on a plan with a writer row is approving unattended edits, and
  now the plan has to tell them so. This was a pre-existing gap, not one introduced here.
- Four external claims in the research doc lacked a URL or fetch date, including the pruning quote the
  entire cut list rests on. All now carry both.

## Rejected, with reasons

**C13 — "Steps 1 and 2 decide against data loaded at Step 3."** Correct as an observation, wrong as a
fix. Requiring two reference reads *before* deciding whether to delegate at all would make the cheap
gate expensive, which is the over-process the evidence warns against (*"if you could describe the diff
in one sentence, skip the plan"*). Step 1's mention of calibration is a pointer, not a required read.
The ordering is deliberate; documented here so it is not re-flagged next round.

**P4 — "Workflow needs explicit opt-in" is over-tight.** The Workflow tool's own rule counts "the user
invoked a skill whose instructions tell you to call Workflow" as qualifying opt-in, so `/subagents`
technically already qualifies. Kept the stricter stance anyway: spending at fan-out scale should be
the user's explicit call, not one inherited from having typed a slash command.

**P2 — `fable` missing from the tier→model snapshot.** The resolution *procedure* already handles
unlisted models correctly ("the harness wins — place it by role... if you cannot tell, don't guess").
Adding a row for a model whose role is undetermined would violate the file's own rule.

**Cognition's full position — share complete traces between agents.** Adopted only its narrow half
(carry the decisions). Adopting the whole thing would contradict Anthropic's measured
context-engineering guidance and the skill's clean-context reviewer property, which is the mechanism
that produced this review's best findings. Recorded as a live disagreement between sources rather than
resolved by preference.

## Deferred

**SKILL.md frontmatter beyond what is used** (B-6). The field list is confirmed
(`when_to_use`, `allowed-tools`, `model`, `effort`, `context`, `agent`, `hooks`, `paths`, `shell`) but
the *semantics* were not established this run. Changing frontmatter on the strength of a field list is
how you ship a config that silently does nothing.

**Seeding `evals/evals.json`.** `skill-creator` ships a full eval harness, and several of this skill's
properties are objectively testable — "a single-file lookup yields 0 agents", "manual mode ends the
turn before spawning". Offered at plan time and not taken up. It remains the highest-value untaken
improvement, because every finding in this review is an argument from reading, not from measurement.

## Observed side-effect

`install.sh` backs up any shipped agent file whose installed copy differs, to protect a user's own
agent of the same name. It cannot distinguish that from a legitimate update, so this run left a
`web-researcher.md.bak` in `~/.claude/agents/`. Harmless — the loader reads `.md` — but every future
skill update will leave one.
