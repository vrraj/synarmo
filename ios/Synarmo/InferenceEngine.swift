import Foundation

final class LlamaCppInferenceEngine: SuggestionEngine, @unchecked Sendable {
    private let bridge = LlamaCppBridge()

    func loadModel(at url: URL) async throws -> InferenceMetrics {
        let started = Date()
        return try await Task.detached(priority: .userInitiated) { [bridge] in
            do {
                try bridge.loadModel(atPath: url.path)
            } catch {
                throw Self.map(error as NSError)
            }
            let elapsed = Int(Date().timeIntervalSince(started) * 1_000)
            let bytes = (try? url.resourceValues(forKeys: [.fileSizeKey]).fileSize).map(Int64.init)
            return InferenceMetrics(
                modelLoadMilliseconds: elapsed,
                suggestionMilliseconds: nil,
                modelSizeBytes: bytes
            )
        }.value
    }

    func suggest(_ request: SuggestionRequest) async throws -> ([Suggestion], InferenceMetrics) {
        let started = Date()
        return try await Task.detached(priority: .userInitiated) { [bridge] in
            var error: NSError?
            let raw = bridge.suggest(
                forText: request.text,
                context: request.context,
                choices: request.settings.choices,
                candidateTokenCount: request.settings.candidateTokens,
                candidateWordCount: request.settings.candidateWords,
                temperature: request.settings.temperature,
                topP: request.settings.topP,
                logprobPool: request.settings.logprobPool,
                error: &error
            )
            if let error { throw Self.map(error) }
            let suggestions = raw.compactMap { item -> Suggestion? in
                guard let text = item["text"] as? String else { return nil }
                return Suggestion(text: text, score: item["score"] as? Double ?? 0)
            }
            let elapsed = Int(Date().timeIntervalSince(started) * 1_000)
            return (suggestions, InferenceMetrics(modelLoadMilliseconds: nil, suggestionMilliseconds: elapsed, modelSizeBytes: nil))
        }.value
    }

    func cancel() { bridge.cancel() }

    func unload() async {
        await Task.detached(priority: .userInitiated) { [bridge] in
            bridge.unloadModel()
        }.value
    }

    private static func map(_ error: NSError?) -> InferenceError {
        let message = error?.localizedDescription ?? "On-device inference failed."
        return message.contains("not linked") ? .runtimeUnavailable : .failed(message)
    }
}
