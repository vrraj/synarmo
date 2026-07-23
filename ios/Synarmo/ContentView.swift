import SwiftUI

struct ContentView: View {
    @StateObject private var settings = SettingsStore()
    @StateObject private var composer = ComposeViewModel()
    @StateObject private var speech = SpeechService()
    @State private var showingSettings = false

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(spacing: 10) {
                    modelCard
                    contextPresetPicker
                    TextEditor(text: $composer.text)
                        .font(.title3)
                        .frame(minHeight: 132, maxHeight: 152)
                        .padding(8)
                        .overlay(RoundedRectangle(cornerRadius: 12).stroke(.secondary.opacity(0.4)))
                        .accessibilityLabel("Message to speak")
                        .onChange(of: composer.text) { _ in composer.textChanged(settings: settings.value) }
                    suggestionPills
                }
                .padding(.horizontal)
                .padding(.bottom)
                .padding(.top, 4)
            }
            .safeAreaInset(edge: .bottom, spacing: 0) {
                controlFooter
            }
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .principal) {
                    Text("Synarmo")
                        .font(.headline.weight(.regular))
                }
                ToolbarItem(placement: .topBarTrailing) {
                    Button { showingSettings = true } label: {
                        Image(systemName: "gear")
                    }
                        .accessibilityLabel("Compose settings")
                }
            }
            .sheet(isPresented: $showingSettings) { SettingsView(settings: settings, composer: composer) }
        }
    }

    @ViewBuilder
    private var contextPresetPicker: some View {
        if !settings.contextPresets.isEmpty {
            Menu {
                ForEach(settings.contextPresets) { preset in
                    Button(preset.name) {
                        settings.selectContextPreset(id: preset.id)
                    }
                }
            } label: {
                Label(
                    settings.activeContextPreset.map { "Context: \($0.name)" } ?? "Choose Context",
                    systemImage: "text.book.closed"
                )
            }
            .frame(maxWidth: .infinity, alignment: .leading)
        }
    }

    @ViewBuilder
    private var suggestionPills: some View {
        Group {
            if !composer.suggestions.isEmpty {
            SuggestionFlowLayout(spacing: 4) {
                ForEach(composer.suggestions.prefix(3)) { suggestion in
                    Button { composer.insert(suggestion) } label: {
                        Text(suggestion.text)
                            .lineLimit(1)
                            .truncationMode(.tail)
                    }
                    .buttonStyle(.bordered)
                    .accessibilityLabel("Insert suggestion \(suggestion.text)")
                }
            }
            }
        }
        // Reserve two button rows so the action and status rows do not jump as
        // suggestions appear, disappear, or wrap.
        .frame(maxWidth: .infinity, minHeight: 68, alignment: .center)
    }

    private var actionBar: some View {
        HStack {
            Button(speech.isSpeaking ? "Speaking…" : "Speak") {
                speech.toggle(text: composer.text, settings: settings.value)
            }
            .buttonStyle(.borderedProminent)
            .accessibilityHint(speech.isSpeaking ? "Stops speaking" : "Speaks the complete message aloud")
            Spacer()
            Button("Clear", role: .destructive) { composer.clear() }
                .buttonStyle(.bordered)
        }
        .frame(maxWidth: .infinity)
    }

    private var controlFooter: some View {
        VStack(spacing: 12) {
            actionBar
            metrics
        }
        .padding(.horizontal)
        .padding(.vertical, 10)
        .background(.background)
    }

    private var modelCard: some View {
        HStack(spacing: 10) {
            switch composer.modelState {
            case .needsDownload:
                Button("Download Model", systemImage: "arrow.down.circle") {
                    Task { await composer.downloadAndLoad(settings: settings.value) }
                }
                .buttonStyle(.borderedProminent)
            case .unloaded:
                Button("Load Model", systemImage: "memorychip") {
                    Task { await composer.downloadAndLoad(settings: settings.value) }
                }
                .buttonStyle(.borderedProminent)
            case .downloading(let progress):
                ProgressView(value: progress > 0 ? progress : nil) {
                    Text("Downloading model…")
                }
            case .loading:
                ProgressView("Loading model…")
            case .ready:
                Label("Model: Llama 3.2 1B", systemImage: "checkmark.circle.fill")
                    .foregroundStyle(.secondary)
            case .unavailable(let message):
                Text(message)
                    .font(.footnote)
                    .foregroundStyle(.red)
                    .lineLimit(2)
                Spacer()
                Button("Retry") {
                    Task { await composer.downloadAndLoad(settings: settings.value) }
                }
                .buttonStyle(.bordered)
            }
        }
        .frame(maxWidth: .infinity, alignment: .leading)
    }

    private var metrics: some View {
        let items = [
            composer.isSuggesting ? "Predicting…" : "Ready",
            composer.metrics.modelLoadMilliseconds.map { "load \(formattedDuration($0))" },
            composer.metrics.suggestionMilliseconds.map { "last \(formattedDuration($0))" }
        ].compactMap { $0 }

        return Text(items.joined(separator: "  •  "))
        .font(.caption)
        .foregroundStyle(.secondary)
        .lineLimit(1)
        .frame(maxWidth: .infinity, alignment: .leading)
        .accessibilityLabel(items.joined(separator: ", "))
    }

    private func formattedDuration(_ milliseconds: Int) -> String {
        String(format: "%.1fs", Double(milliseconds) / 1_000)
    }
}

private struct SuggestionFlowLayout: Layout {
    let spacing: CGFloat

    func sizeThatFits(
        proposal: ProposedViewSize,
        subviews: Subviews,
        cache: inout ()
    ) -> CGSize {
        let availableWidth = proposal.width ?? .infinity
        var rowWidth: CGFloat = 0
        var rowHeight: CGFloat = 0
        var totalHeight: CGFloat = 0

        for subview in subviews {
            let size = subview.sizeThatFits(.unspecified)
            if rowWidth > 0, rowWidth + spacing + size.width > availableWidth {
                totalHeight += rowHeight + spacing
                rowWidth = 0
                rowHeight = 0
            }
            rowWidth += (rowWidth > 0 ? spacing : 0) + min(size.width, availableWidth)
            rowHeight = max(rowHeight, size.height)
        }

        return CGSize(width: proposal.width ?? rowWidth, height: totalHeight + rowHeight)
    }

    func placeSubviews(
        in bounds: CGRect,
        proposal: ProposedViewSize,
        subviews: Subviews,
        cache: inout ()
    ) {
        var sizes: [CGSize] = []
        var rowForSubview: [Int] = []
        var rowWidths: [CGFloat] = [0]
        var rowHeights: [CGFloat] = [0]
        var currentRow = 0

        for subview in subviews {
            let naturalSize = subview.sizeThatFits(.unspecified)
            let width = min(naturalSize.width, bounds.width)
            let size = subview.sizeThatFits(ProposedViewSize(width: width, height: nil))
            let additionalWidth = rowWidths[currentRow] == 0 ? width : spacing + width

            if rowWidths[currentRow] > 0, rowWidths[currentRow] + additionalWidth > bounds.width {
                currentRow += 1
                rowWidths.append(0)
                rowHeights.append(0)
            }

            sizes.append(size)
            rowForSubview.append(currentRow)
            rowWidths[currentRow] += rowWidths[currentRow] == 0 ? width : spacing + width
            rowHeights[currentRow] = max(rowHeights[currentRow], size.height)
        }

        var x = bounds.minX + max(0, (bounds.width - rowWidths[0]) / 2)
        var y = bounds.minY
        var row = 0

        for (index, subview) in subviews.enumerated() {
            if rowForSubview[index] != row {
                y += rowHeights[row] + spacing
                row = rowForSubview[index]
                x = bounds.minX + max(0, (bounds.width - rowWidths[row]) / 2)
            }

            subview.place(
                at: CGPoint(x: x, y: y),
                proposal: ProposedViewSize(width: sizes[index].width, height: sizes[index].height)
            )
            x += sizes[index].width + spacing
        }
    }
}
