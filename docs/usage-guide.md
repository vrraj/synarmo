---
layout: default
title: "Usage Guide | Synarmo"
description: "Usage examples and patterns for synarmo package."
---

# Usage Guide

This guide provides practical usage examples and patterns for the Synarmo
auto-suggest engine.

> **New here?** Start with the project overview on the home page: **[Synarmo docs home](https://vrraj.github.io/synarmo/)**.
>
> **Source + releases:** GitHub repo and PyPI package are linked from the home page.

## Table of Contents

- [Quick Start](#quick-start)
- [How Suggestions Work](#how-suggestions-work)
- [Context Usage](#context-usage)
- [Configuration Patterns](#configuration-patterns)
- [User Profiles and Memory](#user-profiles-and-memory)
- [Runtime Configuration](#runtime-configuration)
- [One-Shot Prediction](#one-shot-prediction)
- [Model Configuration](#model-configuration)
- [CLI Usage](#cli-usage)
- [Service Mode](#service-mode)
- [Web UI](#web-ui)
- [Integration Examples](#integration-examples)
- [Verification Without a Model](#verification-without-a-model)
- [Common Use Cases](#common-use-cases)
- [Performance Tips](#performance-tips)

---

## Quick Start

### Prediction with Local GGUF Model

For real predictions, use the llama-cpp backend with a configured GGUF model:

```dotenv
LOCAL_MODELS_CACHE=~/models/synarmo
SYNARMO_MAX_SUGGESTIONS=3
SYNARMO_TEMPERATURE=0.25
SYNARMO_TOP_P=0.95
SYNARMO_CONTINUATION_TEMPERATURE=0.5
SYNARMO_CONTINUATION_TOP_P=0.9
SYNARMO_CONTINUATION_TOP_K=20
SYNARMO_MODEL_REPO_ID=QuantFactory/Llama-3.2-1B-GGUF
SYNARMO_MODEL=Llama-3.2-1B.Q4_K_M.gguf
```

The first load checks `LOCAL_MODELS_CACHE` and downloads `SYNARMO_MODEL` from
`SYNARMO_MODEL_REPO_ID` if the GGUF file is missing. That download can take
some time.

```python
from synarmo import SynarmoEngine

engine = SynarmoEngine.load(backend="llama-cpp")
suggestions = engine.suggest(
    text="I want to",
    context="At home, asking for help",
)
print([s.text for s in suggestions])
```

### Mock Backend Check

The mock backend does not require a model and is useful for testing package,
CLI, service, or UI wiring. It returns canned deterministic suggestions, not
real predictions:

```python
from synarmo import SynarmoEngine

engine = SynarmoEngine.load(backend="mock")
suggestions = engine.suggest("I want to")
print([s.text for s in suggestions])
```

## How Suggestions Work

Synarmo uses the same basic flow from Python, the CLI, the local service, and
the browser UI:

```text
User types text
  -> Synarmo API
  -> Context assembly
  -> Prompt building
  -> Model generation
  -> Suggestion ranking
  -> Short suggestions
```

The engine combines the current typed text, optional context, and profile
memory when style adaptation is enabled. It builds a prompt for short
continuations, sends that prompt to the selected backend, then cleans and ranks
the returned candidates.

The ranker removes duplicates, trims punctuation, limits suggestion length,
filters instruction echoes, and returns up to the configured number of
suggestions. The default is three suggestions, with each suggestion usually
limited to one to four words.

With the llama.cpp backend, autocomplete uses two sampling phases. First,
Synarmo runs a one-token starter probe with `logprobs` enabled, ranks likely
next-token starters, and removes duplicate first-word starters. Then it expands
each selected starter with an autoregressive continuation pass for multi-word
suggestions. `temperature` and `top_p` tune the starter probe;
`continuation_temperature` and `continuation_top_p` tune the future tokens in
the continuation. Setting `continuation_temperature=0` makes continuation
greedy, while higher values make suggestions more varied. Advanced users can
also set `continuation_top_k` or `SYNARMO_CONTINUATION_TOP_K`; the default is
`20`.

Candidate percentages are phrase-level scores. Synarmo averages the logprobs
for the tokens that remain visible after the word limit is applied, excluding
pure formatting punctuation while keeping meaningful `!` and `?` tokens.

## Context Usage

### Simple Context

Provide a simple context string to guide suggestions:

```python
from synarmo import SynarmoEngine

engine = SynarmoEngine.load(backend="llama-cpp")

# Greeting context
suggestions = engine.suggest(
    text="hello",
    context="greeting a friend"
)

# Work context
suggestions = engine.suggest(
    text="I need to",
    context="at work, sending an email"
)
```

### Multiple Contexts for Evaluation

Evaluate suggestions across different contexts:

```python
from synarmo import SynarmoEngine

engine = SynarmoEngine.load(backend="llama-cpp")

evaluations = engine.evaluate_autocomplete(
    text="I want to",
    contexts=["At home", "At work", "With friends"],
    choices=3,
    temperature=0.5,
    top_p=0.95,
    continuation_temperature=0.5,
    continuation_top_p=0.9,
)

for eval in evaluations:
    print(f"\nContext: {eval.context}")
    for candidate in eval.candidates:
        print(f"  {candidate.text} (logprob: {candidate.logprob})")
```

## Configuration Patterns

### Custom Starter And Continuation Sampling

Adjust randomness and focus separately for starter-token selection and
autoregressive continuation:

```python
from synarmo import SynarmoEngine

# More predictable suggestions: focused starters and near-greedy continuation
engine = SynarmoEngine.load(
    backend="llama-cpp",
    temperature=0.1,
    top_p=0.90,
    continuation_temperature=0.0,
    continuation_top_p=0.9,
)

# More varied suggestions: diverse starters and more natural multi-word phrases
engine = SynarmoEngine.load(
    backend="llama-cpp",
    temperature=0.5,
    top_p=0.95,
    continuation_temperature=0.6,
    continuation_top_p=0.9,
)
```

For advanced tuning, `continuation_top_k` defaults to `20` and acts as a hard
sampling guardrail during continuation. Use `0` to leave llama.cpp unconstrained
by top-k.

### Adjust Suggestion Length

Control the length of suggestions:

```python
from synarmo import SynarmoEngine

# Short suggestions (1-2 words)
engine = SynarmoEngine.load(
    backend="llama-cpp",
    max_suggestion_words=2,
)

# Longer suggestions (up to 4 words)
engine = SynarmoEngine.load(
    backend="llama-cpp",
    max_suggestion_words=4,
)
```

### Number of Suggestions

Control how many suggestions are returned:

```python
from synarmo import SynarmoEngine

# Fewer suggestions
engine = SynarmoEngine.load(
    backend="llama-cpp",
    max_suggestions=3,
)

# More suggestions
engine = SynarmoEngine.load(
    backend="llama-cpp",
    max_suggestions=5,
)
```

## User Profiles and Memory

### Using User Profiles

Create and use different user profiles for personalized suggestions:

```python
from synarmo import SynarmoEngine

# Load with a specific profile
engine = SynarmoEngine.load(
    backend="llama-cpp",
    profile="myuser",
)

suggestions = engine.suggest("I want to")
```

### Remembering Phrases

Add phrases to user memory for style adaptation:

```python
from synarmo import SynarmoEngine

engine = SynarmoEngine.load(
    backend="llama-cpp",
    profile="myuser",
)

# Remember common phrases
engine.remember_phrase("let's grab coffee")
engine.remember_phrase("see you later")
engine.remember_phrase("how's it going")

# Future suggestions will adapt to this style
suggestions = engine.suggest("I want to")
```

### Style Adaptation Toggle

Enable or disable style adaptation:

```python
from synarmo import SynarmoEngine

# Style adaptation enabled (default)
engine = SynarmoEngine.load(
    backend="llama-cpp",
    style_adaptation=True,
)

# Style adaptation disabled
engine = SynarmoEngine.load(
    backend="llama-cpp",
    style_adaptation=False,
)
```

## Runtime Configuration

### Update Configuration at Runtime

Change configuration without reloading the engine:

```python
from synarmo import SynarmoEngine

engine = SynarmoEngine.load(backend="llama-cpp")

# Update configuration
engine.configure(
    max_suggestions=5,
    temperature=0.3,
    max_suggestion_words=3,
)

# Suggestions now use new configuration
suggestions = engine.suggest("I want to")
```

## One-Shot Prediction

### Using Convenience Functions

Use `predict()` or `suggest()` for one-off predictions:

```python
import synarmo

# One-shot prediction
suggestions = synarmo.predict(
    text="hello",
    context="greeting",
    backend="llama-cpp",
    max_suggestions=3,
)

# Alternative alias
suggestions = synarmo.suggest(
    text="hello",
    context="greeting",
    backend="llama-cpp",
)
```

## Model Configuration

### Using Environment Variables

Configure models via `.env` file:

```dotenv
# .env
LOCAL_MODELS_CACHE=~/models/synarmo
SYNARMO_MAX_SUGGESTIONS=3
SYNARMO_MODEL_REPO_ID=QuantFactory/Llama-3.2-1B-GGUF
SYNARMO_MODEL=Llama-3.2-1B.Q4_K_M.gguf
```

Then load without specifying model path:

```python
from synarmo import SynarmoEngine

engine = SynarmoEngine.load(backend="llama-cpp")
```

If the GGUF file is missing, the first load downloads it from Hugging Face and
can take some time. Later loads reuse the cached file.

### Using Local Model Path

Specify a local model path directly:

```python
from synarmo import SynarmoEngine

engine = SynarmoEngine.load(
    backend="llama-cpp",
    model_path="~/models/synarmo/Llama-3.2-1B.Q4_K_M.gguf",
)
```

### Using Absolute Path

Use an absolute path to the model:

```python
from synarmo import SynarmoEngine

engine = SynarmoEngine.load(
    backend="llama-cpp",
    model_path="/Users/raj/models/qwen2.5-1.5b-instruct-q4_k_m.gguf",
)
```

## CLI Usage

### Single Suggestion Request

Use the CLI for quick testing:

```bash
synarmo suggest "I want to" \
  --context "At home, asking for help" \
  --backend llama-cpp
```

### Compose Loop

Use the interactive compose loop:

```bash
synarmo compose "I want to" \
  --context "At home, asking for help" \
  --backend llama-cpp
```

This shows suggestions, lets you choose one, appends it to the text, and immediately predicts the next suggestions.

## Service Mode

### Start the Service

Service mode means running Synarmo as a local server instead of calling it
directly from Python. Use it when another process needs suggestions, such as a
desktop app, web app, keyboard, browser UI, or a client that wants REST or
WebSocket access. The service loads the selected backend once, keeps the model
warm, and exposes local endpoints from the same engine instance.

Start the local service:

```bash
synarmo serve --backend llama-cpp
```

The service defaults to `http://127.0.0.1:8765`. If `SYNARMO_MODEL_REPO_ID` is
configured and the GGUF file is missing, service startup downloads it before
`/health` is ready. That first download can take some time.

### Check Health

```bash
curl http://127.0.0.1:8765/health
```

### Use Service Endpoints

Once service mode is running, clients can call these local endpoints:

| Endpoint | What it does |
| --- | --- |
| `GET /health` | Confirms the service is ready and reports the active backend/model. |
| `POST /suggest` | Returns ranked suggestions for text and optional context. |
| `POST /evaluate/autocomplete` | Returns auto-suggest candidates and token scores for tuning. |
| `WebSocket /ws/suggest` | Accepts repeated suggestion requests over one live connection. |
| `GET /ui` | Opens the browser UI backed by the same service. |

Basic REST suggestion request:

```bash
curl -X POST http://127.0.0.1:8765/suggest \
  -H 'content-type: application/json' \
  -d '{"text":"I want to","context":"At home, asking for help"}'
```

Auto-suggest evaluation request:

```bash
curl -X POST http://127.0.0.1:8765/evaluate/autocomplete \
  -H 'content-type: application/json' \
  -d '{
    "text": "I want to",
    "contexts": ["At home, asking for help"],
    "choices": 3,
    "candidate_tokens": 5,
    "candidate_words": 2,
    "temperature": 0.5,
    "top_p": 0.95,
    "continuation_temperature": 0.5,
    "continuation_top_p": 0.9,
    "continuation_top_k": 20,
    "logprob_pool": 24
  }'
```

Connect to the WebSocket endpoint:

```text
ws://127.0.0.1:8765/ws/suggest
```

Send JSON messages:

```json
{"text": "I want to", "context": "At home, asking for help"}
```

## Web UI

### Access the Interactive UI

With the service running, open:

```text
http://127.0.0.1:8765/ui
```

From a source checkout, you can start the browser UX directly:

```bash
make ux
```

For real inference, run `make model-ensure` first if you want to download or
verify the configured GGUF model before starting the UI. `make ux` performs the
same model load when the service starts.

For a no-model wiring check, start it with the mock backend:

```bash
make ux-mock
```

Stop the background service with:

```bash
make stop
```

The UI lets you:
- Type the current message
- Provide conversation or scene context
- Change auto-suggest parameters (choices, tokens, words, first-word temperature/top-p, phrase temperature/top-p, logprob pool)
- Inspect how the service responds

### UI Parameters

| Parameter | Default | What it does |
| --- | ---: | --- |
| Choices | 3 | Number of suggestions to show |
| Tokens | 5 | Maximum generated tokens per suggestion |
| Words | 1 | Maximum words displayed per suggestion |
| First Word Temp | 0.25 | Controls randomness for the one-token first-word probe |
| First Word Top P | 0.95 | Nucleus sampling value passed to the one-token llama.cpp probe |
| Phrase Temp | 0.5 | Controls randomness during autoregressive phrase continuation |
| Phrase Top P | 0.9 | Nucleus sampling value used while expanding selected first words |
| Logprobs | 24 | Number of top next-token log probabilities to request from llama.cpp for starter selection. |
| Auto - Suggest on Spacebar | On | Automatically request suggestions after typing a space |

`SYNARMO_CONTINUATION_TOP_K` remains available as an advanced `.env`, Python,
and API setting, but it is intentionally hidden from the browser UI. Its default
is `20`.

## Integration Examples

### FastAPI Integration

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

### Flask Integration

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

### Async Integration

```python
import asyncio
from synarmo import SynarmoEngine

async def async_suggest(text: str, context: str = None):
    engine = SynarmoEngine.load(backend="llama-cpp")
    suggestions = engine.suggest(text=text, context=context)
    return [s.text for s in suggestions]

# Usage
suggestions = await async_suggest("I want to", "At home")
```

## Verification Without a Model

### Compile Check

Verify the package compiles without a model:

```bash
python3 -m compileall src tests
```

### Run Verification Specs

Run the verification specs (uses mock backend):

```bash
pip install -e ".[dev]"
PYTHONPATH=src pytest
```

### Mock Backend Verification

Use the mock backend for development and verification:

```python
from synarmo import SynarmoEngine

engine = SynarmoEngine.load(backend="mock")
suggestions = engine.suggest("I want to")
print([s.text for s in suggestions])
```

## Common Use Cases

### Messaging Application

```python
from synarmo import SynarmoEngine

engine = SynarmoEngine.load(backend="llama-cpp")

def get_suggestions_for_message(current_text: str, conversation_context: str):
    suggestions = engine.suggest(
        text=current_text,
        context=conversation_context
    )
    return [s.text for s in suggestions]
```

### Email Client

```python
from synarmo import SynarmoEngine

engine = SynarmoEngine.load(
    backend="llama-cpp",
    profile="email_user",
    max_suggestion_words=4,
)

def complete_email_subject(subject: str):
    suggestions = engine.suggest(
        text=subject,
        context="writing an email subject line"
    )
    return [s.text for s in suggestions]
```

### Assistive Typing

```python
from synarmo import SynarmoEngine

engine = SynarmoEngine.load(
    backend="llama-cpp",
    max_suggestion_words=2,
    temperature=0.1,
    continuation_temperature=0.0,  # Greedy continuation for steadier assistive typing
)

def get_typing_suggestions(current_text: str):
    suggestions = engine.suggest(text=current_text)
    return [s.text for s in suggestions]
```

## Performance Tips

### Keep Engine Warm

Load the engine once and reuse it:

```python
# Good: Load once
engine = SynarmoEngine.load(backend="llama-cpp")

for text in texts:
    suggestions = engine.suggest(text)

# Bad: Load for each request
for text in texts:
    engine = SynarmoEngine.load(backend="llama-cpp")  # Slow!
    suggestions = engine.suggest(text)
```

### Use Appropriate Context Window

Adjust context window based on your needs:

```python
# Short context for faster predictions
engine = SynarmoEngine.load(
    backend="llama-cpp",
    context_window=512,
)

# Longer context for more context-aware predictions
engine = SynarmoEngine.load(
    backend="llama-cpp",
    context_window=2048,
)
```

### Batch Similar Requests

Process similar requests together to benefit from caching:

```python
from synarmo import SynarmoEngine

engine = SynarmoEngine.load(backend="llama-cpp")

# Batch similar contexts
contexts = ["At home", "At work", "With friends"]
evaluations = engine.evaluate_autocomplete(
    text="I want to",
    contexts=contexts,
    choices=3,
)
```
