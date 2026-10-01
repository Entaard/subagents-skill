#!/usr/bin/env bash
# sage-lint.sh — deterministic record-integrity checker for one sage ledger.
#
# RUN BLOCK. Two invocations, nothing else to configure:
#
#   sage-lint.sh <ledger-path>     check one ledger
#   sage-lint.sh --corpus <dir>    check a sage skill directory's own corpus
#
# One line per violation, fixed field order:
#
#   sage-lint <check-id> <path>:<line> <message>
#
# A clean file prints NOTHING — no summary line, no "0 violations". Exit 0 clean, 1
# violations were printed, 2 usage error (nothing was read), 3 the path is unreadable, is a
# directory, is not a ledger at all, or is an old-format ledger (this lint checks the
# four-section schema only).
#
# The ten ledger check ids: state-enum triage-orphan triage-state findings-shape
# disclosure-home sections frame splice secret-shape alt-record.
#
# Empty stdout WITH a line on stderr is not a clean file: a core tool (awk, sed, grep, sort,
# cut, head) is missing. Install it and run again. Never disable this lint — not for that,
# and not to quiet a violation. A violation still standing at Step 6 is a surfaced event,
# written into the run record with the reason it stands.
#
# Everything below is the maintainer's manual: what each check reads, what it cannot see.
# END RUN BLOCK
#
# The one file it checks is `.claude/plans/sage-ledger-<session>.md`, the record of one
# orchestration run — see `../references/dispatch.md` `## The ledger` for the prescribed shape.
# `sage-ledger.sh` is the writer of that file; this script is its checker.
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
#   --corpus <dir>      A SECOND, INDEPENDENT MODE (see CORPUS MODE below), never a
#                        eleventh ledger check: it checks a sage skill DIRECTORY's own
#                        corpus for dangling `.md` citations, credential shapes in its
#                        memory, and machine-local facts in its portable memory template,
#                        not a ledger. `<dir>` must carry a
#                        readable `SKILL.md`; `--corpus` with no following argument, or with
#                        more than one argument total, is a usage error (exit 2) exactly like
#                        the ledger form.
#   --help / -h         Print this reminder, exit 0. Any other argument starting with `-`,
#                        zero arguments, or more than one argument (outside the `--corpus`
#                        form above) is a usage error (exit 2) — nothing is read in that case.
#
# THE LEDGER SCHEMA this lint reads: five headings, `##` or `###`, names EXACT — `Plan`,
# `Resume state`, `Decisions`, `Findings`, `Run record`. `Plan` holds `ASK:` and the other
# field lines, then the unit table; `Findings` holds the findings table; `Decisions` holds the
# `D<n>` table.
#
# "Is a ledger" (the test the path must pass to be checked at all, rather than rejected):
# readable, not a directory, and carrying at least ONE of two marks of being a RECORD rather
# than a DESCRIPTION of one — every heading and table row below read OUTSIDE a fenced (```)
# code block, so a file that quotes the ledger template inside a fence gets no credit for it:
#
#   1. a `# sage ledger` title at `#` depth (any letter case); or
#   2. at least THREE of the five schema headings above AND at least one markdown table row.
#
# One schema heading is deliberately NOT enough: `../references/dispatch.md`, the ledger SPEC
# and the most likely wrong path a caller hands this script, carries the prescribed headings
# as real headings and no table row. A path that fails this test is exit 3, never a pile of
# violations about a file that was never a ledger.
#
# OLD FORMAT is tested BEFORE that, and is also exit 3 with one stderr line: any heading
# exactly `Unit table`, `Findings`, `Assumption log` or `Decisions and
# deviations`, or a line 1 containing `sage occupancy duty`. Such a file is a ledger of the
# eight-section layout; this lint checks the four-section schema only.
#
# TABLE CELLS. Every table-reading check splits a row through one shared awk function
# (`split_cells` in AWK_LIB) that treats `\|` as a literal pipe inside a cell. A bare `|`
# still splits, so a code span holding an unescaped pipe still shifts later columns; the
# writer (`sage-ledger.sh`) always escapes it.
#
# ---------------------------------------------------------------------------
# THE CHECKS — exactly ten, each with a short stable id. Every check reads ONLY the text
# named below and states what it therefore cannot see; that blind spot is not a bug in the
# check, it is the check's honest shape.
#
#   state-enum
#     Reads: the header row of the FIRST table under the FIRST `Plan` heading (to find the
#       column literally labelled `state`, never by counting to a fixed position) and every
#       data row of that table.
#     Fires: a data row's `state` cell does not BEGIN with one of
#       `planned running reported blocked failed abandoned inline` AT A WORD BOUNDARY — the
#       enum word must be the whole cell, or be followed by anything that is not a letter
#       (space, comma, semicolon, ...). Trailing annotation is legal: `reported 07:11` and
#       `reported, steered, re-reported` both pass. `done 07:13...` fails; a word that only
#       starts the same way, like `reportedly`, also fails (boundary check, not a prefix
#       check). An EMPTY state cell fails too: every unit carries a value from the enum. Or
#       the Plan table has no column labelled `state` (one violation for the table, not one
#       per row). Or the `Plan` heading exists with NO table under it — one violation for the
#       section; a row the table never had is otherwise invisible to every per-row check.
#     Cannot see: whether a state was actually KEPT current while the unit ran, only whether
#       the word written down is a legal word. A data row SHORTER than the state column is a
#       parse failure, not an empty cell, and stays silent per FAIL QUIET.
#
#   triage-orphan
#     Reads: the first table under the FIRST exact `Findings` heading (its first column, taken
#       as the set of real finding ids) — the ONLY source of "this id has a triage row".
#       Candidate ids (things that might be orphans) are harvested from two places: (a) the
#       first column of tables OUTSIDE every prescribed section, plus tables under `Run
#       record`. `Plan`, `Resume state`, `Decisions` and `Findings` each carry their own
#       namespace (unit ids, a resume checkpoint, `D1`, `D2`..., the triage set) and none of
#       the four is a candidate source. The exclusion is by prescribed SECTION, never by a
#       table's header label. Section extents are NESTING-AWARE: a lower-level heading inside
#       a prescribed section stays inside it, while a sibling-level heading ends it. A
#       harvested candidate is dropped when it is a KNOWN NON-FINDING id: an id in the Plan
#       table's id column, or a `D<n>` id from the Decisions table's id column.
#       And (b) PROSE, but ONLY on the Run record's `Findings:` summary line — a
#       finding-shaped token at a clean word boundary immediately before a `(`, e.g.
#       `K (residual note, not yet triaged)`. Deliberately narrower than "any prose anywhere":
#       a whole-document scan re-catches ordinary criterion citations with the identical shape.
#     What counts as "looks like a finding id" (conservative on purpose): a bare single
#       UPPERCASE letter, OR 1-4 uppercase letters, an optional hyphen, 1-3 digits, and an
#       optional single lowercase suffix letter (`F1`, `F2a`, `A`, `CI-01`, `F-1`). This
#       deliberately MISSES a shape like `R1-rej` — a missed id is silence, never a false
#       alarm, which is the trade this check is required to make.
#     Fires: a harvested candidate id has no row in the Findings table (orphan — a set
#       difference, so a prose CITATION of an already-triaged id cannot fire); or a token
#       appears twice within the Findings table itself (duplicate).
#     Cannot see: an id that does not match the shape above, or a prose id with no `(` right
#       after it. A finding whose id COLLIDES with a unit id or a Decisions id (`U1`, `D2`)
#       is dropped by the known-non-finding subtraction. Further deliberate escapes:
#         - A table in a subsection UNDER `Findings` is inside the prescribed section, so an
#           untriaged id written THERE is invisible.
#         - A table is treated as SELF-TRIAGED on its header row alone: any header cell
#           merely CONTAINING `triage` or `disposition` excludes the table from candidacy,
#           even with all its cells empty.
#         - Section identity is prefix-matched, so `Plan B` reads as `Plan` and is excluded.
#         - Only `##` and `###` are headings here. A `####` heading does not end a section.
#
#   triage-state
#     Reads: the triage column of the SAME table `triage-orphan` reads as its triage set —
#       the first table under the FIRST exact `Findings` heading. It runs inside that check's
#       awk pass so "which table is the triage table" has one owner. The column is found by
#       LABEL: a header cell whose delabelled text (emphasis and code ticks stripped,
#       lowercased) is EXACTLY `triage` or `disposition`. The exact test is deliberately
#       stricter than the substring test `triage-orphan` uses: that one only EXCLUDES a table
#       from candidacy, while this one SELECTS a column whose every cell then gets ruled on.
#     Fires: a data row whose triage cell is EMPTY, or carries no disposition word anywhere
#       in it at a word boundary. The words: `accepted`, `rejected`, `deferred` and
#       `user decision` — the four triage states in `../references/dispatch.md`
#       `## Findings and triage` — plus `merged`, `retracted` and `disclosed`, which close a
#       finding without one of the four. It catches the PARKED cell (`pending triage`,
#       `open`, `TBD`, empty), not every cell outside the spec's list. The word may sit
#       anywhere in the cell: `all accepted — wording fixes applied` passes. A longer word
#       that merely CONTAINS a state word does not count — `unaccepted` fires.
#     Cannot see:
#       - A Findings table with NO triage column: silence. `state-enum` DOES report a missing
#         `state` column; the difference is that every Plan table carries that column.
#       - Whether a legal word is the RIGHT disposition, or whether `rejected` carries its
#         evidence and `deferred` its owner.
#       - A row whose cell count differs from its header row's after `\|` is read as a
#         literal pipe — an unescaped `|` in a cell slides every later column and the row is
#         skipped in silence (see `findings-shape` for the narrow signature it does report).
#       - A findings table under a differently-named heading: the heading locates the table.
#
#   findings-shape
#     Reads: the SAME table `triage-orphan` reads as its triage set, and its SHAPE rather than
#       its words: each data row's cell count against the header row's, and where a row is
#       over-long, the contents of the overflow.
#     Fires: a data row splits into MORE cells than the header AND carries an empty interior
#       cell immediately followed by a finding-shaped id — the signature of a finding folded
#       onto the previous row's line by a stray `||`. Such a finding has no row of its own,
#       so it has no id for `triage-orphan` and no triage cell for `triage-state`.
#     Cannot see: an over-long row with no empty cell at the join, or a fold whose second id
#       does not match the id shape — silence, never a false alarm. Deliberately NOT a plain
#       cell-count check: a legitimate cell holding an unescaped `|` (a jq command, a code
#       span) over-splits, and a plain count reports every one of them.
#
#   disclosure-home
#     Reads: EVERY line of the document (outside fences) — trigger-anywhere, home-required.
#     Keyword sets (case-insensitive substring, heuristic): a same-family / residual
#       maker-checker bias disclosure is recognised by `same-family`, `same family`, or
#       `self-preference bias`; its one required home is `Findings`. A rail-1 authorisation is
#       recognised by `rail-1`, or by `rail 1` when what follows is not a digit, a decimal
#       point, or a `k`/`m` unit suffix — a rail FIGURE such as `rail 150k` is bookkeeping,
#       not an authorisation; its one required home is `Decisions`.
#     Fires: a keyword set appears somewhere in the document while NO line under its home
#       section carries that same set — one violation per keyword set, pointing at the first
#       trigger line. A trigger outside the home is legal WHEN the home also carries the
#       disclosure.
#     KNOWN FALSE-POSITIVE MODE: a ledger that merely DISCUSSES this rule trips the keywords
#       without owing the disclosure. Reword the discussing line, or carry this check's line
#       to Step 6 as a surfaced event with the reason next to it.
#     Cannot see: a real disclosure phrased without any of the keywords, and it cannot tell a
#       real disclosure from an incidental use of the same words.
#
#   sections
#     Reads: every `##`/`###` heading line in the document (outside fences), compared against
#       the five REQUIRED names: `Plan`, `Resume state`, `Decisions`, `Findings`,
#       `Run record`.
#     Fires: a required name that appears zero times (missing), or more than once
#       (repeated) — one violation per offending name, not per extra occurrence.
#     Cannot see: a heading text that is CLOSE but not exact (`### Decisions (continued)` does
#       not count as a second `Decisions`). Where that near-miss was MANUFACTURED by a bad
#       edit, `splice` below is what sees it.
#
#   frame
#     Reads: the lines of the `Plan` section (from its heading to the next heading).
#     Fires: no line whose text starts with `ASK:` — after optional leading whitespace, a `-`
#       bullet, or `**` — or an `ASK:` line with nothing after the colon. One violation.
#       Silent when there is no `Plan` heading at all: `sections` reports that.
#     Cannot see: whether the ASK is the user's actual words, only that one was written down.
#
#   splice
#     Reads: every line outside a fenced block, tracking inline-code (`) parity cumulatively
#       across lines. That is deliberately LOOSER than a markdown reader, which never lets an
#       inline span cross a block boundary -- the looseness is what lets it see a splice that
#       cut a sentence in half, and it is also this check's one false-positive shape.
#     Fires: a heading or a table row appears while an inline-code span is still OPEN — one
#       violation per offending line. That is the signature of a mis-anchored edit: a
#       `str.replace` whose anchor was a SUBSTRING of a longer string already in the file
#       spliced a whole section into the middle of a sentence, and every other check returned
#       clean on it. The edit-side rule: assert anchor uniqueness before any replace.
#     Cannot see: a splice that lands outside a code span, or one whose fragments happen to
#       leave backtick parity even. Its false positive is the mirror image: ONE stray unpaired
#       backtick in prose opens a span that never closes, and every later heading and table row
#       is then reported. Read a long run of splice findings as "find the stray backtick above
#       the first one", never as that many separate defects.
#
#   alt-record
#     Reads: the Plan unit table's `agent` column, and the Run record's `Alt lane:` line, the
#       first line under `Run record` whose text starts with `Alt lane:` (after optional `-`
#       or `**`) plus any indented lines that continue it.
#     Fires: a Plan row's agent cell names `verifier-alt` or `refuter-alt` while the Run
#       record has no `Alt lane:` line, or that line never names the seat. Or the line has fewer
#       complete entries for a seat than the Plan has rows for it. An entry runs from a seat's
#       name to the next seat name. It is complete when `model=`, `effort=`, `outcome=` and
#       `spend=` each carry a value. A codex seat is invisible to `sage-watch.sh`, so this line
#       is the only place its effort and contribution land. Silent while the Run record's first
#       `OUTCOME:` line is exactly `OUTCOME: pending — written at Step 6`: the record is written
#       at Step 6. The same words anywhere else do not count.
#     Cannot see: whether the figures were copied from the receipt or invented, or whether the
#       line names any contribution at all, or a true one. It checks that the line exists and
#       carries the fields.
#
#   secret-shape
#     Reads: every line of the ledger outside a fenced (```) code block — $SANITIZED, the same
#       fence-blanked text every check above reads.
#     Fires: one line per match of one of SIX fixed credential shapes — an AWS access key id
#       (`AKIA` and sixteen upper-case-or-digit characters), a PEM private key header
#       (`-----BEGIN ... PRIVATE KEY-----`), a GitHub token (`ghp_` and thirty-six), a Slack
#       token (`xox[baprs]-` and ten or more), a `Bearer` token (twenty or more) and an
#       OpenAI-style key (`sk-` and twenty or more).
#     The message NEVER echoes the match. It names the shape and the FIRST FOUR characters,
#       and that is deliberate: this line is written into the run record and into
#       notifications, so copying the secret into either would widen the very leak the check
#       exists to catch. A hit at Step 6 is a surfaced event like any other lint line
#       (`../references/record.md`).
#     Engine: awk, one program shared with the corpus arm below. `grep -E` would give brace
#       intervals (`{16}`) on both GNU and BSD grep, and awk gives none on mawk or BSD awk, so
#       the shapes are BUILT by repeating a character class instead — one engine, one fence
#       convention, one copy of the six shapes, and the file's interval-free rule kept.
#     Cannot see: anything but these six formats. No generic high-entropy detection, no other
#       vendor's spelling, nothing inside a fence, and nothing split across two lines.
#
# ---------------------------------------------------------------------------
# CORPUS MODE (`--corpus <dir>`) — a SECOND, INDEPENDENT mode, not an eleventh ledger check.
# It never reads a ledger and the ten checks above never run in it. `corpus-citation` exists
# because the live corpus cited a document that was deleted, sage-plan-integrity-round3.md, and
# nothing caught it for weeks — the citation just sat there, dead. `corpus-figure` and
# `cortex-budget` exist because `/sage-promote`'s own text names two rules nothing ever checked:
# no count, date or absolute cost in skill text, and the cortex's own size never bounded at all.
#
#   corpus-citation
#     Reads: `<dir>/SKILL.md`, every `<dir>/references/*.md`, every `<dir>/bin/*.sh`, and the
#       sage agent files (found as described below) — each OUTSIDE its own fenced (```)
#       code blocks — the same fence-blanking convention the ledger's "is a ledger" test uses
#       above, reused rather than re-written, so a path quoted inside a fence as an example is
#       never treated as a citation. `bin/*.sh` was added because a script header can cite a
#       corpus file that does not exist, and until this arm existed nothing resolved those
#       citations.
#     Finding the agent files: the first of these that exists —
#       `$SAGE_AGENT_DIR`, then `<dir>/../claude-agents`, then `~/.claude/agents` — supplies
#       the directory, and ONLY these six basenames are read from it:
#       explorer.md, implementer.md, implementer-frontier.md, verifier.md, verifier-standard.md,
#       web-researcher.md.
#       The codex seat files `<dir>/codex/*.md` are read too, resolved corpus-relative like the
#       agent files; no such directory → none read.
#       `~/.claude/agents/` is the user's own directory and holds agents unrelated to this
#       corpus, so nothing else there is read. No directory found in that order → scan none of
#       all of them and stay silent, the same FAIL-QUIET spirit as a missing `references/`.
#     What counts as a citation: a backtick-wrapped span whose entire content is a `.md` path
#       — letters, digits, `.`, `_`, `-`, `/` — immediately followed by nothing but the
#       closing backtick. Resolved relative to the CITING FILE'S OWN DIRECTORY for `SKILL.md`
#       and every `references/*.md` file: a `../`-style relative citation (`../memory/local.md`,
#       seen from `references/`) and a bare sibling citation (harness.md, seen from another
#       file in `references/`) both resolve this way, and those are the shapes the corpus uses.
#       There is deliberately NO corpus-root fallback for these files. One existed, so that a
#       file inside `references/` could cite `references/harness.md` root-relative; it masked
#       exactly the defect this check was built for, a citation that does not resolve from
#       where it is written, and the corpus's three such sites were fixed rather than excused.
#     A `bin/*.sh` file tries its own directory first, same as above — most of its citations
#       are `../`-prefixed (`../SKILL.md`, `../references/dispatch.md`) and resolve that way —
#       then, only on failure, tries CORPUS-RELATIVE TO `<dir>` as well: a bare corpus-relative
#       spelling (`SKILL.md`, `references/harness.md`) is also a real citation, not a dangling
#       one, and a script header is written to be read on its own, without the `../` a reader
#       would need to supply mentally.
#     An agent file's citations resolve CORPUS-RELATIVE TO `<dir>` ONLY, never relative to its
#       own directory. It installs to `~/.claude/agents/`, carries no `references/` of its own,
#       and every sage path it names — `SKILL.md`, `references/harness.md`, memory/shared/... —
#       is a sage-corpus path, written as if read from inside `<dir>`, not from beside the
#       agent file itself. Resolving it any other way would flag every one of those citations
#       as dangling by construction.
#     Memory citations, in two halves — the split is narrower than the directory on purpose:
#       OUT OF SCOPE, never checked: the genuinely PER-MACHINE files — the journal
#         (journal.md, memory/journal.md, .../memory/journal.md), the local KI files
#         (harness-stamp.md, and any `local/<file>.md` / `.../local/<file>.md` spelling),
#         and the v2 names (local.md, local-*.md, path-qualified or bare). They are
#         seeded or written on each machine and are deliberately absent from the repo
#         (harness.md: "excluded from the synced tree"), so no existence test can be honest
#         about them, and checking them would turn "not seeded yet" into a false alarm.
#       IN SCOPE, resolved BY BASENAME under `<dir>/memory/`, `<dir>/memory/shared/` and
#         `<dir>/memory/archive/`: everything else the corpus calls by a memory name — a
#         portable KI (`shared/<slug>.md`, `../memory/shared/<slug>.md`, or repo-rooted), an
#         archived file (`memory/archive/<file>.md`), and the retired v2 spellings
#         (shared.md, shared-*.md), which now correctly flag as dangling. Those files are
#         real and checked in, so a dangling citation is a real defect and is reported. Only
#         the basename is common to the spellings, so the basename is what resolves, in any
#         of the three directories a checked-in memory file can legally live in.
#     Fires: a citation's resolved path does not exist (and it is not out of scope, above) —
#       one violation per citation SITE, so the same dangling filename cited three times (as
#       it is, live, for sage-plan-integrity-round3.md) is three violation lines, not one
#       collapsed line, because each site is a separate promise that broke.
#     Cannot see (stated plainly, the same convention as the ten checks above):
#       - a path cited inside a fenced code block as an example — deliberately not a citation;
#       - a path built by string interpolation or otherwise assembled at read time, since this
#         is a text scan of the literal backtick span, never an interpreter;
#       - a citation to a document that EXISTS but whose content moved out from under it — the
#         check resolves a path, it does not read what is at the far end;
#       - a genuinely dangling citation to a PER-MACHINE memory file (journal.md,
#         harness-stamp.md, a `local/` KI, or the v2 names local.md / local-archive.md),
#         or a bare mention shaped like one that is not actually about that directory —
#         silence, not a violation, and the whole remaining cost of the out-of-scope trade
#         directly above; a caller who suspects one exists checks those files by hand. The
#         portable KIs under `memory/shared/` are not in this blind spot;
#       - a `~`-rooted span (`~/.claude/CLAUDE.md`) — it names a path outside this corpus
#         entirely (the user's global config, an installed file, never a file this corpus
#         ships), so it is skipped, not resolved and not flagged;
#       - any agent basename other than the five named above, or any file under a `bin/`,
#         `references/` or agent directory this dir-discovery order never reaches — a
#         second sage install with `SAGE_AGENT_DIR` unset and no `<dir>/../claude-agents`
#         reads `~/.claude/agents` and nothing else, silently, per FAIL QUIET.
#
#   corpus-figure
#     Why: `/sage-promote`'s stage two step 2 forbids a confirmation count, a date, or an
#       absolute cost in skill text — ratios and bands may stand, nothing else. Nothing checked
#       that rule until now; a prior audit found violations the exception list below has to
#       carry, and a wrong exception list would either miss real ones or drown the caller in
#       protected figures re-reported forever.
#     Reads: `<dir>/SKILL.md` and every `<dir>/references/*.md` **except `../references/harness.md`
#       and `../references/harness-measurements.md`**
#       — outside fenced code blocks, same fence convention as `corpus-citation`. `bin/*.sh` and
#       the agent files are OUT OF SCOPE, on purpose, for the same reason `corpus-citation`
#       gave `bin/` a pass: a script header legitimately carries the measurement it documents.
#       `../references/harness-measurements.md` is excluded the same way and for the same reason,
#       not a narrower one: it is the corpus's own declared destination for exactly this data, and
#       `../references/harness.md` keeps the two verification dates a run reads as its docs-drift trigger —
#       "harness facts go to harness.md with their measurement, date and population" is
#       `../SKILL.md`'s own instruction, restated at half a dozen citation sites — so treating
#       its normal contents as
#       violations would flag the file for doing its one job. No other `references/*.md` file
#       carries that declared role, so no other file is excluded.
#     Finds three shapes, each a plain pattern over the unfenced text:
#       - a bare date: `\b20[0-9]{2}-[0-9]{2}-[0-9]{2}\b`;
#       - a `k`-scaled absolute cost: `\b[0-9]+(\.[0-9]+)?k\b` — deliberately misses a
#         comma-grouped raw count (`466,802`) and a plain unscaled integer; both are real
#         absolute costs and both are outside what this pattern can see (see Cannot see, below);
#       - a population phrase: digit(s) immediately before one of
#         `times|runs|dispatches|confirmations|rounds|lenses|instances|cases|sessions|attempts|
#         findings|tests|machines|files|minutes`, or `<digits>%` immediately followed by
#         `of the`/`of a`/`of an` — a population statistic, not a threshold. A percentage alone,
#         with no `of the`/`of a`/`of an` after it, is never flagged: that is what keeps a
#         multiplier or a bare percentage threshold (`30%` on its own) out of this pattern's
#         reach; only `30% of the window` shapes trip it, and `30%` itself is on the exception
#         list below regardless.
#     The exception list — data, not scattered special cases, and named so its source can be
#       re-derived: the thirteen protected figures (`P-01`..`P-13`) ruled by the provenance lens
#       in the repo's .claude/plans/sage-48627a15-lens-2.md, "## Protected — exception applies or
#       the floor protects; leave in place" — every ratio, band, and anti-band that section clears.
#       None of those needs a literal entry here, because a bare ratio (`~4×`, `1.6–1.7×`) never
#       matches any of the three shapes above — no digit-`k`, no date, no population noun. The
#       entries that DO need one are the `k`-scaled and population-phrase shapes the lens
#       protects anyway: `150k`/`500k` (the budget rail's own floors), `296k` (the anti-band
#       observation "one point under the threshold... during a run actually at 11%"), `1–2k`
#       (the report-size bound the brief contract computes with, both hyphens the corpus uses),
#       and `max(5% of the compaction point, 30k)` (the checkpoint rung's margin, a computed
#       predicate, never a population statistic). A hit is suppressed when the LINE containing it contains one of these
#       substrings verbatim — a line match, not a token match, because the surrounding words are
#       what make a figure a threshold rather than a statistic, and a token-only match would
#       suppress a genuine `296k` appearing in an unrelated, unprotected sentence.
#     Fires: one violation per matched figure that survives the exception check, `<check-id>`
#       `corpus-figure`, one line per hit.
#     Cannot see: a comma-grouped raw count (`466,802`), a plain unscaled integer used as a
#       cost or a count, a spelled-out number ("twenty-eight runs"), or a population phrase
#       whose noun is not on the list above — all silence, the same miss-over-false-alarm trade
#       the ten ledger checks make throughout this file. It also cannot tell a genuine
#       citation-by-date (naming a specific dated design note) from a bare measurement date;
#       both shapes read identically to a line scan, and only the exception list or a human
#       tells them apart.
#
#   cortex-budget
#     Why: the only one of the five `/sage-promote` growth-control rules that BOUNDS growth
#       rather than detecting one instance of it — the repo's 2026-08-28-sage-cortex-extraction.md
#       §8, closing paragraph. `../SKILL.md` has never once shrunk in the history this repo can measure.
#     Reads: `<dir>/SKILL.md`'s `## Defaults` section, outside fenced code blocks (same fence
#       convention `corpus-figure` uses immediately above, reused rather than re-written), for
#       TWO rows — `Cortex word budget | <N> words` and `Run-loaded word budget | <N> words`,
#       each `<N>` a bare positive integer (commas allowed, e.g. `12,500`). **No such row →
#       silent, always**, per row and independently — the same fail-quiet spirit
#       `corpus-citation` and the ten ledger checks already carry: an undeclared budget is not
#       a violation, it is a knob nobody has turned yet. One check id covers both rows: they
#       bound the same thing, what a run has to read, at two radii.
#     The cortex row bounds `wc -w <dir>/SKILL.md` alone — the router a run always loads.
#     The run-loaded row bounds the whole set a run actually reads, computed as: SKILL.md's
#       own words; plus every distinct `references/<name>.md` cited in a backtick span inside
#       a `## Step <1-6>` section (heading to the next `## `, fenced lines excluded), whole;
#       plus, for every `bin/<name>.sh` cited the same way, only its RUN BLOCK — line 1
#       through the first `# END RUN BLOCK`, which is all a run is told to read. A script with
#       no marker counts entire, deliberately: a missing marker then shows as a loud total
#       instead of as silence. A cited file that does not exist counts zero, because
#       `corpus-citation` already reports it and two lines about one defect say nothing new.
#     A file no step section names is OUTSIDE this total even when the corpus ships it and
#       `## References` lists it — `references/authoring.md`,
#       `references/harness-measurements.md`, `bin/sage-watch.sh` are the live examples. A run never loads them; a maintainer
#       and `/sage-promote` do, and the budget bounds runs.
#     Fires: at most once per row — `<check-id>` `cortex-budget` both times, the cortex line
#       naming the measured word count and the declared budget, the run-loaded line naming the
#       total, the budget, and every file counted with its own figure.
#     Cannot see: a budget declared in the wrong table, spelled with a different label, or a
#       negative or zero figure (any of those read as "no budget declared" and stay silent,
#       never crash and never misreport a huge violation on a typo) — a caller who suspects a
#       silent budget checks `## Defaults` by hand. Nor can it see a file a step section names
#       in prose rather than in a backtick span, or one a reference file itself pulls in: this
#       is a one-hop scan of SKILL.md's own step sections, never a transitive closure, so a
#       real run that follows a citation out of a step file reads more than this total says.
#
#   secret-shape (the ledger check's six shapes, over the memory corpus)
#     Why here: a knowledge item is committed to a repository, and the leak that matters in a
#       repository is a credential, a private path, or a user's identity.
#     Reads: every `.md` file under `<dir>/memory/` — `journal.md`, and every file one
#       directory down (`shared/`, `local/`, `local-seed/`, `archive/`) — and every `.log`
#       file at those two depths (`runs.log`, `inbox.log`), outside fences.
#     Fires: exactly as the ledger check above, with the memory file's path, and with the same
#       four-character message that never echoes the match.
#     Cannot see: a file more than one directory below `memory/` (the shipped layout has
#       none), plus everything the ledger check cannot see.
#
#   shared-leak
#     Reads: `<dir>/memory/shared/*.md` — the portable template that ships to every
#       machine — and <dir>/memory/lessons.md, outside fences. On lessons.md it flags
#       absolute paths and 36-character UUIDs only: that file carries cost bands and run ids
#       by design, so `k`-scaled costs and `run <8hex>` ids are not read there. `local/`, `local-seed/` and the journal are per-machine BY
#       DESIGN, so a machine-local fact is correct there and reading them would report every
#       file for doing its job.
#     Fires: one line per hit, three shapes — an absolute path (a token opening `/Users/`,
#       `/home/`, `/root/`, `/mnt/`, `/tmp/`, `/private/`, or a `C:\` drive prefix); a session
#       id (a 36-character hex UUID, or a bare 8-hex token immediately after `run ` or
#       `session `, kept that narrow because eight hex characters alone are also a commit sha
#       and a hundred ordinary words); and a `k`-suffixed absolute cost, `corpus-figure`'s own
#       cost pattern reused rather than re-written.
#     The message DOES echo the token, to 24 characters: a path or a session id is not a
#       secret, and naming it is what makes the line editable. `secret-shape` above is the
#       opposite case and says so in its own entry.
#     Not part of `corpus-figure`: that check rules SKILL.md and references/, this one rules
#       the shared memory template, and one id per scope keeps either one suppressible alone.
#     Cannot see: a relative path, a hostname, or a user name written as a plain word — all
#       machine-local, none with a shape to key on, all silence per FAIL QUIET.
#
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
    'sage-lint.sh --corpus <dir>      check a sage skill dir'"'"'s own .md citations, dated/' \
    '                                  absolute figures, its two word budgets, and credential and' \
    '                                  machine-local shapes in its memory, across SKILL.md,' \
    '                                  references/, bin/*.sh, memory/, and the sage' \
    '                                  agent files (separate mode)' \
    'sage-lint.sh --help              this reminder' \
    '' \
    'Exit 0 clean OR a required tool is missing and nothing was checked (stderr says' \
    '       which), 1 dirty, 2 usage error, 3 path unreadable/dir/not-a-ledger/old-format' \
    '       ledger (or, in --corpus mode, dir unreadable/not-a-dir/no SKILL.md).' \
    'The ledger schema is four sections: Plan, Resume state, Decisions, Findings, Run record.' \
    'Output: sage-lint <check-id> <path>:<line> <message>' \
    'Checks: state-enum triage-orphan triage-state findings-shape disclosure-home' \
    '        sections frame splice secret-shape alt-record  (ledger mode, all ten)' \
    '        corpus-citation corpus-figure cortex-budget secret-shape shared-leak' \
    '                                                     (--corpus mode, its five checks)'
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
# secret-shape's one awk program, shared by the ledger check and the corpus memory scan (see
# THE CHECKS and CORPUS MODE above). The six shapes are BUILT in BEGIN by repeating a
# character class instead of written with a `{n}` interval, because mawk and BSD awk have no
# brace intervals -- the same interval-free rule the rest of this file runs under. Fence
# blanking is done here too, so ledger mode can feed it the already-blanked $SANITIZED and
# corpus mode can feed it a raw file, with one copy of the shapes between them.
AWK_SECRET='
  function rep(cls, n,   s, i) { s = ""; for (i = 0; i < n; i++) s = s cls; return s }
  function shape(nm, pat) { ns++; sname[ns] = nm; spat[ns] = pat }
  BEGIN {
    ns = 0
    shape("aws access key id", "AKIA" rep("[0-9A-Z]", 16))
    shape("pem private key", "-----BEGIN [A-Z ]*PRIVATE KEY-----")
    shape("github token", "ghp_" rep("[A-Za-z0-9]", 36))
    shape("slack token", "xox[baprs]-" rep("[A-Za-z0-9-]", 10) "[A-Za-z0-9-]*")
    shape("bearer token", "Bearer " rep("[A-Za-z0-9._-]", 20) "[A-Za-z0-9._-]*")
    shape("openai key", "sk-" rep("[A-Za-z0-9]", 20) "[A-Za-z0-9]*")
  }
  {
    t = $0
    sub(/^[ \t]+/, "", t)
    if (t ~ /^```/) { infence = !infence; next }
    if (infence) next
    for (i = 1; i <= ns; i++) {
      rest = $0
      while (match(rest, spat[i])) {
        start = RSTART
        len = RLENGTH
        # The first four characters and nothing more: this line is written into the ledger
        # and into notifications, so echoing the match would widen the leak it reports.
        printf "sage-lint secret-shape %s:%d carries a credential-shaped string (%s, starts '"'"'%s'"'"')\n", \
          FILE, NR, sname[i], substr(rest, start, 4)
        rest = substr(rest, start + len)
      }
    }
  }
'

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

  # SKILL.md plus every references/*.md sibling seed the corpus; bin/*.sh and the four agent
  # files join below. No references/ dir is not an error — SKILL.md alone still gets checked
  # (fail quiet, same spirit as the ledger side).
  CORPUS_FILES="$SKILL_FILE"
  if [ -d "$CORPUS_DIR/references" ]; then
    for _rf in "$CORPUS_DIR"/references/*.md; do
      [ -e "$_rf" ] && CORPUS_FILES="$CORPUS_FILES
$_rf"
    done
  fi

  # bin/*.sh joins the corpus: a script header can cite a corpus file that does not exist.
  # No bin/ dir is not an error, same fail-quiet spirit as a missing references/.
  if [ -d "$CORPUS_DIR/bin" ]; then
    for _bf in "$CORPUS_DIR"/bin/*.sh; do
      [ -e "$_bf" ] && CORPUS_FILES="$CORPUS_FILES
$_bf"
    done
  fi

  # The four sage agent files join too. Directory discovery, first that exists:
  # $SAGE_AGENT_DIR, then <dir>/../claude-agents, then ~/.claude/agents. Only the four
  # basenames below are read from it — ~/.claude/agents/ is the user's own directory and
  # holds agents unrelated to this corpus. No directory found in that order → scan none of
  # the four, silently (see CORPUS MODE, header above).
  AGENT_DIR=""
  for _cand in "${SAGE_AGENT_DIR-}" "$CORPUS_DIR/../claude-agents" "$HOME/.claude/agents"; do
    if [ -n "$_cand" ] && [ -d "$_cand" ]; then
      AGENT_DIR="$_cand"
      break
    fi
  done
  if [ -n "$AGENT_DIR" ]; then
    for _an in explorer implementer implementer-frontier verifier verifier-standard web-researcher; do
      _af="$AGENT_DIR/$_an.md"
      [ -e "$_af" ] && CORPUS_FILES="$CORPUS_FILES
$_af"
    done
  fi

  # The codex seat files are system prompts for a unit, corpus-relative like the agent files.
  ALT_DIR="$CORPUS_DIR/codex"
  if [ -d "$ALT_DIR" ]; then
    for _tf in "$ALT_DIR"/*.md; do
      [ -e "$_tf" ] && CORPUS_FILES="$CORPUS_FILES
$_tf"
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
    # The four agent files resolve corpus-relative to <dir>, never to their own directory
    # (see CORPUS MODE, header above, "The one exception, and why"): an agent file carries no
    # references/ of its own, and every sage path it names is a sage-corpus path.
    if [ -n "$AGENT_DIR" ] && [ "$CDIR" = "$AGENT_DIR" ]; then
      CDIR="$CORPUS_DIR"
    fi
    if [ "$CDIR" = "$ALT_DIR" ]; then
      CDIR="$CORPUS_DIR"
    fi
    # A bin/*.sh file additionally resolves corpus-relative to <dir> (see the fallback below):
    # unlike the four agent files, a script under bin/ already cites most corpus paths
    # `../`-prefixed and those keep resolving from the script's own directory; this flag only
    # widens resolution for the bare corpus-relative spelling.
    case "$CFILE" in
      "$CORPUS_DIR"/bin/*) CBIN=1 ;;
      *) CBIN="" ;;
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

      # OUT OF SCOPE, never checked: the genuinely PER-MACHINE memory files. The journal, the
      # local KI files (harness-stamp.md and everything else under memory/local/), and the v2
      # names local.md / local-* are seeded or written on each machine and are deliberately
      # absent from the repo (harness.md: "excluded from the synced tree"), so no existence
      # test can be honest about them and checking them would turn "not seeded yet" into a
      # false alarm. This exclusion names the per-machine FILES, not the `memory/` directory --
      # narrower than it used to be, and narrower on purpose. See CORPUS MODE, header above.
      case "$CTOK" in
        local.md|local-*.md|memory/local.md|memory/local-*.md|*/memory/local.md|*/memory/local-*.md)
          continue ;;
        journal.md|memory/journal.md|*/memory/journal.md|harness-stamp.md|local/*.md|*/local/*.md)
          continue ;;
      esac

      # IN SCOPE, resolved BY BASENAME under `<dir>/memory/`, `<dir>/memory/shared/` and
      # `<dir>/memory/archive/`: everything else the corpus calls by a memory name. A
      # portable KI under memory/shared/ and an archived file are real checked-in files, so
      # a dangling citation to either is a real defect and must be reported. The corpus
      # spells such paths several ways -- corpus-relative (`../memory/shared/<slug>.md`),
      # bare (`shared/<slug>.md`) and repo-rooted -- and only the basename is common to all
      # of them, so the basename is what resolves, in any of the three directories a
      # checked-in memory file can legally live in.
      case "$CTOK" in
        */memory/*|memory/*|shared.md|shared-*.md|shared/*.md|*/shared/*.md|archive/*.md|*/archive/*.md)
          if [ -e "$CORPUS_DIR/memory/${CTOK##*/}" ] \
            || [ -e "$CORPUS_DIR/memory/shared/${CTOK##*/}" ] \
            || [ -e "$CORPUS_DIR/memory/archive/${CTOK##*/}" ]; then
            continue
          fi
          add "sage-lint corpus-citation $CFILE:$CLINE cites '$CTOK' which does not resolve to a file"
          continue ;;
      esac

      # Everything else resolves relative to the CITING FILE'S OWN DIRECTORY. There is
      # deliberately no corpus-root fallback for SKILL.md and references/*.md: one existed, so
      # a file inside `references/` could cite references/harness.md root-relative, and it
      # MASKED exactly the defect this check was built for -- a citation that does not resolve
      # from where it is written. The corpus's three such sites were fixed rather than excused.
      if [ -e "$CDIR/$CTOK" ]; then
        continue
      fi
      # A bin/*.sh file gets one more try, corpus-relative to <dir>: a script header cites most
      # corpus paths `../`-prefixed (resolved above), but a bare corpus-relative spelling
      # (`SKILL.md`, `references/harness.md`) is also a real citation, not a dangling one.
      if [ -n "$CBIN" ] && [ -e "$CORPUS_DIR/$CTOK" ]; then
        continue
      fi
      add "sage-lint corpus-citation $CFILE:$CLINE cites '$CTOK' which does not resolve to a file"
    done <<EOF
$CANDIDATES
EOF
  done <<EOF
$CORPUS_FILES
EOF

  # ---------------------------------------------------------------------------
  # corpus-figure — see CORPUS MODE, header above, for what it reads, the three shapes it
  # matches, and why the exception list holds exactly these entries. `bin/*.sh`, the agent
  # files, ../references/harness.md and ../references/harness-measurements.md are never in FIGURE_FILES: excluded above `CORPUS_FILES`
  # is built for `corpus-citation`, this list is built separately and on purpose.
  FIGURE_FILES="$SKILL_FILE"
  if [ -d "$CORPUS_DIR/references" ]; then
    for _rf in "$CORPUS_DIR"/references/*.md; do
      [ -e "$_rf" ] || continue
      # harness.md is the run sheet of harness rules; harness-measurements.md is the declared
      # home of every dated figure behind it. Both carry figures by design (header above).
      case "$(basename "$_rf")" in harness.md|harness-measurements.md) continue ;; esac
      FIGURE_FILES="$FIGURE_FILES
$_rf"
    done
  fi

  # The exception list, as data: the thirteen protected figures P-01..P-13, ruled by the
  # provenance lens at the repo's .claude/plans/sage-48627a15-lens-2.md, "## Protected —
  # exception applies or the floor protects; leave in place". Only the entries that can actually collide
  # with one of the three shapes above are listed (see CORPUS MODE, header above, for why a
  # bare ratio never needs one). A hit is suppressed when its own LINE contains one of these
  # substrings verbatim.
  # Pipe-separated, not newline-separated: the BSD awk on macOS rejects a literal newline
  # inside a -v value outright ("newline in string"), so a newline-joined list here would
  # silently break this whole check under 2>/dev/null -- exactly the false-clean failure
  # FAIL QUIET exists to prevent, not produce. None of these entries contains a `|`.
  #
  # Four entries below are not from the lens (SKILL.md-only) but ruled the same way, by hand,
  # against `../references/memory.md`'s own text, the first time this check ever ran over
  # references/*.md: a citation to a specific dated design note (naming which revision, not
  # duplicating a measurement), and three illustrative worked-example strings the corpus
  # quotes to show a FORMAT rather than assert a fact about this machine — the same shape
  # `../references/dispatch.md`'s own worked ledger table uses, fenced off there and quoted
  # in-line here. A real per-machine measurement narrated as evidence for a rule (the
  # memory contract's "uses: 0" case) is the load-bearing anecdote itself, shape 1
  # in the lens's own vocabulary — the rule is unrecognisable without the concrete case, the
  # same reasoning that protects P-08's `296k`/`29%` anti-band anecdote.
  FIGURE_EXCEPTIONS='150k|500k|296k|1–2k|max(5% of the compaction point, 30k)|200k and a 1M|sage-memory-v3 note, cross-machine half revised|≤10k words|including rules at counts of 24, 13 and 12|fetch-heavy research runs 70'

  while IFS= read -r FFILE; do
    [ -n "$FFILE" ] || continue
    CHK=$(awk -v FILE="$FFILE" -v exc="$FIGURE_EXCEPTIONS" '
      BEGIN {
        n = split(exc, ex, "|")
      }
      function excepted(line,   i) {
        for (i = 1; i <= n; i++) if (ex[i] != "" && index(line, ex[i]) > 0) return 1
        return 0
      }
      {
        t = $0
        sub(/^[ \t]+/, "", t)
        if (t ~ /^```/) { infence = !infence; next }
        if (infence) next
        line = $0
        if (excepted(line)) next

        rest = line
        while (match(rest, /(^|[^0-9])20[0-9][0-9]-[0-9][0-9]-[0-9][0-9]([^0-9]|$)/)) {
          seg = substr(rest, RSTART, RLENGTH)
          gsub(/[^0-9-]/, "", seg)
          printf "date\t%d\t%s\n", NR, seg
          rest = substr(rest, RSTART + RLENGTH)
        }

        rest = line
        while (match(rest, /(^|[^0-9.])[0-9]+(\.[0-9]+)?k([^A-Za-z0-9]|$)/)) {
          seg = substr(rest, RSTART, RLENGTH)
          gsub(/[^0-9.k]/, "", seg)
          printf "cost\t%d\t%s\n", NR, seg
          rest = substr(rest, RSTART + RLENGTH)
        }

        rest = line
        while (match(rest, /[0-9]+ (times|runs|dispatches|confirmations|rounds|lenses|instances|cases|sessions|attempts|findings|tests|machines|files|minutes)([^A-Za-z]|$)/)) {
          seg = substr(rest, RSTART, RLENGTH)
          printf "population\t%d\t%s\n", NR, seg
          rest = substr(rest, RSTART + RLENGTH)
        }

        rest = line
        while (match(rest, /[0-9]+(\.[0-9]+)?% +of +(the|a|an) /)) {
          seg = substr(rest, RSTART, RLENGTH)
          printf "population\t%d\t%s\n", NR, seg
          rest = substr(rest, RSTART + RLENGTH)
        }
      }
    ' "$FFILE" 2>/dev/null)

    [ -n "$CHK" ] || continue
    while IFS="$(printf '\t')" read -r FKIND FLINE FSEG; do
      [ -n "$FKIND" ] || continue
      case "$FKIND" in
        date) FMSG="carries a bare date '$FSEG'" ;;
        cost) FMSG="carries an absolute cost '$FSEG'" ;;
        population) FMSG="carries a population phrase '$FSEG'" ;;
        *) FMSG="carries a figure '$FSEG'" ;;
      esac
      add "sage-lint corpus-figure $FFILE:$FLINE $FMSG"
    done <<EOF
$CHK
EOF
  done <<EOF
$FIGURE_FILES
EOF

  # ---------------------------------------------------------------------------
  # cortex-budget — two declared budgets, one check id. See CORPUS MODE, header above, for
  # what each row bounds and what neither can see.

  # declared_budget <label> — the bare positive integer that `| <label> | <N> words` declares
  # in SKILL.md's `## Defaults` section, or nothing at all. Commas are stripped (`12,500`).
  # Outside fenced code blocks, same fence convention `corpus-figure` uses above, so a budget
  # row quoted as an example (fenced, or under another heading) is never read as the real one.
  # No row, or a figure that is not a positive integer, prints nothing and the caller stays
  # silent: an undeclared budget is a knob nobody has turned yet, not a violation.
  declared_budget() {  # declared_budget <row-label>
    awk -v label="$1" '
      {
        t = $0
        sub(/^[ \t]+/, "", t)
        if (t ~ /^```/) { infence = !infence; next }
        if (infence) next
        if (t ~ /^## /) { indefaults = (t ~ /^## Defaults[ \t]*$/); next }
        if (!indefaults) next
        if (t ~ ("^\\| *" label " *\\|")) {
          split(t, cell, "|")
          v = cell[3]
          gsub(/,/, "", v)
          sub(/^[ \t]+/, "", v)
          if (match(v, /^[1-9][0-9]*/)) print substr(v, 1, RLENGTH)
          exit
        }
      }
    ' "$SKILL_FILE" 2>/dev/null
  }

  # run_loaded_files — every distinct `references/<name>.md` and `bin/<name>.sh` that a
  # `## Step N` section of SKILL.md cites inside a backtick span, in citation order. A step
  # section runs from its `## Step <1-6>` heading to the next `## ` heading; fenced lines
  # never count. The token is matched INSIDE the span rather than as the whole span, unlike
  # `corpus-citation`'s whole-span rule: Step 4 names a script inside a command span
  # (`sed -n '1,/^# END RUN BLOCK/p' .../sage-watch.sh`), a run loads that run block, and a
  # whole-span test would leave it out of the total. Paths resolve corpus-relative to <dir>,
  # so the same script named by its installed `~/.claude/skills/sage/` path still resolves.
  run_loaded_files() {
    awk '
      {
        t = $0
        sub(/^[ \t]+/, "", t)
        if (t ~ /^```/) { infence = !infence; next }
        if (infence) next
        if (t ~ /^## /) { instep = (t ~ /^## Step [1-6]/); next }
        if (!instep) next
        line = $0
        while (match(line, /`[^`]*`/)) {
          spanstart = RSTART
          spanlen = RLENGTH
          span = substr(line, spanstart + 1, spanlen - 2)
          rest = span
          while (match(rest, /references\/[A-Za-z0-9_.-]+\.md/)) {
            print substr(rest, RSTART, RLENGTH)
            rest = substr(rest, RSTART + RLENGTH)
          }
          rest = span
          while (match(rest, /bin\/[A-Za-z0-9_.-]+\.sh/)) {
            print substr(rest, RSTART, RLENGTH)
            rest = substr(rest, RSTART + RLENGTH)
          }
          line = substr(line, spanstart + spanlen)
        }
      }
    ' "$SKILL_FILE" 2>/dev/null | awk '!seen[$0]++'
  }

  # run_loaded_words <corpus-relative-path> — the words a run actually loads from this file:
  # a reference file whole, a script only through its `# END RUN BLOCK` marker. A script with
  # no marker counts entire, so a missing marker shows up as a loud total rather than as
  # silence. A cited file that does not exist counts zero — `corpus-citation` is what reports
  # that, and reporting it twice would say nothing new.
  run_loaded_words() {  # run_loaded_words <corpus-relative-path>
    if [ ! -e "$CORPUS_DIR/$1" ]; then
      printf '0'
      return 0
    fi
    case "$1" in
      *.sh) sed -n '1,/^# END RUN BLOCK/p' "$CORPUS_DIR/$1" 2>/dev/null | wc -w | tr -d ' ' ;;
      *) wc -w < "$CORPUS_DIR/$1" | tr -d ' ' ;;
    esac
  }

  SKILL_WORDS=$(wc -w < "$SKILL_FILE" | tr -d ' ')

  CORTEX_BUDGET=$(declared_budget "Cortex word budget")
  if [ -n "$CORTEX_BUDGET" ] && [ "$SKILL_WORDS" -gt "$CORTEX_BUDGET" ]; then
    add "sage-lint cortex-budget $SKILL_FILE:1 SKILL.md is $SKILL_WORDS words, over the ## Defaults budget of $CORTEX_BUDGET words"
  fi

  RUN_BUDGET=$(declared_budget "Run-loaded word budget")
  if [ -n "$RUN_BUDGET" ]; then
    RUN_TOTAL="$SKILL_WORDS"
    RUN_DETAIL="SKILL.md $SKILL_WORDS"
    while IFS= read -r RFILE; do
      [ -n "$RFILE" ] || continue
      RWORDS=$(run_loaded_words "$RFILE")
      RUN_TOTAL=$((RUN_TOTAL + RWORDS))
      RUN_DETAIL="$RUN_DETAIL, $RFILE $RWORDS"
    done <<EOF
$(run_loaded_files)
EOF
    if [ "$RUN_TOTAL" -gt "$RUN_BUDGET" ]; then
      add "sage-lint cortex-budget $SKILL_FILE:1 a run loads $RUN_TOTAL words, over the ## Defaults run-loaded budget of $RUN_BUDGET words: $RUN_DETAIL"
    fi
  fi

  # ---------------------------------------------------------------------------
  # secret-shape over the memory corpus, then shared-leak over the portable template only.
  # See CORPUS MODE, header above, for what each reads and what neither can see.

  for _mf in "$CORPUS_DIR"/memory/*.md "$CORPUS_DIR"/memory/*/*.md \
             "$CORPUS_DIR"/memory/*.log "$CORPUS_DIR"/memory/*/*.log; do
    [ -e "$_mf" ] || continue
    add "$(awk -v FILE="$_mf" "$AWK_SECRET" "$_mf" 2>/dev/null)"
  done

  # Every shape is built from a repeated character class, never a `{n}` interval, for the
  # reason AWK_SECRET states above: mawk and BSD awk have no brace intervals. The cost shape
  # is `corpus-figure`'s own, reused rather than re-written, so the two never drift apart.
  AWK_LEAK='
    function rep(cls, n,   s, i) { s = ""; for (i = 0; i < n; i++) s = s cls; return s }
    # A path or a session id is not a secret, so this message names the token that has to be
    # edited out -- unlike secret-shape, which never echoes its match.
    function report(kind, tok) {
      if (length(tok) > 24) tok = substr(tok, 1, 24)
      printf "sage-lint shared-leak %s:%d carries a machine-local %s ('"'"'%s'"'"')\n", FILE, NR, kind, tok
    }
    BEGIN {
      hex = "[0-9a-fA-F]"
      uuid_re = "(^|[^0-9A-Za-z-])" rep(hex, 8) "-" rep(hex, 4) "-" rep(hex, 4) "-" rep(hex, 4) "-" rep(hex, 12) "([^0-9A-Za-z-]|$)"
      runid_re = "(^|[^A-Za-z])(run|session) " rep(hex, 8) "([^0-9A-Za-z]|$)"
      unix_re = "(^|[^A-Za-z0-9_.~-])/(Users|home|root|mnt|tmp|private)/[^ \t`)\"]*"
      win_re = "(^|[^A-Za-z0-9])[A-Za-z]:\\\\[^ \t`)\"]*"
      cost_re = "(^|[^0-9.])[0-9]+(\\.[0-9]+)?k([^A-Za-z0-9]|$)"
    }
    {
      t = $0
      sub(/^[ \t]+/, "", t)
      if (t ~ /^```/) { infence = !infence; next }
      if (infence) next

      rest = $0
      while (match(rest, unix_re)) {
        start = RSTART
        len = RLENGTH
        seg = substr(rest, start, len)
        report("absolute path", substr(seg, index(seg, "/")))
        rest = substr(rest, start + len)
      }

      rest = $0
      while (match(rest, win_re)) {
        start = RSTART
        len = RLENGTH
        seg = substr(rest, start, len)
        match(seg, /[A-Za-z]:\\/)
        report("absolute path", substr(seg, RSTART))
        rest = substr(rest, start + len)
      }

      rest = $0
      while (match(rest, uuid_re)) {
        start = RSTART
        len = RLENGTH
        seg = substr(rest, start, len)
        sub(/^[^0-9A-Fa-f]+/, "", seg)
        sub(/[^0-9A-Fa-f-]+$/, "", seg)
        report("session id", seg)
        rest = substr(rest, start + len)
      }

      if (lessons) next

      rest = $0
      while (match(rest, runid_re)) {
        start = RSTART
        len = RLENGTH
        seg = substr(rest, start, len)
        match(seg, /(run|session) /)
        report("session id", substr(seg, RSTART + RLENGTH, 8))
        rest = substr(rest, start + len)
      }

      rest = $0
      while (match(rest, cost_re)) {
        start = RSTART
        len = RLENGTH
        seg = substr(rest, start, len)
        gsub(/[^0-9.k]/, "", seg)
        report("absolute cost", seg)
        rest = substr(rest, start + len)
      }
    }
  '

  for _sf in "$CORPUS_DIR"/memory/shared/*.md; do
    [ -e "$_sf" ] || continue
    add "$(awk -v FILE="$_sf" -v lessons=0 "$AWK_LEAK" "$_sf" 2>/dev/null)"
  done
  # lessons.md carries cost bands and run ids by design: paths and UUIDs only there.
  if [ -e "$CORPUS_DIR/memory/lessons.md" ]; then
    add "$(awk -v FILE="$CORPUS_DIR/memory/lessons.md" -v lessons=1 "$AWK_LEAK" "$CORPUS_DIR/memory/lessons.md" 2>/dev/null)"
  fi

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
  # split_cells: split a table row on `|`, but read `\|` as a literal pipe inside a cell.
  # Same contract as split(line, cells, "|"): cells[2]..cells[n-1] are the cells of the row.
  function split_cells(line, cells,   n, i) {
    gsub(/\\\|/, "\001", line)
    n = split(line, cells, "|")
    for (i = 1; i <= n; i++) gsub(/\001/, "|", cells[i])
    return n
  }
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

REQUIRED_SECTIONS='Plan,Resume state,Decisions,Findings,Run record'

# An old-format ledger is told apart first: it would otherwise pass the is-a-ledger test on its
# `# sage ledger` title and then be judged against a schema it never had.
IS_OLD_FORMAT=$(awk "$AWK_LIB"'
  NR == 1 && /sage occupancy duty/ { print "yes"; exit }
  {
    if (is_heading($0)) {
      h = heading_of($0)
      if (h == "Unit table" || h == "Findings and dispositions" || h == "Assumption log" || h == "Decisions and deviations") { print "yes"; exit }
    }
  }
' <<<"$SANITIZED")

if [ "$IS_OLD_FORMAT" = "yes" ]; then
  printf 'sage-lint: %s: an old-format ledger — this lint checks the four-section schema only (Plan, Resume state, Decisions, Findings, Run record)\n' "$FILE" >&2
  exit 3
fi

# Two independent marks of ledger-hood; either is enough (see "Is a ledger" above).
IS_LEDGER=$(awk -v req="$REQUIRED_SECTIONS" "$AWK_LIB"'
  BEGIN { n = split(req, want, ","); for (i = 1; i <= n; i++) ok[want[i]] = 1 }
  {
    line = $0
    if (tolower(line) ~ /^#[ \t]+sage ledger/) bytitle = 1
    if (is_heading(line)) {
      h = heading_of(line)
      if ((h in ok) && !(h in seen)) { seen[h] = 1; heads++ }
      next
    }
    if (line ~ /^\|/) rows++
  }
  END { if (bytitle || (heads >= 3 && rows >= 1)) print "yes" }
' <<<"$SANITIZED")

if [ "$IS_LEDGER" != "yes" ]; then
  printf 'sage-lint: %s: not a ledger — needs a "# sage ledger" title, or at least three of the five schema headings AND at least one table row\n' "$FILE" >&2
  exit 3
fi

OUT=""
add() {  # add <text-with-trailing-lines-or-empty>
  [ -n "$1" ] || return 0
  if [ -z "$OUT" ]; then OUT="$1"; else OUT="$OUT
$1"; fi
}

# ---------------------------------------------------------------------------
# state-enum

CHK=$(awk -v FILE="$FILE" "$AWK_LIB"'
  {
    line = $0
    if (is_heading(line)) {
      in_table = 0
      heading = heading_of(line)
      if (heading == "Plan" && unit_idx == 0) unit_idx = NR
      next
    }
    if (line ~ /^\|/) {
      if (!in_table) {
        in_table = 1
        expect_sep = 1
        is_unit = (unit_idx > 0 && captured == 0 && heading == "Plan")
        if (is_unit) {
          n = split_cells(line, cells)
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
          n = split_cells(line, cells)
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
      printf "sage-lint state-enum %s:%d Plan table has no column labelled '"'"'state'"'"'\n", FILE, header_line
    if (unit_idx > 0 && !header_seen)
      printf "sage-lint state-enum %s:%d Plan heading has no table under it\n", FILE, unit_idx
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
  # followed by a non-alphanumeric separator (`Plan (phase 2)`, `Run record — phase
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
    if (sec_match(h, "Decisions")) return "Decisions"
    if (sec_match(h, "Findings")) return "Findings"
    if (sec_match(h, "Run record")) return "Run record"
    if (sec_match(h, "Resume state")) return "Resume state"
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
      # Section identity is PREFIX-matched (`Plan (phase 2)`), and section extents are
      # NESTING-AWARE: a heading at a LOWER level than the current section is a subsection
      # and stays inside; one at the same or a higher level ends it. A sibling-level heading
      # (`### Fix log` beside `### Run record`) ends the context, which keeps a fix table
      # outside the exclusions and lets an untriaged id there fire.
      s = sec_of(h)
      if (s != "") {
        section = s; seclevel = heading_level(line)
        if (s == "Findings") find_exact = (h == s)
      } else if (section != "" && heading_level(line) > seclevel) {
        ; # a subsection: the enclosing prescribed section still governs
      } else {
        section = ""; seclevel = 0
      }
      if (section == "Findings" && find_exact && find_idx == 0) find_idx = NR
      next
    }
    # Plan, Resume state and Decisions each carry their own id namespace (unit ids, a resume
    # checkpoint, `D1`) and the Findings section supplies the triage set, so none of the four
    # is a source of finding-id candidates. Exclusion is by prescribed SECTION only; a table
    # header label such as `id` excludes nothing. Candidates come from tables OUTSIDE every
    # prescribed section, plus the Run record (its tables and its `Findings:` prose line).
    # A table carrying a column labelled `triage` or `disposition` records its own
    # dispositions in place and is not a candidate source. Known non-finding ids (Plan-table
    # ids, `D<n>` ids) are subtracted in END rather than never harvested.
    candidate_ok = (section == "" || section == "Run record")
    if (line ~ /^\|/) {
      if (!in_table) {
        in_table = 1
        expect_sep = 1
        is_find = (find_idx > 0 && find_captured == 0 && section == "Findings" && find_exact)
        is_unit = (section == "Plan")
        selftriaged = 0
        n = split_cells(line, cells)
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
        n = split_cells(line, cells)
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
        # findings-shape. A finding folded onto a NEIGHBOURING row line has no row of its
        # own: no id for triage-orphan to fire on, no triage cell for triage-state to rule
        # on, so a clean lint and a complete table are indistinguishable. Measured on a
        # real ledger, which held a major that way, joined by a stray double pipe.
        # Narrow on purpose. An over-long row ALONE is the stray-pipe parse FAIL QUIET stays
        # silent on, and it is common -- the header entry for findings-shape carries the
        # measurement and is its one home. What fires here is the JOIN signature: an empty
        # interior cell immediately followed by a finding-shaped id, which no legitimate
        # over-long row in that corpus carries and a double-pipe fold always does.
        # Red-checked against a folded fixture, which it names correctly, and green-checked
        # against a cell holding a jq pipe -- the exact false positive a cell-count test
        # produces.
        if (is_find && find_ncell > 0 && n > find_ncell) {
          for (fs = 2; fs < n; fs++) {
            if (trim(cells[fs]) == "" && is_id(idtoken(cells[fs + 1]))) {
              printf "sage-lint findings-shape %s:%d finding id %s is folded into this row: the line splits into %d cells against the header row %d, so that finding has no row of its own and no triage cell\n", FILE, NR, idtoken(cells[fs + 1]), n - 2, find_ncell - 2
              break
            }
          }
        }
        if (is_unit && tok != "") unit_id[tok] = 1
        if (section == "Decisions" && tok ~ /^D[0-9]+$/) dec_id[tok] = 1
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
        printf "sage-lint triage-orphan %s:%d duplicate finding id '"'"'%s'"'"' appears %d times in Findings\n", FILE, find_last[id], id, find_count[id]
    for (id in cand_line)
      if (!(id in find_count) && !(id in unit_id) && !(id in dec_id))
        printf "sage-lint triage-orphan %s:%d orphan finding id '"'"'%s'"'"': appears in the ledger but has no row in the first table under Findings (the only table this check reads as triage)\n", FILE, cand_line[id], id
  }
' <<<"$SANITIZED" | sort -t: -k2 -n)
add "$CHK"

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
      if (heading == "Findings") fam_home = 1
      else if (fam_first == 0) fam_first = NR
    }
    if (index(low, "rail-1") > 0 || low ~ /rail 1([^0-9.km]|[km][a-z]|\.[^0-9]|\.?$)/) {
      if (heading == "Decisions") rail_home = 1
      else if (rail_first == 0) rail_first = NR
    }
  }
  END {
    if (fam_first > 0 && !fam_home)
      printf "sage-lint disclosure-home %s:%d same-family/residual-bias keywords appear in the ledger but no line under Findings (the required home) carries the disclosure\n", FILE, fam_first
    if (rail_first > 0 && !rail_home)
      printf "sage-lint disclosure-home %s:%d rail-1 keywords appear outside Decisions and no rail-1 line exists there (the required home for an authorisation)\n", FILE, rail_first
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
# frame

CHK=$(awk -v FILE="$FILE" "$AWK_LIB"'
  {
    line = $0
    if (is_heading(line)) {
      inplan = (heading_of(line) == "Plan")
      if (inplan && plan_line == 0) plan_line = NR
      next
    }
    if (!inplan || ask_seen) next
    t = line
    sub(/^[ \t]*(-[ \t]+)?(\*\*)?/, "", t)
    if (t ~ /^ASK:/) {
      ask_seen = 1
      rest = substr(t, 5)
      gsub(/[ \t\r*]/, "", rest)
      ask_empty = (rest == "")
      ask_line = NR
    }
  }
  END {
    if (plan_line == 0) exit
    if (!ask_seen)
      printf "sage-lint frame %s:%d Plan section has no ASK: line (the user words, verbatim)\n", FILE, plan_line
    else if (ask_empty)
      printf "sage-lint frame %s:%d ASK: line has nothing after the colon\n", FILE, ask_line
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
# alt-record

CHK=$(awk -v FILE="$FILE" "$AWK_LIB"'
  function seat_in(text,   t) {
    t = tolower(text)
    if (index(t, "verifier-alt")) rows["verifier-alt"]++
    if (index(t, "refuter-alt")) rows["refuter-alt"]++
  }
  # Splits the Alt lane text at every seat name. Each piece is one entry for the seat it starts
  # with; complete[seat] counts the entries whose four receipt fields all carry a value.
  function count_entries(text,   rest, p, s, best, at, seat, entry, i, ok) {
    rest = text
    while (1) {
      best = 0
      for (s in SEAT_NAMES) { p = index(rest, s); if (p && (!best || p < best)) { best = p; at = s } }
      if (!best) break
      if (seat != "") count_entry(seat, substr(rest, 1, best - 1))
      seat = at; rest = substr(rest, best + length(at))
    }
    if (seat != "") count_entry(seat, rest)
  }
  function count_entry(seat, entry,   i, ok) {
    named[seat] = 1; ok = 1
    for (i = 1; i <= 4; i++)
      if (entry !~ ("(^|[^a-z0-9_-])" NEED[i] "[^ \t\r\n;,]")) { ok = 0; gaps[seat] = gaps[seat] " " NEED[i] }
    if (ok) complete[seat]++
  }
  BEGIN { SEAT_NAMES["verifier-alt"]; SEAT_NAMES["refuter-alt"]; split("model= effort= outcome= spend=", NEED, " ") }
  {
    line = $0
    if (is_heading(line)) {
      heading = heading_of(line); in_table = 0; in_alt = 0
      if (heading == "Run record") record_seen = 1
      next
    }
    if (heading == "Plan" && line ~ /^\|/) {
      n = split_cells(line, cells)
      if (!in_table) {
        in_table = 1; agent_idx = 0; plan_line = NR
        for (i = 2; i < n; i++) if (tolower(trim(cells[i])) == "agent") agent_idx = i
        next
      }
      if (agent_idx > 0 && agent_idx < n && trim(cells[agent_idx]) !~ /^:?-+:?$/) seat_in(cells[agent_idx])
      next
    }
    if (heading != "Run record") next
    t = line
    sub(/^[ \t]*(-[ \t]+)?(\*\*)?/, "", t)
    if (!outcome_seen && t ~ /^OUTCOME:/) {
      outcome_seen = 1; v = t; sub(/^OUTCOME:[ \t]*/, "", v); sub(/[ \t]+$/, "", v)
      pending = (v == "pending — written at Step 6")
    }
    if (!alt_line && t ~ /^Alt lane:/) { alt_line = NR; alt_text = t; in_alt = 1; next }
    if (in_alt && line ~ /^[ \t]+[^ \t]/) { alt_text = alt_text " " line; next }
    in_alt = 0
  }
  END {
    if (!record_seen || pending || !(("verifier-alt" in rows) || ("refuter-alt" in rows))) exit
    if (!alt_line) {
      printf "sage-lint alt-record %s:%d the Plan names a codex seat but the Run record has no Alt lane: line (its effort and contribution have no other home)\n", FILE, plan_line
      exit
    }
    count_entries(tolower(alt_text))
    for (s in rows) {
      if (!(s in named))
        printf "sage-lint alt-record %s:%d the Alt lane: line never names %s, which the Plan dispatched\n", FILE, alt_line, s
      else if (complete[s] + 0 < rows[s])
        printf "sage-lint alt-record %s:%d the Alt lane: line has %d complete entr%s for %s, and the Plan has %d row%s for it: each entry needs model= effort= outcome= spend= with values copied from its receipt (missing:%s)\n", FILE, alt_line, complete[s], (complete[s] == 1 ? "y" : "ies"), s, rows[s], (rows[s] == 1 ? "" : "s"), gaps[s]
    }
  }
' <<<"$SANITIZED")
add "$CHK"

# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# secret-shape

CHK=$(awk -v FILE="$FILE" "$AWK_SECRET" <<<"$SANITIZED")
add "$CHK"


if [ -n "$OUT" ]; then
  printf '%s\n' "$OUT"
  exit 1
fi
exit 0
