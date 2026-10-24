#!/usr/bin/env bash
# health_check.sh - wrapper that delegates to the portable Python implementation.
# This preserves the original entry point while making the tool usable on systems
# where bash/systemd is not available.

set -u

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"

for PYTHON_BIN in "${PYTHON_BIN:-python3}" python python3; do
  if command -v "$PYTHON_BIN" >/dev/null 2>&1; then
    exec "$PYTHON_BIN" "$SCRIPT_DIR/health_check.py" "$@"
  fi
done

echo "Python 3 is required to run the health checks." >&2
exit 2
