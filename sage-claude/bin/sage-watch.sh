#!/usr/bin/env bash
#
# sage-watch.sh — the sage occupancy sensor. Notify only; it never recalls anything.
#
# It reads the in-flight subagent transcripts of one session, watches the single
# parent-occupancy rung — the handover rule in `../SKILL.md` ## Handover — and
# prints ONE LINE PER FIRED RUNG. A healthy sample prints nothing
# and exits 0. It is hosted on `Monitor` with `persistent: true`, where every
# stdout line becomes a notification, so silence is the default output.
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
#                      one ledger line. Empty stdout WITH a line on stderr is NOT that
#                      signal: it names a missing jq, or an explicit directory that does
#                      not resolve, and both are one-line fixes -- fix what it names and
#                      probe again rather than disabling the sensor for the run. The
#                      stderr diagnostics are --status only; ladder mode stays silent.
#
#   SAGE_WINDOW        Env. The live context window, in the same integer/k/K/m/M forms
#                      as below. Defaults to 1006380 (the measured figure in
#                      `../references/harness.md`) when unset, unparseable, or zero.
#                      Drives the parent occupancy rung below — see BLIND SPOTS for
#                      what a wrong value actually does (it is not silence).
#   SAGE_OCC_ACK       Env. Any non-empty value suppresses the parent `occ-30pct` rung
#                      ONLY — not `--status`, which always reports occupancy. Set by a
#                      supervising parent after handover, so the handover alarm stops
#                      repeating once it has been acted on. It is the only rung, so an
#                      ack silences the ladder outright — see THE LADDER below.
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
# The PARENT OCCUPANCY RUNG (occ-30pct — below) runs ONLY when <subagents-dir>
# was passed explicitly. Under discovery it is skipped entirely, unconditionally:
# discovery picks the most recently modified subagents/ directory under the project slug,
# which can belong to a DIFFERENT session than the one asking — measured on this machine:
# 9 candidate directories, top two 1,832s apart — and a handover trigger must
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
#   idle       now minus the last record's timestamp. Reliable for liveness, noisy as a
#              stall proxy (`../references/harness.md` has the base rates). IDLE_CEIL
#              below is set well past the largest returns this corpus has measured.
#   repeat     the largest count of one identical tool call (same name AND same input)
#              across deduplicated records. Diagnostic only now — `--status` reports it,
#              nothing on the ladder acts on it.
#
# ---------------------------------------------------------------------------
# THE LADDER — nothing in it recalls an agent automatically
#
#   rung        action    fires when (and parent occupancy is not presumed acted-on)
#   occ-30pct   handover  parent occupancy >= 30% of SAGE_WINDOW  -> stop launching, run
#                                                                    `../SKILL.md` ## Handover
#
# ONE RUNG, deliberately. There is nothing above `occ-30pct` because a supervising parent
# has no action left to take on its own occupancy: it cannot hand itself over, and there is
# no generation cap for it to run out of (`../SKILL.md` ## Handover, "Supervising past the
# threshold"). The parent rung is a SINGLE line, not per-agent, and it runs only when
# <subagents-dir> was passed explicitly (DISCOVERY RULE above). `occ-30pct` repeats on
# every sample until `SAGE_OCC_ACK` silences it: it is the handover alarm that must survive
# a compaction, and the ack is how it ends once the parent has acted on it.
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
#              raw=496k occupancy=173k idle=2379s repeat=1 records=44
#
# `raw` is the undeduplicated sum, printed only here, only so the dedupe stays auditable.
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
#   sage-watch occ-30pct handover <session-id> [parent] "session transcript" \
#              occupancy=302k window=1006380 pct=30%
#
#   sage-watch status <session-id> [parent] "session transcript" \
#              occupancy=160k window=1006380 pct=16%
#
# `<session-id>` is the session uuid — the basename of the session directory one level
# above `subagents/`, or, under discovery in `--status` mode, whichever session id
# discovery resolved. `--status` prints this line first, ack or not, explicit dir or
# discovered — EXCEPT the five fail-open cases that print no parent line at all: the
# parent transcript is missing, unreadable, or unparseable, it carries no assistant
# records, or its occupancy reads 0. The ladder prints the line only under an explicit
# dir, and only when `occ-30pct` actually fires — which is only when `SAGE_OCC_ACK` is
# unset.
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
#   - The parent occupancy rung trusts `SAGE_WINDOW` completely: it has no way to learn
#     the real window on its own. A window SMALLER than the real one fires EARLY and LOUD —
#     measured: 900k against a real ~1,006,380 fired a false `occ-30pct` at 32% actual
#     occupancy. A window LARGER than the real one
#     fires LATE or never — measured: 10m against the same occupancy read `pct=4%`. Neither
#     direction goes silent on its own; a value that parses to 0 is treated as unparseable
#     and falls back to the 1006380 default (below), so it cannot zero out the percentage.
#     Only discovery mode (above) silences the rung outright. Pass the resolved window
#     explicitly rather than trusting the built-in default.
#   - `occ-30pct` repeats every sample once it fires, by design (THE LADDER above) — that
#     persistence is not a bug to suppress with anything but `SAGE_OCC_ACK`.
#
# FAIL OPEN. An absent signal means no alarm, never a recall.

IDLE_CEIL=21600       # 6h. Past this a not-yet-finished unit is presumed gone, not stalled
OCC_HANDOVER_PCT=30   # rung occ-30pct: parent occupancy as a percent of WINDOW

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
    'SAGE_WINDOW (env): the live context window, default 1006380. SAGE_OCC_ACK (env):' \
    'non-empty suppresses the parent occ-30pct rung. Both documented above.' \
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
# resolve a different session's directory, and a handover trigger must never fire on it.
if [ -n "$DIR" ]; then EXPLICIT_DIR=1; else EXPLICIT_DIR=0; fi
[ -n "$DIR" ] || DIR=$(discover_dir)

# Fail open: no directory, an unreadable one, or no jq to read it with, is not an alarm.
# This is the "probe once at start" answer — a --status call that prints nothing on stdout
# AND nothing on stderr means the sensor cannot run on this layout, and the parent disables
# it and writes one ledger line. Empty stdout WITH a line on stderr is the other case, and
# the split below is what makes the two tellable apart.
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
if [ -z "$DIR" ] || [ ! -d "$DIR" ] || [ ! -r "$DIR" ]; then
  if [ "$STATUS" -eq 1 ] && [ "$EXPLICIT_DIR" -eq 1 ]; then
    printf 'sage-watch: %s: no such readable directory -- the layout is <project>/<session-id>/subagents, one level deeper than <project>/subagents; readlink -f the output_file any dispatch returned -- it is a symlink under tasks/ -- and use its target directory\n' "$DIR" >&2
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
# is readable — safe to `cd` into. The parent occupancy sensor derives the parent transcript
# path from $DIR's own parents (dirname twice); a relative, one-component $DIR (e.g.
# `--status subagents`, run from inside the session directory) derives a garbage path from
# that arithmetic and silently disables the sensor instead of failing loudly. `cd` in a
# subshell so the script's own working directory never moves.
DIR=$(cd "$DIR" && pwd)

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
#
# `last_ts` is the last timestamp on ANY record, not just an assistant one: a tool
# result lands between assistant turns and is the freshest liveness evidence there is.
# `assistant_records` is why a transcript with no assistant record produces no `--status`
# line: no records is no evidence about the agent, and no evidence is never a signal.
# Fields 8 and 9 (tool, input) are read by nothing here. PROBE is deliberately unchanged,
# byte for byte, because the parent occupancy sensor and `--status` share it.

PROBE='
def num($x): if ($x|type) == "number" then $x else 0 end;
def spend_of: num(.input_tokens) + num(.cache_creation_input_tokens) + num(.output_tokens);
def occ_of:   num(.input_tokens) + num(.cache_creation_input_tokens) + num(.cache_read_input_tokens);
def flat: (. // "") | tostring | gsub("[\\t\\r\\n]"; " ");

[inputs | fromjson? | select(type == "object")] as $all
| [$all[] | select((.type? == "assistant") and (.message?.id? != null))] as $asst
| ($asst | group_by(.message.id) | map(.[-1])) as $ded
| [$ded[] | (.message.content? // []) | if type == "array" then .[] else empty end
   | select(.type? == "tool_use")
   | {n: (.name // "?"), i: ((.input // {}) | tojson)}] as $calls
| ($calls | group_by([.n, .i]) | map({n: .[0].n, i: .[0].i, c: length}) | max_by(.c)) as $top
| [$all[] | .timestamp? | select(type == "string")] as $stamps
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
     else ($stamps[-1] | sub("\\.[0-9]+Z$"; "Z") | (fromdateiso8601? // -1)) end),
    ($top.c // 0),
    ($asst | length),
    (if $top == null then "" else ($top.n | flat) end),
    (if $top == null then "" else ($top.i | flat | .[0:70]) end)
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

# ---------------------------------------------------------------------------
# Parent occupancy sensor (issue 2 / SKILL.md ## Handover). Reuses PROBE above; it needs
# no second jq program, since occupancy is field 4 of the same TSV shape.
#
# `--status` reports the parent under discovery too — it is diagnostic, not a trigger, so
# resolving to the wrong session's occupancy costs nothing. The ladder rung below runs
# only under an EXPLICIT <subagents-dir> (DISCOVERY RULE above): a handover
# trigger must never fire on a different session's occupancy.
if [ "$STATUS" -eq 1 ] || [ "$EXPLICIT_DIR" -eq 1 ]; then
  session_dir=$(dirname "$DIR")
  session_id=$(basename "$session_dir")
  parent_transcript="$(dirname "$session_dir")/$session_id.jsonl"

  if [ -f "$parent_transcript" ] && [ -r "$parent_transcript" ]; then
    prow=$("$JQ" -R -n -r "$PROBE" < "$parent_transcript" 2>/dev/null) || prow=""
    if [ -n "$prow" ]; then
      IFS=$'\t' read -r p_done p_spend p_raw p_occ p_ts p_rep p_recs p_tool p_in <<EOF
$prow
EOF
      # Fail open: a non-numeric figure, no assistant records, or zero occupancy is not
      # an alarm — a missing or unreadable parent transcript already skipped this block.
      case "$p_occ$p_recs" in *[!0-9]*|'') p_occ=""; p_recs=0 ;; esac
      if [ -n "$p_occ" ] && [ "$p_recs" -ge 1 ] && [ "$p_occ" -gt 0 ]; then
        p_pct=$(pct "$p_occ" "$WINDOW")
        # `window=` is always the RAW figure, never `tok()`-shortened: the caller passed
        # SAGE_WINDOW and must read back exactly what it passed.
        if [ "$STATUS" -eq 1 ]; then
          printf 'sage-watch status %s [parent] "session transcript" occupancy=%s window=%s pct=%s%%\n' \
            "$session_id" "$(tok "$p_occ")" "$WINDOW" "$p_pct"
        elif [ "$EXPLICIT_DIR" -eq 1 ]; then
          # One rung (THE LADDER above): a supervising parent has no action left to take
          # on its own occupancy, so the ack silences this alarm outright once acted on.
          if [ "$p_pct" -ge "$OCC_HANDOVER_PCT" ] && [ -z "${SAGE_OCC_ACK:-}" ]; then
            emit occ-30pct handover "$session_id" parent "session transcript" \
              "occupancy=$(tok "$p_occ") window=$WINDOW pct=${p_pct}%"
          fi
        fi
      fi
    fi
  fi
fi

# In ladder mode, per-unit rows do no work at all now — nothing on the ladder reads them.
# Skip the loop entirely so a ladder sample reads only the parent transcript above.
if [ "$STATUS" -eq 1 ]; then
  for f in "$DIR"/agent-*.jsonl; do
    [ -f "$f" ] && [ -r "$f" ] || continue

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
    # An unparseable transcript yields nothing. Fail open: no row, no alarm.
    [ -n "$row" ] || continue

    # Fields 8 and 9 (tool name, tool input) are absorbed and unused: PROBE is frozen
    # byte-identical, and nothing left in this script reads them.
    IFS=$'\t' read -r done spend raw_spend occ last_ts rep_n recs _ _ <<EOF
$row
EOF

    # Fail open once more: anything non-numeric where a figure belongs is no signal.
    case "$done$spend$raw_spend$occ$last_ts$rep_n$recs" in *[!0-9-]*|'') continue ;; esac

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
    printf 'sage-watch status %s [%s] "%s" done=%s spend=%s raw=%s occupancy=%s idle=%s repeat=%s records=%s\n' \
      "$id" "${atype:-?}" "$desc" "$done_s" "$(tok "$spend")" "$(tok "$raw_spend")" \
      "$(tok "$occ")" "$idle_s" "$rep_n" "$recs"
  done
fi

# No transcripts is not an alarm either.
exit 0
