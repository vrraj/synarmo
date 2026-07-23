import SwiftUI

struct SettingsView: View {
    @ObservedObject var settings: SettingsStore
    @ObservedObject var composer: ComposeViewModel
    @Environment(\.dismiss) private var dismiss
    @State private var showingDeleteModelConfirmation = false
    @State private var contextPresetError: String?

    var body: some View {
        NavigationStack {
            Form {
                Section("Suggestions") {
                    Stepper("Choices: \(settings.value.choices)", value: binding(\.choices), in: 1...10)
                    Stepper("Tokens: \(settings.value.candidateTokens)", value: binding(\.candidateTokens), in: 1...64)
                    Stepper("Words: \(settings.value.candidateWords)", value: binding(\.candidateWords), in: 1...8)
                    Stepper("Logprobs: \(settings.value.logprobPool)", value: binding(\.logprobPool), in: 1...50)
                    SliderRow(label: "Temperature", value: binding(\.temperature), range: 0...2, step: 0.1)
                    SliderRow(label: "Top P", value: binding(\.topP), range: 0.05...1, step: 0.05)
                    Toggle("Suggest after a space", isOn: binding(\.suggestOnSpacebar))
                    if settings.value.suggestOnSpacebar {
                        Stepper(
                            "Prediction delay: \(settings.value.predictionDebounceMilliseconds) ms",
                            value: binding(\.predictionDebounceMilliseconds),
                            in: 0...500,
                            step: 25
                        )
                    }
                }
                Section("Working Context") {
                    TextField("Profile name", text: binding(\.contextProfile))
                    TextEditor(text: binding(\.context))
                        .frame(minHeight: 100)
                        .accessibilityLabel("Composition context")
                }
                Section("Context Presets") {
                    Picker("Active preset", selection: activePresetBinding) {
                        Text("None").tag(UUID?.none)
                        ForEach(settings.contextPresets) { preset in
                            Text(preset.name).tag(Optional(preset.id))
                        }
                    }
                    Button("Save Working Context as New Preset") {
                        if !settings.saveCurrentContextAsNewPreset() {
                            contextPresetError = "Enter both a profile name and context before saving a preset."
                        }
                    }
                    Button("Update Active Preset") {
                        if !settings.updateActiveContextPreset() {
                            contextPresetError = "Select a preset and enter both a profile name and context before updating it."
                        }
                    }
                    .disabled(settings.activeContextPreset == nil)
                    Button("Delete Active Preset", role: .destructive) {
                        settings.deleteActiveContextPreset()
                    }
                    .disabled(settings.activeContextPreset == nil)
                    if let contextPresetError {
                        Text(contextPresetError)
                            .font(.footnote)
                            .foregroundStyle(.red)
                    }
                }
                Section("Speech") {
                    SliderRow(label: "Rate", value: binding(\.speechRate), range: 0...1, step: 0.05)
                    SliderRow(label: "Pitch", value: binding(\.speechPitch), range: 0.5...2, step: 0.1)
                }
                Section("Model") {
                    Toggle("Unload model when idle", isOn: binding(\.unloadModelWhenIdle))
                    if settings.value.unloadModelWhenIdle {
                        Stepper(
                            "Unload after: \(settings.value.modelIdleTimeoutMinutes) minutes",
                            value: binding(\.modelIdleTimeoutMinutes),
                            in: 1...60
                        )
                    }
                    if composer.hasDownloadedModel {
                        Button("Delete Model", role: .destructive) {
                            showingDeleteModelConfirmation = true
                        }
                    } else {
                        Text("No model downloaded")
                            .foregroundStyle(.secondary)
                    }
                }
            }
            .onChange(of: settings.value.unloadModelWhenIdle) { _ in
                composer.updateIdleUnloadTimer(settings: settings.value)
            }
            .onChange(of: settings.value.modelIdleTimeoutMinutes) { _ in
                composer.updateIdleUnloadTimer(settings: settings.value)
            }
            .navigationTitle("Settings")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .confirmationAction) {
                    Button("Done") { dismiss() }
                        .accessibilityLabel("Close settings")
                }
            }
            .alert("Delete downloaded model?", isPresented: $showingDeleteModelConfirmation) {
                Button("Delete Model", role: .destructive) {
                    Task { await composer.deleteModel() }
                }
                Button("Cancel", role: .cancel) {}
            } message: {
                Text("This removes the model from this iPhone. The next time you need suggestions, downloading the model again may take some time.")
            }
        }
    }

    private func binding<T>(_ keyPath: WritableKeyPath<ComposeSettings, T>) -> Binding<T> {
        Binding(get: { settings.value[keyPath: keyPath] }, set: { settings.value[keyPath: keyPath] = $0 })
    }

    private var activePresetBinding: Binding<UUID?> {
        Binding(get: { settings.activeContextPresetID }, set: { settings.selectContextPreset(id: $0) })
    }
}

private struct SliderRow: View {
    let label: String
    let value: Binding<Double>
    let range: ClosedRange<Double>
    let step: Double

    var body: some View {
        VStack(alignment: .leading) {
            Text("\(label): \(value.wrappedValue, specifier: "%.2f")")
            Slider(value: value, in: range, step: step)
                .accessibilityLabel(label)
        }
    }
}
