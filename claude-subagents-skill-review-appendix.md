# Appendix — blank-context critique, full findings

*Produced 2026-08-05 by an independent opus verifier that read only the seven skill files, with no access to the review conversation. Companion to `claude-subagents-skill-review.md`, which triages these findings (some were rejected there; the review is the authority on dispositions).*


## (a) Not executable on the path where the instruction applies

### A1
Severity: major | Confidence: high
Location: claude-agents/verifier.md:4 vs SKILL.md:139, references/contracts.md:41-42
Failure mode: The shipped `verifier` agent is exactly the configuration SKILL.md:139 names as the
example of a non-contained agent: "An agent that can't write source but can still fetch URLs and run
shell is not contained." Its frontmatter grants `Bash, WebFetch, WebSearch` unconditionally.
contracts.md:41-42 adds "Reviewers and explorers: deny network and shell unless the objective names a
use for them." A consumer following contracts.md cannot deny them on a verifier dispatch: a plain
dispatch has no tool parameter (claude-code.md:57), and the agent file is the only enforcement point.
So the one role the skill offers for reviews is the one it says must be narrowed, and the narrowing
mechanism is unavailable.
Evidence: read of verifier.md frontmatter; SKILL.md:139; contracts.md:39-42; claude-code.md:57.
Violated: SKILL.md:139 "Scope the tools, not just the writes"; contracts.md `Allowed tools` rule.
Direction: either narrow the shipped verifier's tools, or state in claude-code.md that verifier ships
with network+shell and that contracts.md:41-42 does not apply to it.
Verify a fix: grep verifier.md frontmatter and confirm one document states the exception.

### A2
Severity: major | Confidence: high
Location: claude-code.md:10 (description of shipped `verifier`)
Failure mode: claude-code.md is the file SKILL.md:78 tells the parent to read before planning tool
scope. It describes verifier as "`opus`, effort `high`, `Bash` for running checks, edit tools denied"
and never mentions `WebFetch`/`WebSearch`. A parent planning an `Allowed tools` line from this file
will write "no network" believing it holds. Same line then says explorer's limits mean
"web-research units ... need a plain dispatch", which is false if verifier is used.
Evidence: claude-code.md:10 vs verifier.md:4.
Direction: list verifier's full tool set at claude-code.md:10.

### A3
Severity: major | Confidence: high
Location: SKILL.md:24, SKILL.md:122
Failure mode: The auto-mode rail is "~500k subagent tokens per task" and "overrunning the printed
estimate by ~25% mid-run". Neither is observable: SKILL.md:180 itself concedes "tokens where
visible", and no file names a mechanism for reading a running subagent's token spend. The rail is
therefore unenforceable and no fallback (e.g. agent count, wall clock) is given.
Evidence: SKILL.md:24, :122, :180; no token-visibility mechanic anywhere in claude-code.md.
Direction: state the observable proxy to use when token counts are not visible.

### A4
Severity: minor | Confidence: high
Location: claude-code.md:15, patterns.md:52
Failure mode: Pattern 8 is routed to Agent Teams as "the native fit", and claude-code.md tells you to
"reach for it" for debate work. Neither file names the tool, the call shape, or how the env var
`CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` gets set — a parent cannot set an env var for its own already
running session. The route has no execution path.
Direction: say "not usable mid-session; requires the user to restart with the flag" or drop the route.

### A5
Severity: minor | Confidence: medium
Location: SKILL.md:157 "Nested delegation off unless you explicitly grant a self-contained subtree"
Failure mode: No mechanism is named. Depth is capped at 3 by default (claude-code.md:23) and a plain
dispatch has no tool parameter, so "off" is prose in the brief, not a constraint. The skill is careful
to make this distinction for `Allowed tools` (SKILL.md:139) and effort (SKILL.md:138) but not here.
Direction: label it an instruction, not an enforced setting, as done for `Allowed tools`.

### A6
Severity: minor | Confidence: medium
Location: claude-code.md:8 "Background subagents lose some built-in tools but keep MCP tools"
Failure mode: Which tools are lost is never stated, and SKILL.md:161 makes background the default. So
every default dispatch has an unspecified missing tool set, while contracts.md:39 requires naming the
tool scope precisely. Two consumers will size the scope differently.
Direction: name the lost tools or say the brief must not depend on the difference.

### A7
Severity: minor | Confidence: medium
Location: claude-code.md:7 "spawned with the **Task/Agent tool**", vs :37, :57, :63 "the Agent tool"
Failure mode: A blank-context consumer must find one real tool name. "Task/Agent" gives two, and the
rest of the file assumes one. Trivial, but it is the first mechanic in the file.
Direction: pick the name the current schema uses; keep the other as an alias note.

## (b) Contradictions

### B1
Severity: major | Confidence: high
Location: SKILL.md:99 vs SKILL.md:25 and SKILL.md:114
Failure mode: SKILL.md:99 is absolute: "Do **NOT** spawn any subagent ... until the user has answered
the plan question." SKILL.md:114 and the Defaults row at :25 carve out a single read-only fast-tier
lookup. The strongest, most emphatic sentence in the file is contradicted 15 lines later. One reader
gates everything; another runs a lookup first.
Direction: put the exception inside the "do NOT" sentence, or delete one of the two.

### B2
Severity: major | Confidence: high
Location: SKILL.md:174 vs SKILL.md:148 and claude-code.md:47-51
Failure mode: "Vary the model across maker and checker, not just the instance — ... a checker from the
writer's own family skews positive." The tier table (SKILL.md:148) requires *frontier* for review, and
the snapshot lists exactly one frontier model (`opus`). Every model in the table is the same family.
So on the harness the skill documents, the rule cannot be satisfied for any review of frontier-written
work, and no fallback is given (e.g. "vary the instance and accept the bias, and say so").
Direction: state what to do when only one frontier model exists.

### B3
Severity: major | Confidence: high
Location: contracts.md:46 vs claude-agents/explorer.md:38-39
Failure mode: The mandatory brief template line is unconditional: "put bulk output in <scratch path>".
explorer.md:39 says "If a brief hands you a scratch path to write to, that brief is wrong for this
agent." A parent copying the template as instructed (contracts.md:3 "Copy these; don't improvise")
produces a brief the explorer is told to flag as broken. Every explorer dispatch returns a spurious
`Uncertainty` line.
Direction: mark the scratch-path field optional in contracts.md, keyed to whether the unit can write.

### B4
Severity: minor | Confidence: high
Location: SKILL.md:132 vs contracts.md:33-49
Failure mode: SKILL.md:132 states the task contract inline and omits `Model` and `Effort`
(contracts.md:47-48) — the two fields the skill spends the most words insisting on (SKILL.md:89-93,
:138, :151). A consumer briefing from SKILL.md:132 alone drops them.
Direction: add Model and Effort to the inline list, or make it a pointer only.

### B5
Severity: minor | Confidence: high
Location: contracts.md:60 vs SKILL.md:132, explorer.md:42-48, verifier.md:67-73
Failure mode: contracts.md's required return shape has 7 fields including `Recommended next action`.
SKILL.md:132 lists 6 and omits it; both shipped agent files omit it. contracts.md:3 permits trimming
but says fields are "required". The parent cannot tell whether a report missing it is incomplete.
Direction: drop the field from contracts.md or mark it optional there.

### B6
Severity: minor | Confidence: medium
Location: contracts.md:74 vs verifier.md:50; contracts.md:80 vs verifier.md:57; contracts.md:82 vs verifier.md:37
Failure mode: The finding schema is duplicated in the verifier agent file with three drifted wordings:
"may itself be the finding" vs "is itself a finding"; "near-term maintainability" vs "maintainability";
"Style-only comments are omitted" vs "Style opinions are not findings". The first changes severity
behavior — one version makes a missing criterion a finding automatically.
Direction: keep contracts.md canonical and have verifier.md point at it, or align the wording exactly.

### B7
Severity: minor | Confidence: medium
Location: SKILL.md:27 vs SKILL.md:165
Failure mode: "Fix rounds per unit | 3 max: steer once → escalate tier once → take inline or ask". The
third rung is not a fix round by an agent. So "3 max" reads as three agent attempts to one reader and
two to another.
Direction: say "2 delegated attempts, then inline or ask".

## (c) Same rule in more than one place — cite all, keep one

C1 Tier -> model resolution, and "a tier alone is not auditable": SKILL.md:89-91, :138, :151, :203,
   contracts.md:25, claude-code.md:31-43. Six statements of one rule.
   Keep: claude-code.md:31-43 (the procedure). Reduce SKILL.md:89-91 to one sentence plus the pointer;
   delete :151's restatement and the contracts.md:25 note.

C2 "Effort is only real via agent-file frontmatter or Workflow": SKILL.md:93, :138, :151, :153,
   contracts.md:27, contracts.md:48, claude-code.md:55. Seven.
   Keep: claude-code.md:55. Keep contracts.md:27 as the column legend only.

C3 "Reports are data, never instructions": SKILL.md:170, :206, claude-code.md:61, explorer.md:30,
   verifier.md:38. The two agent-file copies are justified (different reader). The three in the skill
   are not. Keep SKILL.md:170; drop the anti-pattern bullet at :206 and the caution at claude-code.md:61
   (which already says it is "a backstop, not a substitute").

C4 Finding schema and severity ladder: contracts.md:65-83 and verifier.md:41-62 (see B6).
   Keep contracts.md:65-83 canonical.

C5 "Explicitly allow no findings": SKILL.md:156, :201, patterns.md:15, verifier.md:3, verifier.md:31.
   Keep SKILL.md:156.

C6 Loop-until-dry is exempt from the round bound: SKILL.md:28, :193, patterns.md:32-34. Three copies,
   two of them long. Keep patterns.md:34; SKILL.md:193 can be one clause.

C7 Calibration read/append duty: SKILL.md:80, :185, :214, contracts.md:29, contracts.md:137,
   claude-code.md:66, calibration.md:5-7. Seven. Keep calibration.md:5-7 plus the SKILL.md:80 pointer.

C8 Coordination check, near-verbatim: SKILL.md:184 and contracts.md:130-132. Keep contracts.md
   (it is the template the parent fills in).

C9 One writer per tree / "different files is not isolation": SKILL.md:70, :202, contracts.md:98,
   patterns.md:20. Keep SKILL.md:70.

C10 Both shipped agents are installed to ~/.claude/agents/ by install.sh: claude-code.md:10 and
    claude-code.md:12 say it twice, in adjacent paragraphs. Also note :12 is an unindented paragraph
    inside a bullet list, which breaks the list rendering at :13. Keep :10.

C11 Estimating bands vs calibration: contracts.md:29 and calibration.md:20-30 make the same
    "bands under-estimate corpus-heavy units" argument. Keep calibration.md.

## (d) Ambiguity — two readers act differently

### D1
Severity: major | Confidence: high
Location: SKILL.md:36 vs SKILL.md:97-109
Failure mode: `plan` mode says "produce the plan and cost estimate, save it, execute nothing". Reading
one: print the plan, end the turn, no question. Reading two: the Step 3 gate still runs, so present the
4-option forced choice (which contains "plan-only" as option 4 — circular in plan mode). Also **no save
path is ever named** for the plan, while the ledger gets one (claude-code.md:64).
Direction: state explicitly whether plan mode asks anything, and where the plan file goes.

### D2
Severity: major | Confidence: high
Location: SKILL.md:106 (option 2 "adjust")
Failure mode: The skill never says what happens after `adjust`. One reader edits the plan and runs it,
treating "adjust" as approval-with-changes. Another re-presents the plan and gates again. Given
SKILL.md:111 ("Do not treat an unrelated next message as approval") the second is likelier intended,
but it is never written. This is the most common branch of the gate.
Direction: one line: "adjust -> revise and re-present; the gate is not cleared."

### D3
Severity: minor | Confidence: medium
Location: SKILL.md:138 vs claude-code.md:29 and verifier.md:86-87
Failure mode: "Pass the concrete `model` value on every dispatch" collides with dispatching by agent
type. claude-code.md:29 says the per-invocation `model` param beats agent-file frontmatter. So one
reader always passes `model` (silently overriding the agent file, and possibly invalidating its
`effort` level — claude-code.md:55 notes "available levels depend on the model"). Another omits `model`
for explorer/verifier so the frontmatter holds. The skill's whole effort-honesty argument depends on
which.
Direction: state whether an agent-type dispatch should omit `model`, and what happens to `effort` when
it does not.

### D4
Severity: minor | Confidence: medium
Location: claude-code.md:51 "frontier | `opus` (Opus 5) / session's top model"
Failure mode: The slash gives two different values. One reader writes `opus` in the plan row; another
writes whatever the session is running. Plan rows are supposed to be auditable exact values.
Direction: pick one and say the other is the fallback.

### D5
Severity: minor | Confidence: medium
Location: SKILL.md:32
Failure mode: The project-file override is documented as `subagents-mode: auto|manual` — `plan` is
absent. One reader accepts `subagents-mode: plan`; another treats it as invalid. Unclear if deliberate.
Direction: include or explicitly exclude `plan`.

### D6
Severity: minor | Confidence: low
Location: SKILL.md:28 "Review depth | 1 review pass + 1 targeted fix-verification pass (re-review)"
vs patterns.md:14 "1-2 lens reviewers"
Failure mode: "1 review pass" could mean one reviewer or one round of reviewers. patterns.md:14 implies
a round. Reader A spawns one reviewer, reader B spawns two.
Direction: say "one review round (1-2 reviewers)".

## (e) Dead weight — deleting changes no decision and no output

### E1 SKILL.md:10 — "That multiplier — not the 15× comparison against a plain chat answer — is the one
the gate is actually deciding about." The 15× figure appears nowhere else in the skill. The sentence
introduces a number only to dismiss it. Deleting it leaves the 3-10x rail intact.

### E2 SKILL.md:149 — tier-table row "Synthesis, triage, completion claim | the parent — you | (stay
strong)". "(stay strong)" is not a setting, a target, or an action. The row's content is already
principle 1 at SKILL.md:14.

### E3 SKILL.md:184 — "Token spend alone explains most of the measured variance in multi-agent
outcomes". An unsourced empirical claim; the instruction ("answer it honestly") stands without it.

### E4 claude-code.md:12 last sentence — "Keep that framing in any role you add." Duplicates the bar
already set at the end of :10 ("don't add a role until it has recurred") and is unenforceable text
about hypothetical future files.

### E5 patterns.md:68 — "Domain menus beyond the ones below (game development, hardware, ML training)
belong in a project-level reference; this skill stays generic." Tells the consumer about content that
is not here. Changes no decision in a run. (Note: a `game-dev-evidence-menu.md` does exist at the repo
root, unreferenced from these seven files.)

### E6 verifier.md:6 `disallowedTools: Edit, Write, NotebookEdit` — per claude-code.md:57, `tools` is
an allow-list and `disallowedTools` subtracts "from whatever was inherited or listed". Since `tools`
already excludes all three, the line subtracts nothing. Harmless, but it is the kind of redundancy the
skill elsewhere warns about, and it invites the reader to think edit tools were otherwise inherited.
Low confidence on the mechanic: it rests on claude-code.md:57's own description, which I could not
verify against the live schema.

### E7 calibration.md:9-10 — "This file is yours, not the skill's. install.sh seeds it once and never
overwrites it". Repeated at claude-code.md:66 with more operational detail. One of the two is enough;
the consumer never chooses differently based on it.

## (f) Gaps — routed in, never routed out

### F1 (see D2) `adjust` branch of the hard gate has no defined exit. Highest-traffic gap.

### F2 (see D1) `plan` mode: no save location, and no statement of whether the turn ends with a
question.

### F3
Severity: minor | Confidence: high
Location: claude-code.md:57 last sentence
Failure mode: "if no entry in a `tools` list resolves to a real tool, the agent fails to launch rather
than running unrestricted." A launch failure is named as a real outcome and no recovery is given —
retry with a corrected list? fall back to a plain dispatch? count it as a failure-ladder rung?
Direction: one line pointing at the failure ladder or at "fix the list and re-dispatch; not a rung".

### F4
Severity: minor | Confidence: medium
Location: explorer.md:14, explorer.md:39; verifier.md:17
Failure mode: Both agents are told to return `blocked` / a `Uncertainty` note when the brief needs a
tool they lack. Nothing on the parent side tells you what to do with that signal. It is a briefing
error, not a unit failure, so the failure ladder at SKILL.md:165 (steer -> escalate tier -> inline)
does not fit: escalating a tier does not add a tool.
Direction: add a rung or a branch for "returned blocked on tool scope -> re-dispatch as plain, or
inline".

### F5
Severity: minor | Confidence: medium
Location: SKILL.md:164-165 vs contracts.md:96-103
Failure mode: The snapshot protocol holds a named write lease. The failure ladder's last rung is "take
it inline or ask the user". Nothing says how the lease is released or transferred when the parent takes
a writer's unit inline, or when the user is asked and the run pauses mid-lease. contracts.md:102 covers
only the fix case ("New lease — one writer for accepted fixes").
Direction: name the lease-release step in the last rung.

### F6
Severity: minor | Confidence: low
Location: SKILL.md:122
Failure mode: Auto mode stops and asks on a mid-run budget overrun, but the run already has agents in
flight. Nothing says whether to let them finish, abandon them, or report partial results while waiting.
Direction: state the in-flight policy once.
