import XCTest
@testable import Synarmo

final class SynarmoTests: XCTestCase {
    func testSuggestionInsertionAddsOneSpaceAfterAWord() {
        XCTAssertEqual(TextInsertion.appending("to go", to: "I want"), "I want to go")
    }

    func testSuggestionInsertionPreservesExistingTrailingSpace() {
        XCTAssertEqual(TextInsertion.appending("to go", to: "I want "), "I want to go")
    }

    func testComposeSettingsRoundTripsThroughPersistenceFormat() throws {
        var settings = ComposeSettings.default
        settings.choices = 5
        settings.context = "At a doctor appointment"
        XCTAssertEqual(try JSONDecoder().decode(ComposeSettings.self, from: JSONEncoder().encode(settings)), settings)
    }
}

