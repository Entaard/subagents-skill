# Delegation policy

Policy owner: `policy.delegation`

## Axioms

1. Sage adds placement, boundaries, and evidence, not intelligence. Place each unit on the least costly model that can still reach the right answer; cost never excuses an incapable placement.
2. Every claim is checkable or explicitly a hypothesis. The orchestrator's post-fix confidence receives no special trust.
3. Buy useful conflict through disjoint mandates, refutation, and a settling observation. Agreement alone is not evidence.
4. Autonomy is legibility recorded rather than continuously displayed. Silence is a presentation choice, never a record-loss choice.

The root policy actor declares and accepts the baseline, chooses acceptance criteria, grants the writer lease, accepts or adopts results, dispositions findings, settles conflicts, revises plans, and owns integration and the completion claim. Workers propose and produce evidence; none inherits those authorities from a brief or successful check. Zero delegated units remains valid for work with no independently valuable seat.

## Qualify and decompose

Split the task before deciding which units to delegate. Split at context and intervention boundaries, not into sequential job titles. The phases of one tightly coupled deliverable remain with one owner; independent review is the deliberate exception because separation is its source of value.

Each unit must be independently checkable and must not exchange undeclared information with a concurrent peer. Merge or serialize coupled units. Choose a barrier only when the next stage needs the entire preceding wave or a shared resource must stabilize; otherwise pipeline each item into its dependent check.

Classify every unit as read-only or mutating. One mutating actor may own a shared mutable resource at a time. Parallel mutating units require independently enforced isolation, disjoint deliverables, and a named integration owner. Different filenames alone do not establish isolation.

A unit is safe to delegate only when all five conditions hold:

1. It has a bounded deliverable and a one-sentence, falsifiable completion criterion.
2. It can make useful progress without frequent policy decisions.
3. Its required context can be packaged as explicit artifacts and decisions.
4. Its result can be checked or falsified from evidence.
5. Its effects are read-only, serialized under one lease, or isolated by an effective boundary.

A safe unit is worth delegating only when at least one benefit is material: shorter critical path, protection of the policy actor's context from bulk material, an independent evidence lens, or cohesive ownership of a substantial unit. A unit that fails either test stays policy-actor-owned; it is not omitted.

## Bootstrap discovery

When targeted reads cannot produce a complete plan, the first revision may be a bounded bootstrap. It contains only read-only discovery units whose output is the evidence needed to commit the first complete plan.

A bootstrap declares its unit, attempt, concurrency, and spend bounds before admission. It has at most two discovery rounds; the second is limited to follow-ups exposed by the first. Discovery cost is recorded as already spent. A bootstrap cannot contain mutation, implementation, open-ended search, or work that could have been specified in the complete plan.

Completion criterion: the bootstrap ends with either a complete plan revision or an explicit gap that blocks planning. It never silently becomes the implementation plan.

## Risk and bounded admission

Assess failure impact, coupling breadth, novelty, reversibility, automated-verification strength, compatibility, and human-decision dependence. Data migration, credentials, security, networking, irreversible conversion, public compatibility, core performance budgets, and behavior without a reliable oracle are high-risk triggers.

Planning may begin with every task-specific rail explicitly uncommitted. Before admitting any revision or dispatching any brief or attempt, the root commits finite unit, attempts-per-unit, concurrency, plan-revision, wall-clock-admission, admitted-agent, and no-progress bounds chosen for that task. There is no universal numeric default for those rails. A comparable spend limit includes work retained by the root; absence of a trustworthy spend sensor is unknown, never zero. An uncapped-spend experiment is a separate attended choice with an external limit and the same finite non-spend rails.

### Admission policy profiles

An admission profile is selected and versioned in the plan. It is one of:

- `bounded-observed`: finite admissions, attempts per unit, plan revisions, concurrency, and wall-clock admission, plus token or cost caps only where reliable telemetry exists;
- `fixed`: user or organization caps for attempts, agents, tokens, cost, and time;
- `estimate-multiple`: estimate-derived task, unit, and agent-count ceilings with versioned multipliers and floors;
- `uncapped-observed`: no Sage spend ceiling, permitted only for an explicitly consented attended experiment under an external hard ceiling and the ordinary finite admission, failure, and revision stops;
- `custom`: a named, versioned organization or user policy whose complete bounds and enforcement sources are recorded.

The portable profile is `bounded-observed`, but its task-specific values have no universal seed. The compatibility profile may seed comparable spend rails only where the adapter proves comparable usage. Crossing any finite limit drains selected in-flight work, admits nothing new, records the exact measured, provider-reported, estimated, or unknown sensor and its provenance, and enters `AwaitingHuman`.

The baseline compatibility profile is `estimate-multiple/baseline-v1`. It retains three separate projected ceilings:

| Scope | Ceiling | Floor |
| --- | --- | --- |
| whole task | four times the complete plan estimate | 500,000 normalized tokens |
| one unit | four times that unit revision's estimate | 150,000 normalized tokens |
| admitted agent count | twice the planned agent count | 10 agents |

Before each admission, the projection is landed usage plus every in-flight estimate plus the candidate estimate. Task and unit token scopes are checked independently; an overrun that arrives after the last admission is still surfaced. The compatibility sensor is the baseline host's bring-current status observation and manual policy-actor projection, so it is advisory unless a later adapter proves enforced and comparable accounting. An environment without that sensor uses `bounded-observed`; it does not manufacture compatibility figures.

Reclassify risk and commit a new plan revision when evidence changes the blast radius. A close delegation, topology, model-placement, or test-suite decision is an assumption with a falsifier.

## Placement

Describe the unit's requirements before resolving a concrete model: corpus size, ambiguity, number of reasoning steps, tool and modality needs, latency preference, cost ceiling, independence requirement, and verification criticality. A versioned host profile resolves those requirements to an exact available model and effort.

Record requested and effective model, effort, permissions, and isolation separately. Preserve a user's explicit concrete model choice. A missing required capability rejects admission or forces a plan revision; a missing preferred capability takes the fallback named in the plan. Prompt text never substitutes for an unavailable capability.

## Planning and estimation

Before dispatch, commit either the bounded bootstrap or a complete plan revision. The complete plan states objective, risk, topology, dependencies, concurrency and attempt bounds, estimates, acceptance criteria, evidence classes, risks, and a solo alternative when delegation is a close call.

Estimate from the corpus a unit must hold and the lenses it must apply, not from output length or role name. Account for discovery separately from repair, and price review together with its fix verification and possible blocker/major follow-up. When a claim turns on a number, establish the measurement method and baseline before briefing workers; every unit comparing that number uses the same method.

Completion criterion: every unit has a stable ID, immutable unit-spec revision, owner, effect class, dependencies, done-when sentence, requested capability predicates, placement requirements, and estimate before admission.

## Root and worker ownership

For substantial software mutations, the normal plan gives mutation to a dedicated writer and gives baseline/reproduction, acceptance, and accepted-fix verification to independent read-only workers. Writer self-checks stabilize its candidate but do not constitute independent acceptance. The root grants and later releases the writer lease, freezes the candidate, adopts accepted results, triages all review evidence, and uses a fresh fix-verification seat after accepted repairs.

The root implements directly only when the mutation is small and tightly coupled to its judgment, no matching worker capability is available, or matching delegated attempts have exhausted their admitted failure bound. It runs settling commands itself only when the command is narrower and cheaper than dispatch. In Light mode these ownership rules are policy discipline backed by recorded hashes and native snapshots, not an externally enforced lease.
