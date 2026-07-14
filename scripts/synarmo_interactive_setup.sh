#!/usr/bin/env bash
# Set up this checkout for Synarmo's local browser UI.

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

"$ROOT_DIR/scripts/synarmo_pkg_setup.sh"

echo
echo "Interactive UI setup complete:"
echo "  - The local API and browser UI dependencies are installed"
echo "  - The configured llama.cpp model is ready"
echo "Next: run 'make serve-lan' and open http://<this-computer's-IP>:8765/ui"
echo "      Or run 'make ux' for http://127.0.0.1:8765/ui"
