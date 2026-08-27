❯ /model
  ⎿  Set model to Fable 5 and saved as your default for new sessions

❯ /sage I think there're 2 big problems with the sage skill right now:
1. Auto consolitdation keeps on making errors in memory files (blank lines, wrong updates), that eventually prevents sage-promote from working.
2. The sage and sage-promote are blind on the accepted rules, patterns, skill texts, shared memories, and maybe more. Those things are never updated or obsoleted.
Verify my two claim carefully. If I'm correct, say so, and brainstorm me a rough plan (simple words, easy to understand) to fix those issues. I want a rough plan to check the ideas first. You can always add more details to it later. Also,
I have 2 things in mind:
1. Make consolidation manual instead of auto, so that it doesn't get in the way of the current task(s)? It can be a part of sage-promote.
2. Define the cortex of the sage - the most important things that can't be removed and will never or very rarely need to be updated, so that they're removed out of the normal promotion flow. Everything else, let's call the "knowledge item
(KI)" (including skill texts, rules, patterns, shared memories, etc) is perishable. First, I think the KI should be modular, so that they're easy to plug and play, and easy to unplug. Then, I think the each KI needs statistics to for the
sage to know if one KI is useful, or if it produces mistake and how to improve it, or just archive a KI if it isn't used for a long, long time.
Check if they're valid. And note that, they are my opinions, not at all your limitation. Feel free to suggest better options or improvement to my own options.

  Verdict on your two claims

  Claim 1 — automatic memory writes keep damaging the files and blocking sage-promote: TRUE, with one refinement. The evidence is overwhelming: the repair report you committed today (eb8c683) documents six distinct defects on the other
  machine — a blank line splitting the Watch list into two tables, run records misfiled as ### subsections, watch rows glued into the Run log with an illegal open status, a v1 sentinel against a v2 contract — all of which aborted
  /sage-promote at preflight. On this machine, references/memory.md itself records the 2026-08-18 blank-line damage and the 2026-08-19 glued-row corruption, there's a "fix consolidation" commit, and your memory/ directory holds eleven
  repair/backup snapshots (pre-consolidate, pre-rowfix, pre-append…). That backup pile is itself the diagnosis: the files get broken often enough that every write is preceded by a manual safety copy.

  The refinement: the consolidation pass is more victim than culprit. Most documented damage came from the Step 6 append (every run, an LLM hand-editing fragile markdown tables) and from the v1→v2 format migration. Consolidation corrupted
  the file once (through an approved diff — memory.md admits this), but mostly it just aborts when it finds damage, and since the protocol forbids it repairing what it validates, every incident ends in a by-hand repair on your word. So the
  real root cause is: memory lives in strict-format markdown tables that an LLM edits directly, guarded by checks that can only abort, never fix. Your fix should target the write path, not only the consolidate pass.

  Claim 2 — sage/sage-promote are blind to accepted rules, skill text, shared memories: TRUE in practice, though not in design. On paper the machinery exists: falsifiers per rule, a retirement trigger, eviction, stage zero corpus repair.
  In practice it's nearly unreachable:

  - shared.md has 11 rules; git history shows zero rules ever removed. The only downward edit ever (cutting one hedge, 2026-08-21) was done through a path the skill doesn't even describe — recorded as a gap row.
  - Retirement needs a run to notice a contradiction and file a contradiction watch row naming the rule. In the entire history, exactly one such row exists.
  - Nothing anywhere records whether a rule was read, applied, or helped. Confirmations only accrue when a run volunteers one; bands only ratchet upward ("a band rises by arithmetic and falls only by eviction").
  - Skill text only grows — the sage SKILL.md is enormous and studded with (calibration:) clauses; clause-level retirement "has no written procedure anywhere" (your own gap row at local.md:89), and another gap row (local.md:112) says
    outright: "No instrument reads local.md's structural growth."

  The system is a ratchet: strong upward paths (promote, confirm, band-raise), theoretical-only downward paths. Your word "blind" is right — there's no feedback signal at all, only the hope that a run happens to trip over a contradiction
  and files it.

  Your two ideas, judged

  Idea 1 — manual consolidation, folded into sage-promote: valid, and I'd go one step further. Concentrating all corpus rewriting into the one human-invoked skill is clean: runs would only ever append, promote would own every
  restructuring. But manual-vs-auto doesn't fix the bigger damage source — appends. So pair it with: make the run's write path too dumb to fail. Either a small script (sage-append.sh) does the table surgery deterministically and the model
  only hands it cell values, or (better, see below) runs append to a plain journal — one line per fact, no table to corrupt — and promote does all the merging into structured form.

  Idea 2 — cortex + perishable modular KIs with statistics: valid, and it's the stronger of the two because it fixes both problems at once if you take the modularity literally:

  - One file per KI. This kills the corruption class outright — no shared table means no blank-line splits, no glued rows, no misfiled appends. Plug/unplug = add/delete a file. Git history per KI for free. Stats live in each KI's own
    frontmatter.
  - Cortex maps well onto what already exists implicitly: the axioms, the step skeleton, the rails, the structural contracts — things sage already calls "the compression floor." Making that split explicit would also shrink the bloated
    SKILL.md, because most of its calibration-tagged clauses are really KIs wearing a skill-text costume.
  - Statistics — one caution. Attribution is self-report: only the run knows which KI it actually used, and this ecosystem has already measured that "safety prose gets obeyed, bookkeeping prose goes dead" (that's why sage-lint exists). So
    keep the per-run duty to ~one line ("KIs used: k12, k31; k12 misled on X"), and let sage-promote do all aggregation, scoring, and archiving. If the stats require ceremony mid-run, they will silently stop being written, exactly like the
    ledgers did.

  Rough plan (to check the ideas, details later)

  1. Split the corpus into cortex and KIs. Cortex = a short, hand-owned file (axioms, steps, rails, invariants) that promote never touches. Everything else — shared rules, bands, calibration clauses currently in skill text, watch
     observations — becomes one KI file each, with frontmatter: id, kind, class, band, created, last-used, use-count, hit/miss notes, falsifier, status.
  2. Dumb down the run's writes. A run writes exactly two things: its run-log line and a raw journal of observations/KI-usage (append-only, one line each, no structure to break). No table edits, no in-place count bumps, no consolidation.
     The blank-line failure class becomes impossible.
  3. Move consolidation into sage-promote as its first stage: read the journal since last promote, merge into KI files (bump counts, extend dates, file new KIs, reconcile), archive the journal. All structural risk now sits in one
     human-supervised place with the existing gates.
  4. Give promote a KI review stage (this is the anti-blindness piece): for each KI, look at its stats — unused for N promotes → archive; misses recorded → repair or retire; count crossed a threshold → raise band / push into
     cortex-adjacent "loaded by default" set. Retirement stops requiring a lucky contradiction row; disuse and misses are now signals too.
  5. Migrate, don't rewrite: current shared.md rules and local.md rows convert mechanically into KI files (the repair report proves this kind of transcription is doable); the old tables get archived, not deleted.

  One open question worth deciding early: what a run loads. Today Step 2 reads everything, and that cost only grows. With modular KIs you can load by relevance (kind/recogniser match against the task) — that's the "plug and play" payoff,
  and it's the piece the current design has no answer for at all.

  Two housekeeping notes: the consolidation hint is due (15 actionable rows ≥ the bar of 10) — I deliberately did not run the auto-pass, since it's the mechanism you're auditing; that's logged as a deviation. And this run's row was
  appended to local.md with the before/after check clean (Run log 1 47 → 1 48).

  sage: 0 agents · ~85k · ~15 min · .claude/plans/sage-ledger-d29b4e41.md

  artifacts:
    ledger   .claude/plans/sage-ledger-d29b4e41.md
    report   2026-08-27-local-md-repair-report.md (committed, eb8c683)

  Surfaced events: consolidation hint due (15 actionable rows; pass skipped on your framing — say the word and I'll run it); solo run — coordination check N/A by plan.

✻ Sautéed for 3m 53s · done 10:30 PM
