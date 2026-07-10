---
layout: default
title: "Synarmo: Local-First Auto-Suggest Engine"
description: "A local-first, low-latency auto-suggest engine for personalized next-word and short-phrase predictions across messaging, chat, and assistive typing workflows."
---

# Synarmo

<p align="left">
  <a href="https://pypi.org/project/synarmo/">
    <img src="https://img.shields.io/pypi/v/synarmo?color=3776ab&logo=pypi&logoColor=white" alt="PyPI - Version">
  </a>
  <a href="https://github.com/vrraj/synarmo/releases">
    <img src="https://img.shields.io/github/v/release/vrraj/synarmo?label=github%20release&color=0f172a&logo=github" alt="GitHub Release">
  </a>
  <a href="https://github.com/vrraj/synarmo/actions/workflows/ci.yml">
    <img src="https://github.com/vrraj/synarmo/actions/workflows/ci.yml/badge.svg" alt="CI Status">
  </a>
</p>

Synarmo (derived from *synarmozo* — "to fit together, to join closely") is a
local-first, low-latency auto-suggest engine and Python package for
personalized next-word and short-phrase predictions across messaging, chat, and
assistive typing workflows.

Use it to embed short type-ahead suggestions in Python apps, run a local
REST/WebSocket suggestion service, test autocomplete behavior in a browser
`/ui`, and evaluate different local GGUF models through llama.cpp.

> Local-first next-word and next-phrase suggestions tuned for short completions.

![Synarmo context-aware auto-suggest UI](https://raw.githubusercontent.com/vrraj/synarmo/main/assets/synarmo-context-aware-auto-suggest.jpeg)

## Why this exists

People who type to communicate benefit from suggestions that are fast, short,
context-aware, and personal. Generic completion systems often optimize for long
answers, remote inference, or broad chat behavior. Synarmo focuses on a narrower
loop: the user has typed a partial thought, and the engine should return a few
natural continuations that can be inserted immediately.

The package keeps that loop local where possible. It loads the model once,
keeps it warm, combines the current text with optional context and profile
memory, then ranks and filters candidates into short suggestions.

## Primary use case: local type-ahead suggestions

Synarmo is designed for applications where another UI owns the typing
experience and needs suggestions from a reusable local engine.

```text
User typing -> App UI -> Python API or local service -> SynarmoEngine -> Suggestions
```

In practice:

```text
Current text + optional context + optional profile memory
-> PromptBuilder
-> ModelBackend
-> SuggestionRanker
-> 1 to 4 word suggestions
```

The core package stays UI-free. Applications can call it directly from Python
or talk to the local FastAPI service over REST or WebSocket.

## Architecture overview

Synarmo is split into two layers:

- **Synarmo Core**: inference, model lifecycle, context assembly, user memory,
  prompt construction, suggestion ranking, filtering, configuration, and
  service mode.
- **Applications**: desktop, browser, keyboard, mobile, web, or other UIs that
  call the core package or local service.

Runtime flow:

```text
User typing
  -> Application UI
  -> Python API or local WebSocket
  -> SynarmoEngine
  -> ContextAssembler + UserMemory
  -> PromptBuilder
  -> ModelBackend
  -> SuggestionRanker
  -> Suggestions
```

Current model backends:

- `llama-cpp`: local GGUF inference through `llama_cpp.Llama`

See [Architecture](ARCHITECTURE.html) for the full design notes and mobile
direction.

## What you get

- **Python prediction package** with `SynarmoEngine`, `predict()`, and
  `suggest()`
- **Local llama.cpp/GGUF backend** for real on-device inference
- **Context and profile memory hooks** for personalized suggestions
- **Suggestion ranking and filtering** tuned for short continuations
- **CLI commands** for one-off suggestions and an interactive compose loop
- **FastAPI service mode** for REST, WebSocket, and browser UI clients
- **Interactive `/ui`** for testing context, model behavior, and autocomplete
  parameters

## Install

For real local inference with the service and browser UI support:

```bash
pip install "synarmo[llama,service]"
mkdir -p ~/models/synarmo
```

Create a `.env` file in the directory where you will run `synarmo` or your
Python app:

```dotenv
LOCAL_MODELS_CACHE=~/models/synarmo
SYNARMO_MAX_SUGGESTIONS=3
SYNARMO_MODEL_REPO_ID=QuantFactory/Llama-3.2-1B-GGUF
SYNARMO_MODEL=Llama-3.2-1B.Q4_K_M.gguf
```

When the `llama-cpp` backend starts, Synarmo checks `LOCAL_MODELS_CACHE` and
downloads `SYNARMO_MODEL` from `SYNARMO_MODEL_REPO_ID` if the GGUF file is
missing. The first real request can take longer while the model downloads and
loads; later runs reuse the cached file.

## Quick example

```python
from synarmo import SynarmoEngine

engine = SynarmoEngine.load(
    backend="llama-cpp",
    max_suggestions=3,
    max_suggestion_words=4,
    temperature=0.25,
    top_p=0.95,
    max_tokens=5,
)

suggestions = engine.suggest(
    text="My goals",
    context="in the gym working out with a coach. I am looking to build strength and being able to run up a flight of stairs without tiring",
)

print([item.text for item in suggestions])
```

The engine loads the model once and reuses it for later predictions when used
as an object or service.

## CLI and service

Run a single local suggestion request:

```bash
synarmo suggest "My goals" \
  --context "in the gym working out with a coach. I am looking to build strength and being able to run up a flight of stairs without tiring" \
  --backend llama-cpp
```

Start the local service:

```bash
synarmo serve --backend llama-cpp
```

Service mode keeps one model instance warm and exposes:

| Endpoint | Use it for |
| --- | --- |
| `GET /health` | Check service readiness and active backend/model details. |
| `POST /suggest` | Request ranked suggestions for text and optional context. |
| `POST /evaluate/autocomplete` | Tune autocomplete candidates and token-scoring parameters. |
| `WebSocket /ws/suggest` | Keep a live suggestion channel open while a user types. |
| `GET /ui` | Open the browser interface backed by the same service. |

Minimal REST request:

```bash
curl -X POST http://127.0.0.1:8765/suggest \
  -H 'content-type: application/json' \
  -d '{"text":"My goals","context":"in the gym working out with a coach. I am looking to build strength and being able to run up a flight of stairs without tiring"}'
```

## Interactive UI

The source checkout includes a browser UI for testing local suggestions with
context and autocomplete parameters. It uses the same `/health` and
`/evaluate/autocomplete` endpoints that client applications can call directly.

```bash
git clone https://github.com/vrraj/synarmo.git
cd synarmo
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[llama,service]"
cp .env.example .env
make model-ensure
make ux
```

Open:

```text
http://127.0.0.1:8765/ui
```

Stop the background service when finished:

```bash
make stop
```

## Summary

Synarmo is a reusable local suggestion layer for short, personalized
type-ahead. It is intentionally narrower than a general chatbot: it accepts
current text and context, keeps inference local when configured with a GGUF
model, and returns a few immediately insertable suggestions.

The Python implementation is also the reference shape for future applications,
including desktop clients, browser integrations, keyboards, and mobile apps
that use the same prompt, memory, ranking, and service contracts.

## Links

- [GitHub Repository](https://github.com/vrraj/synarmo)
- [PyPI Package](https://pypi.org/project/synarmo/)
- [Full README](https://github.com/vrraj/synarmo#readme)
- [API Reference](api-reference.html)
- [Usage Guide](usage-guide.html)
- [Deployment Guide](DEPLOYMENT.html)
- [Architecture](ARCHITECTURE.html)
