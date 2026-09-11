# Sage for Codex Light equivalence

Sage Light preserves the current `sage-claude` policy behavior while replacing Claude-specific mechanics with native Codex collaboration and portable structured artifacts. “Equivalent” here means the same orchestration judgments, evidence duties, safety rails, and completion conditions. It does not claim Managed-mode enforcement where Codex exposes no authoritative scheduler, lease, usage, or context-pressure sensor.

| Sage behavior | Codex Light realization |
| --- | --- |
| explicit-only activation; task, report, and resume forms | `$sage` metadata disables implicit invocation; the skill routes new runs, `report`, and `resume` separately |
| scout-before-plan and zero-agent validity | revision 0 is bounded read-only bootstrap discovery; complete plans may keep every unit with the policy actor |
| safe/worth decomposition and parent-owned judgment | canonical delegation policy owns qualification; workers propose and the root owns plan, risk, triage, integration, and completion |
| full topology set | independent sweep, implement–review–fix, migration, bake-off, dry loops, adversarial review, quarantined reads, competing hypotheses, completeness critic, blind acceptance, pre-write critic, and blind behavioral lens remain canonical |
| deliberate placement | Codex requirements resolve to an explicit model and effort; requested and effective identity are separate, with unknown preserved |
| falsifiable plans and briefs | schema v1 records immutable plan/unit/brief revisions, dependencies, criteria, effects, capabilities, bounds, baseline, return contract, and inline alternative |
| native parallel coordination | `spawn_agent`, `send_message`, `followup_task`, `list_agents`, `wait_agent`, and `interrupt_agent` map start, steer, continue, snapshot, wait, and interrupt |
| specialized worker seats | scout, researcher, writer, verifier, and successor are explicit brief contracts; child reports remain unprivileged |
| shared-tree mutation safety | one active writer, counting the root; mutation baseline, changed paths, frozen review snapshot, separate reviewer, bounded fix lease, and regression verification |
| evidence before agreement | deterministic checks precede review; disjoint spec/quality lenses, conflict reproduction, dispositions, dry blocker/major round, and adversarial post-fix review remain policy duties |
| failure ladder and bounded retries | failure signatures distinguish specification, capability, and blocked work; two matching signatures end delegated retry and reopen policy |
| safety and human rails | destructive/external authority, writer collision, scope escape, and bound crossing pause admission; unavailable isolation or approval is never inferred from prose |
| assumptions, gaps, decisions, and coordination value | structured rows preserve falsifiers, corrections, unresolved evidence, abandoned disagreements, and whether delegation helped |
| completion and user-facing delivery | schema and semantic validation require terminal units/results, evidence, checks, finding disposition, scope, human state, coordination outcome, and the actual deliverable |
| durable reporting | JSON is authoritative; Markdown is a deterministic, hash-bound, reproducible projection printed in full by `sage-light report` |
| 30-percent handover and recovery | automatic triggering is claimed only with a supported numerator and denominator; explicit handover writes authoritative hash-bound `handoff.json`, optional Markdown is regenerated from it, and resume fails on JSON integrity/staleness, baseline drift, or unknown attempts |
| memory | active runs read only indexed promoted knowledge and append allowlisted current-run facts; they never mine old raw logs or create lessons |
| promotion | explicit `$sage-promote` inspects one or more closed runs, consolidates then, refutes candidates, and lands stable-ID records to the installed overlay by default or source-only with explicit `--global` |
| install, update, and removal | `sage/install.sh` and `sage/uninstall.sh` drive receipt-bound, recoverable lifecycle operations while preserving run history and installed promotion on update |

## Deliberate Codex-plan changes

- Runtime logs are factual evidence only. Confirmation counting, lesson extraction, knowledge consolidation, and policy self-editing never happen during an active run.
- Closed logs become reusable input only through an explicit later `$sage-promote` pass. Multiple closed runs may be consolidated in one candidate with qualified evidence references.
- Installed promotion is the default and changes only the installation's promoted overlay. Explicit global promotion changes source knowledge only and prints the checkout's later `sage/install.sh`; it does not reinstall.
- Native worker snapshots replace transcript watching. A transcript or rendered report is not an authoritative lifecycle sensor.
- Role specialization is carried in immutable briefs because the live Codex start call does not expose a named custom-agent selector.
- Codex lifecycle scripts live under `sage/`. Repository-root `install.sh` and `uninstall.sh` remain owned by `sage-claude`.

The frozen Phase 1 paired pilot is a separate quality/managed-need experiment. Its unavailable hard-cap and root-loss controls do not make the implemented Light workflow reader-only; they prevent fabricating pilot outcomes until the preregistered harness requirements exist.
