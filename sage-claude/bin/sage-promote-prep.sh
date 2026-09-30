#!/usr/bin/env bash
# RUN BLOCK
#   sage-promote-prep.sh [--memory <mem>] [--repo <dir>]   print the four prep blocks, write nothing
#   sage-promote-prep.sh --drain <to> [--memory <mem>]     archive pending lines up to line <to>
#   sage-promote-prep.sh --pending [--memory <mem>]        print the pending line count, write nothing
#   sage-promote-prep.sh --self-test                       fixtures, one ok/FAIL line each
# Blocks: "== inbox (<n> lines)", "== lineup", "== corpus lint", "== trees". A clean block
# prints (no changes) / (clean) / (match). The inbox block names its drain boundary <to>.
# inbox.log is append-only and never rewritten. --drain <to> publishes payload lines
# <from>..<to> as one batch, archive/inbox-lines-<from>.log. A failed check or a lost race
# writes nothing, exit 1. Exit 2 bad args.
# END RUN BLOCK
#
# MAINTAINER MANUAL
#
# Defaults: mem ~/.claude/skills/sage/memory; repo = the path in <mem>/source-repo. The
# installed skill dir is the parent of <mem>. Siblings called: sage-lineup-check.sh and
# sage-lint.sh (--corpus <repo>/sage-claude), both found next to this script. Payload = every
# line of inbox.log that is not a `#` line.
#
# Why batches: a sage run appends to inbox.log at any time, so nothing rewrites it. A batch
# is named by its first line only and published with `ln`, which fails when that name
# exists: two drains starting at the same line cannot both publish, and a retry of the same
# range finds its own identical batch. The drained count is the last line of the last batch.
# The batches must tile lines 1..<to> in order, each byte-equal to those inbox lines, or
# every read refuses, loudly.
#
# Locale pinned to C.

set -u
export LC_ALL=C

HERE="$(cd "$(dirname "$0")" && pwd)"

main() {
  if [ "${1:-}" = "--self-test" ]; then run_self_test; exit $?; fi
  local drain=0 drain_to="" pending=0 mem="" repo=""
  while [ $# -gt 0 ]; do
    case "$1" in
      --drain) [ $# -ge 2 ] || usage_error "--drain needs the boundary the inbox block printed"; drain=1; drain_to="$2"; shift ;;
      --pending) pending=1 ;;
      --memory) [ $# -ge 2 ] || usage_error "--memory needs a value"; mem="$2"; shift ;;
      --repo) [ $# -ge 2 ] || usage_error "--repo needs a value"; repo="$2"; shift ;;
      *) usage_error "unknown argument $1" ;;
    esac
    shift
  done
  mem="${mem:-$HOME/.claude/skills/sage/memory}"
  if [ "$drain" = 1 ]; then drain_inbox "$mem" "$drain_to"; exit $?; fi
  if [ "$pending" = 1 ]; then inbox_payload "$mem" | wc -l | tr -d ' '; exit "${PIPESTATUS[0]}"; fi
  if [ -z "$repo" ] && [ -f "$mem/source-repo" ]; then repo="$(head -n 1 "$mem/source-repo")"; fi
  [ -n "$repo" ] || usage_error "no --repo and no $mem/source-repo"
  print_prep "$mem" "$repo"
}

usage_error() {
  echo "sage-promote-prep: $1" >&2
  echo "usage: sage-promote-prep.sh [--memory <mem>] [--repo <dir>] | --drain <to> [--memory <mem>] | --pending [--memory <mem>] | --self-test" >&2
  exit 2
}

# ---- prep blocks --------------------------------------------------------

print_prep() {
  local mem="$1" repo="$2"
  print_inbox_block "$mem"
  print_block "lineup" "(no changes)" "$HERE/sage-lineup-check.sh" --memory "$mem" --repo "$repo"
  print_block "corpus lint" "(clean)" "$HERE/sage-lint.sh" --corpus "$repo/sage-claude"
  print_block "trees" "(match)" diff -rq "$repo/sage-claude/" "$(dirname "$mem")/" -x memory
}

print_inbox_block() {
  local done_n payload n=0
  done_n="$(drained_count "$1")" || { echo "== inbox (unreadable: see stderr)"; return 0; }
  payload="$(inbox_payload "$1")"
  if [ -n "$payload" ]; then n="$(printf '%s\n' "$payload" | wc -l | tr -d ' ')"; fi
  echo "== inbox ($n lines, drain with --drain $((done_n + n)))"
  if [ -n "$payload" ]; then printf '%s\n' "$payload"; fi
}

print_block() {
  local title="$1" empty_note="$2"; shift 2
  local out; out="$("$@" 2>&1)"
  echo "== $title"
  if [ -n "$out" ]; then printf '%s\n' "$out"; else echo "$empty_note"; fi
}

inbox_payload() {  # inbox_payload <mem> — the pending lines: payload after the drained count
  local n; n="$(drained_count "$1")" || return 1
  if [ -f "$1/inbox.log" ]; then payload_lines "$1" | tail -n +"$((n + 1))"; fi
  return 0
}

payload_lines() { grep -v '^#' "$1/inbox.log" 2> /dev/null; }

# drained_count <mem> — the highest <to> among the batch files, after proving the batches
# tile 1..<to> in order and each equals its inbox lines byte for byte.
drained_count() {
  local mem="$1" n=0 f from lines
  while IFS= read -r f; do
    [ -n "$f" ] || continue
    from="${f##*/inbox-lines-}"; from="${from%.log}"
    case "$from" in ''|*[!0-9]*) echo "sage-promote-prep: $f is not a batch name" >&2; return 1 ;; esac
    lines="$(wc -l < "$f" | tr -d ' ')"
    if [ "$from" -ne "$((n + 1))" ] || [ "$lines" -lt 1 ]; then
      echo "sage-promote-prep: archive batches do not tile the inbox at $f (expected a batch from line $((n + 1)))" >&2
      return 1
    fi
    if ! payload_lines "$mem" | sed -n "${from},$((from + lines - 1))p" | cmp -s - "$f"; then
      echo "sage-promote-prep: $f no longer matches inbox.log from line $from; inbox.log must only ever be appended to" >&2
      return 1
    fi
    n=$((from + lines - 1))
  done < <(ls "$mem"/archive/inbox-lines-*.log 2> /dev/null | awk -F'inbox-lines-' '{print $NF + 0 "\t" $0}' | sort -n | cut -f2-)
  echo "$n"
}

# ---- drain --------------------------------------------------------------

drain_inbox() {  # drain_inbox <mem> <to>
  local mem="$1" to="$2" inbox="$1/inbox.log" done_n total batch tmp
  if [ ! -f "$inbox" ]; then echo "sage-promote-prep: no $inbox" >&2; return 1; fi
  case "$to" in ''|*[!0-9]*) usage_error "--drain needs a line number, got '$to'" ;; esac
  done_n="$(drained_count "$mem")" || return 1
  total="$(payload_lines "$mem" | wc -l | tr -d ' ')"
  if [ "$to" -le "$done_n" ]; then echo "drained 0 lines (already drained through line $done_n)"; return 0; fi
  if [ "$to" -gt "$total" ]; then echo "sage-promote-prep: inbox.log has $total payload lines, fewer than $to" >&2; return 1; fi
  mkdir -p "$mem/archive" 2> /dev/null || { echo "sage-promote-prep: cannot create $mem/archive" >&2; return 1; }
  batch="$mem/archive/inbox-lines-$((done_n + 1)).log"
  tmp="$(mktemp "$mem/archive/.batch.XXXXXX" 2> /dev/null)" || { echo "sage-promote-prep: drain failed; nothing drained" >&2; return 1; }
  payload_lines "$mem" | sed -n "$((done_n + 1)),${to}p" > "$tmp"
  if [ "$(wc -l < "$tmp" | tr -d ' ')" -ne "$((to - done_n))" ]; then
    rm -f "$tmp"; echo "sage-promote-prep: drain failed; nothing drained" >&2; return 1
  fi
  if ! ln "$tmp" "$batch" 2> /dev/null; then
    rm -f "$tmp"
    echo "sage-promote-prep: another drain published a batch from line $((done_n + 1)) first; nothing drained. Run prep again." >&2
    return 1
  fi
  rm -f "$tmp"
  [ "$(drained_count "$mem")" = "$to" ] || { echo "sage-promote-prep: drain verification failed at $batch" >&2; return 1; }
  echo "drained $((to - done_n)) lines (inbox lines $((done_n + 1))-$to) into $batch"
}

# ---- self-test ----------------------------------------------------------

T_FAILS=0
check() {
  local name="$1"; shift
  if "$@"; then echo "ok   $name"; else echo "FAIL $name"; T_FAILS=$((T_FAILS + 1)); fi
}

INBOX_SENTINEL='# sage-local-memory v4 — inbox.log: obs lines for /sage-promote, drained by its pass'

build_mem() {
  mkdir -p "$1/archive"
  { echo "$INBOX_SENTINEL"; echo '2026-09-04 obs s3 | one'; echo '2026-09-05 obs s4 | two'; } > "$1/inbox.log"
}

case_drain_archives_lines_and_leaves_the_inbox_alone() {
  local m="$1/a"; build_mem "$m"; cp "$m/inbox.log" "$1/a-before.log"
  bash "$0" --drain 2 --memory "$m" > /dev/null || return 1
  cmp -s "$m/inbox.log" "$1/a-before.log" || return 1
  [ "$(cat "$m/archive/inbox-lines-1.log")" = "$(printf '%s\n' '2026-09-04 obs s3 | one' '2026-09-05 obs s4 | two')" ] || return 1
  [ -z "$(inbox_payload "$m")" ]
}

case_a_retried_drain_writes_the_same_batch_once() {
  local m="$1/b"; build_mem "$m"
  bash "$0" --drain 2 --memory "$m" > /dev/null || return 1
  bash "$0" --drain 2 --memory "$m" > /dev/null || return 1
  [ "$(ls "$m"/archive/inbox-lines-*.log | wc -l | tr -d ' ')" -eq 1 ]
}

case_failed_verify_with_unwritable_archive_dir() {
  local m="$1/d"; build_mem "$m"
  printf 'not a dir\n' > "$m/archive-blocker"
  rm -rf "$m/archive"; ln -s "$m/archive-blocker" "$m/archive"
  cp "$m/inbox.log" "$1/d-before.log"
  bash "$0" --drain 2 --memory "$m" > /dev/null 2>&1; local rc=$?
  [ "$rc" -eq 1 ] && cmp -s "$m/inbox.log" "$1/d-before.log"
}

case_prep_prints_four_blocks_and_writes_nothing() {
  local d="$1/e" out
  mkdir -p "$d/skill/memory" "$d/repo/sage-claude/bin"
  build_mem "$d/skill/memory"
  echo 'same' > "$d/repo/sage-claude/f.md"; echo 'same' > "$d/skill/f.md"
  cp "$d/skill/memory/inbox.log" "$d/before.log"
  out="$(bash "$0" --memory "$d/skill/memory" --repo "$d/repo" 2> /dev/null)"
  printf '%s\n' "$out" | grep -q '^== inbox (2 lines, drain with --drain 2)$' || return 1
  for t in lineup 'corpus lint' trees; do printf '%s\n' "$out" | grep -q "^== $t\$" || return 1; done
  printf '%s\n' "$out" | grep -q '2026-09-05 obs s4 | two' || return 1
  cmp -s "$d/skill/memory/inbox.log" "$d/before.log"
}

case_a_line_appended_after_prep_stays_pending() {
  local m="$1/race"; build_mem "$m"
  echo '2026-09-06 obs s5 | three' >> "$m/inbox.log"
  bash "$0" --drain 2 --memory "$m" > /dev/null || return 1
  [ "$(inbox_payload "$m")" = '2026-09-06 obs s5 | three' ] || return 1
  bash "$0" --drain 3 --memory "$m" > /dev/null || return 1
  [ -z "$(inbox_payload "$m")" ] && [ -f "$m/archive/inbox-lines-3.log" ]
}

case_an_edited_drained_prefix_is_refused() {
  local m="$1/edit"; build_mem "$m"
  bash "$0" --drain 2 --memory "$m" > /dev/null || return 1
  sed -i.bak 's/| one/| ONE/' "$m/inbox.log"
  bash "$0" --drain 2 --memory "$m" > /dev/null 2>&1 && return 1
  return 0
}

case_a_gap_between_batches_is_refused() {
  local m="$1/overlap"; build_mem "$m"
  bash "$0" --drain 1 --memory "$m" > /dev/null || return 1
  payload_lines "$m" | sed -n '1,1p' > "$m/archive/inbox-lines-3.log"
  bash "$0" --pending --memory "$m" > /dev/null 2>&1 && return 1
  return 0
}

case_bad_argument_exits_2() {
  bash "$0" --bogus > /dev/null 2>&1
  [ $? -eq 2 ]
}

run_self_test() {
  local dir; dir="$(mktemp -d)" || return 1
  check "drain archives the lines and never rewrites inbox.log" case_drain_archives_lines_and_leaves_the_inbox_alone "$dir"
  check "a retried drain writes the same batch once" case_a_retried_drain_writes_the_same_batch_once "$dir"
  check "failed verify (archive is not a directory) leaves inbox.log byte-identical" case_failed_verify_with_unwritable_archive_dir "$dir"
  check "prep prints four blocks and writes nothing" case_prep_prints_four_blocks_and_writes_nothing "$dir"
  check "a line appended after prep stays pending past the drain" case_a_line_appended_after_prep_stays_pending "$dir"
  check "an edited drained prefix is refused" case_an_edited_drained_prefix_is_refused "$dir"
  check "a gap between batches is refused" case_a_gap_between_batches_is_refused "$dir"
  check "bad argument exits 2" case_bad_argument_exits_2
  rm -rf "$dir"
  [ "$T_FAILS" -eq 0 ]
}

main "$@"
