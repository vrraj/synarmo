# Synarmo

Synarmo (derived from synarmozo : to fit together, to join closely) is a local AI communication companion for extremely low-latency,
personalized type-ahead suggestions. It is designed for people who type to
communicate, while keeping the core broad enough for messaging, email, chat,
and other writing workflows.

This repository starts with the reusable engine first:

- `synarmo` Python package for inference, memory, context, ranking, and config
- pluggable model backends, including a `llama.cpp` GGUF backend
- local service mode for desktop, web, keyboard, and communication front ends
- tests that run without downloading a model

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
suggestions = engine.suggest(text="I want to", context="At home after lunch")
print([item.text for item in suggestions])
```

Or use the convenience API:

```python
import synarmo

suggestions = synarmo.predict(
    text="I want to",
    context="Talking with a caregiver about lunch",
    user_profile="demo",
)
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

Synarmo does not download models automatically yet. Download GGUF files into
`LOCAL_MODELS_CACHE`, which defaults to `~/models/synarmo` in `.env`. You can
set `SYNARMO_MODEL_PATH` to a specific GGUF filename; relative values are
resolved from `LOCAL_MODELS_CACHE`.

```dotenv
LOCAL_MODELS_CACHE=~/models/synarmo
SYNARMO_MAX_SUGGESTIONS=3
SYNARMO_MODEL_PATH=Llama-3.2-1B-Instruct-Q4_K_M.gguf
```

Run with the configured model:

```bash
synarmo suggest "I want to" \
  --context "At home, asking for help" \
  --backend llama-cpp
```

You can still override the env config for a single run with `--model-path`.

For a more realistic type-ahead loop, use compose mode. It shows the next
suggestions, lets you choose one, appends it, and immediately predicts again:

```bash
synarmo compose "I want to" --context "At home, asking for help" --backend llama-cpp
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
  -d '{"text":"I want to","context":"At home after lunch"}'
```

WebSocket clients can connect to `ws://127.0.0.1:8765/ws/suggest` and send:

```json
{"text": "I want to", "context": "At home after lunch"}
```

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
