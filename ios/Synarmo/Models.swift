import Foundation

struct ContextPreset: Identifiable, Codable, Equatable {
    let id: UUID
    var name: String
    var text: String

    init(id: UUID = UUID(), name: String, text: String) {
        self.id = id
        self.name = name
        self.text = text
    }
}

struct ComposeSettings: Codable, Equatable {
    var choices = 3
    var candidateTokens = 5
    var candidateWords = 1
    var temperature = 0.5
    var topP = 0.95
    var logprobPool = 24
    var suggestOnSpacebar = true
    var predictionDebounceMilliseconds = 100
    var contextProfile = "Everyday"
    var context = ""
    var speechRate = 0.5
    var speechPitch = 1.0
    var unloadModelWhenIdle = true
    var modelIdleTimeoutMinutes = 10

    static let `default` = ComposeSettings()

    init() {}

    private enum CodingKeys: String, CodingKey {
        case choices, candidateTokens, candidateWords, temperature, topP, logprobPool
        case suggestOnSpacebar, predictionDebounceMilliseconds, contextProfile, context, speechRate, speechPitch
        case unloadModelWhenIdle, modelIdleTimeoutMinutes
    }

    init(from decoder: Decoder) throws {
        let values = try decoder.container(keyedBy: CodingKeys.self)
        choices = try values.decodeIfPresent(Int.self, forKey: .choices) ?? 3
        candidateTokens = try values.decodeIfPresent(Int.self, forKey: .candidateTokens) ?? 5
        candidateWords = try values.decodeIfPresent(Int.self, forKey: .candidateWords) ?? 1
        temperature = try values.decodeIfPresent(Double.self, forKey: .temperature) ?? 0.5
        topP = try values.decodeIfPresent(Double.self, forKey: .topP) ?? 0.95
        logprobPool = try values.decodeIfPresent(Int.self, forKey: .logprobPool) ?? 24
        suggestOnSpacebar = try values.decodeIfPresent(Bool.self, forKey: .suggestOnSpacebar) ?? true
        predictionDebounceMilliseconds = try values.decodeIfPresent(Int.self, forKey: .predictionDebounceMilliseconds) ?? 100
        contextProfile = try values.decodeIfPresent(String.self, forKey: .contextProfile) ?? "Everyday"
        context = try values.decodeIfPresent(String.self, forKey: .context) ?? ""
        speechRate = try values.decodeIfPresent(Double.self, forKey: .speechRate) ?? 0.5
        speechPitch = try values.decodeIfPresent(Double.self, forKey: .speechPitch) ?? 1.0
        unloadModelWhenIdle = try values.decodeIfPresent(Bool.self, forKey: .unloadModelWhenIdle) ?? true
        modelIdleTimeoutMinutes = try values.decodeIfPresent(Int.self, forKey: .modelIdleTimeoutMinutes) ?? 10
    }
}

struct Suggestion: Identifiable, Equatable {
    let text: String
    let score: Double
    var id: String { text.lowercased() }
}

struct SuggestionRequest: Equatable {
    let text: String
    let context: String
    let settings: ComposeSettings
}

struct InferenceMetrics: Equatable {
    var modelLoadMilliseconds: Int?
    var suggestionMilliseconds: Int?
    var modelSizeBytes: Int64?
}

enum InferenceError: LocalizedError, Equatable {
    case modelNotDownloaded
    case runtimeUnavailable
    case failed(String)

    var errorDescription: String? {
        switch self {
        case .modelNotDownloaded: return "Download the model before requesting suggestions."
        case .runtimeUnavailable: return "On-device llama.cpp inference has not been linked into this build."
        case .failed(let message): return message
        }
    }
}

protocol SuggestionEngine: Sendable {
    func loadModel(at url: URL) async throws -> InferenceMetrics
    func suggest(_ request: SuggestionRequest) async throws -> ([Suggestion], InferenceMetrics)
    func cancel()
    func unload() async
}

enum ModelConfiguration {
    static let filename = "Llama-3.2-1B.Q4_K_M.gguf"
    static let downloadURL = URL(string: "https://huggingface.co/QuantFactory/Llama-3.2-1B-GGUF/resolve/main/Llama-3.2-1B.Q4_K_M.gguf")!
}
