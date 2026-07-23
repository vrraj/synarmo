import Combine
import Foundation

@MainActor
final class ComposeViewModel: ObservableObject {
    enum ModelState: Equatable {
        case needsDownload
        case downloading(Double)
        case loading
        case ready
        case unloaded
        case unavailable(String)

        var label: String {
            switch self {
            case .needsDownload: return "Model not downloaded"
            case .downloading(let value): return "Downloading model \(Int(value * 100))%"
            case .loading: return "Loading model…"
            case .ready: return "On-device model ready"
            case .unloaded: return "Downloaded model is not loaded"
            case .unavailable(let message): return message
            }
        }
    }

    @Published var text = ""
    @Published private(set) var suggestions: [Suggestion] = []
    @Published private(set) var modelState: ModelState = .needsDownload
    @Published private(set) var isSuggesting = false
    @Published private(set) var metrics = InferenceMetrics()

    let downloader = ModelDownloadService()
    private let engine: SuggestionEngine
    private var suggestionTask: Task<Void, Never>?
    private var idleUnloadTask: Task<Void, Never>?
    private var loadedModelURL: URL?

    init(engine: SuggestionEngine = LlamaCppInferenceEngine()) {
        self.engine = engine
        downloader.restoreState()
        syncDownloadState()
    }

    func syncDownloadState() {
        switch downloader.state {
        case .notDownloaded: modelState = .needsDownload
        case .downloading(let progress): modelState = .downloading(progress)
        case .downloaded(let url):
            if loadedModelURL != url { modelState = .unloaded }
        case .failed(let message): modelState = .unavailable(message)
        }
    }

    func downloadAndLoad(settings: ComposeSettings) async {
        do {
            let url = try await downloader.download()
            modelState = .loading
            metrics = try await engine.loadModel(at: url)
            loadedModelURL = url
            modelState = .ready
            resetIdleUnloadTimer(settings: settings)
        } catch {
            modelState = .unavailable(error.localizedDescription)
        }
    }

    var hasDownloadedModel: Bool {
        if case .downloaded = downloader.state {
            return true
        }
        return false
    }

    func deleteModel() async {
        engine.cancel()
        suggestionTask?.cancel()
        idleUnloadTask?.cancel()
        suggestions = []
        await engine.unload()

        do {
            try downloader.delete()
            loadedModelURL = nil
            metrics = InferenceMetrics()
            modelState = .needsDownload
        } catch {
            modelState = .unavailable("Could not delete the downloaded model: \(error.localizedDescription)")
        }
    }

    func textChanged(settings: ComposeSettings) {
        suggestionTask?.cancel()
        if isSuggesting {
            engine.cancel()
        }
        guard settings.suggestOnSpacebar,
              text.last?.isWhitespace == true,
              !text.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty
        else { return }
        suggestionTask = Task { [weak self] in
            try? await Task.sleep(for: .milliseconds(max(0, settings.predictionDebounceMilliseconds)))
            guard !Task.isCancelled else { return }
            await self?.suggest(settings: settings)
        }
    }

    func suggest(settings: ComposeSettings) async {
        guard case .ready = modelState else {
            modelState = .unavailable("Load the downloaded model before requesting suggestions.")
            return
        }
        let currentText = text.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !currentText.isEmpty else {
            suggestions = []
            return
        }
        isSuggesting = true
        defer { isSuggesting = false }
        resetIdleUnloadTimer(settings: settings)
        do {
            let request = SuggestionRequest(
                text: currentText,
                context: promptContext(from: settings),
                settings: settings
            )
            let (items, newMetrics) = try await engine.suggest(request)
            guard currentText == text.trimmingCharacters(in: .whitespacesAndNewlines) else { return }
            suggestions = uniqueSuggestions(items)
            metrics.suggestionMilliseconds = newMetrics.suggestionMilliseconds
            resetIdleUnloadTimer(settings: settings)
        } catch {
            guard !Task.isCancelled,
                  currentText == text.trimmingCharacters(in: .whitespacesAndNewlines)
            else { return }
            modelState = .unavailable(error.localizedDescription)
        }
    }

    func updateIdleUnloadTimer(settings: ComposeSettings) {
        resetIdleUnloadTimer(settings: settings)
    }

    private func resetIdleUnloadTimer(settings: ComposeSettings) {
        idleUnloadTask?.cancel()
        guard settings.unloadModelWhenIdle, case .ready = modelState else { return }

        let timeout = settings.modelIdleTimeoutMinutes
        idleUnloadTask = Task { [weak self] in
            try? await Task.sleep(for: .seconds(timeout * 60))
            guard !Task.isCancelled else { return }
            await self?.unloadForInactivity()
        }
    }

    private func unloadForInactivity() async {
        guard case .ready = modelState else { return }
        engine.cancel()
        suggestions = []
        await engine.unload()
        loadedModelURL = nil
        modelState = .unloaded
    }

    private func uniqueSuggestions(_ items: [Suggestion]) -> [Suggestion] {
        var seen = Set<String>()
        return items.filter { item in
            let key = item.text.trimmingCharacters(in: .whitespacesAndNewlines).lowercased()
            return !key.isEmpty && seen.insert(key).inserted
        }
    }

    func insert(_ suggestion: Suggestion) {
        text = TextInsertion.appending(suggestion.text, to: text)
        suggestions = []
    }

    func clear() {
        engine.cancel()
        suggestionTask?.cancel()
        text = ""
        suggestions = []
    }

    private func promptContext(from settings: ComposeSettings) -> String {
        let profile = settings.contextProfile.trimmingCharacters(in: .whitespacesAndNewlines)
        let context = settings.context.trimmingCharacters(in: .whitespacesAndNewlines)
        return [
            profile.isEmpty ? nil : "Conversation profile: \(profile)",
            context.isEmpty ? nil : context
        ]
        .compactMap { $0 }
        .joined(separator: "\n")
    }
}
