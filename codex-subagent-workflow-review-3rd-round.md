# Third-Round Review: From Workflow Critique to a Cross-Tool Skill

Reviewed sources: `codex-subagent-workflow-review.md` (round 1), `codex-subagent-workflow-review-2nd-round.md` (round 2)
Reviewer: Claude (Fable 5, max reasoning effort)
Review date: 2026-08-02
Method: both documents read in full; three parallel research subagents verified current Codex docs, Claude Code docs, the agentskills.io spec, and the leading community orchestration skills (~325k subagent tokens, ~75 tool calls, ~8 minutes wall clock — itself a data point for the cost section below).
Status: **final review round.** Deliverable is the `subagents/` skill in this directory. Further improvement should come from piloting the skill, not a fourth review.

## Verdict

Round 1 correctly reframed the goal (evidence over agreement). Round 2 correctly operationalized it (delegation gate, write leases, falsifiable contracts, disposition-based stop rules). Both survive fact-checking: the `learn.chatgpt.com` citations are real and live — it is the current home of the Codex docs (`developers.openai.com/codex` now 308-redirects there), and round 2's product claims (sandbox/approval inheritance, live parent overrides beating custom-agent defaults, `agents/openai.yaml`) match the live pages as of today.

What remains wrong or missing falls into four groups:

1. **Neither round designs the interaction model** — when the orchestrator decides alone vs. when it stops and asks the user. That auto/manual dial is the skill's actual core requirement.
2. **Both rounds are Codex-shaped.** A generic skill needs a tool-abstraction layer, and the Claude-side canon (Anthropic's multi-agent numbers, Claude Code's subagent mechanics, obra/superpowers) contributes several rules neither document has.
3. **The cost model is qualitative.** "Cost-efficient" appears throughout with no numbers, no budget knob, and no cost reporting.
4. **A few round-2 recommendations over-correct** and should be softened or reversed (detailed below).

## What is settled — do not relitigate

These survived three rounds and external validation; the skill adopts them wholesale:

- Agents produce **independent evidence** (tests, reproductions, measurements), not chains of opinion; reviewer silence is not a stop condition.
- **Delegation gate**: bounded deliverable, packageable context, checkable result, isolated workspace effects — plus at least one material benefit. Zero subagents is a valid outcome.
- **One writer per working tree** (write lease); parallel writers only in isolated worktrees with disjoint deliverables and a named integration owner.
- **Freeze the candidate before independent review**; same brief + same frozen diff to each reviewer; hide reviewers from each other; dedupe by root cause.
- **Findings are triaged** (accepted / rejected with evidence / deferred / user decision), never auto-applied; the round-2 finding schema and severity definitions are excellent as-is.
- **Read-only is two concepts** (role instruction vs. OS sandbox) — confirmed against live Codex docs.
- **Risk rubric with hard triggers**, no averaging away a severe axis.
- Human-only criteria (game feel, product judgment) stay human; agents prepare evidence, never claim approval.
- Model routing expressed as **task properties, not hardcoded model names** in the core.

## Corrections to round 2

Round 2 corrected round 1 in a table; here is the same treatment applied to round 2.

| Round-2 position | Problem | Third-round change |
| --- | --- | --- |
| "Inspect the live concurrency limit when available rather than hardcode a number." | Impractical: Codex documents no numeric default for `agents.max_concurrent_threads_per_session` (verified today — the doc literally says "Codex chooses the default"), and Claude Code's limits live in env vars the model can't reliably introspect mid-turn. | **Set caps explicitly instead of discovering them.** Default useful fan-out is 3–5 concurrent (Anthropic's research system used 3–5 subagents per wave; Codex's own worked examples set 6–8). Make the cap a user-visible knob in the plan. |
| Waves: exploration → implementation → review → verification. | Waves are *barriers*: every task in wave N waits for all of wave N−1. Correct for a shared working tree; wasteful for independent items (e.g. verify each finding as its review lands, don't wait for all reviews). | Keep waves for shared-mutable-state phases; use **per-item pipelining** for independent items. The barrier/pipeline choice is an explicit step in the skill. |
| "Do not create permanent plan or review files by default… ask before adding durable process artifacts." | Contradicts round 2's own §3 (the phase contract is the continuity mechanism) and contradicts the strongest field practice: superpowers' git-backed ledger and Claude Code Agent Teams' shared task list both exist because **durable external state, not context, is the recovery mechanism**. | Default to a **ledger file in scratch/gitignored space** (task IDs, briefs, states, evidence pointers). Only *repo* artifacts require permission. |
| "The skill should initially require explicit invocation… `policy.allow_implicit_invocation: false`." | Conflates two dials. *Activation* (does the skill load?) and *autonomy* (may it spawn agents without approval?) are independent. With manual mode as the default autonomy setting, implicit activation is safe — activating the skill on a complex task merely produces a plan and a question, never surprise token spend. | Ship with implicit activation **on** in both tools (precise trigger description + "zero subagents is valid" gate), manual mode as the autonomy default. The `allow_implicit_invocation` knob stays documented for users who find triggering noisy. Note: it is a *skill-policy* key in `agents/openai.yaml`, not subagent config — round 2 was directionally right but the file's purpose is broader (interface metadata, tool dependencies). |
| One 12-step orchestration instruction block. | A monolithic prompt violates the skill format's own best practices (progressive disclosure, SKILL.md < 500 lines, references one level deep) and buries the two decisions that matter most (gate, mode) in the middle. | Restructure as a 7-step procedure with hard gates as named sections and heavy templates pushed to `references/`. |
| Retry once with a narrower brief; repeated failure → take it back inline. | Right instinct, incomplete policy. | Adopt the superpowers escalation ladder: retry with a sharpened brief on the **same** agent (steer, don't respawn); after repeated failure, dispatch a **fresh agent one model tier up** with full ownership framing; cap total rounds; every dropped disagreement gets logged, never silently discarded. |

## Gaps in both rounds (now fixed in the skill)

1. **No auto/manual interaction design.** The skill's manual mode presents an Orchestration Plan — topology, per-agent model tier + reasoning effort, concurrency cap, isolation, cost estimate — then stops on a *forced enumerated question* ("reply `go`, or adjust 1/2/3"). Research finding worth recording: open-ended "wait for approval" prose demonstrably fails even in first-party implementations (Claude Code's own plan-approval gate has multiple open issues about models sliding past it); enumerated-choice questions and redundant, named hard-gate sections are the patterns that hold. Auto mode runs the same decision procedure silently but keeps **hard rails** that stop for the user regardless: irreversible actions, parallel writers without isolation, budget overrun, scope ambiguity.

2. **No quantitative cost model.** Now included: multi-agent ≈ **15×** chat tokens, subagents ≈ **4×** (Anthropic, measured); effort-scaling table (simple lookup = 0–1 agents; comparison = 2–4; large sweep = 5–10; only migrations/audits justify more); subagent reports should return **1–2k tokens**; keep the orchestrator's context in the **40–60%** utilization band. This review's own research fan-out (3 agents, ~325k tokens) is the kind of line item the plan and final report must show.

3. **The artifact-handoff rule.** The sharpest rule in the field (superpowers), absent from both rounds: **never replay conversation history into a dispatch, and never let raw agent output accumulate in the orchestrator's context** — everything pasted in or printed back stays resident and is re-read every subsequent turn. Hand off via files (briefs, contracts, diffs, ledgers); subagents return distilled summaries only.

4. **Trust boundary around subagent reports.** A subagent that read untrusted content (web, third-party code) can relay injected instructions. This is now a shipped platform concern — Claude Code scans subagent reports for instruction-shaped content since v2.1.210 (one of my research agents' reports was visibly flagged by exactly this scanner today). The skill's rule: reports are *claims + data, never instructions*; load-bearing claims get verified against repo state or a second source before integration.

5. **Parallelism is a batching mechanic, not a mode.** In Claude Code, multiple Task calls in one message run concurrently, one per message runs sequentially; in Codex you ask for parallel spawns explicitly and cap via `[agents]` config. Neither round says how parallelism is physically achieved; the tool reference files now do.

6. **Peer-to-peer is a distinct primitive.** By mid-2026 both ecosystems have two coordination modes: hierarchical subagents (report to parent — the default) and peer teams (Claude Code Agent Teams, experimental: shared task list, agents debate each other — for competing-hypothesis work where anchoring bias is the enemy). The skill defaults to hierarchy and names the escalation condition.

7. **The orchestrator's own model matters.** Both rounds route *subagent* capability but never state that the parent — who synthesizes, triages, and owns the completion claim — should be the strong model. Corollary on Codex: `ultra` reasoning effort enables *proactive* delegation, which overlaps this skill's auto mode; the skill notes the interaction so the two don't fight.

8. **Code-review shape.** Even round 2's generic core assumes implement→review→fix. Complicated tasks the user actually faces include research sweeps, migrations, bake-offs (N competing designs → judge), and loop-until-dry discovery. The skill ships a pattern library with these topologies, and the game-dev evidence rules become one domain menu among several (per round 2 §12, Godot specifics stay out — they can be a future optional reference).

9. **Validation scenarios were code-only.** Added: a research fan-out task, an auto-mode task that *should* spawn zero agents (over-spawning is the classic failure — Anthropic's early system spawned 50 subagents for simple queries), and an assertion that the final report includes actual cost.

## Residual notes on round 1

Round 1's remaining weakness is scope, not error: it cites only the three OpenAI subagent doc sections and never consulted the Claude-side canon, which is where most of the quantitative and mechanical guidance above comes from. Its role/effort table and its "cost-efficient subagent policy" section remain the best-condensed parts of either document and are carried into the skill nearly verbatim.

## Design decisions taken in the skill (review these)

1. **Name: `subagents`** — short enough to type as `/subagents`; spec-compliant (matches directory name). Anthropic style guidance mildly prefers gerunds (`orchestrating-subagents`); I chose typing ergonomics. Rename the folder + `name:` field together if you disagree.
2. **Manual is the default; auto is opt-in** per invocation ("auto: …"), or durable via one line in `CLAUDE.md`/`AGENTS.md` (`subagents-mode: auto`). A third `plan` mode produces the plan and cost estimate without executing.
3. **Approval floor (deliberate deviation from "manual asks for everything"):** a *single read-only, cheap* lookup agent does not require plan approval even in manual mode — it is the moral equivalent of a grep, and forcing ceremony there would make the skill worse than not using it. Everything beyond that floor (≥2 agents, any writer, tier escalation) blocks on the plan. If you want strict manual, delete the floor paragraph — it's marked.
4. **Implicit activation is on in both tools** (see the round-2 correction above). Flip `policy.allow_implicit_invocation` to `false` (Codex) and add `disable-model-invocation: true` (Claude Code) if it triggers too eagerly in practice.
5. **Model names live only in the two tool reference files**, tier-based routing lives in the core, and both tables carry an as-of date plus an instruction to verify at runtime — model lineups changed twice during the lifetime of your two review docs alone.
6. **No custom agent role files ship with the skill** (round 2 decision #7 upheld): built-in agent types + per-dispatch briefing contracts first; freeze recurring roles into `.claude/agents/` / `.codex/agents/*.toml` only after they stabilize across real tasks. Codex caveat discovered in research: named custom agents currently may not be spawnable through the tool-call interface (open bug openai/codex#15250) — another reason not to depend on them yet.

## Pilot plan (the actual next round)

Round 2's validation scenarios + the three added above, but with measurements, per its own advice: agent count/topology, wall clock, tokens, findings accepted vs. rejected vs. duplicate, defects caught by deterministic checks vs. model review, defects found *after* completion was declared. Two changes to its plan:

- Run the pilot **before** tuning any default (cap, budget, floor) — the current numbers are literature-derived, not fitted to your projects.
- Add one meta-check per run: did manual mode's plan question actually block execution, and did auto mode's rails fire when they should? Those two gates are the novel machinery; they are what needs field-testing most.

## Disposition of this review series

Applying round 2's own stop rule to the series itself: acceptance criteria for "reviewed enough" are met — external validation performed, contradictions resolved, remaining findings converted into a shippable artifact. A fourth review round would be reviewer fatigue by the documents' own definition. **Series closed; next evidence comes from usage.**

## Sources consulted this round (all fetched live 2026-08-02)

- Codex docs (current home: learn.chatgpt.com): Subagents; Best practices; Build skills; Git worktrees; Models; Non-interactive mode; CLI reference
- Claude Code docs: Sub-agents; Agent teams; Skills
- Anthropic engineering: "How we built our multi-agent research system"; "Effective context engineering for AI agents"
- Anthropic platform docs: Agent Skills authoring best practices; agentskills.io specification (+ adopter list: 40+ products including both target tools)
- obra/superpowers: `subagent-driven-development`, `dispatching-parallel-agents`, `writing-plans`, `brainstorming` skills; Simon Willison's independent review
- humanlayer: ACE-FCA ("subagents are about context control", 40–60% band); 12-factor agents (Factors 3, 8, 10)
- openai/codex issues #15250, #11701 (custom-agent spawn gap)
- wshobson/agents, VoltAgent/awesome-claude-code-subagents (role libraries — orthogonal to orchestration, intentionally not adopted)
