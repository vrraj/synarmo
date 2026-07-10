# Synarmo

[![CI](https://github.com/vrraj/synarmo/actions/workflows/ci.yml/badge.svg)](https://github.com/vrraj/synarmo/actions)
[![PyPI - Version](https://img.shields.io/pypi/v/synarmo?color=3776ab&logo=pypi&logoColor=white)](https://pypi.org/project/synarmo/)
[![GitHub Release](https://img.shields.io/github/v/release/vrraj/synarmo?label=github%20release&color=0f172a&logo=github)](https://github.com/vrraj/synarmo/releases)

Synarmo (derived from *synarmozo* — "to fit together, to join closely") is a
local-first, low-latency auto-suggest engine and Python package for
personalized next-word and short-phrase predictions across messaging, chat, and
assistive typing workflows. It combines context-aware local inference, service
APIs, and llama.cpp/GGUF support for swappable local models.

> Local-first next-word and next-phrase suggestions tuned for short completions.

<video src="./assets/synarmo-auto-suggest.mp4" controls muted playsinline width="100%"></video>

Synarmo is intended to be used as:

- a PyPI package for predicting suggestions from Python
- a local FastAPI service for REST and WebSocket clients
- an interactive browser `/ui` for testing and tuning API calls with context and parameters
- a llama.cpp/GGUF-backed engine that can test different local models through `.env`

There are two ways to work with Synarmo, and they don't require the same setup:

| | Requires | Needs a GGUF model? |
| --- | --- | --- |
| **[Python Package](#python-package)** | `pip install synarmo` | No — only if you want real inference |
| **[Interactive `/ui`](#interactive-ui)** | Cloning the repo | No for wiring checks; yes for real predictions |

---

## Python Package

Install the package from PyPI:

```bash
pip install synarmo
```

This alone lets you exercise the package API with the deterministic mock
backend — **no GGUF model or download required.**

```bash
python -c "from synarmo import SynarmoEngine; e=SynarmoEngine.load(); print([s.text for s in e.suggest('I want to')])"
```

When working from a source checkout, you can also run the test suite:

```bash
pip install -e ".[dev]"
PYTHONPATH=src pytest
```

Tests use deterministic local test doubles and monkeypatched llama.cpp adapter
checks, so the default suite validates package behavior without ever touching
a real model.

### Add real local inference

The basic package install uses the mock backend. For real predictions, install
the llama.cpp extra and configure a local GGUF model first:

```bash
pip install "synarmo[llama,service]"
mkdir -p ~/models/synarmo
```

Create a `.env` file in the directory where you will run `synarmo` or your
Python app:

```dotenv
LOCAL_MODELS_CACHE=~/models/synarmo
SYNARMO_MAX_SUGGESTIONS=3
SYNARMO_MODEL_REPO_ID=hugging-quants/Llama-3.2-1B-Instruct-Q4_K_M-GGUF
SYNARMO_MODEL=llama-3.2-1b-instruct-q4_k_m.gguf
```

Then run Synarmo with the llama.cpp backend:

```bash
synarmo suggest "My goals" \
  --context "in the gym working out with a coach. I am looking to build strength and being able to run up a flight of stairs without tiring" \
  --backend llama-cpp
```

With that `.env`, the first `--backend llama-cpp` run downloads the model to:

```text
~/models/synarmo/llama-3.2-1b-instruct-q4_k_m.gguf
```

Later runs reuse the already downloaded file.

**Summary:** `pip install synarmo` → package works, testable without a model.
Add `[llama,service]` + your own `.env` with `LOCAL_MODELS_CACHE` and
`SYNARMO_MODEL` → same package now produces real suggestions.

---

## Interactive `/ui`

The browser `/ui` is most useful with a real model, but it can also run against
the deterministic `mock` backend for wiring checks. It requires the repository
itself (not just the PyPI package), since it needs the FastAPI service, static
UI assets, and a venv to run in.

![Synarmo context-aware auto-suggest UI](./assets/synarmo-context-aware-auto-suggest.jpeg)

**Step 1 — Clone the repository:**

```bash
git clone https://github.com/vrraj/synarmo.git
cd synarmo
```

**Step 2 — Create a virtual environment and install with dev, llama.cpp, and
service extras:**

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev,llama,service]"
```

**Step 3 — Configure a local GGUF model** — see
[Configure A Local Model](#configure-a-local-model) below.

**Step 4 — Start the service with real local inference:**

```bash
make ux
```

`make ux` starts the configured backend in the background, waits for `/health`,
and prints the browser UI URL. To start the same UX without a model for a quick
wiring check, use:

```bash
make ux-mock
```

**Step 5 — Open the UI shown by `make ux`:**

```text
http://127.0.0.1:8765/ui
```

The UI calls the same `/health` and `/evaluate/autocomplete` endpoints that a
client application can call directly.

---

## Configure A Local Model

Real local inference needs two things:

- the `llama-cpp` backend dependencies, installed with `[llama]`
- a `.env` file that tells Synarmo where the model is and what it is called

Synarmo does not create `.env` automatically. It reads a file literally named
`.env` from the current working directory when `SynarmoEngine.load()` runs.

For a source checkout, start from the included example:

```bash
cp .env.example .env
mkdir -p ~/models/synarmo
```

For an installed PyPI package, there may be no `.env.example` next to your app.
Create `.env` yourself in your app directory or the terminal directory where
you run `synarmo`:

```bash
mkdir -p ~/models/synarmo
```

Use this `.env` for automatic download from Hugging Face:

```dotenv
LOCAL_MODELS_CACHE=~/models/synarmo
SYNARMO_MAX_SUGGESTIONS=3
SYNARMO_MODEL_REPO_ID=hugging-quants/Llama-3.2-1B-Instruct-Q4_K_M-GGUF
SYNARMO_MODEL=llama-3.2-1b-instruct-q4_k_m.gguf
```

When `SYNARMO_MODEL_REPO_ID` is set, `llama-cpp-python` checks
`LOCAL_MODELS_CACHE` and downloads `SYNARMO_MODEL` there if it is missing. With
the default values above, the downloaded file will be stored at:

```text
~/models/synarmo/llama-3.2-1b-instruct-q4_k_m.gguf
```

Use this `.env` for a manually downloaded model in the cache directory:

```dotenv
LOCAL_MODELS_CACHE=~/models/synarmo
SYNARMO_MODEL=Llama-3.2-1B.Q4_K_M.gguf
```

Relative model filenames are resolved from `LOCAL_MODELS_CACHE`, so the example
above points to:

```text
~/models/synarmo/Llama-3.2-1B.Q4_K_M.gguf
```

Use this `.env` for a model stored somewhere else:

```dotenv
SYNARMO_MODEL=/Users/raj/models/qwen2.5-1.5b-instruct-q4_k_m.gguf
```

You can also skip `.env` for one command by passing a model path directly:

```bash
synarmo suggest "My goals" \
  --backend llama-cpp \
  --model-path ~/models/synarmo/Llama-3.2-1B.Q4_K_M.gguf
```

Any llama.cpp-compatible GGUF model works this way. To try another family such
as Qwen, change `SYNARMO_MODEL_REPO_ID` and `SYNARMO_MODEL`, point
`SYNARMO_MODEL` at a different local `.gguf` file, or pass `--model-path`.

Useful model commands:

```bash
make ux
make ux-mock
make stop
make models
make model-current
make model-ensure
```

`make model-ensure` loads the configured backend once. For `llama-cpp`, that
checks whether the selected model is already available and downloads it if
needed. `synarmo serve --backend llama-cpp` performs the same model load when
the service starts.

---

## Interfaces At A Glance

| Interface | Use it for | Example |
| --- | --- | --- |
| Python API | Embed suggestions in another Python app | `SynarmoEngine.load(backend="llama-cpp").suggest("My goals")` |
| CLI | Run quick local prediction commands | `synarmo suggest "My goals" --backend llama-cpp` |
| REST API | Call Synarmo from desktop, web, keyboard, or mobile clients | `POST http://127.0.0.1:8765/suggest` |
| WebSocket | Keep a live local suggestion channel open while a user types | `ws://127.0.0.1:8765/ws/suggest` |
| Browser UI | Test and tune contexts and autocomplete parameters | `http://127.0.0.1:8765/ui` |

Minimal REST request:

```bash
curl -X POST http://127.0.0.1:8765/suggest \
  -H 'content-type: application/json' \
  -d '{"text":"My goals","context":"in the gym working out with a coach. I am looking to build strength and being able to run up a flight of stairs without tiring"}'
```

---

## Integration Details

### Python API

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
    text="My goals",
    context="in the gym working out with a coach. I am looking to build strength and being able to run up a flight of stairs without tiring",
)

print([item.text for item in suggestions])
```

For a one-off call:

```python
import synarmo

suggestions = synarmo.predict(
    text="My goals",
    context="in the gym working out with a coach. I am looking to build strength and being able to run up a flight of stairs without tiring",
    backend="llama-cpp",
    max_suggestions=3,
    max_suggestion_words=4,
    temperature=0.25,
    top_p=0.95,
    max_tokens=32,
)
```

The engine loads the model once and reuses it for later predictions when used
as an object or service.

After changing code or prompt text, restart any running `synarmo serve`
process so the service reloads the updated Python modules. The service keeps
the model warm and does not hot-reload prompt construction while it is
running.

### Service Mode

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

### Test And Tune With `/ui`

The browser UI is for tuning API calls before building a production client. It
lets you:

- type the current message
- provide conversation or scene context
- change autocomplete parameters such as choices, candidate words, temperature,
  top-p, and logprob pool
- inspect how the service responds

#### Compose Parameters

| Parameter | Default | What it does |
| --- | ---: | --- |
| Choices | 3 | Number of suggestions to show. |
| Tokens | 10 | Maximum generated tokens behind each suggestion. Higher values allow longer completions but can take longer. |
| Words | 1 | Maximum words displayed for each suggestion. |
| Temperature | 0.5 | Controls randomness. Lower is more predictable; higher is more varied. |
| Top P | 0.95 | Shapes the useful candidate pool first by keeping likely tokens whose combined probability reaches this value. Lower values are more focused. |
| Logprobs | 24 | Number of scored next-token options to inspect after Top P has shaped the pool. Higher values give Synarmo more candidates to choose from, while Choices still controls how many suggestions appear. |
| Auto - Suggest on Spacebar | On | Automatically asks for new suggestions after typing a space. |

`Logprobs` does not directly mean "show this many suggestions." `Top P` shapes
the candidate pool first, then `Logprobs` controls how many scored options
Synarmo can inspect from that pool. For example, if `Top P = 0.70` leaves only
`go`, `watch`, and `eat` as useful next-token candidates, then `Logprobs = 24`
will not create 24 useful starters. It can only inspect what the pool makes
available. With `Choices = 3`, Synarmo then picks up to 3 useful unique
starters from the inspected options.

### REST And WebSocket API

Basic suggestions:

```bash
curl -X POST http://127.0.0.1:8765/suggest \
  -H 'content-type: application/json' \
  -d '{"text":"My goals","context":"in the gym working out with a coach. I am looking to build strength and being able to run up a flight of stairs without tiring"}'
```

Autocomplete evaluation used by `/ui`:

```bash
curl -X POST http://127.0.0.1:8765/evaluate/autocomplete \
  -H 'content-type: application/json' \
  -d '{
    "text": "My goals",
    "contexts": ["in the gym working out with a coach. I am looking to build strength and being able to run up a flight of stairs without tiring"],
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
{"text": "My goals", "context": "in the gym working out with a coach. I am looking to build strength and being able to run up a flight of stairs without tiring"}
```

### CLI Suggestion Loop

Run a single suggestion request:

```bash
synarmo suggest "My goals" \
  --context "in the gym working out with a coach. I am looking to build strength and being able to run up a flight of stairs without tiring" \
  --backend llama-cpp
```

Run the terminal compose loop:

```bash
synarmo compose "My goals" \
  --context "in the gym working out with a coach. I am looking to build strength and being able to run up a flight of stairs without tiring" \
  --backend llama-cpp
```

`compose` shows suggestions, lets you choose one, appends it to the typed
text, and immediately predicts the next suggestions.

Expected shape:

```text
My goals
1. go outside
2. have water
3. talk to you
Choose 1-3, enter custom text, or q to quit:
```

---

## Use Cases

- messaging, email, or chat clients that need short completions inline
- assistive typing workflows where each keystroke matters
- local or air-gapped deployments that cannot send user text to remote APIs
- desktop and browser clients that need a local prediction service
- mobile keyboards or apps that need consistent suggestion behavior across
  contexts

---

## How It Works

Synarmo separates UI concerns from the reusable engine. The core package
covers context assembly, personalization memory, prompt construction,
inference, and ranking. Applications call the Python API directly or
communicate with the local FastAPI service.

The reusable package contains the prediction engine:

- `synarmo` Python package for inference, context assembly, prompt
  construction, user memory, ranking, and configuration
- GGUF inference through `llama.cpp` / `llama-cpp-python`
- local service mode for desktop, web, keyboard, mobile, or other clients
- interactive `/ui` to test and evaluate autocomplete requests with different
  contexts and compose token-prediction parameters, before building a client
  with REST APIs

The model layer is intentionally swappable at the GGUF level. If another
model works with llama.cpp, Synarmo can test it by changing model
configuration rather than changing application code.

## Extending Inference & Mobile Direction

Synarmo currently ships with a `llama-cpp` runtime backend for local GGUF
model inference. The core engine is designed around a small backend boundary:

```python
class ModelBackend(Protocol):
    name: str

    def generate(self, prompt: str, options: GenerationOptions) -> str:
        ...
```

That means the prompt builder, context assembly, ranking, CLI, and service
APIs can stay stable while a new runtime adapter implements `generate(...)`.
Additional runtimes such as ONNX, MLX, Core ML, or a mobile-specific
llama.cpp adapter would need their own backend implementation,
tokenizer/model loading, decoding loop, sampling behavior, and tests. They are
extension points rather than built-in runtime support today.

The next product step is a mobile app that uses the same prediction flow with
an on-device model. Synarmo is also intended to serve as a portable reference
implementation for smartphone apps — the Python package defines the
prediction flow, API shape, prompting, context handling, and ranking behavior
that can be reimplemented in a native mobile client with an on-device model
runtime:

- on-device GGUF/Core ML/MLX-style model runtime where appropriate
- shared prompt, memory, and ranking concepts
- local-first prediction loop tuned for short suggestions

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

## License

MIT License - see LICENSE file for details.

## Contributing

Contributions welcome! Please feel free to submit a Pull Request.
