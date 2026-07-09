# Synarmo

[![CI](https://github.com/vrraj/synarmo/actions/workflows/ci.yml/badge.svg)](https://github.com/vrraj/synarmo/actions)
[![PyPI - Version](https://img.shields.io/pypi/v/synarmo?color=3776ab&logo=pypi&logoColor=white)](https://pypi.org/project/synarmo/)
[![GitHub Release](https://img.shields.io/github/v/release/vrraj/synarmo?label=github%20release&color=0f172a&logo=github)](https://github.com/vrraj/synarmo/releases)

Synarmo (derived from *synarmozo* — "to fit together, to join closely") is a
local AI tool for extremely low-latency, personalized type-ahead suggestions
across messaging, chat, and assistive typing workflows.

> Local-first next-word and next-phrase suggestions tuned for short completions.

Synarmo is intended to be used as:

- a PyPI package for predicting suggestions from Python
- a local FastAPI service for REST and WebSocket clients
- a browser `/ui` for testing and tuning API calls with context and parameters
- a model-backed engine that can test different local GGUF models through `.env`

The application needs a local GGUF model to make useful predictions. The current
runtime backend uses `llama-cpp-python`, loads the model once, and keeps
inference local.

## Current Shape

The reusable package contains the prediction engine:

- `synarmo` Python package for inference, context assembly, prompt construction,
  user memory, ranking, and configuration
- GGUF inference through `llama.cpp` / `llama-cpp-python`
- local service mode for desktop, web, keyboard, mobile, or other clients
- interactive `/ui`  to test and evaluate autocomplete requests with differet contexts and compose token-predication parameters, before building a 
  client with REST APIs.

The next product step is a mobile app that uses the same prediction flow with an
on-device model.

## Install

From PyPI:

```bash
pip install "synarmo[llama,service]"
```

For local development from this repository:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev,llama,service]"
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

When `SYNARMO_MODEL_REPO_ID` is set, `llama-cpp-python` checks
`LOCAL_MODELS_CACHE` and downloads `SYNARMO_MODEL` if it is missing.

You can also use a manually downloaded model:

```dotenv
LOCAL_MODELS_CACHE=~/models/synarmo
SYNARMO_MODEL=Llama-3.2-1B.Q4_K_M.gguf
```

or an absolute path:

```dotenv
SYNARMO_MODEL=/Users/raj/models/qwen2.5-1.5b-instruct-q4_k_m.gguf
```

Any llama.cpp-compatible GGUF model can be tested this way. To try another
family such as Qwen, change `SYNARMO_MODEL_REPO_ID` and `SYNARMO_MODEL`, or point
`SYNARMO_MODEL` at a different local `.gguf` file. No code change is needed for
compatible GGUF models.

Useful model commands:

```bash
make models
make model-current
make model-ensure
```

`make model-ensure` loads the configured backend once. For `llama-cpp`, that
checks whether the selected model is already available and downloads it if
needed. `synarmo serve --backend llama-cpp` performs the same model load when
the service starts.

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

The engine loads the model once and reuses it for later predictions when used as
an object or service.

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

The browser UI is for tuning the API calls before building a production client.
It lets you:

- type the current message
- provide conversation or scene context
- change autocomplete parameters such as choices, candidate words, temperature,
  top-p, and logprob pool
- inspect how the service responds

With the service running, open:

```text
http://127.0.0.1:8765/ui
```

The UI calls the same `/health` and `/evaluate/autocomplete` endpoints that a
client application can call directly.

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
    "logprob_pool": 12
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

`compose` shows suggestions, lets you choose one, appends it to the typed text,
and immediately predicts the next suggestions.

Expected shape:

```text
I want to
1. go outside
2. have water
3. talk to you
Choose 1-3, enter custom text, or q to quit:
```

## Use Cases

- messaging, email, or chat clients that need short completions inline
- assistive typing workflows where each keystroke matters
- local or air-gapped deployments that cannot send user text to remote APIs
- desktop and browser clients that need a local prediction service
- mobile keyboards or apps that need consistent suggestion behavior across
  contexts

## System Overview

Synarmo separates UI concerns from the reusable engine. The core package covers
context assembly, personalization memory, prompt construction, inference, and
ranking. Applications call the Python API directly or communicate with the local
FastAPI service.

The model layer is intentionally swappable at the GGUF level. If another model
works with llama.cpp, Synarmo can test it by changing model configuration rather
than changing application code.

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for design notes and mobile
direction.

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

The current package and service are the reference implementation. The next step
is a mobile app with the same core behavior:

- on-device GGUF/Core ML/MLX-style model runtime where appropriate
- shared prompt, memory, and ranking concepts
- local-first prediction loop tuned for short suggestions


## License

MIT License - see LICENSE file for details.

## Contributing

Contributions welcome! Please feel free to submit a Pull Request.