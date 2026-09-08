# Orchestration topologies

Policy owner: `policy.topologies`

Choose the smallest pattern that fits the risk and evidence need. Compose patterns only where their ownership and stopping conditions remain explicit.

## Independent sweep

Use for a broad question with genuinely independent subsystems, lenses, or source types. Give each reader a non-overlapping angle and tell it what peers cover. Synthesize citations and evidence; send conflicts to verification. Repeating one angle buys redundancy, while a disjoint angle buys coverage, so record which one the plan intends.

## Implement, review, fix

Use for one bounded mutation. For a substantial change, the root declares the baseline, an independent read-only worker captures it and reproduces the target, and the root accepts the evidence before one dedicated writer receives the lease. Run deterministic checks, freeze the candidate, obtain independent fixed-point Standards and Spec verdicts, triage at the root, return accepted fixes to one writer, then assign independent fix verification and re-freeze. Writer feedback checks are not acceptance. Continue blocker/major follow-up reviews until one dry round.

## Migration pipeline

Use for one transformation across many sites. First produce and spot-check the complete work list. Pipeline each item through transform and verification rather than waiting for a full wave. Parallel writers require isolated resources and a named integration order. Every skipped or failed item remains explicit, and a compose check rules on the whole result.

## Bake-off and judge panel

Use when picking the wrong approach is expensive. Produce independent attempts from declared, meaningfully different angles in isolated resources. Write scoring criteria before results return. Judges see candidates without authorship framing; the policy actor reads both scores and cross-angle convergence before synthesizing.

## Loop until dry

Use for unknown-size discovery. Run small batches with different find strategies and deduplicate against every seen finding, including rejected ones. Stop after two consecutive dry rounds or the admitted bound. Report `dry after N rounds`, never `found everything`.

## Adversarial verification

Use for high-stakes claims. Give at least two independent verifiers the claim and evidence pointers, not the finder's reasoning, and ask them to refute it or attack distinct failure surfaces. Uncertainty defaults to refutation. Prefer model-family diversity where effectively available and record the residual when it is not.

## Quarantined deep read

Use when a large corpus must be digested but the policy actor needs only conclusions. Partition by corpus boundary, return compact fact/evidence/gotcha distillations, and synthesize from those artifacts. The unit ends when its assigned corpus is accounted for, not when a token target is reached.

## Competing hypotheses

Use when anchoring is the principal risk. Give one independent unit each plausible hypothesis and require it to support its own while trying to falsify the alternatives. Adjudicate on reproductions and evidence quality.

## Completeness critic

Use near the end of a large run. A fresh reader asks only what is missing: an unswept angle, unsupported claim, unverified criterion, undispositioned finding, missing unit, or effect outside scope. Follow-ups close accepted gaps; unresolved items remain explicit.

## Blind acceptance suite

Use when a mutating plan has at least one checkable requirement that can be expressed without inventing behavior. Choose `none`, `light`, or `full` before implementation and record the deciding signal and criteria verbatim.

Signals, in precedence order: a high-risk trigger argues upward except behavior without a reliable oracle, which routes to human judgment; existing coverage argues downward; a one-sentence change argues downward; flake-prone criteria reduce `full` to `light` but never justify `none`. No mutation, no checkable criterion, or no independent author means `none`. A close call is an assumption.

The blind author sees observable requirements and criteria, not design or source. Each case carries an ID, criterion, steps, observable outcome, and evidence class. Ambiguity returns as a question. For `full`, compile only machine-verifiable cases against the built interface, show each non-preservation case fails on the baseline, then run it in the normal verification stage. A failing case becomes a finding for triage. The implementer never sees the suite; a fix brief carries the failed criterion and observed behavior.

## Pre-write plan critic

Use for high risk or a change to behavior-shaping guidance. Before mutation, a fresh critic tries to refute the plan's central justification from its evidence. This is distinct from the end-of-run completeness critic.

## Blind behavioral lens

Use when changing text intended to shape future actor behavior. Have a fresh actor perform the procedure on a sandboxed control corpus and changed corpus without seeing defect history or author intent. Run the control first.

One control observation that fails to reproduce the alleged baseline behavior is enough to stop the edit. Agreement between one sample per arm is not evidence of null effect and never licenses revert; a null claim requires a predeclared repeated-sample program, manual reading of matches, and variance reporting. The trial must perform the action named by the trigger. Materialize the control from the actual pre-change artifact. If the control reproduces the failure but one sample per arm agrees, record an unresolved question.

## Evidence menus

For software, use build, lint, type, focused and full tests as applicable; a runnable reproduction per bug; regression verification for accepted findings; performance measurement wherever a budget exists; and a diff-scope check. Execute installation or packaging behavior in a disposable environment when it affects the deliverable.

For research and writing, fetch every load-bearing source during the run, distinguish fetched content from snippets, surface conflicting sources, check recency against the run date, and use a completeness critic.

For data and analysis, state input and coverage counts, spot-check transformations against raw records, rederive quoted figures independently, and check visualizations against their underlying table.
