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

engine = SynarmoEngine.load(profile="user")
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

Future backends:

- Core ML for iPhone
- MLX for Apple Silicon experiments
- remote backend for evaluation only

## Technology Components

### Backend

**Core Python Package**
- `SynarmoEngine`: Main engine API for loading models and generating suggestions
- `ModelBackend`: Protocol for pluggable inference backends
  - `LlamaCppBackend`: GGUF model inference via llama-cpp-python
  - `MockBackend`: Deterministic test backend
- `ContextAssembler`: Builds conversation context from user memory
- `UserMemory`: Manages user profiles, preferences, and conversation history
- `PromptBuilder`: Constructs prompts for the model
- `SuggestionRanker`: Ranks and filters generated suggestions
- `SynarmoConfig`: Configuration management with environment variable support

**Model Backends**
- llama-cpp-python: Local GGUF model inference
- huggingface-hub: Model downloading and caching
- Future: Core ML (iOS), MLX (Apple Silicon)

### Service Layer

**FastAPI Application**
- REST API endpoints
- WebSocket support for real-time suggestions
- Static file serving for web UI
- Jinja2 templating for HTML responses
- Pydantic models for request/response validation

**API Endpoints**
- `GET /health`: Service health and model status
- `POST /suggest`: Generate suggestions (REST)
- `POST /evaluate/autocomplete`: Evaluate autocomplete quality
- `WebSocket /ws/suggest`: Real-time suggestion streaming
- `GET /ui`: Browser-based UI
- `GET /docs`: FastAPI auto-generated API documentation

### Frontend

**Web UI**
- HTML templates (Jinja2)
- Static assets (CSS, JavaScript)
- Browser-based interface for testing and demonstration
- WebSocket client for real-time suggestions

### Interfaces

**Python API**
```python
from synarmo import SynarmoEngine

engine = SynarmoEngine.load(backend="llama-cpp")
suggestions = engine.suggest("I want to", context="At home")
```

**Local Service**
- REST API over HTTP
- WebSocket for streaming
- Configurable host and port
- Background process support

**Configuration**
- Environment variables (.env file)
- Profile-based user settings
- Runtime configuration updates

## Performance Principles

- Load the model once and keep it warm.
- Keep the prompt short and purpose-built.
- Return three to five short phrase continuations.
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
