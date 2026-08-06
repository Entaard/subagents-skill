# Research: agent-orchestration best practice, 2026-08

Evidence gathered to review and optimize the `/subagents` skill. Four parallel readers, one wave,
2026-08-06. Every load-bearing claim below carries a URL and a fetch date, and claims that rest on a
**search snippet rather than a fetched page** are labelled — they are one grade weaker and were not
allowed to drive a change on their own.

**Method.** Four non-overlapping angles, launched as one batch: external *evidence* on when
multi-agent orchestration pays (A1); external *practice* on briefing, context and verification (A2);
Claude Code harness fact-check (B); and a blind critique of the skill corpus by a reviewer that never
saw the author's reasoning (C). Actual cost 236k tokens against a 300k estimate, ~8 min wall clock.

A fifth angle — reconciling the repo's six prior note files — was cut at plan time and covered by
grep instead. The prior rounds' own closing note ("series closed; next evidence comes from usage")
made re-reading them low-value.

---

## 1. When does multi-agent orchestration pay?

**The skill's headline cost figure was unsourced.** Its opening line claimed fanning out costs
"roughly 3–10× what one agent would spend on the same task". No source states that, as a range or
otherwise. The nearest real figures come from Anthropic's research-system post: *"agents typically
use about 4× more tokens than chat interactions, and multi-agent systems use about 15× more tokens
than chats."* Dividing gives ~3.75× multi-agent vs single-agent — close to the old range's floor, but
derived from two ratios rather than measured directly.
→ https://www.anthropic.com/engineering/multi-agent-research-system (fetched 2026-08-05)

The same post also sharpens a claim the skill stated vaguely: *"token usage by itself explains 80% of
the variance, with the number of tool calls and the model choice as the two other explanatory
factors"* (95% together). The skill said "most of the measured variance"; 80% is both stronger and
checkable.

**The strongest counter-position is Cognition's.** *"Actions carry implicit decisions, and
conflicting decisions carry bad results"* — their argument is that decision-making disperses across
agents and context cannot be shared thoroughly enough between them. They permit multi-agent only for
well-defined, decision-free subtasks, and name Claude Code's read-only investigative subagents as the
acceptable case.
→ https://cognition.com/blog/dont-build-multi-agents (fetched 2026-08-06)

The two sources are usually presented as opposed. They are not, quite: **both agree independence is
the precondition**, and disagree only on how often real tasks meet it. Anthropic treats open-ended
research as sufficiently decomposable; Cognition treats almost all build work as too coupled. That
distinction is what the skill's delegation gate already encodes, which is why the gate survived this
review unchanged.

**Failure taxonomy.** MAST (arXiv:2503.13657, NeurIPS 2025) annotated 1,600+ traces across seven
multi-agent frameworks. Sub-mode percentages were read directly from the HTML: reasoning-action
mismatch 13.2%, disobeying task specification 11.8%, incomplete verification 8.2%, task derailment
7.4%, conversation reset 2.2%.
→ https://arxiv.org/html/2503.13657 (fetched 2026-08-06; abstract at /abs/2503.13657 fetched
2026-08-05, PDF unparseable)

The headline three-category split often quoted as 41.8% specification
/ 36.9% inter-agent misalignment / 21.3% verification is **snippet-grade** here — the consolidated
table was not directly read this run, though the repo's earlier round reported the same figures
independently. Treat the ordering as sound and the exact percentages as approximate.

The durable point survives the hedge: **specification quality is the largest single failure
category** — bigger than model limitation. That is evidence for the skill's brief contract, not for
its procedure.

**Evidence for doing less.** Collected deliberately, because a research-driven review's natural
output is a longer skill:

- *"For many applications... optimizing single LLM calls with retrieval and in-context examples is
  usually enough"*; add agentic complexity *"only when it demonstrably improves outcomes."*
  → https://www.anthropic.com/engineering/building-effective-agents (fetched 2026-08-05)
- MAST's own headline: performance gains for multi-agent systems over single agents on popular
  benchmarks are often minimal.
- Cognition's whole thesis: single-threaded by default; multi-agent is the exception.

---

## 2. How to brief, hand off, and verify

**Briefing.** The closest thing to a documented checklist: *"the most useful specs are
self-contained: they name the files and interfaces involved, state what is out of scope, and end with
an end-to-end verification step,"* with under-specified prompts ("add tests for foo.py") shown as the
failure mode. This validates the skill's existing brief contract rather than changing it.
→ https://code.claude.com/docs/en/best-practices (fetched 2026-08-06)

**Report size.** The skill's "1–2k tokens returned" default looked arbitrary. It isn't: subagents
*"return only a condensed, distilled summary of [their] work (often 1,000-2,000 tokens)."*
→ https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents (pub 2025-09-29,
fetched 2026-08-06)

**Handoff — a real disagreement.** Anthropic's context-engineering position is distilled summaries.
LangGraph's default is the opposite: agents share a single message list, with an explicit opt-out to
private state (**snippet-grade** — the docs page would not render for the researcher). Cognition sits
with LangGraph on this and blames fragmented context for a concrete failure. The skill's rule ("hand
off via artifacts, never via transcript") follows Anthropic, and that is defensible for *readers and
reviewers*. It was under-specified for *coupled writers*, which is what changed — see improvements.

**Verification.** The richest seam, and it resolved a claim A1 could not find:

- *"A fresh context improves code review since Claude won't be biased toward code it just wrote"*
  and *"have a fresh model try to refute the result, so the agent doing the work isn't the one
  grading it."* The skill's clean-context principle and its adversarial-verification pattern were
  both previously asserted without a source.
  → https://code.claude.com/docs/en/best-practices (fetched 2026-08-06)
- **Reviewer-eagerness bias, which the skill did not cover at all:** *"A reviewer prompted to find
  gaps will usually report some, even when the work is sound, because that is what it was asked to
  do... Tell the reviewer to flag only gaps that affect correctness or the stated requirements."*
  And on acting on them: *"Chasing every finding leads to over-engineering."*
  → https://code.claude.com/docs/en/best-practices (fetched 2026-08-06; quotes re-verified
  independently by the adversarial reviewer)
- **Self-preference bias** is real and mechanistically explained: judges *"assign significantly
  higher evaluations to outputs with lower perplexity than human evaluators"* — familiarity-driven
  rather than identity-driven. A quantified figure ("up to 50% more likely" on rubric evaluation)
  surfaced **snippet-only** and was not shipped.
  → https://arxiv.org/abs/2410.21819 (abstract fetched 2026-08-06; submitted 2024-10-29, rev.
  2025-06-21)

**Structured output.** No fetched source recommends schemas blanket-style; Anthropic's tool-writing
article is explicitly empirical — *"there is no one-size-fits-all solution."* This tempered a change
that would otherwise have overclaimed.
→ https://www.anthropic.com/engineering/writing-tools-for-agents (pub 2025-09-11, fetched 2026-08-06)

**On pruning instructions** — the finding that justified the whole cut list: *"The over-specified
CLAUDE.md... Claude ignores half of it because important rules get lost in the noise. Fix: Ruthlessly
prune."* Over-specification does not merely waste context; it causes rules to be **ignored**. That
converts leanness from a budget into a correctness property.
→ https://code.claude.com/docs/en/best-practices (fetched 2026-08-06; quote independently
re-verified by the adversarial reviewer, since it carries more weight here than any other single
citation)

---

## 3. Harness fact-check

Verified against code.claude.com docs on 2026-08-06, local install v2.1.222. **The reference file was
substantially correct** — most of this run's value here was insurance, not correction.

Confirmed verbatim, no change needed: all three `/rewind` gaps (subagent edits, Bash-made changes,
external edits — *"edits a subagent applies land outside your session's checkpoints"*); the four-level
model precedence order; the `availableModels` silent skip-and-inherit; output scanning for
instruction-shaped content since v2.1.210; `SendMessage` retaining full history; `memory:
user|project|local`; `effort` levels `low|medium|high|xhigh|max` with model-dependent availability;
`disable-model-invocation`; and *"Explore and Plan are the only subagents that omit CLAUDE.md and git
status. There is no frontmatter field or per-agent setting to change which agents skip them."*

Corrections found: `manual` is an **alias** for `default` in `permissionMode`, not a peer value;
every env-var default carries a **version gate**, and spawn depth has already moved 5 → 1 → 3 across
releases; there is **no per-agent toggle for auto-delegation alone** (`permissions.deny:
["Agent(<name>)"]` is the only hard lever, and it blocks explicit dispatch too); and `maxTurns` is
documented to stop a unit but **nothing documents whether the caller learns the cap was the reason**.

One live observation: the harness's injection scanner **fired on the fact-checker's own report**,
matching `bypassPermissions` and `permissions.deny` — legitimate documented values quoted in context.
A false positive on the exact defense the skill describes, and a good demonstration of why reports are
read as data.

---

## 4. The skill reviewed against itself

A blind reviewer (opus, high effort, never shown the author's reasoning) read the five files against
Anthropic's own skill-authoring guidance and returned 15 findings plus a cut list. The four that
mattered are documented in `improvements-2026-08.md`. Two are worth repeating here because they are
generalizable failure modes:

- **An invoked-but-undefined rail.** "The wall-clock rail" appeared three times as the designated
  fallback when token counts aren't visible, and no wall-clock number existed anywhere in the corpus.
  A rule can be cited repeatedly and still never have been written.
- **A request phrased as a constraint.** "Reports are *capped* at 1–2k each" — nothing caps them. The
  skill has an entire discipline about distinguishing enforced constraints from brief-level requests,
  and had violated it in a line that was load-bearing for a topology decision.

Conformance to the authoring standard came back: length PASS (216 lines vs <500), reference ToCs not
required (all <300 lines), no-surprise PASS, explain-the-why SUBSTANTIAL PASS. The two PARTIALs —
description quality and reference read-triggers — were both fixed.

---

## Evidence quality and open questions

- Two named sources were never directly read: OpenAI's *A practical guide to building agents* (PDF
  unparseable, HTML mirror 403) and LangGraph's multi-agent docs (JS-rendered; archive.org blocked).
  Everything attributed to them is snippet-grade and none of it drove a change alone.
- MAST's consolidated category percentages remain snippet-grade across two independent research
  rounds. Worth one direct read if they are ever quoted in the skill itself.
- The quantified self-preference figure is unverified and deliberately unshipped.
- SKILL.md's frontmatter supports far more than this skill uses (`when_to_use`, `allowed-tools`,
  `model`, `effort`, `context`, `agent`, `hooks`, `paths`, `shell`). Field *semantics* were not
  established this run, so no frontmatter change was made on the strength of a field list.
