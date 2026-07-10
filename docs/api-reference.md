---
layout: default
title: "API Reference | Synarmo"
description: "Complete API documentation for SynarmoEngine, SynarmoConfig, and prediction APIs."
---

# API Reference

This document provides the complete API reference for the Synarmo library, including class constructors, method signatures, parameter details, and common usage patterns.

> **New here?** Start with the project overview on the home page: **[Synarmo docs home](https://vrraj.github.io/synarmo/)**.
>
> **Source + releases:** GitHub repo and PyPI package are linked from the home page.

## Table of Contents

- [Core Classes](#core-classes)
- [SynarmoEngine API](#synarmoengine-api)
- [Configuration API](#configuration-api)
- [Suggestion API](#suggestion-api)
- [Convenience Functions](#convenience-functions)
- [Common Usage Patterns](#common-usage-patterns)

---

## Core Classes

### `SynarmoEngine`

Main prediction engine for generating text suggestions.

```python
class SynarmoEngine:
    def __init__(
        self,
        config: SynarmoConfig,
        backend: ModelBackend,
        memory: UserMemory,
    ) -> None
```

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `config` | `SynarmoConfig` | Runtime configuration object |
| `backend` | `ModelBackend` | Model backend instance (mock or llama-cpp) |
| `memory` | `UserMemory` | User profile and memory data |

### `SynarmoConfig`

Runtime configuration for the Synarmo engine.

```python
@dataclass(slots=True)
class SynarmoConfig:
    backend: BackendName = "mock"
    model_path: Path | None = None
    model_repo_id: str | None = None
    model_filename: str | None = None
    models_cache_dir: Path = field(default_factory=configured_models_cache)
    profile: str = "default"
    max_suggestions: int = field(default_factory=configured_max_suggestions)
    max_latency_ms: int = 100
    context_window: int = 2048
    style_adaptation: bool = True
    temperature: float = 0.25
    top_p: float = 0.95
    max_tokens: int = 32
    max_suggestion_words: int = 4
    stop: list[str] = field(default_factory=lambda: ["\n\n"])
    profiles_dir: Path = Path("profiles")
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `backend` | `BackendName` | "mock" | Model backend to use ("mock" or "llama-cpp") |
| `model_path` | `Path | None` | None | Path to local GGUF model file |
| `model_repo_id` | `str | None` | None | Hugging Face repo ID for auto-download |
| `model_filename` | `str | None` | None | Model filename in repo or cache |
| `models_cache_dir` | `Path` | ~/models/synarmo | Directory for cached models |
| `profile` | `str` | "default" | User profile name |
| `max_suggestions` | `int` | 3 | Maximum number of suggestions to return (1-10) |
| `max_latency_ms` | `int` | 100 | Target maximum latency in milliseconds |
| `context_window` | `int` | 2048 | Context window size in tokens (min 128) |
| `style_adaptation` | `bool` | True | Whether to adapt to user style from memory |
| `temperature` | `float` | 0.25 | Sampling temperature (0.0-2.0) |
| `top_p` | `float` | 0.95 | Nucleus sampling threshold (greater than 0.0 and up to 1.0) |
| `max_tokens` | `int` | 32 | Maximum tokens to generate (1-128) |
| `max_suggestion_words` | `int` | 4 | Maximum words per suggestion (1-20) |
| `stop` | `list[str]` | ["\n\n"] | Stop sequences for generation |
| `profiles_dir` | `Path` | "profiles" | Directory for user profiles |

### `Suggestion`

A single text suggestion with scoring.

```python
@dataclass(frozen=True, slots=True)
class Suggestion:
    text: str
    score: float
    source: str = "model"
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `text` | `str` | - | Suggested text completion |
| `score` | `float` | - | Confidence score (0.0-1.0) |
| `source` | `str` | "model" | Source of the suggestion |

---

## SynarmoEngine API

### `load()`

Load and initialize a SynarmoEngine instance.

```python
@classmethod
def load(
    cls,
    *,
    profile: str = "default",
    backend: BackendName = "mock",
    model_path: str | Path | None = None,
    profiles_dir: str | Path = "profiles",
    **overrides: object,
) -> "SynarmoEngine"
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `profile` | `str` | "default" | User profile name |
| `backend` | `BackendName` | "mock" | Model backend ("mock" or "llama-cpp") |
| `model_path` | `str | Path | None` | None | Optional path to local GGUF model |
| `profiles_dir` | `str | Path` | "profiles" | Directory for user profiles |
| `**overrides` | `object` | - | Additional config overrides |

**Returns:** `SynarmoEngine` - Initialized engine instance

**Example:**

```python
from synarmo import SynarmoEngine

# Load with llama-cpp backend using .env model configuration
engine = SynarmoEngine.load(
    backend="llama-cpp",
    profile="default",
    max_suggestions=3,
    temperature=0.25,
)

# Load with mock backend for no-model wiring checks
mock_engine = SynarmoEngine.load(backend="mock")
```

When `SYNARMO_MODEL_REPO_ID` and `SYNARMO_MODEL` are configured in `.env`, the
first llama.cpp load checks `LOCAL_MODELS_CACHE` and downloads the GGUF file if
it is missing. That first download can take some time. If `model_path` is
passed directly, that local GGUF file must already exist.

### `suggest()`

Generate suggestions for the given text.

```python
def suggest(self, text: str, context: str | None = None) -> list[Suggestion]
```

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `text` | `str` | ✅ | Current text to complete |
| `context` | `str | None` | ❌ | Optional conversation or scene context |

**Returns:** `list[Suggestion]` - List of ranked suggestions

**Example:**

```python
from synarmo import SynarmoEngine

engine = SynarmoEngine.load(backend="llama-cpp")
suggestions = engine.suggest(
    text="I want to",
    context="At home, asking for help"
)

for suggestion in suggestions:
    print(f"{suggestion.text} (score: {suggestion.score})")
```

### `evaluate_autocomplete()`

Evaluate autocomplete with detailed token-level information. The llama-cpp backend returns model logprobs; the mock backend returns deterministic fallback candidates for tests and wiring checks.

```python
def evaluate_autocomplete(
    self,
    *,
    text: str,
    contexts: list[str],
    choices: int = 3,
    max_tokens: int = 5,
    max_words: int = 1,
    temperature: float = 0.5,
    top_p: float = 0.95,
    logprob_pool: int = 24,
) -> list[AutocompleteEvaluation]
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `text` | `str` | - | Current text to complete |
| `contexts` | `list[str]` | - | List of context strings to evaluate |
| `choices` | `int` | 3 | Number of suggestions to return |
| `max_tokens` | `int` | 10 | Maximum tokens per suggestion |
| `max_words` | `int` | 1 | Maximum words per suggestion |
| `temperature` | `float` | 0.5 | Sampling temperature |
| `top_p` | `float` | 0.95 | Nucleus sampling threshold |
| `logprob_pool` | `int` | 24 | Number of logprob tokens to inspect |

**Returns:** `list[AutocompleteEvaluation]` - Detailed evaluation results

**Example:**

```python
from synarmo import SynarmoEngine

engine = SynarmoEngine.load(backend="llama-cpp")
evaluations = engine.evaluate_autocomplete(
    text="I want to",
    contexts=["At home", "At work", "With friends"],
    choices=3,
    temperature=0.5,
)

for eval in evaluations:
    print(f"Context: {eval.context}")
    for candidate in eval.candidates:
        print(f"  {candidate.text} (logprob: {candidate.logprob})")
```

### `configure()`

Update engine configuration at runtime.

```python
def configure(self, **updates: object) -> None
```

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `**updates` | `object` | Configuration key-value pairs to update |

**Example:**

```python
engine.configure(
    max_suggestions=5,
    temperature=0.3,
    max_suggestion_words=3,
)
```

### `remember_phrase()`

Add a phrase to user memory for style adaptation.

```python
def remember_phrase(self, phrase: str) -> None
```

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `phrase` | `str` | Phrase to remember |

**Example:**

```python
engine.remember_phrase("let's grab coffee")
engine.remember_phrase("see you later")
```

---

## Configuration API

### `SynarmoConfig.copy_with()`

Create a copy of the configuration with updated values.

```python
def copy_with(self, **updates: object) -> "SynarmoConfig"
```

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `**updates` | `object` | Configuration key-value pairs to update |

**Returns:** `SynarmoConfig` - New configuration instance

**Example:**

```python
from synarmo import SynarmoConfig

config = SynarmoConfig()
new_config = config.copy_with(
    max_suggestions=5,
    temperature=0.3,
    backend="llama-cpp"
)
```

### `SynarmoConfig.resolved_profile_dir()`

Get the resolved absolute path for the profile directory.

```python
def resolved_profile_dir(self) -> Path
```

**Returns:** `Path` - Absolute path to profile directory

**Example:**

```python
config = SynarmoConfig(profile="myuser")
profile_dir = config.resolved_profile_dir()
print(profile_dir)  # /path/to/profiles/myuser
```

---

## Suggestion API

### `SuggestionRanker`

Internal class for ranking and filtering suggestions.

```python
class SuggestionRanker:
    def rank(
        self,
        raw_text: str,
        *,
        current_text: str,
        max_suggestions: int,
        max_words: int = 4,
    ) -> list[Suggestion]
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `raw_text` | `str` | - | Raw model output text |
| `current_text` | `str` | - | Current user text |
| `max_suggestions` | `int` | - | Maximum suggestions to return |
| `max_words` | `int` | 4 | Maximum words per suggestion |

**Returns:** `list[Suggestion]` - Ranked and filtered suggestions

---

## Convenience Functions

### `predict()`

One-shot prediction function (loads engine on first call).

```python
def predict(
    text: str,
    context: str | None = None,
    user_profile: str = "default",
    **load_options: object,
) -> list[Suggestion]
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `text` | `str` | - | Current text to complete |
| `context` | `str | None` | None | Optional context |
| `user_profile` | `str` | "default" | User profile name |
| `**load_options` | `object` | - | Engine load options |

**Returns:** `list[Suggestion]` - List of suggestions

**Example:**

```python
import synarmo

suggestions = synarmo.predict(
    text="I want to",
    context="At home",
    backend="llama-cpp",
    max_suggestions=3,
)
```

### `suggest()`

Alias for `predict()` function.

```python
def suggest(
    text: str,
    context: str | None = None,
    user_profile: str = "default",
    **load_options: object,
) -> list[Suggestion]
```

**Example:**

```python
import synarmo

suggestions = synarmo.suggest(
    text="hello",
    context="greeting",
    backend="mock",
)
```

---

## Common Usage Patterns

### 1. Prediction with Configured GGUF Model

```python
from synarmo import SynarmoEngine

engine = SynarmoEngine.load(backend="llama-cpp")
suggestions = engine.suggest(
    text="I want to",
    context="At home, asking for help",
)
print([s.text for s in suggestions])
```

This uses the model configured in `.env`:

```dotenv
LOCAL_MODELS_CACHE=~/models/synarmo
SYNARMO_MAX_SUGGESTIONS=3
SYNARMO_MODEL_REPO_ID=QuantFactory/Llama-3.2-1B-GGUF
SYNARMO_MODEL=Llama-3.2-1B.Q4_K_M.gguf
```

If the GGUF file is missing, the first load downloads it and can take some
time. Later loads reuse the cached file.

### 2. Prediction with Direct Local GGUF Path

```python
from synarmo import SynarmoEngine

engine = SynarmoEngine.load(
    backend="llama-cpp",
    model_path="~/models/synarmo/Llama-3.2-1B.Q4_K_M.gguf",
)
suggestions = engine.suggest(
    text="I want to",
    context="At home, asking for help"
)
```

When passing `model_path`, Synarmo expects that local file to already exist.

### 3. Mock Backend Check

```python
from synarmo import SynarmoEngine

engine = SynarmoEngine.load(backend="mock")
suggestions = engine.suggest("I want to")
print([s.text for s in suggestions])
```

The mock backend does not require a model. It returns canned deterministic
suggestions for package, CLI, service, UI, and CI wiring checks; it does not
test real prediction quality.

### 4. One-Shot Prediction

```python
import synarmo

suggestions = synarmo.predict(
    text="hello",
    context="greeting",
    backend="llama-cpp",
    max_suggestions=3,
    temperature=0.25,
)
```

### 5. Custom Configuration

```python
from synarmo import SynarmoEngine

engine = SynarmoEngine.load(
    backend="llama-cpp",
    max_suggestions=5,
    max_suggestion_words=3,
    temperature=0.3,
    top_p=0.90,
    style_adaptation=True,
)
```

### 6. Runtime Configuration Update

```python
from synarmo import SynarmoEngine

engine = SynarmoEngine.load(backend="llama-cpp")
engine.configure(max_suggestions=5, temperature=0.3)
```

### 7. User Profile and Memory

```python
from synarmo import SynarmoEngine

engine = SynarmoEngine.load(
    backend="llama-cpp",
    profile="myuser",
)

# Remember phrases for style adaptation
engine.remember_phrase("let's grab coffee")
engine.remember_phrase("see you later")

# Suggestions will now adapt to this style
suggestions = engine.suggest("I want to")
```

### 8. Multiple Contexts Evaluation

```python
from synarmo import SynarmoEngine

engine = SynarmoEngine.load(backend="llama-cpp")
evaluations = engine.evaluate_autocomplete(
    text="I want to",
    contexts=["At home", "At work", "With friends"],
    choices=3,
    temperature=0.5,
)

for eval in evaluations:
    print(f"\nContext: {eval.context}")
    for candidate in eval.candidates:
        print(f"  {candidate.text} (logprob: {candidate.logprob})")
```

### 9. Integration with FastAPI

```python
from fastapi import FastAPI
from synarmo import SynarmoEngine

app = FastAPI()
engine = SynarmoEngine.load(backend="llama-cpp")

@app.post("/suggest")
async def get_suggestions(text: str, context: str = None):
    suggestions = engine.suggest(text=text, context=context)
    return {"suggestions": [s.text for s in suggestions]}
```

### 10. Integration with Flask

```python
from flask import Flask, request, jsonify
from synarmo import SynarmoEngine

app = Flask(__name__)
engine = SynarmoEngine.load(backend="llama-cpp")

@app.route("/suggest", methods=["POST"])
def suggest():
    data = request.json
    suggestions = engine.suggest(
        text=data.get("text"),
        context=data.get("context")
    )
    return jsonify({"suggestions": [s.text for s in suggestions]})
```

---

## Parameter Stability

### Stable Parameters

| Parameter | Stability | Notes |
|-----------|-----------|-------|
| `backend` | ✅ Stable | Model backend selection |
| `profile` | ✅ Stable | User profile name |
| `max_suggestions` | ✅ Stable | Maximum suggestions (1-10) |
| `max_suggestion_words` | ✅ Stable | Maximum words per suggestion (1-20) |
| `temperature` | ✅ Stable | Sampling temperature (0.0-2.0) |
| `top_p` | ✅ Stable | Nucleus sampling (greater than 0.0 and up to 1.0) |
| `max_tokens` | ✅ Stable | Maximum tokens (1-128) |
| `context_window` | ✅ Stable | Context window size |
| `style_adaptation` | ✅ Stable | Style adaptation toggle |

**Legend:**
- ✅ **Stable**: Guaranteed interface, won't change
