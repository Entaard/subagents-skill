#!/usr/bin/env bash
# Completely remove the receipt-bound Sage for Codex installation.
set -euo pipefail

sage_source_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
repository_root="$(cd -- "$sage_source_dir/.." && pwd -P)"

exec python3 "$sage_source_dir/scripts/sage-lifecycle.py" \
  uninstall --source-root "$repository_root" "$@"
