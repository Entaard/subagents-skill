#!/usr/bin/env bash
# Remove only unchanged files owned by the receipt-bound Codex Sage package.
set -euo pipefail

sage_source_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
exec python3 "$sage_source_dir/scripts/sage-lifecycle.py" uninstall "$@"
