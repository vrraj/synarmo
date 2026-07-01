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

Initial backends:

- `mock`: deterministic backend for tests and API development
- `llama-cpp`: GGUF backend through `llama_cpp.Llama`

Future backends:

- Core ML for iPhone
- MLX for Apple Silicon experiments
- remote backend for evaluation only

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
