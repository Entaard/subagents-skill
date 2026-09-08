#!/usr/bin/env bash
# Install or safely update the allowlisted Codex Sage package.
set -euo pipefail

sage_source_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
exec python3 "$sage_source_dir/scripts/sage-lifecycle.py" install "$@"
