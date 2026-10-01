#!/usr/bin/env bash
# sage-codex.sh — runs one alt seat on a model outside the Claude family, through the Codex CLI.
#
# RUN BLOCK
#   sage-codex.sh <seat> <brief-file> <unit-dir> [<repo-dir>]
#   sage-codex.sh --probe <seat> <unit-dir>
#   sage-codex.sh --self-test | --help
#
#   <seat>       verifier-alt or refuter-alt. The seat file `../codex/<seat>.md` pins the model
#                and the effort. Nothing on this command line can change either.
#   <brief-file> the task brief, a plain file outside <unit-dir>. Never pass it on the command line.
#   <unit-dir>   a new or empty directory outside the repo. The unit's only writable path.
#                A directory that is not empty, or that overlaps <repo-dir>, is refused (exit 2).
#   <repo-dir>   the tree under review, read-only to the unit. Default: the current directory.
#
#   Start it with Bash `run_in_background`. The completion notice is the wake signal.
#   Then read `<unit-dir>/receipt.txt` first, and `<unit-dir>/report.md` only when it says done:
#
#     sage-codex receipt <seat> outcome=done model=gpt-6.1-sol effort=xhigh source=session
#       spend=48k input=212k cached=170k output=6k reasoning=4k wall=312s exit=0
#       thread=<id> session=<codex-session-file>
#
#   outcome is done, failed, auth-failed, rate-limited, timeout or no-codex. Only a done report is
#   a verdict; another outcome can leave a partial report.md behind. model= and effort= come from
#   the Codex session file of this unit dir (source=session).
#   source=unverified means no such file was found, so the family is unproven: count the unit as
#   same-family.
#   spend = input minus cached, plus output. Exit 0 on outcome=done, 1 on any other outcome,
#   2 on a usage error (nothing ran, nothing written). Needs jq, on PATH or at /usr/bin/jq, and
#   timeout.
# END RUN BLOCK
#
# MAINTAINER MANUAL
#
# WHY A SCRIPT AND NOT AN AGENT FILE. Through 2026-09 the alt seats were Claude Code agent files
# whose `model:` named an OpenAI model behind the LiteLLM gateway. On 2026-09-30 the gateway
# answered that route with 401 "No ChatGPT OAuth token available", and `claude -p --model
# gpt-6-luna` hung with only `[claude-code:unrecognized_model]` on stderr. The Codex CLI sends the
# user's own ChatGPT token, so the same models answer there. A Claude relay agent was rejected:
# it would retype the brief and the report, could edit the report, and would put its own Claude
# model into the transcript that proves the family.
#
# ISOLATION, each flag measured on codex-cli 0.159.2, 2026-09-30:
#   --cd <unit-dir> -s workspace-write   the unit dir is the only writable root; the repo and
#                                        every other path are read-only (a touch in the repo failed)
#   exclude_slash_tmp, exclude_tmpdir    /tmp is read-only too; TMPDIR points into the unit dir,
#                                        so mktemp-based test suites still run
#   network_access=false, web_search     no network and no web tool (curl could not resolve)
#   --disable plugins hooks apps ...     the user's plugins and hooks stay out of the report; one
#                                        hook's text reached a report before this was set
#   mcp_servers={}                       no MCP servers, so no OAuth refresh and no MCP tools
#   shell_environment_policy.exclude     key- and token-shaped variables stay out of the shell
#   developer_instructions               the seat file body; the brief is the user prompt
# Two things still reach the unit: `~/.codex/AGENTS.md` and Codex's built-in skill list.
# `--ignore-user-config` would drop them, but it also drops the model provider, and the one probe
# with it failed on a 429. Revisit when a config profile can carry the provider alone.
#
# EVIDENCE. The receipt reads model and effort from the Codex session file,
# `~/.codex/sessions/**/rollout-*-<thread>.jsonl`: the `payload.model` and `payload.effort` of the
# first `turn_context` record whose `payload.cwd` is this unit's directory. Codex writes that
# record, not the model. Token counts come from the top-level `turn.completed` events on stdout.
# Every event and record is parsed with jq, so key order and spacing do not matter. This replaces
# the `MODEL-FAMILY:` self-report, which disagreed with the transcript twice.
#
# TRUST. SAGE_CODEX_BIN, SAGE_CODEX_SESSIONS and SAGE_CODEX_TIMEOUT are test seams for
# --self-test. Whoever sets them can run another program or point at forged session files, so the
# pin and the receipt hold only against the brief and the command line, never against the caller.
# The same is true of the rest of the caller's environment, such as PATH or an exported function.
# Codex writes the events and the session file with a strict JSON writer, and every text the model
# writes sits inside a JSON string. So the script checks each record's structure, never its syntax:
# jq also reads some text that is not JSON, such as NaN or a repeated key.
#
# BLIND SPOTS. It proves which model ran, never that the model is good at the job. The unit can
# write events.jsonl while it runs, so the token counts and the error kind are only as honest as
# the unit. The session file and the codex exit status are out of its reach. A Codex release that
# renames `turn_context` turns every receipt into source=unverified, and one that renames
# `turn.completed` turns every unit into outcome=failed with zero spend: loud, never a false done.
# --self-test uses a fake codex, so it tests this script and not Codex; `--probe` is the live check.

set -u
export LC_ALL=C

HERE=$(cd "$(dirname "$0")" && pwd)
SELF="$HERE/$(basename "$0")"
SEAT_DIR="$HERE/../codex"
SEATS='verifier-alt refuter-alt'
TIMEOUT_S=${SAGE_CODEX_TIMEOUT:-5400}
CODEX_BIN=${SAGE_CODEX_BIN:-codex}
CODEX_SESSIONS=${SAGE_CODEX_SESSIONS:-${CODEX_HOME:-$HOME/.codex}/sessions}
PROBE_BRIEF='Reply with exactly the word OK.'
JQ=jq
command -v "$JQ" >/dev/null 2>&1 || JQ=/usr/bin/jq

main() {
  case "${1-}" in
    --help|-h) usage; exit 0 ;;
    --self-test) self_test; exit $? ;;
    --probe) shift; [ $# -eq 2 ] || usage_error "--probe needs <seat> <unit-dir>"; run_probe "$@" ;;
    ''|-*) usage_error "unknown or missing argument ${1-}" ;;
    *) [ $# -ge 3 ] && [ $# -le 4 ] || usage_error "needs <seat> <brief-file> <unit-dir> [<repo-dir>]"
       run_unit "$1" "$2" "$3" "${4:-$PWD}" ;;
  esac
}

usage() {
  sed -n '/^# RUN BLOCK/,/^# END RUN BLOCK/p' "$SELF" | sed -e '/RUN BLOCK/d' -e 's/^# \{0,1\}//'
}

usage_error() {
  printf 'sage-codex: %s\n' "$1" >&2
  exit 2
}

# A probe has no repo under review, so its prompt carries no repo line.
run_probe() {  # run_probe <seat> <unit-dir>
  PROBE_BRIEF_FILE=$(mktemp) || usage_error "cannot create a temp file for the probe brief"
  trap 'rm -f "$PROBE_BRIEF_FILE"' EXIT
  printf '%s\n' "$PROBE_BRIEF" > "$PROBE_BRIEF_FILE"
  run_unit "$1" "$PROBE_BRIEF_FILE" "$2" ""
}

run_unit() {  # run_unit <seat> <brief-file> <unit-dir> <repo-dir, empty for a probe>
  local seat=$1 brief=$2 unit repo="" seat_file=$SEAT_DIR/$1.md model effort started status outcome
  require_seat "$seat"
  command -v "$JQ" >/dev/null 2>&1 || usage_error "jq is required to read the Codex events"
  command -v timeout >/dev/null 2>&1 || usage_error "timeout is required to stop a unit that hangs"
  [ -f "$brief" ] && [ -r "$brief" ] && [ -s "$brief" ] || usage_error "brief file '$brief' is missing or empty"
  if [ -n "$4" ]; then
    [ -d "$4" ] || usage_error "repo dir '$4' is not a directory"
    repo=$(cd -P "$4" && pwd -P)
  fi
  unit=$(physical_path "$3") || usage_error "unit dir '$3' has a '..' in a part that does not exist yet"
  reject_overlap "$unit" "$repo"
  model=$(front_matter "$seat_file" model)
  effort=$(front_matter "$seat_file" effort)
  [ -n "$model" ] && [ -n "$effort" ] || usage_error "$seat_file has no model: or effort: line"
  prepare_unit_dir "$unit"
  write_prompt "$brief" "$unit/prompt.md" "$repo" || usage_error "cannot read the brief '$brief'"

  if ! command -v "$CODEX_BIN" >/dev/null 2>&1; then
    write_receipt "$seat" "$unit" no-codex "$model" "$effort" 0 127
    exit 1
  fi
  started=$(date +%s)
  run_codex "$seat_file" "$model" "$effort" "$unit"
  status=$?
  outcome=$(outcome_of "$status" "$unit")
  write_receipt "$seat" "$unit" "$outcome" "$model" "$effort" $(( $(date +%s) - started )) "$status"
  [ "$outcome" = done ]
}

require_seat() {  # require_seat <seat>
  case " $SEATS " in
    *" $1 "*) ;;
    *) usage_error "seat '$1' is not one of: $SEATS" ;;
  esac
  [ -r "$SEAT_DIR/$1.md" ] || usage_error "seat file $SEAT_DIR/$1.md is missing"
}

# The unit dir may not exist yet, so its nearest existing ancestor is resolved and the rest is
# appended. A `..` in that rest cannot be resolved without creating it, so it is refused.
physical_path() {  # physical_path <path>
  local head=$1 tail=""
  while [ ! -d "$head" ]; do
    case "$(basename "$head")" in .|..) return 1 ;; esac
    tail="/$(basename "$head")$tail"
    head=$(dirname "$head")
  done
  printf '%s%s\n' "$(cd -P "$head" && pwd -P)" "$tail"
}

# The unit can write its own directory, so a unit dir inside the repo, or one holding it, would
# let the unit write the tree under review.
reject_overlap() {  # reject_overlap <unit-dir> <repo-dir, or empty>
  [ -n "$2" ] || return 0
  case "${1%/}/" in "${2%/}/"*) usage_error "unit dir $1 is inside the repo $2" ;; esac
  case "${2%/}/" in "${1%/}/"*) usage_error "unit dir $1 holds the repo $2" ;; esac
}

# A new or empty dir means every file in it is this run's: no stale report can pass as a result,
# and no brief can be a file the run is about to overwrite.
prepare_unit_dir() {  # prepare_unit_dir <unit-dir>
  if [ -e "$1" ] && { [ ! -d "$1" ] || [ -n "$(ls -A "$1")" ]; }; then
    usage_error "$1 is not a new or empty directory; give each unit a new directory"
  fi
  mkdir -p "$1/tmp" || usage_error "cannot create $1"
}

write_prompt() {  # write_prompt <brief-file> <prompt-file> <repo-dir, or empty>
  { if [ -n "$3" ]; then printf 'The repository under review is %s, read-only.\n\n' "$3"; fi
    cat "$1"; } > "$2"
}

front_matter() {  # front_matter <file> <key>
  awk -v key="$2" '
    /^---[ \t]*$/ { fence++; if (fence == 2) exit; next }
    fence == 1 && index($0, key ":") == 1 { v = substr($0, length(key) + 2); gsub(/^[ \t]+|[ \t\r]+$/, "", v); print v; exit }
  ' "$1"
}

seat_body() {  # seat_body <file> — everything after the closing front-matter fence
  awk '/^---[ \t]*$/ && fence < 2 { fence++; next } fence >= 2 && (started || NF) { started = 1; print }' "$1"
}

run_codex() {  # run_codex <seat-file> <model> <effort> <unit-dir>
  local unit=$4 instructions tmpdir
  instructions=$(seat_body "$1" | toml_string)
  tmpdir=$(printf '%s' "$unit/tmp" | toml_string)
  TMPDIR="$unit/tmp" timeout "$TIMEOUT_S" "$CODEX_BIN" exec \
    --cd "$unit" --skip-git-repo-check --ignore-rules \
    -m "$2" -c "model_reasoning_effort=\"$3\"" -c 'approval_policy="never"' \
    -s workspace-write \
    -c 'sandbox_workspace_write.network_access=false' \
    -c 'sandbox_workspace_write.exclude_slash_tmp=true' \
    -c 'sandbox_workspace_write.exclude_tmpdir_env_var=true' \
    -c 'web_search="disabled"' -c 'mcp_servers={}' \
    --disable plugins --disable hooks --disable apps --disable memories --disable multi_agent \
    --disable browser_use --disable computer_use --disable image_generation \
    -c 'shell_environment_policy.exclude=["*KEY*","*SECRET*","*TOKEN*","*PASSWORD*","ANTHROPIC_*","CLAUDE*","CODEX_COMPANION_*"]' \
    -c "shell_environment_policy.set={TMPDIR=$tmpdir}" \
    -c "developer_instructions=$instructions" \
    --json -o "$unit/report.md" - < "$unit/prompt.md" > "$unit/events.jsonl" 2> "$unit/codex.err"
}

# TOML basic string: backslash and double quote escaped, newlines as \n.
toml_string() {
  awk 'BEGIN { ORS = "" } { gsub(/\\/, "\\\\"); gsub(/"/, "\\\""); gsub(/\t/, "\\t"); gsub(/\r/, "")
         line[NR] = $0 }
       END { printf "\""; for (i = 1; i <= NR; i++) printf "%s%s", line[i], (i < NR ? "\\n" : ""); printf "\"" }'
}

# An `error` event alone is not a failure: Codex emits one for a retry that later succeeds.
# A `turn.failed` event is final, so it rules out done whatever follows it.
outcome_of() {  # outcome_of <exit-status> <unit-dir>
  local unit=$2 events=$2/events.jsonl
  [ "$1" -eq 124 ] && { echo timeout; return; }
  if [ "$1" -eq 0 ] && [ -s "$unit/report.md" ] && has_event turn.completed "$events" \
     && ! has_event turn.failed "$events"; then
    echo done; return
  fi
  if error_text "$events" | grep -qE '429|Too Many Requests|rate.limit'; then
    echo rate-limited
  elif error_text "$events" | grep -qE '401|[Uu]nauthori[sz]ed' \
       || grep -qE '^Error:.*(401|[Uu]nauthori[sz]ed|[Nn]ot logged in)' "$unit/codex.err" 2>/dev/null; then
    echo auth-failed
  else
    echo failed
  fi
}

# Only the top-level `type` of an event counts: text in a report or a tool result that looks like
# an event sits inside a string or a nested object.
has_event() {  # has_event <type> <events-file>
  [ -n "$(top_level_events "$2" | "$JQ" -c --arg t "$1" 'select(.type == $t)' 2>/dev/null)" ]
}

# Codex puts the message at `.message` of an error event and `.error.message` of a turn.failed
# event. Other fields can hold any text, so they never decide the outcome.
error_text() {  # error_text <events-file> — the messages of every error and turn.failed event
  top_level_events "$1" | "$JQ" -r '
    if .type == "error" then .message
    elif .type == "turn.failed" then (.error | objects | .message)
    else empty end | strings' 2>/dev/null
}

# One JSON object per line; a line jq cannot parse is skipped, never fatal.
top_level_events() {  # top_level_events <events-file>
  [ -r "$1" ] || return 0
  "$JQ" -c -R 'fromjson? | select(type == "object")' "$1" 2>/dev/null
}

write_receipt() {  # write_receipt <seat> <unit-dir> <outcome> <pinned-model> <pinned-effort> <wall-s> <exit>
  local seat=$1 unit=$2 thread session measured model effort source usage
  thread=$(top_level_events "$unit/events.jsonl" \
    | "$JQ" -r 'select(.type == "thread.started") | .thread_id | strings | select(test("^[A-Za-z0-9-]+$"))' | head -n 1)
  session=$(session_file_of "$thread")
  measured=$(session_model_effort "$session" "$unit")
  if [ -n "$measured" ]; then
    source=session; model=${measured%% *}; effort=${measured#* }
  else
    source=unverified; model=$4; effort=$5
  fi
  usage=$(usage_totals "$unit/events.jsonl")
  session=$(receipt_path "$session")
  printf 'sage-codex receipt %s outcome=%s model=%s effort=%s source=%s %s wall=%ss exit=%s thread=%s session=%s\n' \
    "$seat" "$3" "${model:-none}" "${effort:-none}" "$source" "$usage" "$6" "$7" \
    "${thread:-none}" "${session:-none}" > "$unit/receipt.txt"
  cat "$unit/receipt.txt"
}

# CODEX_HOME or HOME can hold a blank, and a blank would split the receipt field.
receipt_path() {  # receipt_path <path> — prints it with %, blanks and CR percent-encoded
  local p=${1//%/%25}
  p=${p// /%20}; p=${p//$'\t'/%09}; p=${p//$'\r'/%0D}
  printf '%s\n' "$p"
}

session_file_of() {  # session_file_of <thread-id>
  [ -n "$1" ] && [ -d "$CODEX_SESSIONS" ] || return 0
  find "$CODEX_SESSIONS" -name "rollout-*-$1.jsonl" 2>/dev/null | head -n 1
}

# Blank and control characters in a value become `_`, so a value can never split into a second
# receipt field or a second line.
session_model_effort() {  # session_model_effort <session-file> <unit-dir> — prints "<model> <effort>"
  [ -n "$1" ] && [ -r "$1" ] || return 0
  top_level_events "$1" | "$JQ" -r --arg cwd "$2" '
    def field: tostring | gsub("[[:space:][:cntrl:]]"; "_");
    select(.type == "turn_context" and (.payload | type) == "object" and .payload.cwd == $cwd
           and (.payload.model | type) == "string" and .payload.model != "")
    | "\(.payload.model | field) \(.payload.effort // "none" | field)"' | head -n 1
}

# Sums every turn.completed usage block. Codex reports cached input inside input_tokens.
# A field that is not a number counts as 0, so it never drops the rest of its event.
usage_totals() {  # usage_totals <events-file>
  top_level_events "$1" | "$JQ" -r '
      def tokens: if type == "number" then . else 0 end;
      select(.type == "turn.completed") | (.usage | objects // {})
      | [(.input_tokens | tokens), (.cached_input_tokens | tokens), (.output_tokens | tokens),
         (.reasoning_output_tokens | tokens)]
      | @tsv' | awk -F'\t' '
    { i += $1; c += $2; o += $3; r += $4 }
    function k(n) { n += 0; return (n >= 1000) ? sprintf("%dk", (n + 500) / 1000) : n }
    END { printf "spend=%s input=%s cached=%s output=%s reasoning=%s", k(i - c + o), k(i), k(c), k(o), k(r) }'
}

# ---------------------------------------------------------------------------
# self-test: a fake codex stands in for the real one, so nothing here spends tokens.

T_FAILS=0

check() {  # check <name> <command...>
  local name=$1; shift
  if "$@"; then printf 'ok   %s\n' "$name"; else printf 'FAIL %s\n' "$name"; T_FAILS=$((T_FAILS + 1)); fi
}

write_fake_codex() {  # write_fake_codex <path> — behaviour set by FAKE_MODE
  cat > "$1" <<'FAKE'
#!/usr/bin/env bash
out="" cwd="" args="$*"
while [ $# -gt 0 ]; do
  [ "$1" = "-o" ] && out=$2
  [ "$1" = "--cd" ] && cwd=$2
  shift
done
printf '%s\n' "$args" > "$FAKE_ARGS"
cat > "$FAKE_ARGS.stdin"
tid=01aa0000-0000-7000-8000-00000000abcd
case "$FAKE_MODE" in
  done|other-cwd)
    [ "$FAKE_MODE" = other-cwd ] && cwd=/somewhere/else
    mkdir -p "$FAKE_SESSIONS/2026/09/30"
    printf '{"type":"turn_context","payload":{"settings":{"cwd":"%s","model":"nested","effort":"nested"},"cwd":"%s","model":"gpt-6.1-sol","effort":"xhigh"}}\n' "$FAKE_UNIT" "$cwd" \
      > "$FAKE_SESSIONS/2026/09/30/rollout-2026-09-30T00-00-00-$tid.jsonl"
    printf '{"type":"thread.started","thread_id":"%s"}\n' "$tid"
    printf '{"type":"turn.completed","usage":{"input_tokens":20000,"cached_input_tokens":15000,"output_tokens":800,"reasoning_output_tokens":300}}\n'
    printf 'Status: completed\n' > "$out" ;;
  retry-then-done)
    printf '{"type":"thread.started","thread_id":"%s"}\n' "$tid"
    printf '{"type":"error","message":"stream error: 429 Too Many Requests; retrying"}\n'
    printf '{"type":"turn.completed","usage":{"input_tokens":10,"cached_input_tokens":0,"output_tokens":5,"reasoning_output_tokens":0}}\n'
    printf 'Status: completed\n' > "$out" ;;
  failed-then-done)
    printf '{"type":"thread.started","thread_id":"%s"}\n' "$tid"
    printf '{"error": {"message": "401 Unauthorized"}, "type": "turn.failed"}\n'
    printf '{"type":"turn.completed","usage":{"input_tokens":10,"cached_input_tokens":0,"output_tokens":5,"reasoning_output_tokens":0}}\n'
    printf 'Status: completed\n' > "$out" ;;
  nested-only)
    printf '{"type":"thread.started","thread_id":"%s"}\n' "$tid"
    printf '{"type":"item.completed","item":{"type":"turn.completed"}}\n'
    printf 'Status: completed\n' > "$out" ;;
  no-session)
    printf '{"type":"thread.started","thread_id":"%s"}\n' "$tid"
    printf '{"type":"turn.completed","usage":{"input_tokens":10,"cached_input_tokens":0,"output_tokens":5,"reasoning_output_tokens":0}}\n'
    printf 'Status: completed\n' > "$out" ;;
  rate)
    printf '{"type":"thread.started","thread_id":"%s"}\n' "$tid"
    printf '{"type":"turn.failed","error":{"message":"exceeded retry limit, last status: 429 Too Many Requests"}}\n'
    exit 1 ;;
  auth)
    echo 'Error: 401 Unauthorized' >&2; exit 1 ;;
  replay)
    if [ -f "$FAKE_DIR/session.in" ]; then
      mkdir -p "$FAKE_SESSIONS/2026/09/30"
      sed "s|@CWD@|$cwd|g" "$FAKE_DIR/session.in" > "$FAKE_SESSIONS/2026/09/30/rollout-2026-09-30T00-00-00-$tid.jsonl"
    fi
    cat "$FAKE_DIR/events.in"
    printf 'Status: completed\n' > "$out"
    exit "$(cat "$FAKE_DIR/exit.in" 2>/dev/null || echo 0)" ;;
  hang) sleep 5 ;;
esac
FAKE
  chmod +x "$1"
}

run_fake() {  # run_fake <dir> <mode> [<seat> [<unit-dir> [<brief-file>]]] — one unit, fake codex
  local d=$1 brief=${5:-$1/brief.md} sessions=${FAKE_SESSIONS_DIR:-$1/sessions}
  mkdir -p "$d/repo"
  [ -n "${5-}" ] || printf 'Refute: the "fix" holds for $HOME and `x` and \\n\n' > "$brief"
  FAKE_MODE=$2 FAKE_DIR="$d" FAKE_ARGS="$d/args" FAKE_SESSIONS="$sessions" SAGE_CODEX_SESSIONS="$sessions" FAKE_UNIT="${4:-$d/unit}" \
    SAGE_CODEX_BIN="$d/codex" SAGE_CODEX_TIMEOUT=2 \
    "$SELF" "${3:-verifier-alt}" "$brief" "${4:-$d/unit}" "$d/repo" > "$d/stdout" 2>&1
}

FAKE_TID=01aa0000-0000-7000-8000-00000000abcd

# replay_case <dir> <exit> <event-line...> — the fake codex prints the lines and exits <exit>.
replay_case() {
  local d=$1 code=$2; shift 2
  mkdir -p "$d"; write_fake_codex "$d/codex"
  printf '%s\n' "$@" > "$d/events.in"
  printf '%s\n' "$code" > "$d/exit.in"
  run_fake "$d" replay
}

receipt_is_one_line_of_16_fields() {  # <receipt-file>
  [ "$(wc -l < "$1")" -eq 1 ] && [ "$(awk '{ print NF }' "$1")" -eq 16 ]
}

case_done_receipt() {
  local d=$1/done; mkdir -p "$d"; write_fake_codex "$d/codex"
  run_fake "$d" done || return 1
  grep -q '^sage-codex receipt verifier-alt outcome=done model=gpt-6.1-sol effort=xhigh source=session spend=6k input=20k cached=15k output=800 reasoning=300 ' "$d/unit/receipt.txt"
}

case_pins_come_from_the_seat_file() {
  local d=$1/pins; mkdir -p "$d"; write_fake_codex "$d/codex"
  run_fake "$d" done refuter-alt
  grep -q -- '-m gpt-6-astra ' "$d/args" && grep -q 'model_reasoning_effort="medium"' "$d/args"
}

case_isolation_flags() {
  local d=$1/iso; mkdir -p "$d"; write_fake_codex "$d/codex"
  run_fake "$d" done
  grep -q -- "--cd $d/unit " "$d/args" && grep -q 'network_access=false' "$d/args" \
    && grep -q 'mcp_servers={}' "$d/args" && grep -q -- '--disable hooks' "$d/args" \
    && grep -q 'developer_instructions="You verify. You never fix.' "$d/args"
}

case_brief_reaches_stdin_intact() {
  local d=$1/brief; mkdir -p "$d"; write_fake_codex "$d/codex"
  run_fake "$d" done
  { printf 'The repository under review is %s, read-only.\n\n' "$d/repo"; cat "$d/brief.md"; } \
    | cmp -s - "$d/args.stdin"
}

case_brief_inside_the_unit_dir_is_refused() {
  local d=$1/briefalias; mkdir -p "$d/unit"; write_fake_codex "$d/codex"
  printf 'the real brief\n' > "$d/unit/prompt.md"
  run_fake "$d" done verifier-alt "$d/unit" "$d/unit/prompt.md"
  [ $? -eq 2 ] && [ ! -e "$d/args" ] && grep -qx 'the real brief' "$d/unit/prompt.md"
}

case_unit_dir_overlapping_the_repo_is_refused() {
  local d=$1/overlap; mkdir -p "$d/repo/sub"; write_fake_codex "$d/codex"
  ln -s "$d/repo" "$d/repo-link"
  run_fake "$d" done verifier-alt "$d/repo/unit"; [ $? -eq 2 ] || return 1
  run_fake "$d" done verifier-alt "$d/repo-link/unit"; [ $? -eq 2 ] || return 1
  run_fake "$d" done verifier-alt "$d/repo"; [ $? -eq 2 ] || return 1
  run_fake "$d" done verifier-alt "$d"; [ $? -eq 2 ] || return 1
  [ ! -e "$d/args" ] && [ ! -e "$d/repo/unit" ]
}

case_session_of_another_dir_is_unverified() {
  local d=$1/othercwd; mkdir -p "$d"; write_fake_codex "$d/codex"
  run_fake "$d" other-cwd
  grep -q ' source=unverified ' "$d/unit/receipt.txt"
}

case_a_retried_error_still_ends_done() {
  local d=$1/retry; mkdir -p "$d"; write_fake_codex "$d/codex"
  run_fake "$d" retry-then-done && grep -q ' outcome=done ' "$d/unit/receipt.txt"
}

case_a_failed_turn_is_never_done() {
  local d=$1/faildone; mkdir -p "$d"; write_fake_codex "$d/codex"
  run_fake "$d" failed-then-done && return 1
  grep -q ' outcome=auth-failed ' "$d/unit/receipt.txt"
}

case_a_nested_completion_is_not_done() {
  local d=$1/nested; mkdir -p "$d"; write_fake_codex "$d/codex"
  run_fake "$d" nested-only && return 1
  grep -q ' outcome=failed ' "$d/unit/receipt.txt"
}

case_missing_session_is_unverified() {
  local d=$1/nosess; mkdir -p "$d"; write_fake_codex "$d/codex"
  run_fake "$d" no-session
  grep -q ' outcome=done model=gpt-6.1-sol effort=xhigh source=unverified ' "$d/unit/receipt.txt"
}

case_rate_limit_exits_1() {
  local d=$1/rate; mkdir -p "$d"; write_fake_codex "$d/codex"
  run_fake "$d" rate && return 1
  grep -q ' outcome=rate-limited ' "$d/unit/receipt.txt"
}

case_auth_failure() {
  local d=$1/auth; mkdir -p "$d"; write_fake_codex "$d/codex"
  run_fake "$d" auth && return 1
  grep -q ' outcome=auth-failed ' "$d/unit/receipt.txt"
}

case_timeout() {
  local d=$1/hang; mkdir -p "$d"; write_fake_codex "$d/codex"
  run_fake "$d" hang && return 1
  grep -q ' outcome=timeout ' "$d/unit/receipt.txt"
}

case_no_codex() {
  local d=$1/nocodex; mkdir -p "$d"
  run_fake "$d" done && return 1
  grep -q ' outcome=no-codex model=gpt-6.1-sol effort=xhigh source=unverified ' "$d/unit/receipt.txt"
}

case_a_directory_brief_exits_2_and_writes_nothing() {
  local d=$1/dirbrief; mkdir -p "$d/brief-dir"; write_fake_codex "$d/codex"
  printf 'x\n' > "$d/brief-dir/f"
  run_fake "$d" done verifier-alt "$d/unit" "$d/brief-dir"
  [ $? -eq 2 ] && [ ! -e "$d/unit" ] && [ ! -e "$d/args" ]
}

case_unknown_seat_exits_2() {
  local d=$1/seat; mkdir -p "$d"; write_fake_codex "$d/codex"
  run_fake "$d" done explorer-alt
  [ $? -eq 2 ] && [ ! -e "$d/unit/receipt.txt" ]
}

case_nested_error_text_does_not_decide() {
  local d=$1/nestederr
  replay_case "$d" 1 '{"type":"error","message":"stream closed","metadata":{"status":"429 401"}}' && return 1
  grep -q ' outcome=failed ' "$d/unit/receipt.txt"
}

case_a_forged_thread_id_adds_no_field() {
  local d=$1/forgedtid
  replay_case "$d" 1 "{\"type\":\"thread.started\",\"thread_id\":\"$FAKE_TID outcome=done\"}" && return 1
  receipt_is_one_line_of_16_fields "$d/unit/receipt.txt" && grep -q ' outcome=failed .* thread=none ' "$d/unit/receipt.txt"
}

case_session_values_cannot_split_the_receipt() {
  local d=$1/spacedmodel; mkdir -p "$d"
  printf '%s\n' '{"type":"turn_context","payload":{"cwd":"@CWD@","model":"gpt 6\tx","effort":"high outcome=done"}}' \
    > "$d/session.in"
  replay_case "$d" 0 "{\"type\":\"thread.started\",\"thread_id\":\"$FAKE_TID\"}" '{"type":"turn.completed","usage":{}}' \
    || return 1
  receipt_is_one_line_of_16_fields "$d/unit/receipt.txt" \
    && grep -q ' model=gpt_6_x effort=high_outcome=done source=session ' "$d/unit/receipt.txt"
}

case_a_blank_in_the_session_path_is_encoded() {
  local d=$1/spacedpath
  mkdir -p "$d"; write_fake_codex "$d/codex"
  FAKE_SESSIONS_DIR="$d/my sessions" run_fake "$d" done || return 1
  receipt_is_one_line_of_16_fields "$d/unit/receipt.txt" \
    && grep -q " source=session .* session=$d/my%20sessions/" "$d/unit/receipt.txt"
}

case_the_exit_status_comes_from_the_outcome() {
  local d=$1/exitfromoutcome; mkdir -p "$d"
  printf '%s\n' '{"type":"turn_context","payload":{"cwd":"@CWD@","model":"m","effort":" outcome=done "}}' \
    > "$d/session.in"
  replay_case "$d" 1 "{\"type\":\"thread.started\",\"thread_id\":\"$FAKE_TID\"}" && return 1
  grep -q ' outcome=failed ' "$d/unit/receipt.txt"
}

case_no_timeout_exits_2() {
  local d=$1/notimeout bin=$1/notimeout/bin tool
  mkdir -p "$bin"; write_fake_codex "$d/codex"
  for tool in bash env awk sed grep cat ls mkdir mktemp dirname basename date find head printf rm wc "$JQ"; do
    [ -x "$tool" ] && ln -sf "$tool" "$bin/" || ln -sf "$(command -v "$tool")" "$bin/" 2>/dev/null
  done
  PATH=$bin run_fake "$d" done
  [ $? -eq 2 ] && [ ! -e "$d/args" ] && [ ! -e "$d/unit/receipt.txt" ]
}

case_a_non_number_usage_field_counts_as_0() {
  local d=$1/usagetypes
  replay_case "$d" 0 \
    '{"type":"turn.completed","usage":{"input_tokens":100,"cached_input_tokens":null,"output_tokens":"7","reasoning_output_tokens":[]}}' \
    '{"type":"turn.completed","usage":{"input_tokens":23}}' || return 1
  grep -q ' spend=123 input=123 cached=0 output=0 reasoning=0 ' "$d/unit/receipt.txt"
}

case_reused_unit_dir_exits_2() {
  local d=$1/reuse; mkdir -p "$d"; write_fake_codex "$d/codex"
  run_fake "$d" done || return 1
  run_fake "$d" done
  [ $? -eq 2 ]
}

self_test() {
  local dir
  dir=$(mktemp -d) && dir=$(cd -P "$dir" && pwd -P) || return 1
  check "a done unit writes the measured receipt" case_done_receipt "$dir"
  check "model and effort come from the seat file" case_pins_come_from_the_seat_file "$dir"
  check "the sandbox and isolation flags are passed" case_isolation_flags "$dir"
  check "the brief reaches codex on stdin, byte for byte" case_brief_reaches_stdin_intact "$dir"
  check "a brief inside the unit dir is refused, and kept" case_brief_inside_the_unit_dir_is_refused "$dir"
  check "a unit dir inside, or holding, the repo is refused" case_unit_dir_overlapping_the_repo_is_refused "$dir"
  check "no session file -> source=unverified" case_missing_session_is_unverified "$dir"
  check "a session of another dir -> source=unverified" case_session_of_another_dir_is_unverified "$dir"
  check "a retried error, then completion -> done" case_a_retried_error_still_ends_done "$dir"
  check "a failed turn is never done, whatever follows" case_a_failed_turn_is_never_done "$dir"
  check "a nested completion-shaped item is not done" case_a_nested_completion_is_not_done "$dir"
  check "a 429 -> rate-limited, exit 1" case_rate_limit_exits_1 "$dir"
  check "a 401 -> auth-failed, exit 1" case_auth_failure "$dir"
  check "past the time limit -> timeout, exit 1" case_timeout "$dir"
  check "codex not on PATH -> no-codex, exit 1" case_no_codex "$dir"
  check "an unknown seat exits 2 and writes nothing" case_unknown_seat_exits_2 "$dir"
  check "a directory as the brief exits 2 and writes nothing" case_a_directory_brief_exits_2_and_writes_nothing "$dir"
  check "a used unit dir is refused" case_reused_unit_dir_exits_2 "$dir"
  check "error text outside the message field decides nothing" case_nested_error_text_does_not_decide "$dir"
  check "a forged thread id adds no receipt field, exit 1" case_a_forged_thread_id_adds_no_field "$dir"
  check "session values cannot split the receipt" case_session_values_cannot_split_the_receipt "$dir"
  check "a non-number usage field counts as 0" case_a_non_number_usage_field_counts_as_0 "$dir"
  check "the exit status comes from the outcome, not the receipt text" case_the_exit_status_comes_from_the_outcome "$dir"
  check "a blank in the session path is encoded, one field" case_a_blank_in_the_session_path_is_encoded "$dir"
  check "no timeout on PATH exits 2 and starts nothing" case_no_timeout_exits_2 "$dir"
  rm -rf "$dir"
  [ "$T_FAILS" -eq 0 ]
}

main "$@"
