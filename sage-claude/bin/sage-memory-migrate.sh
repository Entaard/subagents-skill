#!/usr/bin/env bash
# RUN BLOCK
#   sage-memory-migrate.sh <mem> [--dry-run]   one-time sage memory v3 -> v4
#   sage-memory-migrate.sh --self-test         run built-in fixtures, one ok/FAIL line each
# <mem> is ~/.claude/skills/sage/memory. Already v4: prints "already v4", changes nothing.
# It writes runs.log (every run line, deduped, date-sorted) and inbox.log (obs lines after
# the last mark), verifies them against the sources, and only then moves local/, shared/,
# archive/* and journal.md under archive/v3/. It deletes nothing. Exit 0 ok, 1 refused or
# verify failed (nothing moved), 2 bad arguments.
# END RUN BLOCK
#
# MAINTAINER MANUAL
#
# Line grammar (v3 and v4 alike): `<date> <type> <session> | <payload>`. A run line is one
# whose 2nd whitespace field is `run`. The last `mark` line of journal.md is promote's drain
# marker: obs lines after it are undrained and become inbox.log. `use` lines are dropped.
#
# Order of work: build both logs as temps in <mem>; verify (every source run line is in the
# temp runs.log, obs count equals an independent sed|grep count); move the old tree; install
# the logs last, so a runs.log on disk means the migration finished. lessons.md and
# lineup.json are not created here.
#
# Locale is pinned to C so sort is stable and byte-wise on every platform.

set -u
export LC_ALL=C

# A payload line starts with a real date. The v3 journal header quotes the grammar
# (`<date> run <session> ...`), and those example lines must not migrate as data.
DATE_RE='[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]'
DATE_FIELD="^$DATE_RE$"
RUNS_SENTINEL='# sage-local-memory v4 — runs.log: one run line per sage run, append-only, never drained'
INBOX_SENTINEL='# sage-local-memory v4 — inbox.log: obs lines for /sage-promote, drained by its pass'

main() {
  case "${1:-}" in
    --self-test) run_self_test; exit $? ;;
  esac
  local mem="" dry=0 arg
  for arg in "$@"; do
    case "$arg" in
      --dry-run) dry=1 ;;
      -*) usage_error "unknown option $arg" ;;
      *) [ -z "$mem" ] || usage_error "two memory paths"; mem="$arg" ;;
    esac
  done
  [ -n "$mem" ] || usage_error "missing <mem>"
  [ -d "$mem" ] || usage_error "not a directory: $mem"
  migrate "$mem" "$dry"
}

usage_error() {
  echo "sage-memory-migrate: $1" >&2
  echo "usage: sage-memory-migrate.sh <mem> [--dry-run] | --self-test" >&2
  exit 2
}

migrate() {
  local mem="$1" dry="$2"
  if is_v4 "$mem"; then echo "already v4"; return 0; fi
  if [ ! -f "$mem/journal.md" ] && [ -f "$mem/archive/v3/journal.md" ]; then
    finish_interrupted_migration "$mem" "$dry"; return $?
  fi
  if [ ! -f "$mem/journal.md" ]; then
    echo "note: no journal.md and no v4 runs.log in $mem; nothing to migrate"
    return 0
  fi
  if ! destinations_are_free "$mem"; then
    echo "sage-memory-migrate: $mem holds a runs.log, inbox.log or staging file that is not a v4 log; refusing, nothing moved" >&2
    return 1
  fi
  if [ -e "$mem/archive/v3" ]; then
    echo "sage-memory-migrate: $mem/archive/v3 already exists; refusing" >&2
    return 1
  fi
  local scratch runs_tmp inbox_tmp
  scratch="$(mktemp -d)" || return 1
  runs_tmp="$scratch/runs.log"; inbox_tmp="$scratch/inbox.log"
  if ! build_runs_log "$mem" "$runs_tmp" || ! build_inbox_log "$mem" "$inbox_tmp" \
     || ! verify_logs "$mem" "$runs_tmp" "$inbox_tmp"; then
    rm -rf "$scratch"
    echo "sage-memory-migrate: verification failed; nothing moved" >&2
    return 1
  fi
  local n_runs n_obs
  n_runs=$(($(wc -l < "$runs_tmp") - 1)); n_obs=$(($(wc -l < "$inbox_tmp") - 1))
  if [ "$dry" = 1 ]; then
    rm -rf "$scratch"
    describe_moves "$mem"
    echo "dry-run: would write runs.log ($n_runs run lines) and inbox.log ($n_obs obs lines) in $mem"
    return 0
  fi
  install_logs_then_move_old_tree "$mem" "$scratch" || { rm -rf "$scratch"; return 1; }
  rm -rf "$scratch"
  echo "migrated $mem to v4: runs.log $n_runs run lines, inbox.log $n_obs obs lines; old tree kept under archive/v3/"
}

# destinations_are_free <mem> — nothing stands where the new logs will land, so no move
# can fail halfway through on a blocked destination.
destinations_are_free() {
  local p
  for p in runs.log inbox.log; do
    if [ -e "$1/$p" ] || [ -L "$1/$p" ]; then return 1; fi
  done
  return 0
}

# finish_interrupted_migration <mem> [dry] — a run stopped after the old tree moved into
# archive/v3/ but before the logs landed. The data is whole under archive/v3/, so rebuild
# the logs from there and verify them the same way; never seed empty logs over it.
finish_interrupted_migration() {
  local mem="$1" dry="$2" v3="$1/archive/v3" scratch missing
  if [ "$dry" = 1 ]; then
    echo "dry-run: would finish an interrupted migration from $v3"; return 0
  fi
  scratch="$(mktemp -d)" || return 1
  build_runs_log "$v3" "$scratch/runs.log" && build_inbox_log "$v3" "$scratch/inbox.log" \
    && verify_logs "$v3" "$scratch/runs.log" "$scratch/inbox.log" || {
    rm -rf "$scratch"; echo "sage-memory-migrate: could not rebuild the logs from $v3; nothing written" >&2; return 1; }
  publish_log "$scratch/inbox.log" "$mem/inbox.log" || true
  missing="$(lines_missing_from "$scratch/inbox.log" "$mem/inbox.log")"
  if [ "$missing" != 0 ]; then
    rm -rf "$scratch"
    echo "sage-memory-migrate: $mem/inbox.log exists but lacks $missing migrated observations; it was left untouched. They are in $v3/journal.md." >&2
    return 1
  fi
  publish_log "$scratch/runs.log" "$mem/runs.log" || true
  missing="$(lines_missing_from "$scratch/runs.log" "$mem/runs.log")"
  if [ "$missing" != 0 ]; then
    rm -rf "$scratch"
    echo "sage-memory-migrate: $mem/runs.log exists but lacks $missing migrated run lines; it was left untouched. They are in $v3/." >&2
    return 1
  fi
  echo "finished an interrupted migration of $mem from archive/v3/: runs.log $(($(wc -l < "$scratch/runs.log") - 1)) run lines, inbox.log $(grep -vc '^#' "$mem/inbox.log") obs lines"
  rm -rf "$scratch"
}

# publish_log <complete-file> <dest> — creates <dest> from a complete copy with `ln`, which
# fails when <dest> exists. The staged copy has a name no other process can guess (mktemp)
# and is unlinked at once, so after publication no second path reaches the live log's inode.
# 1 when <dest> already existed.
publish_log() {
  local staged status
  staged="$(mktemp "$(dirname "$2")/.stage.XXXXXXXX")" || return 1
  cp "$1" "$staged" || { rm -f "$staged"; return 1; }
  ln "$staged" "$2" 2>/dev/null; status=$?
  rm -f "$staged"
  return "$status"
}

# lines_missing_from <rebuilt> <log> — how many rebuilt payload lines the log lacks, or
# `unreadable` when the log is missing or does not carry the v4 sentinel.
lines_missing_from() {
  if ! head -n 1 "$2" 2>/dev/null | grep -q '^# sage-local-memory v4'; then echo unreadable; return; fi
  grep -v '^#' "$1" | grep -vxFf "$2" | wc -l | tr -d ' '
}

is_v4() {
  [ -f "$1/runs.log" ] && [ "$(head -n 1 "$1/runs.log")" = "$RUNS_SENTINEL" ]
}

source_journals() {
  local mem="$1" f
  echo "$mem/journal.md"
  for f in "$mem"/archive/journal-*.md "$mem"/archive/archive/journal-*.md; do
    if [ -f "$f" ]; then echo "$f"; fi
  done
}

all_source_run_lines() {
  local f
  while IFS= read -r f; do awk -v d="$DATE_FIELD" '$1 ~ d && $2=="run"' "$f"; done < <(source_journals "$1")
}

build_runs_log() {
  { echo "$RUNS_SENTINEL"
    all_source_run_lines "$1" | awk '!seen[$0]++' | sort -s -k1,1
  } > "$2"
}

build_inbox_log() {
  local last_mark
  last_mark=$(awk -v d="$DATE_FIELD" '$1 ~ d && $2=="mark"{n=NR} END{print n+0}' "$1/journal.md")
  { echo "$INBOX_SENTINEL"
    awk -v lm="$last_mark" -v d="$DATE_FIELD" 'NR>lm && $1 ~ d && $2=="obs"' "$1/journal.md"
  } > "$2"
}

verify_logs() {
  local mem="$1" runs_tmp="$2" inbox_tmp="$3" missing expected_obs got_obs last_mark
  missing=$(all_source_run_lines "$mem" | grep -vxFf "$runs_tmp" | wc -l)
  [ "$missing" -eq 0 ] || return 1
  last_mark=$(grep -nE "^$DATE_RE mark " "$mem/journal.md" | tail -n 1 | cut -d: -f1)
  expected_obs=$(sed -n "$((${last_mark:-0} + 1)),\$p" "$mem/journal.md" | grep -cE "^$DATE_RE obs ")
  got_obs=$(grep -cE "^$DATE_RE obs " "$inbox_tmp")
  [ "$expected_obs" -eq "$got_obs" ]
}

archive_entries() {
  if [ -d "$1/archive" ]; then find "$1/archive" -mindepth 1 -maxdepth 1; fi
}

describe_moves() {
  local mem="$1" e
  for e in local shared; do
    if [ -e "$mem/$e" ]; then echo "would move $mem/$e -> $mem/archive/v3/$e"; fi
  done
  while IFS= read -r e; do
    if [ -n "$e" ]; then echo "would move $e -> $mem/archive/v3/archive/$(basename "$e")"; fi
  done < <(archive_entries "$mem")
  echo "would move $mem/journal.md -> $mem/archive/v3/journal.md"
}

# The logs are published last, so a runs.log on disk means the migration finished. Each is
# published by publish_log: a private staged copy, linked in only if no log stands there.
install_logs_then_move_old_tree() {
  local mem="$1" scratch="$2" entries e
  entries="$(archive_entries "$mem")"
  mkdir -p "$mem/archive/v3/archive" || return 1
  for e in local shared; do
    if [ -e "$mem/$e" ]; then mv "$mem/$e" "$mem/archive/v3/$e" || return 1; fi
  done
  while IFS= read -r e; do
    if [ -n "$e" ] && [ "$e" != "$mem/archive/v3" ]; then mv "$e" "$mem/archive/v3/archive/" || return 1; fi
  done <<< "$entries"
  mv "$mem/journal.md" "$mem/archive/v3/journal.md" || return 1
  publish_or_accept "$scratch/inbox.log" "$mem/inbox.log" && publish_or_accept "$scratch/runs.log" "$mem/runs.log"
}

# publish_or_accept <complete-file> <dest> — publishes <dest>, or accepts one another
# migration published first when it already holds every line. Never edits it.
publish_or_accept() {
  publish_log "$1" "$2" && return 0
  local missing; missing="$(lines_missing_from "$1" "$2")"
  [ "$missing" = 0 ] && return 0
  echo "sage-memory-migrate: $2 exists but lacks $missing migrated lines; it was left untouched" >&2
  return 1
}

# ---------------------------------------------------------------- self-test

T_FAILS=0
check() {
  local name="$1"; shift
  if "$@"; then echo "ok   $name"; else echo "FAIL $name"; T_FAILS=$((T_FAILS + 1)); fi
}

build_fixture() {
  local mem="$1"
  mkdir -p "$mem/archive" "$mem/local" "$mem/shared"
  printf 'x\n' > "$mem/local/a.md"; printf 'y\n' > "$mem/shared/b.md"
  printf 'repo\n' > "$mem/source-repo"
  printf 'old\n' > "$mem/archive/local-v2.md"
  {
    echo '<!-- sage-local-memory v3 -->'
    echo '# Sage journal'
    echo '2026-09-02 run s2 | second run'
    echo '2026-09-01 obs s1 | obs before mark'
    echo '2026-09-01 run s1 | first run'
    echo '2026-09-03 mark promote | drained'
    echo '2026-09-04 obs s3 | obs after mark one'
    echo '2026-09-04 use s3 | a use line'
    echo '2026-09-05 obs s4 | obs after mark two'
    echo '2026-09-05 run s4 | third run'
  } > "$mem/journal.md"
  {
    echo '<!-- sage-local-memory v3 -->'
    echo '2026-09-01 run s1 | first run'
    echo '2026-08-30 run s0 | zeroth run'
  } > "$mem/archive/journal-a.md"
}

tree_state() { (cd "$1" && find . -type f | sort | xargs cksum; find . -type d | sort); }
count_files() { find "$1" -type f | wc -l; }

case_migrates_correctly() {
  local mem="$1/m"; build_fixture "$mem"
  local before; before=$(count_files "$mem")
  bash "$0" "$mem" > /dev/null || return 1
  [ "$(sed -n '2,$p' "$mem/runs.log")" = "$(printf '%s\n' \
    '2026-08-30 run s0 | zeroth run' '2026-09-01 run s1 | first run' \
    '2026-09-02 run s2 | second run' '2026-09-05 run s4 | third run')" ] || return 1
  [ "$(head -n 1 "$mem/runs.log")" = "$RUNS_SENTINEL" ] || return 1
  [ "$(cat "$mem/inbox.log")" = "$(printf '%s\n' "$INBOX_SENTINEL" \
    '2026-09-04 obs s3 | obs after mark one' '2026-09-05 obs s4 | obs after mark two')" ] || return 1
  [ -f "$mem/archive/v3/local/a.md" ] && [ -f "$mem/archive/v3/shared/b.md" ] || return 1
  [ -f "$mem/archive/v3/journal.md" ] && [ -f "$mem/archive/v3/archive/journal-a.md" ] || return 1
  [ -f "$mem/archive/v3/archive/local-v2.md" ] && [ ! -e "$mem/journal.md" ] || return 1
  [ "$(count_files "$mem")" -eq $((before + 2)) ]
}

case_second_run_says_already_v4() {
  local mem="$1/m2"; build_fixture "$mem"
  bash "$0" "$mem" > /dev/null || return 1
  local before; before=$(tree_state "$mem")
  [ "$(bash "$0" "$mem")" = "already v4" ] && [ "$(tree_state "$mem")" = "$before" ]
}

case_dry_run_changes_nothing() {
  local mem="$1/m3"; build_fixture "$mem"
  local before; before=$(tree_state "$mem")
  bash "$0" "$mem" --dry-run | grep -q '^dry-run:' || return 1
  [ "$(tree_state "$mem")" = "$before" ]
}

case_existing_v3_dir_refuses() {
  local mem="$1/m4"; build_fixture "$mem"; mkdir -p "$mem/archive/v3"
  local before; before=$(tree_state "$mem")
  bash "$0" "$mem" > /dev/null 2>&1 && return 1
  [ "$(tree_state "$mem")" = "$before" ]
}

case_blocked_destination_moves_nothing() {
  local mem="$1/blocked"; build_fixture "$mem"; mkdir -p "$mem/inbox.log"
  local before; before=$(tree_state "$mem")
  bash "$0" "$mem" > /dev/null 2>&1 && return 1
  [ "$(tree_state "$mem")" = "$before" ]
}

case_interrupted_run_finishes_from_archive() {
  local mem="$1/interrupted"; build_fixture "$mem"
  bash "$0" "$mem" > /dev/null || return 1
  local want; want=$(sed -n '2,$p' "$mem/runs.log")
  rm -f "$mem/runs.log"
  bash "$0" "$mem" > /dev/null || return 1
  [ -n "$want" ] && [ "$(sed -n '2,$p' "$mem/runs.log")" = "$want" ]
}

case_recovery_keeps_a_line_appended_before_it() {
  local mem="$1/kept"; build_fixture "$mem"
  bash "$0" "$mem" > /dev/null || return 1
  printf '%s\n' '2026-09-30 obs s9 | gap local | appended after the stop | falsifier: x' >> "$mem/inbox.log"
  cp "$mem/inbox.log" "$1/kept-inbox"
  rm -f "$mem/runs.log"
  bash "$0" "$mem" > /dev/null || return 1
  cmp -s "$mem/inbox.log" "$1/kept-inbox" && is_v4 "$mem"
}

case_recovery_never_edits_a_partial_inbox() {
  local mem="$1/partial"; build_fixture "$mem"
  bash "$0" "$mem" > /dev/null || return 1
  head -n 1 "$mem/inbox.log" > "$1/partial-inbox"; cp "$1/partial-inbox" "$mem/inbox.log"
  rm -f "$mem/runs.log"
  bash "$0" "$mem" > /dev/null 2>&1 && return 1
  cmp -s "$mem/inbox.log" "$1/partial-inbox" && [ ! -e "$mem/runs.log" ]
}

case_no_journal_is_a_note() {
  local mem="$1/m5"; mkdir -p "$mem"
  bash "$0" "$mem" | grep -q '^note:' && [ ! -e "$mem/runs.log" ]
}

run_self_test() {
  local dir; dir="$(mktemp -d)" || return 1
  check "migrates runs.log, inbox.log and the old tree" case_migrates_correctly "$dir"
  check "second run prints already v4 and changes nothing" case_second_run_says_already_v4 "$dir"
  check "--dry-run changes nothing" case_dry_run_changes_nothing "$dir"
  check "pre-existing archive/v3 refuses" case_existing_v3_dir_refuses "$dir"
  check "no journal is a note, exit 0" case_no_journal_is_a_note "$dir"
  check "a blocked destination refuses and moves nothing" case_blocked_destination_moves_nothing "$dir"
  check "an interrupted run finishes from archive/v3 with every run line" case_interrupted_run_finishes_from_archive "$dir"
  check "a recovery keeps a line appended before it" case_recovery_keeps_a_line_appended_before_it "$dir"
  check "a recovery never edits a partial inbox, and says so" case_recovery_never_edits_a_partial_inbox "$dir"
  rm -rf "$dir"
  [ "$T_FAILS" -eq 0 ]
}

main "$@"
