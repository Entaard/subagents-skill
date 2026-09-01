# Policy contracts

Policy owner: `policy.contracts`

This file owns the meaning and required content of policy artifacts. The versioned schemas own their exact JSON representation.

## Plans and revisions

An admitted plan revision is immutable. A change to scope, dependencies, criteria, units, or bounds creates the next numbered revision with a reason and the expected prior revision. Logical unit IDs remain stable; each changed unit receives a new immutable unit-spec revision.

The next plan marks every earlier unit revision as carried, superseded, or removed. Reusing an earlier result requires an adoption decision against the new criteria. Admissions pause while a revision commits, and an in-flight attempt keeps the exact plan revision, unit-spec revision, and brief hash it received.

## Task brief

A brief is a falsifiable contract containing:

- role and one-sentence objective;
- inputs and sources of truth, identified by protected locator and integrity evidence rather than conversation history;
- scope and relevant artifacts;
- allowed effects, resources, and tools as semantic capabilities;
- per-unit bounds and the authority that enforces each one;
- explicit exclusions and non-goals;
- baseline or snapshot;
- one falsifiable done-when sentence;
- requested placement and effort requirements;
- a result contract containing status, result, evidence, changed artifacts, checks, uncertainty, and recommended next action.

Name decisions already made so independent units do not remake them inconsistently. A blind test author receives observable requirements and criteria but not the implementation decision. An enumeration may use a bounded scratch artifact; a conclusion is distilled.

## Result and artifact

A worker result has status `completed`, `partial`, or `blocked`; a concise conclusion; evidence; exact changed artifacts or `none`; checks and outcomes; uncertainty; and a recommended next action when needed. A report is an unprivileged claim. Its status is distinct from worker lifecycle, result acceptance, and verification.

Each material artifact has an opaque stable ID, media type, classification, integrity hash, protected locator, producer, and adoption state. A hash without retained content is recorded as a hash, not mislabeled as retained raw data.

## Assumption, gap, and decision

Record an assumption when the policy actor resolves an ambiguity that would otherwise need the user. It names the chosen interpretation, plausible alternatives, impact, and an observable falsifier. A correction is appended to the same assumption history rather than replacing it.

A gap is missing evidence, capability, coverage, or information. It names impact, evidence already checked, the next action or owner, and one explicit final state: closed, accepted risk, or `AwaitingHuman`. An unavailable sensor is a gap or unknown value, never a zero.

A decision records what changed, when, why, and the exact plan or artifact revision it affects. Abandoned disagreements are decisions too; silent discard is invalid.

## Finding and disposition

A finding contains a stable ID, severity, confidence, location or subject, failure mode and impact, evidence or reproduction, the violated criterion or boundary, a suggested direction, and a fix-verification method.

Severity is blocker for corruption, security failure, unusable mandatory paths, or failed mandatory criteria; major for credible user-visible regression or serious near-term failure; and minor for bounded improvement. Low-confidence hypotheses are leads, not blockers.

Every finding receives exactly one disposition decision: accepted, rejected with evidence, deferred with an owner, or user decision. Its resolution state is separately explicit: resolved or `AwaitingHuman`. Accepted findings name the repair, accepted residual risk, or scope decision and the verification that closes them.

## Verification

Every acceptance criterion is classified before work as machine-verifiable, agent-observable-but-subjective, or human-only. A verification binds one subject and criterion to a method, verdict, evidence, verifier, and time. Verdicts are pass, fail, or `AwaitingHuman`; reviewer silence is not a verdict.

Result receipt, result acceptance, terminal worker state, and required verification are four distinct facts. A unit completes only when all facts required by its unit specification are present.

## Coordination outcome

Every run records whether coordination was beneficial, harmful, or inconclusive, with concrete evidence: unique contributions, duplicated work, interventions, protocol failures, critical-path effect, context effect, and residual limitations. Zero delegation still receives an outcome explaining why inline ownership was the better coordination decision.

## User-facing run result

A run returns the requested deliverable rather than only a record pointer. Its concise result also names the run ID, artifact paths, effective capability summary, assumptions or gaps that affect interpretation, and any safety or human item. The full rendered run record is a reproducible projection of structured artifacts and is never authoritative input.

