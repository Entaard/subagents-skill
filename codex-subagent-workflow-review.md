# A Higher-Quality, Cost-Efficient Subagent Workflow for Game Development

## Current workflow

1. Use a near-highest-capability model at its highest reasoning effort to generate a detailed plan for making a specific game.
2. In a new session, assign subagents to implement one phase of that plan:
   - One subagent implements the phase.
   - One subagent reviews the implementation critically.
   - One subagent addresses the review feedback.
3. Repeat implementation and review until there is no more feedback, with a maximum of three rounds.
4. Use the highest-capability model with lower reasoning effort for these subagents.

## Executive assessment

The workflow has a strong core idea: construction and criticism are separated. Its main weakness is that it spends tokens in the wrong places and treats agent agreement as a quality signal.

“No more feedback” can mean genuine convergence, but it can also mean reviewer fatigue, shared blind spots, correlated reasoning, or increasingly trivial comments. It does not prove that the game phase is correct, maintainable, performant, or fun.

The workflow should instead use agents to produce independent evidence: tests, reproductions, acceptance criteria, profiling results, and playable demonstrations. Reviewer consensus should not control the loop.

## What should change

### 1. Do not use maximum reasoning for every initial plan

A very detailed plan created before implementation often becomes speculative. It can anchor later agents to incorrect architecture and encourage them to complete the document rather than respond to what the repository reveals.

Use the strongest model and highest reasoning effort only for genuinely expensive decisions, such as:

- Core architecture and data models
- Save compatibility and migrations
- Networking or deterministic simulation
- Performance-sensitive systems
- Changes that constrain many future phases

For ordinary gameplay phases, use a strong model at medium or high effort. Require it to inspect the repository first and produce:

- Acceptance criteria
- Non-goals
- Important constraints
- Risks and unresolved questions
- A verification strategy
- A small sequence of independently testable increments

Favor a short, executable plan over an exhaustive design. Each phase should produce a playable vertical increment.

### 2. Review the plan before reviewing the code

In the current workflow, the first independent challenge appears after implementation. Correcting a bad decomposition is much more expensive at that point.

Before implementation, ask one read-only agent to challenge only the risky assumptions:

> Find architectural assumptions, missing acceptance criteria, integration risks, and aspects of this plan that cannot be verified. Do not rewrite the plan wholesale.

Because this task is bounded and read-heavy, it can usually be performed with an efficient model.

### 3. Make implementation assignments smaller than an entire phase

“Implement a phase” is often insufficiently bounded. A phase might combine combat logic, animation, UI, persistence, audio, and content. That increases context pressure and makes verification vague.

Break a phase into increments that can be demonstrated independently, such as:

1. Domain and state logic
2. Runtime integration
3. Presentation and player feedback
4. Persistence
5. Tests and instrumentation

Keep one writing owner at a time. Parallel agents are most useful for exploration, tests, triage, and targeted review. Parallel write-heavy work creates conflicts and coordination overhead.

### 4. Eliminate the dedicated feedback fixer by default

A third agent that did not implement the feature must reconstruct the implementer’s mental model. This creates handoff loss and can introduce a second design on top of the first.

The default structure should be:

- The original implementer addresses accepted findings.
- The reviewer remains read-only.
- A verifier checks only the fixes and possible regressions.
- A fresh fixer is introduced only when the original implementer is stuck, defensive, unavailable, or repeatedly failing the same issue.

This also makes responsibility clearer. The implementer should explain whether each finding was accepted, rejected, or deferred.

### 5. Do not apply reviewer feedback automatically

Reviewers produce false positives, stylistic preferences, and unnecessary redesign proposals. The orchestrator should arbitrate every finding against evidence and requirements.

Require each finding to include:

- Severity: blocking, important, or minor
- A concrete failure mode
- Evidence or reproduction steps
- File and symbol references
- The violated acceptance criterion
- A suggested direction rather than a mandatory implementation
- Confidence level

Reject unactionable observations such as “this could be cleaner.” Review should prioritize correctness, regressions, missing tests, performance, and maintainability risks rather than stylistic churn.

### 6. Reviewer reasoning should often be higher, not lower

Using one high-capability model at low effort for every subagent is too uniform. Reviewing complex behavior may require tracing assumptions, execution paths, and edge cases.

| Role | Suggested capability and effort |
| --- | --- |
| Repository exploration | Efficient model, low or medium effort |
| Mechanical implementation | Efficient model, medium effort |
| Ambiguous integration | Strong model, medium or high effort |
| Correctness or security review | Strong model, high effort |
| Test execution and verification | Efficient model, low or medium effort |
| Architecture adjudication | Strongest model, high or maximum effort only when necessary |

Allocate reasoning according to uncertainty and blast radius rather than applying one setting to every role.

### 7. Use independent review lenses instead of generic repeated review

Three rounds from essentially the same reviewer role tend to produce diminishing returns and correlated mistakes.

For high-risk changes, use two bounded, read-only reviews in parallel:

- **Behavioral reviewer:** correctness, state transitions, edge cases, and regressions
- **Integration reviewer:** Godot lifecycle, scene ownership, resources, signals, performance, and testing

For lower-risk changes, use only one reviewer. Add a specialist only when relevant, such as save migration, performance, shaders, input accessibility, or multiplayer.

Agent diversity should primarily come from different evidence and review lenses, not merely from several prompts saying “be critical.”

### 8. Replace “no feedback” with an objective stop condition

Use the following quality gate:

- All acceptance criteria have been demonstrated.
- Automated checks pass.
- No blocking or important findings remain unresolved.
- Every accepted finding has a regression test where practical.
- Performance budgets pass where relevant.
- The required playtest checkpoint has been completed.
- Remaining minor issues are explicitly deferred.

Default to one implementation review and one fix-verification pass. Permit a second full review only after substantial changes. A third round should require a concrete reason rather than happen automatically.

## Game-specific blind spot

Code review cannot establish whether a game is readable, satisfying, correctly paced, visually coherent, or fun. A workflow focused entirely on plans, code, and review can produce technically polished systems that feel wrong in play.

Each phase should define evidence beyond code:

- A playable scenario or test scene
- Expected player-visible behavior
- A frame-time or memory budget where relevant
- Captures or screenshots for visual behavior
- Input and edge-case checks
- A short human playtest checklist
- Temporary debug overlays or logging for hard-to-observe state

Human judgment is especially valuable at phase boundaries. Spend expensive model reasoning on technical uncertainty; spend human attention on game feel and product direction.

## Recommended workflow

1. The main agent inspects the repository and turns the phase into measurable acceptance criteria.
2. Efficient read-only explorers investigate only uncertain code paths, engine behavior, and existing tests.
3. The main agent synthesizes a short implementation plan.
4. A plan critic challenges high-risk assumptions.
5. One implementer owns all code changes.
6. Deterministic checks run before model review.
7. One or two read-only, lens-specific reviewers inspect the actual diff.
8. The main agent triages findings; the original implementer fixes accepted issues.
9. A verifier checks only the fixes, regressions, and acceptance criteria.
10. The workflow stops based on the quality gate rather than reviewer silence.

## Risk-based operating modes

### Low-risk change

- One implementer
- Automated verification
- One bounded review if the change is not completely mechanical
- No repeated loop unless an important issue is found

### Medium-risk change

- One or two read-only explorers if uncertainty exists
- One implementer
- Automated verification
- One strong reviewer
- Original implementer fixes accepted findings
- One targeted verification pass

### High-risk change

- Read-only exploration by relevant specialists
- Plan criticism before implementation
- One implementation owner
- Automated tests, profiling, and runtime evidence
- Two independent, lens-specific reviewers
- Explicit triage by the orchestrator
- Original implementer fixes accepted findings
- Targeted regression verification
- Human playtest or product checkpoint

## Cost-efficient subagent policy

Use subagents only when at least one of the following is true:

- The work can genuinely run independently.
- A subtask would pollute the main context with logs or exploration.
- Specialized review provides meaningful downside protection.
- Parallelism saves substantial wall-clock time.

For a small, well-understood change, one capable agent plus tests is usually better and cheaper. For a risky phase, spending more on one strong reviewer is usually more valuable than employing several low-effort generic reviewers.

Additional cost controls:

- Give subagents narrow tasks and explicit output formats.
- Keep reviewers read-only.
- Return summaries and evidence rather than raw exploration output.
- Run deterministic checks before paying for model review.
- Do not send every subagent the full historical conversation when the repository, plan artifact, and a focused task brief are sufficient.
- Escalate model strength and reasoning effort only after uncertainty or failure justifies it.
- Avoid open-ended instructions such as “keep reviewing until perfect.”

## Suggested orchestration instruction

```text
Implement this increment against the written acceptance criteria.

Workflow:
1. Inspect the current repository state and identify any mismatch between the plan and the code. Do not assume the plan is correct.
2. If material uncertainty exists, delegate only bounded, read-only exploration tasks and summarize their evidence.
3. Assign one implementation owner. Keep all other agents read-only.
4. Run the relevant deterministic checks before review.
5. Review the resulting diff using these independent lenses:
   - behavioral correctness, edge cases, and regressions;
   - Godot integration, lifecycle, performance, and missing tests.
   Use the second reviewer only if the change is medium or high risk.
6. Every finding must include severity, evidence or reproduction steps, file references, the violated acceptance criterion, and confidence. Omit style-only comments.
7. Triage each finding as accepted, rejected with reason, or deferred with reason. Do not apply feedback automatically.
8. Have the original implementer address accepted blocking and important findings.
9. Verify only the fixes, regressions, and acceptance criteria. Do not begin another open-ended review unless the fixes substantially changed the design.

Stop when all acceptance criteria pass, deterministic checks pass, no blocking or important findings remain, and minor findings are explicitly deferred. Allow at most one ordinary fix-verification pass; require a concrete risk-based reason for any additional full review.
```

## Central principle

Use agents to generate independent evidence rather than a chain of opinions. Tests, reproductions, acceptance criteria, profiling, and playable demonstrations should determine when the work is complete. Reviewer consensus should not.

## References

- [OpenAI: Subagents](https://learn.chatgpt.com/docs/agent-configuration/subagents)
- [OpenAI: Why subagent workflows help](https://learn.chatgpt.com/docs/agent-configuration/subagents#why-subagent-workflows-help)
- [OpenAI: Choosing models and reasoning](https://learn.chatgpt.com/docs/agent-configuration/subagents#choosing-models-and-reasoning)

