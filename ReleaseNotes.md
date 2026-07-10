# Release Notes

## Docs: README and Documentation Cleanup

This release restructures the project README and companion docs for clarity,
and documents the new LAN service binding helper. It includes a small CLI
help/test update for `synarmo serve --host`.

### Why

The previous README interleaved setup, configuration, and architecture
content, and repeated the same `.env`/model configuration steps in three
different places. This made it unclear which steps were required for each use
case, especially the difference between mock-backed wiring checks and real
GGUF inference.

### What Changed

- **Made real local inference the primary setup path** right after the intro:
  install `synarmo[llama,service]`, configure `.env`, then run with
  `--backend llama-cpp`.
- **Moved mock mode into a supporting role** with a top-level tip and a
  dedicated `Mock Mode` section that explains what it can test: package, CLI,
  service, UI wiring, deterministic tests, and suggestion parsing/ranking.
- **Clarified model download timing** so users know `pip install` does not
  install a GGUF model. The first `--backend llama-cpp` load, `make
  model-ensure`, or service startup can download the configured model and may
  take some time.
- **Updated the Interactive `/ui` path** into a linear sequence: clone the repo
  → create a venv → install dev/llama/service extras → copy `.env.example` →
  create the model cache directory → run `make model-ensure` → run `make ux` →
  open the browser UI.
- **Consolidated model/`.env` configuration** into a single
  `Configure A Local Model` section, referenced by both paths instead of
  duplicated across three sections.
- **Merged duplicate architecture sections** — "Current Shape" and "System
  Overview" combined into one `How It Works` section.
- **Merged forward-looking sections** — "Extending Inference" and "Mobile
  Direction" combined into one `Extending Inference & Mobile Direction`
  section, grouped with other roadmap/architecture content instead of being
  split apart by unrelated sections.
- **Reordered** the document so setup-oriented content (real local inference →
  interactive UI → model configuration → interfaces) comes before
  conceptual/reference content (integration details → use cases → how it works
  → roadmap → repository layout), matching the order a new reader typically
  needs it.
- **Added LAN service guidance** for binding `synarmo serve` to `0.0.0.0`
  on trusted networks, including `make serve-lan` and the loopback caveat for
  `/etc/hosts`.
- **Added UX Make targets** so users can run `make ux` to start the browser
  UI with the configured backend, `make ux-mock` for a no-model wiring check,
  and `make stop` to stop the background service.
- **Fixed docs accuracy issues** around Python version support, `top_p`
  validation, model examples, mock autocomplete fallback behavior, and the
  usage guide heading.

### Not Changed

- The prediction engine, service endpoints, model configuration variables, and
  public Python API are unchanged.
- No model files, generated profiles, or personal conversation data are
  included.
