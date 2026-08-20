# Sage plan integrity — round 3

Status: **narrow proposal, with a provenance correction to round 2.** Written 2026-08-19 by a sage run on this machine (session d005200d; ledger at `.claude/plans/sage-ledger-d005200d.md`). This document reviews `sage-improve-conversation.md` (round 1) and `sage-plan-integrity-proposal.md` (round 2). It rules on their arguments from evidence that resolves on this machine, and it proposes five small changes. It does not change sage itself.

The short version:

- Round 2's **verdicts mostly hold**. Its **evidence does not**: every run-corpus citation in it points at files that do not exist anywhere on this machine.
- The real corpus (4 ledgers, 552 lines) says the plan-trust concern is aimed at the wrong layer. Plans get amended freely and safely. **What breaks, in 4 runs out of 4, is the record of the plan** — states never updated, findings without triage rows, amendments that leave the Plan table untouched.
- So the answer to "does sage over-trust its initial plan" is: no — but **sage cannot currently show you the plan it is actually running**, and that is fixable with checks that hold mechanically.

---

## 1. What this run did

Four evidence sources, all of them resolvable from this machine:

1. **Exhaustive search** for round 2's cited corpus: `find` over the whole home directory (Trash included), `git grep` over this repo's full history, and `grep` over every Claude Code session transcript in `~/.claude/projects/`.
2. **A clean-context audit** of the only sage ledgers that exist here — `sage-ledger-00049e8d`, `sage-ledger-01trav` (this repo), `sage-ledger-2b2ed63f`, `sage-ledger-8f7be95a` (tower-def-RPG) — plus `memory/local.md`. The auditor did not read either disputed document. Detail file: the run scratchpad, `corpus-audit-detail.md`.
3. **Primary-source fetch** of the two papers the rounds disagree about (both fetched 2026-08-19).
4. **A docs check** of what Claude Code hooks and agent files can actually enforce.

An adversarial refuter was pointed at a frozen draft of this document. It confirmed the central thesis, refuted three proposal details — including one factual error that this document's own docs-check unit had introduced — and every accepted finding is folded into the text below. Its full report is in the run ledger. That a same-run reader unit produced a wrong field list, and only an adversarial re-fetch caught it, is itself a data point for section 4's conclusion.

## 2. The provenance problem

Round 2 cites `sage-ledger-1a43545e`, `sage-ledger-61264f83`, `sage-ledger-0042d31e`, `sage-ledger-6d1a7c19`, `sage-ledger-ff95b189`, and `sage-handoff-61264f83`, and says the corpus holds "11 prior ledgers", "3 handoff notes", and "60 assumption rows".

**None of that resolves here.** In every file, git commit, and session transcript on this machine that predates this run, the five IDs appear in exactly one place: round 2 itself. (This run's own ledger and transcript now also contain them, by quoting them — re-running the searches today hits those too.) The machine holds 4 sage ledgers, 0 handoff notes, and 22 assumption rows. Neither round's session ran in any local Claude Code session (no transcript mentions either document or its distinctive content), so both documents arrived from an environment this machine cannot see — plausibly a cloud session or another machine.

What this does and does not mean:

- It does **not** prove round 2's evidence was invented. Its corpus may be real somewhere. This run's ledger records that as an open assumption.
- It **does** mean round 2's specific counterexamples carry no weight here. Where its verdicts survive below, they survive on evidence this run re-derived, not on round 2's citations.
- Round 2 also broke sage's own Step 6 on any reading: a sage run must leave a ledger and a run-log row, and no environment reachable from this machine holds either.

Two things restore some trust in round 2: every claim it makes about the **skill corpus itself** checked out (the `dispatch.md` scratch-path rule; the count-0 ceiling-raise row in `local.md`; the quoted axioms), and its citation correction C1 is **confirmed by primary source**. The EMNLP 2024 paper (aclanthology.org/2024.emnlp-main.714, fetched 2026-08-19) states in its own abstract that its method "enhances LLM performance in identifying and correcting inaccurate answers **without external feedback**". Round 1's claim that the rebuttal "turns on having an external verification condition" is wrong; round 2's reading — the distinction is structured-vs-open-ended, not external-vs-internal — is right.

Round 1's provenance is worse and was already correctly called out by round 2 (C7): it dispatched `general-purpose` agents, left no ledger, and its own text admits its outside agents' evidence "is in this conversation only" — pointers that were dead the moment the session ended.

## 3. The four original edits — final disposition

| Edit | Disposition | Deciding evidence on this machine |
| --- | --- | --- |
| E1 seat check | **Reject as skill text; keep as habit** (unchanged from round 2) — but see proposal item 4, which makes the one measured sub-case hold mechanically | The one measured cost (22.4k) was a model-parameter error, not a seat error; the rule text already exists and was hardened 2026-08-19 (`747e7a1`) |
| E2 plan-premise check | **Reject** (round 2's §6 kill, now corroborated locally) | Of 22 real assumption rows, only 6 could be fired by a same-run report; the 2 that ever fired were fired by adversarial units sage already plans, not by any read-back check. The instrument E2 wants to read is not written to be readable in-run — and that is by design (`SKILL.md` defines the log as ambiguities that would otherwise need the user) |
| E3 superseding plan block | **Reject the block; revive the kernel differently** (proposal items 1–2) | The real corpus shows the problem is worse than round 2 thought — amendments leave Plan rows untouched and unmarked in every run that amended anything — but a fifth plan representation cannot fix non-compliance with the four that exist |
| E4 re-pricing ban | **Reject** (unchanged) | Zero mid-run re-prices, zero ceiling raises, zero refusals in the real corpus — the feared event has never been observed here, and round 2's counterexample (a re-price that was correct and the rail fired anyway) is unverifiable. A ban on an unobserved behavior, argued from a watch-list row whose count is 0, is not an evidence-backed edit |

## 4. What the real corpus actually shows

From the clean-context audit of all 552 ledger lines:

**Plans are not over-trusted — they are amended, freely and safely.** At least 10 amendments across 4 runs (the audit's section headers count 10; its enumerated rows reach 13 — the gap is a counting-rule ambiguity over compound events, and every candidate on either count leaves the unit set intact — two were destructive of other things: a 3-commit collapse of history and a 516-file cut of one review mandate, both disclosed in their ledger): scope additions, a writer reorder, a mid-flight brief correction, review-mandate cuts at freeze, fix-round extensions, one landing change on a user answer. None destroyed the unit set; no unit was ever dropped or merged; nothing suggests a stale plan ever hurt a run. Round 1's fear (a frozen plan colliding with mid-run discovery) has no local instance, and neither does its proposed failure mode for E4 (no estimate was ever touched after Plan time).

**The record of the plan is what fails, and it fails everywhere.**

- The Unit table's state column is dead: across all 4 ledgers, no state **cell** ever carries `planned`, `running`, `blocked`, `failed`, or `abandoned` — every unit is written once, post-hoc, as `reported` (one ledger invented `done`). The enum words do occur elsewhere in the files (Flow columns, prose), which is exactly why the check has to read the column, not grep the file. The "live per-unit state" the ledger spec requires does not exist in practice.
- Amendments leave no mark on the rows they amend. When one run cut 516 files from its review mandate and another added a unit, the affected Plan rows stayed untouched — a reader of the Plan table alone cannot tell what is still in force. This is the true kernel of round 1's E3.
- Findings escape triage: one run's **worst defect** (a blocker) exists only in its fix table, with no row and no triage state in Findings and dispositions. Five dead dispatches in another run never entered the Unit table at all.
- The same disclosure duty landed in four different homes: all four runs ran same-family maker/checker pairs, the rule names `### Findings and dispositions` as where to record that residual bias, and the four runs recorded it in four different places (Plan, Decisions, Gaps, nowhere).
- The handover header is written inconsistently because its initial value is undefined: one run stamped `Generation: 1, role: parent` having spawned nothing — which is exactly the field a post-compaction reader uses to conclude a successor already exists — and another invented `Generation: 0/3`, a cap that contradicts "generations are not capped".

**Round 2's §7 is confirmed, with a sharper shape.** On this corpus the parent obeys the *safety* prose (all 4 runs: snapshots taken, freezes held, adversarial pass at own fixes run, caps respected) and disobeys the *bookkeeping* prose. So "which rules can be made to hold rather than be asked for" is the right question, and the answer is concrete: the record-keeping rules, because they are exactly the ones that are mechanically checkable.

**One live demonstration, from this very run:** sage's own `memory/local.md` currently fails its structural invariants — the Watch list holds two table blocks, because a past run's append silently created a second table. The consolidation pass this run triggered aborted on that marker, exactly as designed. A prose append rule broke structure; a mechanical check caught it — a year of asking nicely would not have.

## 5. The proposal — five items, smallest first

**1. A ledger lint that runs at points that already exist.** One deterministic script (a sibling of `bin/sage-watch.sh`) that checks a ledger for record integrity: every Unit-table state cell carries a value from the enum; every finding ID that appears anywhere in the ledger has exactly one triage row; every Plan row has a Unit row and every Unit row a Plan row (or a Decisions row explaining the difference); the header's Generation/role fields parse. Run it at each bring-current point and at Step 6, the same way `--status` is already read there. Its output is one line per violation, silence on a clean ledger. Honest coverage, mapped against the audit's eight violations: the checks above catch the missing-triage blocker (D4) and the untabled-unit-count mismatch (D6) outright, plus both header defects and the dead state column; they make the wrongly-homed disclosure (D1) and the unrecorded push authorisation (D7) checkable once item 2 fixes each duty's home; they cannot catch a briefing error (D2), a wrong-path reproduction (D3), or a dispatch that was never written down at all (D5) — a text lint cannot see a row that does not exist. That is most of the record-integrity class held mechanically, and the remainder named, not implied away. No new cadence is needed: the bring-current points already exist and already run a probe.

**2. Mark amended rows where they live, and define the header.** Two sentences of skill text, no new machinery: (a) a plan amendment writes its Decisions row *and* tags the affected Plan/Unit row (`superseded → D<n>` in the unit cell), so the plan in force is readable from the table without replaying the Decisions log — the surviving kernel of E3, at one cell of cost instead of a fifth representation; (b) define the header convention once: the original parent writes `Generation: 1, role: parent`; the count increments only when a successor is actually spawned; no denominator; (c) fix one home per disclosure duty — the maker/checker residual-bias note lives in `### Findings and dispositions` (where the rule already points) and a rail-1 authorisation lives in `### Decisions and deviations` — which is what turns item 1's two conditional catches into real ones. The lint (item 1) checks all three.

**3. Cited evidence must resolve where the deliverable lands.** One rule sentence extending "grep the claim before you assert it": a run-produced document that cites artifacts (ledgers, transcripts, scratch files) runs one existence check over every cited path before the completion claim, and either the paths resolve on the machine where the document is filed, or the document says where they resolve instead. Both prior rounds failed exactly this, in opposite directions — round 1 pointed at scratch files that died with the session, round 2 pointed at ledgers no reachable filesystem holds. Cost: one `ls`/`grep` loop. This is also the only item aimed at the failure that made this third round necessary.

**4. One enforcement hook, offered by `install.sh` the way the compact hook already is — probe first.** A hook that denies a dispatch of `explorer-alt`/`verifier-alt`/`web-researcher-alt` carrying a `model` parameter — the one rule in the corpus that is absolute ("pass no `model` at all"), has a measured failure (22.4k spent, three dispatches testing nothing, no agent noticed), and has a deterministic predicate with zero legitimate exceptions. Feasibility is **not yet settled**: this run's two docs checks disagreed on whether `PreToolUse` matchers cover the `Agent` tool (the matcher examples in the hooks doc are ordinary tools; `SubagentStart` is the documented spawn-time event, with unconfirmed block capability), and the Agent tool's `tool_input` schema is not in the public docs. So the item's first step is a five-minute probe: a no-op `PreToolUse` hook that logs `tool_name` and `tool_input` during one dispatch. If the probe shows `Agent` with readable `subagent_type`/`model` fields, ship the guard, failing **open** when the fields are absent; if not, evaluate `SubagentStart`, and if neither can deny, record the negative result and drop the item. Deliberately a pilot either way: one rule, to learn whether hook enforcement earns wider use, not a program to convert sage's prose wholesale.

**5. One erratum to file.** `memory/local.md`'s Watch list needs its two table blocks merged — the sanctioned repair path is the consolidation pass once the row is restored to the main table (a one-line manual fix the user can make, since the file is the user's data and this run's checker is forbidden to repair what it validates). A second erratum drafted here — cutting `harness.md`'s per-agent `hooks` frontmatter row as undocumented — was **refuted before filing**: the refuter re-fetched the sub-agents docs and found the field documented ("Lifecycle hooks scoped to this subagent"), meaning the docs-check unit in this very run returned an incomplete field list and harness.md is right. The near-miss is kept in this text deliberately: it is what proposal item 3's one-command check looks like when it works.

## 6. What is deliberately not proposed

- **No plan-premise check, no re-verification loop for the plan.** The corpus shows amendments arriving through instruments sage already has — critics, refuters, user words — and never through a read-back of logged assumptions. Adding a checkpoint that history says would have fired zero times buys ritual, not integrity.
- **No re-pricing ban.** The behavior it bans has never been observed here. The watch-list row stays a watch-list row.
- **No wholesale "enforcement program".** Only item 4's single hook, as a measured pilot. Most of sage's prose rules (briefing quality, verification judgment, triage) have no deterministic predicate, and pretending they do would recreate this same failure one layer down.

## 7. Evidence index (everything resolves on this machine)

- Run ledger for this document: `.claude/plans/sage-ledger-d005200d.md`
- Real corpus audited: `.claude/plans/sage-ledger-00049e8d.md`, `.claude/plans/sage-ledger-01trav.md`, `~/Projects/games/godot/tower-def-RPG/.claude/plans/sage-ledger-2b2ed63f.md`, `.../sage-ledger-8f7be95a.md`; `~/.claude/skills/sage/memory/local.md`
- Audit detail (per-row): session scratchpad, `corpus-audit-detail.md`
- Papers: https://aclanthology.org/2024.emnlp-main.714/ and https://arxiv.org/abs/2310.01798, abstracts fetched 2026-08-19
- Hook docs: https://code.claude.com/docs/en/hooks.md, https://code.claude.com/docs/en/sub-agents.md, https://code.claude.com/docs/en/permissions.md, fetched 2026-08-19
- Searches that came back empty at run time (re-running them now also hits this run's own ledger and transcript, which quote the IDs): `find` over `/Users/tuananhnguyen` (Trash included) for `sage-ledger-*`/`sage-handoff-*` beyond the four above; `git grep` of the five round-2 IDs over all refs; `grep` of all transcripts under `~/.claude/projects/` for the IDs and both document names
