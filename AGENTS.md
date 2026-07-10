# AGENTS.md

## Project Summary

Synarmo is a local, private AI communication companion that helps people who type to communicate by predicting short next-word or next-phrase suggestions. The core goal is low-latency, personalized type-ahead that learns a user's style, preferences, conversation context, and intent while keeping inference local whenever possible.

## Architecture

Synarmo is split into two layers:

- `synarmo` core Python package: inference, model lifecycle, context assembly, user memory, prompt construction, suggestion ranking/filtering, configuration, and service mode.
- Applications: desktop, web, keyboard, mobile, browser, or other UIs that call the core package or local service.

The core package should stay UI-free and reusable.

## Current Repo Shape

- `src/synarmo/engine.py`: public engine API, including `SynarmoEngine.load(...)`, `engine.suggest(...)`, and convenience `predict(...)`.
- `src/synarmo/models/`: pluggable model backends. Current backends are `mock` for deterministic tests and `llama-cpp` for GGUF models.
- `src/synarmo/service/`: FastAPI app factory for REST and WebSocket local service mode.
- `src/synarmo/context.py`, `memory.py`, `prompts.py`, `suggestions.py`: context, personalization, prompt, and ranking logic.
- `tests/`: lightweight tests that run without downloading a model.
- `docs/ARCHITECTURE.md`: design notes and future mobile direction.

## Design Principles

- Load the model once and keep it warm.
- Keep the Python package modular and backend-swappable.
- Keep suggestions short, usually 1 to 4 words.
- Prefer local inference and local storage.
- Keep UI concerns out of the core package.
- Keep dependencies light; optional extras should cover heavier runtimes and service mode.
- Make the mock backend useful enough for fast tests and API development.

## Common Commands

```bash
PYTHONPATH=src python3 -m synarmo.cli suggest "I want to" --context "At home"
PYTHONPATH=src python3 -c "from synarmo import SynarmoEngine; e=SynarmoEngine.load(); print([s.text for s in e.suggest('I want to')])"
python3 -m compileall src tests
```

When dependencies are installed:

```bash
pip install -e ".[dev,service]"
pytest
synarmo serve
```

For GGUF inference:

```bash
pip install -e ".[llama,service]"
cp .env.example .env
mkdir -p ~/models/synarmo
synarmo suggest "I want to" --backend llama-cpp
```

Local GGUF files should live under `LOCAL_MODELS_CACHE` from `.env`, defaulting
to `~/models/synarmo`. Set `SYNARMO_MODEL_PATH` in `.env` to the model filename
or pass `--model-path` for a one-off override.

## Notes For Future Agents

- The repo is intended to remain private.
- Do not commit model files, generated profiles, or personal conversation data.
- If editing outside the active workspace root, respect sandbox approvals.
- Before finishing documentation changes, verify every configuration value,
  command, model reference, endpoint, and behavior claim against the source
  configuration files and the code that implements or reads them.
- Before finishing code changes, run at least a syntax or smoke check if full tests are unavailable.
