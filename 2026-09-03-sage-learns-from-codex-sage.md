# Proposal: what sage-claude should take from Codex Sage

Date: 2026-09-03. Subject: `2026-08-31-sage-codex-proposal.md`, the `sage/` directory (Sage for Codex, Phase 0 and Phase 1), and the six root-level documents that describe and measure it. Target: `sage-claude/` in this repository.

## Verdict in one paragraph

Codex Sage is a real implementation, not a paper design. Its Python library and its 44 tests run and pass on this machine once one portability defect is patched. Most of its policy is a port of sage-claude and brings nothing back. Its two large new mechanisms, the JSON run record with a Markdown projection and the receipt-bound installer, solve problems sage-claude has already solved another way, at a cost that no measurement justifies. Eleven smaller items are worth taking. Each one is a bounded change to a template, a script, or one rule. Seven of them (A1, A2, A4, A5, A6, A7, A8) rest on a measurement or a memory item that already exists in sage-claude, not on Codex Sage's claims. Three (A3, A9, A10) are argued and unmeasured, and each one says so and names its falsifier. One (A11) is an evaluation method with no local instance yet. Two items are rejected explicitly because they look strong and are not.

## How this study was done, and what it found about the corpus

Six read-only scouts enumerated the corpus into one line per mechanism with a file:line pointer. The scout reports sit in this session's scratchpad. The parent ran Codex Sage's own checks and read the primary files that each verdict below depends on.

Three facts about the corpus shape every verdict that follows.

**The code works, and one line stops it from running here.** `python3 sage/scripts/check-phase0.py --self-test` passes. `python3 sage/scripts/check-phase1.py` fails as shipped: 40 of 44 tests raise `FileNotFoundError` because `sage/tests/test_phase1.py` hardcodes `dir="/private/tmp"`, a macOS-only path, in 40 places (first at line 141; the traceback shows line 382). With that string replaced by `/tmp` in a scratch clone, all 44 tests pass in 38 seconds and the Phase 1 gate reports "implementation and frozen-gate checks passed". The repository also commits `cpython-311` bytecode from the author's machine. The README's instruction to run the complete Phase 1 matrix is therefore true only on the author's platform. This is not a reason to distrust the design. It is a reason to treat every "tested" claim as tested on one machine.

**No Codex Sage design has outcome evidence.** The Phase 1 paired pilot that was meant to show the policy's value never started (`sage/README.md`, "Phase 1 pilot gate"; `sage/evaluation/phase-1/STATUS.md`). The Managed mode, the runtime protocol, the capability negotiation and the resource coordinator exist as schemas and prose only. `sage/knowledge/index.json` holds zero promoted records, so the promotion workflow has never landed a real record. Every adoption below therefore has to justify itself on sage-claude's own measurements. Where it cannot, it is rejected, however clean the Codex design reads.

**The effort that produced it was expensive.** `codex-massive-usage.md` lines 84 to 90 attribute 105.3M tokens to the proposal session group, 86.5M to the Phase 1 implementation, 98.1M to the later `$sage` instruction work, and 37.5M to the implementation review. The usage investigation (`codex-vs-claude-sage-usage-investigation.md`) traces the spend to a root model on maximum reasoning, thousands of tool cycles, repeated compaction and fan-out. None of that spend bought a single measured run of the skill itself. A design that consumed this much before its first evaluation is not evidence of value. It is evidence of scope.

## Items to adopt or adapt

Each item names what Codex Sage does with a pointer, what sage-claude does today with a pointer, the verdict, the reason, and the design.

### A1. Classify every acceptance criterion by evidence class at plan time

**Codex Sage.** Every criterion carries `evidence_class` with three values: `machine`, `agent_observable`, `human_only` (`sage/artifacts/schemas/sage-artifact-v1.schema.json:90`). `sage/policy/contracts.md:54` requires the classification before work starts. Every verification then records `verdict: pass | fail | AwaitingHuman` against a criterion (`schema:505`).

**sage-claude today.** Criteria go into `### Plan` as verbatim text (`references/dispatch.md`, Plan template). The split between a measured pass and a judged pass appears only in the run record at Step 6 (`references/dispatch.md:187`), where it asks to name "any machine-verifiable case that downgraded to judged". Nothing earlier in the run defines which cases were machine-verifiable, so that sentence has nothing to compare against.

**Verdict: adopt.**

**Reason.** The run record already wants the measured-versus-judged distinction. Without a plan-time class, a reviewer decides at Step 5 what kind of evidence a criterion needs, at the moment it is cheapest to decide "judged". sage-claude's own Step 5 warns that "a criterion can pass literally while the mechanic it describes is broken" and that a verifier with two words available "will guess". A class fixed before the work is what turns the downgrade into a checkable event.

**Design.**

1. In the Plan template, each criterion line starts with its class in brackets: `R1 [machine] <text>`, `R2 [agent] <text>`, `R3 [human] <text>`. Three words, matching the run record's existing vocabulary: `[machine]` passes only by a command whose output is recorded; `[agent]` passes by a clean-context reviewer's read; `[human]` is `Awaiting human` until a person rules.
2. Step 5 adds one sentence: a `[machine]` criterion reported as a judged pass is a downgrade, and the run record's Verification line names it.
3. `sage-lint.sh` gains a check `criterion-class`: every line matching `^\s*R[0-9]+ ` under the Plan's `Criteria:` label carries one of the three bracketed words. Blind spot, stated in the header: it reads the label, never whether the class is right.
4. The blind acceptance-suite author (`references/topologies.md` #10) receives the class with each criterion, because it decides whether a case is executable or a human checkpoint.

Cost: a template edit, one Step 5 sentence, roughly twenty lines of awk.

### A2. Measure the effective model from the transcript instead of asserting it

**Codex Sage.** Placement records `requested_model` and `effective_model` separately, and `effective_model` may be `unknown` (`sage-artifact-v1.schema.json:353`; `sage/skills/sage/references/guarantees.md:14`). Codex cannot observe the effective model, so the design preserves the unknown instead of copying the request.

**sage-claude today.** The unit table's `model used` cell is filled by the parent from what it passed (`references/dispatch.md`, Unit table). `bin/sage-watch.sh --status` prints occupancy and spend per agent but no model (`grep -n model bin/sage-watch.sh` returns nothing). The alt lane already reaches for measurement: `references/harness.md`, "The alt lane", settles family identity by grepping the transcript.

**Verdict: adopt, and go further than Codex Sage can.**

**Reason.** Claude Code writes `message.model` on every assistant record of every agent transcript. Measured this run: all six explorer scouts show `claude-haiku-4-5-20251001` on every record. `references/harness.md`, "Models and effort", lists two paths that silently swap a requested model, the `CLAUDE_CODE_SUBAGENT_MODEL` override and the `availableModels` fallback, and says "either path turns every Model cell in the ledger into fiction". The transcript is the one place the fiction cannot reach. Codex Sage has the right column and no sensor. sage-claude has the sensor and no column.

**Design.**

1. `bin/sage-watch.sh --status` prints `model=<value>` per agent, taken from the latest assistant record's `message.model`, or `model=unknown` when no assistant record exists yet. About ten lines of `jq`, beside the fields it already prints.
2. The unit table's `model used` cell records that measured value, with the word `measured`, at the bring-current point where the parent reads `--status`. A cell the parent fills from its own dispatch says `asserted`.
3. A measured value whose family or tier differs from the Plan row is a `### Decisions and deviations` row, written when it is read, because it means a swap happened that the run did not order.
4. The Step 6 run record's Agents line carries the measured model, which is what makes the audit surface true after the fact.

Cost: one script edit and two template words. A lineup claim about which model ran becomes a grep, not a belief.

### A3. Give the coordination check a fixed state word

**Codex Sage.** `CoordinationOutcome.state` is an enum: `open | beneficial | harmful | inconclusive | not_delegated`, with evidence fields beside it (`sage-artifact-v1.schema.json:550`; `sage/policy/contracts.md:60`).

**sage-claude today.** The coordination check is a prose line in the run record (`references/dispatch.md:189`) and a surfaced event when negative (`SKILL.md`, Step 6). It is the line that can falsify sage's own premise, and it cannot be counted across runs because it has no fixed vocabulary.

**Verdict: adopt the state word only.**

**Reason.** `/sage-promote` reads the journal to build its slate. A prose sentence per run is invisible to `grep -c`. The four words cost nothing, and they make "how often does the fan-out buy nothing" a number instead of a feeling. The extra Codex fields (`unique_contributions`, `duplicated_work`, `interventions`, `critical_path_effect`) duplicate what the run record's Agents and Deviations lines already hold, so they are not taken.

**Design.**

1. The run record line becomes `Coordination check: <beneficial | harmful | inconclusive | not-delegated> — <one clause of evidence>`. `harmful` is for a run where the fan-out cost the result something, for example a writer collision or a lost finding in a distillation. `inconclusive` replaces "nothing; one agent would likely have matched it".
2. The journal `run` line gains `coord=<state>` next to `agents=N`, so the slate can count it.
3. `sage-lint.sh` gains `coord-state`: the run record's Coordination line, when present, starts with one of the four words.
4. `harmful` and `inconclusive` both remain surfaced events, as the negative answer is today.

Evidence status: argued, unmeasured. No memory item records a run where the prose form blocked a count. Falsifier: the KI-review stage of `/sage-promote` runs three times without ever wanting the count.

### A4. Make the handover response depend on remaining work, not only on occupancy

**Codex Sage.** Recommendation 1 of the usage investigation (`codex-vs-claude-sage-usage-investigation.md:196-212`) replaces a fixed 30% rule with absolute headroom: `remaining = window - occupancy`, `required_headroom = max(p95_next_turn_growth, 2 * handoff_payload, recovery_reserve)`, prepare a checkpoint when `remaining <= required_headroom`, hand over at a clean phase boundary or at once when another substantive turn is required, and "record how every term was measured; if growth data is unavailable, use a conservative pilot value and label it estimated".

**sage-claude today.** A single rung: parent occupancy at 30% of the window fires `occ-30pct`, and `## Handover` runs (`SKILL.md`, Handover). The installed memory holds `lesson-occ-30pct-fires-with-nothing-to-launch` in `~/.claude/skills/sage/memory/local/`, at `count: 7` with the last two occurrences on 2026-08-28: the rung fires late in investigation-shaped and corpus-edit runs. Its fifth occurrence (2026-08-27) names the sharper predicate: the threshold was reached "with one unit in flight and the deliverable already durable on disk", so the carve-out is "nothing in flight and the deliverable durable", not "nothing left to launch". This run reached 23% with all scouts landed and the draft not yet written.

**Verdict: adapt.** Keep the sensor and the 30% rung. Change what the parent does when it fires.

**Reason.** The Codex recommendation was written for a 258k-token window where 30% is 77k and compaction was observed between 71% and 96% of the window. Those numbers do not port. What ports is the shape of the rule: the decision should compare the room that remains with the work that remains, not with a fixed fraction. sage-claude's own seven observations are the local evidence that the fixed fraction misfires. The honesty clause ports too: no auto-compaction has been observed on this machine, so the reserve is an estimate and must say so (`references/harness.md`, "Transcripts and the token arithmetic").

**Design.**

1. The rung stays as it is. `sage-watch.sh` changes nothing.
2. When it fires, the parent computes two figures at that bring-current point and writes them into one `### Decisions and deviations` row: `remaining = window - occupancy`, and `needed = reports still to land + fix rounds still planned + Step 6 record + reserve`. The reserve is the measured handoff write cost, 5 to 8k (`references/harness.md`), plus a compaction margin labelled `estimated`, because no local measurement places the auto-compact trigger.
3. `needed < remaining`, nothing in flight, and the deliverable already durable on disk: finish in place. The row records the arithmetic and the handover does not run. The rung is acknowledged with `SAGE_OCC_ACK=1` exactly as a supervisor does today.
4. Otherwise: run `## Handover` as written.
5. The journal `run` line records both figures when the rung fired, which is how the reserve gets a measured value after enough runs.

What this does not do: it does not move the threshold. Moving it needs a measurement of where compaction fires, and there is none. Recommendation 12 of the same document (`:294`) is the design for that measurement: a matched experiment, early handover against native compaction, with overlap and rehydration cost recorded. sage-claude has never observed an auto-compaction, so the experiment cannot run here until one does. Record it as the open measurement behind this item.

### A5. Add a secret-shape check to the ledger lint

**Codex Sage.** `sage/lib/facts.py:69-101` validates every fact appended to a run log: it rejects payloads over a size cap, requires a hash and locator for confidential facts, and rejects credential-shaped strings with the message "a current-run fact payload appears to contain restricted credential material" (`facts.py:101`). The skill's guarantees list "credential/payload rejection" as enforced (`guarantees.md:19`).

**sage-claude today.** The ledger is free text. Evidence cells quote command output. `references/harness.md:243` measured that `.claude/plans/` is not gitignored in a fresh repository, so a ledger can enter a user's history with one `git add -A`. Nothing scans it.

**Verdict: adopt, as a lint check.**

**Reason.** The write-time gate Codex Sage uses does not exist in a Markdown ledger, but the lint runs at every bring-current point, which is the same moment. The check is deterministic, costs a regex, and fails open on unknown formats, which is the lint's existing contract.

**Design.** `sage-lint.sh` gains `secret-shape`: one line per match of a small fixed pattern set on the whole file, outside fenced blocks: `AKIA[0-9A-Z]{16}`, `-----BEGIN [A-Z ]*PRIVATE KEY-----`, `ghp_[A-Za-z0-9]{36}`, `xox[baprs]-[A-Za-z0-9-]{10,}`, `Bearer [A-Za-z0-9._-]{20,}`, `sk-[A-Za-z0-9]{20,}`. The header states the blind spot: it knows these six shapes and nothing else. A hit at Step 6 is a surfaced event, like any other lint line. The same check runs in `--corpus` mode over `memory/`, because knowledge items are committed to the repository and `sage/skills/sage-promote/references/workflow.md:15` names the leak that matters there: credentials, private paths, user identity.

### A6. Split the promotion bar by evidence class

**Codex Sage.** Promotion thresholds depend on the record's class: a deterministic invariant needs one closed run plus a passing independent refutation; an empirical heuristic needs three distinct runs; shared-policy guidance needs six plus a behavioural evaluation (`sage/skills/sage-promote/references/promotion-contract.md:17`; enforced in `sage/lib/knowledge.py`, tested at `sage/tests/test_phase1.py:608`).

**sage-claude today.** One bar: three confirmations graduate a lesson to `shared/` (`SKILL.md`, Handover, "what closes such an observation is three confirmations"; `references/memory.md`). A deterministic fact about the harness, for example a transcript field's name, waits for the same three runs as a cost tendency does.

**Verdict: adapt the two-way split. Reject the number six.**

**Reason for the split.** A deterministic fact is settled by one reproduction, and sage-promote already owns the refuter that would test it (its degradation gate). Holding it for three runs delays knowledge the next run could use and costs nothing in safety, because the falsifier is a command. The distinction is the same one sage-claude's Step 5 draws between a measured and a judged pass.

**Reason against six.** The follow-up report itself says these numbers should be recalibrated "from outcomes not intuition" (`sage-codex-follow-up-report.md:154`), and no promotion has ever run under them. sage-claude already gates behaviour-shaping text with the two-arm behavioural lens (`references/topologies.md` #12), which is a stronger gate than a count.

**Design.** In `claude-skills/sage-promote/SKILL.md`, landed by hand as described under "Order of work" (that skill may not edit its own file), the minting stage classifies each candidate `deterministic` or `empirical` and writes the word into the KI's stats sidecar. `deterministic` may land in `shared/` after one run when the degradation gate's refuter reproduces the falsifier's command. `empirical` keeps the three-confirmation bar. The `references/memory.md` shape section names the field and its two values.

### A7. Record a novelty disposition when a KI is minted

**Codex Sage.** Every create or revise candidate carries a `NoveltyReview`: the stable IDs it was compared against and one disposition, `novel | revise_existing | overlap_accepted` (`knowledge-record-v1.schema.json:96`; `promotion-contract.md:19`). The library rejects a review that did not name every other active record (`sage/lib/knowledge.py:604`, `_verify_novelty_review`).

**sage-claude today.** The minting step already requires the comparison: "where an existing KI already records the same observation, treat the line as a `confirm` of it instead" (`claude-skills/sage-promote/SKILL.md:120`). What it does not require is a record of the comparison's result. Nothing in a minted KI says which existing KIs it was weighed against or why it was judged new. The memory shows the cost of an unrecorded comparison: `defect-migrated-lesson-class-calls-inconsistent` records three lessons with same-shaped evidence and inconsistent class calls. (The separate "one home" check at `:76` covers the skill text, not the KI set.)

**Verdict: adapt, small.**

**Reason.** A comparison that leaves no record cannot be audited when two KIs later turn out to overlap. Recording three words at minting time is cheaper than the reconciliation the memory has already had to do once.

**Design.** Landed by hand (see "Order of work"). The minting step in sage-promote runs `bin/sage-index.sh`, names in the new KI's provenance the KI ids whose recogniser overlaps, and writes one of three words: `novel`, `revises <ki-id>`, `overlaps <ki-id> (accepted: <why>)`. `revises` routes the candidate into the existing KI as a confirmation or an edit instead of a new file. No script change: the index already exists, and the pass already reads it.

### A8. Two lint checks that Codex Sage's invalid fixtures name and the text lint can make

**Codex Sage.** `sage/artifacts/fixtures/invalid/` holds 63 fixtures. Two of them describe conditions a text lint can read: `accepted-finding-without-verification.json` and `unknown-spend-misrepresented.json`.

**sage-claude today.** `sage-lint.sh` has eleven checks. `triage-state` fires on an empty or illegal triage cell. Nothing fires on an `accepted` finding whose evidence cell is empty, or on a `reported` unit whose `actual tokens` cell is empty.

**Verdict: adopt both.**

**Reason.** Rail 4 is checked from `--status` in flight, but the `actual tokens` cell is what the run record, the journal `run` line and the next run's estimate read; an empty one hides spend from every later reader. An accepted finding with no evidence is the shape the commit gate's second half exists to catch by hand (`SKILL.md`, Step 5, "read the triage column yourself"). Both checks are cell-emptiness tests on labelled columns, which is exactly the shape `triage-state` already implements.

**Design.** `finding-evidence`: a Findings row whose triage cell reads `accepted` and whose evidence cell is empty. `unit-actual`: a Unit table row whose state cell reads `reported` and whose `actual tokens` cell is empty. Both state in the header what they cannot see: a non-empty but false cell.

### A9. One table that says which controls are enforced and which are advisory

**Codex Sage.** `sage/skills/sage/references/guarantees.md:7-22` lists sixteen controls and states for each whether Codex Light enforces it, observes it, or only asks for it. The invariant `EXP-LIGHT-ADVISORY` requires that a control be reported advisory unless a boundary proves enforcement.

**sage-claude today.** The same facts exist, spread across `SKILL.md` Step 3 ("Only a saved agent file enforces this; on a plain dispatch the line is an instruction"), `references/harness.md` ("Frontmatter beyond tools"), `references/dispatch.md` (Per-unit caps "BIND") and the `sage-alt-guard.sh` header. A parent deciding whether a brief line is enough has to remember all four.

**Verdict: adopt as one reference table, no new rules.**

**Reason.** Axiom 2 says every claim is checkable; a brief line that reads as a control but binds nothing is the one claim the parent cannot check by reading the brief. Evidence status: argued, unmeasured. No memory item records a run that mistook an advisory line for an enforced one. Falsifier: three runs consult the table and none changes a brief because of it.

**Design.** A table in `references/harness.md` with one row per control: tool scope, `maxTurns`, model, nested delegation, alt no-model rule, write lease, occupancy threshold, budget rail, one-writer rule. Columns: enforced by what (agent file, hook, script, nothing), and the failure mode when only asked. Every row points at the section that owns the detail, so the table adds no second home. The `--corpus` lint mode already checks that citations resolve.

### A10. Record the recogniser that should have fired

**Codex Sage.** For each loaded knowledge id, the run appends whether it was useful, neutral or misleading, and separately "a missed recogniser and the affected decision" (`sage/policy/memory.md:15`; `sage/skills/sage/SKILL.md:30`).

**sage-claude today.** The `use` line records `hit` or `miss: <why>` for KIs read at Step 2 (`references/memory.md:88`). A KI that was not loaded but whose rule applied leaves no trace, so the KI-review stage cannot see that a recogniser is too narrow.

**Verdict: adopt one clause.**

**Reason.** The KI-review stage retires knowledge on recorded misses. A recogniser that is too narrow never gets loaded, so it never records a miss and can never be retired or widened. Evidence status: argued, unmeasured. The journal holds no instance of a KI that should have fired and did not, which is exactly what this clause would make visible. Falsifier: ten runs write the clause and none ever names a KI.

**Design.** The `use` grammar gains `<ki-id> missed: <what matched in hindsight>` for a KI not loaded at Step 2 whose rule the run needed. Step 6's Coordination and Gaps writing is the moment to ask the question. The KI-review stage treats `missed` as a recogniser defect, not a rule defect.

### A11. A pre-registered paired evaluation, scaled down

**Codex Sage.** `sage/evaluation/phase-1/` defines a frozen two-arm pilot: 20 paired tasks, control without the skill and treatment with it (`prompts/control.txt`, `prompts/treatment.txt`), a six-dimension rubric with mandatory-failure conditions (`rubric.json`), two blind judges and an adjudicator, a non-inferiority margin, a 1.25× spend-comparability bound, and a pre-registered definition of an operator intervention (`preregistration.md`, hashes in `PREREGISTRATION.sha256`). It never ran, because Codex exposes no hard per-arm token cap (`STATUS.md`).

**sage-claude today.** Two open gaps have no measurement path: `gap-unattended-vs-approved-plan-unmeasured` ("running unattended is unmeasured against running with a human approving the plan first") and the handover-versus-compaction question in A4. The two-arm behavioural lens (`references/topologies.md` #12) tests one text change, not a policy's value.

**Verdict: adapt the method, unscheduled.**

**Reason.** The method is sound and independent of the designs it was meant to evaluate. sage-claude has what Codex lacked: a per-unit spend read (`--status`) and a budget rail that can serve as the hard cap. The cost is real, so this is a design to keep, not work to start.

**Design.** Five to ten paired tasks, not twenty; arms are "plan approved by the user" against "unattended"; the cap is rail 4's per-unit figure; scoring by a clean-context `verifier` against the rubric's six dimensions with the mandatory failures kept verbatim; pre-registration is one file with its hash in the ledger before the first task runs. Run only when a gap KI has been open long enough that its cost exceeds the pilot's.

### The usage investigation's other six recommendations, one line each

The draft above weighs recommendations 1 (A4), 4 and 6 (R7), 5 (R8) and 8 (R9). The rest:

- **Rec 3, separate occupancy, spend and progress rails (`:219`).** Already separate in sage-claude: the occupancy rung, rail 4, and the failure ladder's same-signature stop. No change.
- **Rec 7, bound worker occupancy and return size (`:258`).** sage-claude bounds reports at 1–2k tokens and measured the handoff note at 5–8k. No change.
- **Rec 9, reuse a verifier thread only for a tight re-check (`:274`).** This is sage-claude's own rule, cited back from its memory. No change.
- **Rec 10, replace the blanket 4× with named cost profiles (`:280`).** Touches the open KI `gap-4x-budget-multiplier-may-be-consumed`, which records that every past ceiling raise was spent up to the new ceiling. A profile is a differently named ceiling and does not answer a consumption pattern. Rejected; the KI stays open, and the honest estimate-versus-actual journal line remains the instrument.
- **Rec 11, record quota before and after each phase (`:290`).** sage-claude records estimate against actual per run and per unit. Per-phase adds a duty with no reader. No change.
- **Rec 12, the matched handover experiment (`:294`).** Folded into A4 as the open measurement behind it.

### Two small adaptations

**Hash the task-owned files into the handoff note.** Codex Sage's handoff carries `path, sha256, kind, device, inode` per baseline file and refuses to resume on drift (`sage-handoff-v1.schema.json:41`; `test_phase1.py:424`). sage-claude's `/sage resume` compares `git status` against Paths touched. That misses untracked and out-of-repo files, which the snapshot protocol already flags as unrecoverable. Add one `sha256sum` line per task-owned path to the note's Snapshot baseline field, and have `/sage resume` re-run it. One command each way.

**Name the spend figure's provenance in the cell.** Codex Sage tags every usage value `measured | provider-reported | estimated | unknown` (`2026-08-31-sage-codex-proposal.md:728`). sage-claude's journal already writes "transcript-measured" and "notif counters read zero" by hand. Make the `actual tokens` cell carry one of `probe`, `notif`, `projection`, so rail 4 knows which kind of figure it is comparing. This is the same move as A2 for spend.

**Check `shared/` for machine-local content.** `check-phase0.py` has `host_leak_issues`, a scan for host-specific names in portable text. sage-claude's memory records two of this machine's promote passes writing a shared band down (`defect-this-machine-wrote-shared-bands-down`, now dropped with its subject). A `--corpus` lint line that flags absolute paths, session ids and `k`-suffixed figures inside `memory/shared/` is the same idea at the cost of one grep.

## Items rejected, with reasons

### R1. JSON run record as authority, Markdown as a hash-bound projection

Codex Sage makes `run.json` plus an append-only `facts.jsonl` the authority and renders `run.md` from it (`sage/scripts/sage-light.py`: `start` 353, `commit-state` 486, `append-fact` 535, `render` 559; `sage/lib/artifacts.py`). Schema and semantic validation reject illegal states before they land.

Rejected for sage-claude. The ledger's measured failures were compliance failures: ledgers written once and post-hoc, dispatches never entered, findings parked in illegal states (`SKILL.md`, Step 4, the lint paragraph). A JSON authority moves the same duty from "write the row" to "call `commit-state`". A model that skips the row skips the call. The one thing JSON buys, semantic validation, is what A1, A3, A5 and A8 take piecemeal into the text lint, at the cost of a few awk lines each. What it would cost: every state change becomes a CLI round trip through the parent's context, the working record stops being readable by a person mid-run, and a compaction-time reader loses the header comment that today re-teaches the occupancy duty from line 1. No measurement shows the JSON path produces better-kept records, because no Codex Sage run has been kept.

### R2. Immutable plan revisions

Codex Sage forbids editing an admitted plan; a change is `PlanRevision N+1` with `prior_units` dispositions (`sage-artifact-v1.schema.json:252`; `sage/policy/contracts.md:9`).

Rejected. `references/dispatch.md`, Decisions and deviations, records the audit that produced the current rule: amendments were leaving the rows they amended untouched. The fix chosen was the `superseded → D<n>` tag on the amended row plus a Decisions row, with the sentence "a fifth representation of the plan cannot fix non-compliance with the four that already exist". A revision series is that fifth representation. No new evidence has arrived since the tag rule was written, and the lint already strips the tag when it compares Plan and Unit id sets.

### R3. A run may write facts only, never observations

Codex Sage forbids the active run from recording any lesson (`sage/policy/memory.md:10-13`; `test_phase1.py:287` rejects `lesson.extracted`). Only a later promotion pass may mine the closed log.

Rejected. sage-claude's `obs` lines are written at Step 6 by the parent that holds the run's whole context, with a falsifier attached, and they flip no status. The journal shows what they are worth: run `5f8bfa2d` recorded that six of nine review findings were defects the parent's own fixes introduced, a lesson no fact log without the parent's reasoning would carry. Codex Sage's promotion pass would have to reconstruct that from facts, and it has never run on a real closed log to show it can. The point where both designs agree, that the run consolidates nothing and promotes nothing, is already sage-claude's v3 rule.

The reading half of the same Codex rule is rejected too. `sage/policy/memory.md:13` forbids an active run from scanning "raw prior ledgers, journal tails, closed logs, archives for same-shape precedent". sage-claude's Step 2 requires exactly that read: the journal tail since the last `mark` is where same-shape run lines come from, and the live shared rule `price-off-a-same-shape-row` (calibration: established) says a same-shape logged row beats band arithmetic. Adopting the Codex clause would retire that rule with no measurement against it. The Codex rule protects a Codex weakness, a root that re-reads whole logs into a 258k window; sage-claude reads a few tail lines into a 1M window and records on the `use` line whether each read helped.

One adjacent field gets a verdict here rather than nowhere: Codex Sage's promotion candidate carries `expected_benefit`, `expected_cost` and a `net_assessment` (`promotion-contract.md:17`; `knowledge-record-v1.schema.json:85`). Rejected. sage-promote already gates every candidate with a falsifier and a refuting degradation gate; a self-declared net assessment is a field the author fills in its own favour and no later stage reads.

### R4. Capability negotiation, runtime protocol v0, `sage-core`, Managed mode

The proposal's architecture sections 2 to 5 and the `sage/runtime/protocol-v0/` schemas define principals, capability snapshots, observation envelopes, leases with fencing tokens and crash-safe dispatch.

Rejected for now. Claude Code exposes no scheduler, lease or approval surface for a core to own, and the proposal's own Phase 2 gate, which was to decide whether Managed mode is needed, never ran. The usage investigation's numbers show what building the design's first two phases cost without a single evaluated run. sage-claude's design already names its enforcement gaps honestly (`references/harness.md`, "Cautions"). Reopen only if a measured run shows a failure that a saved agent file, a hook or a script cannot close.

### R5. The receipt-bound installer

`sage/lib/lifecycle.py` (2,517 lines) and 13 tests in `LifecycleTests` implement an ownership receipt with journal phases, resource identities, backups and recovery from interruption at every phase.

Rejected as a port. `install.sh` already keeps timestamped backups outside the auto-discovered directories and writes manifests that `uninstall.sh` reads to decide what it owns (`install.sh:121-142`; `uninstall.sh:197-216`). The installer defects sage-claude has measured, a `.bak` clobbered on the second install and a guard testing `[ -f ]` on a directory, were found by the installer-execution verifier in Step 5 and fixed. No incident of an interrupted install or an unrecoverable uninstall exists locally. The receipt design solves a problem that has not occurred, in a language the installer does not use. Keep the execution-verifier check. Revisit if an uninstall ever removes something it did not own.

### R6. Placement by requirement vector instead of tier

Codex Sage records `corpus_size, ambiguity, reasoning_steps, tool_needs, latency_preference, cost_ceiling, independence_required, verification_criticality` per unit and resolves them through a host profile (`sage-artifact-v1.schema.json:171`; `sage/policy/delegation.md:72`).

Rejected. sage-claude's tier table is resolved against the live session at Step 2 and already crosses tier with step count (`references/harness.md`, "Models and effort"). The requirement vector has no calibration behind it, and it adds eight fields per unit that the parent fills by judgment, which is the same judgment the tier column records in one word.

### R7. Lower fan-out and the model-placement profile from the usage investigation

Recommendations 4 and 6 (`codex-vs-claude-sage-usage-investigation.md:231, 254`) cap fan-out at two concurrent children and three total, and move the root off the top model.

Rejected as Codex-specific. The spend pathology they answer is a root on maximum reasoning at twenty times the cheap model's cached rate, across thousands of cycles. sage-claude runs the parent on the apex model by a stated design decision (`references/harness.md`, "The parent is apex's real home"), caps at four, and prices every run against its own estimate. The evidence does not transfer. One mechanism in the recommendation is already in place: no child inherits the parent's model silently, because every dispatch names its model.

### R8. Cycle and compaction rails

Recommendation 5 adds rails at 25 root turns and 50 tool calls, and on compaction count.

Rejected. The numbers are unmeasured, and sage-claude's rails are multiples of the run's own estimate with floors (`SKILL.md`, Rails). The local analogue of runaway parent cost, run `87b40637` where the parent came in 60% over while the fleet came in under, was priced wrong, not counted wrong. A4 addresses the compaction side.

### R9. Root and successor overlap

Recommendation 8 (`:270`) wants the old root to supervise only unresolved handles after handover and to stop substantive work, and to record the overlap cost.

No change. sage-claude's supervisor mode already limits the parent to steers, rails, the watchdog and one spot check (`SKILL.md`, Handover, "Supervisor mode"), and `## Handover` already orders every generation's supervision cost onto the `run` line. The recommendation describes the current design.

### Not adoptable because they are ports

Explicit-only activation, the six-step spine, the four axioms, the safe-and-worth tests, the topology catalogue, the failure ladder, the four rails, the snapshot protocol, one writer per tree, disjoint review lenses, the blind acceptance suite, the completeness critic, and the clean-code and diff-review policies in `sage/policy/implementation.md` and `software-review.md` are ports of sage-claude text. `sage/docs/phase1/equivalence.md` says so. Nothing comes back from them.

## Two things that look strong and are not

**The 63 invalid fixtures and 44 tests.** They prove that the Python library rejects the states its own schema forbids. They prove nothing about whether a Codex root model writes those states in a real run, because none has been recorded. The lint in sage-claude states the same limit about itself: it "reads legality, never liveness". Fixture count is not evidence of kept records.

**The sixteen-row guarantee table.** It reads as rigour, and A9 takes its form. But its content for Codex Light is mostly "advisory", "policy bookkeeping", "unknown unless supported". It is an honest inventory of what Codex Sage cannot enforce. It is not a list of things sage-claude lacks.

## What this proposal does not settle

- The handover reserve in A4 has no measured value and starts as an estimate labelled as such. Seven occurrences of the misfire are the evidence for changing the response, not for a number.
- A6 keeps three confirmations for empirical rules by inertia. No local evidence says three is right either. It says only that six has none.
- The Codex Sage test suite's portability defect was patched in a scratch clone for this study and not in the repository. Whether to fix it in `sage/tests/test_phase1.py` is a Codex Sage decision, outside this proposal's scope. It is one `sed` of `dir="/private/tmp"` to `dir="/tmp"`, or a `tempfile.gettempdir()` call.

## Order of work, if adopted

1. A2 and A8: script changes only, each testable against the ledgers already under `.claude/plans/`.
2. A1, A3, A5: template plus lint, one review round.
3. A9, A10, the two small adaptations: reference and grammar edits.
4. A4: a `SKILL.md` Handover edit, gated by the two-arm behavioural lens because it changes what the parent does at a rung.
5. A6 and A7: edits to `claude-skills/sage-promote/SKILL.md`. That skill's write table (`SKILL.md:17-26`) has no row for its own file, and the journal records the standing rule that it never touches it. Land them the way the memory's escalation did: a `/sage` run on the user's explicit word, verified by the two-arm behavioural lens.
6. A11: unscheduled; a design kept against two open gap KIs.

Every item above is a corpus edit to behaviour-shaping text, so `references/authoring.md` governs its form, and `references/topologies.md` #12 governs its verification.
