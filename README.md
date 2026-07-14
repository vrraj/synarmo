# Synarmo - Context-Aware Edge Auto-Suggest Engine  

[![CI](https://github.com/vrraj/synarmo/actions/workflows/ci.yml/badge.svg)](https://github.com/vrraj/synarmo/actions)
[![PyPI - Version](https://img.shields.io/pypi/v/synarmo?color=blue&logo=pypi&logoColor=white)](https://pypi.org/project/synarmo/)
[![GitHub Release](https://img.shields.io/github/v/release/vrraj/synarmo?label=github%20release&color=0f172a&logo=github)](https://github.com/vrraj/synarmo/releases)

Synarmo (derived from *synarmozo* — "to fit together, to join closely") is a
local inference, low-latency auto-suggest engine and Python package for
personalized next-word and short-phrase predictions across messaging, chat, and
assistive typing workflows. It combines context-aware local inference, service
APIs, and llama.cpp/GGUF support for swappable local models.

Synarmo uses [uv](https://docs.astral.sh/uv/) for local development and
dependency management. Install `uv` before using the checkout commands below.

```bash
# Install the Synarmo CLI with llama.cpp and service support
uv tool install "synarmo[llama,service]"
```

The repository includes an
[Interactive UI](#install---interactive-ui-git-clone) for evaluations and tuning
API calls with context and parameters. When `SYNARMO_LLAMA_VERBOSE=1` is enabled
in `.env`, native llama.cpp logs include generation throughput in tokens/sec,
plus KV cache details, Metal/CUDA buffer sizes, and other load diagnostics.


![Synarmo context-aware auto-suggest UI](https://raw.githubusercontent.com/vrraj/synarmo/main/assets/synarmo-context-aware-auto-suggest.png)

Synarmo Key Features:

- a PyPI package for predicting suggestions
- integration surfaces for other applications through REST and WebSocket
- an interactive browser `/ui` for testing and tuning API calls with context and parameters
- a llama.cpp/GGUF-backed engine that can run on CPU or supported GPUs such as Apple Metal, with model and GPU-layer settings controlled through `.env`
- configurable starter-token generation and autoregressive continuation tokens for multi-word suggestions

The primary path uses a local GGUF model for inference through llama.cpp. For no-model verification checks of package install, CLI, service, or UI wiring, see
[Mock Mode](#mock-mode).

---

## Install - PyPI Package

Choose this route when you want the published command-line package. For a
source checkout, use `./scripts/synarmo_pkg_setup.sh` instead; it performs the
checkout-local setup in one command.

Install Synarmo with llama.cpp and service support:

**Step 1: Install the package**

```bash
uv tool install "synarmo[llama,service]"
mkdir -p ~/models/synarmo
```

**Step 2: Set up configuration and the model**

```bash
synarmo setup
```

The command:

- creates `.env` in the current directory only when one does not already exist;
- uses the default local model configuration;
- downloads or verifies the configured GGUF model; and
- prints the installed runtime and next command.

With the default configuration, the model is stored at:

```text
~/models/synarmo/Llama-3.2-1B.Q4_K_M.gguf
```

See
[Configure A Local Model](#configure-a-local-model) for model paths and
[Infrastructure - llama.cpp Configuration](#infrastructure---llamacpp-configuration)
for CPU/GPU settings.

**Step 3: Test the installed package with the llama.cpp backend**

Run one suggestion request:

```bash
synarmo suggest "My goals" \
  --context "in the gym working out with a coach. I am looking to build strength and being able to run up a flight of stairs without tiring" \
  --backend llama-cpp
```

Run the interactive autosuggest loop from the installed package:

```bash
synarmo compose "I want to" \
  --context "At the gym, with my coach. Discussing strength training and endurance goals like running up a flight of stairs." \
  --backend llama-cpp
```

`compose` shows suggestions, lets you choose one, appends it to the typed
text, and immediately predicts the next suggestions.

---

## Install - Interactive `/ui` (Git Repo Clone)

The Interactive `/ui` lets you test local suggestions with context and
auto-suggest parameters. This is the source-checkout route.

**Step 1 — Clone the repository:**

```bash
git clone https://github.com/vrraj/synarmo.git
cd synarmo
```

**Step 2 — Run the setup script:**

```bash
./scripts/synarmo_interactive_setup.sh
```

The script:

- creates `.venv` and installs Synarmo with llama.cpp and FastAPI;
- creates `.env` only when it is missing;
- downloads or verifies the configured GGUF model; and
- prints the next command and UI URL.

Run it once per virtual environment. If you later run plain `uv sync` or
`make install`, run `make llama` before starting the UI to restore the UI and
llama.cpp dependencies.

**Step 3 — Start the UI:**

```bash
make ux
```

`make ux` starts the configured llama.cpp backend in the background and waits
for `/health`. For another trusted device on your LAN, use `make serve-lan`.

**Step 4 — Open the UI:**

```text
http://127.0.0.1:8765/ui
```

The UI calls the same `/health` and `/evaluate/autocomplete` endpoints that a
client application can call directly.

**Stop the background service when you are done:**

```bash
make stop
```

---

### Configure A Local Model

**Step 1 — Create `.env` and the model cache**

For a source checkout:

```bash
cp .env.example .env
mkdir -p ~/models/synarmo
```

For PyPI installs, create a `.env` file in the directory where you run `synarmo` or
start your Python app with the following configuration, then create the cache:

```bash
cat > .env << 'EOF'
LOCAL_MODELS_CACHE=~/models/synarmo
SYNARMO_MAX_SUGGESTIONS=3
SYNARMO_MAX_TOKENS=5
SYNARMO_MAX_SUGGESTION_WORDS=4
SYNARMO_TEMPERATURE=0.0
SYNARMO_TOP_P=1.0
SYNARMO_CONTINUATION_TEMPERATURE=0.5
SYNARMO_CONTINUATION_TOP_P=0.9
SYNARMO_CONTINUATION_TOP_K=20
SYNARMO_LOGPROB_POOL=24
SYNARMO_N_GPU_LAYERS=-1
SYNARMO_LLAMA_VERBOSE=0
SYNARMO_MODEL_REPO_ID=QuantFactory/Llama-3.2-1B-GGUF
SYNARMO_MODEL=Llama-3.2-1B.Q4_K_M.gguf
EOF
mkdir -p ~/models/synarmo
```

**Step 2 — Choose a model source**

For automatic download from Hugging Face:

**Default config**

```dotenv
LOCAL_MODELS_CACHE=~/models/synarmo
SYNARMO_MAX_SUGGESTIONS=3
SYNARMO_MAX_TOKENS=5
SYNARMO_MAX_SUGGESTION_WORDS=4
SYNARMO_TEMPERATURE=0.0
SYNARMO_TOP_P=1.0
SYNARMO_CONTINUATION_TEMPERATURE=0.5
SYNARMO_CONTINUATION_TOP_P=0.9
SYNARMO_CONTINUATION_TOP_K=20
SYNARMO_LOGPROB_POOL=24
SYNARMO_N_GPU_LAYERS=-1
SYNARMO_LLAMA_VERBOSE=0
SYNARMO_MODEL_REPO_ID=QuantFactory/Llama-3.2-1B-GGUF
SYNARMO_MODEL=Llama-3.2-1B.Q4_K_M.gguf
```

For a GGUF file you downloaded yourself:

```dotenv
LOCAL_MODELS_CACHE=~/models/synarmo
SYNARMO_N_GPU_LAYERS=-1
SYNARMO_LLAMA_VERBOSE=0
SYNARMO_MODEL=Llama-3.2-1B.Q4_K_M.gguf
```

For a model stored outside the cache, use an absolute path:

```dotenv
SYNARMO_N_GPU_LAYERS=-1
SYNARMO_LLAMA_VERBOSE=0
SYNARMO_MODEL=/Users/raj/models/qwen2.5-1.5b-instruct-q4_k_m.gguf
```

Relative `SYNARMO_MODEL` filenames resolve inside `LOCAL_MODELS_CACHE`.

**Step 3 — Download or verify the model**

For PyPI installs:

```bash
synarmo model-ensure --backend llama-cpp
```

For a source checkout from the git repository:

```bash
make model-ensure
```

>Both commands load the backend once, downloading the Hugging Face GGUF file if it is missing.

**Step 4 — Run with llama.cpp**

```bash
synarmo suggest "My goals" \
  --context "at the gym working with a coach. I want to get stronger and be able to run up a flight of stairs without getting tired." \
  --backend llama-cpp
```

For a one-off override, pass `--model-path`:

```bash
synarmo suggest "My goals" \
  --backend llama-cpp \
  --model-path ~/models/synarmo/Llama-3.2-1B.Q4_K_M.gguf
```

> Any llama.cpp-compatible GGUF model works. To try another family such as Qwen, change `SYNARMO_MODEL_REPO_ID` and `SYNARMO_MODEL`, or point `SYNARMO_MODEL` at a local `.gguf` file.

---

## Infrastructure - llama.cpp Configuration

Synarmo uses `llama-cpp-python` for GGUF inference. Install with `[llama]`,
then choose the context window and how many layers llama.cpp should offload.
For the local type-ahead path, `SYNARMO_CONTEXT_WINDOW` is passed to
`llama-cpp-python` as `n_ctx`:

```dotenv
SYNARMO_CONTEXT_WINDOW=4096
```

The autocomplete prompt keeps fixed instructions first, stable context next,
and the typed message last. That shape lets embedded `llama-cpp-python` reuse
the longest matching KV prefix across repeated type-ahead calls when the
context stays stable and only the typed suffix grows.

`cache_prompt`, `--cache-ram`, and `--cache-reuse` are `llama-server` settings,
not settings used by Synarmo's current embedded `llama-cpp-python` backend. If
Synarmo adds a separate HTTP `llama-server` backend later, `cache_prompt: true`
should be sent on every completion request; `--cache-ram 0` should be treated
as disabled, not as a boolean false value.

Choose how many layers llama.cpp should offload:

| Value | Behavior | When to use |
| ---: | --- | --- |
| `0` | CPU inference | Portable default, CPU-only machines, or debugging GPU issues. |
| `-1` | Offload all possible layers | Apple Silicon with Metal, NVIDIA CUDA, or another supported GPU build. |
| positive integer | Offload only that many layers | Limited GPU memory or heat/power tuning. |

```dotenv
SYNARMO_N_GPU_LAYERS=-1
```

`SYNARMO_N_GPU_LAYERS` is a layer count, not a GPU count. The default
configuration uses `-1` for Apple Silicon/Metal. If the variable is unset,
Synarmo falls back to CPU-only (`0`) for portability.

Older Intel Macs with discrete low-memory GPUs may report Metal support but
fail during GPU-offloaded requests, sometimes appearing in the browser as
`Failed to fetch`. For those machines, prefer CPU mode:

```dotenv
SYNARMO_N_GPU_LAYERS=0
```

For Apple Silicon Metal offload, 16 GB or more of unified memory is a practical
recommended floor for smooth local testing with the default 1B Q4_K_M model and
service UI. Systems with less available GPU/unified memory should use CPU mode
or a small positive layer count instead of `-1`.

### Performance Logs

Temporarily enable native llama.cpp logs:

```dotenv
SYNARMO_LLAMA_VERBOSE=1
```

Verbose logs include generation tokens/sec, KV cache details, and Metal/CUDA
buffer sizes. Leave it `0` during normal service use.

> On this Apple M2 setup, the default 1B Q4_K_M model with Metal offload commonly shows about 70 - 95 generation tokens/sec on a lightly loaded machine.

### CPU, Metal, CUDA

For CPU-only:

```dotenv
SYNARMO_N_GPU_LAYERS=0
```

On Apple Silicon, the normal install is usually enough. If Metal offload is not
available, rebuild `llama-cpp-python` with Metal:

```bash
CMAKE_ARGS="-DGGML_METAL=on" uv pip install --upgrade --reinstall --no-cache llama-cpp-python
```

For NVIDIA CUDA:

```bash
CMAKE_ARGS="-DGGML_CUDA=on" uv pip install --upgrade --reinstall --no-cache llama-cpp-python
```

Then use:

```dotenv
SYNARMO_N_GPU_LAYERS=-1
```

> If GPU memory is tight, use a positive layer count instead of `-1`.

### Verify GPU Support

```bash
.venv/bin/python -c "import llama_cpp, platform; print(llama_cpp.__version__); print(platform.machine())"
.venv/bin/python -c "from llama_cpp import llama_cpp; print(llama_cpp.llama_supports_gpu_offload())"
```

On macOS, `libggml-metal` should appear here when Metal support is linked:

```bash
otool -L .venv/lib/python3.13/site-packages/llama_cpp/lib/libllama.dylib
```

---

## Interfaces At A Glance

| Interface | Use it for | Example |
| --- | --- | --- |
| Python API | Embed suggestions in another Python app | `SynarmoEngine.load(backend="llama-cpp").suggest("My goals")` |
| CLI | Run quick local prediction commands | `synarmo suggest "My goals" --backend llama-cpp` |
| Service Mode | Run Synarmo as a local server for app, UI, REST, or WebSocket clients | `synarmo serve --backend llama-cpp` |

Service mode starts one local Synarmo process, keeps the model warm, and makes
that model available over local endpoints:

| Endpoint | Use it for |
| --- | --- |
| `GET /health` | Check that the service is ready and see the active backend/model. |
| `POST /suggest` | Request suggestions from an app, script, keyboard, or other client. |
| `POST /evaluate/autocomplete` | Test auto-suggest parameters; this is the endpoint used by `/ui`. |
| `WebSocket /ws/suggest` | Keep a live suggestion channel open while a user types. |
| `GET /ui` | Open the browser interface for testing and tuning suggestions. |

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
    temperature=0.0,
    top_p=1.0,
    continuation_temperature=0.5,
    continuation_top_p=0.9,
    continuation_top_k=20,
    max_tokens=5,
    logprob_pool=24,
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
    temperature=0.0,
    top_p=1.0,
    continuation_temperature=0.5,
    continuation_top_p=0.9,
    continuation_top_k=20,
    max_tokens=5,
    logprob_pool=24,
)
```

The engine loads the model once and reuses it for later predictions when used
as an object or service. If `SYNARMO_MODEL_REPO_ID` is configured and the GGUF
file is missing, this first load downloads the model before returning
suggestions, which can take some time.

After changing code or prompt text, restart any running `synarmo serve`
process so the service reloads the updated Python modules and prompt
construction. The service keeps the model warm while it is running.

### Service Mode

Run Synarmo as a local REST/WebSocket server when another app or the browser
`/ui` needs suggestions. The service loads the backend once and keeps it warm.

```bash
synarmo serve --backend llama-cpp
```

By default it listens at:

```text
http://127.0.0.1:8765
```

Useful endpoints:

| Endpoint | What it does |
| --- | --- |
| `GET /health` | Confirms the service is ready and reports the active backend/model. |
| `POST /suggest` | Returns ranked suggestions for text and optional context. |
| `POST /evaluate/autocomplete` | Returns auto-suggest candidates and token scores for tuning. |
| `WebSocket /ws/suggest` | Accepts repeated suggestion requests over one live connection. |
| `GET /ui` | Opens the browser UI backed by the same service. |

Check readiness from another terminal:

```bash
curl http://127.0.0.1:8765/health
```

If the configured Hugging Face model is missing, startup downloads it before
`/health` is ready.

### Test And Tune With `/ui`

The browser UI is for tuning API calls before building a production client. It
lets you:

- type the current message
- provide conversation or scene context
- change auto-suggest parameters such as choices, candidate words, first-word
  logprob pool, and phrase sampling
- inspect how the service responds

#### Compose Parameters

When testing an installed package or the browser UI, these startup defaults can
come from `.env`. UI changes still apply to the current browser request; edit
`.env` and restart `synarmo serve` or `make ux` to change the initial defaults.

| Parameter | Browser UI default | What it does |
| --- | ---: | --- |
| Choices | 3 | Number of suggestions to show. |
| Tokens | 5 | Maximum generated tokens behind each suggestion. Higher values allow longer completions but can take longer. |
| Words | 4 | Maximum words displayed for each suggestion. |
| First Word Temp | 0.0 | Fixed in the browser UI. Starter branches are chosen from ranked raw logprobs, not from the sampled starter token. |
| First Word Top P | 1.0 | Fixed in the browser UI. The first-word candidate list comes from `Logprobs`, so Top P is not used as a visible starter cutoff. |
| Logprobs | 24 | Number of top next-token log probabilities to request from llama.cpp for starter selection. |
| Phrase Temp | 0.5 | Controls randomness while expanding each selected first word into a phrase. |
| Phrase Top P | 0.9 | Nucleus sampling value used during phrase continuation. |
| Auto - Suggest on Spacebar | On | Automatically asks for new suggestions after typing a space. |

| `.env` setting | Applies to |
| --- | --- |
| `SYNARMO_MAX_SUGGESTIONS` | Choices |
| `SYNARMO_MAX_TOKENS` | Tokens |
| `SYNARMO_MAX_SUGGESTION_WORDS` | Words |
| `SYNARMO_TEMPERATURE` | First Word Temp for API/package calls; browser UI fixes this to `0.0` |
| `SYNARMO_TOP_P` | First Word Top P for API/package calls; browser UI fixes this to `1.0` |
| `SYNARMO_LOGPROB_POOL` | Logprobs |
| `SYNARMO_CONTINUATION_TEMPERATURE` | Phrase Temp |
| `SYNARMO_CONTINUATION_TOP_P` | Phrase Top P |
| `SYNARMO_CONTINUATION_TOP_K` | Advanced continuation top-k guardrail |
| `SYNARMO_CONTEXT_WINDOW` | llama.cpp `n_ctx` |

For auto-suggest, Synarmo separates first-word branch selection from phrase
continuation:

```text
First word:
  raw logprobs -> filter/rank/diversify -> Choices visible branches

Phrase:
  sampler chain -> natural autoregressive continuation
```

`Logprobs` controls how many next-token candidates Synarmo asks llama.cpp to
return for the first-word pool. `Choices` controls how many of those filtered
starter branches are kept and shown. For example, with `Logprobs = 24` and
`Choices = 3`, Synarmo inspects up to 24 likely next tokens, removes empty or
duplicate first-word starters, then expands up to 3 visible suggestions.

Synarmo uses raw logprobs for the first word because auto-suggest needs a small
menu of strong next-phrase directions quickly. Ranking the returned logprob
table gives stable starter branches and useful confidence scores without
running several independent full generations. The browser UI therefore fixes
first-word temperature to `0.0` and first-word Top P to `1.0`.

Continuation sampling controls the autoregressive expansion after a starter has
been selected, so multi-word suggestions can sound natural without using purely
greedy decoding.

#### How The Auto-suggest Flow Works

With the llama.cpp backend, this same auto-suggest flow powers
`synarmo.predict()`, `engine.suggest()`, REST `/suggest`, WebSocket
`/ws/suggest`, and the browser `/ui`.

Suppose the current text is:

```text
I want to
```

Synarmo first asks the model for likely next-token starters. The top scored
starters might be:

```text
go
eat
help
```

Those starters become the beginning of each candidate:

```text
I want to go
I want to eat
I want to help
```

Then Synarmo expands each starter just enough to make a cleaner word or short
phrase:

```text
go outside
eat lunch
help me
```

`Tokens` controls the internal room the model has for that expansion. `Words`
controls how many whitespace-separated words are kept for display. For example,
if the model produces:

```text
go outside with my friends
```

then the displayed suggestion depends on `Words`:

```text
Words = 1  -> go
Words = 2  -> go outside
Words = 3  -> go outside with
```

#### Starter, Continuation, And Probability Flow

The llama.cpp auto-suggest path has two phases:

1. Starter probe: Synarmo asks for one generated token and a `Logprobs`-sized
   table of likely next-token alternatives. It sorts that raw logprob table,
   filters empty tokens, removes duplicate first-word starters, and keeps up to
   `Choices` starters. `Choices` comes from `SYNARMO_MAX_SUGGESTIONS` or the
   browser UI field with the same label.
2. Autoregressive continuation: Synarmo appends each starter to the prompt and
   generates up to `Tokens - 1` future tokens through the llama.cpp sampler
   chain using `Phrase Temp` and `Phrase Top P`. Setting `Phrase Temp` to `0`
   makes this phase greedy; higher values make the multi-word continuation more
   varied. Advanced users can also set `SYNARMO_CONTINUATION_TOP_K` as a hard
   sampling guardrail.

Each candidate retains the model-provided logprob for its starter token. The
browser displays `exp(starter_logprob) * 100`, which is the likelihood of that
first word at the cursor—not the likelihood of the full generated phrase.
`Choices`, `Tokens`, and `Words` do not alter that score. Continuation
logprobs are not requested, keeping live type-ahead responsive.

### Use Service Endpoints

Basic suggestions:

```bash
curl -X POST http://127.0.0.1:8765/suggest \
  -H 'content-type: application/json' \
  -d '{"text":"My goals","context":"in the gym working out with a coach. I am looking to build strength and being able to run up a flight of stairs without tiring"}'
```

Auto-suggest evaluation (via `/evaluate/autocomplete`) used by `/ui`:

```bash
curl -X POST http://127.0.0.1:8765/evaluate/autocomplete \
  -H 'content-type: application/json' \
  -d '{
    "text": "My goals",
    "contexts": ["in the gym working out with a coach. I am looking to build strength and being able to run up a flight of stairs without tiring"],
    "choices": 3,
    "candidate_tokens": 5,
    "candidate_words": 2,
    "temperature": 0.0,
    "top_p": 1.0,
    "continuation_temperature": 0.5,
    "continuation_top_p": 0.9,
    "continuation_top_k": 20,
    "phrase_logprobs": false,
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

From a source checkout, you can also run the repo-only interactive autosuggest
smoke script:

```bash
python scripts/test_package_predict.py
```

The script imports `synarmo` like a normal package consumer, loads compose
defaults from `.env`, and then repeatedly asks for suggestions, lets you pick
one, appends it, and predicts the next set. Use it from a checkout after
installing Synarmo into the active Python environment and setting up a model:

```bash
python scripts/test_package_predict.py \
  --text "I want to" \
  --context "At the gym, with my coach. Discussing strength training and endurance goals like running up a flight of stairs." \
  --backend llama-cpp
```

Add `--auto` to always accept the first candidate for a quick end-to-end run.

Expected shape:

```text
My goals
1. go outside
2. have water
3. talk to you
Choose 1-3, enter custom text, or q to quit:
```

---

## Mock Mode

Mock mode is a deterministic development backend for verifying Synarmo without a
GGUF model, llama.cpp setup, or model download. It returns canned short
suggestions and sends them through the same context, prompt, service, and
ranking pipeline used by the real backend.

Use it to check:

- Python package imports and API calls
- CLI wiring for `suggest` and `compose`
- FastAPI startup, `/health`, `/suggest`, and `/evaluate/autocomplete`
- browser `/ui` request and rendering behavior
- deterministic verification specs and CI runs
- suggestion parsing, deduping, filtering, truncation, and max suggestion count

Install the lightweight package and run a no-model API check:

```bash
uv run --with synarmo python -c "from synarmo import SynarmoEngine; e=SynarmoEngine.load(); print([s.text for s in e.suggest('I want to')])"
```

From a source checkout, run the verification specs without downloading a model:

```bash
uv sync --extra dev
uv run pytest
```

The files under `tests/` are production behavior verification specs. For
example, `test_engine.py` verifies prediction behavior, `test_config.py`
verifies configuration contracts, and `test_service.py` verifies service/API
contracts.

Start the service or browser UI with the mock backend:

```bash
synarmo serve --backend mock
make ux-mock
```

Use `--backend llama-cpp` when checking real suggestion quality, model latency,
memory usage, token probabilities, or how a specific GGUF model behaves.

---

## How It Works

Synarmo keeps UI code outside the core package. A client sends current text,
optional context, and profile settings to the engine. The engine builds a
prompt, runs the selected backend, then ranks and trims candidates into short
suggestions.

```text
client or /ui
  -> SynarmoEngine
  -> context + memory + prompt
  -> model backend
  -> ranking and filtering
  -> short suggestions
```

The model layer is swappable. Any llama.cpp-compatible GGUF model can be tried
by changing `.env` values or passing `--model-path`.

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
llama.cpp adapter can plug in through the same boundary with their own backend
implementation, tokenizer/model loading, decoding loop, sampling behavior, and
tests.

The next product step is a mobile app that uses the same prediction flow with
an on-device model. Synarmo is also intended to serve as a portable reference
implementation for smartphone apps — the Python package defines the
prediction flow, API shape, prompting, context handling, and ranking behavior
that can be reimplemented in a native mobile client with an on-device model
runtime:

- on-device GGUF/Core ML/MLX-style model runtime where appropriate
- shared prompt, memory, and ranking concepts
- local inference prediction loop tuned for short suggestions

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
  ui/                    # Local UI assets
docs/
  ARCHITECTURE.md
```

## License

MIT License - see LICENSE file for details.

## Contributing

Contributions welcome! Please feel free to submit a Pull Request.
