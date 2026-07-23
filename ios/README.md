# Synarmo for iOS

This directory is a standalone native iOS application. It is deliberately not
part of the Python package: `pyproject.toml`, `src/`, the FastAPI service, and
the desktop browser UI neither build nor import this code.

## First device-performance milestone

The initial target is the existing `Llama-3.2-1B.Q4_K_M.gguf` model. The app
downloads it after installation (it is not in the app bundle), caches it in
Application Support, loads it through llama.cpp, and records model load and
suggestion latency. This lets us decide from measurements on real phones
whether the model is responsive enough before adding more product features.

## Open and run

1. Install full Xcode (the Command Line Tools alone cannot build an iOS app).
2. Open `Synarmo.xcodeproj`.
3. Select an iPhone simulator to exercise the UI, or a real iPhone for model
   inference and AVSpeechSynthesizer verification.
4. Add the llama.cpp XCFramework as described in
   `Docs/llama-cpp-integration.md` and set `SYNARMO_LLAMA_CPP=1` for the app
   target. Until then, the app clearly reports that on-device inference has
   not been linked; it never presents fake output as a model result.

The default model URL is the same GGUF configuration used by the Python
project. Before release, host or select a versioned, checksum-pinned model URL
that you are licensed to distribute.

## What is persisted

- Compose tuning and speech preferences: `UserDefaults`
- Named context presets and the active preset: `UserDefaults`
- Downloaded model: `Library/Application Support/Synarmo/Models/`

Typed text and generated suggestions are not sent to a server by this app.

## Context presets

Use **Settings → Context Presets** to save named situations such as a doctor's
office visit. Selecting a preset copies it into the editable working context
used for suggestions. Editing that working context does not modify the saved
preset unless the user explicitly saves a new preset or updates the active one.
The Compose screen also provides a quick context picker when saved presets are
available.
