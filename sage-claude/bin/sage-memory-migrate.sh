#!/usr/bin/env bash
# RUN BLOCK
#   sage-memory-migrate.sh <mem> [--dry-run]   one-time sage memory v3 -> v4
#   sage-memory-migrate.sh --recover-late <mem>  v4 only: append v3-format lines written after
#                                              the migration; silent when there are none
#   sage-memory-migrate.sh --self-test         run built-in fixtures, one ok/FAIL line each
# <mem> is ~/.claude/skills/sage/memory. Already v4: prints "already v4", changes nothing.
# It writes runs.log (every run line, deduped, date-sorted) and inbox.log (obs lines after
# the last mark), verifies them against the sources, and only then moves local/, shared/,
# archive/* and journal.md under archive/v3/. It deletes nothing. A run that stopped partway
# through those moves is finished by the next run once the cause is fixed; an archive/v3 it
# did not create is refused. Where a v4 log already stands, the lines it lacks are appended;
# a file without the v4 sentinel is refused. Exit 0 ok, 1 refused or verify failed (nothing
# more moved), 2 bad arguments.
#
# --recover-late reads a top-level journal.md (an old-skill session appended to it after the
# migration; it is moved aside to archive/v3/journal-late-<n>.md first), archive/v3/journal.md
# and the earlier journal-late-*.md. It appends each run line runs.log lacks and each obs line
# after that file's last mark that inbox.log lacks. It only appends; a second run is silent.
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
# Ownership of archive/v3: before its first move the migrator creates archive/v3 with the
# marker file .sage-migrate-partial, by one rename of a staged directory, and removes the
# marker once both logs are published. A retry
# resumes only an archive/v3 that carries the marker, so a shape match alone is never trusted.
#
# Completion: the marker stays until the late lines are appended and archive/v3/.staging/ (the
# only place staged log copies live) is cleared, so a re-run after any stop finishes that step.
# Nothing outside archive/v3/.staging/ and the empty marker is ever removed.
#
# Publishing onto an existing log: when runs.log or inbox.log already exists and carries its v4
# sentinel, the migrator appends the rebuilt lines it lacks (exact-line dedupe, never an edit),
# as --recover-late does, so a late line cannot block a retry. Without the sentinel it refuses.
#
# Sources are read by logical v3 location, whether or not a move already took them under
# archive/v3: journal.md, then archive/journal-*.md, then archive/archive/journal-*.md, each
# group by basename. A retried run so builds the same runs.log as an uninterrupted one.
#
# Locale is pinned to C so sort is stable and byte-wise on every platform.

set -u
export LC_ALL=C

# A payload line starts with a real date. The v3 journal header quotes the grammar
# (`<date> run <session> ...`), and those example lines must not migrate as data.
DATE_RE='[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]'
DATE_FIELD="^$DATE_RE$"
PARTIAL_MARKER='.sage-migrate-partial'
STAGING='.staging'
RUNS_SENTINEL='# sage-local-memory v4 — runs.log: one run line per sage run, append-only, never drained'
INBOX_SENTINEL='# sage-local-memory v4 — inbox.log: obs lines for /sage-promote, drained by its pass'

SCRATCH=""
trap 'if [ -n "$SCRATCH" ]; then rm -rf "$SCRATCH"; fi' EXIT
trap 'exit 143' TERM
trap 'exit 130' INT

main() {
  case "${1:-}" in
    --self-test) run_self_test; exit $? ;;
    --recover-late)
      [ $# -eq 2 ] || usage_error "--recover-late takes exactly one <mem>"
      [ -d "$2" ] || usage_error "not a directory: $2"
      recover_late_lines "$2"; exit $? ;;
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
  echo "usage: sage-memory-migrate.sh <mem> [--dry-run] | --recover-late <mem> | --self-test" >&2
  exit 2
}

migrate() {
  local mem="$1" dry="$2"
  if is_v4 "$mem"; then
    if [ "$dry" != 1 ] && needs_finalize "$mem"; then finalize_migration "$mem" || return 1; fi
    echo "already v4"; return 0
  fi
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
  if [ -e "$mem/archive/v3" ] && ! is_own_partial_move "$mem"; then
    echo "sage-memory-migrate: $mem/archive/v3 already exists and holds more than a partial move by this migrator; refusing" >&2
    return 1
  fi
  if remaining_moves_collide "$mem"; then
    echo "sage-memory-migrate: an entry still to move already exists under $mem/archive/v3; refusing, nothing moved" >&2
    return 1
  fi
  local scratch runs_tmp inbox_tmp
  scratch="$(mktemp -d)" || return 1
  SCRATCH="$scratch"
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
  finalize_migration "$mem" || return 1
  echo "migrated $mem to v4: runs.log $(($(wc -l < "$mem/runs.log") - 1)) run lines, inbox.log $(($(wc -l < "$mem/inbox.log") - 1)) obs lines; old tree kept under archive/v3/"
}

# create_marked_v3 <mem> — archive/v3 appears only by one rename of a staged directory that
# already holds archive/ and the marker, so no interruption leaves an unmarked archive/v3 of
# this migrator's own making. A staging directory an earlier stop left behind is removed only
# in a shape that stop can leave: empty, the empty marker alone, or the empty marker plus an
# empty archive/. Anything else is left alone.
create_marked_v3() {
  local mem="$1" stage d
  for d in "$mem"/.v3-staging.*; do
    # The reverse of the creation order, so a stop part-way leaves a shape the next run removes.
    if is_empty_stage "$d"; then
      if [ -d "$d/archive" ]; then rmdir "$d/archive" || continue; fi
      rm -f "$d/$PARTIAL_MARKER"; rmdir "$d"
    fi
  done
  mkdir -p "$mem/archive" || return 1
  stage="$(mktemp -d "$mem/.v3-staging.XXXXXX")" || return 1
  # mktemp -d makes the directory 0700; archive/v3 gets the mode mkdir would give it.
  chmod "$(printf '%o' $((0777 & ~$(umask))))" "$stage" || return 1
  : > "$stage/$PARTIAL_MARKER" && mkdir "$stage/archive" && mv "$stage" "$mem/archive/v3" || return 1
}

is_empty_stage() {
  local d="$1" n
  [ -d "$d" ] && [ ! -L "$d" ] || return 1
  n="$(find "$d" -mindepth 1 | wc -l | tr -d ' ')"
  [ "$n" -eq 0 ] && return 0
  [ -f "$d/$PARTIAL_MARKER" ] && [ ! -L "$d/$PARTIAL_MARKER" ] && [ ! -s "$d/$PARTIAL_MARKER" ] || return 1
  [ "$n" -eq 1 ] && return 0
  [ "$n" -eq 2 ] && [ -d "$d/archive" ] && [ ! -L "$d/archive" ]
}

# is_own_partial_move <mem> — archive/v3 carries the marker install_logs_then_move_old_tree
# writes before its first move, and holds nothing a failed move could not have left.
is_own_partial_move() {
  local v3="$1/archive/v3" e
  if [ -L "$v3" ] || [ ! -d "$v3/archive" ]; then return 1; fi
  own_marker "$v3" || return 1
  while IFS= read -r e; do
    case "$(basename "$e")" in local|shared|archive|"$PARTIAL_MARKER") ;; *) return 1 ;; esac
  done < <(find "$v3" -mindepth 1 -maxdepth 1)
  return 0
}

# `mv dir existing-dir` nests instead of failing, so a collision is caught before any move.
remaining_moves_collide() {
  local mem="$1" v3="$1/archive/v3" e
  for e in local shared; do
    if [ -e "$mem/$e" ] && { [ -e "$v3/$e" ] || [ -L "$v3/$e" ]; }; then return 0; fi
  done
  while IFS= read -r e; do
    if [ -n "$e" ] && { [ -e "$v3/archive/$(basename "$e")" ] || [ -L "$v3/archive/$(basename "$e")" ]; }; then return 0; fi
  done < <(archive_entries "$mem")
  return 1
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
  local mem="$1" dry="$2" v3="$1/archive/v3" scratch
  if [ -L "$v3" ] || [ -L "$v3/journal.md" ] || [ -L "$v3/$STAGING" ]; then
    echo "sage-memory-migrate: $v3, its journal.md or its $STAGING is a symlink; refusing, nothing written" >&2
    return 1
  fi
  if [ "$dry" = 1 ]; then
    echo "dry-run: would finish an interrupted migration from $v3"; return 0
  fi
  scratch="$(mktemp -d)" || return 1
  SCRATCH="$scratch"
  build_runs_log "$v3" "$scratch/runs.log" && build_inbox_log "$v3" "$scratch/inbox.log" \
    && verify_logs "$v3" "$scratch/runs.log" "$scratch/inbox.log" || {
    rm -rf "$scratch"; echo "sage-memory-migrate: could not rebuild the logs from $v3; nothing written" >&2; return 1; }
  if ! publish_or_append "$scratch/inbox.log" "$mem/inbox.log" \
     || ! publish_or_append "$scratch/runs.log" "$mem/runs.log"; then
    rm -rf "$scratch"
    echo "sage-memory-migrate: the migrated lines are still whole under $v3/; nothing more written" >&2
    return 1
  fi
  finalize_migration "$mem" || { rm -rf "$scratch"; return 1; }
  echo "finished an interrupted migration of $mem from archive/v3/: runs.log $(($(wc -l < "$scratch/runs.log") - 1)) run lines, inbox.log $(grep -vc '^#' "$mem/inbox.log") obs lines"
  rm -rf "$scratch"
}

# publish_log <complete-file> <dest> — creates <dest> from a complete copy with `ln`, which
# fails when <dest> exists. The staged copy lives in archive/v3/.staging/, which only this
# migrator writes, has a name no other process can guess (mktemp), and is unlinked at once.
# 1 when <dest> already existed.
publish_log() {
  local staged status dir="$(dirname "$2")/archive/v3/$STAGING"
  if [ -L "$dir" ]; then echo "sage-memory-migrate: $dir is a symlink; refusing" >&2; return 1; fi
  mkdir -p "$dir" || return 1
  staged="$(mktemp "$dir/.stage.XXXXXXXX")" || return 1
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

# source_journals <root> — the v3 journals under <root> in their logical v3 order, wherever a
# partial move left each one: journal.md, then archive/, then archive/archive/, by basename.
source_journals() {
  local root="$1"
  if [ -f "$root/journal.md" ]; then echo "$root/journal.md"; else echo "$root/archive/v3/journal.md"; fi
  journals_by_basename "$root/archive" "$root/archive/v3/archive"
  journals_by_basename "$root/archive/archive" "$root/archive/v3/archive/archive"
}

journals_by_basename() {
  local d f
  for d in "$@"; do
    for f in "$d"/journal-*.md; do
      if [ -f "$f" ]; then printf '%s/%s\n' "$(basename "$f")" "$f"; fi
    done
  done | sort -s -t / -k1,1 | cut -d / -f 2-
}

all_source_run_lines() {
  local f
  while IFS= read -r f; do run_lines_of "$f"; done < <(source_journals "$1")
}

run_lines_of() {
  awk -v d="$DATE_FIELD" '$1 ~ d && $2=="run"' "$1"
}

obs_lines_after_last_mark() {
  local last_mark
  last_mark=$(awk -v d="$DATE_FIELD" '$1 ~ d && $2=="mark"{n=NR} END{print n+0}' "$1")
  awk -v lm="$last_mark" -v d="$DATE_FIELD" 'NR>lm && $1 ~ d && $2=="obs"' "$1"
}

build_runs_log() {
  { echo "$RUNS_SENTINEL"
    all_source_run_lines "$1" | awk '!seen[$0]++' | sort -s -k1,1
  } > "$2"
}

build_inbox_log() {
  { echo "$INBOX_SENTINEL"
    obs_lines_after_last_mark "$1/journal.md"
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
  local e
  if [ ! -d "$1/archive" ]; then return 0; fi
  while IFS= read -r e; do
    if [ "$e" != "$1/archive/v3" ]; then echo "$e"; fi
  done < <(find "$1/archive" -mindepth 1 -maxdepth 1)
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
  if [ ! -d "$mem/archive/v3" ]; then create_marked_v3 "$mem" || return 1; fi
  for e in local shared; do
    if [ -e "$mem/$e" ]; then mv "$mem/$e" "$mem/archive/v3/$e" || return 1; fi
  done
  while IFS= read -r e; do
    if [ -n "$e" ]; then mv "$e" "$mem/archive/v3/archive/" || return 1; fi
  done <<< "$entries"
  mv "$mem/journal.md" "$mem/archive/v3/journal.md" || return 1
  publish_or_append "$scratch/inbox.log" "$mem/inbox.log" && publish_or_append "$scratch/runs.log" "$mem/runs.log"
}

# publish_or_append <complete-file> <dest> — publishes <dest>, or appends to an existing <dest>
# that carries its v4 sentinel the payload lines it lacks. Then verifies <dest> holds them all.
publish_or_append() {
  if ! publish_log "$1" "$2"; then
    if [ ! -f "$2" ]; then echo "sage-memory-migrate: could not publish $2" >&2; return 1; fi
    if ! carries_its_v4_sentinel "$2"; then
      echo "sage-memory-migrate: $2 exists without its v4 sentinel; it was left untouched" >&2; return 1
    fi
    grep -v '^#' "$1" | append_lines_missing_from "$2" || return 1
  fi
  local missing; missing="$(lines_missing_from "$1" "$2")"
  [ "$missing" = 0 ] && return 0
  echo "sage-memory-migrate: $2 still lacks $missing migrated lines after publishing" >&2
  return 1
}

# append_late_lines <journal> <mem> — appends to <mem>'s logs the run lines and post-mark obs
# lines of <journal> that they lack. Lines are only ever added at the end.
append_late_lines() {
  append_lines_missing_from "$2/runs.log" < <(run_lines_of "$1")
  append_lines_missing_from "$2/inbox.log" < <(obs_lines_after_last_mark "$1")
}

# The sentinel prefix the memory contract names; install.sh may seed the rest of line 1.
carries_its_v4_sentinel() {
  case "$(head -n 1 "$1" 2>/dev/null)" in "# sage-local-memory v4 — $(basename "$1"):"*) return 0 ;; esac
  return 1
}

append_lines_missing_from() {
  local missing
  missing="$(awk '!seen[$0]++' | grep -vxFf "$1")"
  [ -n "$missing" ] || return 0
  # A last line without its newline would glue to the first appended line.
  if [ -s "$1" ] && [ "$(tail -c 1 "$1" | wc -l)" -eq 0 ]; then printf '\n' >> "$1" || return 1; fi
  printf '%s\n' "$missing" >> "$1"
}

# The partial marker is the migration's completion record: it stands from before the first
# move until finalize_migration has appended the late lines and cleared the staging directory.
# needs_finalize <mem> — a finished publish whose last step did not complete.
needs_finalize() {
  local v3="$1/archive/v3"
  [ -d "$v3" ] && [ ! -L "$v3" ] || return 1
  own_marker "$v3" || { [ -d "$v3/$STAGING" ] && [ ! -L "$v3/$STAGING" ]; }
}

own_marker() {
  [ -f "$1/$PARTIAL_MARKER" ] && [ ! -L "$1/$PARTIAL_MARKER" ] && [ ! -s "$1/$PARTIAL_MARKER" ]
}

# finalize_migration <mem> — idempotent, so a stop anywhere inside it is finished by a re-run.
# A line appended to journal.md between verify and its move sits only in the moved copy.
finalize_migration() {
  local mem="$1" v3="$1/archive/v3" f
  if [ -L "$v3" ] || [ ! -d "$v3" ]; then return 1; fi
  if [ -f "$v3/journal.md" ] && [ ! -L "$v3/journal.md" ]; then append_late_lines "$v3/journal.md" "$mem" || return 1; fi
  if [ -d "$v3/$STAGING" ] && [ ! -L "$v3/$STAGING" ]; then
    for f in "$v3/$STAGING"/.stage.*; do
      if [ -f "$f" ] && [ ! -L "$f" ]; then rm -f "$f"; fi
    done
    rmdir "$v3/$STAGING" 2>/dev/null || { echo "sage-memory-migrate: $v3/$STAGING holds other files; left in place" >&2; return 1; }
  fi
  if own_marker "$v3"; then rm -f "$v3/$PARTIAL_MARKER"; fi
}

recover_late_lines() {
  local mem="$1" v3="$1/archive/v3" runs_before obs_before stray="" f n_runs n_obs
  if ! is_v4 "$mem" || [ "$(head -n 1 "$mem/inbox.log" 2>/dev/null)" != "$INBOX_SENTINEL" ]; then
    echo "sage-memory-migrate: $mem does not hold both v4 logs; nothing recovered" >&2
    return 1
  fi
  if [ -L "$v3" ]; then echo "sage-memory-migrate: $v3 is a symlink; nothing recovered" >&2; return 1; fi
  if needs_finalize "$mem"; then finalize_migration "$mem" || return 1; fi
  # Moved before it is read: a later old-skill append then starts a new top-level file, which
  # the next run picks up, instead of landing unread in the moved one.
  if [ -f "$mem/journal.md" ]; then
    mkdir -p "$v3" || return 1
    stray="$(free_late_journal_path "$v3")"
    mv "$mem/journal.md" "$stray" || return 1
  fi
  runs_before=$(wc -l < "$mem/runs.log"); obs_before=$(wc -l < "$mem/inbox.log")
  for f in "$v3/journal.md" "$v3"/journal-late-*.md; do
    if [ -f "$f" ]; then append_late_lines "$f" "$mem"; fi
  done
  n_runs=$(($(wc -l < "$mem/runs.log") - runs_before)); n_obs=$(($(wc -l < "$mem/inbox.log") - obs_before))
  if [ -z "$stray" ] && [ "$n_runs" -eq 0 ] && [ "$n_obs" -eq 0 ]; then return 0; fi
  printf 'recovered %s run lines into runs.log and %s obs lines into inbox.log from v3 journals written after the migration' "$n_runs" "$n_obs"
  if [ -n "$stray" ]; then printf '; the stray %s/journal.md is now %s' "$mem" "$stray"; fi
  printf '\n'
}

free_late_journal_path() {
  local n=1
  while [ -e "$1/journal-late-$n.md" ] || [ -L "$1/journal-late-$n.md" ]; do n=$((n + 1)); done
  echo "$1/journal-late-$n.md"
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

case_recovery_appends_to_a_sentinel_only_inbox() {
  local mem="$1/partial"; build_fixture "$mem"
  bash "$0" "$mem" > /dev/null || return 1
  head -n 1 "$mem/inbox.log" > "$1/partial-inbox"; cp "$1/partial-inbox" "$mem/inbox.log"
  local inode; inode="$(inode_of "$mem/inbox.log")"
  rm -f "$mem/runs.log"
  bash "$0" "$mem" > /dev/null || return 1
  starts_with_bytes_of "$mem/inbox.log" "$1/partial-inbox" && [ "$(inode_of "$mem/inbox.log")" = "$inode" ] || return 1
  [ "$(sed -n '2,$p' "$mem/inbox.log")" = "$(printf '%s\n' \
    '2026-09-04 obs s3 | obs after mark one' '2026-09-05 obs s4 | obs after mark two')" ] && is_v4 "$mem"
}

case_recovery_refuses_an_inbox_without_sentinel() {
  local mem="$1/nosentinel"; build_fixture "$mem"
  bash "$0" "$mem" > /dev/null || return 1
  printf 'hand-written notes\n' > "$mem/inbox.log"; cp "$mem/inbox.log" "$1/nosentinel-inbox"
  rm -f "$mem/runs.log"
  bash "$0" "$mem" > /dev/null 2>&1 && return 1
  cmp -s "$mem/inbox.log" "$1/nosentinel-inbox" && [ ! -e "$mem/runs.log" ]
}

inode_of() { ls -i "$1" | awk '{print $1}'; }

# A PATH wrapper that makes `mv` fail on one source basename, as a root-owned entry would.
install_failing_mv() {
  local bin="$1" fail_on="$2" real_mv; real_mv="$(command -v mv)"
  mkdir -p "$bin"
  printf '#!/usr/bin/env bash\nfor a in "$@"; do case "$(basename "$a")" in %s) echo "mv: cannot move $a" >&2; exit 1 ;; esac; done\nexec %s "$@"\n' \
    "$fail_on" "$real_mv" > "$bin/mv"
  chmod +x "$bin/mv"
}

case_partial_move_then_retry_finishes() {
  local mem="$1/pm" bin="$1/pm-bin"; build_fixture "$mem"; install_failing_mv "$bin" journal.md
  PATH="$bin:$PATH" bash "$0" "$mem" > /dev/null 2>&1 && return 1
  [ -d "$mem/archive/v3/local" ] && [ -f "$mem/journal.md" ] && [ ! -e "$mem/runs.log" ] || return 1
  bash "$0" "$mem" > /dev/null || return 1
  [ "$(sed -n '2,$p' "$mem/runs.log")" = "$(printf '%s\n' \
    '2026-08-30 run s0 | zeroth run' '2026-09-01 run s1 | first run' \
    '2026-09-02 run s2 | second run' '2026-09-05 run s4 | third run')" ] || return 1
  [ "$(sed -n '2,$p' "$mem/inbox.log")" = "$(printf '%s\n' \
    '2026-09-04 obs s3 | obs after mark one' '2026-09-05 obs s4 | obs after mark two')" ] || return 1
  [ -f "$mem/archive/v3/journal.md" ] && [ -f "$mem/archive/v3/archive/journal-a.md" ] && [ ! -e "$mem/local" ]
}

case_partial_move_with_a_collision_refuses() {
  local mem="$1/pmc" bin="$1/pmc-bin"; build_fixture "$mem"; install_failing_mv "$bin" shared
  PATH="$bin:$PATH" bash "$0" "$mem" > /dev/null 2>&1 && return 1
  mkdir -p "$mem/archive/v3/shared"
  local before; before=$(tree_state "$mem")
  bash "$0" "$mem" > /dev/null 2>&1 && return 1
  [ "$(tree_state "$mem")" = "$before" ]
}

case_foreign_v3_of_partial_shape_refuses() {
  local mem="$1/foreign-shape"; build_fixture "$mem"
  mkdir -p "$mem/archive/v3/archive"
  printf '%s\n' '2025-01-01 run foreign | x' > "$mem/archive/v3/archive/journal-foreign.md"
  local before; before=$(tree_state "$mem")
  bash "$0" "$mem" > /dev/null 2>&1 && return 1
  [ "$(tree_state "$mem")" = "$before" ]
}

# Adds a nested archive/archive/ journal and a second archive journal whose run shares a date
# with journal-a.md, so the source order shows in the stable date sort.
build_nested_fixture() {
  build_fixture "$1"
  mkdir -p "$1/archive/archive"
  printf '%s\n' '2026-08-30 run s0b | zeroth run, second copy' > "$1/archive/journal-b.md"
  printf '%s\n' '2026-08-29 run n1 | nested run' '2026-08-30 run n0 | nested same day' \
    > "$1/archive/archive/journal-c.md"
}

case_retry_after_journal_stop_matches_a_clean_run() {
  local mem="$1/rj" bin="$1/rj-bin"
  build_nested_fixture "$1/rj-clean"; bash "$0" "$1/rj-clean" > /dev/null || return 1
  build_nested_fixture "$mem"; install_failing_mv "$bin" journal.md
  PATH="$bin:$PATH" bash "$0" "$mem" > /dev/null 2>&1 && return 1
  bash "$0" "$mem" > /dev/null || return 1
  grep -qxF '2026-08-29 run n1 | nested run' "$mem/runs.log" || return 1
  cmp -s "$mem/runs.log" "$1/rj-clean/runs.log" && cmp -s "$mem/inbox.log" "$1/rj-clean/inbox.log"
}

# The wrapper stops on journal-b.md with journal-a.md and archive/archive/ already moved,
# whatever order find lists them in.
install_mv_failing_mid_archive() {
  local bin="$1" real_mv; real_mv="$(command -v mv)"
  mkdir -p "$bin"
  printf '#!/usr/bin/env bash\ncase "$1" in *archive/journal-b.md)\n  d="${1%%%%/journal-b.md}"\n  for e in "$d/journal-a.md" "$d/archive"; do if [ -e "$e" ]; then %s "$e" "$2" || exit 1; fi; done\n  echo "mv: cannot move $1" >&2; exit 1 ;; esac\nexec %s "$@"\n' \
    "$real_mv" "$real_mv" > "$bin/mv"
  chmod +x "$bin/mv"
}

case_retry_after_mid_archive_stop_matches_a_clean_run() {
  local mem="$1/ra" bin="$1/ra-bin"
  build_nested_fixture "$1/ra-clean"; bash "$0" "$1/ra-clean" > /dev/null || return 1
  build_nested_fixture "$mem"; install_mv_failing_mid_archive "$bin"
  PATH="$bin:$PATH" bash "$0" "$mem" > /dev/null 2>&1 && return 1
  [ -f "$mem/archive/v3/archive/journal-a.md" ] && [ -f "$mem/archive/v3/archive/archive/journal-c.md" ] \
    && [ -f "$mem/archive/journal-b.md" ] || return 1
  bash "$0" "$mem" > /dev/null || return 1
  grep -qxF '2026-08-29 run n1 | nested run' "$mem/runs.log" || return 1
  cmp -s "$mem/runs.log" "$1/ra-clean/runs.log" && cmp -s "$mem/inbox.log" "$1/ra-clean/inbox.log"
}

case_foreign_v3_dir_refuses() {
  local mem="$1/foreign"; build_fixture "$mem"
  mkdir -p "$mem/archive/v3/archive"; printf 'mine\n' > "$mem/archive/v3/notes.md"
  local before; before=$(tree_state "$mem")
  bash "$0" "$mem" > /dev/null 2>&1 && return 1
  [ "$(tree_state "$mem")" = "$before" ]
}

LATE_RUN='2026-09-06 run s5 | appended after build'
LATE_OBS='2026-09-06 obs s5 | confirm ki-1 | appended after build'

case_line_appended_after_build_is_recovered() {
  local mem="$1/late" bin="$1/late-bin"; build_fixture "$mem"
  # The wrapper appends as journal.md moves: the last moment an old-skill session can write.
  mkdir -p "$bin"
  printf '#!/usr/bin/env bash\ncase "$1" in *journal.md) printf "%%s\\n" "%s" "%s" >> "$1" ;; esac\nexec %s "$@"\n' \
    "$LATE_RUN" "$LATE_OBS" "$(command -v mv)" > "$bin/mv"
  chmod +x "$bin/mv"
  PATH="$bin:$PATH" bash "$0" "$mem" > /dev/null || return 1
  grep -qxF "$LATE_RUN" "$mem/archive/v3/journal.md" || return 1
  grep -qxF "$LATE_RUN" "$mem/runs.log" && grep -qxF "$LATE_OBS" "$mem/inbox.log"
}

case_recover_late_takes_a_stray_journal_once() {
  local mem="$1/stray"; build_fixture "$mem"
  bash "$0" "$mem" > /dev/null || return 1
  printf '%s\n' "$LATE_RUN" "$LATE_OBS" >> "$mem/journal.md"
  bash "$0" --recover-late "$mem" | grep -q '^recovered 1 run lines into runs.log and 1 obs lines' || return 1
  grep -qxF "$LATE_RUN" "$mem/runs.log" && grep -qxF "$LATE_OBS" "$mem/inbox.log" || return 1
  [ ! -e "$mem/journal.md" ] && [ -f "$mem/archive/v3/journal-late-1.md" ] || return 1
  local before; before=$(tree_state "$mem")
  [ -z "$(bash "$0" --recover-late "$mem")" ] && [ "$(tree_state "$mem")" = "$before" ]
}

case_recover_late_only_appends() {
  local mem="$1/append"; build_fixture "$mem"
  bash "$0" "$mem" > /dev/null || return 1
  printf '%s\n' '2026-09-07 obs s6 | gap local | a v4 line' >> "$mem/inbox.log"
  cp "$mem/runs.log" "$1/append-runs"; cp "$mem/inbox.log" "$1/append-inbox"
  printf '%s\n' "$LATE_RUN" "$LATE_OBS" >> "$mem/journal.md"
  bash "$0" --recover-late "$mem" > /dev/null || return 1
  starts_with_bytes_of "$mem/runs.log" "$1/append-runs" && starts_with_bytes_of "$mem/inbox.log" "$1/append-inbox" \
    && [ "$(wc -l < "$mem/runs.log")" -eq $(($(wc -l < "$1/append-runs") + 1)) ] \
    && [ "$(wc -l < "$mem/inbox.log")" -eq $(($(wc -l < "$1/append-inbox") + 1)) ]
}

# A PATH wrapper that makes `ln` fail when it would create <mem>/runs.log.
install_failing_ln_for_runs_log() {
  local bin="$1" real_ln; real_ln="$(command -v ln)"
  mkdir -p "$bin"
  printf '#!/usr/bin/env bash\ncase "${@: -1}" in */runs.log) echo "ln: cannot link runs.log" >&2; exit 1 ;; esac\nexec %s "$@"\n' \
    "$real_ln" > "$bin/ln"
  chmod +x "$bin/ln"
}

case_late_obs_with_failed_runs_log_finishes_on_rerun() {
  local mem="$1/lateln" bin="$1/lateln-bin"; build_fixture "$mem"
  mkdir -p "$bin"
  printf '#!/usr/bin/env bash\ncase "$1" in *journal.md) printf "%%s\\n" "%s" >> "$1" ;; esac\nexec %s "$@"\n' \
    "$LATE_OBS" "$(command -v mv)" > "$bin/mv"
  chmod +x "$bin/mv"
  install_failing_ln_for_runs_log "$bin"
  PATH="$bin:$PATH" bash "$0" "$mem" > /dev/null 2>&1 && return 1
  [ ! -e "$mem/runs.log" ] || return 1
  bash "$0" "$mem" > /dev/null || return 1
  [ "$(grep -cxF "$LATE_OBS" "$mem/inbox.log")" -eq 1 ] && is_v4 "$mem" || return 1
  [ ! -e "$mem/archive/v3/$PARTIAL_MARKER" ] && [ -z "$(bash "$0" --recover-late "$mem")" ]
}

case_recover_late_after_a_log_missing_its_last_newline() {
  local mem="$1/nonl"; build_fixture "$mem"
  bash "$0" "$mem" > /dev/null || return 1
  printf '%s' '2026-09-07 run s7 | hand edit, no newline' >> "$mem/runs.log"
  printf '%s\n' "$LATE_RUN" >> "$mem/journal.md"
  bash "$0" --recover-late "$mem" > /dev/null || return 1
  grep -qxF '2026-09-07 run s7 | hand edit, no newline' "$mem/runs.log" && grep -qxF "$LATE_RUN" "$mem/runs.log" || return 1
  [ -z "$(bash "$0" --recover-late "$mem")" ]
}

starts_with_bytes_of() {
  [ "$(head -c "$(wc -c < "$2")" "$1" | cksum)" = "$(cksum < "$2")" ]
}

case_stop_before_v3_rename_retries() {
  local mem="$1/stage" bin="$1/stage-bin"; build_fixture "$mem"; install_failing_mv "$bin" '.v3-staging.*'
  PATH="$bin:$PATH" bash "$0" "$mem" > /dev/null 2>&1 && return 1
  [ ! -e "$mem/archive/v3" ] && [ -f "$mem/journal.md" ] || return 1
  bash "$0" "$mem" > /dev/null || return 1
  is_v4 "$mem" && [ ! -e "$mem/archive/v3/$PARTIAL_MARKER" ] || return 1
  [ -z "$(find "$mem" -maxdepth 1 -name '.v3-staging.*')" ]
}

case_stage_cleanup_leaves_other_content() {
  local mem="$1/stagekeep"; build_fixture "$mem"
  mkdir -p "$mem/.v3-staging.user/archive"; printf 'keep\n' > "$mem/.v3-staging.user/archive/notes.md"
  : > "$mem/.v3-staging.user/$PARTIAL_MARKER"
  local before; before=$(tree_state "$mem/.v3-staging.user")
  bash "$0" "$mem" > /dev/null || return 1
  [ "$(tree_state "$mem/.v3-staging.user")" = "$before" ] && is_v4 "$mem"
}

case_rerun_never_removes_user_files() {
  local mem="$1/userfiles"; build_fixture "$mem"
  bash "$0" "$mem" > /dev/null || return 1
  cp "$mem/runs.log" "$mem/.stage.user-copy"; : > "$mem/.stage.user-empty"
  printf 'mine\n' > "$mem/archive/v3/$PARTIAL_MARKER"
  local before; before=$(tree_state "$mem")
  bash "$0" "$mem" > /dev/null || return 1
  bash "$0" --recover-late "$mem" > /dev/null || return 1
  [ "$(tree_state "$mem")" = "$before" ]
}

case_stop_before_finalize_is_finished_by_a_rerun() {
  local mem="$1/fin"; build_fixture "$mem"
  bash "$0" "$mem" > /dev/null || return 1
  # The state a stop right after runs.log's ln leaves: marker and staging still there, and a
  # late line in the moved journal not yet appended.
  : > "$mem/archive/v3/$PARTIAL_MARKER"; mkdir -p "$mem/archive/v3/$STAGING"
  cp "$mem/runs.log" "$mem/archive/v3/$STAGING/.stage.ABCDEFGH"
  printf '%s\n' "$LATE_RUN" "$LATE_OBS" >> "$mem/archive/v3/journal.md"
  bash "$0" "$mem" > /dev/null || return 1
  grep -qxF "$LATE_RUN" "$mem/runs.log" && grep -qxF "$LATE_OBS" "$mem/inbox.log" || return 1
  [ ! -e "$mem/archive/v3/$PARTIAL_MARKER" ] && [ ! -e "$mem/archive/v3/$STAGING" ] || return 1
  local before; before=$(tree_state "$mem")
  bash "$0" "$mem" > /dev/null && [ "$(tree_state "$mem")" = "$before" ]
}

case_symlinked_v3_without_journal_refuses() {
  local mem="$1/symfin" tgt="$1/symfin-target"; build_fixture "$mem"
  mkdir -p "$tgt/archive"; : > "$tgt/$PARTIAL_MARKER"; mv "$mem/journal.md" "$tgt/journal.md"
  ln -s "$tgt" "$mem/archive/v3"
  local before; before=$(tree_state "$tgt")
  bash "$0" "$mem" > /dev/null 2>&1 && return 1
  [ "$(tree_state "$tgt")" = "$before" ] && [ ! -e "$mem/runs.log" ]
}

case_interrupted_stage_cleanup_is_removed() {
  local mem="$1/stagecut"; build_fixture "$mem"
  mkdir -p "$mem/.v3-staging.aaaaaa" "$mem/.v3-staging.bbbbbb"; : > "$mem/.v3-staging.aaaaaa/$PARTIAL_MARKER"
  bash "$0" "$mem" > /dev/null || return 1
  [ -z "$(find "$mem" -maxdepth 1 -name '.v3-staging.*')" ] && is_v4 "$mem"
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
  check "a recovery appends to a sentinel-only inbox, same inode, bytes kept" case_recovery_appends_to_a_sentinel_only_inbox "$dir"
  check "a recovery refuses an inbox without its sentinel and leaves it untouched" case_recovery_refuses_an_inbox_without_sentinel "$dir"
  check "a partial move, retried, finishes with every run and obs line" case_partial_move_then_retry_finishes "$dir"
  check "a partial move whose next entry collides refuses and moves nothing" case_partial_move_with_a_collision_refuses "$dir"
  check "a foreign archive/v3 refuses and moves nothing" case_foreign_v3_dir_refuses "$dir"
  check "a stop before archive/v3 is renamed into place leaves no unmarked v3; a retry finishes" case_stop_before_v3_rename_retries "$dir"
  check "a staging-named directory with other content is left byte-identical" case_stage_cleanup_leaves_other_content "$dir"
  check "a re-run never removes a user file, even one named like a stage or the marker" case_rerun_never_removes_user_files "$dir"
  check "a stop before the last step is finished by a re-run: late lines in, marker and staging gone" case_stop_before_finalize_is_finished_by_a_rerun "$dir"
  check "a symlinked archive/v3 with no top-level journal refuses, target untouched" case_symlinked_v3_without_journal_refuses "$dir"
  check "staging directories an interrupted cleanup leaves are removed" case_interrupted_stage_cleanup_is_removed "$dir"
  check "a foreign archive/v3 of partial-move shape, without the marker, refuses" case_foreign_v3_of_partial_shape_refuses "$dir"
  check "a retry after a stop at journal.md matches a clean run, nested run kept" case_retry_after_journal_stop_matches_a_clean_run "$dir"
  check "a retry after a stop mid-archive matches a clean run, nested run kept" case_retry_after_mid_archive_stop_matches_a_clean_run "$dir"
  check "a line appended to journal.md after the build is recovered" case_line_appended_after_build_is_recovered "$dir"
  check "--recover-late takes a stray journal.md once, then is silent" case_recover_late_takes_a_stray_journal_once "$dir"
  check "--recover-late only appends to runs.log and inbox.log" case_recover_late_only_appends "$dir"
  check "a late obs plus a failed runs.log finishes on re-run, obs once" case_late_obs_with_failed_runs_log_finishes_on_rerun "$dir"
  check "--recover-late on a log missing its last newline appends a separate line once" case_recover_late_after_a_log_missing_its_last_newline "$dir"
  rm -rf "$dir"
  [ "$T_FAILS" -eq 0 ]
}

main "$@"
