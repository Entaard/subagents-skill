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
else
  # The rows in an existing calibration.md are user data, so we leave the file alone. But the text
  # ABOVE the table is skill-authored guidance, and that does change between versions. Without this
  # notice, a guidance change would never reach anyone who already installed. Reconciling is the
  # user's call: only they can tell a seed row from one of their own.
  header_src="$(sed -n '1,/^| date |/p' "${src}calibration.md")"
  header_dest="$(sed -n '1,/^| date |/p' "${dest}calibration.md")"
  if [ "$header_src" != "$header_dest" ]; then
    echo
    echo "NOTE: calibration.md guidance changed in this version. Your copy was left untouched,"
    echo "      because it holds your accumulated rows. To see what moved above the table:"
    echo "        diff ${src}calibration.md ${dest}calibration.md"
  fi
fi

# Agent files have to live in ~/.claude/agents/; Claude Code does not discover them inside a skill
# directory. No --delete here — other agents in that directory are not this script's to remove.
#
# NOTE: ~/.claude/agents/ is GLOBAL. Claude Code watches it and can auto-delegate to these agents in
# any project, based on their `description` field. All three descriptions are written to say they are
# dispatched by name from an approved orchestration plan, and to send ordinary lookups to the
# built-in Explore agent instead, so they should not capture routine work. Delete them from
# ~/.claude/agents/ if you would rather they not exist outside this skill.
agents_src="$repo_dir/claude-agents/"
agents_dest="$HOME/.claude/agents/"

mkdir -p "$agents_dest"

# 'explorer', 'verifier' and 'web-researcher' are generic enough to collide with an agent you
# already wrote. Back up anything we are about to replace rather than overwriting it silently.
for f in "$agents_src"*.md; do
  name="$(basename "$f")"
  existing="$agents_dest$name"
  if [ -f "$existing" ] && ! cmp -s "$f" "$existing"; then
    cp "$existing" "$existing.bak"
    echo "NOTE: replaced a different $name; previous version saved to $existing.bak"
  fi
done

rsync -av "$agents_src" "$agents_dest"

# Ecosystem skills (clean-code, diff-review) live beside the subagents skill in ~/.claude/skills/,
# one directory per skill. Their names are chosen to coexist with the separately installed
# mattpocock skills (tdd, code-review); this script never touches those. Same conflict-safe copy as
# agents above: back up a same-named skill with different content, never delete skills this repo
# doesn't own, and refuse to replace a symlink — a symlink is another installer's property.
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
    if [ -d "$existing" ] && ! diff -rq "$d" "$existing" >/dev/null 2>&1; then
      rm -rf "$existing.bak"
      cp -R "$existing" "$existing.bak"
      echo "NOTE: replaced a different $name skill; previous version saved to $existing.bak"
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

for f in "$styles_src"*.md; do
  name="$(basename "$f")"
  existing="$styles_dest$name"
  if [ -f "$existing" ] && ! cmp -s "$f" "$existing"; then
    cp "$existing" "$existing.bak"
    echo "NOTE: replaced a different $name; previous version saved to $existing.bak"
  fi
done

rsync -av "$styles_src" "$styles_dest"

echo
echo "Installed subagents skill  -> $dest"
echo "Installed subagent agents  -> $agents_dest"
if [ -d "$eco_src" ]; then
  echo "Installed ecosystem skills -> $eco_dest (from claude-skills/)"
fi
echo "Installed output styles    -> $styles_dest"
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
