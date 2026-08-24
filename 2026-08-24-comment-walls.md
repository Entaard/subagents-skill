# Why sage-written code still gets walls of comments

Date: 2026-08-24. Trigger: `LogLostQuotaCharge()` on branch `fix/429D5Y-use-the-same-locks-for-updating-quotas` of Cortex_Core — 25 lines of XML doc over a one-line `Log.Warn`, with a summary that is partly wrong. This doc records what was measured, the causes ranked, and the fixes.

## Verdict

The walls do not come from an implementer ignoring the clean-code skill. They come from a write path where clean-code is never present at all: **the sage parent writing code inline**. On that path, four things line up in the same direction:

1. clean-code's only delivery mechanism is the `implementer` agent's `skills:` preload. A parent-kept writer unit gets nothing. Both commits on this branch were parent-written.
2. The writer's system prompt actively instructs the opposite of rule 28 — it says to **match the surrounding file's comment density**, twice (harness coding guidance + the Simplified Technical English output style, line 54), in a file that is already ~158% saturated with doc blocks.
3. No reviewer in the loop has a mandate on comment **volume or redundancy**. The lenses reliably flag comment *falsity* — four such findings across the two runs — but a wall passes review as long as it is accurate. diff-review's smell baseline has no comment-noise item, and reviewers report what they are asked to look for.
4. When a reviewer caught a comment being *wrong*, the fix round repaired it by rewriting it **longer**, not by deleting it — and other flagged comment findings were left "pending triage" and shipped anyway.

A fifth cause is in clean-code itself: rule 28 ("write why, never what") does not discriminate at the point of failure. These walls contain why-material, so they pass the rule as written. An independent reader (haiku, fresh context) asked to bucket every added comment classified the exact block the user complained about as a legitimate "WHY" comment. And a sixth: reviewer findings against these very comments were left "pending triage" and shipped (C6 below).

## Evidence

All transcript paths are under `~/.claude/projects/`. Ledger paths are inside the Cortex_Core repo.

**Who wrote the code.**

- The whole branch (commits `b31f236717f` 2026-08-21 and `23b806ab286` 2026-08-24) was written in sage runs recorded by `.claude/plans/sage-ledger-29PLOF-lock-unification.md` and `.claude/plans/sage-ledger-bf13437a.md` in `/app/Cortex_Core`. The first ledger records a **parent-owned writer** with a reader/verifier fleet around it; its writing session (`-app-Cortex-Core-XCortex/3de0b6c1-…`) edited `DDoS_Protection_BO.cs` 10 times and dispatched no implementer. The second run's session (`bf13437a-…`) dispatched 6 subagents — all `verifier`/`verifier-alt` lenses, zero implementers — and its parent made all the edits (10 Edit calls: 9 on `DDoS_Protection_BO.cs`, 1 on the test file).
- clean-code was in neither writer's context. In `bf13437a`, marker text ("one-read test") appears **0 times** and the only skill invoked was `diff-review`. In `3de0b6c1`, the only skill invoked was `concurrency` — whose own text says it "adds to the `clean-code` rules" — and "Write why, never what" appears **0 times**. So rule 28 was absent from both writing sessions.
- Contrast: the 4 `implementer` dispatches found across all Cortex sessions (e.g. session `07bb8fcb`) all had clean-code preloaded (marker text present) and added a net **+3, +1, +6, +0 `<summary>` blocks** in their edits — each a one-line summary (e.g. `/// <summary>Upper bound, in seconds, on one Azure Computer Vision HTTP call.</summary>`), none a multi-paragraph remarks wall. The preload does not stop the block-per-member habit, but it visibly caps length: walls appear only on the parent path.

**What was written.**

- Raw diff `922fcef9ce8..23b806ab286`: **66 added `///` lines** (11 removed, net +55) across 4 touched members — 4 of 4 got doc blocks. Per-commit greps show 37 (commit 1) and 25 (commit 2); the totals differ from the cumulative count because commit 2 rewrote and removed some of commit 1's lines.
- `LogLostQuotaCharge` (`XCortex/Matrix/Matrix5/Web/DDoS_Protection_BO/DDoS_Protection_BO.cs:2408-2432`): 25 doc lines, 1 body line. The summary — "Logs a quota charge that could not be recorded, **and swallows the cause**" — ascribes the call sites' behavior to the method. `Log.Warn` swallows nothing; the `catch` blocks that call this method do. The `<remarks>` then spends three paragraphs narrating the *callers* ("Two of those entry points run at the end of the request…") — facts the method does not own, in the place a reader of the method does not need them.
- This repeats a recorded failure signature: finding **V2-F4** in the 29PLOF ledger — "my `<remarks>` claimed the old code 'put the quota charge on a thread pool thread after the request had ended'. Not universally true" — was fixed by **rewriting the comment longer**. Comments that narrate mechanism and history keep being wrong because they assert facts their scope does not own; the loop's repair direction ("make the narrative accurate") grows them instead of deleting them.

**What pushed in that direction.**

- The harness coding guidance in the main-loop system prompt says: "Write code that reads like the surrounding code: **match its comment density**, naming, and idiom."
- The active output style (`~/.claude/output-styles/simplified-technical-english.md:54`) says: "Do not change how many comments the surrounding code has. **Match the file's comment density** and simplify the language." The style was in play in the writing session (215 transcript occurrences of its name).
- `DDoS_Protection_BO.cs` carries ~122 `/// <summary>` blocks over ~77 members. In that file, "match the density" *means* "document everything, at length".
- Output styles apply to the main loop only — they never reach the implementer. So the one path with clean-code loaded also escaped the density-matching instruction, and the one path with the density-matching instruction had no clean-code. The asymmetry matches the measured outcomes exactly.

**What was ruled out.**

- No build enforcement reaches this file. `XCortex/build/Common.props:35-37` sets `GenerateDocumentationFile` only for `OrangeLogic.*` non-test projects; the DDoS file is in a Matrix project. No CS1591/SA1600/stylecop rules found anywhere at the checked depths.
- No repo instruction mandates doc comments. No CLAUDE.md/AGENTS.md in Cortex_Core mentions XML docs; `AGENTS.md:100` even says "Do not make general comments about the code base that is not asked for."
- So the walls are purely behavioral. Nothing forces them; several things invite them; nothing forbids them at the moment of writing or review.

## Causes, ranked

| # | Cause | Kind |
| --- | --- | --- |
| C1 | Parent-inline writer path has no clean-code binding. Sage's own design keeps coupled/high-risk implementation with the parent, and the skill's rules reach writers only via the implementer preload. | structural hole in sage |
| C2 | The writer's system prompt mandates comment-density matching (harness guidance + output style line 54) in an already saturated file. | active mis-instruction |
| C3 | No review lens is mandated to flag comment **noise** (volume, redundancy). The standards lens reliably catches comment *falsity* — S1 and S3 in the bf13437a run, V2-F3 and V2-F4 in the 29PLOF run — but an accurate wall passes. diff-review's 16-item smell baseline has no comment-noise item (item 15 covers convention-vs-structure only). Reviewers report what you ask them to look for. | review gap |
| C4 | clean-code rules 28–29 discriminate only partly. Rule 29 already bans history narratives (change logs) — the "While this module was asynchronous…" paragraph violates it as written, which strengthens C1: the rule existed and was simply never loaded. But rule 28 sets no rule against restating the member name, narrating call sites, or unbounded volume, so walls containing why-material pass it — verified by a fresh reader bucketing the complained-about block as WHY. | skill-text gap |
| C5 | Fix-round dynamics: a "this comment is wrong" finding gets repaired by expansion. A wrong what-comment is evidence the comment never belonged; nothing in clean-code, diff-review, or sage says so. | loop dynamics |
| C6 | Findings produced but never dispositioned. The bf13437a run's comment findings S1, S3, and D1 are marked "pending triage" in its own ledger, and S3's disputed claim is still verbatim in HEAD (`DDoS_Protection_BO.cs:2421-2424`). A reviewer flagged a wrong comment and the wall shipped anyway. Sage's stop rule ("every finding is dispositioned") forbids this; the run stopped without meeting it. | process violation |

Background, not a differentiator: the model family's own prior toward documenting C# exists, but the implementer (same family, clean-code loaded) wrote 1–2 blocks where the parent wrote walls. Instructions, not weights, separate the two outcomes.

## Suggested fixes

Ordered by leverage. 1–3 close the paths; 4–5 fix the text that failed.

**F1 — Close the parent-writer hole in sage** (`~/.claude/skills/sage/SKILL.md`, and the sage source repo).
In Step 1's parent-kept clause and Step 4, add: *a parent-kept **writer** row loads `clean-code` (Skill tool) before its first edit, and the ledger's unit row records that it did.* For the `orchestrator` successor, which has no Skill tool, the handoff note names `~/.claude/skills/clean-code/SKILL.md` as a path to `Read` before editing.

**F2 — Make clean-code's comment section discriminate** (`~/.claude/skills/clean-code/SKILL.md`, rules 28–29).
Add, with one before/after example (the `LogLostQuotaCharge` block is ready-made):

- *A comment states only facts its own scope owns.* Never describe callers or call sites; that text belongs at the call site or nowhere. (Kills "swallows the cause".)
- *A summary that paraphrases the name is noise — delete it.* Rule 4 already makes the name carry the job.
- *Why-comments are short.* One to three lines. Rationale that needs paragraphs goes in the commit message or an ADR, not above the method.
- Add one example under rule 29 making explicit that a *"how it used to work" narrative is a change log* — the rule already bans it, but both walls on this branch contain one, so the category evidently needs naming.
- *Density-matching never applies to comments.* State it explicitly: "Match the surrounding code's comment density" (harness guidance, output styles) is overridden by these rules — new code carries the comments these rules allow, nothing more. Skills override default harness behavior; say so or the two instructions keep fighting silently.

**F3 — Give review the mandate** (`~/.claude/skills/diff-review/SKILL.md` smell baseline).
Add a smell: *Comment that restates the member name or body, narrates call sites or history, or asserts facts about code outside its scope → delete, or shrink to the owned why.* The lens already catches comment falsity without being asked; volume and redundancy it has no mandate for, so accurate walls pass — they did on this branch.

**F4 — Fix the output style** (`~/.claude/output-styles/simplified-technical-english.md:54`, user's file — suggested wording, not applied).
Replace "Do not change how many comments the surrounding code has. Match the file's comment density and simplify the language." with: *"These rules govern comment wording only. They never add a comment. How many comments to write is the clean-code skill's decision: write why, never what."*

**F5 — Set the repair direction for wrong comments** (clean-code or diff-review triage guidance).
*When a review finding says a comment is factually wrong, the default repair is deletion.* Keep only what survives F2's tests. A comment that could be wrong was asserting something the code doesn't show — that is rule 28's own definition of text that must earn its place, and the burden is on keeping it.

**F6 — Finish triage before shipping** (process, not text).
Sage's stop rule already requires every finding dispositioned; the bf13437a run committed with S1, S3, and D1 pending. No new rule is needed — but the ledger lint already detects triage orphans, so running `sage-lint.sh` as a pre-commit gate on runs that write code would make the existing rule mechanical.

Optional, cheap: a PostToolUse lint on writer edits flagging an added `<summary>` whose content shares most of its tokens with the member name. Deterministic, zero context cost; only worth adding if F1–F3 prove insufficient.

## Limits of this investigation

- "Every code the sage ever writes has this issue" is confirmed for **parent-written** code on this branch and consistent with the V2-F4 record. The measured implementer samples (4 dispatches) do not show walls; if walls exist on implementer output elsewhere, that evidence was not found here.
- Whether the output style was formally active in the writing session was read indirectly (215 transcript occurrences of the style's name; no `outputStyle` key found in config files). The harness density-matching guidance is present regardless of the style.
- The classification of the branch's comments (what vs why) is one reader's judgment plus the parent's; the counts (66 added `///` lines, 4/4 members documented, 26/1 doc-to-body ratio on `LogLostQuotaCharge`) are measured.
