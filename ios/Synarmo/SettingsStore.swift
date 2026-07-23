import Combine
import Foundation

@MainActor
final class SettingsStore: ObservableObject {
    @Published var value: ComposeSettings {
        didSet { save() }
    }
    @Published private(set) var contextPresets: [ContextPreset]
    @Published private(set) var activeContextPresetID: UUID?

    private let key = "compose-settings-v1"
    private let contextPresetsKey = "context-presets-v1"
    private let activeContextPresetKey = "active-context-preset-v1"
    private let defaults: UserDefaults

    init(defaults: UserDefaults = .standard) {
        self.defaults = defaults
        contextPresets = defaults.data(forKey: contextPresetsKey)
            .flatMap { try? JSONDecoder().decode([ContextPreset].self, from: $0) } ?? []
        activeContextPresetID = defaults.string(forKey: activeContextPresetKey).flatMap(UUID.init(uuidString:))
        guard let data = defaults.data(forKey: key),
              let saved = try? JSONDecoder().decode(ComposeSettings.self, from: data)
        else {
            value = .default
            return
        }
        value = saved
    }

    private func save() {
        guard let data = try? JSONEncoder().encode(value) else { return }
        defaults.set(data, forKey: key)
    }

    var activeContextPreset: ContextPreset? {
        contextPresets.first { $0.id == activeContextPresetID }
    }

    @discardableResult
    func saveCurrentContextAsNewPreset() -> Bool {
        let name = value.contextProfile.trimmingCharacters(in: .whitespacesAndNewlines)
        let text = value.context.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !name.isEmpty, !text.isEmpty else { return false }
        let preset = ContextPreset(name: name, text: text)
        contextPresets.append(preset)
        selectContextPreset(id: preset.id)
        saveContextPresets()
        return true
    }

    @discardableResult
    func updateActiveContextPreset() -> Bool {
        guard let id = activeContextPresetID,
              let index = contextPresets.firstIndex(where: { $0.id == id })
        else { return false }
        let name = value.contextProfile.trimmingCharacters(in: .whitespacesAndNewlines)
        let text = value.context.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !name.isEmpty, !text.isEmpty else { return false }
        contextPresets[index].name = name
        contextPresets[index].text = text
        saveContextPresets()
        return true
    }

    func selectContextPreset(id: UUID?) {
        activeContextPresetID = id
        defaults.set(id?.uuidString, forKey: activeContextPresetKey)
        guard let id, let preset = contextPresets.first(where: { $0.id == id }) else { return }
        value.contextProfile = preset.name
        value.context = preset.text
    }

    func deleteActiveContextPreset() {
        guard let id = activeContextPresetID else { return }
        contextPresets.removeAll { $0.id == id }
        activeContextPresetID = nil
        defaults.removeObject(forKey: activeContextPresetKey)
        saveContextPresets()
    }

    private func saveContextPresets() {
        guard let data = try? JSONEncoder().encode(contextPresets) else { return }
        defaults.set(data, forKey: contextPresetsKey)
    }
}

enum TextInsertion {
    static func appending(_ suggestion: String, to text: String) -> String {
        let cleanSuggestion = suggestion.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !cleanSuggestion.isEmpty else { return text }
        guard !text.isEmpty, !text.hasSuffix(" "), !text.hasSuffix("\n") else {
            return text + cleanSuggestion
        }
        return text + " " + cleanSuggestion
    }
}
