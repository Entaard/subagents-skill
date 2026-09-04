#!/usr/bin/env bash
#
# sage-alt-guard.sh — the one sage rule with a deterministic predicate, made to hold.
#
# A `PreToolUse` hook. It reads one hook payload on stdin and denies exactly one thing:
# an `Agent` dispatch of an **alt** role that carries a `model` parameter.
#
# It never writes a file, never touches a transcript, and denies nothing else. Everything
# it cannot parse, it allows.
#
# ---------------------------------------------------------------------------
# WHY THIS ONE RULE
#
#   The alt roles — explorer-alt, verifier-alt, web-researcher-alt — exist to place a unit
#   on a model OUTSIDE this harness's own family. Their model comes from the agent file.
#   The per-invocation `model` parameter WINS over that file, so passing one silently
#   deletes the only thing the alt row was dispatched for: the dispatch succeeds, the
#   report comes back, and the run believes it bought a second model family when it
#   bought another in-family agent at a higher price.
#
#   `../references/harness.md` states the rule once, in "The alt lane" ("pass no `model` at all"). It has a measured
#   failure anyway: one run spent real money proving three alt dispatches that tested
#   nothing, and no agent noticed (figure and full account: ../references/harness.md,
#   "## The alt lane"). It is the only rule in the corpus that is absolute, has a
#   deterministic predicate, and has zero legitimate exceptions — which is what makes it
#   the one worth enforcing rather than asking for.
#
#   Deliberately a pilot, and deliberately narrow. It is one rule, shipped to learn whether
#   hook enforcement earns wider use. Most of sage's prose has no deterministic predicate,
#   and pretending otherwise would rebuild the same failure one layer down.
#
# ---------------------------------------------------------------------------
# USAGE
#
#   Not run by hand. Registered as a `PreToolUse` hook in a settings file:
#
#     "hooks": { "PreToolUse": [ { "matcher": "Agent",
#       "hooks": [ { "type": "command",
#                    "command": "~/.claude/skills/sage/bin/sage-alt-guard.sh" } ] } ] }
#
#   `install.sh` offers to add exactly that block — writing the `~` expanded to the
#   absolute home path, the same hook — the same way it offers the SessionStart(compact)
#   hook, and never edits a settings file it was not told to.
#
#   sage-alt-guard.sh --help    print this usage and exit 0.
#   sage-alt-guard.sh --selftest
#                               run the built-in fixtures and print one PASS/FAIL line
#                               each. Exits 0 if every fixture behaves, 1 otherwise. It
#                               validates THIS SCRIPT'S OWN LOGIC against fixed fixtures,
#                               and it CANNOT detect harness-side drift: a field rename or
#                               a deny-form deprecation upstream leaves every fixture green
#                               while the guard goes quiet in real dispatches. The live
#                               check is one deliberate alt dispatch WITH a model
#                               parameter, which must come back blocked.
#
# ---------------------------------------------------------------------------
# THE PREDICATE, stated exactly. All four must hold or the dispatch is allowed:
#
#   1. the payload parses as JSON, and
#   2. `.tool_name` is exactly "Agent", and
#   3. `.tool_input.subagent_type` is one of: explorer-alt, verifier-alt, web-researcher-alt
#   4. `.tool_input.model` is a JSON STRING, and is non-empty.
#
# Point 4 is a TYPE test, deliberately. An earlier draft used jq's `//` alternative operator,
# which treats `false` as absent just as it treats `null` — so the stated predicate was wrong
# in BOTH directions, and both were measured: `"model":false` was ALLOWED, while
# `"model":{"name":"x"}` and `"model":["x"]` were DENIED with the whole serialised object
# pasted into the deny reason. A `model` that is not a string is not a model parameter this
# guard understands, and what it does not understand it allows.
#
# Measured against a real payload on 2026-08-19 (Claude Code 2.1.235): a `PreToolUse` hook
# does fire on the Agent tool; `tool_name` is the bare string "Agent"; and `tool_input`
# carries `subagent_type` and `model` as TOP-LEVEL keys, alongside `description`, `prompt`
# and `run_in_background`. Both documented deny paths were observed to stop the dispatch
# before the subagent ran. This file uses the JSON path, because it returns a reason the
# caller can read; the non-zero-exit path surfaces the same text as a hook error.
#
# The deny object carries BOTH documented forms in one emission: the legacy top-level
# `decision`/`reason` pair — the form proven live on Claude Code 2.1.237, kept exactly as
# it was — plus `hookSpecificOutput.permissionDecision: "deny"` with the same reason text,
# the form the current hooks documentation prefers. Whichever form the running Claude Code
# honours, the dispatch stops; a version that reads neither ignores the object entirely,
# which is the fail-open direction.
#
# ---------------------------------------------------------------------------
# FAIL OPEN. This is the whole safety argument for shipping an enforcement hook at all.
#
#   No jq                          -> allow.
#   Payload is not JSON            -> allow.
#   `.tool_name` absent or not Agent -> allow.
#   `subagent_type` absent, or not an alt role  -> allow.
#   `model` absent, null, or ""    -> allow. THIS IS THE CORRECT DISPATCH; it is the whole
#                                     point of the rule, and it must never be blocked.
#   `model` any non-string type    -> allow. `false`, a number, an object, an array — none is
#                                     a model parameter this guard understands, so none is
#                                     its call to make.
#   Field names moved in a Claude Code upgrade -> every lookup returns empty -> allow.
#
#   A guard that fails closed on an unrecognised payload would block every dispatch in the
#   session the day a field is renamed. Failing open costs the enforcement and keeps the
#   run; failing closed costs the run. `--selftest` proves this script's own logic still
#   works; only a live alt+model dispatch proves the harness still listens (see USAGE).
#
# ---------------------------------------------------------------------------
# BLIND SPOTS, stated rather than hidden:
#
#   - It sees the `model` PARAMETER only. `CLAUDE_CODE_SUBAGENT_MODEL` outranks both the
#     parameter and the agent file, and is invisible here — check it at Step 2 as
#     `../references/harness.md` says, because nothing enforces that one.
#   - It cannot tell whether the alt agent is even installed, so a dispatch of an
#     uninstalled alt role passes through untouched and fails later on its own.
#   - It knows the three alt role names as a literal list. A fourth alt role added to the
#     harness is not covered until its name is added below.
#   - It is one rule. Nothing else in sage's prose is enforced by anything.
#
# Exit status: 0 always in hook mode, including a denial — a denial is expressed as the
# JSON decision object on stdout, not as an exit code. 0/1 in --selftest mode. 2 for an
# unknown option.

ALT_ROLES="explorer-alt verifier-alt web-researcher-alt"

JQ=jq
command -v "$JQ" >/dev/null 2>&1 || JQ=/usr/bin/jq

usage() {
  sed -n '2,/^# Exit status/p' "$0" | sed 's/^#\{1,2\} \{0,1\}//'
}

# decide <payload> -> prints the deny JSON and returns 0 when the predicate holds;
#                     prints nothing and returns 1 (allow) in every other case.
decide() {
  payload="$1"
  [ -x "$JQ" ] || command -v "$JQ" >/dev/null 2>&1 || return 1

  tool=$(printf '%s' "$payload" | "$JQ" -r '.tool_name // empty' 2>/dev/null) || return 1
  [ "$tool" = "Agent" ] || return 1

  role=$(printf '%s' "$payload" | "$JQ" -r '.tool_input.subagent_type // empty' 2>/dev/null) || return 1
  [ -n "$role" ] || return 1

  hit=0
  for r in $ALT_ROLES; do
    [ "$role" = "$r" ] && hit=1
  done
  [ "$hit" = 1 ] || return 1

  # A TYPE test rather than `// empty`: `//` treats `false` as absent (letting `"model":false`
  # through) and passes an object or array straight into the reason string. Only a JSON string
  # is a model parameter; every other type — and an absent key, and null — yields empty here,
  # which is the allow case. See THE PREDICATE and FAIL OPEN above.
  model=$(printf '%s' "$payload" | "$JQ" -r 'if (.tool_input.model | type) == "string" then .tool_input.model else empty end' 2>/dev/null) || return 1
  [ -n "$model" ] || return 1

  reason="sage: dispatch \`$role\` with NO model parameter. The parameter wins over the agent \
file, so passing model=\"$model\" replaces the outside-family model this row exists to buy — the \
dispatch would succeed and test nothing. Remove the model parameter and dispatch again. \
(~/.claude/skills/sage/references/harness.md, The alt lane.)"

  # Both documented deny forms in one object (see the header): the legacy top-level pair
  # first — proven live, byte-identical to what it always emitted — then the
  # hookSpecificOutput form with the same reason text.
  printf '%s' "$reason" | "$JQ" -R -s '{decision:"block", reason:., hookSpecificOutput:{hookEventName:"PreToolUse", permissionDecision:"deny", permissionDecisionReason:.}}' 2>/dev/null || return 1
  return 0
}

selftest() {
  fail=0
  # name | payload | expect: deny|allow
  run() {
    name="$1"; payload="$2"; want="$3"
    if out=$(decide "$payload") && [ -n "$out" ]; then got=deny; else got=allow; fi
    if [ "$got" = "$want" ]; then
      printf 'PASS  %-46s %s\n' "$name" "$got"
    else
      printf 'FAIL  %-46s want=%s got=%s\n' "$name" "$want" "$got"; fail=1
    fi
  }
  run "alt role + model            -> deny" \
      '{"tool_name":"Agent","tool_input":{"subagent_type":"verifier-alt","model":"gpt-5"}}' deny
  run "alt role, no model          -> allow" \
      '{"tool_name":"Agent","tool_input":{"subagent_type":"verifier-alt"}}' allow
  run "alt role, model null        -> allow" \
      '{"tool_name":"Agent","tool_input":{"subagent_type":"verifier-alt","model":null}}' allow
  run "alt role, model empty       -> allow" \
      '{"tool_name":"Agent","tool_input":{"subagent_type":"verifier-alt","model":""}}' allow
  # The three payloads that proved the old `// empty` predicate wrong in both directions.
  run "alt role, model false       -> allow" \
      '{"tool_name":"Agent","tool_input":{"subagent_type":"verifier-alt","model":false}}' allow
  run "alt role, model object      -> allow" \
      '{"tool_name":"Agent","tool_input":{"subagent_type":"verifier-alt","model":{"name":"x"}}}' allow
  run "alt role, model array       -> allow" \
      '{"tool_name":"Agent","tool_input":{"subagent_type":"verifier-alt","model":["x"]}}' allow
  run "base role + model           -> allow" \
      '{"tool_name":"Agent","tool_input":{"subagent_type":"verifier","model":"opus"}}' allow
  run "explorer-alt + model        -> deny" \
      '{"tool_name":"Agent","tool_input":{"subagent_type":"explorer-alt","model":"haiku"}}' deny
  run "web-researcher-alt + model  -> deny" \
      '{"tool_name":"Agent","tool_input":{"subagent_type":"web-researcher-alt","model":"sonnet"}}' deny
  run "other tool                  -> allow" \
      '{"tool_name":"Bash","tool_input":{"subagent_type":"verifier-alt","model":"gpt-5"}}' allow
  run "field renamed upstream      -> allow" \
      '{"tool_name":"Agent","tool_input":{"agent_type":"verifier-alt","model_name":"gpt-5"}}' allow
  run "not JSON                    -> allow" 'this is not json at all' allow
  run "empty payload               -> allow" '' allow
  run "JSON but no tool_name       -> allow" '{"tool_input":{"subagent_type":"verifier-alt","model":"x"}}' allow
  # One SHAPE assertion beyond the verdict fixtures: the deny object must carry both
  # documented forms at once — the legacy top-level decision/reason pair and
  # hookSpecificOutput.permissionDecision — with the same reason text in both. A verdict
  # fixture cannot see a dropped field. This still cannot prove the harness READS either
  # form; only the live alt+model dispatch does (see USAGE).
  name="deny output carries both forms"
  out=$(decide '{"tool_name":"Agent","tool_input":{"subagent_type":"verifier-alt","model":"gpt-5"}}')
  if printf '%s' "$out" | "$JQ" -e '(.decision == "block") and ((.reason | type) == "string") and (.reason != "") and (.hookSpecificOutput.hookEventName == "PreToolUse") and (.hookSpecificOutput.permissionDecision == "deny") and (.hookSpecificOutput.permissionDecisionReason == .reason)' >/dev/null 2>&1; then
    printf 'PASS  %-46s shape\n' "$name"
  else
    printf 'FAIL  %-46s deny JSON is missing a required field\n' "$name"; fail=1
  fi
  return $fail
}

case "${1:-}" in
  --help|-h) usage; exit 0 ;;
  --selftest) selftest; exit $? ;;
  "") : ;;
  *) printf 'sage-alt-guard: unknown option %s\n' "$1" >&2; exit 2 ;;
esac

payload=$(cat)
decide "$payload"
exit 0
