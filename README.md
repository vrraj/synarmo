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

## Testing the Suggestion Loop

Use these checks after installing the llama extras and configuring the GGUF
model in `.env`.

### CLI loop

`compose` is the current terminal UI for the real type-ahead flow. It shows the
configured number of suggestions, lets you choose one, appends it to the typed
text, and immediately predicts the next suggestions.

```bash
source .venv/bin/activate
synarmo compose "I want to" \
  --context "At home, asking for help" \
  --backend llama-cpp
```

Expected shape:

```text
I want to
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
  -d '{"text":"I want to","context":"At home, asking for help"}'
```

Simulate choosing a suggestion by appending it to `text` and asking again:

```bash
curl -X POST http://127.0.0.1:8765/suggest \
  -H 'content-type: application/json' \
  -d '{"text":"I want to have water","context":"At home, asking for help"}'
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
  "text": "I want to",
  "context": "At home, asking for help"
}
```

### Browser UI

With the service running, open:

```text
http://127.0.0.1:8765/ui
```

The browser UI provides a text box, context field, and clickable suggestion
buttons. Clicking a suggestion appends it to the typed text and immediately
requests the next suggestions from the local service. The main UI compose panel
uses the logprob autocomplete evaluator and preserves trailing spaces in the
typed text because `"What"` and `"What "` are different model inputs.

### Autocomplete Evaluation UI

The browser UI also includes an **Autocomplete Evaluation** section for comparing
the logprob-based autocomplete evaluator across multiple contexts. This is the
same evaluator used by `scripts/test_base_model_autocomplete.py`; use this panel
when you want to inspect top next-token logprobs, starter tokens, and the greedy
completion for each candidate.

Install Synarmo once in editable mode so commands work without `PYTHONPATH`:

```bash
pyenv exec python -m pip install -e ".[dev,service,llama]"
```

Start the service with the exact GGUF you want to test:

```bash
pyenv exec synarmo serve \
  --backend llama-cpp \
  --model-path ~/models/synarmo/Llama-3.2-1B.Q4_K_M.gguf
```

Then open:

```text
http://127.0.0.1:8765/ui
```

Use the **Autocomplete Evaluation** panel when you want to compare several
contexts against the same typed prefix. Enter one typed prefix, then enter
multiple contexts separated by blank lines. The UI sends all contexts to:

```text
POST /evaluate/autocomplete
```

The response shows candidate text, starter token, greedy rest text, starter
logprob, and the top next-token logprob list for each context. The status pill at
the top of the UI shows the backend and resolved model path/filename so you can
confirm whether the service is using the base or instruct model.

The **Compose** panel also uses `POST /evaluate/autocomplete`, but only for one
context at a time.

### Current UI status

Synarmo has a minimal browser test UI for local service testing. A production
desktop, mobile, or keyboard UI is still future work.

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
