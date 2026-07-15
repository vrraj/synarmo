#!/usr/bin/env bash
# Set up this checkout for Synarmo's local browser UI.

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

"$ROOT_DIR/scripts/synarmo_pkg_setup.sh"

echo
echo "Interactive UI setup complete."
echo "Next: run 'make ux' and open http://127.0.0.1:8765/ui"
