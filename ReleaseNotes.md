# Release Notes

## Synarmo Platform v1

Synarmo Platform v1 establishes the project as a local-first auto-suggest
platform: a reusable Python engine, a local service layer, a browser-based
interaction surface, and a documented GGUF model setup path for private
type-ahead suggestions.

This release turns Synarmo from a package-shaped prototype into a platform that
can be embedded, served locally, tested without a model, and run with real
local llama.cpp inference.

### Highlights

- **Local-first suggestion engine** with `SynarmoEngine.load(...)`,
  `engine.suggest(...)`, and convenience prediction APIs for embedding
  Synarmo in Python applications.
- **Backend-swappable model layer** with a deterministic `mock` backend for
  tests and wiring checks, plus a `llama-cpp` backend for local GGUF inference.
- **Short type-ahead suggestions** tuned around next-word and next-phrase
  completion rather than broad chat responses.
- **Local REST and WebSocket service mode** for applications that need a warm
  local Synarmo process instead of in-process Python calls.
- **Browser `/ui` experience** for interactive local suggestion testing,
  context comparison, and autocomplete evaluation.
- **Model readiness workflow** through `synarmo model-ensure` and
  `make model-ensure`, including local cache handling and configured model
  download support.
- **Environment-driven runtime configuration** for model cache, model filename
  or path, suggestion count, token limits, temperature, top-p, logprob pool,
  GPU offload layers, and llama.cpp verbosity.
- **GPU setup and diagnostics** for llama.cpp inference, including
  `SYNARMO_N_GPU_LAYERS`, CPU-only fallback, supported offload checks, and
  runtime diagnostics surfaced by the CLI and service health endpoint.
- **LAN-capable local service binding** with `synarmo serve --host 0.0.0.0`
  and `make serve-lan` for trusted-network testing.
- **Developer Make targets** for service startup, mock startup, browser UX,
  model checks, health checks, and shutdown.

### Platform Surface

Platform v1 includes four supported ways to use Synarmo:

- **Python API** for direct embedding through `SynarmoEngine`.
- **CLI** for quick local suggestions, interactive compose flows, model checks,
  and service startup.
- **Local service** for REST and WebSocket clients that need a persistent warm
  engine.
- **Browser UI** for local evaluation and hands-on type-ahead testing.

### Documentation

The README and companion docs were reorganized around the v1 platform path:
real local inference first, browser UX setup next, shared model configuration
in one place, then API, service, architecture, and roadmap details.

This release also clarifies:

- when a GGUF model is downloaded or only verified;
- how `LOCAL_MODELS_CACHE`, `SYNARMO_MODEL`, and `SYNARMO_MODEL_PATH` are used;
- how mock mode differs from real llama.cpp inference;
- how to configure CPU-only vs. GPU-offloaded inference;
- how to run the local service on loopback or a trusted LAN;
- how suggestion controls such as choices, candidate tokens, candidate words,
  temperature, top-p, and logprob pool map to runtime behavior.

### Not Included

- No model files are committed.
- No generated profiles or personal conversation data are included.
- UI applications beyond the local browser surface remain outside the reusable
  core package.
