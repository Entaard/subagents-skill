#!/usr/bin/env bash
# Installs the subagents and sage skills for Claude Code into ~/.claude/.
# Run this after every `git pull` to pick up changes.
set -euo pipefail

repo_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

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

# install_skill <src/> <dest/> <seed-src-rel> <seed-dest-rel> <drift-fn> [<user-data-path> ...]
#
# One primary skill directory, synced with --delete so a file dropped from the repo really goes
# away, minus the <user-data-path> arguments. Those are the paths this machine writes into a tree
# the installer otherwise owns; --delete would wipe them on every update. Each is an rsync pattern
# whose leading / anchors it to the top of the synced dir, so a same-named file deeper in the tree
# is still synced normally, and excluding a path is also what protects it from --delete. Every one
# of those patterns is a fixed literal written at the call sites below, never a filename read off
# this machine, which is the only reason --delete is safe here: a pattern is a glob, and the eco
# loop further down had to stop generating patterns from runtime filenames for exactly that
# reason — see the comment there. Do not pass a discovered name to this function. Everything
# else under the dir is managed: a user file placed there is removed on re-install (rsync announces
# each deletion).
#
# <seed-src-rel> is copied to <seed-dest-rel> on first install only — accumulated user data is
# never overwritten. On every later install <drift-fn> is called with the two paths and says
# whatever that skill's notion of "the seed moved on without you" is. The two callers differ there
# and nowhere else, which is the only reason it is a parameter.
install_skill() {
  local src="$1" dest="$2" seed_src="$3" seed_dest="$4" drift_fn="$5"
  shift 5
  local excludes=() p
  for p in ${1+"$@"}; do
    excludes+=(--exclude="$p")
  done

  mkdir -p "$dest"
  # The +alternate form matters here and below: stock macOS ships bash 3.2, where "${arr[@]}" on an
  # empty array is an unbound variable under set -u and would abort every clean install.
  rsync -av --delete ${excludes[@]+"${excludes[@]}"} "$src" "$dest"

  if [ ! -f "$src$seed_src" ]; then
    echo "NOTE: $src$seed_src is missing; $dest$seed_dest was not seeded."
    return 0
  fi
  if [ ! -f "$dest$seed_dest" ]; then
    mkdir -p "$(dirname "$dest$seed_dest")"
    cp "$src$seed_src" "$dest$seed_dest"
    printf 'Seeded %-20s-> %s\n' "$(basename "$seed_dest")" "$dest$seed_dest"
  else
    "$drift_fn" "$src$seed_src" "$dest$seed_dest"
  fi
}

# The rows in an existing calibration.md are user data, so we leave the file alone. But the text
# ABOVE the first "## " section heading is the skill-authored contract, and that does change
# between versions. Without this notice, a guidance change would never reach anyone who already
# installed. The comparison runs from the top of the file through the first "## " heading line
# (sed's range is end-inclusive); everything below that line holds user data (bands, rules, rows)
# and stays out of it. Reconciling is the user's call: only they can tell a seed row from one of
# their own.
drift_calibration_header() { # drift_calibration_header <seed> <installed>
  local header_src header_dest
  header_src="$(sed -n '1,/^## /p' "$1")"
  header_dest="$(sed -n '1,/^## /p' "$2")"
  if [ "$header_src" != "$header_dest" ]; then
    echo
    echo "NOTE: calibration.md guidance changed in this version. Your copy was left untouched,"
    echo "      because it holds your accumulated rows. This note repeats until the text above the"
    echo "      first '## ' heading in your copy matches the new seed's. To see what moved:"
    echo "        diff $1 $2"
  fi
}

# Sage's local memory does NOT get the byte comparison above, and reusing it here would be a bug.
# Sage's own consolidation pass is licensed to rewrite that file in place, so any byte comparison
# against the seed latches on permanently the first time consolidation runs, and then blames the
# seed for a change sage made itself. What it compares instead is the header sentinel
#
#     <!-- sage-local-memory v1 -->
#
# which sage-claude/references/memory.md, "Structural invariants", declares as line 1 of local.md
# and requires every consolidation to preserve verbatim — so it survives the one rewrite a byte
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
    echo "NOTE: sage's memory format is now \"$want\"; your memory/local.md says"
    echo "      \"${have:-nothing}\". Your copy was left untouched, because it holds this machine's"
    echo "      numbers. This note repeats until the two sentinels match. To see what moved:"
    echo "        diff $1 $2"
  fi
}

# The subagents skill. calibration.md accumulates real run costs on this machine, and
# calibration-archive.md (created by /agents-self-reflect) holds its retired rows.
subagents_src="$repo_dir/subagents-claude/"
subagents_dest="$HOME/.claude/skills/subagents/"

install_skill "$subagents_src" "$subagents_dest" \
  calibration.md calibration.md drift_calibration_header \
  '/calibration.md' '/calibration-archive.md'

# The sage skill. Its whole memory/ directory is user data: local.md and local-archive.md are
# written by sage itself, and shared.md is the symlink created below. Nothing in the installed
# memory/ is a copy of a repo file, so --delete must never reach into it — which also means
# local-seed.md is never installed, only read from the repo by install_skill's seed step.
sage_src="$repo_dir/sage-claude/"
sage_dest="$HOME/.claude/skills/sage/"
shared_src="$repo_dir/sage-claude/memory/shared.md"
shared_link="${sage_dest}memory/shared.md"

if [ -d "$sage_src" ]; then
  install_skill "$sage_src" "$sage_dest" \
    memory/local-seed.md memory/local.md drift_memory_sentinel \
    '/memory/'

  # Shared memory is ONE physical file, living in the repo and reached through a symlink. Sage
  # writes ~/.claude/skills/sage/memory/shared.md, the bytes land in the working tree where git
  # sees them, and there is never a second copy to fork — which is the failure the install-vs-repo
  # calibration split already demonstrated. The link is absolute and points into the clone this
  # script was run from, so a machine with two clones tracks whichever one installed last.
  mkdir -p "$(dirname "$shared_link")"
  if [ -L "$shared_link" ] && [ "$(readlink "$shared_link")" = "$shared_src" ]; then
    : # already points at this clone; leave it alone
  elif [ -d "$shared_link" ] && [ ! -L "$shared_link" ]; then
    # A directory where the link belongs. Clearing it would mean rm -rf on whatever is inside, so
    # take a copy and leave it standing: sage's documented behavior with no shared memory is to run
    # on local memory alone and print one line saying so. Leaving it standing is also why the copy
    # is backup_once and not backup — the condition survives the install and would otherwise be
    # re-copied in full on every run.
    backup_once "$shared_link" sage-memory
    echo "NOTE: $shared_link is a directory; leaving it and skipping the shared-memory link."
  else
    # Either nothing is there, or something that is not this clone's link — a link to another
    # clone, or a real file from an installer that predates the symlink. Whatever is there is
    # memory someone accumulated, so it is copied out before it is replaced, never clobbered.
    # -L as well as -e, because a dangling symlink is invisible to -e. rm on a symlink removes the
    # link and never the file it points at.
    if [ -e "$shared_link" ] || [ -L "$shared_link" ]; then
      backup "$shared_link" sage-memory
      rm -f "$shared_link"
    fi
    ln -s "$shared_src" "$shared_link"
  fi
  if [ ! -e "$shared_src" ]; then
    echo "NOTE: $shared_src does not exist; sage will run on local memory alone until it does."
  fi

  # rsync -a carries the source mode across, so this only matters when the repo's copy lost its
  # executable bit (a zip download, a checkout with no exec support). The watchdog is spawned as a
  # command, so a probe that is not executable disables the watchdog on every run.
  if [ -f "${sage_dest}bin/sage-watch.sh" ]; then
    chmod +x "${sage_dest}bin/sage-watch.sh"
  fi
fi

# Agent files have to live in ~/.claude/agents/; Claude Code does not discover them inside a skill
# directory. No --delete here — other agents in that directory are not this script's to remove.
#
# NOTE: ~/.claude/agents/ is GLOBAL. Claude Code watches it and can auto-delegate to these agents in
# any project, based on their `description` field. All the descriptions are written to say they are
# dispatched by name from an orchestration plan, and to send ordinary lookups to the built-in
# Explore agent instead, so they should not capture routine work. Both /subagents and /sage dispatch
# them. Delete them from ~/.claude/agents/ if you would rather they not exist outside those skills.
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

# Ecosystem skills (every directory under claude-skills/) live beside the subagents skill in
# ~/.claude/skills/, one directory per skill. Their names are chosen to coexist with the
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

echo
echo "Installed subagents skill  -> $subagents_dest"
if [ -d "$sage_src" ]; then
  echo "Installed sage skill       -> $sage_dest"
  echo "  shared memory symlink    -> $shared_src"
fi
echo "Installed subagent agents  -> $agents_dest"
if [ -d "$eco_src" ]; then
  echo "Installed ecosystem skills -> $eco_dest (from claude-skills/)"
fi
echo "Installed output styles    -> $styles_dest"
if [ -d "$backup_root" ]; then
  echo "Backups from this run      -> $backup_root"
fi
echo
cat <<'TIP'
Optional, for long orchestration runs:

  Triggering /compact is yours, not the model's. To compact earlier, set
  CLAUDE_AUTOCOMPACT_PCT_OVERRIDE (1-100) or run /autocompact <size>. Sage reads its own context
  usage and hands over at 600k rather than waiting for a compaction; /subagents does not.

  To re-anchor a run after a compaction, add a hook in ~/.claude/settings.json that echoes the
  ledger paths back into the session:

    "hooks": {
      "SessionStart": [
        { "matcher": "compact",
          "hooks": [ { "type": "command",
                       "command": "echo 'Ledger: <scratch>/subagents-ledger.md or .claude/plans/sage-ledger-*.md'" } ] }
      ]
    }
TIP
