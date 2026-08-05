# Review of the `subagents-claude` skill — issues and recommendations

*Written 2026-08-05 against repo HEAD (`e435e86`). The repo copy and the installed copy in `~/.claude/` are identical (verified by `diff -rq`). Line numbers refer to the repo files.*

*Method: I read all seven files directly. Five subagents supplied independent evidence: a blank-context critique of the skill text (opus, 30 findings — full detail in `claude-subagents-skill-review-appendix.md`), a docs fact-check against code.claude.com (sonnet, claude-code-guide), two no-op probes that measured dispatch cost, and an adversarial refuter (opus) that attacked every proposal in this document before it was finalized. §9 records what the refuter killed or weakened; every number and fix below already reflects that pass.*

## 1. Verdict

The skill is sound. All ten items from `graph-loop-subagents-recommendations.md` landed, the contracts are the strongest part, and nothing found here is a blocker. Four problems are worth fixing:

1. The shipped `verifier` agent has unconditional network access, and `claude-code.md` — the file plans are drafted from — misdescribes its tool surface (§3 M1).
2. Several branches the skill routes you into have no defined exit: `plan` mode, the `adjust` answer, a `blocked`-on-tool-scope return — and the gate's decision dialog shows only summary counts, not the per-agent rows the user is supposed to audit (§3, M6).
3. The skill's memory learns costs but not mistakes: coordination-check verdicts, stalls, and gate regrets die with the session (§8).
4. On the compaction question: the model cannot see a usage percentage and cannot trigger compaction, so a "compact at 50%" rule is not implementable in skill prose. The implementable pieces are a checkpoint rule and the harness knobs that already exist (§4).

On size (§5): honest arithmetic, after adversarial measurement, says the realistic cuts are ~590 words gross and the fixes above add ~410 back. Net is roughly flat, about −2%. The dedup is still worth doing — it funds the fixes — but "much shorter and also more capable" is not on the table without a riskier style rewrite.

## 2. Measured baseline

| File | Words | Loaded when |
| --- | --- | --- |
| `SKILL.md` | 3,366 | every invocation |
| `references/claude-code.md` | 1,306 | every planning run (Step 3) |
| `references/contracts.md` | 1,291 | every planning run (templates) |
| `calibration.md` | 424 | every planning run (Step 3) |
| `references/patterns.md` | 920 | only when picking a topology |
| `claude-agents/explorer.md` | 450 | inside each explorer dispatch |
| `claude-agents/verifier.md` | 716 | inside each verifier dispatch |

(The refuter re-measured this table independently; it is exact.) A full orchestrated run loads ~6,400–7,300 words of skill text (~9–10k tokens) into the parent. Step 3 (646 words) and Step 4 (545 words) are 35% of `SKILL.md`, and both are dominated by the model/effort rules that repeat elsewhere.

Dispatch cost, measured this run with no-op probes (haiku, zero tool calls, this machine):

| Dispatch path | Total tokens |
| --- | --- |
| `explorer` (tools: Read/Glob/Grep) | 4,962 |
| `general-purpose` (all tools) | 16,036 |

The ~11k gap is startup context. Per the sub-agents doc (fetched this run): custom and general-purpose subagents load the full CLAUDE.md hierarchy plus a git snapshot, and MCP schemas load on demand — so the gap is mostly built-in tool schemas and the deferred-tool name list. The absolute numbers are machine-specific (they include this machine's CLAUDE.md files); the ~3× ratio is the durable fact. These numbers drive §6 and §7.

## 3. Issues

Majors first; all were found independently by the blank-context agent, confirmed by me against the files, and then re-tested by the refuter. Fixes shown are the post-refutation versions.

**M1 — the shipped `verifier`'s network access is unconditional, and the planning doc misdescribes it.** `verifier.md:4` grants `WebFetch, WebSearch` with only a purpose note (`:80-82`), while `contracts.md:41-42` tells briefs to deny reviewers network unless the objective names a use — a denial no brief can enforce on this agent (`claude-code.md:57`). And `claude-code.md:10`, the file the parent plans tool scope from, describes verifier as "`Bash` for running checks, edit tools denied" without mentioning the network tools at all, so a plan can honestly write "no network" that does not hold. Note the refuter's correction: Bash is *not* part of the gap — `verifier.md:13-17` already binds it to verification-only. Fix (2 lines): list the full tool set at `claude-code.md:10`; add to `verifier.md`: "If the brief does not name a network use, do not fetch." Instruction-level, but it makes brief denials meaningful to the one agent that reads them.

**M2 — the maker/checker diversity rule is unsatisfiable at frontier.** `SKILL.md:174` requires varying the model family between maker and checker; `SKILL.md:148` routes verification to frontier; the snapshot at `claude-code.md:47-51` lists one frontier model. When the maker ran on it (the common case: the parent's own drafts), no compliant checker exists. Fix: amend `:174` itself, so rule and fallback are one sentence: "…skews positive. When no second frontier model exists, use a standard-tier checker with a tight brief for diversity, or accept the same-family check and record the residual bias in the report." (First draft said "vary the instance," which contradicted the very words at `:174` — refuter catch.)

**M3 — two gate branches have no defined next step.** `plan` mode (`SKILL.md:36`) never says whether the gate question is asked (option 4 of that question is "plan-only" — circular in plan mode) or where the plan is saved, while the ledger does get a location rule (`claude-code.md:64`). The `adjust` answer (`SKILL.md:106`) never says whether to revise-and-run or re-gate. Fix (2 lines): plan mode saves to the scratchpad (or a user-named path), prints the plan, ends the turn, asks nothing; `adjust` applies the change, re-presents the changed rows, and still runs only on `go`.

**M4 — (trivial after refutation) the hard gate reads as contradicting the approval floor.** `SKILL.md:99` is absolute; `:25` and `:114` carve out one lookup. The exception is explicit, so no decision actually changes — but the blank-context reader stumbled on it, and five words fix it: add "(one exception: the floor below)" at `:99`.

**M5 — the brief template tells every agent to offload to a scratch path; the explorer cannot write.** `contracts.md:46` is unconditional ("Copy these; don't improvise", `contracts.md:3`); `explorer.md:38-39` correctly flags such a brief as wrong. Every templated explorer dispatch returns a spurious `Uncertainty` line. Fix (1 line in the template): "(omit the scratch path for units that cannot write — `explorer` distills instead)."

**M6 — the gate's decision surface drops the per-agent detail the gate exists to audit.** Step 3 requires presenting the full per-agent table (unit, model, effort, cost), but the forced-choice template at `SKILL.md:103-109` carries only counts ("N agents (M parallel), est. ~X tokens"), and the preferred path — the harness's structured-question tool (`SKILL.md:101`) — makes it worse: the question renders as its own dialog, so the table printed in earlier prose detaches from the choice and is easy to miss at decision time. The user then approves counts, which is the same "nothing to audit" failure Step 3 warns about at `:89`. Observed on this review's own gate: the table was printed in full and still read as absent when the dialog appeared (user report, 2026-08-05). Fix (2 lines in `SKILL.md`, 1 in `claude-code.md`): the audit fields must be in the decision surface itself — in Claude Code, attach the plan table as the markdown `preview` on the `go` option of `AskUserQuestion` (previews are supported on single-select questions), and on an `adjust` re-ask, preview the changed rows; where no preview mechanism exists, the full table must be the last thing printed immediately before the question, never summarized to counts.

Minors that survived refutation, each with a ≤1-line fix:

| ID | Location | Problem | Fix |
| --- | --- | --- | --- |
| N1 | `SKILL.md:24`, `:122` | the token half of the auto rails needs telemetry the harness may not show (current versions show it in completion notifications) | when token counts are absent, the agent-count and wall-clock rails govern; say so in the report |
| N2 | `SKILL.md:27` | "3 max" counts the escape hatch as a fix round | "2 delegated attempts, then inline/ask" |
| N3 | `SKILL.md:132` | inline brief summary omits `Model` and `Effort`, the two fields the skill argues hardest for | add the two words |
| N4 | `SKILL.md:157` | "Nested delegation off" reads as a setting; only the global depth cap (`claude-code.md:23`) enforces anything | "(brief text; only the depth cap enforces)" |
| N5 | `SKILL.md:165` | a `blocked`-on-tool-scope return has no parent branch, and the ladder cannot fix it (a tier adds no tool) | scope-`blocked` is a briefing error: fix the brief or re-route; it costs no rung |
| N6 | `contracts.md:95-105` | lease release undefined when the parent takes a writer unit inline, or when the run pauses to ask the user | inline transfer moves the lease to the parent; pausing freezes it; log either |
| N7 | `SKILL.md:116-124` | budget-stop leaves in-flight agents' fate implicit | six words: in-flight units finish; nothing new launches |
| N8 | `claude-code.md:57` | launch failure from an unresolvable `tools:` list has no recovery | correct the list and re-dispatch (repo copy too, or `install.sh` reverts it); not a ladder rung |
| N9 | `claude-code.md:8` | "lose some built-in tools" unspecified while background is the default | name the set per current docs, or say briefs must not depend on the difference |
| N10 | `calibration.md:1-3` + seed rows | the seed ships the author's real rows under a header claiming local actuals | tag them `(seed)`; one header line explaining them |
| N11 | `SKILL.md:153` ↔ `claude-code.md:10` | circular cross-reference on the add-a-role bar | state it once, in `claude-code.md` |
| N13 | `verifier.md:41-62` | finding schema drifted from `contracts.md` in three places ("may itself be" vs "is itself" a finding; "near-term maintainability" lost) | align wording exactly; keep the copy (separate context) |
| N14 | `claude-code.md:7` | "Task/Agent tool" vs "Agent tool" | pick "Agent" |
| N15 | `SKILL.md:138` + `claude-code.md:55` | "pass `model` on every dispatch" collides with agent-type dispatches, where frontmatter is the promised value and an override can invalidate `effort` (levels depend on model) | edit both lines to one rule: name the model on plain dispatches; on saved-agent dispatches the frontmatter is the named value — override only as a deliberate, logged deviation |
| N16 | `claude-code.md:15`, `patterns.md:52` | Agent Teams route has no execution path from a running session | "(env-var opt-in — a user decision)" |
| N19 | `SKILL.md:28` | "1 review pass" reads as one reviewer or one round | "one review round (1–2 reviewers; adversarial verification keeps its own counts)" |

Dropped after refutation: N12 (calibration already carries a wall-clock column — the pointer is a nicety), N17 (the resolution procedure already yields one value; the snapshot cell is cosmetic), N18 (the `auto|manual` enumeration is exhaustive as written), N20 (`<if any>` already marks the field optional). Also rejected from the blank-context list: cutting `verifier.md:6` `disallowedTools` (8 tokens of defense against a future allow-list edit — keep).

## 4. Area 1 — act on compaction at a context threshold

**Recommendation: no model-side percentage trigger — that control does not exist. Add a slim checkpoint rule for the one real gap, and document the harness knobs that let the *user* set the threshold.**

Facts, fetched from code.claude.com this run by the docs agent (env/command names drift; reverify at edit time, as `claude-code.md:3` already requires):

- The model has no readout of context usage. `context_window.used_percentage` feeds the user's status line only; hook payloads carry no token figures; no early-warning hook exists.
- The model cannot trigger compaction. `/compact` is user-typed; auto-compact belongs to the harness.
- The user can already set the threshold: `/autocompact <size>` (persists `autoCompactWindow`), `CLAUDE_CODE_AUTO_COMPACT_WINDOW`, and `CLAUDE_AUTOCOMPACT_PCT_OVERRIDE` (1–100, fires earlier only, applies to subagents too — and yes, that last name really lacks the `CLAUDE_CODE_` prefix). `PreCompact`/`PostCompact` hooks fire on both manual and auto compaction.

So "act at 50%" splits into three parts, two already solved:

1. *Keep agent output from filling the context* — solved: 1–2k report caps (`SKILL.md:26`), artifacts-not-transcripts (`:137`).
2. *Compact earlier than the default* — a harness knob, not skill prose. `CLAUDE_AUTOCOMPACT_PCT_OVERRIDE=50` does literally what the question asks. A prose rule keyed to a percentage the model cannot check would repeat the defect the skill fixed when it dropped prompt-text effort ("a number that nothing applies is worse than a blank," `SKILL.md:93`).
3. *Survive compaction without losing orchestration state* — the real gap. The ledger updates "on every state change" (`contracts.md:118`), but between launching a wave and integrating it the parent holds plan intent that exists nowhere on disk.

Proposed text — Step 5, one bullet (~2 lines; the refuter trimmed the restatements out of my first draft):

> - **Compaction can land at any moment.** Bring the ledger current before launching a wave and after each integration; after a compaction, re-read it before dispatching anything new.

And one caution in `claude-code.md` (~2 lines): the model cannot see usage or trigger `/compact`; users who want an earlier threshold set `CLAUDE_AUTOCOMPACT_PCT_OVERRIDE` or `/autocompact`; a user-side `PostCompact`/`SessionStart(compact)` hook echoing the ledger path re-anchors a long run. Optionally, `install.sh` prints that hook snippet as a suggestion.

## 5. Area 2 — make the skill shorter without losing function

**Recommendation: take the ~590 words of true duplication and rationale; they fund the ~410 words of fixes in §§3-4-6-7-8. Net size stays roughly flat. Do not expect more: the refuter measured every cited range, and eight of my fourteen first-draft savings claims were overstated.**

Independent convergence: my duplication map and the blank-context agent's agree on the offenders. Four rules carry most of it:

| Rule | Stated at | Canonical after the cut |
| --- | --- | --- |
| resolve tier → named model at plan time | `SKILL.md:89-91`, `:138`, `:151`, `:203`, `contracts.md:25`, `claude-code.md:31-43` | short form in Step 3; procedure in `claude-code.md` |
| effort only via a real control | `SKILL.md:93`, `:138`, `:151`, `:153`, `contracts.md:27`, `:48`, `claude-code.md:55` | mechanics at `claude-code.md:55`; one sentence in Step 3; the explorer/verifier exception stays |
| calibration read/append duty | `SKILL.md:80`, `:185`, `:214`, `contracts.md:29`, `:137`, `calibration.md:5-7`, `claude-code.md:66` | `calibration.md` header + one Step 3 line + one Step 7 line |
| review rounds vs discovery sweeps | `SKILL.md:28`, `:191-193`, `patterns.md:32-34` | Stop rule keeps the short form (always loaded); pattern 5 keeps the long form |

Cut list with **measured** savings (refuter-verified, not my first-draft estimates):

- **C1** `SKILL.md:89-93` → one ~70-word block (rule, resolve-at-plan-time, `haiku (fast)` format, effort-column rule). Saves ~67.
- **C2** `SKILL.md:138` → drop exactly two clauses: "Never write a tier name into the call: the dispatch takes a model, not a category" and "An effort level written into prompt text changes nothing." Saves ~23.
- **C3** `SKILL.md:151` → delete; its one unique clause moves into the `:153` paragraph. Saves ~45.
- **C4** Anti-patterns `SKILL.md:195-207` → keep the four bullets without verbatim homes elsewhere (one-agent-per-role ritual; consensus-as-done; silent model change; fleet-to-look-thorough). Saves ~100.
- **C5** `SKILL.md:165` ladder → ~90 words keeping all three rungs and both signature branches, plus the new N5 clause. Saves ~25 net.
- **C6** `patterns.md:34` stays; `SKILL.md:193` shrinks to two sentences. Saves ~31.
- **C7** `SKILL.md:182-185` → ~120 words; keep both duties, the falsify-own-premise clause, the failed-write fallback, and the variance claim as "(Anthropic's research-system data)". Saves ~68.
- **C8** `SKILL.md:95` Workflow paragraph — measured at 100 words, not my remembered 130; compressing to ~85 saves ~15. Marginal; lowest priority.
- **C9** `SKILL.md:10` drop the "not the 15×" clause (the figure appears nowhere else); `:149` "(stay strong)" becomes `—`. Saves ~11.
- **C10** `claude-code.md` → halve the resolution rationale (`:31-43`) and the Explore-vs-explorer warning (`:10`); **merge** `:12` into `:10` rather than deleting it — `:12` holds two facts that exist nowhere else the model looks (the directory is global with description-based auto-delegation; "keep that framing in any role you add"), since `install.sh` comments are not model-visible. Saves ~80.
- **C11** `contracts.md:25-29` → halve the column notes; keep the "2–5×" figure with a pointer to `calibration.md` (whose "add 60–150%" is a different number, not a substitute). Saves ~50.
- **C12** frontmatter description (`SKILL.md:3`) → ~40 words. Dormant, not dead: `claude-code.md:65` documents re-enabling auto-invocation, so note that restoring trigger phrases comes with that. Saves ~50 of parent-session listing weight.
- **C13** `calibration.md:9-10` → one line. Saves ~13.
- **C14** `patterns.md:68` → "(domain menus beyond these belong in project-level references)". Saves ~11.

What deliberately stays, even though it repeats: one point-of-dispatch reinforcement of the effort rule (the commit history shows this rule failing repeatedly; repetition bought compliance); the agent files' schema and data-not-instructions copies (separate contexts — align drift, keep copies); every template in `contracts.md`.

Arithmetic, post-refutation: gross cuts ≈ 590 (≈ 355 of them in `SKILL.md`); additions from this review ≈ 410 across the four files. Net ≈ −180 words, about −2% of a full run's fixed load; `SKILL.md` lands near 3,215. A further 400–600 words could come only from sentence-level tightening across all prose — a style rewrite that risks exactly the compliance the repetition bought. Not recommended as a batch; do it opportunistically when sections are edited anyway.

## 6. Area 3 — reduce what a subagent loads before working

**Recommendation: the architecture is already right (scoped agent files, artifact handoffs, no skills list in subagents). Make the boot economics visible where plans are written; keep the machine-specific numbers in the machine's file.**

- **R3.1** `claude-code.md`, one qualitative line: "A `tools:`-scoped agent boots several times cheaper than general-purpose — the allow-list drops the unlisted tool schemas from startup. Measure locally; see `calibration.md`." The measured rows (4,962 / 16,036, this machine) go to `calibration.md` through the normal Step 7 append — the refuter is right that absolute floors are machine-specific and belong in the file built for local actuals.
- **R3.2** `claude-code.md`, one caution: custom agents still load the full CLAUDE.md hierarchy and a git snapshot (only built-in Explore/Plan skip them) — a heavy global `~/.claude/CLAUDE.md` taxes every custom dispatch.
- **R3.3** `claude-code.md`, one caution: never dispatch a reviewer or verifier as a `fork`-type agent — forks inherit the parent's entire context, which silently destroys the clean-context property Step 6 depends on. (The refuter flagged `fork` as unverifiable from the skill files alone; it is confirmed by both the live Agent tool schema and the sub-agents doc fetched this run.)
- **R3.4** `SKILL.md:136`, four words: name line ranges only when the location is already certain; otherwise name the file and the question — a wrong range plus the explorer's no-widening rule (`explorer.md:28-29`) means silent truncation. (Refuter catch; my first draft recommended ranges unconditionally.)

## 7. Area 4 — cost efficiency without losing competence

**Recommendation: two small text changes, plus one optional new role; the quality-bearing structures are untouched.**

- **R4.1** The skill already pushes against over-spawning (`SKILL.md:55`, the fleet table, `:69`) — my first draft claimed otherwise and the refuter corrected it. What is genuinely missing is the *floor*: one clause at `:55` — "several small lookups in one area are one explorer with a checklist, not N agents; every dispatch pays a boot floor before any work (see calibration)."
- **R4.2** N1's fallback keeps auto-mode rails meaningful without token telemetry.
- **R4.3 (optional, added 2026-08-05 from a user question)** — a third saved role, `web-researcher`, when the user wants it. `claude-code.md:10` sets the bar for new roles: recurrence across real tasks. Web-research units have already recurred on this machine (two fetch-heavy calibration rows), and today they run as plain dispatches, so their Effort column reads `— (no control)`. A `web-researcher.md` closes that: `sonnet` (standard), effort `medium`, tools `WebSearch, WebFetch, Read`. Add `Write` only if the role should spill source notes to scratch files; frontmatter grants whole tools, so "scratch only" stays a brief-level instruction. Frame the description like the shipped two ("dispatched by name from an approved orchestration plan"). This is the agent class the reports-are-data rule exists for; the enforced part of its containment is keeping repo edit tools off the list. Budget from calibration: 70–120k tokens per fetch-heavy agent. It does not loosen `explorer`: the codebase explorer stays offline, which is what makes a low-effort model safe to point at arbitrary repo text.
- This run also repriced the review band in the *cheap* direction: a frontier verifier over this ~8.5k-word corpus cost 47k tokens, half the calibrated ~95k/agent row. Appending hits like this is already the file's own rule; note that the "three misses, all in the same direction" summary in `calibration.md:20` goes stale once two-sided rows exist — amend that sentence when appending, which is maintenance the file's owner does anyway.
- Quality guard: no cut in §5 touches the gate, the rails, the contracts, or the verification rules.

## 8. Area 5 — apply study-from-mistake

**Recommendation: widen `calibration.md` from a cost log to a cost-and-lessons log, with a user-approved fold rule for growth. Today every non-cost lesson dies with the session.**

Missing today: the **coordination-check verdict** (`SKILL.md:184`) — the one line that can say "the fan-out bought nothing" — is written into a chat report and persisted nowhere; **failure-ladder outcomes** live only in the session-scratch ledger; **gate regrets** have no home at all.

- **R5.1** `SKILL.md:185`, one clause: "…and the note a future run needs — including a negative coordination-check verdict, a failure-ladder stall and what unstuck it, or a gate call you would reverse."
- **R5.2** `calibration.md` header, +2 lines: lessons go in the note column, written so Step 3 can act on them ("fetch-heavy research runs 70–120k/agent" beats "unit 3 was expensive").
- **R5.3** Growth rule, revised after refutation: my first draft's silent prune contradicted `claude-code.md:66` ("append, never rewrite, and never regenerate"). Correct version: past ~40 rows, *propose* to the user folding the oldest rows into the band summaries; amend `claude-code.md:66` in the same edit to name that as the one sanctioned rewrite, user-approved. A memory file that outgrows its read budget becomes the tax it was built to avoid — but it is the user's file, so the user folds it.
- **R5.4** = N10: tag the seed rows so learning starts from honestly labeled data.

**Scope note — why lessons live here rather than in auto-memory (user question, 2026-08-05).** Auto-memory is keyed to the project folder, so a lesson saved there surfaces only in sessions opened in that same folder. `calibration.md` lives in the skill folder: every `/subagents` run on this machine reads it, from any repo, which is the scope orchestration lessons need. Step 3 reads it deterministically; memory recall is best-effort from a one-line index. It also stays readable to the codex variant, which cannot see Claude's memory directory. Memory is still the right complement for repo-specific conventions, and for lessons that must apply when the skill is never invoked. One caution: saved agents can opt into persistent `memory` (`claude-code.md:13`). Keep it off `verifier` — a reviewer that remembers prior runs is no longer the blank-context reviewer Step 6 relies on.

With the existing within-task signature rule (`SKILL.md:165`), this gives the skill both learning loops: inside a task and across tasks.

## 9. Adversarial check of this document

Every proposal above went to an independent opus verifier briefed to refute it (default-refute on ambiguity, no authority granted to the other agents' claims). Verdict over 51 items: 15 survived unchanged, 30 weakened, 6 refuted. This section is the disposition record; all corrections are already applied above.

Fully refuted and removed: N12, N17, N18, N20 (each changed no output), plus my first-draft savings arithmetic — the refuter measured every cited range with `wc` and found eight of fourteen claims overstated (C8 by 3×), collapsing the advertised "−12%" to the honest "−2%" now in §1/§5. Materially corrected: R5.3 (contradicted the standing append-only rule), C10 (would have deleted the only model-visible copy of two facts), M1/M2/N15 (fixes contradicted text they left standing), R4.1 (false premise), the §4 bullet (three of four clauses were restatement), R3.1/probe numbers (machine-specific, moved to calibration), R3.4 (unconditional line ranges misfire against the explorer's no-widening rule). Overridden with evidence: the refuter doubted `fork` dispatches exist (zero mentions in the seven files — correctly flagged as unverifiable from its inputs); the live tool schema and the fetched sub-agents doc both confirm them, so R3.3 stands with its citation.

One honest caveat the refuter could not close by design: it ran without network, so the compaction knob names in §4 rest on the docs agent's fetches (sources cited in its report, dated 2026-08-05). Reverify names at edit time; `claude-code.md:3` already makes that standard practice.

Exceptions to "every proposal was refuted": three items postdate the refutation pass. M6 came from a user report on this review's own gate; its diagnosis is verified directly against `SKILL.md:101-109` (the template text carries only counts), but its fix has not had an adversarial pass. R4.3 and the §8 scope note came from user questions on 2026-08-05; their factual claims are checked against `claude-code.md:10-13`, `explorer.md:33-39`, and the calibration rows, but neither has had an adversarial pass.

## 10. Prioritized change list

| # | Change | Files | Size | Area |
| --- | --- | --- | --- | --- |
| 1 | Lessons in calibration + user-approved fold + seed tags (R5.1–4) | SKILL.md, calibration.md, claude-code.md | +11 lines | 5 |
| 2 | Compaction: checkpoint bullet + harness-knob caution (§4) | SKILL.md, claude-code.md | +4 lines | 1 |
| 3 | Verifier description + network line (M1) | verifier.md, claude-code.md | +2 lines | — |
| 4 | Gate fixes: M2, M3, M5, M6, N5, N6, N7 | SKILL.md, contracts.md, claude-code.md | +11 lines | — |
| 5 | Boot economics: R3.1–R3.4, R4.1; probe rows into calibration | SKILL.md, claude-code.md, calibration.md | +7 lines | 3, 4 |
| 6 | Dedup and trims (C1–C14, post-refutation numbers) | all three + calibration.md | −590 words gross | 2 |
| 7 | Remaining minors (N-table) | various | +10 lines | — |
| 8 | Optional: `web-researcher` agent file (R4.3) | new agent file + claude-code.md:10 | +1 file (~40 lines) | 4 |

Items 1–5 change behavior and are worth doing alone. Item 6 funds them; net size stays about flat. Item 8 is opt-in and waits for the user's call. The codex variant shares most of this text and should receive the same edits where they apply; that is outside this review's scope.
