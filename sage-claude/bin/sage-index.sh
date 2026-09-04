#!/bin/sh
# sage-index.sh -- the knowledge-item index, printed on demand. This header is the manual.
#
# USAGE
#   sage-index.sh [memory-dir]                  default memory-dir: ~/.claude/skills/sage/memory
#   sage-index.sh --stale [months] [memory-dir] default months: 3
#
# OUTPUT -- default mode
#   One line per knowledge item under <memory-dir>/shared/ and <memory-dir>/local/:
#
#     <id> | <kind> | <class> | <band> | <created> | <last-used> | <status> | <first words of body>
#
#   Fields missing from a file's frontmatter print as an em dash. A shared KI's band column is
#   an em dash by design: the band is machine tracking, printed on its stats sidecar's row once
#   a promote pass has written it -- an em dash there too until one has, with the sidecar's
#   count as the interim signal (the memory contract beside sage-promote, The shape). `status` sits second-to-last
#   because its value is free payload that may run to paragraphs; every field before it is
#   positional, so `cut -d'|' -f6` reliably reads last-used. The body excerpt is the first
#   non-empty line after the frontmatter, truncated. Nothing is stored: the index is computed
#   from the files every time, so there is no stale copy to maintain and nothing to corrupt.
#
# OUTPUT -- --stale mode
#   The disuse NOTICE, and it is a notice only: nothing in this ecosystem removes a knowledge
#   item for being unused (the memory contract beside sage-promote, "Knowledge items"). One line per KI whose age
#   since last use is >= <months>, oldest first:
#
#     <id> | <kind> | last-used <date|never> | created <date|unknown> | <n> months
#
#   Age is measured from `last-used:` where the file carries a real date, and from `created:`
#   where it does not -- a KI nothing has ever cited is as old as its filing. A KI with neither
#   date is NOT reported as stale, because its age cannot be proved; those ids are listed on a
#   final `#`-prefixed comment line so they stay visible instead of silently dropping out.
#   Exit 0 whether or not anything is stale: an empty stale list is a result, not a failure.
#
#   A file under shared/ is SKIPPED here, and its stats sidecar stands in for it: a portable KI
#   carries no date at all by design (the memory contract beside sage-promote, the field contract), so walking it
#   would mark every shared rule permanently unassessable. The sidecar reports under the id its
#   `for:` names, tagged `via stats sidecar`, so the notice names the rule and not the sidecar.
#   Two ways that indirection can break, and BOTH are reported rather than swallowed: a shared KI
#   with no sidecar would otherwise vanish from the notice entirely, so it is named on the
#   not-assessable line; and a sidecar whose `for:` names no live shared KI would otherwise print
#   a rule that is not in the corpus, so that line is tagged NO SUCH SHARED KI. Silent
#   invisibility in a notice is the one failure a notice cannot survive.
#
#   Today's date comes from `date +%Y-%m-%d`, overridable with SAGE_TODAY=YYYY-MM-DD so the
#   output is reproducible in a fixture. Month arithmetic is calendar months on the Y/M/D
#   integers -- no date library, same base toolchain as the sibling scripts.
#
# MALFORMED FILES
#   A file with no opening frontmatter fence, an unclosed fence, or no id: is named on stderr
#   and skipped -- the quarantine rule in the memory contract beside sage-promote, "Structural invariants". It
#   never aborts the walk: one bad KI costs one line of stderr, not the index.
#
# EXIT CODES
#   0  index or stale notice printed (possibly empty on a fresh install). A missing or empty
#      shared/ is NOT fatal: the protocol's degraded mode (references/memory.md: a missing
#      `memory/shared/` clone means run on local/ and the journal alone) needs the local KIs,
#      so shared/ is named on stderr and the walk continues over local/ without it.
#   2  <memory-dir>/local does not resolve -- the layout is not v3; the path is named on stderr
#      A --stale argument that is not all digits is read as the memory-dir, not as a bad months
#      value, so `--stale <dir>` works with the default bar and a typo surfaces as this code.
#
# Portability: one file runs on the macOS BSD userland and on Linux, so keep to POSIX sh and POSIX
# utility syntax -- no bashisms, no GNU-only flags, and no digit-option forms such as head -1.
# Checked only by sh -n, dash -n and identical output under both; never against the published spec.

set -u

STALE_MONTHS_DEFAULT=3

mode=index
months="$STALE_MONTHS_DEFAULT"

if [ $# -gt 0 ] && [ "$1" = "--stale" ]; then
  mode=stale
  shift
  case "${1:-}" in
    ''|*[!0-9]*) ;;
    *) months="$1"; shift ;;
  esac
fi

mem="${1:-$HOME/.claude/skills/sage/memory}"
today="${SAGE_TODAY:-$(date +%Y-%m-%d)}"
known_shared=

if [ ! -d "$mem/local" ]; then
  echo "sage-index: missing directory: $mem/local" >&2
  exit 2
fi
shared_has_kis=0
if [ -d "$mem/shared" ]; then
  for _shared_file in "$mem"/shared/*.md; do
    [ -f "$_shared_file" ] || continue
    shared_has_kis=1
    break
  done
fi
if [ "$shared_has_kis" -eq 0 ]; then
  echo "sage-index: shared KIs unreachable (missing or empty $mem/shared); indexing local/ only" >&2
else
  known_shared=$(sed -n 's/^id: //p' "$mem"/shared/*.md 2>/dev/null | tr '\n' ' ')
fi

read_frontmatter='
  function days_in_month(y, mo,   d) {
    d = "31 28 31 30 31 30 31 31 30 31 30 31"
    split(d, dm, " ")
    if (mo == 2 && (y % 4 == 0 && (y % 100 != 0 || y % 400 == 0))) return 29
    return dm[mo] + 0
  }
  # Calendar months, with the anniversary day clamped to the length of the target month: the
  # third month after the 31st of August is the 30th of November, not the 1st of December.
  # No apostrophe may appear anywhere in this awk program -- it lives inside a single-quoted
  # shell string, and one apostrophe silently ends that string.
  function months_since(from, to,   f, t, m, anniversary) {
    split(from, f, "-"); split(to, t, "-")
    m = (t[1] - f[1]) * 12 + (t[2] - f[2])
    anniversary = f[3] + 0
    if (anniversary > days_in_month(t[1] + 0, t[2] + 0)) anniversary = days_in_month(t[1] + 0, t[2] + 0)
    if (t[3] + 0 < anniversary) m--
    return m
  }
  function is_date(v) { return v ~ /^[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]$/ }
  NR==1 { if ($0=="---") { infront=1; next } else exit 3 }
  infront && $0=="---" { infront=0; next }
  infront {
    if (index($0,"id: ")==1)        id=substr($0,5)
    if (index($0,"kind: ")==1)      kind=substr($0,7)
    if (index($0,"class: ")==1)     class=substr($0,8)
    if (index($0,"band: ")==1)      band=substr($0,7)
    if (index($0,"status: ")==1)    status=substr($0,9)
    if (index($0,"created: ")==1)   created=substr($0,10)
    if (index($0,"last-used: ")==1) lastused=substr($0,12)
    if (index($0,"for: ")==1)       forid=substr($0,6)
    next
  }
  body=="" && NF>0 { body=$0 }
'

walk_knowledge_items() {
 for file in "$mem"/shared/*.md "$mem"/local/*.md; do
  [ -f "$file" ] || continue
  case "$file" in "$mem"/shared/*) shared=1 ;; *) shared=0 ;; esac
  awk -v MODE="$mode" -v TODAY="$today" -v BAR="$months" -v SHARED="$shared" \
      -v KNOWN_SHARED="$known_shared" "$read_frontmatter"'
    # No apostrophe may appear anywhere in this awk program -- it lives inside a single-quoted
    # shell string, and one apostrophe silently ends that string.
    END {
      if (infront || id=="") exit 3
      if (kind=="")     kind="—"
      if (class=="")    class="—"
      if (band=="")     band="—"
      if (status=="")   status="—"
      if (created=="")  created="—"
      if (lastused=="") lastused="—"

      if (MODE=="index") {
        if (length(body)>90) body=substr(body,1,90) "…"
        print id " | " kind " | " class " | " band " | " created " | " lastused " | " status " | " body
        exit 0
      }

      # --stale: last use dates the KI; its filing dates one nothing has ever cited.
      if (SHARED) exit 0
      if (kind=="stats" && forid!="") {
        label = forid " (via stats sidecar"                                  \
                (index(" " KNOWN_SHARED " ", " " forid " ") ? "" : " — NO SUCH SHARED KI") ")"
      } else label = id
      anchor = is_date(lastused) ? lastused : (is_date(created) ? created : "")
      if (anchor == "") { print "UNDATED\t" label; exit 0 }
      age = months_since(anchor, TODAY)
      if (age < BAR + 0) exit 0
      print "STALE\t" age "\t" label " | " kind \
            " | last-used " (is_date(lastused) ? lastused : "never") \
            " | created " (is_date(created) ? created : "unknown") \
            " | " age " months"
    }
  ' "$file" || echo "sage-index: malformed KI skipped (no frontmatter, unclosed fence, or no id): $file" >&2
 done
}

if [ "$mode" = index ]; then
  walk_knowledge_items
  exit 0
fi

TAB=$(printf '\t')

# A shared KI whose sidecar is missing has no local record at all, so the walk above cannot see
# it. Name it rather than let it drop out of the notice silently.
uncovered_shared_kis() {
  covered=" $(sed -n 's/^for: //p' "$mem"/local/*.stats.md 2>/dev/null | tr '\n' ' ') "
  for file in "$mem"/shared/*.md; do
    [ -f "$file" ] || continue
    sid=$(sed -n 's/^id: //p' "$file" | head -n 1)
    [ -n "$sid" ] || continue
    case "$covered" in *" $sid "*) ;; *) printf 'UNDATED\t%s (shared KI with no stats sidecar)\n' "$sid" ;; esac
  done
}

{ walk_knowledge_items; uncovered_shared_kis; } | sort -t"$TAB" -k2,2nr | awk -F"$TAB" '
  $1=="STALE"   { print $3; next }
  $1=="UNDATED" { undated = (undated=="" ? $2 : undated ", " $2) }
  END { if (undated != "") print "# not assessable, no created: or last-used: date: " undated }
'

exit 0
