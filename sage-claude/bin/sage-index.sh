#!/bin/sh
# sage-index.sh -- the knowledge-item index, printed on demand. This header is the manual.
#
# USAGE
#   sage-index.sh [memory-dir]          default memory-dir: ~/.claude/skills/sage/memory
#
# OUTPUT
#   One line per knowledge item under <memory-dir>/shared/ and <memory-dir>/local/:
#
#     <id> | <kind> | <class> | <band> | <status> | <first words of the body>
#
#   Fields missing from a file's frontmatter print as an em dash. The body excerpt is the first
#   non-empty line after the frontmatter, truncated. Nothing is stored: the index is computed
#   from the files every time, so there is no stale copy to maintain and nothing to corrupt.
#
# MALFORMED FILES
#   A file with no opening frontmatter fence, an unclosed fence, or no id: is named on stderr
#   and skipped -- the quarantine rule in references/memory.md, "Structural invariants". It
#   never aborts the walk: one bad KI costs one line of stderr, not the index.
#
# EXIT CODES
#   0  index printed (possibly empty on a fresh install). A missing or dangling shared/ is
#      NOT fatal: the protocol's degraded mode (references/memory.md: a dangling `memory/shared`
#      symlink means run on local/ and the journal alone) needs the local KIs, so shared/ is
#      named on stderr and the walk continues over local/ without it.
#   2  <memory-dir>/local does not resolve -- the layout is not v3; the path is named on stderr
#
# Toolchain: sh + awk only, same base set as the sibling scripts.

set -u

mem="${1:-$HOME/.claude/skills/sage/memory}"

if [ ! -d "$mem/local" ]; then
  echo "sage-index: missing directory: $mem/local" >&2
  exit 2
fi
if [ ! -d "$mem/shared" ]; then
  echo "sage-index: shared KIs unreachable (dangling or missing $mem/shared); indexing local/ only" >&2
fi

for file in "$mem"/shared/*.md "$mem"/local/*.md; do
  [ -f "$file" ] || continue
  awk -v file="$file" '
    NR==1 { if ($0=="---") { infront=1; next } else exit 3 }
    infront && $0=="---" { infront=0; next }
    infront {
      if (index($0,"id: ")==1)     id=substr($0,5)
      if (index($0,"kind: ")==1)   kind=substr($0,7)
      if (index($0,"class: ")==1)  class=substr($0,8)
      if (index($0,"band: ")==1)   band=substr($0,7)
      if (index($0,"status: ")==1) status=substr($0,9)
      next
    }
    body=="" && NF>0 { body=$0 }
    END {
      if (infront || id=="") exit 3
      if (kind=="")   kind="—"
      if (class=="")  class="—"
      if (band=="")   band="—"
      if (status=="") status="—"
      if (length(body)>90) body=substr(body,1,90) "…"
      print id " | " kind " | " class " | " band " | " status " | " body
    }
  ' "$file" || echo "sage-index: malformed KI skipped (no frontmatter, unclosed fence, or no id): $file" >&2
done

exit 0
