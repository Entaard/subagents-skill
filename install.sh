#!/usr/bin/env bash
# Installs Sage and its companion agents and skills for Claude Code into ~/.claude/.
# Run this after every `git pull` to pick up changes.
set -euo pipefail

# rsync is the one external tool this installer cannot do without. Every section below copies
# through it — Sage, the agents, the eco-skill loop, the output styles — and the agent copy is
# unconditional, so there is no install path that skips it. Under `set -euo pipefail` an absent
# rsync aborts the run AT that first sync with
# nothing but the shell's own "command not found": after the backup root has been named, before a
# single file is placed, and with no line saying which tool was missing or that the install is now
# half-done. Fail here instead, while nothing has been touched. This is a preflight rather than
# four guards at the four call sites precisely because rsync is not optional — jq gets its guards
# down at the two optional hook sections because those features are, and a guard belongs where the
# thing it protects can legitimately be skipped.
if ! command -v rsync >/dev/null 2>&1; then
  echo "ERROR: rsync is required but was not found on PATH." >&2
  echo "  Every step of this installer copies through it (skills, agents, eco skills, output styles)." >&2
  echo "  Nothing has been installed or modified. Install rsync and re-run:" >&2
  echo "    macOS:         brew install rsync   (or use the system /usr/bin/rsync if PATH is masking it)" >&2
  echo "    Debian/Ubuntu: sudo apt install rsync" >&2
  exit 1
fi

# The installed sage-claude/bin scripts are text tools built on the base POSIX toolchain, not on
# rsync: sage-lint.sh states "awk/sed/grep only, no jq" and carries its own preflight over
# awk/sed/grep/sort/cut/head (sage-claude/bin/sage-lint.sh, the "Core-tool preflight" comment) --
# sage-watch.sh and sage-alt-guard.sh call a subset of that same set (awk, sed, cut). These ship
# with the base OS on macOS and virtually every Linux distribution, so a preflight here rarely
# fires, but a minimal or container PATH can be missing one, and unlike jq below there is no
# fallback: sage-lint.sh's own answer to a missing core tool is to print one stderr line and skip
# the check entirely (exit 0, "the ledger was NOT checked") rather than fabricate a result, so an
# installer that says nothing here just ships a linter that silently never runs. jq is NOT in this
# list on purpose: sage-watch.sh and sage-alt-guard.sh both fail OPEN without it (a probe that
# names the missing tool and skips the check, a guard that allows), and the two hook sections
# further below already guard it and degrade gracefully -- jq being unavailable is not a reason to abort an
# install that does not touch either of those optional features.
missing_hard_tools=()
for _tool in awk sed grep sort cut head; do
  command -v "$_tool" >/dev/null 2>&1 || missing_hard_tools+=("$_tool")
done
if [ "${#missing_hard_tools[@]}" -gt 0 ]; then
  echo "ERROR: missing required tool(s) on PATH: ${missing_hard_tools[*]}" >&2
  echo "  sage-lint.sh (and parts of sage-watch.sh, sage-alt-guard.sh) cannot run without them." >&2
  echo "  Nothing has been installed or modified. Install the missing tool(s) and re-run:" >&2
  # awk/sed/grep/sort/cut/head ship in macOS's own /usr/bin and are essentially never actually
  # absent there -- unlike rsync (a separate, real, uninstalled binary on a bare macOS), a miss
  # here almost always means a PATH that shadows /usr/bin (a from-source coreutils/busybox/etc
  # earlier on PATH, or a stripped-down PATH set by a wrapper), not a package to install. Naming
  # a brew formula anyway would mislead: `brew install coreutils` installs `gsort`/`gcut`/`ghead`
  # (g-prefixed, so `sort` on PATH still resolves to nothing), and the same is true of the
  # gawk/gnu-sed formulas for awk/sed. So this line points at the PATH, not at a formula.
  echo "    macOS:         these ship with the base system (/usr/bin); check 'echo \$PATH' for" >&2
  echo "                   an entry ahead of /usr/bin that shadows it" >&2
  echo "    Debian/Ubuntu: sudo apt install coreutils gawk sed grep   (installs sort/cut/head, awk, sed, grep)" >&2
  exit 1
fi

# SOFT: jq is not required by any hard install path, and both scripts that use it fail open
# without it (sage-watch.sh's --status probe names the miss and skips the check rather than
# alarming; sage-alt-guard.sh allows rather than blocks) -- so its absence must never abort this
# installer, and the two existing guards at the alt-lane guard hook offer and the compaction hook
# install below already handle that at the point each optional feature would be applied. This is a
# SEPARATE, additional report: the whole point of an install-time preflight is that a user learns
# once, up front, what degrades, instead of meeting the same fact three sentences at a time as
# each optional feature quietly skips itself later in this run.
# Probe jq the way its two consumers do, not just on PATH: sage-watch.sh:235 and
# sage-alt-guard.sh:122 both fall back to /usr/bin/jq for exactly the stripped-PATH case the
# hard-tool comment above calls the realistic one. Testing PATH alone reports a degradation
# that is not one on any macOS box whose PATH omits /usr/bin but still has jq where it ships.
if ! command -v jq >/dev/null 2>&1 && ! [ -x /usr/bin/jq ]; then
  echo "NOTE: jq was not found on PATH or at /usr/bin/jq. Three optional features degrade without it:" >&2
  echo "  - the sage-watch.sh occupancy watchdog probe (fails open: reports it cannot run, fires no rungs)" >&2
  echo "  - the sage-alt-guard.sh alt-lane guard hook: this installer SKIPS OFFERING it (the guard needs jq)" >&2
  echo "  - the SessionStart(compact) hook: this installer SKIPS INSTALLING it; a manual TIP prints instead" >&2
  echo "  Install jq for all three to work fully; the install continues without it either way:" >&2
  echo "    macOS:         brew install jq" >&2
  echo "    Debian/Ubuntu: sudo apt install jq" >&2
fi

# Neither tool is in the preflight above, whose list is what the installed sage-claude/bin scripts
# need. These two are this installer's own, and nothing below can run without them.
missing_walk_tools=()
for _tool in readlink dirname; do
  command -v "$_tool" >/dev/null 2>&1 || missing_walk_tools+=("$_tool")
done
if [ "${#missing_walk_tools[@]}" -gt 0 ]; then
  echo "ERROR: missing required tool(s) on PATH: ${missing_walk_tools[*]}" >&2
  echo "  This installer resolves its own location before it can find anything to copy." >&2
  echo "  Nothing has been installed or modified. Check 'echo \$PATH' for an entry shadowing /usr/bin." >&2
  exit 1
fi

# Walked rather than handed to `readlink -f`, whose availability is not something this script can
# check for on the machines it has to run on.
resolve_symlinks() { # resolve_symlinks <path>
  local path="$1" target hops=0
  while [ -L "$path" ]; do
    if [ "$hops" -ge 40 ]; then
      echo "ERROR: more than 40 symlinks stand between $1 and a real file." >&2
      return 1
    fi
    hops=$(( hops + 1 ))
    target="$(readlink "$path")"
    case "$target" in
      /*) path="$target" ;;
      *) path="$(dirname "$path")/$target" ;;
    esac
  done
  printf '%s\n' "$path"
}

# Reached through a symlink, the unresolved path names the link's own directory rather than the
# checkout every source path below is built from. The walk runs in a subshell, so `|| exit` is what
# ends the run on a failed one -- without it repo_dir falls back to the working directory and the
# installer copies from whatever happens to be there. `cd -P` resolves symlinked parent directories,
# which the walk does not: it only ever rewrites the last component.
script_path="$(resolve_symlinks "${BASH_SOURCE[0]}")" || exit 1
repo_dir="$(cd -P "$(dirname "$script_path")" && pwd -P)"

# Backups from every section below land in one timestamped directory per run, OUTSIDE the
# directories Claude Code auto-discovers (skills/, agents/, output-styles/). A backup inside a
# discovered directory becomes a phantom skill or agent (a discoverable clean-code.bak skill
# appeared in practice), and a fixed backup name is clobbered by the next differing install.
# The directory is created lazily, so an install that replaces nothing leaves no empty dir behind.
backups_dir="$HOME/.claude/backups/subagents-skill"
backup_root="$backups_dir/$(date +%Y%m%d-%H%M%S)-$$"

backup() { # backup <path> <category> — preserve a file or directory before it is replaced
  mkdir -p "$backup_root/$2"
  cp -R "$1" "$backup_root/$2/"
  echo "NOTE: replacing a different $(basename "$1"); previous version saved to $backup_root/$2/$(basename "$1")"
}

# backup() names the saved copy after the basename alone, which is right where one directory holds
# one candidate but wrong for the eco loop below, where two released paths in different
# subdirectories can share a basename and the second copy would silently overwrite the first — a
# backup that loses data is worse than none, because it is trusted. This variant takes the path the
# copy should have under its category and keeps it.
preserve() { # preserve <path> <category> <rel-in-category>
  local target="$backup_root/$2/$3"
  # An enclosing directory may already have been copied whole by backup() earlier in the same run,
  # in which case this path is already saved at exactly this spot. `cp -R` onto an existing
  # directory copies INSIDE it rather than over it, so repeating the copy would bury a duplicate at
  # skills/<skill>/SKILL.md/SKILL.md/ and make the saved tree unreadable. Both copies come from the
  # same unmodified live path, so the one already there is the same bytes.
  if [ -e "$target" ] || [ -L "$target" ]; then
    return 0
  fi
  mkdir -p "$(dirname "$target")"
  cp -R "$1" "$target"
}

# backup, for a condition the install reports but does not resolve, so it recurs on every run. An
# unconditional copy there stacks one full duplicate per run under ~/.claude/backups/ forever, which
# is how a safety net turns into unbounded growth. The caller's NOTE still prints every time — the
# condition is still true, and the user still needs telling — but the bytes are copied only when no
# run has already saved an identical copy.
# Only the run directories are globbed; the rest of the path is appended afterwards. Interpolating a
# name into a glob is the same mistake the eco loop had to unlearn — a basename carrying [ ] * or ?
# would match the wrong saved copy, or none.
backup_once() { # backup_once <path> <category> — preserve a path unless an identical copy is saved
  local run prior
  for run in "$backups_dir"/*; do
    prior="$run/$2/$(basename "$1")"
    if [ -e "$prior" ] && diff -rq "$1" "$prior" >/dev/null 2>&1; then
      echo "NOTE: an identical copy is already saved at $prior; not copying it again."
      return 0
    fi
  done
  backup "$1" "$2"
}

# Earlier versions of this script wrote `<name>.bak` beside the original, inside the discovered
# directories. Move any such backup produced for this repo's own names into the backup root, so
# it stops being discoverable; backups of anything this repo does not own are left where they are.
migrate_legacy_bak() { # migrate_legacy_bak <path> <category>
  [ -e "$1" ] || return 0
  mkdir -p "$backup_root/$2"
  mv "$1" "$backup_root/$2/"
  echo "NOTE: moved legacy backup $1 -> $backup_root/$2/ (backups no longer live in discovered directories)"
}

# Sage's journal does NOT get the byte comparison above, and reusing it here would be a bug.
# Every sage run appends lines to it, and /sage-promote's consolidation stage is licensed to
# drain it, so any byte comparison against the seed latches on permanently after the first run
# and then blames the seed for a change sage made itself. What it compares instead is the header
# sentinel
#
#     <!-- sage-local-memory v3 -->
#
# which claude-skills/sage-promote/references/memory-contract.md, "Structural invariants", declares as line 1 of
# journal.md and requires every drain to preserve verbatim — so it survives the rewrites a byte
# comparison cannot survive, and it moves only when the format really does. That makes the notice
# ask the question that matters, is this file still the shape the current sage expects, and go
# quiet again as soon as the answer is yes. A seed carrying no sentinel cannot be compared against,
# so it says so rather than failing open in silence.
sage_memory_sentinel() { # sage_memory_sentinel <file> — the sentinel line, empty when there is none
  sed -n -E '/sage-local-memory/{s/^[[:space:]]*//;s/[[:space:]]*$//;p;q;}' "$1"
}

drift_memory_sentinel() { # drift_memory_sentinel <seed> <installed>
  local want have
  want="$(sage_memory_sentinel "$1")"
  have="$(sage_memory_sentinel "$2")"
  if [ -z "$want" ]; then
    echo "NOTE: $1 carries no sage-local-memory sentinel, so memory-format drift cannot be checked."
    return 0
  fi
  if [ "$want" != "$have" ]; then
    echo
    echo "NOTE: sage's memory format is now \"$want\"; your memory/journal.md says"
    echo "      \"${have:-nothing}\". Your copy was left untouched, because it holds this machine's"
    echo "      numbers. This note repeats until the two sentinels match. To see what moved:"
    echo "        diff $1 $2"
  fi
}

# Sage's v3 memory is a tree whose installed copy contains user data, so it has a dedicated seed step.
# Four machine states, checked in this order:
#   v2 machine    -> local.md exists, journal.md does not: the data is this machine's numbers
#                    in the old shape, so migrate by hand (the design doc's Migration procedure),
#                    never here — auto-migrating user data is how it gets lost
#   half-migrated -> local.md AND journal.md both exist: a migration that has not finished, or a
#                    journal a run's Step 6 append created on an unmigrated machine
#   v3 machine    -> journal.md exists, local.md does not: compare its sentinel to the seed's
#   fresh machine -> neither exists: copy the seed tree once (journal.md + local/), create archive/
# local.md is tested before journal.md because the migration ends by archiving local.md — its
# presence at the top level means the migration has not finished, and a journal.md standing
# beside it must not make this machine read as v3, or the migration notice never prints again.
seed_sage_memory() { # seed_sage_memory <src> <dest>
  local seed="$1memory/local-seed" mem="$2memory"
  if [ ! -f "$seed/journal.md" ]; then
    echo "NOTE: $seed/journal.md is missing; sage's memory was not seeded."
    return 0
  fi
  if [ -f "$mem/local.md" ]; then
    echo
    if [ -f "$mem/journal.md" ]; then
      # Same repair as the v3 branch below: the directories are installer-owned and cheap, and
      # the half state must not be the one shape that leaves structural invariant 4 broken.
      mkdir -p "$mem/local" "$mem/archive"
      echo "NOTE: sage's memory migration is half-done: memory/journal.md (v3) and memory/local.md"
      echo "      (v2) both exist. Nothing was changed. Until local.md's data is migrated and the"
      echo "      file itself is moved into memory/archive/, sage cannot see the v2 numbers."
    else
      echo "NOTE: sage's memory format is now v3 — a journal plus one file per knowledge item."
      echo "      Your memory/local.md is the v2 format and was left untouched, because it holds"
      echo "      this machine's numbers. Until the migration runs, /sage-promote fails closed"
      echo "      (its preflight requires memory/journal.md) and sage runs without local memory."
    fi
    echo "      This note repeats until the migration runs. The migration is an agent task, not a"
    echo "      script: ask Claude to run the 'Migration procedure' in the source repo's"
    echo "      docs/designs/2026-08-27-sage-memory-v3-design.md against this machine's local.md."
    if [ -L "$mem/shared.md" ]; then
      echo "      Your v2 memory/shared.md symlink now dangles (its repo target moved to"
      echo "      memory/archive/shared-v2.md); the migration removes it."
    fi
    return 0
  fi
  if [ -f "$mem/journal.md" ]; then
    # The directories are cheap to re-create and nothing else repairs them, so a v3 machine
    # that lost one gets it back here rather than failing sage's invariant check later.
    mkdir -p "$mem/local" "$mem/archive"
    drift_memory_sentinel "$seed/journal.md" "$mem/journal.md"
    return 0
  fi
  mkdir -p "$mem/local" "$mem/archive"
  cp "$seed/journal.md" "$mem/journal.md"
  # An explicit loop, not `cp "$seed/local/"*.md`: under set -e an unmatched glob makes cp
  # abort the whole install after the journal landed but before local/ is populated.
  for _seed_ki in "$seed/local/"*.md; do
    [ -f "$_seed_ki" ] && cp "$_seed_ki" "$mem/local/"
  done
  printf 'Seeded %-20s-> %s\n' "journal.md + local/" "$mem/"
}

# sync_sage_shared <template-dir> <clone-dir> -- copies every file the template ships into the
# installed clone, one direction only. The template always wins: a differing clone file can only
# be a hand edit or a stale copy, never a legitimate machine-side change (/sage-promote lands its
# writes in the template first, then copies the same bytes to the clone), so it is backed up, not
# merged. A clone file the template no longer ships was retired by another machine's promote pass;
# it moves to archive/ rather than being deleted outright.
sync_sage_shared() {
  local tmpl="$1" clone="$2" archive_dir file rel
  local added=0 updated=0 archived=0

  if [ ! -d "$tmpl" ]; then
    echo "NOTE: $tmpl does not exist; sage's shared memory was not synced."
    return 0
  fi

  if [ -e "$clone" ] && [ ! -d "$clone" ]; then
    # A file or a symlink sitting where the clone directory belongs. mkdir -p below would fail
    # on it and set -e would abort the run half-done, so it is preserved and cleared first, the
    # same bargain the eco-skills loop gives a stray non-directory.
    backup "$clone" sage-memory
    rm -f "$clone"
    echo "NOTE: $clone was not a directory; replaced it with the shared-memory clone."
  fi

  archive_dir="$(dirname "$clone")/archive"
  mkdir -p "$clone"

  # One backup of the whole clone, taken before anything below is written -- not one per file --
  # so a second, unchanged run produces no backup at all.
  if shared_clone_diverges "$tmpl" "$clone"; then
    backup_once "$clone" sage-memory
  fi

  # An explicit loop, not `cp "$tmpl/"*`: under set -e an unmatched glob (an empty template)
  # would abort the install, the same reason seed_sage_memory's local/ loop above is explicit.
  for file in "$tmpl"/*; do
    [ -f "$file" ] || continue
    rel="$(basename "$file")"
    if [ -L "$clone/$rel" ]; then
      # A symlink at a template filename is never something this sync created. Writing the
      # template's bytes through `cp` onto an existing symlink follows it and clobbers whatever
      # it points at, so the link is removed first and the real file copied into its place.
      backup_symlinked_shared "$clone/$rel"
      rm -f "$clone/$rel"
      cp "$file" "$clone/$rel"
      updated=$((updated + 1))
    elif [ ! -e "$clone/$rel" ]; then
      cp "$file" "$clone/$rel"
      added=$((added + 1))
    elif [ -d "$clone/$rel" ]; then
      # A directory squatting on a template filename: `cp` onto it would nest the file inside
      # and the clone would never converge. The whole-clone backup above already preserved it.
      rm -rf "$clone/$rel"
      cp "$file" "$clone/$rel"
      updated=$((updated + 1))
    elif ! cmp -s "$file" "$clone/$rel"; then
      cp "$file" "$clone/$rel"
      updated=$((updated + 1))
    fi
  done

  for file in "$clone"/*; do
    [ -f "$file" ] || [ -L "$file" ] || [ -d "$file" ] || continue
    rel="$(basename "$file")"
    [ -f "$tmpl/$rel" ] && continue
    archive_shared_file "$file" "$archive_dir" "$rel"
    archived=$((archived + 1))
  done

  if [ "$((added + updated + archived))" -gt 0 ]; then
    printf 'Synced shared memory: %d added, %d updated, %d archived\n' "$added" "$updated" "$archived"
  fi
}

# shared_clone_diverges <template-dir> <clone-dir> -- true if sync_sage_shared's loops below
# would touch anything: a symlink or directory at a template filename, a differing file, or a
# clone-only entry (file, link, or directory).
# Answering this up front is what lets the caller take one whole-directory backup before any of
# it happens, instead of a flag threaded through both loops.
shared_clone_diverges() {
  local tmpl="$1" clone="$2" file rel
  for file in "$tmpl"/*; do
    [ -f "$file" ] || continue
    rel="$(basename "$file")"
    [ -L "$clone/$rel" ] && return 0
    [ -d "$clone/$rel" ] && return 0
    if [ -e "$clone/$rel" ] && ! cmp -s "$file" "$clone/$rel"; then
      return 0
    fi
  done
  for file in "$clone"/*; do
    [ -f "$file" ] || [ -L "$file" ] || [ -d "$file" ] || continue
    rel="$(basename "$file")"
    [ -f "$tmpl/$rel" ] || return 0
  done
  return 1
}

# backup_symlinked_shared <clone-file> -- saves the bytes a stray symlink points at, not the link
# itself. A plain `cp` on one symlink argument dereferences it by default, unlike backup_once's
# whole-directory `cp -R`, which would preserve the link and save none of the data it names. A
# dangling link has nothing to save; that failure is swallowed rather than aborting the install.
backup_symlinked_shared() {
  local path="$1" dest="$backup_root/sage-memory/$(basename "$path")"
  mkdir -p "$(dirname "$dest")"
  cp "$path" "$dest" 2>/dev/null || true
}

# archive_shared_file <file> <archive-dir> <rel> -- moves a retired clone file into archive-dir
# without clobbering an existing entry of the same name. A collision gets its own run-stamped
# name instead of silently overwriting whatever archive already holds under <rel>.
archive_shared_file() {
  local file="$1" dir="$2" rel="$3" dest
  mkdir -p "$dir"
  dest="$dir/$rel"
  if [ -e "$dest" ] || [ -L "$dest" ]; then
    dest="$dir/$(date +%Y%m%d-%H%M%S)-$$-$rel"
    echo "NOTE: $dir/$rel already exists; archiving this retired copy as $(basename "$dest") instead."
  fi
  mv "$file" "$dest"
  echo "Archived $rel (retired from the template) -> $dest"
}

# The sage skill. journal.md and local/ are user data: written by sage and /sage-promote, never
# copied from the repo, so --delete must never reach memory/ — which also means local-seed/ is
# never installed, only read from the repo by seed_sage_memory. memory/shared/ is the one
# exception: it is a clone of the repo's template (sage-claude/memory/shared/), kept in step by
# sync_sage_shared on every run, template always wins.
sage_src="$repo_dir/sage-claude/"
sage_dest="$HOME/.claude/skills/sage/"
shared_src="$repo_dir/sage-claude/memory/shared"
shared_dest="${sage_dest}memory/shared"

if [ -d "$sage_src" ]; then
  mkdir -p "$sage_dest"
  rsync -av --delete --exclude='/memory/' "$sage_src" "$sage_dest"
  seed_sage_memory "$sage_src" "$sage_dest"

  # A v3.0 install left an absolute symlink here, pointing straight into the repo. The symlink
  # itself holds no data to preserve — rm removes the link, never the file it points at — so the
  # migration is just: drop the link and let sync_sage_shared below stand up a real clone, exactly
  # as it would on a fresh machine.
  if [ -L "$shared_dest" ]; then
    _old_shared_target="$(readlink "$shared_dest")"
    rm -f "$shared_dest"
    echo "NOTE: $shared_dest was the old v3.0 symlink (-> $_old_shared_target); replaced it with a"
    echo "      real directory synced from the template. Nothing under local/, journal.md, or"
    echo "      archive/ was touched."
    unset _old_shared_target
  fi
  sync_sage_shared "$shared_src" "$shared_dest"
  mkdir -p "${sage_dest}memory"
  echo "$repo_dir" > "${sage_dest}memory/source-repo"

  # rsync -a carries the source mode across, so this only matters when the repo's copy lost its
  # executable bit (a zip download, a checkout with no exec support). The watchdog is spawned as a
  # command, so a probe that is not executable disables the watchdog on every run.
  for _sage_bin in sage-watch.sh sage-lint.sh sage-alt-guard.sh sage-index.sh; do
    if [ -f "${sage_dest}bin/$_sage_bin" ]; then
      chmod +x "${sage_dest}bin/$_sage_bin"
    fi
  done
  unset _sage_bin
fi

# Agent files have to live in ~/.claude/agents/; Claude Code does not discover them inside a skill
# directory. No --delete here: other agents in that directory are not this script's to remove.
# Two narrow exceptions, both of which identify this script's own output before deleting it and
# both of which back it up first: the retired-orchestrator removal below, keyed on the description
# this repo shipped, and the alt-agent removal pass further down, keyed on the generated-file
# marker this script wrote.
#
# NOTE: ~/.claude/agents/ is GLOBAL. Claude Code watches it and can auto-delegate to these agents in
# any project, based on their `description` field. All the descriptions are written to say they are
# dispatched by name from an orchestration plan, and to send ordinary lookups to the built-in
# Explore agent instead, so they should not capture routine work. Sage dispatches them. Delete them
# from ~/.claude/agents/ if you would rather they not exist outside Sage.
agents_src="$repo_dir/claude-agents/"
agents_dest="$HOME/.claude/agents/"

mkdir -p "$agents_dest"

# Names like 'explorer' or 'implementer' are generic enough to collide with an agent you
# already wrote. Back up anything we are about to replace rather than overwriting it silently.
skip_agents=()
for f in "$agents_src"*.md; do
  name="$(basename "$f")"
  existing="$agents_dest$name"
  migrate_legacy_bak "$existing.bak" agents
  if [ -e "$existing" ] && [ ! -f "$existing" ]; then
    # A directory sitting where an agent file belongs. rsync cannot replace it, fails with
    # "unlinkat: Directory not empty" (exit 23), and set -e then aborts the run, so nothing after
    # this point installs at all. Skip this one name instead of clearing it: the path is a
    # directory the user may have made deliberately, and emptying it would mean rm -rf on their
    # data. Same bargain the symlinked skill directory gets below.
    echo "NOTE: $existing is not a regular file; skipping $name."
    skip_agents+=(--exclude="$name")
    continue
  fi
  if [ -f "$existing" ] && ! cmp -s "$f" "$existing"; then
    backup "$existing" agents
  fi
done

rsync -av ${skip_agents[@]+"${skip_agents[@]}"} "$agents_src" "$agents_dest"

# claude-agents/ ships no orchestrator agent, so the rsync above cannot retire the one an earlier
# version installed, and nothing here runs --delete. The description this repo gave that file is
# what tells its copy apart from an agent of the user's own under the same generic name.
retired_orchestrator="Successor unit for the sage orchestration skill"
orchestrator_dest="${agents_dest}orchestrator.md"
if [ -e "$orchestrator_dest" ] || [ -L "$orchestrator_dest" ]; then
  if [ -f "$orchestrator_dest" ] && [ ! -L "$orchestrator_dest" ] &&
     grep -m1 '^description:' "$orchestrator_dest" | grep -qF "$retired_orchestrator"; then
    backup "$orchestrator_dest" agents
    rm -f "$orchestrator_dest"
    echo "Removed the retired orchestrator agent -> $orchestrator_dest (previous version saved to $backup_root/agents/orchestrator.md)"
  else
    echo "NOTE: $orchestrator_dest is an orchestrator.md of your own, not the retired sage one;"
    echo "      leaving it in place."
  fi
fi

# Alt agents are the same three reader roles, on a model outside this harness's own family
# when the machine serves one. Never a different role. Never a name this repo hardcodes.
# The templates live in claude-agents-alt/, a SIBLING of claude-agents/, never a subdirectory of it.
# The rsync above has no exclude for a subdirectory. The backup guard above it globs only
# "$agents_src"*.md. A subdirectory file would be copied to ~/.claude/agents/ wholesale, with no
# backup. A sibling directory sits outside both and cannot be reached by either.
#
# No model name is hardcoded anywhere here or in a template's frontmatter. The machine supplies the
# name through a config file this script only reads. The repo ships `__ALT_MODEL__` placeholders.
# That placeholder is the only thing that keeps a checkout installable on a machine served by a
# different gateway. `/v1/models` cannot be probed for candidates either. The gateway this design
# was built against returns a single placeholder id for every machine, so auto-detection is not
# attempted.
alt_src="$repo_dir/claude-agents-alt/"

if [ -d "$alt_src" ]; then
  alt_conf="${SUBAGENTS_ALT_CONF:-$HOME/.claude/subagents-alt-models.conf}"
  alt_installed=0
  # Every template name this run could have installed. The removal pass below can then tell
  # "opted out" from "never offered", without re-globbing $alt_src a second time.
  alt_names=()
  for tpl in "$alt_src"*.md.in; do
    [ -e "$tpl" ] || continue
    alt_names+=("$(basename "$tpl" .md.in)")
  done

  # Config present -> render the enabled roles. Absent -> install none. Both are DECIDED states, so
  # the removal pass below runs on either: turning the config off, or never having had one, means
  # no alt agent survives on this machine.
  #
  # A directory, an unreadable file, or a dangling symlink at the config path is NOT a decided
  # state. It is a config this run could not read, and the two must never collapse into one
  # outcome. They did: the branches below printed NOTE-and-skip while `enabled_names` stayed unset,
  # and the removal pass then deleted every installed alt agent and reported them as "no longer
  # enabled" — they were still enabled; the file was just unreachable. An unmounted path, a
  # permissions slip, or a mistyped SUBAGENTS_ALT_CONF silently uninstalled the whole lane. So
  # `alt_conf_known` separates "the config says none" from "the config could not be read", and the
  # removal pass runs only on the first. One bad path here still cannot abort the install; it now
  # cannot delete anything either.
  alt_conf_known=1
  alt_conf_dir="$(dirname "$alt_conf")"
  if [ -L "$alt_conf" ] && [ ! -e "$alt_conf" ]; then
    echo "NOTE: $alt_conf is a symlink to a path that does not exist; skipping the alt-model config."
    alt_conf_known=0
  elif [ -e "$alt_conf" ] && [ ! -f "$alt_conf" ]; then
    echo "NOTE: $alt_conf is not a regular file; skipping the alt-model config."
    alt_conf_known=0
  elif [ -f "$alt_conf" ] && [ ! -r "$alt_conf" ]; then
    echo "NOTE: $alt_conf is not readable; skipping the alt-model config."
    alt_conf_known=0
  elif [ ! -e "$alt_conf" ] && { [ ! -d "$alt_conf_dir" ] || [ ! -x "$alt_conf_dir" ]; }; then
    # An absent config is normally a decided opt-out, and the removal pass below is meant to run on
    # it. But "absent" and "unreachable" look identical to `[ -f ]`, and only one of them is a
    # decision. A path on an unmounted volume, a typo in SUBAGENTS_ALT_CONF, or a home directory
    # this run cannot traverse all report the file as absent, and treating that as an opt-out
    # deleted the whole lane — the very scenario the flag above was added to prevent, still open
    # because the check tested the file and never its directory. So an absent file counts as a
    # decision only when the directory that would hold it exists and can be entered.
    echo "NOTE: $alt_conf_dir does not exist or cannot be entered, so $alt_conf cannot be read"
    echo "      (an unmounted path or a typo in SUBAGENTS_ALT_CONF looks exactly like an absent"
    echo "      config). Skipping the alt-model config."
    alt_conf_known=0
  elif [ -f "$alt_conf" ]; then
    enabled_names=()
    # Names already claimed by an earlier line in this same config. A role named twice must not
    # render and back up over its own first render. Its second backup() call would overwrite the
    # first saved copy with this run's own output, and that loses the user's real file for good.
    seen_names=()
    while IFS= read -r line || [ -n "$line" ]; do
      # Trim first, then classify. Classifying the raw line made a whitespace-only line and an
      # indented '# comment' both fall through to the "has no '='" NOTE, contradicting the tip this
      # same script prints ("Blank lines and '#' comments are ignored"). The trim also strips a
      # trailing CR, so a CRLF config needs no separate handling.
      line="${line#"${line%%[![:space:]]*}"}"; line="${line%"${line##*[![:space:]]}"}"
      case "$line" in
        ''|'#'*) continue ;;
      esac
      case "$line" in
        *=*) ;;
        *) echo "NOTE: $alt_conf: '$line' has no '=', skipping."; continue ;;
      esac
      name="${line%%=*}"
      model="${line#*=}"
      # Trim surrounding whitespace from both halves.
      name="${name#"${name%%[![:space:]]*}"}"; name="${name%"${name##*[![:space:]]}"}"
      model="${model#"${model%%[![:space:]]*}"}"; model="${model%"${model##*[![:space:]]}"}"

      if [ -z "$model" ]; then
        echo "NOTE: $alt_conf: '$name' has no model, skipping."
        continue
      fi
      # A name carrying '/' can still match a template by accident (./explorer-alt). The
      # removal pass below then compares against the bare template name, never recognizes this
      # enabled name, and deletes the file this same run just wrote. Reject it here, before the
      # template lookup.
      case "$name" in
        */*) echo "NOTE: $alt_conf: '$name' contains '/', skipping."; continue ;;
      esac
      tpl="$alt_src$name.md.in"
      if [ ! -f "$tpl" ]; then
        echo "NOTE: $alt_conf: '$name' names no matching template ($tpl); skipping."
        continue
      fi
      dup=0
      for sn in ${seen_names[@]+"${seen_names[@]}"}; do
        [ "$sn" = "$name" ] && dup=1 && break
      done
      if [ "$dup" -eq 1 ]; then
        echo "NOTE: $alt_conf: '$name' is named more than once; using the first line, skipping this one."
        continue
      fi
      seen_names+=("$name")
      enabled_names+=("$name")

      # verifier-alt is the one twin whose value IS its model family: it exists to be the checker
      # half of a maker/checker pair, and that is the one benefit no same-family model can supply.
      # An Anthropic model here installs a same-family checker wearing an alt name, while its own
      # description claims the diversity — the exact false claim this lane exists to make honest.
      # The other two twins buy price and window headroom, where an Anthropic model is a perfectly
      # good choice, so this checks verifier-alt alone.
      #
      # It warns and installs anyway rather than skipping. The config is the user's call, this
      # pattern cannot know every non-Anthropic model name, and refusing to install would turn a
      # questionable model choice into no checker at all. The run that would be misled by a
      # same-family checker is a later one, and it has the report's MODEL-FAMILY: line to catch it.
      if [ "$name" = "verifier-alt" ]; then
        case "$model" in
          claude*|*haiku*|*sonnet*|*opus*)
            echo "NOTE: $alt_conf: verifier-alt is set to '$model', which looks like an Anthropic"
            echo "      model. verifier-alt exists to be a checker from a different model family, so"
            echo "      that setting gives it no diversity to offer. Installing it as configured;"
            echo "      set a non-Anthropic model if you want the maker/checker diversity."
            ;;
        esac
      fi

      dest="$agents_dest$name.md"
      if [ -e "$dest" ] && [ ! -f "$dest" ]; then
        echo "NOTE: $dest is not a regular file; skipping $name."
        continue
      fi

      # Index-based substitution, not sed or awk's sub(). A model name can carry / [ ] & or \.
      # A regex-replacement tool treats every one of those specially in the replacement text.
      # `awk -v` is not safe here either: `-v` runs escape-sequence processing on the value it
      # assigns, so a `\` in a model name is consumed before `index()` ever runs. Passing the model
      # through the environment, and reading it back with `ENVIRON`, does no escape processing. So
      # `\` and every other character in the model string reach the substitution literally. This
      # form is also POSIX awk, not a GNU-only extension.
      rendered="$(mktemp "${dest}.XXXXXX")" || {
        echo "NOTE: could not create a temp file to render $name; skipping."
        continue
      }
      if ! m="$model" awk '{
             i = index($0, "__ALT_MODEL__")
             if (i) print substr($0,1,i-1) ENVIRON["m"] substr($0, i+length("__ALT_MODEL__"))
             else print
           }' "$tpl" > "$rendered"; then
        echo "NOTE: failed to render $tpl for '$name'; skipping."
        rm -f "$rendered"
        continue
      fi

      if [ -f "$dest" ]; then
        if cmp -s "$rendered" "$dest"; then
          rm -f "$rendered" # identical content already installed; no backup, nothing to move
          alt_installed=$((alt_installed + 1))
          continue
        fi
        backup "$dest" agents
      fi
      # mktemp creates its file 0600, and mv keeps that mode. Every other file this installer
      # places is 0644. Match that mode before the move, rather than leaving alt agents oddly
      # locked down.
      chmod 644 "$rendered"
      mv "$rendered" "$dest"
      alt_installed=$((alt_installed + 1))
    done < "$alt_conf"
    if [ "$alt_installed" -eq 0 ]; then
      echo "NOTE: $alt_conf exists but enables no alt agent. Uncomment a role and set its model to"
      echo "      turn one on: $alt_conf"
    fi
  fi

  # Removal pass: a template name with no enabled config line loses its installed agent, but only
  # the copy this installer generated. A marker-carrying file is this installer's own output,
  # safe to remove after a backup. A file with no marker is the user's. It is left alone in
  # silence. This rule is narrower than install.sh's usual "no --delete in agents/" rule, not wider.
  alt_marker="<!-- subagents-skill: generated alt agent — regenerate with install.sh, do not hand-edit -->"
  if [ "$alt_conf_known" -eq 0 ]; then
    echo "NOTE: leaving any installed alt agent in place, since $alt_conf could not be read."
    echo "      Fix the path and re-run to apply what the config actually says."
  else
  for name in ${alt_names[@]+"${alt_names[@]}"}; do
    keep=0
    for en in ${enabled_names[@]+"${enabled_names[@]}"}; do
      [ "$en" = "$name" ] && keep=1 && break
    done
    [ "$keep" -eq 1 ] && continue

    dest="$agents_dest$name.md"
    if [ -f "$dest" ] && grep -qxF "$alt_marker" "$dest"; then
      mkdir -p "$backup_root/agents"
      cp "$dest" "$backup_root/agents/"
      rm -f "$dest"
      echo "Removed alt agent no longer enabled -> $dest (previous version saved to $backup_root/agents/$(basename "$dest"))"
    fi
  done
  fi

fi

# This decides whether the TIP heredoc's alt-lane paragraph is worth printing. A machine with no
# config file, and no alt agent installed, sees nothing new. Criterion 1 stays true byte-for-byte
# on that machine: behavior is exactly as before. ANTHROPIC_BASE_URL is not part of this test. It
# marks any Anthropic-compatible proxy, including a corporate proxy in front of the plain API.
# Most machines that set it serve no alt model at all.
alt_lane_relevant=0
if [ -d "$alt_src" ]; then
  if [ -f "$alt_conf" ] || [ "${alt_installed:-0}" -gt 0 ]; then
    alt_lane_relevant=1
  fi
fi

# An installed skill directory holds two kinds of thing: the files this repo ships, and whatever the
# skill itself wrote there at runtime. The two are told apart structurally — no filename this script
# has to be taught, because the point is that ANY eco skill may start writing beside itself and must
# not be punished for it. A destination path with no source counterpart is the subject of the four
# helpers below, and it needs handling in two places at once:
#
#   - Ignoring it in the comparison stops it triggering a backup of the whole skill directory on
#     every install, forever. `diff -rq` exits non-zero on an only-in-destination file, so the backup
#     fired, changed nothing, and fired again next time.
#   - Leaving it off the deletion list stops the sync removing it, which it did on every install.
#
# Either fix alone leaves the other half of the bug doing damage, so they ship together.
#
# One case does not fall out of "no source counterpart": a file the repo used to ship and dropped
# looks exactly like a file the skill wrote. Those still have to go, or a renamed reference lingers
# in the install and the model reads the stale copy forever. Telling them apart needs one bit of
# history, so each install leaves a manifest of what it shipped. Listed in the last manifest and
# gone from the source -> shipped once, not shipped now, it is deleted. In no manifest -> runtime
# data, protected. An install with no manifest to consult protects everything it does not
# recognise; that is the safe direction, and it self-corrects from the next install onward.
#
# The manifest is the deletion authority, so where it lives is a safety property and not a filing
# decision. It used to live inside the skill directory it governs, and that put it inside the one
# tree this whole section exists to say we do not control: the skill writes there at runtime, so
# anything able to write beside itself could rewrite the list of what gets deleted, and the
# redirect that rewrote it each run would follow a symlink planted at that path out to any file on
# the machine, or die on a directory and take the rest of the install with it. Moving it here puts
# it somewhere no skill writes, which retires all three at the root rather than one at a time. The
# leading dot keeps it out of backup_once's "$backups_dir"/* glob over run directories; it is not a
# run and must never be mistaken for one.
manifests_dir="$backups_dir/.manifests"

# What the manifest was called back when it lived in the skill directory. Kept only to adopt one on
# the first install after the move.
legacy_manifest=".install-manifest"

# True when every path under <src> exists under <dest> with identical content. Deliberately
# one-directional: destination-only paths are runtime data and say nothing about whether the
# shipped files were modified. A source-only path still counts as a difference, and the backup it
# triggers is a one-shot — after the install the destination matches and it goes quiet.
src_matches_dest() { # src_matches_dest <src> <dest>
  local src="${1%/}" dest="${2%/}" rel
  while IFS= read -r rel; do
    rel="${rel#./}"
    if [ -d "$src/$rel" ]; then
      [ -d "$dest/$rel" ] || return 1
    else
      cmp -s "$src/$rel" "$dest/$rel" || return 1
    fi
  done < <(cd "$src" && find . -mindepth 1)
  return 0
}

# Every destination path with no source counterpart, relative to <dest>, one per line. A path
# inside a directory that is itself destination-only is skipped: excluding the directory already
# protects the whole subtree.
dest_only_paths() { # dest_only_paths <src> <dest>
  local src="${1%/}" dest="${2%/}" rel parent
  [ -d "$dest" ] || return 0
  while IFS= read -r rel; do
    rel="${rel#./}"
    parent="$(dirname "$rel")"
    if [ "$parent" != "." ] && [ ! -d "$src/$parent" ]; then
      continue
    fi
    [ -e "$src/$rel" ] || echo "$rel"
  done < <(cd "$dest" && find . -mindepth 1)
}

# Every destination path rsync cannot write through, relative to <dest>: a directory standing where
# <src> ships a file. rsync clears one of those only under --delete, which the eco loop no longer
# uses, so the caller has to clear it or the transfer dies with "unlinkat: Directory not empty" and
# takes the rest of the install down with it. Only this direction needs help; a file standing where
# <src> ships a directory rsync replaces on its own.
dest_type_conflicts() { # dest_type_conflicts <src> <dest>
  local src="${1%/}" dest="${2%/}" rel
  [ -d "$dest" ] || return 0
  while IFS= read -r rel; do
    rel="${rel#./}"
    if [ -d "$dest/$rel" ] && [ ! -L "$dest/$rel" ] && [ -f "$src/$rel" ]; then
      echo "$rel"
    fi
  done < <(cd "$dest" && find . -mindepth 1)
}

# True when <rel> is a leftover the repo used to ship and no longer does, so it may be deleted:
# the last manifest lists it, and — for a directory — lists everything inside it too, so no runtime
# file rides along inside a directory being removed. Everything else is runtime data and is kept.
eco_release() { # eco_release <installed-dir> <manifest> <rel>
  local dir="$1" manifest="$2" rel="$3" sub
  [ -f "$manifest" ] || return 1
  grep -qxF "$rel" "$manifest" || return 1
  [ -d "$dir/$rel" ] || return 0
  while IFS= read -r sub; do
    grep -qxF "$rel/${sub#./}" "$manifest" || return 1
  done < <(cd "$dir/$rel" && find . -mindepth 1)
  return 0
}

# Ecosystem skills (every directory under claude-skills/) live beside Sage in ~/.claude/skills/,
# one directory per skill. Their names are chosen to coexist with the
# separately installed mattpocock skills (tdd, code-review); this script never touches those.
# Same conflict-safe copy as agents above: back up a same-named skill with different content,
# never delete skills this repo doesn't own, refuse to replace a symlink — a symlink is another
# installer's property — and clear a stray non-directory rather than aborting the run on it.
eco_src="$repo_dir/claude-skills/"
eco_dest="$HOME/.claude/skills/"

if [ -d "$eco_src" ]; then
  # Losing the manifest directory must not truncate the install, which is the failure mode the
  # guards in this script keep having to undo. With nowhere to record what was shipped, the loop
  # falls back to the safe direction it already takes on a first install: recognise nothing, delete
  # nothing. Every later branch reads an empty manifests_dir as exactly that.
  if ! mkdir -p "$manifests_dir" 2>/dev/null; then
    echo "NOTE: cannot create $manifests_dir, so no manifest is written or read this run and"
    echo "      nothing under $eco_dest is deleted. Clear that path to re-enable deletion."
    manifests_dir=""
  fi
  for d in "$eco_src"*/; do
    [ -d "$d" ] || continue
    name="$(basename "$d")"
    existing="$eco_dest$name"
    if [ -L "$existing" ]; then
      echo "NOTE: $existing is a symlink owned by another installer; skipping $name."
      continue
    fi
    migrate_legacy_bak "$existing.bak" skills
    if [ -d "$existing" ] && ! src_matches_dest "$d" "$existing"; then
      backup "$existing" skills
    elif [ -e "$existing" ] && [ ! -d "$existing" ]; then
      # A stray file sitting where a skill directory belongs. Without this branch mkdir -p fails on
      # it and set -e aborts the whole run, so output styles never install and the summary never
      # prints — a truncated install that looks like a crash. Preserve it, then clear the path, the
      # same bargain a differing skill directory gets above.
      backup "$existing" skills
      rm -f "$existing"
    fi
    mkdir -p "$existing"
    manifest="${manifests_dir:+$manifests_dir/$name}"
    # Installs made before the manifest moved left one inside the skill directory. Adopt it, so the
    # first install after the move still knows what it shipped last time instead of protecting a
    # whole release's worth of dropped files, and so the stale copy stops sitting in a directory
    # Claude Code reads. A plain file only: a symlink or a directory at that path is one of the
    # shapes the move exists to defuse, and its contents are never read. Anything not adopted has no
    # source counterpart and is in no manifest, so the pass below reads it as runtime data and keeps
    # it — inert, and left for the user to remove.
    if [ -n "$manifest" ] && [ ! -e "$manifest" ] && [ ! -L "$manifest" ] &&
       [ -f "$existing/$legacy_manifest" ] && [ ! -L "$existing/$legacy_manifest" ]; then
      mv "$existing/$legacy_manifest" "$manifest"
    fi
    # Deletion is driven from the manifest and performed here, not handed to rsync --delete, and
    # that is the whole reason the guarantee above holds. --delete has to be told what to spare as
    # --exclude patterns, and a pattern is a glob, not a name: a runtime file whose name carries
    # [ ] * ? or \ does not reliably match itself, the exclude misses, and --delete takes the file
    # silently. Escaping cannot rescue it, because the rules are not portable — the openrsync that
    # ships with macOS compares a pattern holding no wildcard literally, so a lone backslash must
    # be left raw, but adds one bracket and the whole pattern goes through fnmatch, where that same
    # backslash becomes an escape. A name holding both defeats any fixed escaping rule.
    #
    # Removing paths here means every deletion is an exact string that came from the same find that
    # wrote the manifest, so there is no pattern language in the protection path at all. It also
    # flips the failure direction: a name this line-oriented plumbing cannot carry — an embedded
    # newline splits one find line into two — is never named exactly, so it is never listed as
    # released, so it is kept. Over-protecting is the acceptable outcome and over-deleting is not,
    # and that now holds for every filename rather than for the ones without metacharacters.
    #
    # That is a claim about which paths are chosen, and it is only half of the promise. The other
    # half is that being chosen wrongly is survivable: every path in the list is copied out before
    # it is removed, so a deletion this pass gets wrong costs a trip to the backup root and not the
    # data. Whatever else is unforeseen about a runtime file — including a manifest that was
    # tampered with, which is a thing a list stored outside the tree makes harder and not
    # impossible — the loss is recoverable rather than final.
    eco_drop=()
    while IFS= read -r rel; do
      if eco_release "$existing" "$manifest" "$rel"; then
        eco_drop+=("$rel")
      fi
    done < <(dest_only_paths "$d" "$existing")
    # A directory standing where the repo now ships a file has to go regardless of what the manifest
    # says, or the transfer below fails outright.
    while IFS= read -r rel; do
      eco_drop+=("$rel")
    done < <(dest_type_conflicts "$d" "$existing")
    # Listed first, removed second. Removing during either walk would pull a directory out from
    # under the find still producing that walk's output.
    for rel in ${eco_drop[@]+"${eco_drop[@]}"}; do
      [ -n "$rel" ] || continue
      preserve "$existing/$rel" skills "$name/$rel"
      echo "deleting $rel (copy saved under $backup_root/skills/$name/)"
      rm -rf "$existing/$rel"
    done
    rsync -av "$d" "$existing/"
    if [ -n "$manifest" ]; then
      # The manifest is rewritten from scratch each run, and the path is cleared first because `>`
      # is not a safe way to reach an unknown path: it follows a symlink and writes through it to
      # wherever that points, and it fails outright on a directory, which under set -e aborts the
      # run and truncates the install — the exact class dest_type_conflicts() was added to prevent,
      # and which it cannot cover here because the manifest has no source counterpart to compare
      # against. rm -f removes a symlink and never its target; a directory needs rm -rf, so it is
      # copied out first. After this the path holds a regular file or nothing at all.
      if [ -d "$manifest" ] && [ ! -L "$manifest" ]; then
        preserve "$manifest" manifests "$name"
        echo "NOTE: $manifest was a directory; saved to $backup_root/manifests/$name and replaced."
        rm -rf "$manifest"
      else
        rm -f "$manifest"
      fi
      (cd "$d" && find . -mindepth 1) | sed 's|^\./||' > "$manifest"
    fi
  done
fi

# Output styles live in ~/.claude/output-styles/, one file per style. Same conflict-safe copy as
# agents above: back up anything with the same filename but different content, never delete styles
# this repo doesn't own.
styles_src="$repo_dir/output-styles/"
styles_dest="$HOME/.claude/output-styles/"

mkdir -p "$styles_dest"

skip_styles=()
for f in "$styles_src"*.md; do
  name="$(basename "$f")"
  existing="$styles_dest$name"
  migrate_legacy_bak "$existing.bak" output-styles
  if [ -e "$existing" ] && [ ! -f "$existing" ]; then
    # Same non-file collision as the agents loop above, and the same reason for skipping rather
    # than clearing. This one aborts last, so it costs only the style and the closing summary.
    echo "NOTE: $existing is not a regular file; skipping $name."
    skip_styles+=(--exclude="$name")
    continue
  fi
  if [ -f "$existing" ] && ! cmp -s "$f" "$existing"; then
    backup "$existing" output-styles
  fi
done

rsync -av ${skip_styles[@]+"${skip_styles[@]}"} "$styles_src" "$styles_dest"

# offer_alt_guard_hook: the one sage rule with a deterministic predicate and zero legitimate
# exceptions — an alt-lane dispatch must carry NO model parameter, because the parameter wins over
# the agent file and silently deletes the outside-family model the row exists to buy. Prose has
# stated it three times and a measured run broke it anyway (figure and full account:
# sage-claude/references/alt-lane.md). Offered, never imposed, and offered with
# the same care as the compaction hook this installer writes:
# ~/.claude/settings.json holds arbitrary other config that this script does not own.
# The guard itself fails OPEN on every unrecognised payload — see sage-claude/bin/sage-alt-guard.sh.
offer_alt_guard_hook() {
  local settings="$HOME/.claude/settings.json"
  local guard="${sage_dest}bin/sage-alt-guard.sh"
  local marker="sage-alt-guard.sh"
  local tmp reply

  # No guard installed (partial tree, or a source checkout without it) -> nothing to offer.
  if [ ! -f "$guard" ]; then
    return 0
  fi
  # A symlinked settings file belongs to something else; never edit through it.
  if [ -L "$settings" ]; then
    echo "NOTE: $settings is a symlink; skipping the alt-lane guard hook offer."
    return 0
  fi
  if ! command -v jq >/dev/null 2>&1; then
    echo "NOTE: jq is not installed; skipping the alt-lane guard hook offer (the guard needs jq too)."
    return 0
  fi
  if [ -e "$settings" ]; then
    # The same invalid-JSON pre-check as install_compact_hook: a settings file that does not
    # parse is bailed on BEFORE the prompt, not discovered at merge time after a backup.
    if ! jq empty "$settings" >/dev/null 2>&1; then
      echo "NOTE: $settings does not parse as JSON; leaving it untouched — no alt-lane guard hook offered."
      return 0
    fi
    # Already present -> say nothing and change nothing. This is what makes re-running safe.
    if jq -e --arg m "$marker" '[.hooks.PreToolUse // [] | .[] | .hooks // [] | .[] | .command // ""] | any(contains($m))' \
         "$settings" >/dev/null 2>&1; then
      return 0
    fi
  fi
  # Non-interactive install -> never prompt, never write.
  if [ ! -t 0 ]; then
    return 0
  fi

  printf 'Add a PreToolUse hook to %s that blocks an alt-lane subagent dispatch carrying a model parameter? [y/N] ' "$settings"
  read -r reply || reply=""
  case "$reply" in
    y|Y|yes|YES|Yes) : ;;
    *) return 0 ;;
  esac

  # Past this point the user has answered `y`, so every bailout says why. A silent `return 0`
  # here reads as "installed" and is not: the same guard shape install_compact_hook uses, and for
  # the same reason — this function runs under `set -euo pipefail`, so an unguarded failure
  # would abort the whole installer after the already-printed sync results.
  if [ -e "$settings" ]; then
    # A DISTINCT backup category from install_compact_hook's `settings`: both can write in
    # one install, backup() names the saved copy by basename inside its category, and a
    # shared category made the second edit's backup overwrite the first's — leaving the
    # only restore point post-first-edit, which is not the file the user started with.
    backup "$settings" settings-alt-guard || {
      echo "NOTE: could not back up $settings; leaving it untouched, no alt-lane guard hook added."
      return 0
    }
  else
    mkdir -p "$(dirname "$settings")" || {
      echo "NOTE: could not create $(dirname "$settings"); skipping the alt-lane guard hook."
      return 0
    }
    printf '{}\n' > "$settings" || {
      echo "NOTE: could not write $settings; skipping the alt-lane guard hook."
      return 0
    }
  fi

  # Beside the target, not in /tmp: same filesystem as the file it will be written into.
  tmp="$(mktemp "${settings}.XXXXXX")" || {
    echo "NOTE: could not create a temp file beside $settings; leaving it untouched."
    return 0
  }
  if ! jq --arg cmd "$guard" \
       '.hooks.PreToolUse = ((.hooks.PreToolUse // []) + [{"matcher": "Agent", "hooks": [{"type": "command", "command": $cmd}]}])' \
       "$settings" > "$tmp"; then
    echo "NOTE: could not merge the alt-lane guard hook into $settings; left it unchanged."
    rm -f "$tmp"
    return 0
  fi
  if ! jq -e . "$tmp" >/dev/null 2>&1; then
    echo "NOTE: the merged settings did not parse; left $settings unchanged."
    rm -f "$tmp"
    return 0
  fi
  # An in-place write, not `mv`: $settings already exists by this point, and writing through
  # it keeps its original mode and ownership rather than inheriting mktemp's 0600. Guarded,
  # because the redirection truncates $settings BEFORE `cat` runs — an unguarded failure here
  # would leave the user with an empty settings file, silently, and abort the installer under
  # `set -euo pipefail` before anything could say so.
  if ! cat "$tmp" > "$settings"; then
    echo "NOTE: could not write the merged settings into $settings; it may now be truncated."
    echo "      If a backup path for settings.json was printed above, restore from there"
    echo "      ($backups_dir/...); if not, this installer created $settings itself this run"
    echo "      and an empty one can simply be deleted."
    rm -f "$tmp"
    return 0
  fi
  rm -f "$tmp"
  echo "Added the alt-lane guard hook to $settings. Check it with: $guard --selftest"
}

# install_compact_hook: the run ledger's `### Resume state` section carries a run's state across a
# compaction, but only a SessionStart(compact) hook makes the compacted session actually go back
# and read it (sage-claude/references/harness.md, Cautions). Installed rather than offered — a run
# that loses its state is the failure this repo ships the hook for, and a prompt is answered "no"
# by every non-interactive install. Written carefully all the same: this is the one place
# install.sh touches a file it does not own the whole of — the user's ~/.claude/settings.json
# holds arbitrary other config.
install_compact_hook() {
  local settings="$HOME/.claude/settings.json" marker="sage-reanchor"
  local cmd

  # Claude Code runs this command through `sh -c`, and the message is single-quoted, so it must
  # carry no apostrophe of its own: "the run ledger section", never "the run ledger's section".
  cmd="echo '$marker: a compaction landed. Before dispatching anything: re-read the run ledger section ### Resume state (.claude/plans/sage-ledger-*.md; fallback: the session scratchpad), then ~/.claude/skills/sage/SKILL.md ## Compaction and resume, then the step file ### Resume state names.'"

  # A symlink is another owner's property, the same rule the installer already applies to
  # symlinked skills and shared memory — never write through it.
  if [ -L "$settings" ]; then
    echo "NOTE: $settings is a symlink; leaving it alone. See the TIP below for the manual hook."
    return 0
  fi

  if ! command -v jq >/dev/null 2>&1; then
    echo "NOTE: jq is not installed, so the compaction hook cannot be offered automatically."
    echo "      See the TIP below for the manual snippet."
    return 0
  fi

  if [ -e "$settings" ]; then
    if ! jq empty "$settings" >/dev/null 2>&1; then
      echo "NOTE: $settings does not parse as JSON; leaving it untouched."
      echo "      See the TIP below for the manual snippet."
      return 0
    fi
    # An earlier version of this installer wrote a different message under this same marker.
    # That machine is carried forward by rewriting the command where it stands: appending a
    # second entry would leave the stale text firing beside the new one on every compaction.
    if sage_compact_hook_exists "$settings" "$marker"; then
      if sage_compact_hook_says "$settings" "$marker" "$cmd"; then
        return 0
      fi
      backup "$settings" settings || {
        echo "NOTE: could not back up $settings; leaving it untouched."
        return 0
      }
      merge_into_settings "$settings" "$marker" "$cmd" \
        '.hooks.SessionStart |= map(
           if .matcher == "compact"
           then .hooks |= map(if (.command // "") | contains($m) then .command = $cmd else . end)
           else . end)' || return 0
      echo "Rewrote sage's SessionStart(compact) hook in $settings (marker: $marker)."
      return 0
    fi

    # A compact hook carrying no marker is the user's own, or the manual snippet an older TIP
    # told them to paste. Neither is this installer's to rewrite.
    if compact_hook_exists "$settings"; then
      echo "NOTE: a SessionStart(compact) hook that is not sage's already exists in $settings;"
      echo "      leaving it alone. The manual snippet in the TIP below shows sage's own hook."
      return 0
    fi
  fi

  # Every state-changing command below gets its own guard. This function runs after the
  # skill/agent/style syncs, under `set -euo pipefail`, so an unguarded failure here would
  # abort those already-printed results into a truncated-looking install. Nothing past this
  # point may exit non-zero without this function catching it and returning 0 itself.
  if [ -e "$settings" ]; then
    backup "$settings" settings || {
      echo "NOTE: could not back up $settings; leaving it untouched."
      return 0
    }
  else
    mkdir -p "$(dirname "$settings")" || {
      echo "NOTE: could not create $(dirname "$settings"); skipping the compaction hook."
      return 0
    }
    printf '{}\n' > "$settings" || {
      echo "NOTE: could not write $settings; skipping the compaction hook."
      return 0
    }
  fi

  merge_into_settings "$settings" "$marker" "$cmd" \
    '.hooks.SessionStart = ((.hooks.SessionStart // []) + [{"matcher": "compact", "hooks": [{"type": "command", "command": $cmd}]}])' || return 0
  echo "Added a SessionStart(compact) hook to $settings (marker: $marker)."
}

# True when a SessionStart(compact) entry exists at all, whoever wrote it.
compact_hook_exists() { # compact_hook_exists <settings>
  jq -e '.hooks.SessionStart[]? | select(.matcher == "compact")' "$1" >/dev/null 2>&1
}

# True when one of those entries carries <marker> in a command, which is what identifies the hook
# this installer wrote — including the version that wrote a different message.
sage_compact_hook_exists() { # sage_compact_hook_exists <settings> <marker>
  jq -e --arg m "$2" \
    '[.hooks.SessionStart[]? | select(.matcher == "compact") | .hooks[]? | .command // ""]
     | any(contains($m))' "$1" >/dev/null 2>&1
}

sage_compact_hook_says() { # sage_compact_hook_says <settings> <marker> <command>
  jq -e --arg m "$2" --arg cmd "$3" \
    '[.hooks.SessionStart[]? | select(.matcher == "compact") | .hooks[]? | .command // ""
      | select(contains($m))] | all(. == $cmd)' "$1" >/dev/null 2>&1
}

# Applies <jq-filter> to <settings> with $m and $cmd bound, and reports failure instead of raising
# it: the caller runs after the skill/agent/style syncs under `set -euo pipefail`, where an
# unguarded non-zero exit aborts the installer into a truncated-looking install.
merge_into_settings() { # merge_into_settings <settings> <marker> <command> <jq-filter>
  local settings="$1" marker="$2" cmd="$3" filter="$4" tmp
  # Beside the target, not in /tmp: same filesystem as the file it will be written into.
  tmp="$(mktemp "${settings}.XXXXXX")" || {
    echo "NOTE: could not create a temp file beside $settings; leaving it untouched."
    return 1
  }
  if ! jq --arg m "$marker" --arg cmd "$cmd" "$filter" "$settings" > "$tmp"; then
    echo "NOTE: failed to build the merged settings.json; leaving $settings untouched."
    rm -f "$tmp"
    return 1
  fi
  if ! jq empty "$tmp" >/dev/null 2>&1; then
    echo "NOTE: the merged settings.json did not parse; leaving $settings untouched."
    rm -f "$tmp"
    return 1
  fi
  # An in-place write, not `mv`: $settings already exists by this point (created by the caller
  # when missing), and writing through it keeps its original mode and ownership rather than
  # inheriting mktemp's 0600.
  if ! cat "$tmp" > "$settings"; then
    echo "NOTE: could not write the merged settings.json into $settings; leaving it untouched."
    rm -f "$tmp"
    return 1
  fi
  rm -f "$tmp"
}

if [ -d "$sage_src" ]; then
  install_compact_hook
  offer_alt_guard_hook
fi

echo
if [ -d "$sage_src" ]; then
  echo "Installed sage skill       -> $sage_dest"
  echo "  shared memory synced from -> $shared_src"
fi
echo "Installed subagent agents  -> $agents_dest"
if [ "${alt_installed:-0}" -gt 0 ]; then
  echo "Installed alt agents       -> $alt_installed of the three, at $agents_dest"
  echo "  Start a new Claude Code session before an alt agent can be dispatched."
  echo "  The agent registry resolves once at session start. One added mid-session is not yet"
  echo "  visible."
fi
if [ -d "$eco_src" ]; then
  echo "Installed ecosystem skills -> $eco_dest (from claude-skills/)"
fi
echo "Installed output styles    -> $styles_dest"
if [ -d "$backup_root" ]; then
  echo "Backups from this run      -> $backup_root"
fi
echo
cat <<'TIP'
For long orchestration runs:

  Sage reads its own occupancy and checkpoints its ledger before the expected compaction.
  Triggering /compact is yours, not the model's. To compact earlier, set
  CLAUDE_AUTOCOMPACT_PCT_OVERRIDE (1-100) or run /autocompact <size>; if you set one, tell the run
  with SAGE_COMPACT_AT=<size> so its sensor expects the right point. Verify those two knob names
  against the current Claude Code docs before relying on them; this installer cannot check them.

  If a NOTE above says the compaction hook was not installed (no jq, or a symlinked settings
  file), add it to ~/.claude/settings.json by hand:

    "hooks": {
      "SessionStart": [
        { "matcher": "compact",
          "hooks": [ { "type": "command",
                       "command": "echo 'sage-reanchor: a compaction landed. Before dispatching anything: re-read the run ledger section ### Resume state (.claude/plans/sage-ledger-*.md; fallback: the session scratchpad), then ~/.claude/skills/sage/SKILL.md ## Compaction and resume, then the step file ### Resume state names.'" } ] }
      ]
    }
TIP

if [ "$alt_lane_relevant" -eq 1 ]; then
cat <<'ALTTIP'

Optional, to place orchestration units on an external model:

  Write ~/.claude/subagents-alt-models.conf (SUBAGENTS_ALT_CONF overrides this path). One role per
  line, as <name>=<model>: explorer-alt, verifier-alt, web-researcher-alt. Blank lines and '#'
  comments are ignored. No model name is guessed for you. Put in the model your own gateway serves.
  Re-run this installer after editing the file. Removing a line removes that agent on the next run.
  Then start a new session. A file added mid-session is not yet dispatchable.
ALTTIP
fi
