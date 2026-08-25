⏺ Every claim verified against its artifact. Here is the report.

  Ran 1 shell command (ctrl+o to expand)

⏺ sage-promote — 2026-08-25
    stage one   → shared: 0 written, 0 refuted, 2 band crossings, 0 not ready
    stage two   → skill:  2 landed, 0 refused, 0 conflicts to the watch list
    stage three → lineup: lineup unchanged, stamp → 2.1.243 2026-08-25
    eviction:            0 retired, 0 corpus removals
    trees:               identical (diff -rq clean)
    local.md:            2 Promoted cells appended, 4 watch-list rows added, 3 closed, 2 confirmed

  Stage zero (not in the report block above, so stated here): 5 defect rows re-verified, all reproduced. 3 repaired across 3 gate rounds — sage-watch.sh's four false documentation claims, its CDPATH hijack, and a tenth sage-lint.sh check.
  2 surfaced, not repaired — below.

  The bin/ diff isn't reproduced above; git diff -- sage-claude/bin/ shows it.

  What the gates changed. They refuted two of my own edits and found five stale sentences my own whole-corpus sweep missed. One comment consumed 2 of the 4 rounds: draft 1 quoted idle=- as what an evidence-free transcript prints — a clock
  artifact, my fixture read seconds after its own timestamp; draft 2 said the diagnostic line prints regardless — true for per-agent rows, false for the [parent] line, which records >= 1 also gates. Draft 3 splits the two paths and
  survived all four clauses. A figure I'd written as "10 findings" measured 44–110.

  Cost. 323.5k over 5 units. Four apex gate rounds ran 62.8–80.3k against the ~120k band — ~0.6×, because every brief named its files, claims, commands and fixtures. Recorded in the run row, along with: price a stage-zero batch by the
  behavioural claims it makes, not the files it touches.

  Needs your eyes

  Two defect rows I could not repair, both left watching.

  The consolidation trigger is dead, and worse than filed. Its bar is 40 non-pointer data rows; the file now stands at 73, of which 71 are structural (Bands 14 + Rules 12 + Watch list 45) and irreducible — consolidation drains only closed
  watch rows and compresses Run-log rows, and only 2 movable rows remain. It fires every run carrying no information. The row names two fixes and picks neither, and neither is determinate: narrowing the count to what a pass can move gives
  2 against a bar of 40 — a trigger that can never fire, the same disease inverted — and scaling the bar needs a formula this skill would have to invent. That is a design decision, not a repair, so I left it rather than improvise a spec
  into the corpus.

  A Promoted cell that contradicts its artifact has no owner. SKILL.md:101 carries "Review and verify are one price" at full strength with (calibration: established); its Rules cell records no skill entry. Stage zero's write list is
  SKILL.md, references/, bin/*.sh and a standing shared.md block's prose fields — it does not reach a local.md Promoted cell. Stage two can't take it either: the cell's refused entry suppresses → skill text, and the skill forbids applying
  the corpus re-check to a refused cell. The gap is in the skill's own stage boundaries.

  Three findings the gates raised that I filed rather than acted on, all now watch rows: consolidation's Rules-table maintenance loses provenance and under-counts (two measured instances); idle reads the last string-typed timestamp while
  two corpus sentences say "any record" — a three-word fix a gate specified and verified, left because it's a semantic edit after three rounds; and build 2.1.243 now shows each subagent's actual model and effort in /tasks, which is a new
  instrument for the Model-column problem harness.md calls unfixable from inside the plan.

  Nothing was refused, retired, or escalated to the never-touched list. The checker seat ran verifier on fable as a logged in-family override — no alt lane is configured on this machine, so all four gates carry residual same-family bias,
  which each reported.

