#!/usr/bin/env bash
#
# RUN BLOCK
# Advisory PostToolBatch hook. Not run by hand. Register it as:
#   "hooks": { "PostToolBatch": [ { "hooks": [ { "type": "command",
#     "command": "~/.claude/skills/sage/bin/sage-clock.sh" } ] } ] }
# It reads the run ledger and injects one line, `sage elapsed <m>m / <target>m`,
# into the parent's context. It never stops the loop, never writes a file, and
# always exits 0.
#   sage-clock.sh --help       print usage
#   sage-clock.sh --self-test  run the built-in fixtures; exit 0 only if all pass
# END RUN BLOCK
#
# ---------------------------------------------------------------------------
# MAINTAINER MANUAL
#
# WHY. An elapsed-time line (`elapsed 340s / 1200s`) made small agent teams finish
# considerably sooner at comparable quality (Opus 5.5 prompting guide). The clock is
# advisory: nothing stops at the target.
#
# INPUT. One hook payload on stdin. Fields read: `session_id`, `cwd`, `agent_id`.
# Uses jq when on PATH or at /usr/bin/jq; else a sed fallback for flat string fields.
#
# LEDGER. `<cwd>/.claude/plans/sage-ledger-<session_id>.md`. Lines read:
#   `Started: <UTC ISO-8601>`   `Wall target: <n> min`
# and the marker `pending — written at Step 6` in the Run record. Once Step 6
# overwrites that marker the run is closed and the clock goes quiet.
#
# OUTPUT. Either nothing, or exactly:
#   {"hookSpecificOutput":{"hookEventName":"PostToolBatch","additionalContext":"sage elapsed 5m / 20m"}}
# This script must never print `decision: "block"` or `continue: false`: either
# would stop the agentic loop.
#
# SILENT CASES (all exit 0): unparseable stdin, no session_id or cwd, a non-empty
# agent_id (only the parent gets the clock), missing ledger, missing Started or
# target line, closed Run record, timestamp neither GNU nor BSD `date` can parse.
#
# BLIND SPOT. --self-test checks this script's logic. It cannot detect a payload
# field renamed upstream: every lookup would come back empty and the clock would
# go quiet, which is the fail-open direction.

JQ=jq
command -v "$JQ" >/dev/null 2>&1 || JQ=/usr/bin/jq

RUN_OPEN_MARKER='pending — written at Step 6'
UTC_FORMAT='%Y-%m-%dT%H:%M:%SZ'

usage() {
  sed -n '2,/^# END RUN BLOCK/p' "$0" | sed 's/^# \{0,1\}//' | sed '1d;$d'
}

hasJq() {
  [ -x "$JQ" ] || command -v "$JQ" >/dev/null 2>&1
}

# payloadField <payload> <name> -> the flat string field, or empty
payloadField() {
  if hasJq; then
    printf '%s' "$1" | "$JQ" -r --arg k "$2" 'if (.[$k] | type) == "string" then .[$k] else empty end' 2>/dev/null
  else
    printf '%s' "$1" | sed -n 's/.*"'"$2"'"[ ]*:[ ]*"\([^"]*\)".*/\1/p' | head -n 1
  fi
}

# ledgerValue <ledger> <label> -> text after `<label>:` on the first such line
ledgerValue() {
  sed -n 's/^[-* ]*'"$2"':[ ]*\(.*\)$/\1/p;/^[-* ]*'"$2"':/q' "$1"
}

isRunOpen() {
  grep -q -F "$RUN_OPEN_MARKER" "$1"
}

# epochOf <utc-iso> -> epoch seconds, or empty when neither date flavour parses it
epochOf() {
  date -u -d "$1" +%s 2>/dev/null \
    || date -j -u -f "$UTC_FORMAT" "$1" +%s 2>/dev/null
}

# targetMinutes <ledger> -> digits from `Wall target: <n> min`, or empty
targetMinutes() {
  ledgerValue "$1" 'Wall target' | sed -n 's/^\([0-9][0-9]*\)[ ]*min.*/\1/p;s/^\([0-9][0-9]*\)[ ]*min$/\1/p' | head -n 1
}

# clockLine <payload> -> the hook JSON, or nothing
clockLine() {
  payload="$1"
  session=$(payloadField "$payload" session_id)
  dir=$(payloadField "$payload" cwd)
  [ -n "$session" ] && [ -n "$dir" ] || return 0
  case "$session" in */*) return 0 ;; esac
  [ -z "$(payloadField "$payload" agent_id)" ] || return 0

  ledger="$dir/.claude/plans/sage-ledger-$session.md"
  [ -f "$ledger" ] || return 0
  isRunOpen "$ledger" || return 0

  started=$(ledgerValue "$ledger" Started | head -n 1)
  target=$(targetMinutes "$ledger")
  [ -n "$started" ] && [ -n "$target" ] || return 0

  startEpoch=$(epochOf "$started")
  [ -n "$startEpoch" ] || return 0

  elapsedSeconds=$(( $(date +%s) - startEpoch ))
  [ "$elapsedSeconds" -ge 0 ] || elapsedSeconds=0
  printf '{"hookSpecificOutput":{"hookEventName":"PostToolBatch","additionalContext":"sage elapsed %sm / %sm"}}\n' \
    $(( elapsedSeconds / 60 )) "$target"
}

# ---------------------------------------------------------------------------
# self-test

writeLedger() {
  # writeLedger <dir> <session> <started-line> <target-line> <run-record-line>
  mkdir -p "$1/.claude/plans"
  {
    printf '## Plan\n'
    [ -z "$3" ] || printf '%s\n' "$3"
    [ -z "$4" ] || printf '%s\n' "$4"
    printf '\n## Run record\n%s\n' "$5"
  } > "$1/.claude/plans/sage-ledger-$2.md"
}

payloadFor() {
  printf '{"session_id":"%s","cwd":"%s","hook_event_name":"PostToolBatch"%s}' "$1" "$2" "$3"
}

# expectCase <name> <stdin> <want: line|empty>
expectCase() {
  name="$1"; stdin="$2"; want="$3"
  out=$(printf '%s' "$stdin" | bash "$0"); status=$?
  if [ "$status" -ne 0 ]; then
    printf 'FAIL  %s (exit %s)\n' "$name" "$status"; selfTestFailed=1; return
  fi
  if [ "$want" = empty ]; then
    [ -z "$out" ] && verdict=ok || verdict=FAIL
  else
    verdict=FAIL
    if [ "$(printf '%s\n' "$out" | wc -l)" -eq 1 ] && printf '%s' "$out" | grep -q 'sage elapsed'; then
      verdict=ok
      if hasJq; then
        printf '%s' "$out" | "$JQ" -e '.hookSpecificOutput.hookEventName == "PostToolBatch" and (.hookSpecificOutput.additionalContext | test("^sage elapsed [0-9]+m / 20m$"))' >/dev/null 2>&1 || verdict=FAIL
      fi
    fi
  fi
  [ "$verdict" = ok ] || selfTestFailed=1
  printf '%s  %s\n' "$verdict" "$name"
}

selfTest() {
  selfTestFailed=0
  root=$(mktemp -d) || return 1
  trap 'rm -rf "$root"' EXIT
  startedLine="Started: $(date -u -d '-7 minutes' +"$UTC_FORMAT" 2>/dev/null || date -u -v-7M +"$UTC_FORMAT")"
  targetLine='Wall target: 20 min (advisory)'
  pending='OUTCOME: pending — written at Step 6'

  writeLedger "$root" live "$startedLine" "$targetLine" "$pending"
  writeLedger "$root" closed "$startedLine" "$targetLine" 'OUTCOME: done'
  writeLedger "$root" notarget "$startedLine" '' "$pending"
  writeLedger "$root" nostart '' "$targetLine" "$pending"
  writeLedger "$root" badstamp 'Started: not-a-date' "$targetLine" "$pending"

  expectCase "ledger with Started and target -> one line" "$(payloadFor live "$root" '')" line
  expectCase "no ledger -> empty" "$(payloadFor absent "$root" '')" empty
  expectCase "agent_id present -> empty" "$(payloadFor live "$root" ',"agent_id":"a1","agent_type":"explorer"')" empty
  expectCase "closed Run record -> empty" "$(payloadFor closed "$root" '')" empty
  expectCase "missing target -> empty" "$(payloadFor notarget "$root" '')" empty
  expectCase "missing Started -> empty" "$(payloadFor nostart "$root" '')" empty
  expectCase "unparseable timestamp -> empty" "$(payloadFor badstamp "$root" '')" empty
  expectCase "garbage stdin -> empty" 'this is not json' empty
  expectCase "empty stdin -> empty" '' empty
  return "$selfTestFailed"
}

case "${1:-}" in
  --help|-h) usage; exit 0 ;;
  --self-test) selfTest; exit $? ;;
  "") : ;;
  *) printf 'sage-clock: unknown option %s\n' "$1" >&2; exit 0 ;;
esac

clockLine "$(cat)" 2>/dev/null
exit 0
