# Synarmo

[![CI](https://github.com/vrraj/synarmo/actions/workflows/ci.yml/badge.svg)](https://github.com/vrraj/synarmo/actions)
[![PyPI - Version](https://img.shields.io/pypi/v/synarmo?color=3776ab&logo=pypi&logoColor=white)](https://pypi.org/project/synarmo/)
[![GitHub Release](https://img.shields.io/github/v/release/vrraj/synarmo?label=github%20release&color=0f172a&logo=github)](https://github.com/vrraj/synarmo/releases)

Synarmo (derived from *synarmozo* — "to fit together, to join closely") is a local AI communication companion for extremely low-latency, personalized type-ahead suggestions across messaging, chat, and assistive typing workflows.

> Local-first, privacy-preserving next-phrase suggestions tuned for 1–4 word completions.

This repository packages the reusable engine:

- `synarmo` Python package for inference, memory, context, ranking, and config
- Pluggable model backends, including a `llama.cpp` GGUF backend for on-device inference
- Local service mode for desktop, web, keyboard, and communication front ends
- Deterministic mock backend and tests that run without downloading a model

## Fast Install

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev,service]"
```

## Model Prerequisites (llama-cpp backend)

Synarmo includes both a deterministic **mock** backend (for tests and CI) and a full browser-based Compose test harness for tuning suggestions, but low-latency deployments typically rely on a local GGUF model via `llama.cpp`. Before calling the engine or service with `backend="llama-cpp"`, make sure you:

1. **Install the extras:** `pip install -e ".[llama,service]"` (adds `llama-cpp-python` + FastAPI bits).
2. **Configure model locations:** copy `.env.example` to `.env`, set `LOCAL_MODELS_CACHE` (defaults to `~/models/synarmo`), and specify `SYNARMO_MODEL`/`SYNARMO_MODEL_REPO_ID` for the GGUF file you want.
3. **Pre-download the weights:** run `make models && make model-ensure` or call `synarmo serve --backend llama-cpp` once; both commands ensure the configured model exists in the cache before suggestions are served.

These steps keep UI code untouched: switching between the mock and llama.cpp backends is just a config/env change, but the model artifacts must be present locally for the GGUF path to succeed.

## Interactive Compose Test UI

Need to tune context, temperature, or token caps without building a full client? The repository ships with a standalone browser UI at `src/synarmo/ui/templates/synarmo.html`. It renders the compose workflow, exposes parameter sliders, and hits the same `/health` plus `/evaluate/autocomplete` endpoints as production clients (@src/synarmo/ui/templates/synarmo.html#315-657).

1. **Start the service** (mock or llama-cpp): `make serve BACKEND=mock` for quick iterations or `make serve BACKEND=llama-cpp` for real GGUF inference.
2. **Host the HTML alongside the service origin.** Copy the template into whatever static route your FastAPI deployment already serves, or mount it behind a simple reverse proxy that forwards `/suggest` and `/evaluate/autocomplete` to the running Synarmo service. (The UI issues relative `fetch("/health")` and `fetch("/evaluate/autocomplete")` calls, so it must share an origin or you need to enable CORS.)
3. **Open the page** (default expectation: `http://127.0.0.1:8765/ui`) and iterate on context, parameter rail values, and the type-ahead loop without touching your host application.

Because the UI is pure static HTML/JS, it is excluded from the PyPI wheel but remains available in the repo for local development and QA. When packaging your own UI, you can reuse this template or embed its logic where appropriate.

## Highlights

- **Local-first inference** – load the model once, keep it warm, and avoid round-trips to remote APIs.
- **Personalized context + memory** – assemble multi-turn context, user traits, and preferences before each suggestion.
- **Pluggable backends** – swap between the deterministic mock backend, llama.cpp GGUF models, or future engines without touching UI code.
- **Service mode + CLI** – expose REST/WebSocket endpoints or use the compose CLI loop for hands-on testing.
- **Lightweight deps** – pure Python core with optional extras for heavier runtimes or service hosting.

## Use Cases

- Assistive communication devices where every keystroke counts
- Messaging, email, or chat clients that need 1–4 word completions inline
- Local/air-gapped deployments that cannot send user text to the cloud
- Agentic workflows that need controllable, low-latency phrase continuations
- Desktop or mobile keyboards that benefit from consistent suggestion quality across modalities

## System Overview

Synarmo separates UI concerns from the reusable engine. The core package covers context assembly, personalization memory, prompt construction, inference, and ranking. Applications (desktop, browser, mobile, or service mode) call the core API or the FastAPI service without embedding model code themselves. See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for the modular roadmap and mobile direction notes.

## Quick Start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev,service]"
pytest
```

Try the package API with the deterministic mock backend:

```python
from synarmo import SynarmoEngine

engine = SynarmoEngine.load(profile="demo")
suggestions = engine.suggest(text="I am", context="At home, watching FIFA world cup soccer match between portugal and spain. This is the Round of 16 and the winning team gets to go to the quarter finals. So far the teams seems even with spain having a slight edge")
print([item.text for item in suggestions])
```

Or use the convenience API:

```python
import synarmo

suggestions = synarmo.predict(
    text="I am",
    context="At home, watching FIFA world cup soccer match between portugal and spain. This is the Round of 16 and the winning team gets to go to the quarter finals. So far the teams seems even with spain having a slight edge",
    user_profile="demo",
    max_suggestions=3,
    max_suggestion_words=4,
    temperature=0.25,
    top_p=0.95,
    max_tokens=32,
)
```

From this repository, you can run the package smoke-test script with the same
public API:

```bash
python scripts/test_package_predict.py \
  --text "I am" \
  --context "At home, watching FIFA world cup soccer match between portugal and spain. This is the Round of 16 and the winning team gets to go to the quarter finals. So far the teams seems even with spain having a slight edge" \
  --choices 3 \
  --max-words 4 \
  --temperature 0.25 \
  --top-p 0.95 \
  --max-tokens 32
```

## GGUF / llama.cpp

Install the optional runtime:

```bash
pip install -e ".[llama,service]"
```

Configure where local models live:

```bash
cp .env.example .env
mkdir -p ~/models/synarmo
```

Synarmo can use `llama-cpp-python` to check the local model cache and download
the configured GGUF file from Hugging Face when it is missing. `LOCAL_MODELS_CACHE`
defaults to `~/models/synarmo` in `.env`.

```dotenv
LOCAL_MODELS_CACHE=~/models/synarmo
SYNARMO_MAX_SUGGESTIONS=3
SYNARMO_MODEL_REPO_ID=hugging-quants/Llama-3.2-1B-Instruct-Q4_K_M-GGUF
SYNARMO_MODEL=llama-3.2-1b-instruct-q4_k_m.gguf
```

This loads the model the same way as:

```python
from llama_cpp import Llama

llm = Llama.from_pretrained(
    repo_id="hugging-quants/Llama-3.2-1B-Instruct-Q4_K_M-GGUF",
    filename="llama-3.2-1b-instruct-q4_k_m.gguf",
)
```

Synarmo passes `LOCAL_MODELS_CACHE` as the local download directory, so model
files stay outside the git repo.

```bash
make models
make model-current
make model-ensure
```

`make model-ensure` loads the configured backend once. For `llama-cpp`, that
checks whether the selected model is already available and downloads it if not.
`make serve` and `synarmo serve --backend llama-cpp` do the same check when the
service starts.

You can still use a manually downloaded local model. `SYNARMO_MODEL` selects a
GGUF file inside `LOCAL_MODELS_CACHE`; absolute paths are used as-is. The legacy
`SYNARMO_MODEL_PATH` variable is still supported as an alias.

Run with the configured model:

```bash
synarmo suggest "I am" \
  --context "At home, watching FIFA world cup soccer match between portugal and spain. This is the Round of 16 and the winning team gets to go to the quarter finals. So far the teams seems even with spain having a slight edge" \
  --backend llama-cpp
```

You can still override the env config for a single run with `--model-path`.

For a more realistic type-ahead loop, use compose mode. It shows the next
suggestions, lets you choose one, appends it, and immediately predicts again:

```bash
synarmo compose "I am" --context "At home, watching FIFA world cup soccer match between portugal and spain. This is the Round of 16 and the winning team gets to go to the quarter finals. So far the teams seems even with spain having a slight edge" --backend llama-cpp
```

The engine loads the model once and reuses it for every prediction when used as
an object or service.

## Service Mode

```bash
synarmo serve --backend llama-cpp
```

REST:

```bash
curl -X POST http://127.0.0.1:8765/suggest \
  -H 'content-type: application/json' \
  -d '{"text":"I am","context":"At home, watching FIFA world cup soccer match between portugal and spain. This is the Round of 16 and the winning team gets to go to the quarter finals. So far the teams seems even with spain having a slight edge"}'
```

WebSocket clients can connect to `ws://127.0.0.1:8765/ws/suggest` and send:

```json
{"text": "I am", "context": "At home, watching FIFA world cup soccer match between portugal and spain. This is the Round of 16 and the winning team gets to go to the quarter finals. So far the teams seems even with spain having a slight edge"}
```

## Testing the Suggestion Loop

Use these checks after installing the llama extras and configuring the GGUF
model in `.env`.

### CLI loop

`compose` is the current terminal UI for the real type-ahead flow. It shows the
configured number of suggestions, lets you choose one, appends it to the typed
text, and immediately predicts the next suggestions.

```bash
source .venv/bin/activate
synarmo compose "I am" \
  --context "At home, watching FIFA world cup soccer match between portugal and spain. This is the Round of 16 and the winning team gets to go to the quarter finals. So far the teams seems even with spain having a slight edge" \
  --backend llama-cpp
```

Expected shape:

```text
I am
1. have water
2. go outside
3. I need help
Choose 1-3, enter custom text, or q to quit:
```

### REST service loop

Start the service in one terminal:

```bash
source .venv/bin/activate
synarmo serve --backend llama-cpp
```

In another terminal, request suggestions:

```bash
curl -X POST http://127.0.0.1:8765/suggest \
  -H 'content-type: application/json' \
  -d '{"text":"I am","context":"At home, watching FIFA world cup soccer match between portugal and spain. This is the Round of 16 and the winning team gets to go to the quarter finals. So far the teams seems even with spain having a slight edge"}'
```

Simulate choosing a suggestion by appending it to `text` and asking again:

```bash
curl -X POST http://127.0.0.1:8765/suggest \
  -H 'content-type: application/json' \
  -d '{"text":"I am","context":"At home, watching FIFA world cup soccer match between portugal and spain. This is the Round of 16 and the winning team gets to go to the quarter finals. So far the teams seems even with spain having a slight edge"}'
```

The service should return JSON with up to `SYNARMO_MAX_SUGGESTIONS` suggestions:

```json
{"suggestions":["go outside","have lunch","eat dinner"],"scores":[0.95,0.95,0.95]}
```

### Browser API tester

With the service running, open:

```text
http://127.0.0.1:8765/docs
```

Use `POST /suggest`, click `Try it out`, and send:

```json
{
  "text": "I am",
  "context": "At home, watching FIFA world cup soccer match between portugal and spain. This is the Round of 16 and the winning team gets to go to the quarter finals. So far the teams seems even with spain having a slight edge"
}
```

### Autocomplete Evaluation Endpoint

The service also exposes the lower-level autocomplete evaluator used by
interactive clients:

```text
POST /evaluate/autocomplete
```

Interactive UI code lives in the repository and is not included in the Python
package artifacts.

## Repository Layout

```text
src/synarmo/
  engine.py              # Main developer API
  config.py              # Runtime configuration
  context.py             # Conversation context assembly
  memory.py              # User profile/personality memory
  prompts.py             # Prompt templates
  suggestions.py         # Ranking and filtering
  models/                # Swappable inference backends
  service/               # REST and WebSocket app factory
docs/
  ARCHITECTURE.md
```

## Mobile Direction

The Python package is the reference engine. For iPhone, the intended path is a
native app with the same engine concepts:

- Core ML or MLX/llama.cpp mobile backend for on-device inference
- shared prompt, memory, and ranking logic ported to Swift where needed
- local service protocol reused for desktop and web development

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for the modular plan.
