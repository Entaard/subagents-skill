#!/usr/bin/env bash
# Installs the subagents skill for Claude Code into ~/.claude/.
# Run this after every `git pull` to pick up changes.
set -euo pipefail

repo_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
src="$repo_dir/subagents-claude/"
dest="$HOME/.claude/skills/subagents/"

mkdir -p "$dest"

# Two files are excluded from the sync on purpose: calibration.md accumulates real run costs on
# this machine, and calibration-archive.md (created by /agents-self-reflect) holds its retired
# rows. --delete would wipe both on every update. They are user data living in a synced tree.
# Everything else under this dir is managed: a user file placed here is removed on re-install
# (rsync announces each deletion). The leading / anchors each pattern to the top of the synced
# dir, so a same-named file deeper in the tree is still synced normally.
rsync -av --delete --exclude='/calibration.md' --exclude='/calibration-archive.md' "$src" "$dest"

# Seed the calibration log on first install only — never overwrite accumulated actuals.
if [ ! -f "${dest}calibration.md" ]; then
  cp "${src}calibration.md" "${dest}calibration.md"
  echo "Seeded calibration log     -> ${dest}calibration.md"
else
  # The rows in an existing calibration.md are user data, so we leave the file alone. But the text
  # ABOVE the first "## " section heading is the skill-authored contract, and that does change
  # between versions. Without this notice, a guidance change would never reach anyone who already
  # installed. The comparison runs from the top of the file through the first "## " heading line
  # (sed's range is end-inclusive); everything below that line holds user data (bands, rules,
  # rows) and stays out of it. Reconciling is the user's call: only they can tell a seed row from
  # one of their own.
  header_src="$(sed -n '1,/^## /p' "${src}calibration.md")"
  header_dest="$(sed -n '1,/^## /p' "${dest}calibration.md")"
  if [ "$header_src" != "$header_dest" ]; then
    echo
    echo "NOTE: calibration.md guidance changed in this version. Your copy was left untouched,"
    echo "      because it holds your accumulated rows. This note repeats until the text above the"
    echo "      first '## ' heading in your copy matches the new seed's. To see what moved:"
    echo "        diff ${src}calibration.md ${dest}calibration.md"
  fi
fi

# Backups from every section below land in one timestamped directory per run, OUTSIDE the
# directories Claude Code auto-discovers (skills/, agents/, output-styles/). A backup inside a
# discovered directory becomes a phantom skill or agent (a discoverable clean-code.bak skill
# appeared in practice), and a fixed backup name is clobbered by the next differing install.
# The directory is created lazily, so an install that replaces nothing leaves no empty dir behind.
backup_root="$HOME/.claude/backups/subagents-skill/$(date +%Y%m%d-%H%M%S)-$$"

backup() { # backup <path> <category> — preserve a file or directory before it is replaced
  mkdir -p "$backup_root/$2"
  cp -R "$1" "$backup_root/$2/"
  echo "NOTE: replacing a different $(basename "$1"); previous version saved to $backup_root/$2/$(basename "$1")"
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

# Agent files have to live in ~/.claude/agents/; Claude Code does not discover them inside a skill
# directory. No --delete here — other agents in that directory are not this script's to remove.
#
# NOTE: ~/.claude/agents/ is GLOBAL. Claude Code watches it and can auto-delegate to these agents in
# any project, based on their `description` field. All the descriptions are written to say they are
# dispatched by name from an approved orchestration plan, and to send ordinary lookups to the
# built-in Explore agent instead, so they should not capture routine work. Delete them from
# ~/.claude/agents/ if you would rather they not exist outside this skill.
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

# The +alternate form matters: stock macOS ships bash 3.2, where "${arr[@]}" on an empty array is an
# unbound variable under set -u and would abort every clean install.
rsync -av ${skip_agents[@]+"${skip_agents[@]}"} "$agents_src" "$agents_dest"

# Ecosystem skills (every directory under claude-skills/) live beside the subagents skill in
# ~/.claude/skills/, one directory per skill. Their names are chosen to coexist with the
# separately installed mattpocock skills (tdd, code-review); this script never touches those.
# Same conflict-safe copy as agents above: back up a same-named skill with different content,
# never delete skills this repo doesn't own, refuse to replace a symlink — a symlink is another
# installer's property — and clear a stray non-directory rather than aborting the run on it.
eco_src="$repo_dir/claude-skills/"
eco_dest="$HOME/.claude/skills/"

if [ -d "$eco_src" ]; then
  for d in "$eco_src"*/; do
    [ -d "$d" ] || continue
    name="$(basename "$d")"
    existing="$eco_dest$name"
    if [ -L "$existing" ]; then
      echo "NOTE: $existing is a symlink owned by another installer; skipping $name."
      continue
    fi
    migrate_legacy_bak "$existing.bak" skills
    if [ -d "$existing" ] && ! diff -rq "$d" "$existing" >/dev/null 2>&1; then
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
    rsync -av --delete "$d" "$existing/"
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
echo "Installed subagents skill  -> $dest"
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

  The model cannot see context usage or trigger /compact — both are yours. To compact earlier,
  set CLAUDE_AUTOCOMPACT_PCT_OVERRIDE (1-100) or run /autocompact <size>.

  To re-anchor a run after a compaction, add a hook in ~/.claude/settings.json that echoes the
  ledger path back into the session:

    "hooks": {
      "SessionStart": [
        { "matcher": "compact",
          "hooks": [ { "type": "command",
                       "command": "echo 'Orchestration ledger: check the session scratchpad for subagents-ledger.md'" } ] }
      ]
    }
TIP
