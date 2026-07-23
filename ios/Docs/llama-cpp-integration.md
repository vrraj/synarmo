# llama.cpp integration

The SwiftUI app owns presentation and state. The inference boundary is
`LlamaCppBridge`, an Objective-C++ class that owns the C++ runtime, and is the
only component allowed to call llama.cpp. Swift calls it off the main actor.

## XCFramework contract

Build or obtain an iOS device-and-simulator XCFramework containing llama.cpp
and expose its public `llama.h` headers. Add it to the `Synarmo` target,
including its headers and required system frameworks. Define
`SYNARMO_LLAMA_CPP=1` in that target only after the framework is linked.

`LlamaCppBridge.mm` intentionally compiles into an unavailable implementation
without that flag. This keeps the UI buildable before native inference is
integrated and prevents accidental fake suggestions.

## Required bridge behavior

The production implementation must:

1. Load exactly one model/context at a time from the downloaded local URL.
2. Keep the model warm between requests and serialize evaluation.
3. Return candidate text plus scores, or a descriptive error.
4. Support cancellation between candidate evaluations.
5. Expose model-load and suggestion elapsed time for the performance panel.
6. Use the same short-candidate constraints as the existing application:
   choices, tokens, words, temperature, top-p, and logprob pool.

The current Objective-C++ file contains the linkage seam; wire its methods to
the llama.cpp version chosen for the XCFramework. Do not expose C++ headers to
Swift or put inference work on the main thread.

