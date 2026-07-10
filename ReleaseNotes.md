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

- **Split setup into two clear paths** right after the intro:
  - **Python Package** — `pip install synarmo` is now explicitly presented as
    usable out of the box with the deterministic mock backend and no GGUF
    download. Adding real inference (`pip install "synarmo[llama,service]"` +
    a configured model) is shown as an incremental step on the same path.
  - **Interactive `/ui`** — now its own linear sequence: clone the repo →
    create a venv → install dev/llama/service extras → configure a model →
    run `synarmo serve --backend llama-cpp` → open the browser UI. Clarified
    that `/ui` can run with the mock backend for wiring checks, but real
    predictions require a configured GGUF model.
- **Added a quick-comparison table** immediately after the intro so a reader
  can tell which path they need before reading further.
- **Consolidated model/`.env` configuration** into a single
  `Configure A Local Model` section, referenced by both paths instead of
  duplicated across three sections.
- **Merged duplicate architecture sections** — "Current Shape" and "System
  Overview" combined into one `How It Works` section.
- **Merged forward-looking sections** — "Extending Inference" and "Mobile
  Direction" combined into one `Extending Inference & Mobile Direction`
  section, grouped with other roadmap/architecture content instead of being
  split apart by unrelated sections.
- **Reordered** the document so setup-oriented content (Quick paths →
  Interfaces at a glance → Configuration) comes before conceptual/reference
  content (Integration Details → Use Cases → How It Works → Roadmap →
  Repository Layout), matching the order a new reader typically needs it.
- **Added LAN service guidance** for binding `synarmo serve` to `0.0.0.0`
  on trusted networks, including `make serve-lan` and the loopback caveat for
  `/etc/hosts`.
- **Added UX Make targets** so users can run `make ux` to start the browser
  UI with the configured backend, `make ux-mock` for a no-model wiring check,
  and `make stop` to stop the background service.
- **Fixed docs accuracy issues** around Python version support, `top_p`
  validation, mock autocomplete fallback behavior, and the usage guide heading.

### Not Changed

- The prediction engine, service endpoints, model configuration variables, and
  public Python API are unchanged.
- No model files, generated profiles, or personal conversation data are
  included.
