#!/usr/bin/env bash
# sage-watch.sh — the sage occupancy sensor. Notify only; it never recalls anything.
#
# RUN BLOCK
#   Ladder: SAGE_WINDOW=<n> [SAGE_COMPACT_AT=<n>] sage-watch.sh <subagents-dir>
#   Probe:  SAGE_WINDOW=<n> [SAGE_COMPACT_AT=<n>] sage-watch.sh --status <subagents-dir>
#
#   SAGE_WINDOW always (unset, it assumes 1006380, the 1M window). SAGE_COMPACT_AT where the
#   user stated a compaction point.
#   SAGE_CHECKPOINT_TURN=<turn> at close, for saving-post-rung. Amounts take a k/K/m/M
#   suffix; SAGE_CHECKPOINT_TURN is a bare integer.
#
#   ONE RUNG, `occ-checkpoint`, ladder mode and an explicit dir only, once per compaction
#   segment. On it the parent checkpoints: `../SKILL.md` `## Compaction and resume`.
#
#     sage-watch occ-checkpoint checkpoint <session> [parent] "session transcript" \
#       occupancy=302k window=1006380 compact-at=177779 source=measured rung=147779 pct=30%
#
#   `--status` fires nothing; one parent line, then one line per unit:
#
#     sage-watch status <session> [parent] "session transcript" model=<id> occupancy=160k \
#       window=1006380 compact-at=<int> source=<measured|stated|assumed> rung=<int> \
#       pct=16% compact=<n> turns=<n> occ-sum=<int> crossed-at=<turn|none> \
#       saving-post-rung=<int>
#     sage-watch status <agent-id> [<type>] "<desc>" done=yes spend=205k raw=496k \
#       occupancy=173k idle=2379s repeat=1 records=44 compact=<n> model=<id>
#
#   FAIL OPEN. `--status` printing nothing on stdout AND nothing on stderr means the
#   sensor cannot run on this layout: disable it and write one ledger line. A line on
#   stderr instead names a fixable cause — fix that and probe again. Exit 0 always,
#   except exit 2 on unusable arguments.
#
#   The rest of this header is the maintainer's manual.
# END RUN BLOCK
#
# It reads the in-flight subagent transcripts of one session, watches the single
# parent-occupancy rung — the checkpoint rule in `../SKILL.md` ## Compaction and resume,
# and `../references/execute.md` — and prints ONE LINE PER FIRED RUNG. A healthy sample
# prints nothing and exits 0. It is hosted on `Monitor` with `persistent: true`, where
# every stdout line becomes a notification, so silence is the default output.
#
# It never writes a file, never calls `TaskStop`, never kills a process, and never
# touches a transcript. It reports; the parent acts.
#
# ---------------------------------------------------------------------------
# USAGE
#
#   sage-watch.sh [<subagents-dir>|-] [<ignored>]
#   sage-watch.sh --status [<subagents-dir>|-] [<ignored>]
#   sage-watch.sh --help
#
#   <subagents-dir>   The session's `subagents/` directory. Omit it, or pass `-`, to
#                      discover it (rule below).
#   <ignored>          A stale second positional argument, accepted and never an error:
#                      fail-open applies to arguments too. `--status` prints one `note`
#                      line saying so; ladder mode says nothing about it, ever.
#   --status           Diagnostic mode. Prints one line per agent with every figure,
#                      fires no rungs. This is the "probe once at start" call: if it
#                      prints nothing ON STDOUT AND NOTHING ON STDERR, the sensor cannot
#                      run on this layout and the parent disables it silently and writes
#                      one ledger line. A line on stderr is NOT that signal, whatever
#                      stdout did: it names a missing jq, an EXPLICIT directory that does
#                      not resolve, or any directory -- explicit or discovered -- that
#                      resolves and holds no readable agent-*.jsonl. Judge the two streams
#                      SEPARATELY, because that third line does not need an empty stdout:
#                      it fires after the per-agent loop, so a directory holding no
#                      agent-*.jsonl but a readable parent transcript prints a `[parent]`
#                      status line on stdout AND the diagnostic on stderr (measured). All
#                      three are one-line fixes -- fix what it names and probe again rather
#                      than disabling the sensor for the run. Discovery that finds no
#                      readable, TRAVERSABLE directory is the one silent case: the guard
#                      below tests -d, -r and -x, so a discovered mode-600 directory passes
#                      -r, fails -x, and is silent too. Those three are --status only, and
#                      ladder mode stays silent about them; an unusable ARGUMENT is the
#                      exception -- it exits 2 and says so in either mode.
#
#   SAGE_WINDOW        Env. The live context window, in the same integer/k/K/m/M forms
#                      as below. Defaults to 1006380 (the 1M window as measured in
#                      `../references/harness-measurements.md`, Compaction record) when unset, unparseable, or zero.
#                      Drives the parent occupancy rung below — see BLIND SPOTS for
#                      what a wrong value actually does (it is not silence).
#   SAGE_COMPACT_AT    Env. The compaction point the USER stated — they ran
#                      `/autocompact <size>`, or they are on a model variant whose
#                      trigger sits below the window. Same integer/k/K/m/M forms. Unset,
#                      unparseable, or zero means "not stated", and the evidence order in
#                      THE COMPACTION POINT below falls through to `assumed`. A
#                      `compact_boundary` in the transcript outranks it: measured beats
#                      stated.
#   SAGE_CHECKPOINT_TURN
#                      Env, `--status` only, a BARE integer (no suffix). The turn the
#                      checkpoint rung actually fired at, as recorded in the ledger's
#                      `### Resume state`. It replaces `crossed-at` as the origin of
#                      `saving-post-rung` — see THE PARENT LINE. Unset or unparseable
#                      falls back to `crossed-at`.
#
# Exit status is 0 in every normal case, including a missing directory, no transcripts,
# malformed JSON, a half-written final line, and a transcript with no assistant records.
# Exit 2 means the ARGUMENTS were unusable (more than two positional arguments, or an
# unknown option); nothing was inspected.
#
# ---------------------------------------------------------------------------
# DISCOVERY RULE (used when <subagents-dir> is omitted or `-`)
#
#   1. slug  = the current working directory with every character outside [A-Za-z0-9]
#              replaced by `-`.  /Users/x/Projects/notes  ->  -Users-x-Projects-notes
#   2. base  = ${CLAUDE_CONFIG_DIR:-$HOME/.claude}/projects/<slug>/
#   3. Pick the most recently modified <session-uuid>/subagents/ directory under base.
#   4. Nothing there -> print nothing, exit 0.
#
# Prefer passing the directory explicitly when the parent already knows the session id;
# discovery is the fallback for a probe launched without one.
#
# The PARENT OCCUPANCY RUNG (occ-checkpoint — below) runs ONLY when <subagents-dir>
# was passed explicitly. Under discovery it is skipped entirely, unconditionally:
# discovery picks the most recently modified subagents/ directory under the project slug,
# which can belong to a DIFFERENT session than the one asking — measured on this machine:
# 9 candidate directories, top two 1,832s apart — and a checkpoint trigger must
# never fire on someone else's occupancy. `--status` is diagnostic, not a trigger, so it
# does not carry that risk: it prints the parent line under discovery too, labeled with
# whichever session id discovery resolved — subject to the fail-open cases in THE PARENT
# LINE below, which withhold the line on either mode.
#
# ---------------------------------------------------------------------------
# THE ARITHMETIC — this is where a naive build goes wrong
#
# THE REFERENCE CORPUS, named once because every figure below is measured on it and on
# nothing else: 197 transcripts, measured 2026-08-18 — every
# `<session>/subagents/agent-*.jsonl` under `~/.claude/projects/`, NON-RECURSIVE, across
# all projects, `workflows/wf_*/` excluded. That is exactly the population this script's
# own glob can read, and it is the same one `../references/harness.md` quotes; the two
# must agree, figure for figure. A recursive sweep instead drags in the `wf_*` sidecars
# of the deleted `Workflow` backend — units this probe never opens and sage never
# produces — and moves every number below. Symlinked duplicates are counted once. This is
# date-stamped because the corpus grows and old transcripts are pruned: re-measure before
# betting anything on it.
#
# Assistant records are STREAMING PARTIALS: one `message.id` is written many times with
# growing `usage`. Summing raw inflates spend, so a rail built the obvious way fires at a
# fraction of real spend and alarms on healthy agents constantly. Always
# `group_by(.message.id) | map(.[-1])` before any sum — the inflation is a DISTRIBUTION,
# not a constant: the median transcript inflates about 2x and the tail past 8x, which is
# the magnitude, and `../references/harness.md`, `## Transcripts and the token arithmetic`
# holds the distribution as its single home. This is why the dedup is not optional.
#
#   done       the unit is presumed FINISHED. Read off the FINAL assistant record in FILE
#              order (not the `group_by` array's last element, which is sorted by id), and
#              not off `any` record. Three clauses, any one sufficient:
#                a. its `stop_reason` is `end_turn` or `stop_sequence`;
#                b. its content carries a `text` block and no `tool_use` block — a turn
#                   that ended in prose with no call pending is over, whatever the
#                   `stop_reason` field says;
#                c. `idle` is past IDLE_CEIL — evidence this cold describes a unit that is
#                   gone, not one that is stalling, and there is nothing left to steer.
#              Clause (b) is the load-bearing one: with it the predicate covers 95.5% of
#              the reference corpus. `../references/harness.md` is the single home for the
#              rest — the per-clause split, the superseded `any`-record rule it replaced,
#              and what `done` still cannot see. Read a coverage figure there, not here.
#   spend      sum of `input + cache_creation + output` over DEDUPLICATED records.
#              Excludes `cache_read` — re-read context is not spend.
#   occupancy  `input + cache_creation + cache_read` on the SINGLE MOST RECENT assistant
#              record. Includes `cache_read` — those tokens are in the window.
#              Point-in-time, never a sum. Reported by --status; fires no rung here.
#   idle       now minus the last record timestamp, which PROBE requires to be a string:
#              a numeric or null one yields `-`, never a stale age (see the probe
#              block). Reliable for liveness, noisy as a stall
#              proxy (`../references/harness.md` has the base rates). IDLE_CEIL
#              below is set well past the largest returns this corpus has measured.
#   repeat     the largest count of one identical tool call (same name AND same input)
#              across deduplicated records. Diagnostic only now — `--status` reports it,
#              nothing on the ladder acts on it.
#   turns      the DEDUPLICATED assistant record count. `records=` on a unit line is the
#              raw count and stays raw; `turns=` on the parent line is this one. They are
#              different figures on purpose — the raw/dedup gap is the inflation above.
#   occ-sum    the sum of `occupancy` over the deduplicated records, in order — every
#              turn's whole window, counted once per turn. This is the cache-read cost the
#              `spend` formula excludes, and it is real money: cache reads bill at 0.1x the
#              input price on most models, and 0.025x on Fable 5.1 and Mythos 5.1. That
#              rate table is why `model=` is on the parent line — the parent needs the id
#              to pick the row before it can price `saving-post-rung`.
#
# ---------------------------------------------------------------------------
# THE COMPACTION POINT — where `compact-at`, `source` and the rung come from
#
# The sensor still CANNOT SEE THE WINDOW, and it cannot see the compaction trigger either
# until one has fired. Three sources of evidence, in strict order, first hit wins:
#
#   measured   the parent transcript holds at least one `.type == "system"` record with
#              `.subtype == "compact_boundary"`. compact-at = the LARGEST
#              `.compactMetadata.preTokens` across them — the trigger observed on this
#              session, on this harness, for this model. Largest, not last: preTokens is
#              what was in the window when the trigger fired, and a compaction that fired
#              early (a single huge tool result, a manual `/compact`) reads LOW and would
#              drag the estimate down.
#   stated     `SAGE_COMPACT_AT` parses to a positive integer. The user's own statement,
#              trusted only until the session produces a boundary of its own.
#   assumed    WINDOW minus a reserve of 30000. The reserve is an ESTIMATE: it was
#              measured on a 200k window only, and is unknown on 1M. Treat an `assumed`
#              compact-at as a placeholder, not a figure to price anything with.
#
#   rung = compact-at - max(WINDOW * 5 / 100, 30000)      (integer arithmetic)
#
# The 30000 floor exists because 5% of a 200k window is 10k, which is about one minute of
# measured parent burn and less than one large tool result — no room to bring a ledger
# current in. Both of those are ESTIMATES too: per-turn growth has not been measured, so
# the floor is a judgement, not a derivation. Re-measure before tightening it.
#
# ---------------------------------------------------------------------------
# THE LADDER — nothing in it recalls an agent automatically
#
#   rung             action      fires when
#   occ-checkpoint   checkpoint  parent occupancy >= rung (THE COMPACTION POINT above),
#                                once per compaction segment -> bring the ledger current
#                                and restamp `### Resume state`; `../SKILL.md`
#                                ## Compaction and resume
#
# ONE RUNG, deliberately. There is nothing above it: the checkpoint is the whole of what a
# parent can do about its own occupancy, and doing it twice buys nothing. The parent rung
# is a SINGLE line, not per-agent, and it runs only when <subagents-dir> was passed
# explicitly (DISCOVERY RULE above).
#
# FIRE ONCE PER SEGMENT, and STATELESSLY — no acknowledgement variable, nothing written
# anywhere. A segment is the run of records AFTER the newest `compact_boundary` in FILE
# order (or after the start of file, when there is none). Over that segment's assistant
# records, deduplicated by `message.id` keeping each id's LAST record and held in
# first-appearance order, the rung fires only when the LAST record is at or past the rung
# AND no earlier record in the segment was. So the sample that first crosses fires; every
# sample after it is silent, because an earlier record in the same segment has now crossed
# too; and the next compaction starts a fresh segment, which can cross and fire again.
# The transcript itself is the state, which is why this survives a compaction with no
# variable to set and nothing to reset when the parent is restarted or resumed.
#
# OUTPUT LINE SHAPE, fixed field order:
#
#   sage-watch <rung> <action> <agent-id> [<agentType>] "<description>" <figures...>
#
# Grep a rung name to select; field 2 is the rung, field 3 the action, field 4 the id.
#
# `--status` uses the same first four fields with the rung `status` and no action, then
# every figure as key=value:
#
#   sage-watch status a37cd95f4 [Explore] "Gate blast radius" done=yes spend=205k \
#              raw=496k occupancy=173k idle=2379s repeat=1 records=44 compact=1 \
#              model=claude-opus-5
#
# `raw` is the undeduplicated sum, printed only here, only so the dedupe stays auditable.
# `compact=` above zero on a UNIT line says that unit compacted mid-work, so its report was
# written from a summary of its own transcript rather than from the transcript — the parent
# treats that as a deviation to record (`../references/execute.md`). `model=` is the
# `message.model` of that unit's newest deduplicated assistant record, `unknown` when it
# has none.
#
# A stale second positional argument prints one extra `note` line, `--status` only, before
# every other line:
#
#   sage-watch note "estimates file ignored: the spend rungs were removed" <path-as-given>
#
# THE PARENT LINE, printed first (after the note line, if any) and separately from the
# per-agent lines above, WHEN it prints at all (fail-open exceptions below). `window=` is
# always the RAW integer, never `tok()`-shortened — the parent must read back exactly the
# figure it passed in `SAGE_WINDOW`, and a rounded window is precision the caller cannot
# use. Ladder rungs print this line only when <subagents-dir> was passed explicitly
# (never under discovery); `--status` prints it whether the dir was explicit or discovered:
#
#   sage-watch occ-checkpoint checkpoint <session-id> [parent] "session transcript" \
#              occupancy=302k window=1006380 compact-at=177779 source=measured \
#              rung=147779 pct=30%
#
#   sage-watch status <session-id> [parent] "session transcript" model=claude-opus-5 \
#              occupancy=160k window=1006380 compact-at=177779 source=measured \
#              rung=147779 pct=16% compact=15 turns=188 occ-sum=17262417 \
#              crossed-at=42 saving-post-rung=9330288
#
# `compact-at`, `rung`, `occ-sum` and `saving-post-rung` print RAW, never `tok()`-shortened,
# for the same reason `window=` does: the parent copies them straight into the ledger and a
# journal `run` line, and a rounded figure is precision it cannot get back.
#
# The `--status`-only fields after `pct=`:
#   compact            how many `compact_boundary` records the parent transcript holds.
#   turns              the deduplicated assistant record count over the WHOLE transcript.
#   occ-sum            the sum of occupancy over those records (THE ARITHMETIC above).
#   crossed-at         the 1-based index, in that same deduplicated first-appearance
#                      order, of the first record at or past `rung` — or `none`. It is a
#                      WHOLE-transcript figure, so it does not reset at a compaction the
#                      way the rung's own fire test does.
#   saving-post-rung   what a fresh window after the checkpoint could have saved: with T
#                      = `SAGE_CHECKPOINT_TURN` when set to a positive integer, else
#                      `crossed-at` (0 for `none`), the sum over deduplicated records
#                      indexed above T of `max(occupancy - 60000, 0)`. The 60000 is the
#                      floor a resumed parent would have carried anyway — skill, ledger
#                      and re-read state — so what is left is the avoidable part. Price it
#                      at the cache-read rate for `model=`, not the input rate.
#
# `<session-id>` is the session uuid — the basename of the session directory one level
# above `subagents/`, or, under discovery in `--status` mode, whichever session id
# discovery resolved. `--status` prints this line first, explicit dir or discovered —
# EXCEPT the five fail-open cases that print no parent line at all: the parent transcript
# is missing, unreadable, or unparseable, it carries no assistant records, or its
# occupancy reads 0. The ladder prints the line only under an explicit dir, and only on
# the one sample per segment where `occ-checkpoint` fires.
# `done` takes three values on `--status`: `yes` (clause a or b), `stale` (clause c — the
# transcript is older than IDLE_CEIL, so the unit is presumed gone), and `no`.
#
# BLIND SPOTS, stated rather than hidden: no signal here detects the confident-wrong
# agent that burns a normal budget and returns a fluent fabrication, correct-but-
# irrelevant work, late-degrading reasoning, or machine sleep — which is indistinguish-
# able from a stall. The verification layer is the only defence for the first.
#
# What the `done` predicate specifically cannot see, since it decides on the last record
# written rather than on any statement of intent — `../references/harness.md` carries the
# full corpus breakdown:
#   - A unit that stalls just after emitting a text block and before its tool call lands
#     in the same turn reads as finished under clause (b). While the unit is alive this
#     self-corrects at the next sample; if it hangs in exactly that window it is silent
#     for good.
#   - A unit that returns a complete, wrong or empty answer is `done` — the predicate
#     reads shape, never content.
#   - A unit genuinely hung inside a tool call for more than IDLE_CEIL is called gone and
#     stops being reported. That is deliberate: `SendMessage` drains at the receiver's
#     next tool round, and a unit with no tool round in six hours has none coming, so the
#     probe has no actionable claim left to make. Machine sleep lands here too, and going
#     quiet after it is the fail-open answer.
#   - THE SENSOR CANNOT SEE THE WINDOW. It never could and nothing here changed that. It
#     trusts `SAGE_WINDOW` for `pct=` and for the rung's margin, and a wrong value moves
#     both: SMALLER than the real window fires EARLY and LOUD — measured: 900k against a
#     real ~1,006,380 read 32% actual occupancy as 30% — and LARGER fires LATE or never —
#     measured: 10m against the same occupancy read `pct=4%`. Neither direction goes silent
#     on its own; a value that parses to 0 is treated as unparseable and falls back to the
#     1006380 default (below), so it cannot zero out the percentage. A window under the
#     30000 `assumed` reserve yields a negative compact-at, and so a rung that fires on the
#     first sample — loud, not silent, which is the intended direction. Only discovery mode
#     (above) silences the rung outright. Pass the resolved window explicitly rather than
#     trusting the built-in default.
#   - What it CAN see is the compaction trigger, and only once one has fired: `measured`
#     needs a `compact_boundary` already in the transcript. Before the first compaction it
#     trusts `SAGE_COMPACT_AT`, and with neither it ASSUMES, on a reserve measured at one
#     window size (THE COMPACTION POINT above). An `assumed` rung on a 1M window is the
#     weakest figure this script prints.
#   - `occ-checkpoint` fires ONCE per compaction segment and then goes quiet even though
#     occupancy keeps climbing. A checkpoint that the parent misses, ignores, or dispatches
#     past is not re-raised until the next compaction resets the segment.
#
# FAIL OPEN. An absent signal means no alarm, never a recall.

IDLE_CEIL=21600         # 6h. Past this a not-yet-finished unit is presumed gone, not stalled
COMPACT_RESERVE=30000   # `assumed` compact-at = WINDOW - this. Measured on 200k only
CHECKPOINT_MARGIN_PCT=5 # rung = compact-at - max(this% of WINDOW, CHECKPOINT_MARGIN_FLOOR)
CHECKPOINT_MARGIN_FLOOR=30000
RESUME_FLOOR=60000      # what a resumed parent carries anyway; saving-post-rung nets it off

# WINDOW: an integer, or an integer with a k/K (x1000) or m/M (x1000000) suffix. An
# unparseable or unset SAGE_WINDOW falls back to the measured figure in
# ../references/harness.md.
parse_amount() {  # parse_amount <raw> <default> — echoes an integer, never fails
  local raw="$1" fallback="$2" num mult=1
  case "$raw" in
    *k|*K) num="${raw%?}"; mult=1000 ;;
    *m|*M) num="${raw%?}"; mult=1000000 ;;
    *)     num="$raw" ;;
  esac
  case "$num" in ''|*[!0-9]*) printf '%s' "$fallback"; return 0 ;; esac
  printf '%s' $((num * mult))
}

WINDOW=$(parse_amount "${SAGE_WINDOW:-}" 1006380)
# A window of exactly 0 parses as a valid integer but zeroes out every percentage instead
# of ever firing, which is a silent failure worse than falling back — so 0 is unparseable too.
[ "$WINDOW" -ge 1 ] || WINDOW=1006380

# 0 means "the user stated no compaction point", so the evidence order falls through to
# `stated`-then-`assumed` exactly as an unset variable does.
STATED_COMPACT_AT=$(parse_amount "${SAGE_COMPACT_AT:-}" 0)

# --status only, and a BARE integer: it is a turn index, not a token amount, so the k/m
# suffixes parse_amount accepts would be a category error here.
CHECKPOINT_TURN="${SAGE_CHECKPOINT_TURN:-}"
case "$CHECKPOINT_TURN" in ''|*[!0-9]*) CHECKPOINT_TURN=0 ;; esac

JQ=$(command -v jq 2>/dev/null)
[ -n "$JQ" ] || JQ=/usr/bin/jq   # fallback for a stripped PATH; jq ships at /usr/bin on macOS

usage() {
  # The header above is the manual; this is the reminder.
  printf '%s\n' \
    'sage-watch.sh <subagents-dir> [<ignored>]       parent occupancy rung only' \
    'sage-watch.sh [-] [<ignored>]                   discovery: prints nothing, by design' \
    'sage-watch.sh --status [<dir>|-] [<ignored>]    one line per agent, fires nothing' \
    'sage-watch.sh --help                            this reminder' \
    '' \
    'A second positional argument is accepted and ignored (stale estimates-file path from' \
    'before the per-unit rungs were cut). --status prints one note line saying so.' \
    'SAGE_WINDOW (env): the live context window, default 1006380. SAGE_COMPACT_AT (env):' \
    'the compaction point the user stated. SAGE_CHECKPOINT_TURN (env, --status, a bare' \
    'integer): the turn the checkpoint fired at. All three documented above.' \
    'Exit 0 always; exit 2 only when the arguments themselves are unusable.'
}

# ---------------------------------------------------------------------------
# Arguments

STATUS=0
DIR=""
IGNORED_ARG=""
POSN=0

for arg in "$@"; do
  case "$arg" in
    --status) STATUS=1 ;;
    -h|--help) usage; exit 0 ;;
    --*) printf 'sage-watch: unknown option %s\n' "$arg" >&2; exit 2 ;;
    *)
      POSN=$((POSN + 1))
      case "$POSN" in
        1) [ "$arg" = "-" ] || DIR="$arg" ;;
        2) IGNORED_ARG="$arg" ;;
        *) printf 'sage-watch: too many arguments\n' >&2; exit 2 ;;
      esac
      ;;
  esac
done

# ---------------------------------------------------------------------------
# Discovery. See DISCOVERY RULE above.

discover_dir() {
  local base slug newest d
  slug=$(printf '%s' "$PWD" | sed 's/[^A-Za-z0-9]/-/g')
  base="${CLAUDE_CONFIG_DIR:-$HOME/.claude}/projects/$slug"
  [ -d "$base" ] || return 0
  newest=""
  for d in "$base"/*/subagents; do
    [ -d "$d" ] || continue
    if [ -z "$newest" ] || [ "$d" -nt "$newest" ]; then newest="$d"; fi
  done
  printf '%s' "$newest"
}

# EXPLICIT_DIR gates the parent occupancy rung below (DISCOVERY RULE): discovery can
# resolve a different session's directory, and a checkpoint trigger must never fire on it.
if [ -n "$DIR" ]; then EXPLICIT_DIR=1; else EXPLICIT_DIR=0; fi
[ -n "$DIR" ] || DIR=$(discover_dir)

# Fail open: no directory, an unreadable one, or no jq to read it with, is not an alarm.
# This is the "probe once at start" answer — a --status call that prints nothing on stdout
# AND nothing on stderr means the sensor cannot run on this layout, and the parent disables
# it and writes one ledger line. A line on stderr is the other case whatever stdout did --
# judge the two streams separately, per USAGE above -- and the split below is what makes the
# two tellable apart.
#
# The jq test and the layout test are SEPARATE, and each names itself on stderr, because
# the two failures need opposite answers and used to be byte-identical. A missing jq is a
# fixable dependency -- jq does NOT ship with Claude Code, and the /usr/bin fallback above
# is a macOS-shaped assumption, so this fires on Linux and not here -- while an unresolved
# layout is the signal ../SKILL.md Step 4 turns into disabling the sensor for the whole
# run. One silent exit 0 for both told the parent to give up permanently on a one-line fix,
# killing the only rail with a measured true positive. The diagnostics are --status only
# and go to stderr: stdout lines become notifications in the hosting loop, and the loop
# must stay silent. An explicit dir that does not resolve is a caller error, not a layout
# verdict, so it says which layout it expected.
if [ ! -x "$JQ" ]; then
  if [ "$STATUS" -eq 1 ]; then
    printf 'sage-watch: jq not found on PATH or at /usr/bin/jq -- install jq and probe again; the layout was NOT tested\n' >&2
  fi
  exit 0
fi
# `-x` as well as `-r`, because the canonicalizing `cd` below needs to TRAVERSE the
# directory, not just list it. Without it a mode-600 directory passed this guard, failed
# that `cd`, and emptied $DIR through the command substitution -- after which the empty-glob
# guard at the foot of this file printed a diagnostic naming no path at all and claiming the
# layout had "resolved". Measured: two stderr lines, one of them the raw shell `cd` error.
if [ -z "$DIR" ] || [ ! -d "$DIR" ] || [ ! -r "$DIR" ] || [ ! -x "$DIR" ]; then
  if [ "$STATUS" -eq 1 ] && [ "$EXPLICIT_DIR" -eq 1 ]; then
    printf 'sage-watch: %s: not a readable, traversable directory -- the layout is <project>/<session-id>/subagents, one level deeper than <project>/subagents; readlink -f the output_file any dispatch returned -- it is a symlink under tasks/ -- and use its target directory\n' "$DIR" >&2
  fi
  exit 0
fi

# The note about the ignored argument is --status-only and prints before every other line.
# It sits BELOW the guard above on purpose: a probe whose layout does not resolve must
# print nothing at all, or the caller reads one note line as "the sensor works here".
if [ "$STATUS" -eq 1 ] && [ -n "$IGNORED_ARG" ]; then
  printf 'sage-watch note "estimates file ignored: the spend rungs were removed" %s\n' "$IGNORED_ARG"
fi

# Canonicalize to an absolute path now, once validation has already proven $DIR exists and
# is both readable and traversable — safe to `cd` into. The parent occupancy sensor derives
# the parent transcript path from $DIR's own parents (dirname twice); a relative,
# one-component $DIR (e.g. `--status subagents`, run from inside the session directory)
# derives a garbage path from that arithmetic and silently disables the sensor instead of
# failing loudly. `cd` in a subshell so the script's own working directory never moves.
# `CDPATH=` on that `cd`, because `cd` consults CDPATH for a RELATIVE argument and ECHOES
# the directory it landed in whenever it uses one. Measured: with CDPATH exported and a
# one-component $DIR, the substitution returned the decoy path TWICE -- $DIR became a
# two-line string naming a directory the caller never asked for, after which the empty-glob
# guard at the foot of this file printed a malformed two-line diagnostic naming the decoy
# while the caller's real transcripts got no status line at all.
DIR=$(CDPATH= cd "$DIR" && pwd)

# ---------------------------------------------------------------------------
# Formatting helpers

# 1250000 -> 1.2M ; 612345 -> 612k ; 900 -> 900
tok() {
  if [ "$1" -ge 1000000 ]; then
    printf '%d.%dM' $(($1 / 1000000)) $(($1 % 1000000 / 100000))
  elif [ "$1" -ge 1000 ]; then printf '%dk' $(($1 / 1000))
  else printf '%d' "$1"; fi
}

emit() {  # rung action id type desc figures...
  local rung="$1" action="$2" id="$3" type="$4" desc="$5"
  shift 5
  printf 'sage-watch %s %s %s [%s] "%s" %s\n' \
    "$rung" "$action" "$id" "${type:-?}" "$desc" "$*"
}

# ---------------------------------------------------------------------------
# The per-transcript probe. Reads raw lines so a half-written final line is dropped
# by `fromjson?` instead of failing the parse. Emits one TSV row:
#   done spend raw_spend occupancy last_ts repeat_count assistant_records tool input
#   model compact max_pretokens turns occ_sum
#
# `last_ts` comes from the last record that CARRIES a `timestamp` at all, not just an
# assistant one: a tool result lands between assistant turns and is the freshest liveness
# evidence there is. That record's stamp must then be a STRING -- a JSON-numeric or null
# one yields `-`. It used to yield the PREVIOUS record's age instead, which is a silently
# WRONG figure rather than a missing one: the old filter dropped the bad stamp outright, so
# `$stamps[-1]` pointed at an older record and `--status` printed that record's age as this
# one's. Reading `$all[-1]` directly would over-correct -- a record with no `timestamp` KEY
# at all must still fall back to the previous stamp -- which is why the guard is
# `has("timestamp")` and the type test sits after it. Fixture-measured 2026-08-27 on four
# shapes: numeric-last and null-last each moved from a stale age to `-`; all-string and
# absent-key-last were unchanged. Regression: `last_ts` byte-identical across every
# realpath-deduped `agent-*.jsonl` under `~/.claude/projects` -- 632 transcripts / 80,566
# stamps when the change was made, and 637 / 80,784 on an independent re-run the same day
# (2026-08-27), the drift being that session's own five dispatches, exactly as
# `../references/harness.md` says to expect. Zero non-string stamps in either run, so the
# repaired path stays documented rather than observed and no figure a caller reads moved.
# `assistant_records` is the evidence count, and what it gates is narrower than it looks.
# It gates the PARENT line and the parent rung, which both test `records >= 1`: a session
# transcript carrying no assistant record produces no `[parent]` status line and fires no
# checkpoint rung. It does NOT gate the per-agent rows -- an evidence-free transcript still
# prints a full row, `records=0` with spend, raw, occupancy and repeat all zero (measured
# on a user-only transcript), because a caller probing the layout needs to see that the
# file was found and read. So `records=0` is the tell, never `idle`: idle is computed from
# the last timestamp on any record, so an evidence-free transcript still
# reports a real age, and its `-` means only that the subtraction could not be made -- an
# absent, non-string, or unparseable stamp, no usable clock, a stamp strictly in the
# future, or one before the epoch, which fails the same non-negative guard.
# Fields 8 and 9 (tool, input) are read by nothing here. PROBE is SHARED by the parent
# occupancy sensor and `--status`, so it moves only against a fixture AND a whole-corpus
# regression, and it moves by APPENDING fields, never by reordering them: every caller
# reads positionally, and both callers absorb the tail they do not use.
# Fields 10 to 14 are the compaction set: `model` (the newest deduplicated assistant
# record's `message.model`, `unknown` with no assistant record), `compact` (how many
# `compact_boundary` records the file holds), `max_pretokens` (the largest
# `compactMetadata.preTokens` across them, 0 with none -- `numbers` drops a null or string
# one so `max` never returns a non-integer), `turns` (the deduplicated count, against
# field 7's raw one) and `occ_sum` (occupancy summed over the deduplicated records).
# NO FIELD MAY EVER BE EMPTY, which is why fields 8 and 9 emit `-` rather than `""` on a
# transcript with no tool call. TAB is IFS whitespace, so `IFS=$'\t' read` collapses a run
# of tabs into ONE delimiter: an empty field 8 and 9 silently shifted every appended field
# two places left, and the parent line printed max_pretokens as `model=` and an occupancy
# sum as `compact-at=` (measured on a fixture). Nothing reads those two fields, so the
# placeholder costs nothing and the invariant is what keeps positional reads honest.
# `model` is descriptive only: the id does NOT carry the window. `claude-opus-5` has run
# in a 200k and in a 1M session on this machine, so there is no model-to-window table here
# and no derivation of one is sound. SAGE_WINDOW stays the only source for the window.

PROBE='
def num($x): if ($x|type) == "number" then $x else 0 end;
def spend_of: num(.input_tokens) + num(.cache_creation_input_tokens) + num(.output_tokens);
def occ_of:   num(.input_tokens) + num(.cache_creation_input_tokens) + num(.cache_read_input_tokens);
def flat: (. // "") | tostring | gsub("[\\t\\r\\n]"; " ");

[inputs | fromjson? | select(type == "object")] as $all
| [$all[] | select((.type? == "assistant") and (.message?.id? != null))] as $asst
| [$all[] | select((.type? == "system") and (.subtype? == "compact_boundary"))] as $bnd
| ($asst | group_by(.message.id) | map(.[-1])) as $ded
| [$ded[] | (.message.content? // []) | if type == "array" then .[] else empty end
   | select(.type? == "tool_use")
   | {n: (.name // "?"), i: ((.input // {}) | tojson)}] as $calls
| ($calls | group_by([.n, .i]) | map({n: .[0].n, i: .[0].i, c: length}) | max_by(.c)) as $top
| [$all[] | select(has("timestamp")) | .timestamp] as $stamps
| ($asst[-1] // null) as $fin
| ($fin | if . == null then []
          else [ (.message.content? // [])
                 | if type == "array" then . else [{type: "text"}] end
                 | .[] | .type? ] end) as $fct
| (if $fin == null then 0
   elif ($fin.message.stop_reason? == "end_turn"
         or $fin.message.stop_reason? == "stop_sequence") then 1
   elif (($fct | any(. == "text")) and (($fct | any(. == "tool_use")) | not)) then 1
   else 0 end) as $done
| [ $done,
    ([$ded[]  | .message.usage? // {} | spend_of] | add // 0),
    ([$asst[] | .message.usage? // {} | spend_of] | add // 0),
    (if ($asst | length) == 0 then 0 else ($asst[-1].message.usage? // {} | occ_of) end),
    (if ($stamps | length) == 0 then -1
     elif (($stamps[-1] | type) != "string") then -1
     else ($stamps[-1] | sub("\\.[0-9]+Z$"; "Z") | (fromdateiso8601? // -1)) end),
    ($top.c // 0),
    ($asst | length),
    (if $top == null then "-" else ($top.n | flat) end),
    (if $top == null then "-" else ($top.i | flat | .[0:70]) end),
    (if ($asst | length) == 0 then "unknown" else ($asst[-1].message.model // "unknown" | flat) end),
    ($bnd | length),
    ([$bnd[] | .compactMetadata?.preTokens? | numbers] | max // 0),
    ($ded | length),
    ([$ded[] | .message.usage? // {} | occ_of] | add // 0)
  ] | @tsv
'

# No usable clock means no usable idle figure.
NOW=$(date +%s 2>/dev/null)
case "$NOW" in ''|*[!0-9]*) NOW=-1 ;; esac

# 302000 1006380 -> 30   (integer math; no bc, no awk)
pct() {
  [ "${2:-0}" -gt 0 ] || { printf '0'; return 0; }
  printf '%d' $(( $1 * 100 / $2 ))
}

compact_at_of() {  # compact_at_of <max_pretokens> — echoes "<integer> <source-word>"
  # THE COMPACTION POINT above owns this order; first hit wins.
  if [ "$1" -gt 0 ]; then printf '%s measured' "$1"
  elif [ "$STATED_COMPACT_AT" -gt 0 ]; then printf '%s stated' "$STATED_COMPACT_AT"
  else printf '%s assumed' $((WINDOW - COMPACT_RESERVE)); fi
}

checkpoint_rung_of() {  # checkpoint_rung_of <compact-at> — echoes an integer
  local margin=$((WINDOW * CHECKPOINT_MARGIN_PCT / 100))
  [ "$margin" -ge "$CHECKPOINT_MARGIN_FLOOR" ] || margin=$CHECKPOINT_MARGIN_FLOOR
  printf '%d' $(($1 - margin))
}

# ---------------------------------------------------------------------------
# The parent-only second pass. PROBE cannot answer these three: they need the records in
# FILE order and split at the newest compaction boundary, while PROBE's own dedup is
# `group_by`, which sorts by message.id. Emits one TSV row:
#   crossed_at saving_post_rung fires
#
# `dedup_ordered` keeps each id's LAST record and holds first-appearance order, which is
# the turn numbering `crossed-at` and `SAGE_CHECKPOINT_TURN` both index into; `group_by`
# would number the same turns by id and hand the parent an index it cannot act on.
# `fires` is the once-per-segment test (THE LADDER above): the segment's last record is at
# or past the rung and no earlier one in the segment was. Reading only the segment is what
# makes it stateless — a compaction truncates the evidence, so the next climb is a first
# crossing again, with nothing to acknowledge and nothing to reset.
CHECKPOINT='
def num($x): if ($x|type) == "number" then $x else 0 end;
def occ_of: num(.input_tokens) + num(.cache_creation_input_tokens) + num(.cache_read_input_tokens);
def assistants: [.[] | select((.type? == "assistant") and (.message?.id? != null))];
def dedup_ordered:
  reduce .[] as $r ({order: [], byid: {}};
      .order = (if .byid[$r.message.id] == null then .order + [$r.message.id] else .order end)
    | .byid[$r.message.id] = $r)
  | . as $s | [$s.order[] | $s.byid[.]];
def occupancies: assistants | dedup_ordered | map(.message.usage? // {} | occ_of);

[inputs | fromjson? | select(type == "object")] as $all
| ([$all | to_entries[]
    | select((.value.type? == "system") and (.value.subtype? == "compact_boundary"))
    | .key][-1] // -1) as $cut
| ($all | occupancies) as $occs
| ($all[($cut + 1):] | occupancies) as $seg
| ([$occs | to_entries[] | select(.value >= $rung) | .key + 1][0] // 0) as $crossed
| (if $cpt > 0 then $cpt else $crossed end) as $origin
| [ $crossed,
    ([$occs | to_entries[] | select(.key + 1 > $origin)
      | .value - $floor | if . > 0 then . else 0 end] | add // 0),
    (if ($seg | length) == 0 then 0
     elif ($seg[-1] < $rung) then 0
     elif ([$seg[:-1][] | select(. >= $rung)] | length) > 0 then 0
     else 1 end)
  ] | @tsv
'

# ---------------------------------------------------------------------------
# Parent occupancy sensor. Reuses PROBE above, then CHECKPOINT for the three figures
# PROBE's id-sorted dedup cannot produce.
#
# `--status` reports the parent under discovery too — it is diagnostic, not a trigger, so
# resolving to the wrong session's occupancy costs nothing. The ladder rung below runs
# only under an EXPLICIT <subagents-dir> (DISCOVERY RULE above): a checkpoint
# trigger must never fire on a different session's occupancy.
if [ "$STATUS" -eq 1 ] || [ "$EXPLICIT_DIR" -eq 1 ]; then
  session_dir=$(dirname "$DIR")
  session_id=$(basename "$session_dir")
  parent_transcript="$(dirname "$session_dir")/$session_id.jsonl"

  if [ -f "$parent_transcript" ] && [ -r "$parent_transcript" ]; then
    prow=$("$JQ" -R -n -r "$PROBE" < "$parent_transcript" 2>/dev/null) || prow=""
    if [ -n "$prow" ]; then
      IFS=$'\t' read -r p_done p_spend p_raw p_occ p_ts p_rep p_recs p_tool p_in \
                        p_model p_compact p_pretok p_turns p_occsum <<EOF
$prow
EOF
      # Fail open: a non-numeric figure, no assistant records, or zero occupancy is not
      # an alarm — a missing or unreadable parent transcript already skipped this block.
      case "$p_occ$p_recs" in *[!0-9]*|'') p_occ=""; p_recs=0 ;; esac
      # The appended fields fail open on their own, and to zero rather than to no line:
      # they are diagnostic, and withholding the whole parent line over one of them would
      # cost the caller the occupancy figure the rung is actually about.
      case "$p_compact$p_pretok$p_turns$p_occsum" in
        *[!0-9]*|'') p_compact=0; p_pretok=0; p_turns=0; p_occsum=0 ;;
      esac
      [ -n "$p_model" ] || p_model=unknown
      if [ -n "$p_occ" ] && [ "$p_recs" -ge 1 ] && [ "$p_occ" -gt 0 ]; then
        p_pct=$(pct "$p_occ" "$WINDOW")
        evidence=$(compact_at_of "$p_pretok")
        compact_at="${evidence%% *}"
        at_source="${evidence#* }"
        rung=$(checkpoint_rung_of "$compact_at")

        crow=$("$JQ" -R -n -r --argjson rung "$rung" --argjson cpt "$CHECKPOINT_TURN" \
                 --argjson floor "$RESUME_FLOOR" "$CHECKPOINT" \
                 < "$parent_transcript" 2>/dev/null) || crow=""
        IFS=$'\t' read -r crossed saving fires <<EOF
$crow
EOF
        case "$crossed$saving$fires" in *[!0-9]*|'') crossed=0; saving=0; fires=0 ;; esac
        if [ "$crossed" -gt 0 ]; then crossed_s="$crossed"; else crossed_s=none; fi

        # `window=`, `compact-at=`, `rung=`, `occ-sum=` and `saving-post-rung=` are always
        # RAW figures, never `tok()`-shortened: the caller passed SAGE_WINDOW and must read
        # back exactly what it passed, and the other four go into the ledger and the
        # journal `run` line, where a rounded figure is precision it cannot get back.
        if [ "$STATUS" -eq 1 ]; then
          printf 'sage-watch status %s [parent] "session transcript" model=%s occupancy=%s window=%s compact-at=%s source=%s rung=%s pct=%s%% compact=%s turns=%s occ-sum=%s crossed-at=%s saving-post-rung=%s\n' \
            "$session_id" "$p_model" "$(tok "$p_occ")" "$WINDOW" "$compact_at" "$at_source" \
            "$rung" "$p_pct" "$p_compact" "$p_turns" "$p_occsum" "$crossed_s" "$saving"
        elif [ "$EXPLICIT_DIR" -eq 1 ] && [ "$fires" -eq 1 ]; then
          emit occ-checkpoint checkpoint "$session_id" parent "session transcript" \
            "occupancy=$(tok "$p_occ") window=$WINDOW compact-at=$compact_at source=$at_source rung=$rung pct=${p_pct}%"
        fi
      fi
    fi
  fi
fi

# In ladder mode, per-unit rows do no work at all now — nothing on the ladder reads them.
# Skip the loop entirely so a ladder sample reads only the parent transcript above.
if [ "$STATUS" -eq 1 ]; then
  found=0
  for f in "$DIR"/agent-*.jsonl; do
    [ -f "$f" ] && [ -r "$f" ] || continue
    found=$((found + 1))

    base="${f##*/}"; base="${base%.jsonl}"; id="${base#agent-}"

    atype=""; desc=""
    meta="$DIR/$base.meta.json"
    if [ -r "$meta" ]; then
      metaline=$("$JQ" -r 'if type == "object"
                           then [(.agentType // ""), ((.description // "") | tostring
                                | gsub("[\t\r\n\"]"; " "))] | @tsv
                           else "" end' "$meta" 2>/dev/null)
      IFS=$'\t' read -r atype desc <<EOF
$metaline
EOF
    fi

    row=$("$JQ" -R -n -r "$PROBE" < "$f" 2>/dev/null) || row=""
    # This guard catches jq FAILING, not garbage input: PROBE reads with `fromjson?`, which
    # drops every unparseable line and still emits a full zeros row, so an unparseable
    # transcript prints `records=0` exactly like any other evidence-free one (measured).
    # Fail open either way -- an empty $row is no row and no alarm.
    [ -n "$row" ] || continue

    # Fields 8, 9, 12 and 13 (tool name, tool input, max_pretokens, turns) are absorbed and
    # unused here: PROBE is shared with the parent sensor above and moves only under its own
    # fixture and whole-corpus regression (see the probe block). A unit has no rung and no
    # window of its own, so only its `compact` count and its `model` reach a line.
    IFS=$'\t' read -r done spend raw_spend occ last_ts rep_n recs _ _ \
                      model n_compact _ _ _ <<EOF
$row
EOF

    # Fail open once more: anything non-numeric where a figure belongs is no signal.
    case "$done$spend$raw_spend$occ$last_ts$rep_n$recs" in *[!0-9-]*|'') continue ;; esac
    # The two appended fields fail open to their own defaults instead, for the same reason
    # as on the parent line: they never withhold the row the older figures can still carry.
    case "$n_compact" in ''|*[!0-9]*) n_compact=0 ;; esac
    [ -n "$model" ] || model=unknown

    if [ "$last_ts" -ge 0 ] && [ "$NOW" -ge 0 ]; then idle=$((NOW - last_ts)); else idle=-1; fi

    # Clause (c) of `done`: a transcript colder than the ceiling describes a unit that is
    # gone, not one that is stalling, and nothing on the ladder can reach it. Needs a
    # usable clock — without one there is no presumption either way.
    stale=0
    if [ "$done" -eq 0 ] && [ "$idle" -ge 0 ] && [ "$idle" -gt "$IDLE_CEIL" ]; then stale=1; fi

    if [ "$idle" -ge 0 ]; then idle_s="${idle}s"; else idle_s="-"; fi
    if [ "$done" -eq 1 ]; then done_s=yes
    elif [ "$stale" -eq 1 ]; then done_s=stale
    else done_s=no; fi
    printf 'sage-watch status %s [%s] "%s" done=%s spend=%s raw=%s occupancy=%s idle=%s repeat=%s records=%s compact=%s model=%s\n' \
      "$id" "${atype:-?}" "$desc" "$done_s" "$(tok "$spend")" "$(tok "$raw_spend")" \
      "$(tok "$occ")" "$idle_s" "$rep_n" "$recs" "$n_compact" "$model"
  done

  # The one silent exit --status still had. Once $DIR resolves, an empty glob and an
  # unresolvable layout produced byte-identical output -- exit 0, empty stdout, empty
  # stderr -- so a caller read a working sensor as absent and disabled the only rail with
  # a measured true positive. Measured: --status on a real, readable tasks/ directory
  # returned 0 bytes on both streams, while the guard above named the path. No byte count
  # here on purpose: that message embeds $DIR, so its length tracks the path, and an
  # earlier draft of this comment cited a stale one. Repairing that guard's wording could
  # not reach this gap -- it fires only when $DIR fails [ -d ], [ -r ] or [ -x ], and here
  # $DIR passes all three. stderr and --status only, for the same reason as every
  # diagnostic above: stdout lines become notifications in the hosting loop, which must
  # stay silent. Not an alarm -- exit 0 stands -- and the count is of glob matches that are
  # also readable files, so an unparseable transcript still fails open above while an
  # unreadable one is what the message's "readable" is doing.
  if [ "$found" -eq 0 ]; then
    printf 'sage-watch: %s: resolved, but holds no readable agent-*.jsonl -- the sensor RAN and found no units, which is not "cannot run here"; if units are in flight this is the wrong directory: readlink -f the output_file any dispatch returned -- it is a symlink under tasks/ -- and use its target directory\n' "$DIR" >&2
  fi
fi

# No transcripts is not an alarm either.
exit 0
