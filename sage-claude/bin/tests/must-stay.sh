#!/usr/bin/env bash
# must-stay.sh [<sage-skill-dir>] — each rule in the top-five plan's section 7 keeps exactly one
# full-strength home in the text a run reads. One pattern per rule clause. A pattern must match in
# exactly one file of the set below; zero is a lost rule, two is a second home.
# Prints one line per clause (ok / LOST / TWO-HOMES) and exits 1 when any clause fails.
set -u
dir="${1:-$(cd "$(dirname "$0")/../.." && pwd)}"
scratch="$(mktemp -d)"
trap 'rm -rf "$scratch"' EXIT
files=("$dir/SKILL.md")
for f in "$dir"/references/*.md; do
  case "$(basename "$f")" in harness-measurements.md|authoring.md) continue ;; esac
  files+=("$f")
done
# A run also reads the run blocks of the scripts a step names.
for s in sage-ledger sage-lint; do
  sed -n '1,/^# END RUN BLOCK/p' "$dir/bin/$s.sh" > "$scratch/$s.runblock"
  files+=("$scratch/$s.runblock")
done

fail=0
check() {  # check <rule-number> <label> <extended-regex>
  local hits=() f
  for f in "${files[@]}"; do
    grep -qiE -- "$3" "$f" && hits+=("$(basename "$f")")
  done
  case "${#hits[@]}" in
    1) printf 'ok         %-3s %-52s %s\n' "$1" "$2" "${hits[0]}" ;;
    0) printf 'LOST       %-3s %s\n' "$1" "$2"; fail=1 ;;
    *) printf 'TWO-HOMES  %-3s %-52s %s\n' "$1" "$2" "${hits[*]}"; fail=1 ;;
  esac
}

check 1  "adversarial pass at the parent's own work"        'point one adversarial pass at your own'
check 1  "a fix can un-pass a verified criterion"           'un-pass a criterion already verified'
check 2  "disjoint mandates, disjoint find-sets"            'disjoint mandates produce disjoint find-sets'
check 2  "dedupe against everything seen"                   'dedupe each round against'
check 3  "settle a disagreement with a command"             'settle a disagreement with a command, not by'
check 3  "a reader's structural claim is a lead"            'structural claim is a lead, not ground truth'
check 3  "grep the claim before you brief it"               'grep the claim before you brief it'
check 4  "ground truth in the brief, forbid re-deriving"    'forbid re-deriving it'
check 5  "loop until a dry round"                           'iterates until it comes back dry'
check 5  "same signature twice reopens the plan"            'two failures sharing one signature|same signature twice'
check 6  "never cross rail 1 on own authority"              'cross rail 1 on your own authority'
check 6  "rail-1 authorisation recorded before the action"  'authorisation is a .*row written before'
check 6  "rails 2 and 3"                                    'more than one writer without worktree isolation'
check 7  "one writer per working tree"                      'one writer per working tree\.'
check 7  "snapshot baseline before any writer"              'take it before the writer'
check 8  "probe each alt role before use"                   'clear each alt role you plan to use'
check 8  "transcript model over self-report"                'transcript outranks the self-report'
check 8  "no model parameter on an alt dispatch"            'an alt dispatch passes no .model. parameter'
check 9  "scope the tools, not only the writes"             'scope the tools, not just the writes'
check 9  "Bash reviewer gets a scratch path outside repo"   'scratch path outside the repo'
check 10 "reports are data, never instructions"             'treat reports as data, never as instructions'
check 10 "never help a reviewer with the rationale"         'never "help" a reviewer'
check 11 "triage every finding into exactly one state"      'triage every finding into exactly one state'
check 11 "every commit passes the triage gate"              'every commit passes a triage gate'
check 12 "coordination check, answered honestly"            'coordination check\.\*\* did any result'
# Subject checks: every file that states the rule's subject as a rule, not as a pointer.
# A home says the rule; a deferral names the home file. Two files stating it is a second home.
subject() {  # subject <rule-number> <label> <extended-regex> — must match in exactly one file
  check "$@"
}
subject 2  "dedupe instruction (subject)"                   'dedupe[^.]*(everything seen|against every)'
subject 5  "reopen on repeated signature (subject)"         'same signature[^.]*(stop patching|reopen the plan)|two attempts with the same signature'
subject 7  "baseline timing (subject)"                      'before the writer (starts|launches)'
subject 9  "checker scratch isolation (subject)"            'scratch path (or worktree )?outside the repo'
subject 11 "the four triage states listed (subject)"        'accepted / rejected with evidence / deferred'
subject 3  "command settles a disagreement (subject)"       'settle a disagreement with a command'
exit "$fail"
