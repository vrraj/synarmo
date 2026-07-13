---
layout: default
title: "Architecture | Synarmo"
description: "Design notes and architecture for synarmo package."
---

# Architecture

This document describes the architecture and design principles of the Synarmo auto-suggest engine.

> **New here?** Start with the project overview on the home page: **[Synarmo docs home](https://vrraj.github.io/synarmo/)**.
>
> **Source + releases:** GitHub repo and PyPI package are linked from the home page.

## Table of Contents

- [Product Vision](#product-vision)
- [Two Layers](#two-layers)
- [Runtime Flow](#runtime-flow)
- [Model Backends](#model-backends)
- [Technology Components](#technology-components)
- [Performance Principles](#performance-principles)
- [iPhone Plan](#iphone-plan)

---

## Product Vision

Synarmo is an AI communication companion that learns a user's communication
style, personality, long-term preferences, current conversation, context, and
intent. It uses local inference to provide low-latency personalized suggestions
for people who type to communicate.

## Two Layers

### Synarmo Core

The pip package contains only the AI engine:

- local LLM inference
- model loading and lifecycle
- context management
- profile and memory management
- prompt construction
- suggestion generation
- ranking and filtering
- configuration

The public API should remain small:

```python
from synarmo import SynarmoEngine

engine = SynarmoEngine.load(profile="user", backend="llama-cpp")
engine.suggest(text=current_text, context=current_context)
```

### Synarmo Applications

Applications contain only UI and integration code:

- desktop app
- web app
- local website
- communication app
- keyboard integration
- browser extension
- mobile app

Applications talk to Synarmo Core through the Python API or local service.

## Runtime Flow

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

## Model Backends

Backends implement a small protocol:

```python
class ModelBackend(Protocol):
    def generate(self, prompt: str, options: GenerationOptions) -> str: ...
```

Runtime backend:

- `llama-cpp`: GGUF backend through `llama_cpp.Llama`, with CPU or supported
  GPU offload controlled by `SYNARMO_N_GPU_LAYERS`
- `mock`: deterministic verification backend for API, service, UI, and CI wiring checks

Future backends:

- Core ML for iPhone
- MLX for Apple Silicon experiments
- remote backend for evaluation only

## Technology Components

### Backend

| Component | Role |
| --- | --- |
| `SynarmoEngine` | Main engine API for loading models and generating suggestions |
| `ModelBackend` | Protocol for pluggable inference backends |
| `LlamaCppBackend` | GGUF model inference via llama-cpp-python |
| `MockBackend` | Deterministic verification backend for API, service, UI, and CI wiring checks |
| `ContextAssembler` | Builds conversation context from user memory |
| `UserMemory` | Manages user profiles, preferences, and conversation history |
| `PromptBuilder` | Constructs prompts for the model |
| `SuggestionRanker` | Ranks and filters generated suggestions |
| `SynarmoConfig` | Configuration management with environment variable support |

| Infrastructure Component | Role |
| --- | --- |
| llama-cpp-python | Local GGUF model inference runtime, including CPU, Metal, CUDA, or other supported native backends |
| huggingface-hub | Model downloading and caching for configured Hugging Face repos |
| Core ML | Future iOS model runtime option |
| MLX | Future Apple Silicon experiment runtime option |

### Runtime Configuration

| Setting | Role |
| --- | --- |
| `SYNARMO_MODEL_REPO_ID` | Hugging Face repo used for automatic GGUF download |
| `SYNARMO_MODEL` | GGUF filename in the repo/cache, or a local model path |
| `LOCAL_MODELS_CACHE` | Local model cache directory |
| `SYNARMO_CONTEXT_WINDOW` | Context window passed to llama.cpp as `n_ctx`; the local tuning default is `4096` |
| `SYNARMO_N_GPU_LAYERS` | Number of model layers to offload; `0` is CPU-only, `-1` asks llama.cpp to offload all possible layers |
| `SYNARMO_LLAMA_VERBOSE` | Enables native llama.cpp load/performance logs, including generation tokens/sec |
| `SYNARMO_TEMPERATURE` | Starter-token sampling temperature for the one-token autocomplete probe |
| `SYNARMO_TOP_P` | Starter-token nucleus sampling value for the one-token autocomplete probe |
| `SYNARMO_CONTINUATION_TEMPERATURE` | Autoregressive continuation sampling temperature for multi-word suggestions |
| `SYNARMO_CONTINUATION_TOP_P` | Autoregressive continuation nucleus sampling value |
| `SYNARMO_CONTINUATION_TOP_K` | Advanced continuation top-k guardrail; default is `20`, and `0` disables the hard top-k cap |
| `SYNARMO_PHRASE_LOGPROBS` | `0` for faster starter-token scoring; `1` to request continuation logprobs and compute phrase-level scores with extra latency |
| `SYNARMO_LOGPROB_POOL` | Number of top next-token log probabilities requested for starter selection |

The autocomplete prompt is structured for prefix reuse: fixed instructions
first, stable context second, and the changing typed message last. In the
current embedded `llama-cpp-python` backend there is no per-request
`cache_prompt` field; prefix-match reuse is handled inside the Python binding
when consecutive prompts share leading tokens.

### Autocomplete Generation Flow

The llama.cpp autocomplete path uses two sampling phases:

1. Starter probe: Synarmo asks llama.cpp for one generated token with
   `logprobs` enabled. It sorts the returned next-token alternatives, removes
   duplicate first-word starters, and keeps up to the configured suggestion
   count.
2. Autoregressive continuation: Synarmo appends each selected starter token to
   the prompt and generates future tokens for the multi-word candidate using
   continuation temperature/top-p and the advanced continuation top-k guardrail.
   Setting continuation temperature to `0` makes this phase greedy.

Displayed probabilities default to starter-token scores for live typing speed.
When `SYNARMO_PHRASE_LOGPROBS=1`, Synarmo requests continuation logprobs and
computes phrase-level scores by averaging the logprobs for the tokens that
remain visible after the word limit is applied, excluding pure formatting
punctuation while keeping meaningful `!` and `?` tokens in the score.

### Service Layer

| Component | Role |
| --- | --- |
| FastAPI app | Local REST, WebSocket, and UI service |
| Pydantic request/response models | Validate API payloads and shape responses |
| Jinja2 templates | Render the browser UI |
| Static file serving | Serve UI CSS and JavaScript |
| Uvicorn | ASGI server used by `synarmo serve` |

| Endpoint | Role |
| --- | --- |
| `GET /health` | Service health and model status |
| `POST /suggest` | Generate suggestions over REST |
| `POST /evaluate/autocomplete` | Evaluate auto-suggest candidates |
| `WebSocket /ws/suggest` | Real-time suggestion channel |
| `GET /ui` | Browser-based UI |
| `GET /docs` | FastAPI-generated API documentation |

### Frontend

| Component | Role |
| --- | --- |
| HTML templates | Browser UI structure rendered by Jinja2 |
| CSS assets | Local UI styling |
| JavaScript assets | Browser-side API calls, parameter controls, and rendering |
| `/ui` page | Interface for testing context and auto-suggest parameters |

### Interfaces

| Interface | Role |
| --- | --- |
| Python API | Embed suggestions in Python applications |
| Service mode | Run Synarmo as a local server for REST, WebSocket, and browser UI clients |
| CLI | Run one-off suggestions, compose loop, or local service |
| Configuration | `.env`, profile settings, and runtime configuration updates |

**Python API**
```python
from synarmo import SynarmoEngine

engine = SynarmoEngine.load(backend="llama-cpp")
suggestions = engine.suggest("I want to", context="At home")
```

## Performance Principles

- Load the model once and keep it warm.
- Use `SYNARMO_N_GPU_LAYERS=-1` when the installed llama.cpp runtime supports
  Metal/CUDA GPU offload; use `0` for portable CPU-only operation.
- Use `SYNARMO_LLAMA_VERBOSE=1` temporarily to inspect native llama.cpp
  throughput, KV cache, and buffer diagnostics.
- Keep the prompt short and purpose-built.
- Return a small set of short phrase continuations; the default is three.
- Prefer WebSocket for live typing.
- Keep ranking cheap and deterministic.
- Separate latency-sensitive suggestion logic from admin/config APIs.

## iPhone Plan

The iPhone app should not embed this Python package directly. Instead, it should
reuse the same architecture:

- Swift model backend using Core ML, llama.cpp mobile, or MLX where appropriate
- Swift equivalents of memory, context assembly, prompt building, and ranking
- same request/response schema as the local service
- export/import user profiles so desktop training and mobile use can share data

The Python package remains the reference implementation and evaluation harness.
