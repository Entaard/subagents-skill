#!/usr/bin/env bash
#
# sage-lint.sh — deterministic record-integrity checker for ONE sage ledger (the single
# markdown file, `.claude/plans/sage-ledger-<session>.md`, that records one orchestration
# run — see `../references/dispatch.md` `## The ledger` for the prescribed shape).
#
# It reads the one file it is given, prints ONE LINE PER VIOLATION, and prints NOTHING on a
# clean ledger. It is a text linter: awk/sed/grep only, no `jq`, no network, no writes of any
# kind — it never creates, edits, or caches a file, and it never touches the ledger it reads.
#
# ---------------------------------------------------------------------------
# USAGE
#
#   sage-lint.sh <ledger-path>
#   sage-lint.sh --corpus <sage-skill-dir>
#   sage-lint.sh --help
#
#   <ledger-path>       The one file to check. Required, exactly one.
#   --corpus <dir>      A SECOND, INDEPENDENT MODE (see CORPUS MODE below), never an
#                        eleventh
#                        ledger check: it checks a sage skill DIRECTORY's own corpus for
#                        dangling `.md` citations, not a ledger. `<dir>` must carry a
#                        readable `SKILL.md`; `--corpus` with no following argument, or with
#                        more than one argument total, is a usage error (exit 2) exactly like
#                        the ledger form.
#   --help / -h         Print this reminder, exit 0. Any other argument starting with `-`,
#                        zero arguments, or more than one argument (outside the `--corpus`
#                        form above) is a usage error (exit 2) — nothing is read in that case.
#
# "Is a ledger" (the test the path must pass to be checked at all, rather than rejected):
# readable, not a directory, and carrying at least ONE of these three marks of being a RECORD
# rather than a DESCRIPTION of one — every heading and table row below read OUTSIDE a fenced
# (```) code block, so a file that quotes the ledger template inside a fence gets no credit
# for the quote:
#
#   1. line 1 is an HTML comment containing `sage occupancy duty`; or
#   2. the file carries a `# sage ledger` title at `#` depth; or
#   3. at least THREE of the six prescribed section headings below appear, AND at least one
#      markdown table row appears.
#
# One prescribed heading is deliberately NOT enough, and the reason is measured:
# `../references/dispatch.md` — the ledger SPEC, and the single most likely wrong path a
# caller hands this script — carries all six prescribed headings as real (unfenced) headings
# and not one table row. Under a one-heading test it came back exit 1 with a pile of
# violations about a file that is not a ledger and never was, breaking the promise made in
# the next sentence. A path that fails this test is exit 3, never a pile of violations:
# reporting "12 things wrong" about a file that was never a ledger to begin with would be
# worse than useless, it would be misleading.
#
# ---------------------------------------------------------------------------
# THE CHECKS — exactly ten, each with a short stable id. Every check reads ONLY the text
# named below and states what it therefore cannot see; that blind spot is not a bug in the
# check, it is the check's honest shape.
#
#   header
#     Reads: line 1 of the raw file.
#     Fires: line 1 is not a one-line HTML comment containing the literal text
#       `sage occupancy duty` — three messages, one each for: the phrase is absent from the
#       whole file; it is present but on a line other than 1; or the comment opens on line 1
#       but does not close on line 1 (a multi-line comment — the fields cannot be read from
#       line 1, so `header-fields` has nothing to parse and stays silent).
#     Cannot see: a header restamped with stale figures — this check only looks at whether
#       the comment exists and sits first, never whether its numbers are current.
#
#   header-fields
#     Reads: the same line 1 comment, ONLY when `header` found it there (a check that has
#       nothing to parse stays silent rather than re-reporting `header`'s own finding).
#     Fires: the comment carries no `Generation: <N>` field, or N is not a bare positive
#       integer (this is what catches both a literal `0` and a fraction like `0/3` — neither
#       is "a generation", one is the zero-eth and the other is not a count at all); or the
#       comment carries no `role:` field, or the role word is neither `parent` nor
#       `supervisor`.
#     Cannot see: whether the Generation number is actually RIGHT for this run — only that it
#       is a well-formed positive integer.
#
#   state-enum
#     Reads: the Unit table's header row (to find the column literally labelled `state`,
#       never by counting to a fixed position) and every data row under the FIRST occurrence
#       of the `Unit table` heading.
#     Fires: a data row's `state` cell does not BEGIN with one of
#       `planned running reported blocked failed abandoned inline` AT A WORD BOUNDARY — the
#       enum word must be the whole cell, or be followed by anything that is not a letter
#       (space, comma, semicolon, ...). Trailing annotation is legal: `reported 07:11` and
#       `reported, steered, re-reported` both pass. `done 07:13...` fails (not one of the
#       seven words); a word that only starts the same way, like a hypothetical `reportedly`,
#       also fails (boundary check, not a prefix check). An EMPTY state cell fails too: the
#       invariant is that every unit carries a value from the enum, and an emptied cell is
#       the emptiest possible violation of it, not a parse the check cannot make. Or the
#       Unit table has no column labelled `state` at all (one violation for the table, not
#       one per row). Or the `Unit table` heading exists with NO table anywhere under it —
#       one violation for the section, the absence case of the same invariant (the sibling
#       of `plan-unit`'s empty-Plan rule; a row the table never had is otherwise invisible
#       to every per-row check here).
#     Cannot see: whether a state was actually KEPT current while the unit ran, only whether
#       the word written down is a legal word. A ledger updated once at the very end and a
#       ledger updated live read identically to this check. A data row SHORTER than the
#       state column (a malformed row with missing cells) is a parse failure, not an empty
#       cell, and stays silent per FAIL QUIET.
#
#   triage-orphan
#     Reads: the first table under the FIRST `Findings and dispositions` heading (its first
#       column, taken as the set of real finding ids) — that is the ONLY source of "this id
#       has a triage row". Candidate ids (things that might be orphans) are harvested from
#       two places: (a) the first column of tables OUTSIDE every prescribed section, plus
#       tables under `Run record` (whose summaries can cite ids that were never triaged).
#       `Plan`, `Unit table`, `Assumption log` and `Decisions and deviations` each carry
#       their own id/index namespace (plan/unit ids, `A1`, `A2`..., `D1`, `D2`...) and the
#       Findings section supplies the triage set — none of the five is a candidate source.
#       The exclusion is by prescribed SECTION, never by a table's header label: an earlier
#       draft also dropped any table whose first column was labelled `id`/`#`/`when`/
#       `assumption`, and that let a fix table headed `id`, holding an untriaged blocker,
#       escape silently — the exact case this check exists for. Section extents are
#       NESTING-AWARE here: a lower-level heading inside a prescribed section (a `###`
#       subsection under `## Findings and dispositions`, a legacy layout the real corpus
#       uses) stays inside it, while a sibling-level section (`### Fix log` beside `### Run
#       record`) ends it — which is what keeps a fix table harvestable. A harvested
#       candidate is then dropped when it is a KNOWN NON-FINDING id: an id that appears in
#       the Unit table's own id column, or a `D<n>` id from the Decisions table's id
#       column — so a stamp table citing unit `U1`, or a summary table citing decision
#       `D2`, cannot turn either into a bogus orphan.
#       And (b) PROSE, but ONLY on the Run record's `Findings:` summary line (the
#       one field the prescribed template reserves for exactly this content) — a
#       finding-shaped token sitting at a clean word boundary immediately before a `(`, e.g.
#       `K (residual note, not yet triaged)`. Deliberately narrower than "any prose anywhere":
#       a whole-document scan re-catches ordinary criterion citations with the identical
#       shape ("R5 (`needs-playtest`) is Awaiting human", "case C6 (i-frames...) was ruled" —
#       both real Run-record prose, zero relation to triage), and a false alarm there costs
#       more than the citations this narrower scan misses.
#     What counts as "looks like a finding id" (conservative on purpose): a bare single
#       UPPERCASE letter (any of A-Z — this run's own review round ran A..K), OR
#       1-4 uppercase letters, an optional hyphen, 1-3 digits, and an optional single
#       lowercase suffix letter (`F1`, `F2a`, `A`, `V1`, `CI-01`, `VOC-01`, `F-1`, `SG-01`,
#       `P1`). This deliberately MISSES a shape like `R1-rej` (a hyphenated word suffix, not a
#       digit-then-letter one) — a missed id is silence, never a false alarm, which is the
#       trade this check is required to make.
#     Fires: a harvested candidate id has no row in the Findings table (orphan — this is a set
#       difference: candidates minus ids that already have a row, so a prose CITATION of an
#       already-triaged id, e.g. "F7b" mentioned again in the Run record, cannot fire); or a
#       token appears twice within the Findings table itself (duplicate).
#     Cannot see: an id that does not match the shape above at all, or a prose id with no `(`
#       right after it — a first cell or a sentence with an id buried where this check does
#       not look is invisible to it, by design. And a finding whose id COLLIDES with a unit
#       id or a Decisions id (`U1`, `D2`) is dropped by the known-non-finding subtraction
#       above — a run that names its findings after its units hides them from this check.
#       Four more escapes are MEASURED, not theoretical, and each one is a deliberate trade
#       against a false-alarm class rather than an oversight:
#         - A table in a subsection UNDER `## Findings and dispositions` is inside the
#           prescribed section, so an untriaged id in a `### Fix log` written THERE (rather
#           than beside Findings) is invisible. Harvesting those subsections was tried and
#           measured: it added 14 false alarms on one real ledger, whose `### Dispositions`
#           table triages its findings in a column labelled `state`. A fix table one heading
#           level up still fires, which is the layout the prescribed template produces.
#         - A table is treated as SELF-TRIAGED on its header row alone. A `disposition`
#           column whose cells are all EMPTY excludes the table just as a filled one does.
#           The label test is a SUBSTRING test, so any header cell merely CONTAINING
#           `triage` or `disposition` excludes the table — `untriaged?` and `predisposition`
#           both do it. Narrowing the test to exact labels was rejected: the real corpus
#           spells these columns freely (`triage`, `**triage**`, `disposition`, `Triage`),
#           and an exact list would miss the spellings the exclusion exists to catch.
#         - Section identity is prefix-matched, so `Plan B` reads as `Plan` and is excluded.
#         - Only `##` and `###` are headings here. A `####` heading does not end a section,
#           so everything under it belongs to the enclosing one.
#
#   triage-state
#     Reads: the triage column of the SAME table `triage-orphan` reads as its triage set —
#       the first table under the FIRST exact `Findings and dispositions` heading. It runs
#       inside that check's awk pass rather than in one of its own, so "which table is the
#       triage table" has one owner here instead of two. The column is found by LABEL, never
#       by counting to a fixed position: a header cell whose delabelled text (emphasis and
#       code ticks stripped, lowercased) is EXACTLY `triage` or `disposition`. Those two
#       words, across four casings, are what every ledger in the local corpus spells. The
#       exact test is deliberately stricter than the substring test `triage-orphan` uses one
#       line above it: that one only EXCLUDES a table from candidacy, where a wrong guess
#       costs nothing, while this one SELECTS a column whose every cell then gets ruled on,
#       where a wrong guess reports a whole table of false violations.
#     Fires: a data row whose triage cell is EMPTY, or carries no disposition word anywhere
#       in it at a word boundary. The words: `accepted`, `rejected`, `deferred` and
#       `user decision` — the four triage states in `../references/dispatch.md`
#       `## Finding schema`, which is their one authority — plus `merged`, `retracted` and
#       `disclosed`, three the real corpus uses to close a finding without one of the four.
#       Those three are here to stop false alarms, and they are why this check is narrower
#       than the commit gate it serves (`../SKILL.md`, Step 5): it catches the PARKED cell
#       (`pending triage`, `open`, `TBD`, empty), not every cell outside the spec's list.
#       The word may sit anywhere in the cell, not only at its start: `all accepted —
#       wording fixes applied` and `merged into C2 (accepted)` are both real cells, and a
#       start-anchored test reports them both. A longer word that merely CONTAINS a state
#       word does not count — `unaccepted` fires. Boundary test, not substring.
#     Measured, on every sage ledger on this machine (17 files): zero violations before this
#       check shipped, and one probe ledger carrying `pending triage` fires. The corpus is
#       what set the accepted word list, not a guess at one.
#     Cannot see:
#       - A Findings table with NO triage column: silence, never a violation. Measured, not
#         assumed — one real ledger records its findings under `## Findings and dispositions`
#         in a corrections table headed `| # | claim | correction | evidence |`. There is no
#         cell to read there, so this is a parse the check cannot make and FAIL QUIET
#         governs. `state-enum` DOES report a missing `state` column, and the difference is
#         the corpus: every Unit table carries that column, while the Findings table's shape
#         varies across real runs.
#       - Whether a legal word is the RIGHT disposition. A finding wrongly marked `accepted`
#         and one correctly marked `accepted` read identically here. Reading the column
#         against the four states stays a human act; this check removes only its parked-cell
#         half, which is the half that shipped a real run with three findings untriaged.
#       - Whether `rejected` really carries its evidence, or `deferred` its owner. The spec
#         names both halves. In the real corpus they usually live in the row's own
#         `evidence` column, so demanding the literal phrase would report compliant rows.
#       - A row whose cell count differs from its header row's — an unescaped `|` inside a
#         cell (a code span, say) slides every later column along. The one violation this
#         check produced over the whole local corpus was exactly that, and the text it
#         reported was a fragment of a jq command. A stray pipe is named in FAIL QUIET as a
#         parse to stay silent on, so it stays silent.
#       - A findings table under a differently-named heading, for the same reason
#         `triage-orphan` cannot see one: the heading is what locates the table.
#
#   plan-unit
#     Reads: the first table under the FIRST `Plan` heading and the first table under the
#       FIRST `Unit table` heading, each table's first column as its id set — with an
#       AMENDMENT TAG stripped off each id before the two sets are compared. The ledger spec
#       (`../references/dispatch.md`, `### Decisions and deviations`) tells a run to mark an
#       amended row in its own first cell, `2 superseded → D2`, so that cell and a bare `2`
#       are the SAME id here; a trailing parenthetical comes off the same way. Without this
#       strip, a ledger that OBEYED that rule would fail this check FOR obeying it, which is
#       the worst thing a linter can do to a rule it shares a corpus with. And, for the
#       escape clause, the raw text of every section headed exactly `Decisions and
#       deviations` (WORD-BOUNDARY search — the id's characters must sit between
#       non-alphanumeric neighbours. Not a bare substring search, because the spec now keys
#       Decisions rows `D1`, `D2`, ...: under a substring test a row `D2` would silence this
#       check for unit id `2` in every COMPLIANT ledger, disabling the check by the act of
#       obeying the rule. It is still a dumb search — an id mentioned at a boundary in an
#       unrelated sentence silences the check, the same way a human skimming for "was this
#       explained anywhere" would be fooled by the same coincidence, and that trade is
#       deliberate and unchanged).
#     Fires: an id in one table's set and not the other's, UNLESS that id string appears
#       somewhere in a `Decisions and deviations` section — one violation per unexplained id;
#       OR the `Plan` heading exists but its extent contains no table at all — ONE violation
#       for that, not a synthetic storm of every id "missing" from a table that was never
#       there.
#     Cannot see: whether the DECISION recorded under `Decisions and deviations` actually
#       explains the specific id, only whether the id's characters occur somewhere in that
#       section's text.
#
#   disclosure-home
#     Reads: EVERY line of the document (outside fences) — trigger-anywhere, home-required.
#       An earlier draft scanned only three sections and excluded `Plan`, `Unit table` and
#       `Run record`; the measured history says those are exactly where a mislaid disclosure
#       actually lands, so the trigger scan now excludes nothing.
#     Keyword sets (case-insensitive substring, heuristic — say so plainly): a same-family /
#       residual maker-checker bias disclosure is recognised by `same-family`, `same family`,
#       or `self-preference bias`; its one required home is `Findings and dispositions`. A
#       rail-1 authorisation is recognised by `rail-1` or `rail 1`; its one required home is
#       `Decisions and deviations`.
#     Fires: a keyword set appears somewhere in the document while NO line under its home
#       section carries that same set — one violation per keyword set, pointing at the first
#       trigger line. A trigger outside the home is legal WHEN the home also carries the
#       disclosure: previews and restatements of a properly-homed line are not the failure,
#       a disclosure whose home is empty is.
#     KNOWN FALSE-POSITIVE MODE, measured live: a ledger that merely DISCUSSES this rule —
#       a finding about the disclosure duty, a run-record sentence weighing same-family
#       lenses — trips the keywords without owing the disclosure. The remedy is to reword
#       the discussing line, or to carry this check's line to Step 6 as a surfaced event
#       with the reason written next to it. A keyword heuristic cannot tell recording a
#       disclosure from reviewing the rule, and saying so here is cheaper than pretending.
#     Cannot see: a real disclosure phrased without any of the keywords (silence, per the
#       miss-over-false-alarm trade), and it cannot tell a real disclosure from an
#       incidental use of the same words — a heuristic, not a parser of meaning.
#
#   amend-tag
#     Reads: the first cell of every data row in the `Plan` and `Unit table` sections that
#       contains the word `superseded`, and the first column of the `Decisions and deviations`
#       table — but ONLY when that table is keyed by an `id` column.
#     Fires: a row tagged `superseded` names a `D<n>` that has no row in
#       `Decisions and deviations` (a tag pointing at nothing), or names no `D<n>` at all.
#     Silent, always, when the Decisions table is absent or is not keyed by `id`: every ledger
#       written before that column existed would otherwise be flooded for predating the rule.
#       This is the fail-quiet rule applied to the check's own precondition.
#     Cannot see: the other half of the rule. `../references/dispatch.md`
#       `### Decisions and deviations` requires BOTH a Decisions row and a tag on the rows it
#       amends; only the tag→row direction has a deterministic predicate. A Decisions row whose
#       amended rows were never tagged is invisible here, because no text says which rows it
#       amended — that half is still asked for, not enforced, and saying so is the point.
#     Does not overlap `plan-unit`: that check STRIPS the tag and compares ids, this one reads
#       the tag and resolves it. A single tagged row can produce at most one line from each,
#       and for different reasons.
#
#   sections
#     Reads: every `##`/`###` heading line in the document (outside fences), compared against
#       the six prescribed names: `Plan`, `Unit table`, `Assumption log`,
#       `Decisions and deviations`, `Findings and dispositions`, `Run record`.
#     Fires: a prescribed name that appears zero times (missing), or more than once
#       (repeated) — one violation per offending name, not per extra occurrence.
#     Cannot see: a heading text that is CLOSE but not exact (`### Decisions and deviations
#       (continued)` does not count as a second `Decisions and deviations` — it is a
#       different heading string, and this check does not guess at near-misses). Where that
#       near-miss was MANUFACTURED by a bad edit rather than typed, `splice` below is what
#       sees it, and it sees it by the splice signature rather than by guessing at names.
#
#   splice
#     Reads: every line outside a fenced block, tracking inline-code (`) parity cumulatively
#       across lines. That is deliberately LOOSER than a markdown reader, which never lets an
#       inline span cross a block boundary -- the looseness is what lets it see a splice that
#       cut a sentence in half, and it is also this check's one false-positive shape.
#     Fires: a heading or a table row appears while an inline-code span is still OPEN — one
#       violation per offending line. That is the signature of a mis-anchored edit, and it is
#       measured: a `str.replace` whose anchor (`## Findings and dispositions`) was a
#       SUBSTRING of a longer string already in the file (a risk sentence quoting
#       `### Findings and dispositions` in backticks) spliced a whole section into the middle
#       of that sentence — prose truncated mid-clause, the section's rows sitting inside an
#       unclosed code span, a malformed heading left behind — and every check that existed at
#       the time returned clean on it, before and after. The edit-side rule this check is
#       the detector for: assert anchor uniqueness (`s.count(old) == 1`) before any replace,
#       because a longer superstring elsewhere makes `replace(..., 1)` silently hit the
#       wrong site.
#     Cannot see: a splice that lands outside a code span, or one whose fragments happen to
#       leave backtick parity even. Its false positive is the mirror image: ONE stray unpaired
#       backtick in prose opens a span that never closes, and every later heading and table row
#       is then reported. The count tracks how much file follows the stray, not how much is
#       wrong: one backtick inserted near the top of each of this corpus's 12 clean ledgers
#       measured 44 to 110 findings. Read a long run of splice findings as "find the stray
#       backtick above the first one", never as that many separate defects. It does NOT
#       check for duplicated non-prescribed headings: `sections` already covers the six
#       prescribed names (measured — it caught a repeated `Run record`), and no ledger in
#       the corpus repeats a heading outside them, so a check for that would be untested
#       guesswork. Measured: zero findings across the 18 ledgers in `.claude/plans/`, three
#       on the spliced fixture.
#
# ---------------------------------------------------------------------------
# CORPUS MODE (`--corpus <dir>`) — a SECOND, INDEPENDENT mode, not an eleventh ledger check.
# It never reads a ledger and the ten checks above never run in it. It exists because the live
# corpus cited a document that was deleted, `sage-plan-integrity-round3.md`, and nothing
# caught it for weeks — the citation just sat there, dead.
#
#   corpus-citation
#     Reads: `<dir>/SKILL.md` and every `<dir>/references/*.md`, each OUTSIDE its own fenced
#       (```) code blocks — the same fence-blanking convention the ledger's "is a ledger" test
#       uses above, reused rather than re-written, so a path quoted inside a fence as an
#       example is never treated as a citation.
#     What counts as a citation: a backtick-wrapped span whose entire content is a `.md` path
#       — letters, digits, `.`, `_`, `-`, `/` — immediately followed by nothing but the
#       closing backtick. Resolved relative to the CITING FILE'S OWN DIRECTORY, and ONLY
#       there: a `../`-style relative citation (`../memory/local.md`, seen from
#       `references/`) and a bare sibling citation (`harness.md`, seen from another file in
#       `references/`) both resolve this way, and those are the shapes the corpus uses. There
#       is deliberately NO corpus-root fallback. One existed, so that a file inside
#       `references/` could cite `references/harness.md` root-relative; it masked exactly the
#       defect this check was built for, a citation that does not resolve from where it is
#       written, and the corpus's three such sites were fixed rather than excused.
#     Memory citations, in two halves — the split is narrower than the directory on purpose:
#       OUT OF SCOPE, never checked: the genuinely PER-MACHINE files — bare `local.md` and
#         `local-*.md`, or path-qualified `memory/local.md` / `.../memory/local-*.md`. They
#         are seeded once at install time and are deliberately absent from the repo
#         (`harness.md`: "excluded from the synced tree"), so no existence test can be honest
#         about them, and checking them would turn "not seeded yet" into a false alarm.
#       IN SCOPE, resolved BY BASENAME under `<dir>/memory/`: everything else the corpus
#         calls by a memory name — `shared.md`, `shared-*.md`, `memory/shared.md`,
#         `../memory/shared.md`, and the repo-rooted `sage-claude/memory/shared.md` that a
#         reader of the REPO (rather than of an install) sees. That file is real and checked
#         in, so a dangling citation to it is a real defect and is reported. Only the
#         basename is common to those five spellings, so the basename is what resolves.
#     Fires: a citation's resolved path does not exist (and it is not out of scope, above) —
#       one violation per citation SITE, so the same dangling filename cited three times (as
#       it is, live, for `sage-plan-integrity-round3.md`) is three violation lines, not one
#       collapsed line, because each site is a separate promise that broke.
#     Cannot see (stated plainly, the same convention as the ten checks above):
#       - a path cited inside a fenced code block as an example — deliberately not a citation;
#       - a path built by string interpolation or otherwise assembled at read time, since this
#         is a text scan of the literal backtick span, never an interpreter;
#       - a citation to a document that EXISTS but whose content moved out from under it — the
#         check resolves a path, it does not read what is at the far end;
#       - a genuinely dangling citation to a PER-MACHINE memory file (`local.md`,
#         `local-archive.md`, `memory/local.md`), or a bare mention shaped like one that is
#         not actually about that directory — silence, not a violation, and the whole
#         remaining cost of the out-of-scope trade directly above; a caller who suspects one
#         exists checks those files by hand. `shared.md` is no longer in this blind spot;
#       - a `~`-rooted span (`~/.claude/CLAUDE.md`) — it names a path outside this corpus
#         entirely (the user's global config, an installed file, never a file this corpus
#         ships), so it is skipped, not resolved and not flagged.
#     Exit codes for this mode only: 0 clean, 1 dirty (same meaning as the ledger form), 2 a
#       `--corpus` usage error, 3 `<dir>` is missing/unreadable/not a directory, or carries no
#       readable `SKILL.md` — the corpus equivalent of "not a ledger", same FAIL-QUIET spirit:
#       a dir that is not a sage skill dir gets one diagnostic on stderr, never a pile of
#       violations about files it was never going to find.
#
# ---------------------------------------------------------------------------
# OUTPUT LINE SHAPE, fixed field order:
#
#   sage-lint <check-id> <path>:<line> <message>
#
# `<path>` is the path exactly as given on the command line (never resolved or shortened) in
# ledger mode; in `--corpus` mode `<path>` is the citing file's path, built from the `<dir>`
# argument exactly as given.
# Grep field 2 to select a check; split on the first `:` after field 3 to get the line
# number. A clean ledger, or a clean corpus, prints NOTHING — no summary line, no "0
# violations", nothing.
#
# ---------------------------------------------------------------------------
# EXIT STATUS
#
#   0   clean — no violations (silence on stdout)
#   1   dirty — one or more violation lines were printed
#   2   usage error — the arguments themselves were unusable; nothing was read
#   3   the path is unreadable, is a directory, or is not a ledger at all (see "Is a ledger"
#       above) — distinguishable from "dirty": a caller can tell "nothing to check here" from
#       "checked it, found problems" without parsing any prose. In `--corpus` mode, exit 3
#       means `<dir>` is unreadable, not a directory, or has no readable `SKILL.md`.
#
# ---------------------------------------------------------------------------
# BLIND SPOTS, stated rather than hidden — none of the ten checks above can see:
#   - a briefing error (a unit given the wrong instructions can still fill every cell out
#     legally);
#   - a wrong-path reproduction (a command that measured the wrong thing but is quoted
#     correctly);
#   - a dispatch that was simply never written down at all — this tool only ever sees what
#     made it onto the page;
#   - an UNTAGGED amendment: a Decisions row that amends a unit while the amended Plan/Unit
#     row carries no `superseded` tag. Only the tag→D-row direction is checked (`amend-tag`
#     resolves a tag to its row); no text says which rows an untagged D-row amended, so that
#     half has no deterministic predicate and is asked for, never enforced — a deliberate
#     decision (this repo's fix-run ledger, decision D3): a keyword guess here would buy the
#     false-alarm cost without buying the check;
#   - and, stated explicitly because it is the one most likely to be over-read: `state-enum`
#     checks that a state word is LEGAL, never that it was kept LIVE. A ledger written once at
#     the very end, backfilling every state to its final value, and a ledger updated at every
#     real transition are indistinguishable to this check. Legality is not liveness.
#   - and its sibling, for the same reason: `triage-state` checks that a triage cell holds a
#     disposition WORD, never that the disposition is the RIGHT one. A finding waved through
#     as `accepted` and one genuinely accepted read identically here. It ends the parked
#     cell, not the wrong call.
#
# FAIL QUIET. A parse this script cannot make is silence, not a violation and not a crash. A
# malformed table, a stray pipe, a non-UTF8 byte, a file with no trailing newline, a heading
# shape it does not recognise — none of these produce a spurious violation line or a non-zero
# exit other than the three defined above. When in doubt, this script says nothing: a linter
# that cries wolf gets ignored, and an ignored linter is worse than none, because the run
# record still says it ran.
#
# DEGRADATION — the same convention as bin/sage-watch.sh. "Cannot run here" means the script
# itself will not execute on this machine: the file is missing or not executable, bash will
# not run it, or every invocation dies before reading the ledger. The response is the
# watchdog's: disable the lint for the rest of the run, write ONE ledger line saying so,
# and never warn about it again.
#
# ONE NAMED EXCEPTION, and it used to be filed under the sentence above: a missing core tool
# (awk, sed, grep, sort, cut, head) is A FIXABLE DEPENDENCY, not a layout this lint cannot
# run on. The preflight below exits 0 with stdout silent and the tool's name on stderr, and
# the correct response is to install it and run again -- NOT to disable the lint for the run.
# Treating it as degradation costs every later check for the sake of an absent `sed`, and
# leaving it unhandled was worse still: without the preflight this script INVENTED violations
# on a valid ledger. Read stderr before you disable this lint (../SKILL.md, Step 5). Exit 2 (bad arguments) and exit 3 (not a ledger) are NOT
# degradation — fix the call and run it again — and exit 1 is the lint working. Nothing here
# changes the exit-code semantics above.

# LC_ALL=C throughout: every regex here is ASCII-anchored, and running byte-wise (rather
# than through a UTF-8 multibyte table) means a stray non-UTF8 byte in the ledger is just
# another byte, never an awk "multibyte conversion" crash — fail quiet, per FAIL QUIET above.
export LC_ALL=C

usage() {
  printf '%s\n' \
    'sage-lint.sh <ledger-path>       check one ledger, one violation per line, silent if clean' \
    'sage-lint.sh --corpus <dir>      check a sage skill dir'"'"'s own .md citations (separate mode)' \
    'sage-lint.sh --help              this reminder' \
    '' \
    'Exit 0 clean OR a required tool is missing and nothing was checked (stderr says' \
    '       which), 1 dirty, 2 usage error, 3 path unreadable/dir/not-a-ledger (or, in' \
    '       --corpus mode, dir unreadable/not-a-dir/no SKILL.md).' \
    'Output: sage-lint <check-id> <path>:<line> <message>' \
    'Checks: header header-fields state-enum triage-orphan triage-state plan-unit' \
    '        disclosure-home sections amend-tag splice         (ledger mode, all ten)' \
    '        corpus-citation                                  (--corpus mode, its one check)'
}

# Core-tool preflight. Without it this script INVENTS violations instead of failing quiet:
# in a stub PATH with no sed it reported two fabricated violations on a VALID ledger, with
# empty stderr, and with no awk it exits 3 "not a ledger" -- a code DEGRADATION below says
# is NOT a degradation, so the caller fixes the call and re-runs instead of disabling the
# lint. Both break the FAIL QUIET promise, and a check that punishes a compliant ledger
# trains the parent to stop reading it. This is the ONE NAMED EXCEPTION in DEGRADATION above,
# not a "cannot run here": stdout is silent and exit 0 so nothing false is ever reported, and
# the missing tool's name goes to stderr, where it costs one line to fix. Shared by both
# modes; the only difference is the noun in the stderr line, passed in by the caller.
preflight_tools() {  # preflight_tools <noun-for-the-stderr-message>
  for _tool in awk sed grep sort cut head; do
    if ! command -v "$_tool" >/dev/null 2>&1; then
      printf 'sage-lint: %s not found on PATH -- install it and run again; the %s was NOT checked\n' "$_tool" "$1" >&2
      exit 0
    fi
  done
}

# ---------------------------------------------------------------------------
# Arguments

if [ "${1-}" = "--corpus" ]; then
  if [ $# -ne 2 ]; then
    usage >&2
    exit 2
  fi
  CORPUS_DIR="$2"
else
  if [ $# -ne 1 ]; then
    usage >&2
    exit 2
  fi

  case "$1" in
    -h|--help) usage; exit 0 ;;
    -*) printf 'sage-lint: unknown option %s\n' "$1" >&2; exit 2 ;;
  esac

  FILE="$1"
fi

# ---------------------------------------------------------------------------
# CORPUS MODE — a separate branch from ledger mode, entered and exited here, so nothing
# below this block (the ledger's own path validation, its checks, its exit codes) changes
# shape for a plain `<ledger-path>` call. See CORPUS MODE in the header above for the one
# check this runs and what it cannot see.

if [ -n "${CORPUS_DIR-}" ]; then
  if [ ! -e "$CORPUS_DIR" ] || [ ! -d "$CORPUS_DIR" ] || [ ! -r "$CORPUS_DIR" ]; then
    printf 'sage-lint: %s: not readable, or not a directory, or missing\n' "$CORPUS_DIR" >&2
    exit 3
  fi

  SKILL_FILE="$CORPUS_DIR/SKILL.md"
  if [ ! -e "$SKILL_FILE" ] || [ -d "$SKILL_FILE" ] || [ ! -r "$SKILL_FILE" ]; then
    printf 'sage-lint: %s: not a sage skill directory (no readable SKILL.md)\n' "$CORPUS_DIR" >&2
    exit 3
  fi

  preflight_tools "corpus"

  # The corpus is SKILL.md plus every references/*.md sibling. No references/ dir is not an
  # error — SKILL.md alone still gets checked (fail quiet, same spirit as the ledger side).
  CORPUS_FILES="$SKILL_FILE"
  if [ -d "$CORPUS_DIR/references" ]; then
    for _rf in "$CORPUS_DIR"/references/*.md; do
      [ -e "$_rf" ] && CORPUS_FILES="$CORPUS_FILES
$_rf"
    done
  fi

  OUT=""
  add() {  # add <text-with-trailing-lines-or-empty>
    [ -n "$1" ] || return 0
    if [ -z "$OUT" ]; then OUT="$1"; else OUT="$OUT
$1"; fi
  }

  while IFS= read -r CFILE; do
    [ -n "$CFILE" ] || continue
    case "$CFILE" in
      */*) CDIR="${CFILE%/*}" ;;
      *)   CDIR="." ;;
    esac

    # Every backtick-wrapped `<path>.md` span outside a fenced (```) code block — same fence
    # convention the ledger's "is a ledger" test uses, reused rather than re-written, so a
    # path quoted as an example inside a fence is never read as a citation. A `~`-rooted span
    # is skipped (see CORPUS MODE / Cannot see, header above): it names a path outside this
    # corpus, never one this check can resolve or should flag.
    CANDIDATES=$(awk '
      {
        t = $0
        sub(/^[ \t]+/, "", t)
        if (t ~ /^```/) { infence = !infence; next }
        if (infence) next
        line = $0
        while (match(line, /`[A-Za-z0-9_.\/~-]+\.md`/)) {
          tok = substr(line, RSTART + 1, RLENGTH - 2)
          if (tok !~ /^~/) print NR "\t" tok
          line = substr(line, RSTART + RLENGTH)
        }
      }
    ' "$CFILE" 2>/dev/null)

    [ -n "$CANDIDATES" ] || continue

    while IFS="$(printf '\t')" read -r CLINE CTOK; do
      [ -n "$CTOK" ] || continue

      # OUT OF SCOPE, never checked: the genuinely PER-MACHINE memory files. `memory/local.md`
      # and its `local-*` siblings are seeded once at install time and are deliberately absent
      # from the repo (`harness.md`: "excluded from the synced tree"), so no existence test can
      # be honest about them and checking them would turn "not seeded yet" into a false alarm.
      # This exclusion names the per-machine FILES, not the `memory/` directory -- narrower than
      # it used to be, and narrower on purpose. See CORPUS MODE, header above.
      case "$CTOK" in
        local.md|local-*.md|memory/local.md|memory/local-*.md|*/memory/local.md|*/memory/local-*.md)
          continue ;;
      esac

      # IN SCOPE, resolved BY BASENAME under `<dir>/memory/`: everything else the corpus calls
      # by a memory name. `memory/shared.md` is a real checked-in file, so a dangling citation
      # to it is a real defect and must be reported. The corpus spells it five ways -- bare
      # (`shared.md`), corpus-relative (`memory/shared.md`, `../memory/shared.md`) and
      # repo-rooted (`sage-claude/memory/shared.md`, the path a reader of the REPO sees) -- and
      # only the basename is common to all of them, so the basename is what resolves.
      case "$CTOK" in
        */memory/*|memory/*|shared.md|shared-*.md)
          if [ -e "$CORPUS_DIR/memory/${CTOK##*/}" ]; then
            continue
          fi
          add "sage-lint corpus-citation $CFILE:$CLINE cites '$CTOK' which does not resolve to a file"
          continue ;;
      esac

      # Everything else resolves relative to the CITING FILE'S OWN DIRECTORY, and only there.
      # There is deliberately no corpus-root fallback: one existed, so a file inside
      # `references/` could cite `references/harness.md` root-relative, and it MASKED exactly
      # the defect this check was built for -- a citation that does not resolve from where it
      # is written. The corpus's three such sites were fixed rather than excused.
      if [ -e "$CDIR/$CTOK" ]; then
        continue
      fi
      add "sage-lint corpus-citation $CFILE:$CLINE cites '$CTOK' which does not resolve to a file"
    done <<EOF
$CANDIDATES
EOF
  done <<EOF
$CORPUS_FILES
EOF

  if [ -n "$OUT" ]; then
    printf '%s\n' "$OUT"
    exit 1
  fi
  exit 0
fi

# ---------------------------------------------------------------------------
# Path validation and "is a ledger" (see USAGE above)

if [ ! -e "$FILE" ] || [ -d "$FILE" ] || [ ! -r "$FILE" ]; then
  printf 'sage-lint: %s: not readable, or a directory, or missing\n' "$FILE" >&2
  exit 3
fi

preflight_tools "ledger"

# The one shared definition of the heading grammar and the cell trim, prepended to every awk
# program below that parses either (the repo's clean-code rule: one definition, not seven
# drifting copies — and the one place a parsing fix lands once instead of seven times).
# `###?` rather than `#{2,3}`: mawk (Debian's default awk) and BSD awk have no brace
# intervals — gawk quietly accepts them, which is how the trap ships — so every regex in
# this file is interval-free, the same convention bin/sage-watch.sh already runs on macOS.
AWK_LIB='
  function trim(s) { sub(/^[ \t]+/, "", s); sub(/[ \t]+$/, "", s); return s }
  function is_heading(line) { return (line ~ /^###?[ \t]/) }
  function heading_level(line) { return (line ~ /^###[ \t]/) ? 3 : 2 }
  function heading_of(line,   h) {
    h = line
    sub(/^###?[ \t]+/, "", h)
    sub(/[ \t\r]+$/, "", h)
    return h
  }
'

# Fence-blank the content once: any line between a pair of ``` fence markers becomes an
# empty line, line count preserved, so every later check that scans for headings or table
# rows never mistakes a quoted template inside a fence for the ledger's own record.
SANITIZED=$(awk "$AWK_LIB"'
  {
    t = trim($0)
    if (t ~ /^```/) { infence = !infence; print ""; next }
    if (infence) { print ""; next }
    print
  }
' "$FILE" 2>/dev/null)

REQUIRED_SECTIONS='Plan,Unit table,Assumption log,Decisions and deviations,Findings and dispositions,Run record'

# Three independent marks of ledger-hood; any one is enough (see "Is a ledger" above).
IS_LEDGER=$(awk -v req="$REQUIRED_SECTIONS" "$AWK_LIB"'
  BEGIN { n = split(req, want, ","); for (i = 1; i <= n; i++) ok[want[i]] = 1 }
  NR == 1 && /<!--/ && /sage occupancy duty/ { byheader = 1 }
  {
    line = $0
    if (line ~ /^#[ \t]+sage ledger/) bytitle = 1
    if (is_heading(line)) {
      h = heading_of(line)
      if ((h in ok) && !(h in seen)) { seen[h] = 1; heads++ }
      next
    }
    if (line ~ /^\|/) rows++
  }
  END { if (byheader || bytitle || (heads >= 3 && rows >= 1)) print "yes" }
' <<<"$SANITIZED")

if [ "$IS_LEDGER" != "yes" ]; then
  printf 'sage-lint: %s: not a ledger — needs a line-1 sage occupancy duty comment, or a "# sage ledger" title, or at least three prescribed section headings AND at least one table row\n' "$FILE" >&2
  exit 3
fi

OUT=""
add() {  # add <text-with-trailing-lines-or-empty>
  [ -n "$1" ] || return 0
  if [ -z "$OUT" ]; then OUT="$1"; else OUT="$OUT
$1"; fi
}

# ---------------------------------------------------------------------------
# header / header-fields

FIRST_HDR_LINE=$(awk '
  /sage occupancy duty/ && /<!--/ && /-->/ { print NR; exit }
' "$FILE" 2>/dev/null)

# The third firing mode (see the header manual): the comment OPENS on line 1 and carries the
# phrase, but does not CLOSE there — a multi-line comment, which is present, on line 1, and
# still unreadable to the field parse. Reporting that as "absent" was factually wrong.
HDR_OPEN_UNCLOSED=$(awk '
  NR == 1 { if (/<!--/ && /sage occupancy duty/ && $0 !~ /-->/) print 1; exit }
' "$FILE" 2>/dev/null)

HEADER_OK=0
if [ -z "$FIRST_HDR_LINE" ]; then
  if [ -n "$HDR_OPEN_UNCLOSED" ]; then
    add "sage-lint header $FILE:1 header comment opens on line 1 but does not close on line 1"
  else
    add "sage-lint header $FILE:1 header comment (sage occupancy duty) is absent"
  fi
elif [ "$FIRST_HDR_LINE" != "1" ]; then
  add "sage-lint header $FILE:$FIRST_HDR_LINE header comment present but not on line 1"
else
  HEADER_OK=1
fi

if [ "$HEADER_OK" -eq 1 ]; then
  LINE1=$(sed -n '1p' "$FILE" 2>/dev/null)

  if printf '%s' "$LINE1" | grep -q 'Generation:'; then
    # A bounded token, not everything-to-the-next-comma: the value is the run of digits and
    # slashes right after `Generation:`, so `Generation: 1` and `Generation: 1.` are as
    # legal as the stamped `Generation: 1,` — requiring the comma made this check fire on a
    # legal header, the one broken-promise defect of the first release — while `0` and
    # `0/3` still fail the positive-integer test below. The captured value is the WHOLE
    # field, not a valid prefix of it: everything up to the first comma, the first blank, or
    # the end of the line. Capturing a prefix instead let `12x`, `1-2` and `1-->` all read as
    # a legal `1`. One trailing period is then stripped, because a header that ends the
    # sentence (`Generation: 1.`) is legal and a comma-delimited one is the stamped form.
    # Known gap: `.*` is greedy, so a line carrying `Generation:` TWICE is validated on the
    # last one. Two such fields are themselves malformed, and this matches the behaviour of
    # the comma-delimited version this replaced. `[[:blank:]]`, never `[ \t]`:
    # BSD sed reads `\t` inside a bracket expression as two literal characters.
    GEN=$(printf '%s' "$LINE1" | sed -n 's/.*Generation:[[:blank:]]*\([^,[:blank:]]*\).*/\1/p')
    GEN=${GEN%.}
    if ! printf '%s' "$GEN" | grep -qE '^[1-9][0-9]*$'; then
      add "sage-lint header-fields $FILE:1 Generation is not a bare positive integer: '$GEN'"
    fi
  else
    add "sage-lint header-fields $FILE:1 header comment carries no Generation: field"
  fi

  if printf '%s' "$LINE1" | grep -q 'role:'; then
    ROLE=$(printf '%s' "$LINE1" | sed -n 's/.*role:[[:blank:]]*\([A-Za-z]*\).*/\1/p')
    if [ "$ROLE" != "parent" ] && [ "$ROLE" != "supervisor" ]; then
      add "sage-lint header-fields $FILE:1 role is neither 'parent' nor 'supervisor': '$ROLE'"
    fi
  else
    add "sage-lint header-fields $FILE:1 header comment carries no role: field"
  fi
fi

# ---------------------------------------------------------------------------
# state-enum

CHK=$(awk -v FILE="$FILE" "$AWK_LIB"'
  {
    line = $0
    if (is_heading(line)) {
      in_table = 0
      heading = heading_of(line)
      if (heading == "Unit table" && unit_idx == 0) unit_idx = NR
      next
    }
    if (line ~ /^\|/) {
      if (!in_table) {
        in_table = 1
        expect_sep = 1
        is_unit = (unit_idx > 0 && captured == 0 && heading == "Unit table")
        if (is_unit) {
          n = split(line, cells, "|")
          state_idx = 0
          for (i = 2; i < n; i++) { if (tolower(trim(cells[i])) == "state") { state_idx = i; break } }
          header_line = NR
          header_seen = 1
        }
        next
      } else if (expect_sep) {
        expect_sep = 0
        next
      } else {
        if (is_unit && state_idx > 0) {
          n = split(line, cells, "|")
          if (state_idx < n) {
            id = trim(cells[2])
            val = trim(cells[state_idx])
            if (val == "") {
              # An emptied cell is the absence case of the same invariant, not a parse
              # failure: the row is well-formed and the cell is there, holding nothing.
              printf "sage-lint state-enum %s:%d unit '"'"'%s'"'"' has an empty state cell\n", FILE, NR, id
            } else if (val !~ /^(planned|running|reported|blocked|failed|abandoned|inline)([^A-Za-z]|$)/) {
              # A legal state word at a real word boundary: end of the cell, or followed by
              # anything that is not a letter (space, comma, semicolon, ...). `reported,` and
              # `reported 07:11` both pass; `done ...` and `reportedly ...` both fail.
              printf "sage-lint state-enum %s:%d unit '"'"'%s'"'"' has illegal state '"'"'%s'"'"'\n", FILE, NR, id, val
            }
          }
        }
        next
      }
    }
    if (in_table) { if (is_unit) captured = 1; in_table = 0 }
  }
  END {
    if (unit_idx > 0 && header_seen && state_idx == 0)
      printf "sage-lint state-enum %s:%d Unit table has no column labelled '"'"'state'"'"'\n", FILE, header_line
    if (unit_idx > 0 && !header_seen)
      printf "sage-lint state-enum %s:%d Unit table heading has no table under it\n", FILE, unit_idx
  }
' <<<"$SANITIZED")
add "$CHK"

# ---------------------------------------------------------------------------
# triage-orphan

CHK=$(awk -v FILE="$FILE" "$AWK_LIB"'
  function idtoken(cell,   t, i, j) {
    t = trim(cell)
    i = index(t, " ")
    if (i > 0) t = substr(t, 1, i - 1)
    j = index(t, "(")
    if (j > 0) t = substr(t, 1, j - 1)
    return t
  }
  function is_id(t) {
    return (t ~ /^[A-Z]$/) || (t ~ /^[A-Z][A-Z]?[A-Z]?[A-Z]?-?[0-9][0-9]?[0-9]?[a-z]?$/)
  }
  # delabel: a header cell compared without markdown emphasis or code ticks, so `**triage**`
  # and `` `disposition` `` still read as their words. Ledgers here bold table cells freely.
  function delabel(s) { gsub(/[*_`]/, "", s); return trim(tolower(s)) }
  # sec_match/sec_of: prefix-matched prescribed-section identity — exact name, or the name
  # followed by a non-alphanumeric separator (`Unit table (phase 2)`, `Run record — phase
  # 2`). `Planning` does not match `Plan`; `Plan B` does, and that is the accepted trade.
  function sec_match(h, name,   c) {
    if (h == name) return 1
    if (index(h, name) == 1) {
      c = substr(h, length(name) + 1, 1)
      if (c !~ /[A-Za-z0-9]/) return 1
    }
    return 0
  }
  function sec_of(h) {
    if (sec_match(h, "Plan")) return "Plan"
    if (sec_match(h, "Unit table")) return "Unit table"
    if (sec_match(h, "Assumption log")) return "Assumption log"
    if (sec_match(h, "Decisions and deviations")) return "Decisions and deviations"
    if (sec_match(h, "Findings and dispositions")) return "Findings and dispositions"
    if (sec_match(h, "Run record")) return "Run record"
    return ""
  }
  function rstrip(s) { sub(/[ \t]+$/, "", s); return s }
  # trailing_token: the run of [A-Za-z0-9-] characters at the very end of s, but only if the
  # character just before that run (if any) is NOT itself alnum — a genuine word boundary,
  # not the tail of a longer identifier. Returns "" when no such boundary-clean run exists.
  function trailing_token(s,   i, c, tok, bc) {
    s = rstrip(s)
    i = length(s)
    tok = ""
    while (i > 0) {
      c = substr(s, i, 1)
      if (c ~ /[A-Za-z0-9-]/) { tok = c tok; i-- } else break
    }
    if (tok == "") return ""
    if (i > 0) {
      bc = substr(s, i, 1)
      if (bc ~ /[A-Za-z0-9]/) return ""
    }
    return tok
  }
  {
    line = $0
    trimmedline = line
    sub(/^[ \t]+/, "", trimmedline)
    if (is_heading(line)) {
      in_table = 0
      h = heading_of(line)
      # Section identity is PREFIX-matched here (`Unit table (phase 2)`, `Run record —
      # phase 2` — legacy multi-run ledgers suffix their section names, and the id
      # namespaces are the same), and section extents are NESTING-AWARE: a heading at a
      # LOWER level than the current section is a subsection and stays inside; one at the
      # same or a higher level ends it. Legacy ledgers keep findings material in `###`
      # subsections under `## Findings and dispositions`, and a flat tracker read every one
      # of those dispositions tables as a foreign section — an orphan storm on files that
      # were, in their own format, fully dispositioned. A sibling-level section (`### Fix
      # log` beside `### Run record`) still ends the context, which is what keeps a fix
      # table outside the exclusions and lets an untriaged id there fire.
      s = sec_of(h)
      if (s != "") {
        section = s; seclevel = heading_level(line)
        if (s == "Findings and dispositions") find_exact = (h == s)
      } else if (section != "" && heading_level(line) > seclevel) {
        ; # a subsection: the enclosing prescribed section still governs
      } else {
        section = ""; seclevel = 0
      }
      if (section == "Findings and dispositions" && find_exact && find_idx == 0) find_idx = NR
      next
    }
    # Assumption log, Plan, Unit table and Decisions and deviations each carry their own
    # id/index namespace (`A1`, `#`-numbered rows, unit ids, `D1`) — never a source of
    # finding-id candidates — and the Findings section itself supplies the triage set, not
    # candidates. Exclusion is by prescribed SECTION only; a table header FIRST-column
    # label such as `id` excludes nothing (a fix table headed `id` holding an untriaged
    # finding must fire — the label exclusion this replaces let exactly that escape).
    # Candidates come from tables OUTSIDE every prescribed section, plus the Run record
    # (its tables and its `Findings:` prose line can cite ids that were never triaged) —
    # minus SELF-TRIAGED tables: a table carrying a column labelled `triage` or
    # `disposition` anywhere in its header row records its own dispositions in place (the
    # legacy multi-run layout), and an id dispositioned where it lives is not an untriaged
    # orphan, however non-prescribed its home. Known non-finding ids are handled by
    # SUBTRACTION: ids from any Unit-table section and `D<n>` ids from any Decisions
    # section are collected below, and a candidate matching one is dropped in END rather
    # than never harvested.
    candidate_ok = (section == "" || section == "Run record")
    if (line ~ /^\|/) {
      if (!in_table) {
        in_table = 1
        expect_sep = 1
        is_find = (find_idx > 0 && find_captured == 0 && section == "Findings and dispositions" && find_exact)
        is_unit = (section == "Unit table")
        selftriaged = 0
        n = split(line, cells, "|")
        for (i = 2; i < n; i++) {
          lab = delabel(cells[i])
          if (index(lab, "triage") > 0 || index(lab, "disposition") > 0) selftriaged = 1
          # triage-state rides this same header walk: the ONE table triage-orphan reads as
          # its triage set is the one whose cells triage-state rules on, so "which table is
          # the triage table" keeps one owner. Exact label, not the substring test above:
          # that one is deliberately loose (it only EXCLUDES a table from candidacy, where a
          # wrong guess costs nothing), while this one selects a column whose every cell then
          # gets ruled on, where a wrong guess reports a whole table of false violations.
          if (is_find && find_tri == 0 && (lab == "triage" || lab == "disposition")) find_tri = i
        }
        if (is_find) find_ncell = n
        next
      } else if (expect_sep) {
        expect_sep = 0
        next
      } else {
        n = split(line, cells, "|")
        tok = idtoken(cells[2])
        # n == find_ncell, not just find_tri < n: a row carrying an unescaped `|` (inside a
        # code span, say) splits into MORE cells than its header, so the triage column slides
        # and the cell read is text from some other column. Measured on the local corpus: the
        # only violation this check produced over every ledger on the machine was exactly
        # that row, and the text it reported was a fragment of a jq command. A stray pipe is
        # named in FAIL QUIET as a parse to stay silent on, so it stays silent.
        if (is_find && find_tri > 0 && n == find_ncell) {
          tri = delabel(cells[find_tri])
          if (tri == "")
            printf "sage-lint triage-state %s:%d finding '"'"'%s'"'"' has an empty triage cell\n", FILE, NR, tok
          else if (tri !~ /(^|[^a-z])(accepted|rejected|deferred|user decision|merged|retracted|disclosed)([^a-z]|$)/)
            printf "sage-lint triage-state %s:%d finding '"'"'%s'"'"' is parked outside every disposition word: '"'"'%s'"'"'\n", FILE, NR, tok, substr(trim(cells[find_tri]), 1, 60)
        }
        if (is_unit && tok != "") unit_id[tok] = 1
        if (section == "Decisions and deviations" && tok ~ /^D[0-9]+$/) dec_id[tok] = 1
        if (tok != "" && is_id(tok)) {
          if (is_find) {
            find_count[tok]++
            if (find_count[tok] == 1) find_line[tok] = NR
            find_last[tok] = NR
          } else if (candidate_ok && !selftriaged) {
            if (!(tok in cand_line)) cand_line[tok] = NR
          }
        }
        next
      }
    }
    if (in_table) { if (is_find) find_captured = 1; in_table = 0 }
    # Prose scan: a finding-shaped id immediately followed by a parenthetical annotation
    # (`K (residual note...)`), and ONLY on the Run record `Findings:` summary line (the one
    # prose field the prescribed template reserves for exactly this content — see
    # `../references/dispatch.md` `### Run record`). Deliberately narrower than "anywhere
    # outside a table": a whole-document scan re-catches ordinary criterion citations like
    # "R5 (`needs-playtest`) is Awaiting human" or "case C6 (i-frames...) was ruled" in a
    # Run record OUTCOME/Gaps prose — same shape, same word-boundary-before-`(`, zero
    # relation to triage — and a false alarm there costs more than the citations this check
    # would otherwise miss. A token has to sit at a clean word boundary right before `(` to
    # count even on the `Findings:` line, exactly as in a table cell.
    is_findings_line = (trimmedline ~ /^Findings:/)
    if (candidate_ok && is_findings_line && index(line, "(") > 0) {
      rest = line
      while ((p = index(rest, "(")) > 0) {
        before = substr(rest, 1, p - 1)
        tok = trailing_token(before)
        if (tok != "" && is_id(tok) && !(tok in cand_line)) cand_line[tok] = NR
        rest = substr(rest, p + 1)
      }
    }
  }
  END {
    if (in_table && is_find) find_captured = 1
    for (id in find_count)
      if (find_count[id] >= 2)
        printf "sage-lint triage-orphan %s:%d duplicate finding id '"'"'%s'"'"' appears %d times in Findings and dispositions\n", FILE, find_last[id], id, find_count[id]
    for (id in cand_line)
      if (!(id in find_count) && !(id in unit_id) && !(id in dec_id))
        printf "sage-lint triage-orphan %s:%d orphan finding id '"'"'%s'"'"': appears in the ledger but has no row in the first table under Findings and dispositions (the only table this check reads as triage)\n", FILE, cand_line[id], id
  }
' <<<"$SANITIZED" | sort -t: -k2 -n)
add "$CHK"

# ---------------------------------------------------------------------------
# plan-unit

extract_table_ids() {  # extract_table_ids <heading-name>  — prints "id<TAB>line" rows, or
                        # "NOTABLE<TAB>line" if the heading exists with no table under it,
                        # or nothing at all if the heading does not exist.
  awk -v target="$1" "$AWK_LIB"'
    # plain_id: an amendment tag is not part of the id (see plan-unit in the header manual).
    # `2 superseded → D2` and `2 (superseded)` both reduce to `2`. The dangling separator —
    # arrow, dash, comma — is stripped only in the branch that actually removed a tag, so an
    # id written `**5**` keeps its own punctuation.
    function plain_id(s,   p) {
      p = index(s, "(")
      if (p > 0) s = trim(substr(s, 1, p - 1))
      p = index(s, "superseded")
      if (p == 0) p = index(s, "Superseded")
      if (p > 0) {
        s = substr(s, 1, p - 1)
        sub(/[^A-Za-z0-9]+$/, "", s)
        s = trim(s)
      }
      return s
    }
    {
      line = $0
      if (is_heading(line)) {
        in_table = 0
        heading = heading_of(line)
        if (heading == target && th_idx == 0) th_idx = NR
        next
      }
      if (heading == target && th_idx > 0 && captured == 0) {
        if (line ~ /^\|/) {
          saw_table = 1
          if (!in_table) { in_table = 1; expect_sep = 1; next }
          else if (expect_sep) { expect_sep = 0; next }
          else {
            n = split(line, cells, "|")
            id = plain_id(trim(cells[2]))
            if (id != "") printf "%s\t%d\n", id, NR
            next
          }
        } else if (in_table) { captured = 1; in_table = 0 }
      }
    }
    END {
      if (th_idx > 0 && saw_table == 0) printf "NOTABLE\t%d\n", th_idx
    }
  ' <<<"$SANITIZED"
}

DECISIONS_TEXT=$(awk "$AWK_LIB"'
  {
    line = $0
    if (is_heading(line)) {
      heading = heading_of(line)
      next
    }
    if (heading == "Decisions and deviations") print line
  }
' <<<"$SANITIZED")

# decisions_explain <id> — does this id appear in a `Decisions and deviations` section at a
# real WORD BOUNDARY? Boundary rather than bare substring, because the ledger spec now keys
# Decisions rows `D1`, `D2`, ... : under a substring test the presence of a row `D2` would
# silence this check for unit id `2` in EVERY compliant ledger, disabling the check by the
# act of obeying the rule. Boundary matching still fails the same way a human skimming for
# "was this explained anywhere" fails — an id mentioned at a boundary in an unrelated
# sentence silences it, and that is the documented, accepted trade — but it no longer
# collides with a decision id.
decisions_explain() {
  [ -n "$DECISIONS_TEXT" ] || return 1
  printf '%s\n' "$DECISIONS_TEXT" | awk -v id="$1" '
    BEGIN { n = length(id); if (n == 0) exit 1 }
    {
      s = $0; p = 0
      while ((q = index(substr(s, p + 1), id)) > 0) {
        p = p + q
        before = (p > 1) ? substr(s, p - 1, 1) : ""
        after = substr(s, p + n, 1)
        if (before !~ /[A-Za-z0-9]/ && after !~ /[A-Za-z0-9]/) { found = 1; exit }
      }
    }
    END { exit (found ? 0 : 1) }
  '
}

PLAN_EX=$(extract_table_ids "Plan")
UNIT_EX=$(extract_table_ids "Unit table")

PLAN_NOTABLE=""
UNIT_NOTABLE=""
if [ -n "$PLAN_EX" ] && printf '%s\n' "$PLAN_EX" | head -1 | grep -q '^NOTABLE'; then
  LN=$(printf '%s\n' "$PLAN_EX" | head -1 | cut -f2)
  add "sage-lint plan-unit $FILE:$LN Plan section has no table"
  PLAN_NOTABLE=1
fi
if [ -n "$UNIT_EX" ] && printf '%s\n' "$UNIT_EX" | head -1 | grep -q '^NOTABLE'; then
  UNIT_NOTABLE=1
fi

if [ -n "$PLAN_EX" ] && [ -n "$UNIT_EX" ] && [ -z "$PLAN_NOTABLE" ] && [ -z "$UNIT_NOTABLE" ]; then
  PLAN_IDS=$(printf '%s\n' "$PLAN_EX" | cut -f1 | awk '!seen[$0]++')
  UNIT_IDS=$(printf '%s\n' "$UNIT_EX" | cut -f1 | awk '!seen[$0]++')

  PU_OUT=""
  while IFS= read -r id; do
    [ -n "$id" ] || continue
    if ! printf '%s\n' "$UNIT_IDS" | grep -qxF "$id"; then
      if ! decisions_explain "$id"; then
        LN=$(printf '%s\n' "$PLAN_EX" | awk -F'\t' -v id="$id" '$1==id{print $2; exit}')
        PU_OUT="${PU_OUT}sage-lint plan-unit $FILE:$LN id '$id' is in Plan but not in Unit table
"
      fi
    fi
  done <<<"$PLAN_IDS"
  while IFS= read -r id; do
    [ -n "$id" ] || continue
    if ! printf '%s\n' "$PLAN_IDS" | grep -qxF "$id"; then
      if ! decisions_explain "$id"; then
        LN=$(printf '%s\n' "$UNIT_EX" | awk -F'\t' -v id="$id" '$1==id{print $2; exit}')
        PU_OUT="${PU_OUT}sage-lint plan-unit $FILE:$LN id '$id' is in Unit table but not in Plan
"
      fi
    fi
  done <<<"$UNIT_IDS"
  add "${PU_OUT%$'\n'}"
fi

# ---------------------------------------------------------------------------
# disclosure-home

# Trigger-anywhere, home-required (see the header manual): every line is scanned for the
# keyword sets; a set found anywhere fires ONE violation — at the first trigger line outside
# the home — unless at least one line under the home section also carries the set. A
# restatement of a properly-homed disclosure is legal; a disclosure whose home is empty is
# the failure this check exists for.
CHK=$(awk -v FILE="$FILE" "$AWK_LIB"'
  {
    line = $0
    if (is_heading(line)) {
      heading = heading_of(line)
      next
    }
    low = tolower(line)
    if (index(low, "same-family") > 0 || index(low, "same family") > 0 || index(low, "self-preference bias") > 0) {
      if (heading == "Findings and dispositions") fam_home = 1
      else if (fam_first == 0) fam_first = NR
    }
    if (index(low, "rail-1") > 0 || index(low, "rail 1") > 0) {
      if (heading == "Decisions and deviations") rail_home = 1
      else if (rail_first == 0) rail_first = NR
    }
  }
  END {
    if (fam_first > 0 && !fam_home)
      printf "sage-lint disclosure-home %s:%d same-family/residual-bias keywords appear in the ledger but no line under Findings and dispositions (the required home) carries the disclosure\n", FILE, fam_first
    if (rail_first > 0 && !rail_home)
      printf "sage-lint disclosure-home %s:%d rail-1 keywords appear outside Decisions and deviations and no rail-1 line exists there (the required home for an authorisation)\n", FILE, rail_first
  }
' <<<"$SANITIZED")
add "$CHK"

# ---------------------------------------------------------------------------
# amend-tag

CHK=$(awk -v FILE="$FILE" "$AWK_LIB"'
  {
    line = $0
    if (is_heading(line)) {
      in_table = 0
      heading = heading_of(line)
      next
    }
    if (line !~ /^\|/) { in_table = 0; next }
    n = split(line, cells, "|")
    first = trim(cells[2])
    if (!in_table) {
      in_table = 1
      expect_sep = 1
      # The Decisions table counts as a referent source ONLY when it is keyed by `id`.
      if (heading == "Decisions and deviations" && dec_seen == 0) {
        dec_seen = 1
        k = first
        gsub(/[*_`]/, "", k)
        dec_keyed = (tolower(trim(k)) == "id")
      }
      next
    }
    if (expect_sep) { expect_sep = 0; next }
    if (heading == "Decisions and deviations" && dec_keyed && first != "") { dec_id[first] = 1; next }
    if (heading == "Plan" || heading == "Unit table") {
      if (tolower(first) ~ /superseded/) {
        ref = ""
        m = first
        while (match(m, /D[0-9]+/)) {
          ref = substr(m, RSTART, RLENGTH)
          m = substr(m, RSTART + RLENGTH)
        }
        nt++
        t_line[nt] = NR; t_cell[nt] = first; t_ref[nt] = ref
      }
    }
  }
  END {
    # Precondition, not a violation: no id-keyed Decisions table means nothing to resolve
    # against, and a check with nothing to parse says nothing (see FAIL QUIET).
    if (!dec_keyed) exit 0
    for (i = 1; i <= nt; i++) {
      if (t_ref[i] == "")
        printf "sage-lint amend-tag %s:%d row '"'"'%s'"'"' is tagged superseded but names no D<n> row in Decisions and deviations\n", FILE, t_line[i], t_cell[i]
      else if (!(t_ref[i] in dec_id))
        printf "sage-lint amend-tag %s:%d row '"'"'%s'"'"' names %s, which has no row in Decisions and deviations\n", FILE, t_line[i], t_cell[i], t_ref[i]
    }
  }
' <<<"$SANITIZED")
add "$CHK"

# ---------------------------------------------------------------------------
# sections

CHK=$(awk -v FILE="$FILE" -v req="$REQUIRED_SECTIONS" "$AWK_LIB"'
  BEGIN { n = split(req, want, ",") }
  {
    line = $0
    if (is_heading(line)) {
      h = heading_of(line)
      for (i = 1; i <= n; i++) {
        if (h == want[i]) {
          count[h]++
          lastline[h] = NR
        }
      }
    }
  }
  END {
    for (i = 1; i <= n; i++) {
      name = want[i]
      c = count[name] + 0
      if (c == 0) printf "sage-lint sections %s:1 section '"'"'%s'"'"' is missing\n", FILE, name
      else if (c > 1) printf "sage-lint sections %s:%d section '"'"'%s'"'"' appears %d times (expected exactly once)\n", FILE, lastline[name], name, c
    }
  }
' <<<"$SANITIZED")
add "$CHK"

# ---------------------------------------------------------------------------
# splice

CHK=$(awk -v FILE="$FILE" "$AWK_LIB"'
  {
    line = $0
    if (open && (is_heading(line) || line ~ /^\|/))
      printf "sage-lint splice %s:%d %s sits inside an unclosed inline-code span -- a mis-anchored edit spliced structure into the middle of a sentence\n", \
        FILE, NR, (is_heading(line) ? "heading" : "table row")
    # Parity is tracked AFTER the test, so the line that opens a span is not itself a
    # finding -- only the structure that follows it is. $SANITIZED has already blanked every
    # fenced line, so a ``` block cannot move this parity.
    if (gsub(/`/, "`") % 2 == 1) open = !open
  }
' <<<"$SANITIZED")
add "$CHK"

# ---------------------------------------------------------------------------

if [ -n "$OUT" ]; then
  printf '%s\n' "$OUT"
  exit 1
fi
exit 0
