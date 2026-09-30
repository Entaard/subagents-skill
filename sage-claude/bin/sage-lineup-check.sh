#!/usr/bin/env bash
# RUN BLOCK
#   sage-lineup-check.sh [--memory <mem>] [--repo <dir>] [--alt-conf <file>]
#                        [--changelog <file-or-url> | --no-changelog]
#   sage-lineup-check.sh --ack <token> [same options]   accept the lineup a check printed
#   sage-lineup-check.sh --self-test            fixtures, one ok/FAIL line each
# Default mode compares <mem>/lineup.json with the live lineup (agent model: lines, alt
# config, price ratio, new changelog entries naming a model) and prints one line per
# difference, then `lineup review <token>`. It never writes. Print nothing = no change.
# Only `--ack <token>` writes lineup.json, and only while the differences still hash to that
# token: a change that arrived after the check was printed makes --ack refuse (exit 1).
# `--ack none` accepts a check that printed nothing. Run --ack ONLY after the study is done.
# Exit 0; 1 a refused --ack; 2 bad arguments. Needs jq; without it: one stderr line, exit 0.
# END RUN BLOCK
#
# MAINTAINER MANUAL
#
# Snapshot: {"pinned":{agent:model},"alt":{name:model},"price_ratio":"1 : 2 : 5",
# "changelog_cursor":"2.1.284"}. pinned = the `model:` frontmatter line of each
# <repo>/claude-agents/*.md. alt = <alt-conf> name=value lines, parsed like install.sh
# (trim both halves, skip blank, '#', no '=' and empty values). price ratio = first
# `price ratio sonnet : opus : fable = a : b : c` in <repo>/sage-claude/references/harness.md.
# Defaults: mem ~/.claude/skills/sage/memory; repo = the path in <mem>/source-repo; alt conf
# $SUBAGENTS_ALT_CONF else ~/.claude/subagents-alt-models.conf.
#
# Changelog: `## <version>` headings, `-`/`*` bullets. Bullets under versions newer than the
# cursor (numeric dotted compare) that name a model, an alias/default move or pricing are
# printed. Fetch failure: stderr note, no changelog lines, and --ack keeps the old cursor so
# the missed entries are still reported next time. No cursor: the changelog is not reported
# (there is nothing to be newer than), but --ack still records the newest version.
#
# Internally both sides are flattened to TSV lines `kind<TAB>key<TAB>value` and compared by
# awk. Locale pinned to C.

set -u
export LC_ALL=C

DEFAULT_CHANGELOG_URL='https://raw.githubusercontent.com/anthropics/claude-code/main/CHANGELOG.md'
NO_CURSOR=""

main() {
  if [ "${1:-}" = "--self-test" ]; then run_self_test; exit $?; fi
  local ack=0 token="" mem="" repo="" alt_conf="" changelog="$DEFAULT_CHANGELOG_URL" scan=1
  while [ $# -gt 0 ]; do
    case "$1" in
      --ack) [ $# -ge 2 ] || usage_error "--ack needs the token a check printed, or none"; ack=1; token="$2"; shift ;;
      --memory) [ $# -ge 2 ] || usage_error "--memory needs a value"; mem="$2"; shift ;;
      --repo) [ $# -ge 2 ] || usage_error "--repo needs a value"; repo="$2"; shift ;;
      --alt-conf) [ $# -ge 2 ] || usage_error "--alt-conf needs a value"; alt_conf="$2"; shift ;;
      --changelog) [ $# -ge 2 ] || usage_error "--changelog needs a value"; changelog="$2"; scan=1; shift ;;
      --no-changelog) scan=0 ;;
      *) usage_error "unknown argument $1" ;;
    esac
    shift
  done
  mem="${mem:-$HOME/.claude/skills/sage/memory}"
  if [ -z "$repo" ] && [ -f "$mem/source-repo" ]; then repo="$(head -n 1 "$mem/source-repo")"; fi
  alt_conf="${alt_conf:-${SUBAGENTS_ALT_CONF:-$HOME/.claude/subagents-alt-models.conf}}"
  JQ="$(find_jq)" || { echo "sage-lineup-check: jq not found; lineup not compared" >&2; exit 0; }
  run_check "$ack" "$mem" "$repo" "$alt_conf" "$changelog" "$scan" "$token"
}

usage_error() {
  echo "sage-lineup-check: $1" >&2
  echo "usage: sage-lineup-check.sh [--ack <token|none>] [--memory <mem>] [--repo <dir>] [--alt-conf <file>] [--changelog <file-or-url> | --no-changelog]" >&2
  exit 2
}

find_jq() {
  if command -v jq > /dev/null 2>&1; then command -v jq; return 0; fi
  if [ -x /usr/bin/jq ]; then echo /usr/bin/jq; return 0; fi
  return 1
}

run_check() {
  local ack="$1" mem="$2" repo="$3" alt_conf="$4" changelog="$5" scan="$6" token="$7" status=0
  local work; work="$(mktemp -d)" || exit 0
  # A reader that closes the pipe early (| head) kills this shell before its own rm.
  trap 'rm -rf "$work"' EXIT
  current_lineup_tsv "$repo" "$alt_conf" > "$work/current.tsv"
  local cursor="$NO_CURSOR" have_snapshot=0
  if [ -f "$mem/lineup.json" ] && snapshot_tsv "$mem/lineup.json" > "$work/snapshot.tsv" 2> /dev/null; then
    have_snapshot=1
    cursor="$(awk -F'\t' '$1=="cursor"{print $3}' "$work/snapshot.tsv")"
  fi
  local scanned=0
  if [ "$scan" = 1 ] && fetch_changelog "$changelog" > "$work/changelog.md"; then scanned=1; fi
  if [ "$scanned" = 1 ]; then scan_changelog "$cursor" < "$work/changelog.md" > "$work/scan.tsv"; else : > "$work/scan.tsv"; fi
  report_differences "$have_snapshot" "$work" > "$work/diff.txt"
  if [ "$ack" = 1 ]; then
    if [ "$(review_token "$work/diff.txt")" = "$token" ]; then
      acknowledge "$mem" "$work" "$cursor" "$scanned"
    else
      echo "sage-lineup-check: --ack refused: the lineup changed since that check. Run the check again and study what it prints." >&2
      status=1
    fi
  else
    cat "$work/diff.txt"
    [ -s "$work/diff.txt" ] && echo "lineup review $(review_token "$work/diff.txt")"
  fi
  rm -rf "$work"
  exit "$status"
}

# review_token <diff-file> — `none` for an empty diff, else a short hash of its lines. The
# token binds an --ack to the exact differences a person reviewed.
review_token() {
  if [ ! -s "$1" ]; then echo none; return; fi
  cksum < "$1" | awk '{print $1}'
}

report_differences() {
  local have_snapshot="$1" work="$2"
  if [ "$have_snapshot" = 0 ]; then
    echo "lineup no snapshot: run the lineup study, then sage-lineup-check.sh --ack <token>"
    awk -F'\t' '{printf "lineup current %s %s: %s\n", $1, $2, $3}' "$work/current.tsv"
    awk -F'\t' '$1=="newest"{printf "lineup changelog newest: %s\n", $2}' "$work/scan.tsv"
    return
  fi
  diff_lineups "$work/snapshot.tsv" "$work/current.tsv"
  awk -F'\t' '$1=="actionable"{printf "lineup changelog %s: %s\n", $2, $3}' "$work/scan.tsv"
}

acknowledge() {
  local mem="$1" work="$2" old_cursor="$3" scanned="$4" newest cursor
  newest="$(awk -F'\t' '$1=="newest"{print $2}' "$work/scan.tsv")"
  cursor="$old_cursor"
  if [ "$scanned" = 0 ]; then
    echo "sage-lineup-check: changelog not scanned; cursor kept (${old_cursor:-none recorded})" >&2
  elif [ -n "$newest" ] && [ "$(newer_version "$newest" "$old_cursor")" = yes ]; then
    cursor="$newest"
  fi
  mkdir -p "$mem" || return 1
  local tmp; tmp="$(mktemp "$mem/.lineup.json.XXXXXX")" || return 1
  { cat "$work/current.tsv"; printf 'cursor\t\t%s\n' "$cursor"; } | tsv_to_json > "$tmp" \
    && mv "$tmp" "$mem/lineup.json" || { rm -f "$tmp"; return 1; }
}

newer_version() {
  awk -v a="$1" -v b="$2" 'BEGIN{print (cmp_version(a, b) > 0) ? "yes" : "no"}
    function cmp_version(x, y,  i, xs, ys, nx, ny, n) {
      nx = split(x, xs, "."); ny = split(y, ys, "."); n = (nx > ny) ? nx : ny
      for (i = 1; i <= n; i++) { if (xs[i] + 0 != ys[i] + 0) return (xs[i] + 0 > ys[i] + 0) ? 1 : -1 }
      return 0 }'
}

# ---- current lineup -----------------------------------------------------

current_lineup_tsv() {
  local repo="$1" alt_conf="$2"
  pinned_models "$repo"
  alt_models "$alt_conf"
  price_ratio "$repo"
}

pinned_models() {
  local f
  for f in "$1"/claude-agents/*.md; do
    if [ -f "$f" ]; then
      awk -v name="$(basename "$f" .md)" '
        /^---[ \t]*$/ { fence++; if (fence == 2) exit; next }
        fence == 1 && /^model:/ { v = $0; sub(/^model:[ \t]*/, "", v); sub(/[ \t\r]*$/, "", v)
                                  if (v != "") { printf "pinned\t%s\t%s\n", name, v; exit } }' "$f"
    fi
  done
}

alt_models() {
  if [ -f "$1" ]; then
    awk '{ sub(/\r$/, "") }
      /^[ \t]*$/ || /^[ \t]*#/ { next }
      index($0, "=") == 0 { next }
      { i = index($0, "="); n = substr($0, 1, i - 1); v = substr($0, i + 1)
        gsub(/^[ \t]+|[ \t]+$/, "", n); gsub(/^[ \t]+|[ \t]+$/, "", v)
        if (v != "") printf "alt\t%s\t%s\n", n, v }' "$1"
  fi
}

price_ratio() {
  local file="$1/sage-claude/references/harness.md"
  if [ -f "$file" ]; then
    awk 'match($0, /[Pp]rice ratio sonnet : opus : fable = [0-9.]+ : [0-9.]+ : [0-9.]+/) {
           r = substr($0, RSTART, RLENGTH); sub(/.*= /, "", r); printf "ratio\t\t%s\n", r; exit }' "$file"
  fi
}

# ---- snapshot -----------------------------------------------------------

snapshot_tsv() {
  "$JQ" -r '
    (.pinned // {} | to_entries[] | "pinned\t\(.key)\t\(.value)"),
    (.alt // {} | to_entries[] | "alt\t\(.key)\t\(.value)"),
    (if .price_ratio then "ratio\t\t\(.price_ratio)" else empty end),
    (if .changelog_cursor then "cursor\t\t\(.changelog_cursor)" else empty end)' "$1"
}

tsv_to_json() {
  "$JQ" -Rn '
    [inputs | split("\t")] as $rows
    | {pinned: ([$rows[] | select(.[0] == "pinned") | {(.[1]): .[2]}] | add // {}),
       alt:    ([$rows[] | select(.[0] == "alt")    | {(.[1]): .[2]}] | add // {})}
      + ([$rows[] | select(.[0] == "ratio")  | {price_ratio: .[2]}] | add // {})
      + ([$rows[] | select(.[0] == "cursor" and .[2] != "") | {changelog_cursor: .[2]}] | add // {})'
}

diff_lineups() {
  awk -F'\t' '
    FNR == 1 { file++ }
    file == 1 { if ($1 != "cursor") { old[$1 SUBSEP $2] = $3; seen[$1 SUBSEP $2] = 1; order[++n] = $1 SUBSEP $2 } next }
    file == 2 { new[$1 SUBSEP $2] = $3
                if (!(($1 SUBSEP $2) in seen)) { seen[$1 SUBSEP $2] = 1; order[++n] = $1 SUBSEP $2 } }
    END { for (i = 1; i <= n; i++) {
            k = order[i]; split(k, p, SUBSEP)
            o = (k in old) ? old[k] : "(none)"; w = (k in new) ? new[k] : "(none)"
            if (o == w) continue
            if (p[1] == "ratio") printf "lineup price-ratio: %s -> %s\n", o, w
            else printf "lineup %s %s: %s -> %s\n", p[1], p[2], o, w } }' "$1" "$2"
}

# ---- changelog ----------------------------------------------------------

fetch_changelog() {
  case "$1" in
    http://*|https://*)
      # stderr is captured in a variable: no temp file, so no fixed path under /tmp.
      local err status
      { err="$(curl -fsSL --max-time 20 "$1" 2>&1 >&3 3>&-)"; status=$?; } 3>&1
      if [ "$status" -ne 0 ]; then
        echo "changelog not scanned: $(printf '%s\n' "${err:-fetch failed}" | head -n 1)" >&2; return 1
      fi ;;
    *)
      if [ ! -r "$1" ]; then echo "changelog not scanned: cannot read $1" >&2; return 1; fi
      cat "$1" ;;
  esac
}

# Prints `newest<TAB>ver` once and `actionable<TAB>ver<TAB>bullet` per matching bullet
# under a version newer than the cursor. An empty cursor reports no bullets.
scan_changelog() {
  awk -v cursor="$1" '
    function cmp(x, y,  i, xs, ys, nx, ny, n) {
      nx = split(x, xs, "."); ny = split(y, ys, "."); n = (nx > ny) ? nx : ny
      for (i = 1; i <= n; i++) if (xs[i] + 0 != ys[i] + 0) return (xs[i] + 0 > ys[i] + 0) ? 1 : -1
      return 0 }
    /^## / { ver = ""
             v = $2; sub(/^v/, "", v)
             if (v ~ /^[0-9][0-9.]*$/) { ver = v; if (newest == "" || cmp(v, newest) > 0) newest = v }
             next }
    ver != "" && cursor != "" && cmp(ver, cursor) > 0 && /^[ \t]*[-*] / {
      line = tolower($0)
      if (line ~ /claude-[a-z]+-[0-9]/ || line ~ /sonnet|opus|haiku|fable|mythos/ ||
          line ~ /default .* model/ || line ~ /alias/ || line ~ /pric/) {
        b = $0; sub(/^[ \t]*[-*][ \t]+/, "", b); sub(/[ \t\r]+$/, "", b)
        printf "actionable\t%s\t%s\n", ver, substr(b, 1, 160) } }
    END { if (newest != "") printf "newest\t%s\n", newest }'
}

# ---- self-test ----------------------------------------------------------

T_FAILS=0
check() {
  local name="$1"; shift
  if "$@"; then echo "ok   $name"; else echo "FAIL $name"; T_FAILS=$((T_FAILS + 1)); fi
}

build_fixture() {
  local d="$1"
  mkdir -p "$d/repo/claude-agents" "$d/repo/sage-claude/references" "$d/mem"
  printf -- '---\nname: explorer\nmodel: sonnet\n---\nbody\n' > "$d/repo/claude-agents/explorer.md"
  printf -- '---\nname: verifier\nmodel: opus\n---\nbody\n' > "$d/repo/claude-agents/verifier.md"
  printf 'Snapshot. Price ratio sonnet : opus : fable = 1 : 2 : 5, input and output\n' > "$d/repo/sage-claude/references/harness.md"
  printf '# alts\nexplorer-alt = gpt-5\n\nverifier-alt=gemini-3\nbroken line\nempty=\n' > "$d/alt.conf"
  printf '%s\n' "$d/repo" > "$d/mem/source-repo"
  printf '# Changelog\n\n## 2.1.284\n\n- Fixed a crash\n' > "$d/cl-base.md"
  local tok; tok="$(bash "$0" --memory "$d/mem" --alt-conf "$d/alt.conf" --changelog "$d/cl-base.md" 2> /dev/null | awk '$2=="review"{print $3}')"
  bash "$0" --ack "$tok" --memory "$d/mem" --alt-conf "$d/alt.conf" --changelog "$d/cl-base.md" 2> /dev/null
}

run_check_in() {
  local d="$1"; shift
  bash "$0" --memory "$d/mem" --alt-conf "$d/alt.conf" "$@" 2> /dev/null
}

case_snapshot_written_with_cursor() {
  local d="$1/a"; build_fixture "$d"
  [ "$(jq -c . "$d/mem/lineup.json")" = '{"pinned":{"explorer":"sonnet","verifier":"opus"},"alt":{"explorer-alt":"gpt-5","verifier-alt":"gemini-3"},"price_ratio":"1 : 2 : 5","changelog_cursor":"2.1.284"}' ]
}

case_unchanged_is_silent() {
  local d="$1/b"; build_fixture "$d"
  [ -z "$(run_check_in "$d" --changelog "$d/cl-base.md")" ]
}

case_build_change_only_is_silent() {
  local d="$1/c"; build_fixture "$d"
  printf '## 2.1.285\n\n- Fixed a crash on startup\n- Improved scrolling\n\n## 2.1.284\n\n- Fixed a crash\n' > "$d/cl.md"
  [ -z "$(run_check_in "$d" --changelog "$d/cl.md")" ]
}

case_pinned_edit_is_one_line() {
  local d="$1/d"; build_fixture "$d"
  sed -i.bak 's/^model: opus/model: fable/' "$d/repo/claude-agents/verifier.md"
  [ "$(run_check_in "$d" --no-changelog | grep -v "^lineup review ")" = "lineup pinned verifier: opus -> fable" ]
}

case_alt_edit_is_one_line() {
  local d="$1/e"; build_fixture "$d"
  sed -i.bak 's/gpt-5/gpt-6/' "$d/alt.conf"
  [ "$(run_check_in "$d" --no-changelog | grep -v "^lineup review ")" = "lineup alt explorer-alt: gpt-5 -> gpt-6" ]
}

case_alt_added_uses_none() {
  local d="$1/f"; build_fixture "$d"
  printf 'web-researcher-alt = m1\n' >> "$d/alt.conf"
  [ "$(run_check_in "$d" --no-changelog | grep -v "^lineup review ")" = "lineup alt web-researcher-alt: (none) -> m1" ]
}

case_ratio_change_is_one_line() {
  local d="$1/g"; build_fixture "$d"
  sed -i.bak 's/= 1 : 2 : 5/= 1 : 2 : 6/' "$d/repo/sage-claude/references/harness.md"
  [ "$(run_check_in "$d" --no-changelog | grep -v "^lineup review ")" = "lineup price-ratio: 1 : 2 : 5 -> 1 : 2 : 6" ]
}

# install_bsd_style_sed <dir> — writes <dir>/sed, which turns `\t` in its arguments into a
# literal `t`, the way BSD sed reads `\t` in a replacement.
install_bsd_style_sed() {
  local shim_dir="$1"
  mkdir -p "$shim_dir"
  { echo '#!/usr/bin/env bash'
    echo 'args=(); for a in "$@"; do args+=("${a//\\t/t}"); done'
    echo "exec $(command -v sed) \"\${args[@]}\""; } > "$shim_dir/sed"
  chmod +x "$shim_dir/sed"
}

case_bsd_style_sed_reads_the_ratio() {
  local d="$1/n"; build_fixture "$d"
  install_bsd_style_sed "$d/bsd-sed"
  [ -z "$(PATH="$d/bsd-sed:$PATH" run_check_in "$d" --no-changelog)" ]
}

case_no_snapshot_one_line() {
  local d="$1/h"; build_fixture "$d"; rm "$d/mem/lineup.json"
  [ "$(run_check_in "$d" --no-changelog | head -n 1)" = "lineup no snapshot: run the lineup study, then sage-lineup-check.sh --ack <token>" ]
}

case_model_announcement_survives_until_ack() {
  local d="$1/i"; build_fixture "$d"
  printf '## 2.1.290\n\n- Added Claude Opus 5 as the default model\n\n## 2.1.284\n\n- Fixed a crash\n' > "$d/cl.md"
  local want="lineup changelog 2.1.290: Added Claude Opus 5 as the default model"
  cp "$d/mem/lineup.json" "$d/before.json"
  [ "$(run_check_in "$d" --changelog "$d/cl.md" | grep -v "^lineup review ")" = "$want" ] || return 1
  cmp -s "$d/before.json" "$d/mem/lineup.json" || return 1
  [ "$(run_check_in "$d" --changelog "$d/cl.md" | grep -v "^lineup review ")" = "$want" ] || return 1
  [ "$(run_check_in "$d" --changelog "$d/cl.md" | grep -v "^lineup review ")" = "$want" ] || return 1
  local tok; tok="$(run_check_in "$d" --changelog "$d/cl.md" | awk '$2=="review"{print $3}')"
  bash "$0" --ack "$tok" --memory "$d/mem" --alt-conf "$d/alt.conf" --changelog "$d/cl.md" 2> /dev/null
  [ -z "$(run_check_in "$d" --changelog "$d/cl.md")" ]
}

case_ack_refuses_a_change_nobody_saw() {
  local d="$1/l"; build_fixture "$d"
  printf '## 2.1.284\n\n- Fixed a crash\n' > "$d/cl.md"
  [ -z "$(run_check_in "$d" --changelog "$d/cl.md")" ] || return 1
  printf '## 2.1.285\n\n- Added Claude Opus 6\n\n## 2.1.284\n\n- Fixed a crash\n' > "$d/cl.md"
  cp "$d/mem/lineup.json" "$d/before.json"
  bash "$0" --ack none --memory "$d/mem" --alt-conf "$d/alt.conf" --changelog "$d/cl.md" 2> /dev/null && return 1
  cmp -s "$d/before.json" "$d/mem/lineup.json" || return 1
  [ -n "$(run_check_in "$d" --changelog "$d/cl.md" | grep 'Opus 6')" ]
}

case_first_ack_refuses_a_pin_changed_after_the_check() {
  local d="$1/m"; build_fixture "$d"; rm "$d/mem/lineup.json"
  local tok; tok="$(run_check_in "$d" --no-changelog | awk '$2=="review"{print $3}')"
  sed -i.bak 's/^model: opus/model: UNREVIEWED/' "$d/repo/claude-agents/verifier.md"
  bash "$0" --ack "$tok" --memory "$d/mem" --alt-conf "$d/alt.conf" --no-changelog 2> /dev/null && return 1
  [ ! -e "$d/mem/lineup.json" ]
}

case_ack_without_scan_keeps_cursor() {
  local d="$1/j"; build_fixture "$d"
  bash "$0" --ack none --memory "$d/mem" --alt-conf "$d/alt.conf" --changelog "$d/missing.md" 2> /dev/null
  [ "$(jq -r .changelog_cursor "$d/mem/lineup.json")" = "2.1.284" ]
}

case_version_compare_is_numeric() {
  local d="$1/k"; build_fixture "$d"
  printf '## 2.1.1000\n\n- New sonnet alias\n\n## 2.1.99\n\n- opus tweak\n\n## 2.1.9\n\n- opus old\n' > "$d/cl.md"
  [ "$(run_check_in "$d" --changelog "$d/cl.md" | grep -vc "^lineup review ")" = 1 ]
}

case_bad_argument_exits_2() {
  bash "$0" --bogus > /dev/null 2>&1
  [ $? -eq 2 ]
}

run_self_test() {
  if ! find_jq > /dev/null; then echo "FAIL jq is required for the self-test"; return 1; fi
  JQ="$(find_jq)"
  local dir; dir="$(mktemp -d)" || return 1
  check "ack writes the snapshot with a cursor" case_snapshot_written_with_cursor "$dir"
  check "E4 unchanged snapshot prints nothing" case_unchanged_is_silent "$dir"
  check "E4 build change only prints nothing" case_build_change_only_is_silent "$dir"
  check "E4 one pinned model edit prints one line" case_pinned_edit_is_one_line "$dir"
  check "E4 one alt value edit prints one line" case_alt_edit_is_one_line "$dir"
  check "added alt name prints (none)" case_alt_added_uses_none "$dir"
  check "price ratio change prints one line" case_ratio_change_is_one_line "$dir"
  check "no snapshot prints one line" case_no_snapshot_one_line "$dir"
  check "a BSD-style sed (\\t written as t) still reads the price ratio" case_bsd_style_sed_reads_the_ratio "$dir"
  check "E4b announcement repeats until ack, snapshot untouched, ack silences" case_model_announcement_survives_until_ack "$dir"
  check "ack without a scan keeps the old cursor" case_ack_without_scan_keeps_cursor "$dir"
  check "ack refuses a change that arrived after the check" case_ack_refuses_a_change_nobody_saw "$dir"
  check "a first ack refuses a pin changed after the check" case_first_ack_refuses_a_pin_changed_after_the_check "$dir"
  check "versions compare numerically" case_version_compare_is_numeric "$dir"
  check "bad argument exits 2" case_bad_argument_exits_2
  rm -rf "$dir"
  [ "$T_FAILS" -eq 0 ]
}

main "$@"
