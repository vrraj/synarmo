#!/usr/bin/env bash
# Set up this checkout for the Synarmo CLI, local model inference, and service mode.

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if ! command -v uv >/dev/null 2>&1; then
  echo "uv is required. Install it from https://docs.astral.sh/uv/ first."
  exit 1
fi

echo "Installing Synarmo with llama.cpp, service, and optional OpenAI speech support..."
uv sync --extra llama --extra service --extra voice-openai

echo "Creating or checking configuration and the configured GGUF model..."
.venv/bin/synarmo setup
