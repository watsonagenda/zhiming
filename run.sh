#!/usr/bin/env bash
# environment-awareness: One-command scan → update
# Usage: bash run.sh

set -euo pipefail
cd "$(dirname "$0")"

SCAN="scripts/scan-environment.sh"
UPDATE="scripts/update-tools.sh"

if [ ! -f "$SCAN" ]; then echo "Missing: $SCAN"; exit 1; fi
if [ ! -f "$UPDATE" ]; then echo "Missing: $UPDATE"; exit 1; fi

echo "[zhiming] Scanning environment..."
bash "$SCAN" | bash "$UPDATE"
echo "[zhiming] Done."
