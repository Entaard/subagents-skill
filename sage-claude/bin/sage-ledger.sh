#!/usr/bin/env bash
# sage-ledger.sh — the one writer of a sage run ledger. Call this instead of editing the
# ledger by hand.
#
# RUN BLOCK. The ledger path is always explicit, never discovered.
#
#   sage-ledger.sh next-path <plans-dir> <session-id>   prints the ledger path a new run uses
#   sage-ledger.sh init <ledger> <title>            (stdin lines = the field block)
#   sage-ledger.sh unit <ledger> <id> <key>=<value>...
#   sage-ledger.sh finding <ledger> <id> <key>=<value>...
#   sage-ledger.sh decision <ledger> <kind> <decision> [<reason>]     prints the D-id
#   sage-ledger.sh restamp <ledger> [step=..] [next=..] [lease=..] [baseline=..] [-- <file>...]
#   sage-ledger.sh record <ledger>                  (stdin = the Run record body)
#   sage-ledger.sh close [--keep-lint] <ledger> [<subagents-dir>]   (stdin = memory lines, `<date> run|obs ...`)
#   sage-ledger.sh --self-test | --help
#
# Exit 0 done, 1 refused or a section/table is missing (nothing written; one stderr line),
# 2 usage error or a rejected key/value (nothing written). `close` exits 1, and appends no
# memory line, when the Run record is still pending or the lint printed a violation. Fix the
# violation and close again. `--keep-lint` appends anyway, for a violation you name in the
# run record with the reason it stands.
#
# The first run in a session uses `sage-ledger-<session-id>.md`, a later one
# `sage-ledger-<session-id>-<n>.md` (lowest free n from 2). `init` refuses an existing file.
# Every write builds a temp file beside the ledger, then `mv`s it over: atomic.
# Everything below is the maintainer's manual.
# END RUN BLOCK
#
# Schema: `### Plan` (field lines, then the unit table), `### Resume state`, `### Decisions`,
# `### Findings`, `### Run record`. `sage-lint.sh` is the checker of what this writes.
#
# Cell values: newlines and tabs become spaces, and a literal `|` is written `\|`; the lint
# reads `\|` as a pipe inside a cell. Table keys are the header names, case-insensitive.
# Upsert keys the row by its first cell; an update merges only the named cells.
#
# Seams: `close` reads memory lines from stdin, appends by `>>` to
# `$SAGE_MEMORY_DIR/runs.log` (2nd field `run`) or `inbox.log` (`obs`); the directory
# defaults to `~/.claude/skills/sage/memory`. It runs the sibling `sage-lint.sh` and, when a
# directory is given, the sibling `sage-watch.sh --status <dir>` once.
#
# Blind spot: it checks a value's shape (enum words, kinds), never whether it is true.

export LC_ALL=C

HERE=$(cd "$(dirname "$0")" && pwd)
SELF="$HERE/$(basename "$0")"
PENDING_TEXT='pending — written at Step 6'
UNIT_KEYS='id unit done-when rw agent flow state agentid evidence'
FINDING_KEYS='id severity stage author location triage evidence'
DECISION_KINDS='assumption deviation dropped discarded open reopen rail-1'
STATE_WORDS='planned running reported blocked failed abandoned inline'
SEVERITIES='blocker major minor'
STAGES='frame plan r1 r2+ final-run post-close user'
AUTHORS='parent unit pre-existing'
MEMORY_DIR_DEFAULT="$HOME/.claude/skills/sage/memory"

# One awk prelude shared by every program below. Cells are kept in their raw, escaped form:
# `\|` is hidden behind \001 while splitting and is never restored, so a rewritten row
# carries the escape it came with.
AWK_LIB='
  function trim(s) { sub(/^[ \t]+/, "", s); sub(/[ \t\r]+$/, "", s); return s }
  function is_heading(line) { return (line ~ /^###?[ \t]/) }
  function heading_of(line,   h) { h = line; sub(/^###?[ \t]+/, "", h); return trim(h) }
  function is_fence(line) { return (trim(line) ~ /^```/) }
  function split_raw(line, cells) { gsub(/\\\|/, "\001", line); return split(line, cells, "|") }
  function fail(msg) { print "sage-ledger: " msg > "/dev/stderr"; failed = 1; exit 1 }
'

usage() {
  sed -n '/^# RUN BLOCK/,/^# END RUN BLOCK/p' "$SELF" | sed -e '/END RUN BLOCK/d' -e 's/^# \{0,1\}//'
}

die() {  # die <exit-code> <message>
  printf 'sage-ledger: %s\n' "$2" >&2
  exit "$1"
}

in_list() {  # in_list <word> <space-separated-list>
  case " $2 " in *" $1 "*) return 0 ;; *) return 1 ;; esac
}

lowercase() { printf '%s' "$1" | tr 'A-Z' 'a-z'; }

cell_text() {  # cell_text <value>  — one line, pipes escaped
  local v=$1
  v=${v//$'\n'/ }
  v=${v//$'\t'/ }
  v=${v//|/\\|}
  printf '%s' "$v"
}

require_ledger() {
  [ -f "$1" ] || die 1 "$1: ledger not found"
}

# swap_in <ledger> <tmp> — the atomic step of every write.
swap_in() {
  mv "$2" "$1"
}

# rewrite_ledger <ledger> <awk-args...> — runs awk over the ledger into a sibling temp file
# and moves it over the ledger only when awk succeeds.
rewrite_ledger() {
  local ledger=$1 tmp
  shift
  tmp=$(mktemp "$(dirname "$ledger")/.sage-ledger.XXXXXX") || die 1 "cannot create a temp file beside $ledger"
  if awk "$@" "$ledger" >"$tmp"; then
    swap_in "$ledger" "$tmp"
  else
    rm -f "$tmp"
    return 1
  fi
}

# ---------------------------------------------------------------------------
# init

cmd_init() {
  [ $# -eq 2 ] || die 2 "usage: init <ledger> <title>"
  local ledger=$1 title=$2 fields="" tmp
  [ ! -e "$ledger" ] || die 1 "$ledger exists; init refuses to overwrite$(next_path_hint "$ledger")"
  mkdir -p "$(dirname "$ledger")" || die 1 "cannot create the directory of $ledger"
  if [ ! -t 0 ]; then
    fields=$(sed -e '/^Started:/d' | awk 'NF { seen = 1 } seen')
  fi
  [ -n "$fields" ] || fields=$(empty_field_block)
  tmp=$(mktemp "$(dirname "$ledger")/.sage-ledger.XXXXXX") || die 1 "cannot create a temp file beside $ledger"
  ledger_skeleton "$title" "$fields" >"$tmp"
  swap_in "$ledger" "$tmp"
}

# next_path_hint <existing-ledger> — `; a new run uses <path>` for a ledger named by the
# session convention, else nothing. A `-<n>` suffix is a run number only when the bare
# ledger it follows exists, since a session id may itself end in digits.
next_path_hint() {
  local dir name session base
  dir=$(dirname "$1")
  name=$(basename "$1")
  case "$name" in sage-ledger-?*.md) ;; *) return 0 ;; esac
  session=${name#sage-ledger-}
  session=${session%.md}
  base=${session%-*}
  case "${session##*-}" in
    ''|*[!0-9]*) ;;
    *) [ "$base" = "$session" ] || [ ! -e "$dir/sage-ledger-$base.md" ] || session=$base ;;
  esac
  printf '; a new run uses %s' "$(next_ledger_path "$dir" "$session")"
}

# ---------------------------------------------------------------------------
# next-path

cmd_next_path() {
  [ $# -eq 2 ] || die 2 "usage: next-path <plans-dir> <session-id>"
  case "$2" in ''|*/*) die 2 "next-path: session id '$2' is empty or holds a /" ;; esac
  next_ledger_path "$1" "$2"
}

next_ledger_path() {  # next_ledger_path <plans-dir> <session-id>
  local n=2
  if [ ! -e "$1/sage-ledger-$2.md" ]; then printf '%s\n' "$1/sage-ledger-$2.md"; return; fi
  while [ -e "$1/sage-ledger-$2-$n.md" ]; do n=$((n + 1)); done
  printf '%s\n' "$1/sage-ledger-$2-$n.md"
}

empty_field_block() {
  printf '%s\n' 'ASK:' 'PURPOSE:' 'PREMISES:' 'DELIVERABLE:' 'APPROACHES:' 'RISK:' \
    'TOPOLOGY:' 'PARENT:' 'Wall target:' 'Acceptance suite:' 'Criteria:'
}

ledger_skeleton() {  # ledger_skeleton <title> <field-block>
  printf '# Sage ledger — %s\n\n### Plan\n\nStarted: %s\n%s\n\n' "$1" "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$2"
  printf '%s\n' \
    '| id | unit | done-when | rw | agent | flow | state | agentId | evidence |' \
    '| --- | --- | --- | --- | --- | --- | --- | --- | --- |' \
    '' '### Resume state' '' 'step: 2 — references/dispatch.md' 'next action: write the Plan rows' 'write lease: none' 'baseline:' '' \
    '### Decisions' '' \
    '| id | kind | when | decision | reason |' \
    '| --- | --- | --- | --- | --- |' \
    '' '### Findings' '' \
    '| id | severity | stage | author | location | triage | evidence |' \
    '| --- | --- | --- | --- | --- | --- | --- |' \
    '' '### Run record' '' "OUTCOME: $PENDING_TEXT"
}

# ---------------------------------------------------------------------------
# unit, finding

cmd_unit() {
  [ $# -ge 3 ] || die 2 "usage: unit <ledger> <id> <key>=<value>..."
  local ledger=$1 id=$2
  shift 2
  require_ledger "$ledger"
  collect_updates "$UNIT_KEYS" "$@"
  reject_bad_state
  upsert_row "$ledger" "Plan" "$id"
}

cmd_finding() {
  [ $# -ge 3 ] || die 2 "usage: finding <ledger> <id> <key>=<value>..."
  local ledger=$1 id=$2
  shift 2
  require_ledger "$ledger"
  collect_updates "$FINDING_KEYS" "$@"
  reject_bad_finding_values
  upsert_row "$ledger" "Findings" "$id"
}

# collect_updates <allowed-keys> <key=value>... — fills UPDATES ("key<TAB>value" lines) and
# the UPDATE_<key> lookups the value checks read. Rejects an unknown key (exit 2).
collect_updates() {
  local allowed=$1 pair key value
  shift
  UPDATES=""
  UPDATE_KEYS=""
  for pair in "$@"; do
    case "$pair" in *=*) ;; *) die 2 "expected <key>=<value>, got '$pair'" ;; esac
    key=$(lowercase "${pair%%=*}")
    value=${pair#*=}
    in_list "$key" "$allowed" || die 2 "unknown key '${pair%%=*}' (keys: $allowed)"
    UPDATES="$UPDATES$key	$(cell_text "$value")
"
    UPDATE_KEYS="$UPDATE_KEYS $key"
    eval "UPDATE_$(printf '%s' "$key" | tr -c 'a-z0-9\n' '_')=\$value"
  done
}

update_value() {  # update_value <key> — the raw value given for a key, or nothing
  eval "printf '%s' \"\${UPDATE_$(printf '%s' "$1" | tr -c 'a-z0-9\n' '_')-}\""
}

has_update() { in_list "$1" "${UPDATE_KEYS# }"; }

reject_bad_state() {
  has_update state || return 0
  local state
  state=$(update_value state)
  local word
  for word in $STATE_WORDS; do
    case "$state" in
      "$word") return 0 ;;
      "$word"[!A-Za-z]*) return 0 ;;
    esac
  done
  die 2 "state '$state' does not begin with one of: $STATE_WORDS"
}

reject_bad_finding_values() {
  has_update severity && ! in_list "$(update_value severity)" "$SEVERITIES" \
    && die 2 "severity '$(update_value severity)' is not one of: $SEVERITIES"
  has_update stage && ! in_list "$(update_value stage)" "$STAGES" \
    && die 2 "stage '$(update_value stage)' is not one of: $STAGES"
  has_update author && ! in_list "$(update_value author)" "$AUTHORS" \
    && die 2 "author '$(update_value author)' is not one of: $AUTHORS"
  return 0
}

# upsert_row <ledger> <section> <id> — merges UPDATES into the row keyed by <id> in the first
# table under <section>, or appends a row of empty cells plus the updates.
upsert_row() {
  local ledger=$1 section=$2 id
  id=$(cell_text "$3")
  SL_SECTION=$section SL_ID=$id SL_UPD=$UPDATES rewrite_ledger "$ledger" "$AWK_LIB"'
    function emit_row(cells, n,   i, out) {
      out = "|"
      for (i = 1; i <= ncols; i++) out = out " " cells[i] " |"
      gsub(/\001/, "\\|", out)
      print out
    }
    function apply_updates(cells,   k, col) {
      for (k = 1; k <= nupd; k++) {
        col = hcol[ukey[k]]
        if (col == 0) fail("table under " sec " has no column " ukey[k])
        cells[col] = uval[k]
      }
    }
    function flush_table(   i, cells) {
      if (!matched) {
        for (i = 1; i <= ncols; i++) cells[i] = ""
        cells[1] = id
        apply_updates(cells)
        emit_row(cells)
      }
      intable = 0
      done = 1
    }
    BEGIN {
      sec = ENVIRON["SL_SECTION"]; id = ENVIRON["SL_ID"]
      n = split(ENVIRON["SL_UPD"], raw, "\n")
      for (i = 1; i <= n; i++) {
        if (raw[i] == "") continue
        p = index(raw[i], "\t")
        nupd++; ukey[nupd] = substr(raw[i], 1, p - 1); uval[nupd] = substr(raw[i], p + 1)
      }
    }
    {
      if (is_fence($0)) { infence = !infence; if (intable) flush_table(); print; next }
      if (infence) { print; next }
      if (is_heading($0)) {
        if (intable) flush_table()
        insec = (heading_of($0) == sec)
        if (insec) secseen = 1
        print; next
      }
      if (insec && !done && $0 ~ /^\|/) {
        if (!intable) {
          intable = 1; tableseen = 1; sepdone = 0
          m = split_raw($0, hc)
          ncols = m - 2
          for (i = 2; i < m; i++) hcol[tolower(trim(hc[i]))] = i - 1
          print; next
        }
        if (!sepdone) { sepdone = 1; print; next }
        m = split_raw($0, rc)
        if (trim(rc[2]) == id) {
          matched = 1
          for (i = 1; i <= ncols; i++) cells[i] = (i + 1 < m) ? trim(rc[i + 1]) : ""
          apply_updates(cells)
          emit_row(cells)
          next
        }
        print; next
      }
      if (intable) flush_table()
      print
    }
    END {
      if (failed) exit 1
      if (intable) flush_table()
      if (!secseen) fail("section " sec " not found")
      if (!tableseen) fail("no table under section " sec)
    }
  '
}

# ---------------------------------------------------------------------------
# decision

cmd_decision() {
  [ $# -ge 3 ] && [ $# -le 4 ] || die 2 "usage: decision <ledger> <kind> <decision> [<reason>]"
  local ledger=$1 kind=$2 decision=$3 reason=${4-} step id
  require_ledger "$ledger"
  in_list "$kind" "$DECISION_KINDS" || die 2 "unknown decision kind '$kind' (kinds: $DECISION_KINDS)"
  step=$(resume_step "$ledger") || die 1 "$ledger: section Resume state with a step: line not found"
  id="D$(next_decision_number "$ledger")"
  collect_updates 'id kind when decision reason' \
    "kind=$kind" "when=step $step $(date -u +%H:%M)Z" "decision=$decision" "reason=$reason"
  upsert_row "$ledger" "Decisions" "$id" || return 1
  printf '%s\n' "$id"
}

resume_step() {  # resume_step <ledger> — first token of the Resume state `step:` line
  awk "$AWK_LIB"'
    is_fence($0) { infence = !infence; next }
    infence { next }
    is_heading($0) { insec = (heading_of($0) == "Resume state"); next }
    insec && /^step:/ {
      v = $0; sub(/^step:[ \t]*/, "", v)
      split(v, w, /[ \t]+/)
      print (w[1] == "" ? "?" : w[1]); found = 1; exit
    }
    END { exit (found ? 0 : 1) }
  ' "$1"
}

next_decision_number() {  # next_decision_number <ledger>
  awk "$AWK_LIB"'
    is_heading($0) { insec = (heading_of($0) == "Decisions"); next }
    insec && /^\| *D[0-9]+ *\|/ {
      v = $0; sub(/^\| */, "", v); sub(/ *\|.*/, "", v); sub(/^D/, "", v)
      if (v + 0 > max) max = v + 0
    }
    END { print max + 1 }
  ' "$1"
}

# ---------------------------------------------------------------------------
# restamp

cmd_restamp() {
  [ $# -ge 1 ] || die 2 "usage: restamp <ledger> [step=..] [next=..] [lease=..] [baseline=..] [-- <file>...]"
  local ledger=$1 arg files="" have_files=""
  shift
  require_ledger "$ledger"
  local step="" next="" lease="" baseline="" want=""
  while [ $# -gt 0 ]; do
    arg=$1
    shift
    case "$arg" in
      step=*) step=${arg#*=}; want="$want step" ;;
      next=*) next=${arg#*=}; want="$want next" ;;
      lease=*) lease=${arg#*=}; want="$want lease" ;;
      baseline=*) baseline=${arg#*=}; want="$want baseline" ;;
      --) have_files=1; break ;;
      *) die 2 "restamp takes step= next= lease= baseline= and -- <file>..., got '$arg'" ;;
    esac
  done
  local hashes=""
  if [ -n "$have_files" ]; then
    hashes=$(hash_lines "$@") || exit 2
  fi
  SL_WANT="$want" SL_STEP=$(one_line "$step") SL_NEXT=$(one_line "$next") \
    SL_LEASE=$(one_line "$lease") SL_BASELINE=$(one_line "$baseline") \
    SL_HASHES=$hashes SL_HAVE_FILES=$have_files \
    rewrite_ledger "$ledger" "$AWK_LIB"'
    function has(k) { return index(" " ENVIRON["SL_WANT"] " ", " " k " ") > 0 }
    function is_hash_line(line,   f) {
      split(line, f, /[ \t]+/)
      return (length(f[1]) == 64 && f[1] ~ /^[0-9a-f]+$/)
    }
    function replace_line(key, label, envname) {
      if (!has(key)) return 0
      print label " " ENVIRON[envname]
      seen[key] = 1
      return 1
    }
    {
      if (is_fence($0)) { infence = !infence; print; next }
      if (infence) { print; next }
      if (is_heading($0)) { insec = (heading_of($0) == "Resume state"); if (insec) secseen = 1; skiphash = 0; print; next }
      if (skiphash) { if (is_hash_line($0)) next; skiphash = 0 }
      if (insec && /^step:/) { if (replace_line("step", "step:", "SL_STEP")) next; seen["step"] = seen["step"] }
      if (insec && /^next action:/) { if (replace_line("next", "next action:", "SL_NEXT")) next }
      if (insec && /^write lease:/) { if (replace_line("lease", "write lease:", "SL_LEASE")) next }
      if (insec && /^baseline:/) {
        baseline_found = 1
        if (!replace_line("baseline", "baseline:", "SL_BASELINE")) print
        if (ENVIRON["SL_HAVE_FILES"] != "") {
          if (ENVIRON["SL_HASHES"] != "") print ENVIRON["SL_HASHES"]
          skiphash = 1
        }
        next
      }
      print
    }
    END {
      if (!secseen) fail("section Resume state not found")
      if (has("step") && !seen["step"]) fail("Resume state has no step: line")
      if (has("next") && !seen["next"]) fail("Resume state has no next action: line")
      if (has("lease") && !seen["lease"]) fail("Resume state has no write lease: line")
      if ((has("baseline") || ENVIRON["SL_HAVE_FILES"] != "") && !baseline_found) fail("Resume state has no baseline: line")
    }
  '
}

one_line() {
  local v=$1
  v=${v//$'\n'/ }
  printf '%s' "$v"
}

hash_lines() {  # hash_lines <file>... — sha256 lines, one per file
  local f
  for f in "$@"; do
    [ -r "$f" ] || { printf 'sage-ledger: cannot read %s to hash it\n' "$f" >&2; return 1; }
    if command -v sha256sum >/dev/null 2>&1; then sha256sum "$f"; else shasum -a 256 "$f"; fi
  done
}

# ---------------------------------------------------------------------------
# record

cmd_record() {
  [ $# -eq 1 ] || die 2 "usage: record <ledger>   (Run record body on stdin)"
  local ledger=$1 body
  require_ledger "$ledger"
  body=$(cat)
  [ -n "$(printf '%s' "$body" | tr -d ' \t\n')" ] || die 2 "record refuses empty stdin"
  SL_BODY=$body rewrite_ledger "$ledger" "$AWK_LIB"'
    {
      if (is_heading($0)) {
        if (insec) { print ""; insec = 0; done = 1 }
        if (!done && heading_of($0) == "Run record") {
          insec = 1; secseen = 1
          print; print ""; print ENVIRON["SL_BODY"]
          next
        }
        print; next
      }
      if (insec) next
      print
    }
    END { if (!secseen) fail("section Run record not found") }
  '
}

# ---------------------------------------------------------------------------
# close

cmd_close() {
  local keep_lint=0
  if [ "${1-}" = "--keep-lint" ]; then keep_lint=1; shift; fi
  [ $# -ge 1 ] && [ $# -le 2 ] || die 2 "usage: close [--keep-lint] <ledger> [<subagents-dir>]"
  local ledger=$1 subagents=${2-} lint_status=0
  require_ledger "$ledger"
  if grep -q "$PENDING_TEXT" "$ledger"; then
    die 1 "Run record still says '$PENDING_TEXT'; write it with record first"
  fi
  "$HERE/sage-lint.sh" "$ledger" || lint_status=$?
  [ -z "$subagents" ] || "$HERE/sage-watch.sh" --status "$subagents"
  # runs.log is append-only, so a close that a retry repeats must not have appended the
  # first time: a dirty lint appends nothing unless the caller keeps the violation on purpose.
  if [ "$lint_status" -ne 0 ] && [ "$keep_lint" -eq 0 ]; then
    die 1 "the lint printed a violation; no memory line appended. Fix it and close again, or close --keep-lint"
  fi
  append_memory_lines || die 1 "an obs line did not land in the inbox (named above); put it in the printed block"
  [ "$lint_status" -eq 0 ] || exit 1
}

# append_memory_lines — stdin memory lines go to runs.log or inbox.log by their 2nd field;
# prints the tail of each file it appended to.
append_memory_lines() {
  local dir=${SAGE_MEMORY_DIR:-$MEMORY_DIR_DEFAULT} line kind touched="" failed=0
  [ ! -t 0 ] || return 0
  while IFS= read -r line || [ -n "$line" ]; do
    [ -n "$line" ] || continue
    kind=$(printf '%s' "$line" | awk '{ print $2 }')
    case "$kind" in
      run) if append_log_line "$dir/runs.log" "$line"; then touched="$touched runs.log"; else failed=1; fi ;;
      obs) if append_log_line "$dir/inbox.log" "$line"; then touched="$touched inbox.log"; else failed=1; fi ;;
      *) printf 'sage-ledger: refused memory line (2nd field must be run or obs): %s\n' "$line" >&2 ;;
    esac
  done
  local log
  for log in runs.log inbox.log; do
    in_list "$log" "${touched# }" && tail -n 3 "$dir/$log"
  done
  return "$failed"
}

# append_log_line <log> <line> — appends only to a log that already carries its v4 sentinel.
# A run never creates a memory log: the installer does. So a run never writes a file that
# the migration is still building.
append_log_line() {
  if ! head -n 1 "$1" 2>/dev/null | grep -q '^# sage-local-memory v4'; then
    printf 'sage-ledger: %s is missing or not a v4 log (run install.sh); line NOT appended: %s\n' "$1" "$2" >&2
    return 1
  fi
  # A last line without its newline would glue to the appended line.
  if [ -s "$1" ] && [ "$(tail -c 1 "$1" | wc -l)" -eq 0 ]; then printf '\n' >>"$1"; fi
  printf '%s\n' "$2" >>"$1" || { printf 'sage-ledger: line NOT appended: %s\n' "$2" >&2; return 1; }
}

# ---------------------------------------------------------------------------
# self-test

TESTS_FAILED=0

check() {  # check <name> <exit-code-of-the-assertion>
  if [ "$2" -eq 0 ]; then printf 'ok   %s\n' "$1"; else printf 'FAIL %s\n' "$1"; TESTS_FAILED=$((TESTS_FAILED + 1)); fi
}

lint_says() {  # lint_says <file> <check-id> — lint exits 1 and names the id
  local out rc=0
  out=$("$HERE/sage-lint.sh" "$1" 2>&1) || rc=$?
  [ "$rc" -eq 1 ] && printf '%s\n' "$out" | grep -q "^sage-lint $2 "
}

lint_exit() {  # lint_exit <file> <expected-code>
  local rc=0
  "$HERE/sage-lint.sh" "$1" >/dev/null 2>&1 || rc=$?
  [ "$rc" -eq "$2" ]
}

build_full_ledger() {  # build_full_ledger <ledger> <file-to-hash>
  local l=$1
  printf '%s\n' 'ASK: fix the flaky login test' 'PURPOSE: stop the red builds' 'PREMISES: none' \
    'DELIVERABLE: a green test' 'APPROACHES: retry, or fix the race' 'RISK: low' \
    'TOPOLOGY: one implementer' 'PARENT: main' 'Wall target: 30 min' \
    'Acceptance suite: tests/login' 'Criteria: C1 passes ten runs' | "$SELF" init "$l" 'fix flaky login' || return 1
  "$SELF" unit "$l" U1 unit='write the fix' done-when='C1 holds' rw=rw agent=implementer flow=solo state=planned || return 1
  "$SELF" unit "$l" U2 unit=verify state=running agentId=ab12 || return 1
  "$SELF" unit "$l" U1 state='reported 07:11' evidence='grep -c a|b returns 2' || return 1
  "$SELF" unit "$l" U3 unit=extra state=abandoned || return 1
  "$SELF" finding "$l" F1 severity=major stage=r1 author=unit location=a.sh:3 triage=accepted evidence=repro || return 1
  "$SELF" finding "$l" F2 severity=minor stage=final-run author=parent || return 1
  "$SELF" finding "$l" F2 triage='deferred to next run' || return 1
  "$SELF" decision "$l" assumption 'tests run offline' 'no network in the sandbox' >/dev/null || return 1
  "$SELF" decision "$l" deviation 'skip the second review' 'diff is one line' >/dev/null || return 1
  "$SELF" restamp "$l" step=3 next='run the suite' lease='src/login/**' baseline=abc123 -- "$2" || return 1
  printf '%s\n' 'OUTCOME: done' 'Findings: F1 (fixed)' | "$SELF" record "$l"
}

self_test_build() {
  local dir=$1 ledger=$1/plans/ledger.md rc
  printf 'baseline file\n' >"$dir/lease-file.txt"
  build_full_ledger "$ledger" "$dir/lease-file.txt"
  check "build: every subcommand succeeds" $?
  lint_exit "$ledger" 0
  check "build: sibling lint is clean, exit 0" $?
  [ -z "$("$HERE/sage-lint.sh" "$ledger")" ]
  check "build: lint prints nothing" $?
  grep -q 'grep -c a\\|b returns 2' "$ledger"
  check "build: a pipe in a cell is written as \\|" $?
  grep -q '^| D2 | deviation | step 2 ' "$ledger"
  check "build: decision ids run D1, D2 and read the step" $?
  cp "$ledger" "$dir/before.md"
  "$SELF" unit "$ledger" U1 state=banana 2>/dev/null; rc=$?
  [ "$rc" -eq 2 ] && cmp -s "$dir/before.md" "$ledger"
  check "reject: state=banana exits 2, nothing written" $?
  "$SELF" decision "$ledger" bogus x 2>/dev/null; rc=$?
  [ "$rc" -eq 2 ] && cmp -s "$dir/before.md" "$ledger"
  check "reject: unknown decision kind exits 2, nothing written" $?
  "$SELF" finding "$ledger" F9 severity=huge 2>/dev/null; rc=$?
  [ "$rc" -eq 2 ] && cmp -s "$dir/before.md" "$ledger"
  check "reject: severity outside the three exits 2, nothing written" $?
  "$SELF" init "$ledger" again </dev/null 2>/dev/null; rc=$?
  [ "$rc" -eq 1 ] && cmp -s "$dir/before.md" "$ledger"
  check "reject: init on an existing file exits 1, nothing written" $?
  self_test_close "$dir" "$ledger"
}

self_test_next_path() {
  local plans=$1/next/.claude/plans sid=5e55-1 err rc=0
  [ "$("$SELF" next-path "$plans" "$sid")" = "$plans/sage-ledger-$sid.md" ]
  check "next-path: a free session prints the bare name" $?
  "$SELF" init "$plans/sage-ledger-$sid.md" first </dev/null
  [ "$("$SELF" next-path "$plans" "$sid")" = "$plans/sage-ledger-$sid-2.md" ]
  check "next-path: after the first run it prints -2" $?
  "$SELF" init "$plans/sage-ledger-$sid-2.md" second </dev/null
  [ "$("$SELF" next-path "$plans" "$sid")" = "$plans/sage-ledger-$sid-3.md" ]
  check "next-path: after the second run it prints -3" $?
  err=$("$SELF" init "$plans/sage-ledger-$sid.md" again </dev/null 2>&1) || rc=$?
  [ "$rc" -eq 1 ] && printf '%s\n' "$err" | grep -q -F "$plans/sage-ledger-$sid-3.md"
  check "init: refusing an existing ledger names the next free path" $?
}

self_test_close() {
  local dir=$1 ledger=$2 out
  mkdir -p "$dir/nomem"
  printf '2026-09-29 run nolog x\n' | SAGE_MEMORY_DIR="$dir/nomem" "$SELF" close "$ledger" >/dev/null 2>&1
  [ $? -eq 1 ] && [ ! -e "$dir/nomem/runs.log" ]
  check "close: a missing memory log is not created, and close exits 1" $?
  mkdir -p "$dir/mem"
  printf '# sage-local-memory v4 — runs.log: test\n' >"$dir/mem/runs.log"
  printf '# sage-local-memory v4 — inbox.log: test\n' >"$dir/mem/inbox.log"
  printf '# Sage ledger — pending\n\n### Plan\n\nASK: x\n\n| id | state |\n| --- | --- |\n\n### Run record\n\nOUTCOME: %s\n' "$PENDING_TEXT" >"$dir/pending.md"
  "$SELF" close "$dir/pending.md" </dev/null >/dev/null 2>&1
  [ $? -eq 1 ]
  check "close: a pending Run record exits 1" $?
  out=$(printf '2026-09-29 run 54dd10c5 ok\n2026-09-29 obs a note\n2026-09-29 bad line\n' \
    | SAGE_MEMORY_DIR="$dir/mem" "$SELF" close "$ledger" 2>/dev/null)
  [ $? -eq 0 ] && grep -q 'run 54dd10c5' "$dir/mem/runs.log" && grep -q 'obs a note' "$dir/mem/inbox.log" \
    && ! grep -rq 'bad line' "$dir/mem"
  check "close: run and obs lines are appended, others refused" $?
  printf '%s\n' "$out" | grep -q 'run 54dd10c5'
  check "close: prints the tail of each appended file" $?
  cp "$ledger" "$dir/dirty.md"
  printf '\n| orphan | x |\n| --- | --- |\n| Q9 | cited but never triaged |\n' >>"$dir/dirty.md"
  printf '2026-09-29 run dirty1 x\n' | SAGE_MEMORY_DIR="$dir/mem" "$SELF" close "$dir/dirty.md" >/dev/null 2>&1
  [ $? -eq 1 ] && ! grep -q 'run dirty1' "$dir/mem/runs.log"
  check "close: a dirty lint exits 1 and appends nothing" $?
  printf '2026-09-29 run dirty2 x\n' | SAGE_MEMORY_DIR="$dir/mem" "$SELF" close --keep-lint "$dir/dirty.md" >/dev/null 2>&1
  [ $? -eq 1 ] && [ "$(grep -c 'run dirty2' "$dir/mem/runs.log")" -eq 1 ]
  check "close: --keep-lint appends once and still exits 1" $?
  printf '2026-09-29 run nonl x' >>"$dir/mem/runs.log"
  printf '2026-09-29 run afternonl x\n' | SAGE_MEMORY_DIR="$dir/mem" "$SELF" close "$ledger" >/dev/null 2>&1
  [ $? -eq 0 ] && grep -qx '2026-09-29 run nonl x' "$dir/mem/runs.log" && grep -qx '2026-09-29 run afternonl x' "$dir/mem/runs.log"
  check "close: a log missing its last newline gets the line on its own line" $?
}

self_test_negative_fixtures() {
  local dir=$1 fixtures=$HERE/tests id
  for id in state-enum triage-state triage-orphan frame sections findings-shape disclosure-home; do
    lint_says "$fixtures/neg-$id.md" "$id"
    check "negative: neg-$id.md fires $id" $?
  done
  { cat "$dir/plans/ledger.md"; printf 'token %s%s\n' 'AKIA' 'ABCDEFGHIJKLMNOP'; } >"$dir/neg-secret.md"
  lint_says "$dir/neg-secret.md" secret-shape
  check "negative: a secret-shaped string fires secret-shape" $?
  lint_exit "$fixtures/old-format.md" 3
  check "old format: exit 3" $?
}

self_test_corpus() {
  local dir=$1/corpus out rc=0 secret
  mkdir -p "$dir/memory/shared"
  printf '# skill\n' >"$dir/SKILL.md"
  secret="ghp_$(printf 'a%.0s' $(seq 1 36))"
  printf 'line %s\n' "$secret" >"$dir/memory/inbox.log"
  out=$("$HERE/sage-lint.sh" --corpus "$dir" 2>&1) || rc=$?
  [ "$rc" -eq 1 ] && printf '%s\n' "$out" | grep -q 'secret-shape .*inbox.log'
  check "corpus: a secret in memory/inbox.log fires secret-shape" $?
  : >"$dir/memory/inbox.log"
  printf 'see /root/notes for detail\n' >"$dir/memory/lessons.md"
  out=$("$HERE/sage-lint.sh" --corpus "$dir" 2>&1) || true
  printf '%s\n' "$out" | grep -q 'shared-leak .*lessons.md'
  check "corpus: a /root path in lessons.md fires shared-leak" $?
  printf 'costs run 70–120k, see run 54dd10c5\n' >"$dir/memory/lessons.md"
  out=$("$HERE/sage-lint.sh" --corpus "$dir" 2>&1)
  [ -z "$out" ]
  check "corpus: cost bands and run ids in lessons.md stay silent" $?
}

cmd_self_test() {
  local dir
  dir=$(mktemp -d) || die 1 "cannot create a temp directory"
  self_test_build "$dir"
  self_test_next_path "$dir"
  self_test_negative_fixtures "$dir"
  self_test_corpus "$dir"
  rm -rf "$dir"
  [ "$TESTS_FAILED" -eq 0 ]
}

# ---------------------------------------------------------------------------

main() {
  local cmd=${1-}
  [ $# -eq 0 ] || shift
  case "$cmd" in
    next-path) cmd_next_path "$@" ;;
    init) cmd_init "$@" ;;
    unit) cmd_unit "$@" ;;
    finding) cmd_finding "$@" ;;
    decision) cmd_decision "$@" ;;
    restamp) cmd_restamp "$@" ;;
    record) cmd_record "$@" ;;
    close) cmd_close "$@" ;;
    --self-test) cmd_self_test ;;
    -h|--help) usage ;;
    *) usage >&2; exit 2 ;;
  esac
}

main "$@"
