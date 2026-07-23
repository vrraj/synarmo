import Combine
import Foundation

@MainActor
final class ModelDownloadService: ObservableObject {
    enum State: Equatable {
        case notDownloaded
        case downloading(progress: Double)
        case downloaded(URL)
        case failed(String)
    }

    @Published private(set) var state: State = .notDownloaded

    var localModelURL: URL {
        get throws {
            let directory = try FileManager.default.url(
                for: .applicationSupportDirectory,
                in: .userDomainMask,
                appropriateFor: nil,
                create: true
            ).appendingPathComponent("Synarmo/Models", isDirectory: true)
            try FileManager.default.createDirectory(at: directory, withIntermediateDirectories: true)
            return directory.appendingPathComponent(ModelConfiguration.filename)
        }
    }

    func restoreState() {
        guard let url = try? localModelURL else { return }
        state = FileManager.default.fileExists(atPath: url.path) ? .downloaded(url) : .notDownloaded
    }

    func download() async throws -> URL {
        let destination = try localModelURL
        if FileManager.default.fileExists(atPath: destination.path) {
            state = .downloaded(destination)
            return destination
        }
        state = .downloading(progress: 0)
        do {
            let (temporaryURL, response) = try await URLSession.shared.download(from: ModelConfiguration.downloadURL)
            guard let httpResponse = response as? HTTPURLResponse,
                  (200..<300).contains(httpResponse.statusCode)
            else {
                throw URLError(.badServerResponse)
            }
            try? FileManager.default.removeItem(at: destination)
            try FileManager.default.moveItem(at: temporaryURL, to: destination)
            state = .downloaded(destination)
            return destination
        } catch {
            state = .failed(error.localizedDescription)
            throw error
        }
    }

    func delete() throws {
        let destination = try localModelURL
        if FileManager.default.fileExists(atPath: destination.path) {
            try FileManager.default.removeItem(at: destination)
        }
        state = .notDownloaded
    }
}
