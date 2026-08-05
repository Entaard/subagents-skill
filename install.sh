#!/usr/bin/env bash
# Installs the subagents skill for Claude Code into ~/.claude/.
# Run this after every `git pull` to pick up changes.
set -euo pipefail

repo_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
src="$repo_dir/subagents-claude/"
dest="$HOME/.claude/skills/subagents/"

mkdir -p "$dest"

# calibration.md is excluded from the sync on purpose: it accumulates real run costs on this
# machine, and --delete would wipe them on every update. It is user data living in a synced tree.
rsync -av --delete --exclude='calibration.md' "$src" "$dest"

# Seed the calibration log on first install only — never overwrite accumulated actuals.
if [ ! -f "${dest}calibration.md" ]; then
  cp "${src}calibration.md" "${dest}calibration.md"
  echo "Seeded calibration log     -> ${dest}calibration.md"
fi

# Agent files have to live in ~/.claude/agents/; Claude Code does not discover them inside a skill
# directory. No --delete here — other agents in that directory are not this script's to remove.
#
# NOTE: ~/.claude/agents/ is GLOBAL. Claude Code watches it and can auto-delegate to these agents in
# any project, based on their `description` field. Both descriptions are written to say they are
# dispatched by name from an approved orchestration plan, and to send ordinary lookups to the
# built-in Explore agent instead, so they should not capture routine work. Delete them from
# ~/.claude/agents/ if you would rather they not exist outside this skill.
agents_src="$repo_dir/claude-agents/"
agents_dest="$HOME/.claude/agents/"

mkdir -p "$agents_dest"

# 'explorer' and 'verifier' are generic enough to collide with an agent you already wrote.
# Back up anything we are about to replace rather than overwriting it silently.
for f in "$agents_src"*.md; do
  name="$(basename "$f")"
  existing="$agents_dest$name"
  if [ -f "$existing" ] && ! cmp -s "$f" "$existing"; then
    cp "$existing" "$existing.bak"
    echo "NOTE: replaced a different $name; previous version saved to $existing.bak"
  fi
done

rsync -av "$agents_src" "$agents_dest"

echo
echo "Installed subagents skill  -> $dest"
echo "Installed subagent agents  -> $agents_dest"
