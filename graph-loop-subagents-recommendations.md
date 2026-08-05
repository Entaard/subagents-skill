# Combining graph and loop engineering to deepen the subagents skill

*Written 2026-08-04, against the current `subagents` skill (SKILL.md + contracts.md + patterns.md + claude-code.md). Companion documents: `graph-engineering.md`, `loop-engineering.md`.*

## Diagnosis: you already wrote a graph. It's missing its loops.

Grade the current skill against the graph framing and it scores well, mostly without using the vocabulary:

| Graph primitive | Where the skill already has it |
| --- | --- |
| Nodes | Steps 0–7; the per-agent rows in the Orchestration Plan |
| Typed state | The contracts — plan, brief, report, finding schema, ledger |
| Edges / conditional routing | The failure ladder; barrier-vs-pipeline choice in Step 2 |
| Checkpointing | The snapshot protocol: baseline → lease → stabilize → **freeze** |
| Single-writer discipline | "One writer per working tree" |
| Capability scoping | `Allowed writes` per brief; named model per plan row |
| Subgraph isolation | `isolation: worktree`; agents start blank |

That single-writer rule is worth noting: it is the same conclusion Cognition reached from production evidence — *"multi-agent systems work best when writes stay single-threaded and the additional agents contribute intelligence rather than actions."* You got there independently.

Now grade it against the loop framing, and the picture inverts. Of LangChain's four stacked loops:

1. **Agent loop** — present (each subagent runs one).
2. **Verification loop** — present and well-designed (freeze → review → triage → fix → targeted verification).
3. **Event-driven loop** — out of scope, correctly.
4. **Hill-climbing loop** — **entirely absent.**

The skill runs Steps 0→7 once and stops. Its only internal loops are attempt-counters (3 fix rounds, 1 review pass + 1 fix-verification pass), and its stop rule actively argues against iterating. Nothing it learns in one run reaches the next one.

**So: don't rebuild the graph. Add the loops it's missing.** Every source in the research converges on the same non-dichotomy — graphs contain loops, loops don't replace graphs — and the cheap move on a good graph is adding loops, not re-architecting.

## Seven concrete gaps

### 1. The calibration data is generated and thrown away

Step 7 requires "actual cost vs. estimate." `contracts.md` says the token bands "are coarse; report actuals afterward and calibrate." Calibrate *what*, against *what*? There is no artifact. The Defaults table says "edit this block to tune the skill" — a manual hill-climbing loop with no data feeding it.

**This run is the proof.** `contracts.md` estimates exploration at 15–40k tokens. The five research agents actually spent 72k, 89k, 77k, 122k, and 91k — 451k total against a 310k estimate. The band is off by 2–3× for web research that fetches primary sources, and nothing in the skill would ever discover that.

**Change:** a persistent `calibration.md` beside the skill. Step 7 appends one line per run — task class, agent count, estimated vs actual tokens, wall clock. Step 3 reads it before estimating. Ten lines of skill text; it is the entire missing Loop 4.

```
| date | task class | agents | est | actual | note |
| 2026-08-04 | web research sweep, primary sources | 5 | 225k | 451k | fetch-heavy research = 70-120k/agent, not 30-50k |
```

### 2. The stop rule counts attempts instead of detecting non-progress

Current: *"3 max: steer once → escalate tier once → take inline or ask"* and *"If the same failure survives two fix attempts, stop patching."*

Loop engineering's convergent finding is that counters are the wrong instrument. Detect stalls by **fingerprinting consecutive tool-call or finding signatures**, then escalate. The distinction matters: two attempts failing *differently* is progress — you are learning the shape of the problem, and the third rung is worth spending. Two attempts failing *identically* means the feedback path isn't bounded, and the third rung is waste. The infinite-loop study's root cause was exactly this: *"the feedback path is not effectively bounded."*

**Change:** replace the counter with a signature check.

> Failure ladder per unit: steer once → escalate one tier → take inline or ask. **Before spending a rung, compare the new failure's signature (same file, same symbol, same error class) against the previous one. Identical signature means the loop is stuck: skip the remaining rungs and escalate now. Different signatures mean the unit is making progress; spend the rung.**

### 3. Decomposition is sized by work, not by context boundary

Step 2 says to split by independence and to size units so an agent finishes in one focused session. That is decomposition by *work volume*. Two sources point somewhere sharper:

- Anthropic's newer multi-agent guidance: decompose by **context boundary, not by problem type**. Splitting one task into sequential phases creates "telephone game" handoffs that lose fidelity at every hop.
- Prefect: put a boundary **wherever you want to reason about progress, intervene, or interject programmatic logic** — a ten-step workflow does not need ten nodes.

The current heuristic can produce exactly the telephone-game failure the skill never warns about.

**Change:** add to Step 2 — *"Split where context must not cross, and where you'd want to inspect or intervene. Do not split one task into sequential phases handed agent-to-agent: each handoff loses fidelity, and phases of the same task usually belong to one agent."*

### 4. The cost baseline is the wrong denominator

SKILL.md opens with: *"a subagent costs roughly 4× a direct turn, and a full multi-agent run costs roughly 15× a plain chat answer."* Both figures are Anthropic's and cited correctly — but **both are measured against a chat baseline**, and that is not the decision the parent faces at Step 1. The real question is always *delegate, or do this inline as one agent?*

Anthropic's newer, more conservative figure for that comparison is **3–10× tokens for multi-agent versus single-agent on equivalent tasks**. Quoting 15× against chat makes delegation look several times more expensive than its actual marginal cost, which biases the gate toward solo in precisely the cases where fan-out pays.

**Change:** one line. *"A subagent costs ~4× a direct turn; fanning out costs ~3–10× what one agent would spend on the same task. That multiplier — not the 15× chat comparison — is the one the gate is deciding about."*

### 5. Rows name a model but not a tool scope

The plan table names the model per row, and briefs name `Allowed writes`. Neither names **which tools the agent may use** — network access, bash, MCP servers.

Per-node capability scoping is the one thing a monolithic loop structurally cannot do, and Prefect's framing is the memorable one: it prevents "handing the agent a bazooka." Your plan table is already a node table; it is one field away from having this.

**Change:** add `Allowed tools` to the brief contract, and make read-only reviewers explicit — a reviewer with network write access is not read-only in any meaningful sense, whatever the role line says.

### 6. Verification doesn't exploit clean context or model diversity

Two findings the skill gets partial credit for:

- **Clean context is the mechanism, not the agent count.** Cognition's production reviewer catches ~2 bugs per PR, 58% rated severe, specifically because it is given a *clean* context rather than inheriting the coder's session. The skill already forbids passing conversation history ("Inputs: file paths, never conversation history") — so it gets this right, but by rule rather than by reason. Naming the reason protects the rule: it tells you never to "help" a reviewer by pasting the writer's rationale.
- **Model diversity is not covered at all.** Self-preference bias is documented: models rate their own family's output higher. The tier table routes reviewers to frontier, which usually means the *same* model the parent and writer used.

**Change:** in Step 6 — *"On high-stakes findings, vary the model across maker and checker, not just the instance. A reviewer from the same family as the writer skews positive."*

### 7. Nothing distinguishes "the topology helped" from "we spent more"

This is the deepest gap, and it goes to the skill's premise.

Anthropic's own data: on their research eval, **token usage alone explains 80% of the variance in outcomes.** And a methodological paper argues much of the reported coordination gain across the multi-agent literature may be statistically indistinguishable from noise, because benchmarks compare coordinated multi-agent systems against *single*-agent baselines rather than against deliberately *un*coordinated multi-agent ones.

Step 7 reports cost and outcome. It never asks whether the orchestration did anything a single agent with the same budget wouldn't have.

**Change:** one line in the Orchestration Report.

> `Coordination check:` did any result depend on agents being independent — two reports disagreeing, one refuting another, a finding only visible by comparing angles? Or would one agent with the same token budget plausibly have found the same things?

It costs a sentence, and it is the only line in the skill capable of falsifying its own premise. Note for honesty: on *this* run, it partly would have. Five parallel researchers mostly covered disjoint ground — but the one genuinely coordination-dependent result was the parent catching that a subagent's characterization of a named person was wrong, which required an independent check rather than a wider sweep.

## The three loops to add

1. **Hill-climbing loop (across tasks)** — gap 1. The calibration file. Highest value per line of any change here, because it is the only one that improves the skill automatically.
2. **Progress-detection loop (within a unit)** — gap 2. Signature comparison replacing attempt counting.
3. **Coverage loop (within a task)** — and here the skill contradicts itself. `patterns.md` pattern 5 is loop-until-dry, with the correct rule ("stop after 2 consecutive dry rounds"). SKILL.md's stop rule says *"More review rounds are not more quality."* Both are right about different things and the skill doesn't distinguish them.

   **Resolve it:** *re-reviewing the same artifact* has sharply diminishing returns — bound it, as the stop rule does. *Sweeping for unknown-size discovery* is a different activity that terminates on dry rounds, not on a count. Say which one the stop rule governs, or the guidance reads as forbidding pattern 5.

## Would a genuinely "deeper" skill be better?

Two real options, with honest verdicts.

### Option A — saved agent files, to make effort reachable

**Recommended.** The tier table in Step 4 has a "Target effort" column, and `claude-code.md` concedes effort is settable in exactly two places: agent-file frontmatter, and the Workflow tool. On a plain dispatch it is unreachable — which is why every row of this run's plan honestly read `— (no control)`. **The skill ships a column it cannot fill.**

Two saved agent files fix that: a low-effort explorer and a high-effort verifier. The skill's own caution is not to create custom roles until they've stabilized across real tasks — and these two have the strongest claim of any: both are named roles in the brief contract's `Role:` line, and reader-shaped and verifier-shaped units recur across most of the nine patterns. This converts an acknowledged dead column into a working control, and it is the smallest change with the largest capability gain.

### Option B — the Workflow tool as an execution backend

This is the literal graph-engineering upgrade, and the primitives line up almost suspiciously well: `pipeline()` is per-item flow, `parallel()` is a barrier, `budget.remaining()` is a real spend rail rather than a prose one, and `resumeFromRunId` is an actual checkpointer with a cached-prefix replay — the thing your ledger approximates in markdown.

**But not as the default.** Three reasons: it requires explicit per-invocation opt-in, so it can never be the standard path; a script cannot be steered mid-run, and the skill's failure ladder depends on steering an existing agent; and the bitter lesson applies most sharply to the most hand-authored structure.

**Verdict:** offer it at Step 3 as an optional backend for *pipeline-shaped* work — migrations, sweeps over many known items, anything with a discovered work-list and a uniform per-item transform. Keep manual dispatch as the default for everything else. One paragraph in the skill, not a rewrite.

## What to delete

Adding to this skill is not free. It is prose loaded into context at invocation, so every line you add is context the task doesn't get. My recommendations above add roughly 40–60 lines; budget for it.

The clearest candidate for removal: `patterns.md` carries a substantial game-development evidence menu, in a parenthetical that tells *itself* to stay generic — *"(Engine-specific review lenses... belong in a separate project-level reference; keep this skill generic.)"* The block violates its own note. Move it to a project-level reference and the additions above are close to free.

## The caution worth taking seriously

Both research strands warn against precisely what you asked for.

- **"Loopmaxxing"** — the belief that more iterations eventually produce correctness. The structural equivalent is believing more procedure produces better orchestration.
- **The bitter lesson** — *"Add structures needed for the given level of compute and data available. Remove them later."* Lance Martin's case study is a team **removing** orchestrator-worker structure as models improved and scoring better with less of it.
- **"90-day artifacts"** — the argument that harnesses should be treated as disposable, not as products.

Your skill already states the discipline that answers this: *"Zero subagents is a valid outcome."* The same test applies to the skill itself. **Every recommendation above is anchored to a specific documented or observed failure** — a wrong estimate band, an unreachable column, a wrong denominator, a self-contradiction between two files. I would reject any proposal that isn't, including ones that sound sophisticated.

**But the bitter lesson does not get the last word, and the counter-evidence is unusually good.** The [MAST failure taxonomy (arXiv:2503.13657, NeurIPS 2025)](https://arxiv.org/abs/2503.13657) annotated 1,600+ traces across seven multi-agent frameworks and found failures distribute as **41.8% specification issues** (poor task and role design), **36.9% inter-agent misalignment**, and **21.3% inadequate verification**. Its conclusion states the point directly: *"many MAS failures arose from the challenges in organizational design and agent coordination rather than the limitations of individual agents."* MAST also found that systems with explicit verifier roles fail less — though not enough on their own, since one such system still managed only 33% correctness on simple tasks.

If four in ten failures come from bad specification, then better models do not dissolve the need for structure the way the strong bitter-lesson reading predicts — because a sharper model still cannot infer a boundary nobody wrote down. And notice which structure MAST vindicates: **specification quality is the single largest failure category, and the brief contract is exactly the artifact that addresses it.** That is evidence for the contracts, not for the procedure.

And the sharpest form of the bitter lesson, applied to this specific artifact: the skill is prose read by a model, and its structure exists to compensate for the model not already knowing how to orchestrate. As that changes, the parts most at risk of becoming dead weight are the most procedural — the step-by-step state machine. The parts most likely to keep their value are the **contracts** (a falsifiable brief, a required report shape, a finding schema with forced triage) and the **discipline** (the hard gate, the ledger, one writer per tree). Those encode judgment that doesn't get cheaper as models improve.

**Invest in contracts. Hold procedure loosely.**

## Suggested sequence

| # | Change | Effort | Why first |
| --- | --- | --- | --- |
| 1 | Calibration file + Step 7 append + Step 3 read | ~10 lines | The only change that compounds on its own |
| 2 | Fix the cost denominator | 1 line | Wrong number at the gate distorts every delegation decision |
| 3 | Signature-based stall detection | ~3 lines | Stops the most expensive failure mode |
| 4 | Two saved agent files (explorer, verifier) | 2 small files | Makes an already-shipped column real |
| 5 | Context-boundary decomposition rule | ~2 lines | Prevents telephone-game handoffs |
| 6 | `Coordination check:` in the report | 1 line | The only self-falsifying line in the skill |
| 7 | `Allowed tools` in the brief | 1 field | Cheap, closes a real scoping hole |
| 8 | Resolve the loop-until-dry contradiction | ~2 lines | Two files currently disagree |
| 9 | Move the game-dev menu out | deletion | Pays for items 1–8 |
| 10 | Workflow backend paragraph | ~4 lines | Optional; only for pipeline-shaped work |

Items 1–3 are worth doing regardless. Item 4 is the largest capability unlock. Item 10 is the only one I'd genuinely argue about, and I'd argue for keeping it small.
