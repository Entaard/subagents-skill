#!/usr/bin/env bash
#
# LC_ALL=C throughout: every regex here is ASCII-anchored, and running byte-wise (rather
# than through a UTF-8 multibyte table) means a stray non-UTF8 byte in the ledger is just
# another byte, never an awk "multibyte conversion" crash — fail quiet, per FAIL OPEN below.
export LC_ALL=C
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
#   sage-lint.sh --help
#
#   <ledger-path>   The one file to check. Required, exactly one.
#   --help / -h     Print this reminder, exit 0. Any other argument starting with `-`,
#                   zero arguments, or more than one argument is a usage error (exit 2) —
#                   nothing is read in that case.
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
# THE CHECKS — exactly eight, each with a short stable id. Every check reads ONLY the text
# named below and states what it therefore cannot see; that blind spot is not a bug in the
# check, it is the check's honest shape.
#
#   header
#     Reads: line 1 of the raw file.
#     Fires: line 1 is not an HTML comment containing the literal text
#       `sage occupancy duty` — either the phrase is absent from the whole file, or it is
#       present but on a line other than 1.
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
#       also fails (boundary check, not a prefix check). Or the Unit table has no column
#       labelled `state` at all (one violation for the table, not one per row).
#     Cannot see: whether a state was actually KEPT current while the unit ran, only whether
#       the word written down is a legal word. A ledger updated once at the very end and a
#       ledger updated live read identically to this check.
#
#   triage-orphan
#     Reads: the first table under the FIRST `Findings and dispositions` heading (its first
#       column, taken as the set of real finding ids) — that is the ONLY source of "this id
#       has a triage row". Candidate ids (things that might be orphans) are harvested from
#       two places: (a) the first column of every OTHER table in the document, EXCEPT the
#       `Plan`, `Unit table`, `Assumption log` and `Decisions and deviations` sections in full
#       (each carries its own id/index namespace — plan/unit ids, `A1`, `A2`... in two real
#       ledgers, and `D1`, `D2`... in the Decisions table — none of that is a finding id, and
#       scanning it invites exactly the false positive this check must not produce; Decisions
#       is excluded by SECTION NAME rather than by its `id` header label, because `D1` is
#       finding-shaped and a ledger that merely bolds that header cell would otherwise turn
#       every compliant decision row into an orphan), and also except a table whose header's
#       first column reads `id`, `#`, `when`, or `assumption` — markdown emphasis and code
#       ticks stripped before that comparison — even outside those four sections, as one
#       further belt-and-suspenders exclusion; and (b) PROSE, but ONLY on the Run record's `Findings:` summary line (the
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
#       not look is invisible to it, by design.
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
#     Reads: every line whose CURRENT heading (the nearest preceding `##`/`###` line) is
#       exactly one of `Findings and dispositions`, `Decisions and deviations`, or
#       `Assumption log` — deliberately NOT `Plan`, `Unit table`, or `Run record`, both of
#       which routinely preview or restate a disclosure that lives properly elsewhere
#       ("residual bias recorded in Findings"), and firing on that preview would be exactly
#       the noise this check must not make.
#     Keyword sets (case-insensitive substring, heuristic — say so plainly): a same-family /
#       residual maker-checker bias disclosure is recognised by `same-family`, `same family`,
#       or `self-preference bias`; its one legal home is `Findings and dispositions`. A
#       rail-1 authorisation is recognised by `rail-1` or `rail 1`; its one legal home is
#       `Decisions and deviations`.
#     Fires: either keyword set found in one of the three scanned sections OTHER than its own
#       legal home.
#     Cannot see: anything outside those three sections (by design, see above), and cannot
#       tell a real disclosure from an incidental use of the same words in an unrelated
#       sentence — a heuristic, not a parser of meaning.
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
#       different heading string, and this check does not guess at near-misses).
#
# ---------------------------------------------------------------------------
# OUTPUT LINE SHAPE, fixed field order:
#
#   sage-lint <check-id> <path>:<line> <message>
#
# `<path>` is the path exactly as given on the command line (never resolved or shortened).
# Grep field 2 to select a check; split on the first `:` after field 3 to get the line
# number. A clean ledger prints NOTHING — no summary line, no "0 violations", nothing.
#
# ---------------------------------------------------------------------------
# EXIT STATUS
#
#   0   clean — no violations (silence on stdout)
#   1   dirty — one or more violation lines were printed
#   2   usage error — the arguments themselves were unusable; nothing was read
#   3   the path is unreadable, is a directory, or is not a ledger at all (see "Is a ledger"
#       above) — distinguishable from "dirty": a caller can tell "nothing to check here" from
#       "checked it, found problems" without parsing any prose.
#
# ---------------------------------------------------------------------------
# BLIND SPOTS, stated rather than hidden — none of the eight checks above can see:
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
#
# FAIL QUIET. A parse this script cannot make is silence, not a violation and not a crash. A
# malformed table, a stray pipe, a non-UTF8 byte, a file with no trailing newline, a heading
# shape it does not recognise — none of these produce a spurious violation line or a non-zero
# exit other than the three defined above. When in doubt, this script says nothing: a linter
# that cries wolf gets ignored, and an ignored linter is worse than none, because the run
# record still says it ran.

usage() {
  printf '%s\n' \
    'sage-lint.sh <ledger-path>   check one ledger, one violation per line, silent if clean' \
    'sage-lint.sh --help          this reminder' \
    '' \
    'Exit 0 clean, 1 dirty, 2 usage error, 3 path unreadable/dir/not-a-ledger.' \
    'Output: sage-lint <check-id> <path>:<line> <message>' \
    'Checks: header header-fields state-enum triage-orphan plan-unit disclosure-home sections' \
    '        amend-tag'
}

# ---------------------------------------------------------------------------
# Arguments

if [ $# -ne 1 ]; then
  usage >&2
  exit 2
fi

case "$1" in
  -h|--help) usage; exit 0 ;;
  -*) printf 'sage-lint: unknown option %s\n' "$1" >&2; exit 2 ;;
esac

FILE="$1"

# ---------------------------------------------------------------------------
# Path validation and "is a ledger" (see USAGE above)

if [ ! -e "$FILE" ] || [ -d "$FILE" ] || [ ! -r "$FILE" ]; then
  printf 'sage-lint: %s: not readable, or a directory, or missing\n' "$FILE" >&2
  exit 3
fi

# Fence-blank the content once: any line between a pair of ``` fence markers becomes an
# empty line, line count preserved, so every later check that scans for headings or table
# rows never mistakes a quoted template inside a fence for the ledger's own record.
SANITIZED=$(awk '
  {
    t = $0
    sub(/^[ \t]+/, "", t)
    if (t ~ /^```/) { infence = !infence; print ""; next }
    if (infence) { print ""; next }
    print
  }
' "$FILE" 2>/dev/null)

REQUIRED_SECTIONS='Plan,Unit table,Assumption log,Decisions and deviations,Findings and dispositions,Run record'

# Three independent marks of ledger-hood; any one is enough (see "Is a ledger" above).
IS_LEDGER=$(awk -v req="$REQUIRED_SECTIONS" '
  BEGIN { n = split(req, want, ","); for (i = 1; i <= n; i++) ok[want[i]] = 1 }
  NR == 1 && /<!--/ && /sage occupancy duty/ { byheader = 1 }
  {
    line = $0
    if (line ~ /^#[ \t]+sage ledger/) bytitle = 1
    if (match(line, /^#{2,3}[ \t]+/)) {
      h = line
      sub(/^#{2,3}[ \t]+/, "", h)
      sub(/[ \t\r]+$/, "", h)
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

HEADER_OK=0
if [ -z "$FIRST_HDR_LINE" ]; then
  add "sage-lint header $FILE:1 header comment (sage occupancy duty) is absent"
elif [ "$FIRST_HDR_LINE" != "1" ]; then
  add "sage-lint header $FILE:$FIRST_HDR_LINE header comment present but not on line 1"
else
  HEADER_OK=1
fi

if [ "$HEADER_OK" -eq 1 ]; then
  LINE1=$(sed -n '1p' "$FILE" 2>/dev/null)

  if printf '%s' "$LINE1" | grep -q 'Generation:'; then
    GEN=$(printf '%s' "$LINE1" | sed -n 's/.*Generation:[ \t]*\([^,]*\),.*/\1/p')
    GEN=$(printf '%s' "$GEN" | sed 's/^[ \t]*//; s/[ \t]*$//')
    case "$GEN" in
      [1-9]|[1-9][0-9]|[1-9][0-9][0-9]|[1-9][0-9][0-9][0-9]|[1-9][0-9][0-9][0-9][0-9]) : ;;
      [0-9]*)
        if ! printf '%s' "$GEN" | grep -qE '^[1-9][0-9]*$'; then
          add "sage-lint header-fields $FILE:1 Generation is not a bare positive integer: '$GEN'"
        fi
        ;;
      *)
        add "sage-lint header-fields $FILE:1 Generation is not a bare positive integer: '$GEN'"
        ;;
    esac
  else
    add "sage-lint header-fields $FILE:1 header comment carries no Generation: field"
  fi

  if printf '%s' "$LINE1" | grep -q 'role:'; then
    ROLE=$(printf '%s' "$LINE1" | sed -n 's/.*role:[ \t]*\([A-Za-z]*\).*/\1/p')
    if [ "$ROLE" != "parent" ] && [ "$ROLE" != "supervisor" ]; then
      add "sage-lint header-fields $FILE:1 role is neither 'parent' nor 'supervisor': '$ROLE'"
    fi
  else
    add "sage-lint header-fields $FILE:1 header comment carries no role: field"
  fi
fi

# ---------------------------------------------------------------------------
# state-enum

CHK=$(awk -v FILE="$FILE" '
  function trim(s) { sub(/^[ \t]+/, "", s); sub(/[ \t]+$/, "", s); return s }
  {
    line = $0
    if (match(line, /^#{2,3}[ \t]+/)) {
      in_table = 0
      h = line
      sub(/^#{2,3}[ \t]+/, "", h)
      sub(/[ \t\r]+$/, "", h)
      heading = h
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
            if (val != "") {
              # A legal state word at a real word boundary: end of the cell, or followed by
              # anything that is not a letter (space, comma, semicolon, ...). `reported,` and
              # `reported 07:11` both pass; `done ...` and `reportedly ...` both fail.
              if (val !~ /^(planned|running|reported|blocked|failed|abandoned|inline)([^A-Za-z]|$)/) {
                printf "sage-lint state-enum %s:%d unit '"'"'%s'"'"' has illegal state '"'"'%s'"'"'\n", FILE, NR, id, val
              }
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
  }
' <<<"$SANITIZED")
add "$CHK"

# ---------------------------------------------------------------------------
# triage-orphan

CHK=$(awk -v FILE="$FILE" '
  function trim(s) { sub(/^[ \t]+/, "", s); sub(/[ \t]+$/, "", s); return s }
  function idtoken(cell,   t, i, j) {
    t = trim(cell)
    i = index(t, " ")
    if (i > 0) t = substr(t, 1, i - 1)
    j = index(t, "(")
    if (j > 0) t = substr(t, 1, j - 1)
    return t
  }
  function is_id(t) {
    return (t ~ /^[A-Z]$/) || (t ~ /^[A-Z]{1,4}-?[0-9]{1,3}[a-z]?$/)
  }
  function rstrip(s) { sub(/[ \t]+$/, "", s); return s }
  # delabel: a header cell compared without markdown emphasis or code ticks, so `**id**`,
  # `_id_` and `` `id` `` all read as `id`. Ledgers on this machine bold table cells freely.
  function delabel(s) { gsub(/[*_`]/, "", s); return trim(tolower(s)) }
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
    if (match(line, /^#{2,3}[ \t]+/)) {
      in_table = 0
      h = line
      sub(/^#{2,3}[ \t]+/, "", h)
      sub(/[ \t\r]+$/, "", h)
      heading = h
      if (heading == "Findings and dispositions" && find_idx == 0) find_idx = NR
      next
    }
    # Assumption log, Plan, Unit table and Decisions and deviations each carry their own
    # id/index namespace (`A1`, `#`-numbered rows, unit ids, `D1`) — never a source of
    # finding-id candidates. Decisions is excluded BY NAME rather than by its `id` header
    # label: `D1`, `D2` are finding-SHAPED, so a ledger that merely bolds that header cell
    # (`**id**`) would turn every one of its decision rows into a bogus orphan — a
    # false-positive storm produced by a fully compliant ledger.
    excluded_section = (heading == "Assumption log" || heading == "Plan" || \
                        heading == "Unit table" || heading == "Decisions and deviations")
    if (line ~ /^\|/) {
      if (!in_table) {
        in_table = 1
        expect_sep = 1
        is_find = (find_idx > 0 && find_captured == 0 && heading == "Findings and dispositions")
        n = split(line, cells, "|")
        header_label = delabel(cells[2])
        next
      } else if (expect_sep) {
        expect_sep = 0
        next
      } else {
        n = split(line, cells, "|")
        tok = idtoken(cells[2])
        if (tok != "" && is_id(tok)) {
          if (is_find) {
            find_count[tok]++
            if (find_count[tok] == 1) find_line[tok] = NR
            find_last[tok] = NR
          } else if (!excluded_section && header_label != "id" && header_label != "#" && \
                     header_label != "when" && header_label != "assumption") {
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
    if (!excluded_section && is_findings_line && index(line, "(") > 0) {
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
      if (!(id in find_count))
        printf "sage-lint triage-orphan %s:%d orphan finding id '"'"'%s'"'"': appears in the ledger but has no row in the first table under Findings and dispositions (the only table this check reads as triage)\n", FILE, cand_line[id], id
  }
' <<<"$SANITIZED" | sort -t: -k2 -n)
add "$CHK"

# ---------------------------------------------------------------------------
# plan-unit

extract_table_ids() {  # extract_table_ids <heading-name>  — prints "id<TAB>line" rows, or
                        # "NOTABLE<TAB>line" if the heading exists with no table under it,
                        # or nothing at all if the heading does not exist.
  awk -v target="$1" '
    function trim(s) { sub(/^[ \t]+/, "", s); sub(/[ \t]+$/, "", s); return s }
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
      if (match(line, /^#{2,3}[ \t]+/)) {
        in_table = 0
        h = line
        sub(/^#{2,3}[ \t]+/, "", h)
        sub(/[ \t\r]+$/, "", h)
        heading = h
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

DECISIONS_TEXT=$(awk '
  {
    line = $0
    if (match(line, /^#{2,3}[ \t]+/)) {
      h = line
      sub(/^#{2,3}[ \t]+/, "", h)
      sub(/[ \t\r]+$/, "", h)
      heading = h
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

CHK=$(awk -v FILE="$FILE" '
  {
    line = $0
    if (match(line, /^#{2,3}[ \t]+/)) {
      h = line
      sub(/^#{2,3}[ \t]+/, "", h)
      sub(/[ \t\r]+$/, "", h)
      heading = h
      next
    }
    cat = ""
    if (heading == "Findings and dispositions") cat = "FIND"
    else if (heading == "Decisions and deviations") cat = "DEC"
    else if (heading == "Assumption log") cat = "ASSUM"
    if (cat == "") next
    low = tolower(line)
    if ((index(low, "same-family") > 0 || index(low, "same family") > 0 || index(low, "self-preference bias") > 0) && cat != "FIND")
      printf "sage-lint disclosure-home %s:%d same-family/residual bias disclosure keyword found outside its home (Findings and dispositions); seen in %s\n", FILE, NR, heading
    if ((index(low, "rail-1") > 0 || index(low, "rail 1") > 0) && cat != "DEC")
      printf "sage-lint disclosure-home %s:%d rail-1 authorisation keyword found outside its home (Decisions and deviations); seen in %s\n", FILE, NR, heading
  }
' <<<"$SANITIZED")
add "$CHK"

# ---------------------------------------------------------------------------
# amend-tag

CHK=$(awk -v FILE="$FILE" '
  function trim(s) { sub(/^[ \t]+/, "", s); sub(/[ \t]+$/, "", s); return s }
  {
    line = $0
    if (match(line, /^#{2,3}[ \t]+/)) {
      in_table = 0
      h = line
      sub(/^#{2,3}[ \t]+/, "", h)
      sub(/[ \t\r]+$/, "", h)
      heading = h
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

CHK=$(awk -v FILE="$FILE" -v req="$REQUIRED_SECTIONS" '
  BEGIN { n = split(req, want, ",") }
  {
    line = $0
    if (match(line, /^#{2,3}[ \t]+/)) {
      h = line
      sub(/^#{2,3}[ \t]+/, "", h)
      sub(/[ \t\r]+$/, "", h)
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

if [ -n "$OUT" ]; then
  printf '%s\n' "$OUT"
  exit 1
fi
exit 0
