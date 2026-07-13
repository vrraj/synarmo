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
    context_window: int = field(default_factory=configured_context_window)
    style_adaptation: bool = True
    temperature: float = field(default_factory=configured_temperature)
    top_p: float = field(default_factory=configured_top_p)
    continuation_temperature: float = field(default_factory=configured_continuation_temperature)
    continuation_top_p: float = field(default_factory=configured_continuation_top_p)
    continuation_top_k: int = field(default_factory=configured_continuation_top_k)
    phrase_logprobs: bool = field(default_factory=configured_phrase_logprobs)
    max_tokens: int = 5
    max_suggestion_words: int = 4
    logprob_pool: int = field(default_factory=configured_logprob_pool)
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
| `context_window` | `int` | 2048 unless `SYNARMO_CONTEXT_WINDOW` is set | Context window size in tokens (min 128). Local tuning uses `4096`. |
| `style_adaptation` | `bool` | True | Whether to adapt to user style from memory |
| `temperature` | `float` | 0.25 unless `SYNARMO_TEMPERATURE` is set | First-word probe temperature for API/package calls. For the logprob-based starter flow, pass `0.0` for deterministic starter ranking. |
| `top_p` | `float` | 0.95 unless `SYNARMO_TOP_P` is set | First-word probe Top P for API/package calls. For the logprob-based starter flow, pass `1.0` so starter candidates come from the raw logprob table. |
| `continuation_temperature` | `float` | 0.5 unless `SYNARMO_CONTINUATION_TEMPERATURE` is set | Phrase continuation temperature (0.0-2.0) |
| `continuation_top_p` | `float` | 0.9 unless `SYNARMO_CONTINUATION_TOP_P` is set | Phrase continuation nucleus sampling threshold |
| `continuation_top_k` | `int` | 20 unless `SYNARMO_CONTINUATION_TOP_K` is set | Phrase continuation top-k guardrail; `0` disables |
| `phrase_logprobs` | `bool` | false unless `SYNARMO_PHRASE_LOGPROBS=1` | Enables phrase-level logprob scoring for visible tokens; adds latency |
| `max_tokens` | `int` | 5 | Maximum tokens to generate (1-128) |
| `max_suggestion_words` | `int` | 4 | Maximum words per suggestion (1-20) |
| `logprob_pool` | `int` | 24 unless `SYNARMO_LOGPROB_POOL` is set | Number of first-word next-token logprobs to inspect |
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
    temperature=0.0,
    top_p=1.0,
    continuation_temperature=0.5,
    continuation_top_p=0.9,
    logprob_pool=24,
)

# Load with mock backend for no-model wiring checks
mock_engine = SynarmoEngine.load(backend="mock")
```

When `SYNARMO_MODEL_REPO_ID` and `SYNARMO_MODEL` are configured in `.env`, the
first llama.cpp load checks `LOCAL_MODELS_CACHE` and downloads the GGUF file if
it is missing. That first download can take some time. If `model_path` is
passed directly, that local GGUF file must already exist.

### `suggest()`

Generate suggestions for the given text. Request-level overrides can be passed
without mutating the engine's default configuration.

```python
def suggest(
    self,
    text: str,
    context: str | None = None,
    *,
    max_suggestions: int | None = None,
    max_tokens: int | None = None,
    max_words: int | None = None,
    temperature: float | None = None,
    top_p: float | None = None,
    continuation_temperature: float | None = None,
    continuation_top_p: float | None = None,
    continuation_top_k: int | None = None,
    phrase_logprobs: bool | None = None,
    logprob_pool: int | None = None,
) -> list[Suggestion]
```

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `text` | `str` | ✅ | Current text to complete |
| `context` | `str | None` | ❌ | Optional conversation or scene context |
| `max_suggestions` | `int | None` | ❌ | Override the number of suggestions (falls back to config) |
| `max_tokens` | `int | None` | ❌ | Override maximum generation tokens |
| `max_words` | `int | None` | ❌ | Override maximum visible words per suggestion |
| `temperature` | `float | None` | ❌ | Override starter probe temperature |
| `top_p` | `float | None` | ❌ | Override starter probe Top P |
| `continuation_temperature` | `float | None` | ❌ | Override continuation temperature |
| `continuation_top_p` | `float | None` | ❌ | Override continuation Top P |
| `continuation_top_k` | `int | None` | ❌ | Override continuation Top K guardrail |
| `phrase_logprobs` | `bool | None` | ❌ | Override phrase logprob scoring toggle |
| `logprob_pool` | `int | None` | ❌ | Override number of next-token logprobs to request |

**Returns:** `list[Suggestion]` - List of ranked suggestions

**Example:**

```python
from synarmo import SynarmoEngine

engine = SynarmoEngine.load(
    backend="llama-cpp",
    temperature=0.0,
    top_p=1.0,
    continuation_temperature=0.5,
    continuation_top_p=0.9,
    logprob_pool=24,
)
suggestions = engine.suggest(
    text="I want to",
    context="At home, asking for help"
)

for suggestion in suggestions:
    print(f"{suggestion.text} (score: {suggestion.score})")
```

### `evaluate_autocomplete()`

Run `suggest()` for multiple contexts while surfacing the assembled prompt and
ranked candidates. This compatibility adapter keeps the public API stable while
ensuring every entry point (CLI, service, browser UI, Python API) now shares the
same prediction path. The `logprob` field mirrors the per-suggestion score
returned by the ranker; `top_tokens` will be empty unless you call a backend's
`evaluate_autocomplete()` directly.

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
    continuation_temperature: float | None = None,
    continuation_top_p: float | None = None,
    continuation_top_k: int | None = None,
    phrase_logprobs: bool | None = None,
    logprob_pool: int = 24,
) -> list[AutocompleteEvaluation]
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `text` | `str` | - | Current text to complete |
| `contexts` | `list[str]` | - | List of context strings to evaluate |
| `choices` | `int` | 3 | Number of suggestions to return |
| `max_tokens` | `int` | 5 | Maximum tokens per suggestion |
| `max_words` | `int` | 1 | Maximum words per suggestion |
| `temperature` | `float` | 0.5 | First-word probe temperature. For logprob-ranked starter branches, use `0.0`. |
| `top_p` | `float` | 0.95 | First-word probe Top P. For logprob-ranked starter branches, use `1.0`. |
| `continuation_temperature` | `float | None` | None | Phrase continuation temperature; `None` uses engine config |
| `continuation_top_p` | `float | None` | None | Phrase continuation Top P; `None` uses engine config |
| `continuation_top_k` | `int | None` | None | Phrase continuation Top K; `None` uses engine config |
| `phrase_logprobs` | `bool | None` | None | Enables phrase-level logprob scoring; `None` uses engine config |
| `logprob_pool` | `int` | 24 | Number of first-word next-token logprobs to inspect |

**Returns:** `list[AutocompleteEvaluation]` - Detailed auto-suggest evaluation results

**Example:**

```python
from synarmo import SynarmoEngine

engine = SynarmoEngine.load(backend="llama-cpp")
evaluations = engine.evaluate_autocomplete(
    text="I want to",
    contexts=["At home", "At work", "With friends"],
    choices=3,
    temperature=0.0,
    top_p=1.0,
    continuation_temperature=0.5,
    continuation_top_p=0.9,
    logprob_pool=24,
)

for eval in evaluations:
    print(f"Context: {eval.context}")
    for candidate in eval.candidates:
        print(f"  {candidate.text} (score: {candidate.logprob})")
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
    temperature=0.0,
    top_p=1.0,
    continuation_temperature=0.5,
    continuation_top_p=0.9,
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
    temperature=0.0,
    top_p=1.0,
    continuation_temperature=0.5,
    continuation_top_p=0.9,
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

One-shot prediction function (loads engine on first call). Any keyword arguments
recognized by `SynarmoEngine.suggest()` (e.g., `max_suggestions`, `max_tokens`,
`max_words`, sampling controls, `phrase_logprobs`, `logprob_pool`) can now be
passed directly and apply only to that request. The helper also accepts the
legacy `max_suggestion_words` name and maps it to `max_words` for convenience.

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
    temperature=0.0,
    top_p=1.0,
    continuation_temperature=0.5,
    continuation_top_p=0.9,
    logprob_pool=24,
)
```

### `suggest()`

Alias for `predict()` with the same per-request override behavior and
`max_suggestion_words` compatibility alias.

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
SYNARMO_TEMPERATURE=0.0
SYNARMO_TOP_P=1.0
SYNARMO_CONTINUATION_TEMPERATURE=0.5
SYNARMO_CONTINUATION_TOP_P=0.9
SYNARMO_LOGPROB_POOL=24
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
    temperature=0.0,
    top_p=1.0,
    continuation_temperature=0.5,
    continuation_top_p=0.9,
    logprob_pool=24,
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
verify real prediction quality.

### 4. One-Shot Prediction

```python
import synarmo

suggestions = synarmo.predict(
    text="hello",
    context="greeting",
    backend="llama-cpp",
    max_suggestions=3,
    temperature=0.0,
    top_p=1.0,
    continuation_temperature=0.5,
    continuation_top_p=0.9,
    logprob_pool=24,
)
```

### 5. Custom Configuration

```python
from synarmo import SynarmoEngine

engine = SynarmoEngine.load(
    backend="llama-cpp",
    max_suggestions=5,
    max_suggestion_words=3,
    temperature=0.0,
    top_p=1.0,
    continuation_temperature=0.5,
    continuation_top_p=0.9,
    logprob_pool=24,
    style_adaptation=True,
)
```

### 6. Runtime Configuration Update

```python
from synarmo import SynarmoEngine

engine = SynarmoEngine.load(backend="llama-cpp")
engine.configure(
    max_suggestions=5,
    temperature=0.0,
    top_p=1.0,
    continuation_temperature=0.5,
    continuation_top_p=0.9,
)
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
    temperature=0.0,
    top_p=1.0,
    continuation_temperature=0.5,
    continuation_top_p=0.9,
    logprob_pool=24,
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
| `temperature` | ✅ Stable | First-word probe temperature (0.0-2.0); use `0.0` for logprob-ranked starters |
| `top_p` | ✅ Stable | First-word probe Top P; use `1.0` for logprob-ranked starters |
| `continuation_temperature` | ✅ Stable | Phrase continuation temperature (0.0-2.0) |
| `continuation_top_p` | ✅ Stable | Phrase continuation nucleus sampling |
| `continuation_top_k` | ✅ Stable | Phrase continuation top-k guardrail |
| `logprob_pool` | ✅ Stable | Number of first-word logprob candidates to inspect |
| `max_tokens` | ✅ Stable | Maximum tokens (1-128) |
| `context_window` | ✅ Stable | Context window size |
| `style_adaptation` | ✅ Stable | Style adaptation toggle |

**Legend:**
- ✅ **Stable**: Guaranteed interface, won't change
