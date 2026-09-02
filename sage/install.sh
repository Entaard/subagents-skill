#!/usr/bin/env bash
# Install or update the receipt-bound Sage for Codex Light distribution.
set -euo pipefail

sage_source_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
repository_root="$(cd -- "$sage_source_dir/.." && pwd -P)"

exec python3 "$sage_source_dir/scripts/sage-lifecycle.py" \
  install --source-root "$repository_root" "$@"
