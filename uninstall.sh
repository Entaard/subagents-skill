#!/usr/bin/env bash
# Reverses install.sh: removes the skills, agent files, output styles and settings hooks it
# placed under ~/.claude/. Every path removed is copied under the backup root first, so an
# uninstall run by mistake costs a restore rather than the data.
set -euo pipefail

repo_dir=""
claude_dir="$HOME/.claude"
skills_dest="$claude_dir/skills"
agents_dest="$claude_dir/agents"
styles_dest="$claude_dir/output-styles"
settings="$claude_dir/settings.json"
backups_dir="$claude_dir/backups/subagents-skill"
backup_root=""
manifests_dir="$backups_dir/.manifests"
alt_conf="${SUBAGENTS_ALT_CONF:-$claude_dir/subagents-alt-models.conf}"

# install.sh stamps this exact line into every alt agent it renders. It is the only thing that
# tells its own output from an agent of the same name that the user wrote, so removal is gated
# on it — the same narrow rule install.sh applies when a config line goes away.
alt_marker="<!-- subagents-skill: generated alt agent — regenerate with install.sh, do not hand-edit -->"
guard_hook_command="$skills_dest/sage/bin/sage-alt-guard.sh"
compact_hook_marker="sage-reanchor"

sage_only=0
dry_run=0
assume_yes=0
removed_any=0
target_paths=()
target_categories=()
left_standing=()

main() {
  parse_args "$@"
  require_core_tools
  resolve_paths
  # bash runs the EXIT trap with $? still 0 when a signal ends the script, which would send
  # report_interrupted_state down its "finished cleanly" branch in exactly the case it exists for.
  # Exiting with the conventional 128+signal status is what gives that trap a failure to see.
  trap 'exit 130' INT
  trap 'exit 143' TERM
  trap report_interrupted_state EXIT
  collect_targets
  if [ "${#target_paths[@]}" -eq 0 ] && ! settings_has_sage_hooks; then
    echo "Nothing to remove: no part of this repo's install was found under $claude_dir."
    print_left_standing
    exit 0
  fi
  print_plan
  confirm
  apply
  print_summary
}

usage() {
  cat <<'USAGE'
uninstall.sh — remove what install.sh placed under ~/.claude/.

  --sage-only   Remove the sage skill, its sage-promote companion, all five shipped agents,
                generated alt agents and its two settings hooks. Leaves the other ecosystem
                skills and output styles.
  --dry-run     Print what would be removed and change nothing.
  --yes, -y     Skip the confirmation prompt. Required when stdin is not a terminal.
  --help, -h    Print this.

Everything removed is copied under ~/.claude/backups/subagents-skill/ first. That directory and
the alt-model config are never removed; the closing summary names everything left behind.
USAGE
}

parse_args() {
  local arg
  for arg in ${1+"$@"}; do
    case "$arg" in
      --sage-only) sage_only=1 ;;
      --dry-run) dry_run=1 ;;
      --yes|-y) assume_yes=1 ;;
      --help|-h) usage; exit 0 ;;
      *) echo "ERROR: unknown option '$arg'." >&2; usage >&2; exit 1 ;;
    esac
  done
}

# install.sh aborts up front on a missing core tool rather than half-way through a copy. The
# same reasoning is sharper here: an abort part-way through a removal pass leaves the install
# in a state neither script has a name for.
require_core_tools() {
  local tool missing=()
  for tool in cp rm mkdir basename cmp grep date readlink dirname find; do
    command -v "$tool" >/dev/null 2>&1 || missing+=("$tool")
  done
  if [ "${#missing[@]}" -gt 0 ]; then
    echo "ERROR: missing required tool(s) on PATH: ${missing[*]}" >&2
    echo "  Nothing has been removed. Check 'echo \$PATH' for an entry shadowing /usr/bin." >&2
    exit 1
  fi
}

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

# Both values shell out, so they are set here and not beside the other globals: no external tool is
# known to exist until require_core_tools has run. repo_dir resolves the script's own path first —
# reached through a symlink it would otherwise name the link's directory, where none of the source
# globs match, and the run would report a clean uninstall having removed almost nothing. The walk
# runs in a subshell, so `|| exit` is what ends the run on a failed one; without it repo_dir falls
# back to the working directory. `cd -P` resolves symlinked parent directories, which the walk does
# not: it only ever rewrites the last component.
resolve_paths() {
  local script_path
  script_path="$(resolve_symlinks "${BASH_SOURCE[0]}")" || exit 1
  repo_dir="$(cd -P "$(dirname "$script_path")" && pwd -P)"
  backup_root="$backups_dir/$(date +%Y%m%d-%H%M%S)-$$-uninstall"
}

# A run that dies part-way has still removed things, and the shell's own error message says
# nothing about that. install.sh's preflight comment names this failure: a half-done install
# that looks like a crash.
report_interrupted_state() {
  local status=$?
  if [ "$status" -eq 0 ] || [ "$dry_run" -eq 1 ]; then
    return 0
  fi
  echo >&2
  if [ "$removed_any" -eq 0 ]; then
    echo "This run stopped before removing anything. Nothing under $claude_dir was changed." >&2
  else
    echo "This run stopped part-way: some of the install is removed and the rest is not." >&2
    echo "Everything it did remove is under $backup_root." >&2
  fi
  echo "Fix what the error above names and run it again; it skips whatever is already gone." >&2
}

collect_targets() {
  collect_primary_skill sage
  if [ "$sage_only" -eq 1 ]; then
    collect_eco_skill sage-promote
  else
    collect_eco_skills
    collect_output_styles "$repo_dir/output-styles" "$styles_dest"
  fi
  collect_sage_agents "$repo_dir/claude-agents" "$repo_dir/claude-agents-alt" "$agents_dest"
}

collect_output_styles() { # collect_output_styles <source-dir> <destination-dir>
  local source_dir="$1" destination_dir="$2" src
  for src in "$source_dir"/*.md; do
    [ -f "$src" ] || continue
    collect_shipped_file "$src" "$destination_dir/$(basename "$src")" output-styles
  done
}

collect_sage_agents() { # collect_sage_agents <source-dir> <alt-source-dir> <destination-dir>
  local source_dir="$1" alt_source_dir="$2" destination_dir="$3" src
  for src in "$source_dir"/*.md; do
    [ -f "$src" ] || continue
    collect_shipped_file "$src" "$destination_dir/$(basename "$src")" agents
  done
  collect_generated_alt_agents "$alt_source_dir" "$destination_dir"
}

collect_primary_skill() { # collect_primary_skill <name>
  local dir="$skills_dest/$1"
  if [ -L "$dir" ]; then
    # install.sh guards the eco skills against a symlink and this path against nothing: it
    # mkdir -p's and rsyncs straight through the link. Removing the link would leave the whole
    # skill installed at a path this script has no claim on.
    echo "NOTE: $dir is a symlink and install.sh wrote through it, so the skill is at its target."
    left_standing+=("$dir -> $(readlink "$dir") — install.sh wrote through this symlink; remove the target by hand")
    return 0
  fi
  if [ -e "$dir" ] && [ ! -d "$dir" ]; then
    echo "NOTE: $dir is not a directory; leaving it."
    left_standing+=("$dir — not a directory")
    return 0
  fi
  add_target "$dir" skills
}

collect_eco_skills() {
  local manifest name
  for manifest in "$repo_dir"/claude-skills/*/; do
    [ -d "$manifest" ] || continue
    collect_eco_skill "$(basename "$manifest")"
  done
  if ! manifests_are_readable; then
    echo "NOTE: no install manifests can be read at $manifests_dir, so this run cannot tell a"
    echo "      skill install.sh put here from one of your own that shares the name, and it"
    echo "      cannot find one an older version installed under a name since dropped."
    return 0
  fi
  # install.sh never removes an eco skill it has stopped shipping, so a checkout that renamed one
  # leaves an orphan no source glob can find. Only the manifest records that it was shipped here.
  for manifest in "$manifests_dir"/*; do
    [ -f "$manifest" ] || continue
    name="$(basename "$manifest")"
    if [ -d "$repo_dir/claude-skills/$name" ]; then
      continue
    fi
    # A manifest outlives the skill it names, so on its own it proves only that the name was once
    # ours — not that whatever stands there now is. Another installer that claimed the name in the
    # meantime would be removed on the strength of a stale record, so make the record earn it.
    case "$(manifest_verdict "$manifest" "$skills_dest/$name")" in
      unreadable)
        echo "NOTE: $manifest cannot be read, so nothing here can say whether $skills_dest/$name is"
        echo "      ours; leaving it."
        left_standing+=("$skills_dest/$name — its install record could not be read, so ownership is unproven")
        continue
        ;;
      missing)
        echo "NOTE: $skills_dest/$name does not hold what $manifest says this repo shipped, so it"
        echo "      belongs to something else now; leaving it."
        left_standing+=("$skills_dest/$name — holds something other than what this repo shipped under that name")
        continue
        ;;
      extra)
        echo "NOTE: $skills_dest/$name matches what $manifest says this repo shipped, plus files that"
        echo "      record does not list; leaving it rather than removing those too."
        left_standing+=("$skills_dest/$name — matches this repo's install record plus files it does not list")
        continue
        ;;
    esac
    echo "NOTE: $name is no longer shipped, and $manifests_dir/$name says this repo installed it."
    echo "      That record is the only evidence it is ours; check it before answering."
    collect_eco_skill "$name"
  done
}

manifests_are_readable() {
  [ -d "$manifests_dir" ] && [ -r "$manifests_dir" ] && [ -x "$manifests_dir" ]
}

# Says what <dir> is, measured against the manifest that records this repo having shipped that name.
# Four answers, because the caller has a different thing to say for each and one boolean forced it to
# say the same wrong thing for three of them.
#
# `extra` is a separate answer rather than part of `missing` because extra files are NOT evidence
# against ownership. install.sh writes the manifest as a walk of the repo SOURCE it rsyncs from
# (install.sh:949), never of the installed tree, and it deliberately keeps destination-only paths as
# runtime data (dest_only_paths, install.sh:798) — so a directory this repo really did install can
# hold files no manifest lists. What extra files do mean is that removing the directory would take
# something the record cannot vouch for, which is worth telling the user and is not worth asserting
# the directory is somebody else's.
#
# `exact` is the only answer that earns a removal, and it earns a hedged one: four of the five
# manifests on a real install are the single line `SKILL.md`, which any single-file skill matches.
# An absent directory answers `exact` — nothing stands there to mistake for ours, and the manifest is
# then the only leftover.
manifest_verdict() { # manifest_verdict <manifest> <dir> -> exact | unreadable | missing | extra
  local manifest="$1" dir="$2" rel
  if [ ! -r "$manifest" ]; then
    printf 'unreadable\n'
    return 0
  fi
  if [ ! -d "$dir" ]; then
    printf 'exact\n'
    return 0
  fi
  # `|| [ -n "$rel" ]` keeps the last entry of a manifest that ends without a newline; plain `read`
  # returns false on it and the loop would drop the one path most likely to be missing.
  while IFS= read -r rel || [ -n "$rel" ]; do
    [ -n "$rel" ] || continue
    if [ ! -e "$dir/$rel" ] && [ ! -L "$dir/$rel" ]; then
      printf 'missing\n'
      return 0
    fi
  done < "$manifest"
  while IFS= read -r rel; do
    # `-e` and `</dev/null`: a manifest line such as `-v` would otherwise be read as a grep option,
    # leaving no pattern, so grep would consume this loop's own stdin and drain the walk unchecked.
    if ! grep -qxF -e "${rel#./}" -- "$manifest" </dev/null; then
      printf 'extra\n'
      return 0
    fi
  done < <(cd "$dir" && find . -mindepth 1)
  printf 'exact\n'
}

collect_eco_skill() { # collect_eco_skill <name>
  local name="$1" dir="$skills_dest/$1"
  if [ -L "$dir" ]; then
    # install.sh skips a symlinked eco skill outright, so nothing of this repo's is inside it.
    echo "NOTE: $dir is a symlink owned by another installer; leaving it."
    left_standing+=("$dir — a symlink this repo never wrote through")
    return 0
  fi
  if [ -e "$dir" ] && [ ! -d "$dir" ]; then
    echo "NOTE: $dir is not a directory; leaving it."
    left_standing+=("$dir — not a directory")
    return 0
  fi
  # These names are generic enough to collide with a skill of the user's own, and install.sh
  # says so where it installs them. Its manifest is the only evidence that this one is ours.
  if [ -d "$dir" ] && manifests_are_readable && [ ! -f "$manifests_dir/$name" ]; then
    echo "NOTE: $dir carries no install manifest, so it may be a skill of your own sharing the"
    echo "      name. It is in the list below; check it before answering."
  fi
  add_target "$manifests_dir/$name" manifests
  add_target "$dir" skills
}

collect_generated_alt_agents() { # collect_generated_alt_agents <template-dir> <destination-dir>
  local template_dir="$1" destination_dir="$2" tpl dest
  for tpl in "$template_dir"/*.md.in; do
    [ -f "$tpl" ] || continue
    dest="$destination_dir/$(basename "$tpl" .md.in).md"
    if [ -L "$dest" ]; then
      echo "NOTE: $dest is a symlink you made after installing; leaving it."
      left_standing+=("$dest — a symlink this repo did not create")
      continue
    fi
    if [ -f "$dest" ] && grep -qxF "$alt_marker" "$dest"; then
      add_target "$dest" agents
    elif [ -e "$dest" ]; then
      echo "NOTE: $dest carries no generated-by marker, so install.sh did not write it; leaving it."
      left_standing+=("$dest — an alt agent of your own at a name install.sh also renders")
    fi
  done
}

collect_shipped_file() { # collect_shipped_file <repo-copy> <installed-path> <category>
  local src="$1" dest="$2" category="$3"
  if [ -L "$dest" ]; then
    # rsync replaces a symlink at this path with a regular file, so a link here was made after
    # the install and points at a file of the user's that a backup would not capture.
    echo "NOTE: $dest is a symlink you made after installing; leaving it."
    left_standing+=("$dest — a symlink this repo did not create")
    return 0
  fi
  if [ -e "$dest" ] && [ ! -f "$dest" ]; then
    echo "NOTE: $dest is not a regular file; leaving it."
    left_standing+=("$dest — not a regular file")
    return 0
  fi
  if [ -f "$dest" ] && ! cmp -s "$src" "$dest"; then
    echo "NOTE: $dest differs from this repo's copy; the backup will be the only copy left."
  fi
  add_target "$dest" "$category"
}

add_target() { # add_target <path> <category>
  if [ ! -e "$1" ] && [ ! -L "$1" ]; then
    return 0
  fi
  target_paths+=("$1")
  target_categories+=("$2")
}

settings_has_sage_hooks() {
  [ -f "$settings" ] || return 1
  [ ! -L "$settings" ] || return 1
  if command -v jq >/dev/null 2>&1; then
    local stripped
    stripped="$(strip_sage_hooks "$settings" 2>/dev/null)" || return 1
    [ "$(jq -S . "$settings" 2>/dev/null)" != "$(printf '%s\n' "$stripped" | jq -S . 2>/dev/null)" ]
    return $?
  fi
  # Without jq the exact answer is unreachable, and install.sh's own TIP tells a user to add the
  # compaction hook by hand — on a machine that never had jq at all. Reporting "nothing to
  # remove" over a hook that is still there is the worse error, so name either marker anywhere.
  grep -qF "$(basename "$guard_hook_command")" "$settings" ||
    grep -qF "$compact_hook_marker" "$settings"
}

print_plan() {
  local i
  echo "About to remove from $claude_dir:"
  for (( i = 0; i < ${#target_paths[@]}; i++ )); do
    echo "  ${target_paths[$i]}"
  done
  if settings_has_sage_hooks; then
    if command -v jq >/dev/null 2>&1; then
      echo "  sage's two hooks in $settings (every other entry is kept; jq rewrites the file)"
    else
      echo "  ...but NOT sage's hooks in $settings: editing that file needs jq and jq is not"
      echo "     installed, so they stay. The closing summary says how to delete them by hand."
    fi
  fi
  echo
  echo "Each of those is copied under $backup_root before it goes."
  if plan_removes_a_skill_dir; then
    echo "A skill directory goes whole, so whatever has accumulated inside one since it was"
    echo "installed goes with it, into that same backup — sage keeps its memory and journal in"
    echo "$skills_dest/sage/memory."
  fi
}

plan_removes_a_skill_dir() {
  local path
  for path in ${target_paths[@]+"${target_paths[@]}"}; do
    case "$path" in "$skills_dest"/*) return 0 ;; esac
  done
  return 1
}

confirm() {
  local reply
  if [ "$dry_run" -eq 1 ] || [ "$assume_yes" -eq 1 ]; then
    return 0
  fi
  if [ ! -t 0 ]; then
    echo "ERROR: stdin is not a terminal, so nothing was removed. Re-run with --yes." >&2
    exit 1
  fi
  printf 'Proceed? [y/N] '
  read -r reply || reply=""
  case "$reply" in
    y|Y|yes|YES|Yes) return 0 ;;
    *) echo "Nothing was removed."; exit 0 ;;
  esac
}

apply() {
  local i
  for (( i = 0; i < ${#target_paths[@]}; i++ )); do
    discard "${target_paths[$i]}" "${target_categories[$i]}"
  done
  remove_settings_hooks
}

# Neither `cp -R` nor `rm -rf` follows a symlink it is handed, or one it finds inside a directory
# it walks: the backup stores the link and the removal takes the link, so a link's target is never
# read or deleted here. Measured on this platform rather than assumed.
discard() { # discard <path> <category>
  local path="$1" category="$2"
  if [ ! -e "$path" ] && [ ! -L "$path" ]; then
    return 0
  fi
  if [ "$dry_run" -eq 1 ]; then
    echo "would remove $path"
    removed_any=1
    return 0
  fi
  mkdir -p "$backup_root/$category"
  cp -R "$path" "$backup_root/$category/"
  rm -rf "$path"
  echo "removed $path (saved to $backup_root/$category/$(basename "$path"))"
  removed_any=1
}

# The user's settings.json holds arbitrary config this repo does not own, so this drops the two
# hook commands install.sh added and leaves every other entry. Each bailout says why: under
# `set -euo pipefail` a silent one would read as "removed" and abort the run.
remove_settings_hooks() {
  local stripped
  if [ ! -e "$settings" ]; then
    return 0
  fi
  if [ -L "$settings" ]; then
    echo "NOTE: $settings is a symlink; leaving it. Remove sage's hooks there by hand."
    left_standing+=("$settings — a symlink, so sage's hooks are still in it")
    return 0
  fi
  if ! command -v jq >/dev/null 2>&1; then
    echo "NOTE: jq is not installed, so sage's hooks in $settings were left in place. Delete by"
    echo "      hand: the PreToolUse entry whose command is $guard_hook_command, and the"
    echo "      SessionStart entry whose command mentions $compact_hook_marker."
    left_standing+=("$settings — sage's hooks are still in it; jq was not available to edit it")
    return 0
  fi
  if ! jq empty "$settings" >/dev/null 2>&1; then
    echo "NOTE: $settings does not parse as JSON; leaving it untouched."
    left_standing+=("$settings — does not parse as JSON, so sage's hooks are still in it")
    return 0
  fi
  if ! stripped="$(strip_sage_hooks "$settings")" ||
     ! printf '%s\n' "$stripped" | jq empty >/dev/null 2>&1; then
    echo "NOTE: could not rewrite $settings; left it unchanged."
    return 0
  fi
  if [ "$(printf '%s\n' "$stripped" | jq -S .)" = "$(jq -S . "$settings")" ]; then
    return 0
  fi
  if [ "$dry_run" -eq 1 ]; then
    echo "would remove sage's hooks from $settings"
    removed_any=1
    return 0
  fi
  mkdir -p "$backup_root/settings"
  cp "$settings" "$backup_root/settings/"
  # printf is a shell builtin, so this write cannot fail for want of a binary on PATH. The
  # redirection still truncates before it runs, which is why the copy above is unconditional.
  if ! printf '%s\n' "$stripped" > "$settings"; then
    echo "NOTE: could not write $settings; it may now be truncated. Restore it from"
    echo "      $backup_root/settings/$(basename "$settings")"
    return 0
  fi
  echo "removed sage's hooks from $settings (saved to $backup_root/settings/$(basename "$settings"))"
  removed_any=1
}

# Drops the hook objects install.sh added, then an entry this filter emptied, then a key this
# filter emptied. An entry that already held no hooks, and a key that was already an empty array,
# are the user's and come through untouched — which is why every prune checks the original too.
# The guard command is matched whole because it is an absolute path; the compaction hook is matched
# by a marker substring, which is loose enough to hit a hook of the user's that merely mentions the
# marker, so that half is confined to the matcher install.sh writes it under.
strip_sage_hooks() { # strip_sage_hooks <settings-file>
  jq --arg guard "$guard_hook_command" --arg compact "$compact_hook_marker" '
    def is_command(f):
      (type == "object") and ((.command | type) == "string") and (.command | f);
    def strip(entry_ok; f):
      map(
        if (type != "object") or ((.hooks | type) != "array") or (entry_ok | not) then .
        else
          (.hooks | length) as $before
          | .hooks = (.hooks | map(select(is_command(f) | not)))
          | if $before > 0 and (.hooks | length) == 0 then empty else . end
        end
      );
    def prune($key; $orig):
      if (.hooks[$key] | type) == "array" and (.hooks[$key] | length) == 0
         and ((($orig.hooks // {})[$key] // []) | length) > 0
      then del(.hooks[$key]) else . end;

    . as $orig
    | if type != "object" then .
      elif (.hooks | type) != "object" then .
      else
        (if (.hooks.PreToolUse | type) == "array"
           then .hooks.PreToolUse |= strip(true; . == $guard or startswith($guard + " "))
           else . end)
        | (if (.hooks.SessionStart | type) == "array"
             then .hooks.SessionStart |= strip(.matcher == "compact"; contains($compact))
             else . end)
        | prune("PreToolUse"; $orig)
        | prune("SessionStart"; $orig)
        | (if (.hooks | length) == 0 and (($orig.hooks // {}) | length) > 0
             then del(.hooks) else . end)
      end' "$1"
}

# Every path a collector declined to touch, named where the user will read it. It runs on the
# early-exit path too: a run that finds nothing to remove is exactly the run whose only output
# is this list.
print_left_standing() {
  local entry
  for entry in ${left_standing[@]+"${left_standing[@]}"}; do
    echo "Left standing: $entry"
  done
}

print_summary() {
  echo
  print_left_standing
  if [ "$dry_run" -eq 1 ]; then
    echo "Dry run: nothing was changed."
    return 0
  fi
  if [ "$removed_any" -eq 0 ]; then
    echo "Nothing was removed."
    return 0
  fi
  echo "Backups from this run  -> $backup_root"
  echo "Nothing inside $repo_dir was changed."
  echo "Kept: $backups_dir"
  echo "      It holds every backup install.sh and this script have made, including the ones"
  echo "      above, so removing it is yours to do:  rm -rf \"$backups_dir\""
  if [ -f "$alt_conf" ]; then
    echo "Kept: $alt_conf (you wrote it; install.sh only ever read it)."
  fi
  echo "Kept: $skills_dest, $agents_dest and $styles_dest, empty or not — Claude Code"
  echo "      reads all three and other installers put files there too."
  if settings_holds_nothing; then
    echo "Kept: $settings, now holding nothing at all. install.sh creates it when it has to,"
    echo "      so delete it if it was not yours to begin with."
  fi
  echo "A version of this repo that renamed an agent or an output style leaves the old name"
  echo "      behind in $agents_dest or $styles_dest, where nothing records it; so does a skill"
  echo "      dropped before install.sh moved its manifests out of the skill directory. Older"
  echo "      versions of install.sh also wrote <name>.bak beside anything they replaced, and"
  echo "      only install.sh clears those. Check all four by hand if you have installed more"
  echo "      than one version here."
  echo "Re-install at any time with: $repo_dir/install.sh"
}

settings_holds_nothing() {
  [ -f "$settings" ] || return 1
  command -v jq >/dev/null 2>&1 || return 1
  jq -e '. == {}' "$settings" >/dev/null 2>&1
}

main "$@"
