# Synarmo Architecture

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

- `llama-cpp`: GGUF backend through `llama_cpp.Llama`
- `mock`: deterministic test backend for API, service, UI, and CI wiring checks

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
| `MockBackend` | Deterministic test backend for API, service, UI, and CI wiring checks |
| `ContextAssembler` | Builds conversation context from user memory |
| `UserMemory` | Manages user profiles, preferences, and conversation history |
| `PromptBuilder` | Constructs prompts for the model |
| `SuggestionRanker` | Ranks and filters generated suggestions |
| `SynarmoConfig` | Configuration management with environment variable support |

| Infrastructure Component | Role |
| --- | --- |
| llama-cpp-python | Local GGUF model inference runtime |
| huggingface-hub | Model downloading and caching for configured Hugging Face repos |
| Core ML | Future iOS model runtime option |
| MLX | Future Apple Silicon experiment runtime option |

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
| `POST /evaluate/autocomplete` | Evaluate autocomplete candidates |
| `WebSocket /ws/suggest` | Real-time suggestion channel |
| `GET /ui` | Browser-based UI |
| `GET /docs` | FastAPI-generated API documentation |

### Frontend

| Component | Role |
| --- | --- |
| HTML templates | Browser UI structure rendered by Jinja2 |
| CSS assets | Local UI styling |
| JavaScript assets | Browser-side API calls, parameter controls, and rendering |
| `/ui` page | Interface for testing context and autocomplete parameters |

### Interfaces

| Interface | Role |
| --- | --- |
| Python API | Embed suggestions in Python applications |
| Local REST service | Call Synarmo from desktop, web, keyboard, or mobile clients |
| WebSocket service | Keep a live local suggestion channel open while a user types |
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
