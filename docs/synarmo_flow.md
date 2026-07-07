# Synarmo Suggestion Flow

## Overview

This document explains how Synarmo generates suggestions when a user types text, using a top-down approach from the user interface to the model inference.

## Top-Level Flow

```
User types text
    ↓
Application UI (CLI, Web, Desktop, etc.)
    ↓
Synarmo API (Python or WebSocket)
    ↓
SynarmoEngine.suggest()
    ↓
Context Assembly → Prompt Building → Model Generation → Ranking
    ↓
Return suggestions to UI
```

## API Methods

### Python API

**SynarmoEngine.suggest()** (`src/synarmo/engine.py:71-122`)
- Main method for generating suggestions
- Parameters: `text: str`, `context: str | None = None`
- Returns: `list[Suggestion]` (each with `text` and `score`)

**SynarmoEngine.load()** (`src/synarmo/engine.py:42-65`)
- Class method to load and initialize the engine
- Parameters: `profile`, `backend`, `model_path`, `profiles_dir`, `**overrides`
- Returns: `SynarmoEngine` instance

**SynarmoEngine.configure()** (`src/synarmo/engine.py:67-69`)
- Runtime configuration updates
- Parameters: `**updates: object`

**SynarmoEngine.remember_phrase()** (`src/synarmo/engine.py:174-178`)
- Add a phrase to user memory
- Parameters: `phrase: str`

**SynarmoEngine.evaluate_autocomplete()** (`src/synarmo/engine.py:124-172`)
- Evaluation method for autocomplete testing
- Parameters: `text`, `contexts`, `choices`, `max_tokens`, `max_words`, `temperature`, `top_p`, `logprob_pool`
- Returns: `list[AutocompleteEvaluation]`

### Convenience Functions

**suggest()** (`src/synarmo/engine.py:193-202`)
- Global convenience function with cached engine
- Parameters: `text`, `context`, `user_profile`, `**load_options`
- Returns: `list[Suggestion]`

**predict()** (`src/synarmo/engine.py:184-190`)
- Alias for `suggest()`

### CLI API

**synarmo suggest** (`src/synarmo/cli.py:47-51`)
- Command-line interface for suggestions
- Arguments: `text`, `--context`, `--profile`, `--backend`, `--model-path`, `--max-suggestions`

**synarmo compose** (`src/synarmo/cli.py:53-56`)
- Interactive composition mode
- Arguments: `text`, `--context`, `--profile`, `--backend`, `--model-path`, `--max-suggestions`

**synarmo serve** (`src/synarmo/cli.py:58-67`)
- Start local REST/WebSocket service
- Arguments: `--host`, `--port`, `--profile`, `--backend`, `--model-path`, `--max-suggestions`

### Service API (FastAPI)

**POST /suggest** (`src/synarmo/service/app.py:70-76`)
- REST endpoint for suggestions
- Request: `{"text": str, "context": str | None}`
- Response: `{"suggestions": list[str], "scores": list[float]}`

**WebSocket /ws/suggest** (`src/synarmo/service/app.py:113-125`)
- WebSocket endpoint for real-time suggestions
- Message: `{"text": str, "context": str | None}`
- Response: `{"suggestions": list[str], "scores": list[float]}`

**GET /health** (`src/synarmo/service/app.py:59-68`)
- Health check endpoint
- Response: `{"status": str, "backend": str, "model": str}`

**GET /ui** (`src/synarmo/service/app.py:53-57`)
- Web UI endpoint
- Returns: HTML interface

**POST /evaluate/autocomplete** (`src/synarmo/service/app.py:78-111`)
- Evaluation endpoint for autocomplete testing
- Request: `{"text": str, "contexts": list[str], "choices": int, ...}`
- Response: `{"results": list[AutocompleteEvalItemResponse]}`

## Detailed Suggestion Flow

### 1. Entry Point

**CLI Example** (`src/synarmo/cli.py:49`)
```python
engine.suggest(text=args.text, context=args.context)
```

**Service Example** (`src/synarmo/service/app.py:72`)
```python
suggestions = engine.suggest(text=request.text, context=request.context)
```

### 2. Context Assembly

**ContextAssembler.assemble()** (`src/synarmo/context.py:12-23`)

The engine assembles context from:
- User memory (style summary, preferences, common phrases)
- Current context (optional conversation context)
- Current typed text

```python
assembled_context = self.context_assembler.assemble(
    text=text,
    context=context,
    memory=self.memory if self.config.style_adaptation else UserMemory(profile=self.config.profile),
)
```

Output format:
```
User style: {style_summary}
Known preferences: {preferences}
Current context: {context}
Current typed text: {text}
```

### 3. Prompt Construction

**PromptBuilder.build()** (`src/synarmo/prompts.py:5-43`)

The prompt builder creates a structured prompt with:
- System instructions for Synarmo
- Rules for suggestion generation (1-4 words, natural continuation, no answers)
- Examples of good continuations
- Assembled context from step 2

```python
prompt = self.prompt_builder.build(
    assembled_context=assembled_context,
    max_suggestions=generation_count,
)
```

### 4. Model Generation

**ModelBackend.generate()** (`src/synarmo/engine.py:84-91`)

The engine sends the prompt to the model backend:
- Calculates generation count (3x max_suggestions, capped at 10)
- Sets max_tokens based on generation count
- Applies temperature and stop tokens from config

```python
raw = self.backend.generate(
    prompt,
    GenerationOptions(
        max_tokens=generation_max_tokens,
        temperature=self.config.temperature,
        stop=self.config.stop,
    ),
)
```

Available backends:
- `mock`: Deterministic backend for testing
- `llama-cpp`: GGUF model backend

### 5. Ranking and Filtering

**SuggestionRanker.rank()** (`src/synarmo/suggestions.py:15-34`)

The ranker processes raw model output:

**Parsing** (`src/synarmo/suggestions.py:36-48`)
- Extracts suggestions from raw text
- Strips formatting (bullets, numbers, quotes)
- Splits on delimiters (commas, semicolons)

**Normalization** (`src/synarmo/suggestions.py:50-56`)
- Truncates to 4 words max
- Removes trailing punctuation
- Normalizes whitespace

**Filtering** (`src/synarmo/suggestions.py:58-84`)
- Removes duplicates
- Filters out suggestions that duplicate current text
- Filters out non-word characters
- Filters out instruction echoes (e.g., "suggestions", "alternatives")

**Scoring** (`src/synarmo/suggestions.py:86-92`)
- 1-4 words: 1.0 - (word_count - 1) * 0.05
- 5+ words: 0.5
- Sorted by score descending

```python
ranked = self.ranker.rank(
    raw,
    current_text=text,
    max_suggestions=self.config.max_suggestions,
)
```

### 6. Fill Pass (Optional)

**Engine fill logic** (`src/synarmo/engine.py:97-117`)

If first pass returns fewer than `max_suggestions`:
- Generates additional alternatives with higher temperature
- Appends to original raw output
- Re-ranks combined results

### 7. Return Results

**Final return** (`src/synarmo/engine.py:118-122`)

Returns ranked list of `Suggestion` objects:
```python
return self.ranker.rank(
    raw,
    current_text=text,
    max_suggestions=self.config.max_suggestions,
)
```

Each `Suggestion` contains:
- `text`: The suggested continuation
- `score`: Ranking score (0.0-1.0)
- `source`: "model" (default)

## User Memory Integration

**UserMemory** (`src/synarmo/memory.py`)

User memory persists per profile:
- `style_summary`: User's communication style
- `preferences`: Dictionary of user preferences
- `common_phrases`: List of frequently used phrases

Memory is loaded from `profiles/{profile}/memory.json` and updated via `remember_phrase()`.

## Thread Safety

**Generation Lock** (`src/synarmo/engine.py:40`, `83`)

The engine uses a threading lock to ensure only one generation runs at a time:
```python
with self._generation_lock:
    raw = self.backend.generate(...)
```

## Configuration

**SynarmoConfig** controls:
- `max_suggestions`: Number of suggestions to return (default: 5)
- `max_tokens`: Maximum tokens per generation
- `temperature`: Sampling temperature
- `stop`: Stop tokens
- `context_window`: Context size limit
- `style_adaptation`: Whether to use user memory
