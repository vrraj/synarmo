---
layout: default
title: "Synarmo: Local-First Auto-Suggest Engine"
description: "A local-first, low-latency auto-suggest engine for personalized next-word and short-phrase predictions across messaging, chat, and assistive typing workflows."
---

# Synarmo: Local-First Auto-Suggest Engine

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

Synarmo (derived from *synarmozo* — "to fit together, to join closely") is a local-first, low-latency auto-suggest engine and Python package for personalized next-word and short-phrase predictions across messaging, chat, and assistive typing workflows. It combines context-aware local inference, service APIs, and llama.cpp/GGUF support for swappable local models.

> Local-first next-word and next-phrase suggestions tuned for short completions.

Synarmo is intended to be used as:

- a PyPI package for predicting suggestions from Python
- a local FastAPI service for REST and WebSocket clients
- an interactive browser `/ui` for testing and tuning API calls with context and parameters
- a llama.cpp/GGUF-backed engine that can test different local models through `.env`

> The application needs a local GGUF model to make useful predictions. The current runtime backend uses `llama-cpp-python`, loads the model once, and keeps inference local.

## Use Cases

- messaging, email, or chat clients that need short completions inline
- assistive typing workflows where each keystroke matters
- local or air-gapped deployments that cannot send user text to remote APIs
- desktop and browser clients that need a local prediction service
- mobile keyboards or apps that need consistent suggestion behavior across contexts

## System Overview

Synarmo separates UI concerns from the reusable engine. The core package covers context assembly, personalization memory, prompt construction, inference, and ranking. Applications call the Python API directly or communicate with the local FastAPI service.

The model layer is intentionally swappable at the GGUF level. If another model works with llama.cpp, Synarmo can test it by changing model configuration rather than changing application code.

## Install

### PyPI Package

Step 1: install the base Python package:

```bash
pip install synarmo
```

Step 2: install the llama.cpp model runtime and service modules:

```bash
pip install "synarmo[llama,service]"
```

Then configure a GGUF model before running prediction commands such as `synarmo suggest`, `synarmo compose`, or `synarmo serve --backend llama-cpp`. The default `.env.example` points at a small Hugging Face GGUF model and `llama-cpp-python` downloads it on first load if it is not already in `LOCAL_MODELS_CACHE`.

## Test The Package Without A Model

You can verify the package, prompt logic, ranking, service wiring, and llama.cpp adapter integration without downloading a GGUF model:

```bash
python3 -m compileall src tests
```

After installing development dependencies:

```bash
pip install -e ".[dev]"
PYTHONPATH=src pytest
```

The default test suite does not require a model download. Tests use deterministic local test doubles and monkeypatched llama.cpp adapter checks, so they can validate package behavior quickly while keeping real GGUF inference as a separate runtime smoke test.

## Interactive UI From The Repository

Step 1: clone the repository:

```bash
git clone https://github.com/vrraj/synarmo.git
cd synarmo
```

Step 2: create a virtual environment and install the repo with development, llama.cpp, and service modules:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev,llama,service]"
```

Step 3: configure a local GGUF model:

```bash
cp .env.example .env
mkdir -p ~/models/synarmo
```

Step 4: start the service and open the interactive UI:

```bash
synarmo serve --backend llama-cpp
```

```text
http://127.0.0.1:8765/ui
```

## Configure A Local Model

Copy the example environment file and choose a GGUF model:

```bash
cp .env.example .env
mkdir -p ~/models/synarmo
```

Default `.env` shape:

```dotenv
LOCAL_MODELS_CACHE=~/models/synarmo
SYNARMO_MAX_SUGGESTIONS=3
SYNARMO_MODEL_REPO_ID=hugging-quants/Llama-3.2-1B-Instruct-Q4_K_M-GGUF
SYNARMO_MODEL=llama-3.2-1b-instruct-q4_k_m.gguf
```

When `SYNARMO_MODEL_REPO_ID` is set, `llama-cpp-python` checks `LOCAL_MODELS_CACHE` and downloads `SYNARMO_MODEL` if it is missing.

Smoke test the full package-plus-model setup with:

```bash
synarmo suggest "I want to" \
  --context "At home, asking for help" \
  --backend llama-cpp
```

This smoke test is useful after installing `synarmo[llama]` or changing model configuration because it verifies the real runtime path: the package imports, `llama-cpp-python` loads, the configured GGUF file is found or downloaded, and Synarmo returns suggestions through the same engine used by the CLI and service. If the model has not been downloaded yet, this first run can take a while because it has to fetch and load the GGUF file. Later predictions reuse the already downloaded model.

You can also use a manually downloaded model:

```dotenv
LOCAL_MODELS_CACHE=~/models/synarmo
SYNARMO_MODEL=Llama-3.2-1B.Q4_K_M.gguf
```

or an absolute path:

```dotenv
SYNARMO_MODEL=/Users/raj/models/qwen2.5-1.5b-instruct-q4_k_m.gguf
```

Any llama.cpp-compatible GGUF model can be tested this way. To try another family such as Qwen, change `SYNARMO_MODEL_REPO_ID` and `SYNARMO_MODEL`, or point `SYNARMO_MODEL` at a different local `.gguf` file. No code change is needed for compatible GGUF models.

## Python API

Use `SynarmoEngine` when embedding prediction into another Python app:

```python
from synarmo import SynarmoEngine

engine = SynarmoEngine.load(
    backend="llama-cpp",
    max_suggestions=3,
    max_suggestion_words=4,
    temperature=0.25,
    top_p=0.95,
    max_tokens=32,
)

suggestions = engine.suggest(
    text="I want to",
    context="At home, asking for help",
)

print([item.text for item in suggestions])
```

For a one-off call:

```python
import synarmo

suggestions = synarmo.predict(
    text="I want to",
    context="At home, asking for help",
    backend="llama-cpp",
    max_suggestions=3,
    max_suggestion_words=4,
    temperature=0.25,
    top_p=0.95,
    max_tokens=32,
)
```

The engine loads the model once and reuses it for later predictions when used as an object or service.

After changing code or prompt text, restart any running `synarmo serve` process so the service reloads the updated Python modules. The service keeps the model warm and does not hot-reload prompt construction while it is running.

## Service Mode

Start the local service with the configured `.env` model:

```bash
synarmo serve --backend llama-cpp
```

When using `pyenv` and a specific local GGUF file:

```bash
pyenv exec synarmo serve \
  --backend llama-cpp \
  --model-path ~/models/synarmo/Llama-3.2-1B.Q4_K_M.gguf
```

The service defaults to:

```text
http://127.0.0.1:8765
```

Check health:

```bash
curl http://127.0.0.1:8765/health
```

## Test And Tune With `/ui`

The browser UI is for tuning the API calls before building a production client. It lets you:

- type the current message
- provide conversation or scene context
- change autocomplete parameters such as choices, candidate words, temperature, top-p, and logprob pool
- inspect how the service responds

With the service running, open:

```text
http://127.0.0.1:8765/ui
```

The UI calls the same `/health` and `/evaluate/autocomplete` endpoints that a client application can call directly.

### Compose Parameters

| Parameter | Default | What it does |
| --- | ---: | --- |
| Choices | 3 | Number of suggestions to show. |
| Tokens | 10 | Maximum generated tokens behind each suggestion. Higher values allow longer completions but can take longer. |
| Words | 1 | Maximum words displayed for each suggestion. |
| Temperature | 0.5 | Controls randomness. Lower is more predictable; higher is more varied. |
| Top P | 0.95 | Shapes the useful candidate pool first by keeping likely tokens whose combined probability reaches this value. Lower values are more focused. |
| Logprobs | 24 | Number of scored next-token options to inspect after Top P has shaped the pool. Higher values give Synarmo more candidates to choose from, while Choices still controls how many suggestions appear. |
| Auto - Suggest on Spacebar | On | Automatically asks for new suggestions after typing a space. |

`Logprobs` does not directly mean "show this many suggestions." `Top P` shapes the candidate pool first, then `Logprobs` controls how many scored options Synarmo can inspect from that pool. For example, if `Top P = 0.70` leaves only `go`, `watch`, and `eat` as useful next-token candidates, then `Logprobs = 24` will not create 24 useful starters. It can only inspect what the pool makes available. With `Choices = 3`, Synarmo then picks up to 3 useful unique starters from the inspected options.

## REST And WebSocket API

Basic suggestions:

```bash
curl -X POST http://127.0.0.1:8765/suggest \
  -H 'content-type: application/json' \
  -d '{"text":"I want to","context":"At home, asking for help"}'
```

Autocomplete evaluation used by `/ui`:

```bash
curl -X POST http://127.0.0.1:8765/evaluate/autocomplete \
  -H 'content-type: application/json' \
  -d '{
    "text": "I want to",
    "contexts": ["At home, asking for help"],
    "choices": 3,
    "candidate_tokens": 10,
    "candidate_words": 2,
    "temperature": 0.5,
    "top_p": 0.95,
    "logprob_pool": 24
  }'
```

WebSocket clients can connect to:

```text
ws://127.0.0.1:8765/ws/suggest
```

and send:

```json
{"text": "I want to", "context": "At home, asking for help"}
```

## CLI Suggestion Loop

Run a single suggestion request:

```bash
synarmo suggest "I want to" \
  --context "At home, asking for help" \
  --backend llama-cpp
```

Run the terminal compose loop:

```bash
synarmo compose "I want to" \
  --context "At home, asking for help" \
  --backend llama-cpp
```

`compose` shows suggestions, lets you choose one, appends it to the typed text, and immediately predicts the next suggestions.

Expected shape:

```text
I want to
1. go outside
2. have water
3. talk to you
Choose 1-3, enter custom text, or q to quit:
```

## Extending Inference

Synarmo currently ships with a `llama-cpp` runtime backend for local GGUF model inference. The core engine is designed around a small backend boundary:

```python
class ModelBackend(Protocol):
    name: str

    def generate(self, prompt: str, options: GenerationOptions) -> str:
        ...
```

That means the prompt builder, context assembly, ranking, CLI, and service APIs can stay stable while a new runtime adapter implements `generate(...)`. Additional runtimes such as ONNX, MLX, Core ML, or a mobile-specific llama.cpp adapter would need their own backend implementation, tokenizer/model loading, decoding loop, sampling behavior, and tests. They are extension points rather than built-in runtime support today.

See [docs/ARCHITECTURE.md](ARCHITECTURE.md) for design notes and mobile direction.

## Repository Layout

```text
src/synarmo/
  engine.py              # Python prediction API
  config.py              # Runtime and model configuration
  context.py             # Context assembly
  memory.py              # Local user profile data
  prompts.py             # Prompt construction
  suggestions.py         # Suggestion ranking and filtering
  models/                # Model backends
  service/               # FastAPI app factory
  ui/                    # Local test UI assets
docs/
  ARCHITECTURE.md
```

## Mobile Direction

The current package and service are the reference implementation. The next step is a smartphone app with the same core behavior. The Python package is not meant to be embedded directly into the phone app; instead, its architecture can be ported into native mobile code:

- on-device GGUF/Core ML/MLX-style model runtime where appropriate
- shared prompt, memory, and ranking concepts
- local-first prediction loop tuned for short suggestions

## Links

- [GitHub Repository](https://github.com/vrraj/synarmo)
- [PyPI Package](https://pypi.org/project/synarmo/)
- [Full README](https://github.com/vrraj/synarmo#readme)
- [API Reference](api-reference.html)
- [Usage Guide](usage-guide.html)
- [Deployment Guide](DEPLOYMENT.html)
