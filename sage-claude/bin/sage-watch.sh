#!/usr/bin/env bash
#
# sage-watch.sh — the sage watchdog probe. Notify only; it never recalls anything.
#
# It reads the in-flight subagent transcripts of one session, walks the ladder in
# `../SKILL.md` Step 4 — the arithmetic behind each signal is `../references/harness.md`,
# `## Transcripts and the token arithmetic` — and prints ONE LINE PER FIRED RUNG. A healthy sample prints
# nothing and exits 0. It is hosted on `Monitor` with `persistent: true`, where every
# stdout line becomes a notification, so silence is the default output.
#
# It never writes a file, never calls `TaskStop`, never kills a process, and never
# touches a transcript. It reports; the parent acts.
#
# ---------------------------------------------------------------------------
# USAGE
#
#   sage-watch.sh [<subagents-dir>|-] [<estimates-file>]
#   sage-watch.sh --status [<subagents-dir>|-] [<estimates-file>]
#   sage-watch.sh --help
#
#   <subagents-dir>    The session's `subagents/` directory. Omit it, or pass `-`, to
#                      discover it (rule below).
#   <estimates-file>   Optional. Per-unit token estimates, so the spend rungs are
#                      relative to each row's own estimate (format below).
#   --status           Diagnostic mode. Prints one line per agent with every figure,
#                      fires no rungs. This is the "probe once at start" call: if it
#                      prints nothing, the watchdog cannot run on this layout and the
#                      parent disables it silently and writes one ledger line.
#
# Exit status is 0 in every normal case, including a missing directory, no transcripts,
# malformed JSON, a half-written final line, and a transcript with no assistant records.
# Exit 2 means the ARGUMENTS were unusable (too many, or an unreadable estimates file);
# nothing was inspected.
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
# ---------------------------------------------------------------------------
# ESTIMATES FILE FORMAT
#
# One row per unit. Blank lines and `#` comments ignored. The LAST whitespace-separated
# field is the estimate; everything before it is the key, so keys may contain spaces:
#
#     # key                          estimate
#     ac00f3c9804d0df39              240k        # agent id, with or without `agent-`
#     implementer                    250k        # agentType from the .meta.json sidecar
#     Write the watchdog probe       120000      # exact description from the sidecar
#
# Estimate forms: a bare integer, or an integer with a `k`/`K` (x1000) or `m`/`M`
# (x1000000) suffix. A row that parses as neither is ignored.
#
# Key match precedence per agent, first hit wins: agent id, then description, then
# agentType. No estimate for a unit -> the 150k floor. Every estimate is floored at
# 150k, so a small row cannot make the rungs fire on ordinary work.
#
# ---------------------------------------------------------------------------
# THE ARITHMETIC — this is where a naive build goes wrong
#
# THE REFERENCE CORPUS, named once because every figure below is measured on it and on
# nothing else: 212 transcripts, measured 2026-08-18 — every
# `<session>/subagents/agent-*.jsonl` under `~/.claude/projects/`, NON-RECURSIVE, across
# all projects, `workflows/wf_*/` excluded. That is exactly the population this script's
# own glob can read, and it is the same one `../references/harness.md` quotes; the two
# must agree, figure for figure. A recursive sweep instead drags in the `wf_*` sidecars
# of the deleted `Workflow` backend — units this probe never opens and sage never
# produces — and moves every number below. Symlinked duplicates are counted once. These
# are date-stamped because the corpus grows and old transcripts are pruned: re-measure
# before betting a threshold on them.
#
# Assistant records are STREAMING PARTIALS: one `message.id` is written many times with
# growing `usage`. Summing raw inflates spend, so a rail built the obvious way fires at a
# fraction of real spend and alarms on healthy agents constantly. Always
# `group_by(.message.id) | map(.[-1])` before any sum.
#
# The inflation is a DISTRIBUTION, not a constant. Raw/deduplicated over the reference
# corpus (212 transcripts, 2026-08-18): min 1.00x, p10 1.66x, p25 1.88x, p50 2.14x,
# p75 2.53x, p90 2.94x, p99 4.22x, max 4.26x; mean 2.26x; corpus aggregate (all raw /
# all dedup) 2.01x. A single transcript can land anywhere in that range, which is exactly
# why the dedup is not optional and why no single multiplier can stand in for it.
#
#   done       the unit is presumed FINISHED, and a finished unit fires nothing. Read off
#              the FINAL assistant record in FILE order (not the `group_by` array's last
#              element, which is sorted by id), and not off `any` record. Three clauses,
#              any one sufficient:
#                a. its `stop_reason` is `end_turn` or `stop_sequence`;
#                b. its content carries a `text` block and no `tool_use` block — a turn
#                   that ended in prose with no call pending is over, whatever the
#                   `stop_reason` field says;
#                c. `idle` is past IDLE_CEIL — evidence this cold describes a unit that is
#                   gone, not one that is stalling, and there is nothing left to steer.
#              Clause (b) is the load-bearing one. Over the reference corpus (212
#              transcripts, 2026-08-18), 41 (19.3%) carry `end_turn` NOWHERE: their final
#              record reads `null` 34 times, `tool_use` 5, `stop_sequence` 2. An
#              `any(end_turn)` test called every one of them still-running, forever, and
#              at the 60s Monitor cadence that turns roughly one finished unit in five
#              into a permanent notification: that superseded rule covers 171/212 (80.7%)
#              where clauses (a)+(b) cover 204/212 (96.2%). Two tempting explanations are
#              both wrong, measured on the same corpus: deduplication loses an `end_turn`
#              in 0 of 212, and judging the final record instead of `any` gives the
#              identical 171 — the field is simply absent from the file. What makes (b) a
#              strict superset rather than a looser guess: all 171 `end_turn` finals end
#              in a text-only content array, and so do 33 of the 41 that lack the field.
#              Clause (c) covers the residue that leaves — 8 transcripts (3.8%), 7 ending
#              in a `tool_use` and one truncated mid-`thinking`. That shape looks the same
#              for a unit running a long tool right now and a unit killed mid-call days
#              ago; only elapsed time separates the two, so only there does time get a
#              vote — and on 3.8% of the corpus, not the fifth an `any` test would hand it.
#   spend      sum of `input + cache_creation + output` over DEDUPLICATED records.
#              Excludes `cache_read` — re-read context is not spend.
#   occupancy  `input + cache_creation + cache_read` on the SINGLE MOST RECENT assistant
#              record. Includes `cache_read` — those tokens are in the window.
#              Point-in-time, never a sum. Reported by --status; fires no rung here.
#   idle       now minus the last record's timestamp. Reliable for liveness, noisy as a
#              stall proxy — over the reference corpus (212 transcripts, 2026-08-18) 39%
#              of the runs this predicate calls done still contain a gap over 120s, so
#              idle is unusable below 300s; the rungs sit at 600s and 1800s, where the
#              base rates fall to 5% and 1%. Ceiling above: p99 of the per-transcript
#              largest gap is 3764s and the largest gap any transcript came back from is
#              13195s (3.7h, and that one is machine sleep, not work). IDLE_CEIL sits at
#              21600s — 12x the top rung, 5.7x that p99, and 1.6x the largest observed
#              return — so a unit past it is called gone, not stalled.
#   repeat     the largest count of one identical tool call (same name AND same input)
#              across deduplicated records. Sharp distribution over the reference corpus
#              (2026-08-18): p90 is 1, p99 is 3, max 5 — which is why REPEAT_MIN sits at 4.
#
# ---------------------------------------------------------------------------
# THE LADDER — nothing in it recalls an agent automatically
#
#   rung        action    fires when (and the unit is not presumed finished)
#   idle-600    log       idle > 600s
#   idle-1800   message   idle > 1800s          -> SendMessage asking for a one-liner
#   tool-repeat message   same tool call >= 4x  -> SendMessage naming the repeated call
#   spend-2x    log       spend > 2x estimate
#   spend-4x    message   spend > 4x estimate   -> SendMessage: report what you have now
#   spend-6x    surface   spend > 6x estimate   -> surface to the user; TaskStop only on
#                                                  their word
#
# Only the HIGHEST idle rung and the HIGHEST spend rung fire per agent, so one agent
# emits at most three lines. `tool-repeat` is independent of the other two.
#
# The other arm of that last rung in `../SKILL.md` Step 4 — "no reply 600s after two
# messages" — needs state this script does not have; it never saw the messages. The
# parent tracks that arm.
#
# OUTPUT LINE SHAPE, fixed field order:
#
#   sage-watch <rung> <action> <agent-id> [<agentType>] "<description>" <figures...>
#   sage-watch spend-4x message a1cc4e647a6d9 [implementer] "Write the probe" \
#              spend=640k est=150k ratio=4.2x
#
# Grep a rung name to select; field 2 is the rung, field 3 the action, field 4 the id.
#
# `--status` uses the same first four fields with the rung `status` and no action, then
# every figure as key=value:
#
#   sage-watch status a37cd95f4 [Explore] "Gate blast radius" done=yes spend=205k \
#              raw=496k occupancy=173k idle=2379s repeat=1 records=44 est=150k
#
# `raw` is the undeduplicated sum, printed only here, only so the dedupe stays auditable.
# `done` takes three values: `yes` (clause a or b), `stale` (clause c — the transcript is
# older than IDLE_CEIL, so the unit is presumed gone), and `no`. Both `yes` and `stale`
# fire nothing; only `no` walks the ladder.
#
# BLIND SPOTS, stated rather than hidden: no signal here detects the confident-wrong
# agent that burns a normal budget and returns a fluent fabrication, correct-but-
# irrelevant work, late-degrading reasoning, or machine sleep — which is indistinguish-
# able from a stall. The verification layer is the only defence for the first.
#
# What the `done` predicate specifically cannot see, since it decides on the last record
# written rather than on any statement of intent:
#   - A unit that stalls just after emitting a text block and before its tool call lands
#     in the same turn reads as finished under clause (b). While the unit is alive this
#     self-corrects at the next sample; if it hangs in exactly that window it is silent
#     for good. Seven of the eight non-text-terminal transcripts in the reference corpus
#     stall inside a tool call instead, which is the shape clause (b) leaves alone.
#   - A unit that returns a complete, wrong or empty answer is `done` — the predicate
#     reads shape, never content.
#   - A unit genuinely hung inside a tool call for more than IDLE_CEIL is called gone and
#     stops being reported. That is deliberate: `SendMessage` drains at the receiver's
#     next tool round, and a unit with no tool round in six hours has none coming, so the
#     probe has no actionable claim left to make. Machine sleep lands here too, and going
#     quiet after it is the fail-open answer.
#   - `stop_reason` values outside `end_turn`/`stop_sequence`/`tool_use`/null are all but
#     absent from the reference corpus, and untested where it counts: sweeping every
#     assistant `stop_reason` in it (2026-08-18), `max_tokens` appears exactly once and
#     mid-transcript — never as the FINAL record this predicate actually reads, whose only
#     observed values are those four. `max_tokens` on a text-only final would read as
#     finished, which is right in effect — a truncated unit is not going to continue.
#
# FAIL OPEN. An absent signal means no alarm, never a recall.

IDLE_LOG=600          # rung idle-600
IDLE_MSG=1800         # rung idle-1800
IDLE_CEIL=21600       # 6h. Past this a not-yet-finished unit is presumed gone, not stalled
REPEAT_MIN=4          # rung tool-repeat
EST_FLOOR=150000      # every estimate is floored here

JQ=$(command -v jq 2>/dev/null)
[ -n "$JQ" ] || JQ=/usr/bin/jq   # fallback for a stripped PATH; jq ships at /usr/bin on macOS

usage() {
  # The header above is the manual; this is the reminder.
  printf '%s\n' \
    'sage-watch.sh [<subagents-dir>|-] [<estimates-file>]   walk the ladder, print fired rungs' \
    'sage-watch.sh --status [<dir>|-] [<estimates>]         one line per agent, fires nothing' \
    'sage-watch.sh --help                                   this reminder' \
    '' \
    'Estimates file: one row per unit, `<agent-id | agentType | description>  <tokens>`,' \
    'the estimate last, `k`/`m` suffixes allowed, `#` comments ignored, 150k floor.' \
    'Exit 0 always; exit 2 only when the arguments themselves are unusable.'
}

# ---------------------------------------------------------------------------
# Arguments

STATUS=0
DIR=""
EST_FILE=""
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
        2) EST_FILE="$arg" ;;
        *) printf 'sage-watch: too many arguments\n' >&2; exit 2 ;;
      esac
      ;;
  esac
done

if [ -n "$EST_FILE" ] && [ ! -r "$EST_FILE" ]; then
  printf 'sage-watch: estimates file not readable: %s\n' "$EST_FILE" >&2
  exit 2
fi

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

[ -n "$DIR" ] || DIR=$(discover_dir)

# Fail open: no directory, an unreadable one, or no jq to read it with, is not an alarm.
# This is the "probe once at start" answer — a --status call that prints nothing means the
# watchdog cannot run on this layout, and the parent disables it and writes one ledger line.
if [ -z "$DIR" ] || [ ! -d "$DIR" ] || [ ! -r "$DIR" ] || [ ! -x "$JQ" ]; then exit 0; fi

# ---------------------------------------------------------------------------
# Estimates. Parsed once into two parallel indexed arrays (bash 3.2 has no
# associative arrays). Lookups are a linear scan over a handful of rows.

EST_KEYS=()
EST_VALS=()

parse_estimates() {
  local line key val num mult
  while IFS= read -r line || [ -n "$line" ]; do
    line="${line%%#*}"                       # strip comment
    line="${line//$'\t'/ }"                  # tabs become spaces
    while [ "$line" != "${line//  / }" ]; do line="${line//  / }"; done
    line="${line# }"; line="${line% }"       # trim
    case "$line" in ''|' ') continue ;; esac
    case "$line" in *' '*) : ;; *) continue ;; esac   # need a key AND a value
    val="${line##* }"
    key="${line% *}"
    mult=1
    case "$val" in
      *k|*K) num="${val%?}"; mult=1000 ;;
      *m|*M) num="${val%?}"; mult=1000000 ;;
      *)     num="$val" ;;
    esac
    case "$num" in ''|*[!0-9]*) continue ;; esac      # unparseable row: ignore
    EST_KEYS[${#EST_KEYS[@]}]="$key"
    EST_VALS[${#EST_VALS[@]}]=$((num * mult))
  done < "$1"
}

[ -n "$EST_FILE" ] && parse_estimates "$EST_FILE"

# Exact lookup of one key. Echoes the token count, or nothing.
est_lookup() {
  local want="$1" i=0 n=${#EST_KEYS[@]}
  while [ "$i" -lt "$n" ]; do
    if [ "${EST_KEYS[$i]}" = "$want" ]; then printf '%s' "${EST_VALS[$i]}"; return 0; fi
    i=$((i + 1))
  done
  return 1
}

# Precedence: agent id, then description, then agentType. Floored at EST_FLOOR.
estimate_for() {
  local id="$1" desc="$2" type="$3" v=""
  v=$(est_lookup "$id") || v=$(est_lookup "agent-$id") \
    || { [ -n "$desc" ] && v=$(est_lookup "$desc"); } \
    || { [ -n "$type" ] && v=$(est_lookup "$type"); } \
    || v=""
  case "$v" in ''|*[!0-9]*) v=0 ;; esac
  [ "$v" -ge "$EST_FLOOR" ] || v=$EST_FLOOR
  printf '%s' "$v"
}

# ---------------------------------------------------------------------------
# Formatting helpers

# 1250000 -> 1.2M ; 612345 -> 612k ; 900 -> 900
tok() {
  if [ "$1" -ge 1000000 ]; then
    printf '%d.%dM' $(($1 / 1000000)) $(($1 % 1000000 / 100000))
  elif [ "$1" -ge 1000 ]; then printf '%dk' $(($1 / 1000))
  else printf '%d' "$1"; fi
}

# 640000 150000 -> 4.2x   (integer math; no bc, no awk)
ratio() {
  local r
  r=$(( $1 * 10 / $2 ))
  printf '%d.%dx' $((r / 10)) $((r % 10))
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
# `assistant_records` gates the ladder — a transcript with no assistant record carries
# no evidence about the agent at all, and no evidence is never an alarm.

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

# No usable clock means no usable idle figure. The spend and repeat rungs still stand.
NOW=$(date +%s 2>/dev/null)
case "$NOW" in ''|*[!0-9]*) NOW=-1 ;; esac

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

  IFS=$'\t' read -r done spend raw_spend occ last_ts rep_n recs rep_tool rep_in <<EOF
$row
EOF

  # Fail open once more: anything non-numeric where a figure belongs is no signal.
  case "$done$spend$raw_spend$occ$last_ts$rep_n$recs" in *[!0-9-]*|'') continue ;; esac

  est=$(estimate_for "$id" "$desc" "$atype")

  if [ "$last_ts" -ge 0 ] && [ "$NOW" -ge 0 ]; then idle=$((NOW - last_ts)); else idle=-1; fi

  # Clause (c) of `done`: a transcript colder than the ceiling describes a unit that is
  # gone, not one that is stalling, and nothing on the ladder can reach it. Needs a
  # usable clock — without one there is no presumption either way.
  stale=0
  if [ "$done" -eq 0 ] && [ "$idle" -ge 0 ] && [ "$idle" -gt "$IDLE_CEIL" ]; then stale=1; fi

  if [ "$STATUS" -eq 1 ]; then
    if [ "$idle" -ge 0 ]; then idle_s="${idle}s"; else idle_s="-"; fi
    if [ "$done" -eq 1 ]; then done_s=yes
    elif [ "$stale" -eq 1 ]; then done_s=stale
    else done_s=no; fi
    printf 'sage-watch status %s [%s] "%s" done=%s spend=%s raw=%s occupancy=%s idle=%s repeat=%s records=%s est=%s\n' \
      "$id" "${atype:-?}" "$desc" "$done_s" "$(tok "$spend")" "$(tok "$raw_spend")" \
      "$(tok "$occ")" "$idle_s" "$rep_n" "$recs" "$(tok "$est")"
    continue
  fi

  # No assistant record means no evidence about this agent. No evidence, no alarm.
  [ "$recs" -ge 1 ] || continue

  # A unit presumed finished — by its final record, or by the idle ceiling — fires nothing.
  [ "$done" -eq 1 ] && continue
  [ "$stale" -eq 1 ] && continue

  # Idle — highest rung only.
  if [ "$idle" -gt "$IDLE_MSG" ]; then
    emit idle-1800 message "$id" "$atype" "$desc" "idle=${idle}s"
  elif [ "$idle" -gt "$IDLE_LOG" ]; then
    emit idle-600 log "$id" "$atype" "$desc" "idle=${idle}s"
  fi

  # Repeated identical tool call — independent of the idle and spend rungs.
  if [ "$rep_n" -ge "$REPEAT_MIN" ]; then
    emit tool-repeat message "$id" "$atype" "$desc" \
      "count=$rep_n tool=${rep_tool:-?} input=${rep_in}"
  fi

  # Spend — highest rung only.
  if [ "$spend" -gt $((est * 6)) ]; then
    emit spend-6x surface "$id" "$atype" "$desc" \
      "spend=$(tok "$spend") est=$(tok "$est") ratio=$(ratio "$spend" "$est")"
  elif [ "$spend" -gt $((est * 4)) ]; then
    emit spend-4x message "$id" "$atype" "$desc" \
      "spend=$(tok "$spend") est=$(tok "$est") ratio=$(ratio "$spend" "$est")"
  elif [ "$spend" -gt $((est * 2)) ]; then
    emit spend-2x log "$id" "$atype" "$desc" \
      "spend=$(tok "$spend") est=$(tok "$est") ratio=$(ratio "$spend" "$est")"
  fi
done

# No transcripts is not an alarm either.
exit 0
