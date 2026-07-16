import sys
from types import SimpleNamespace

import pytest

import synarmo
from synarmo.voice import VoiceService


def test_browser_voice_returns_a_browser_instruction() -> None:
    output = VoiceService(backend="browser").synthesize("  Hello, world.  ")

    assert output.backend == "browser"
    assert output.text == "Hello, world."
    assert output.audio is None


def test_browser_voice_can_override_the_configured_backend() -> None:
    output = VoiceService(backend="openai").synthesize("Hello, world.", backend="browser")

    assert output.backend == "browser"
    assert output.audio is None


def test_public_speak_returns_a_browser_instruction() -> None:
    output = synarmo.speak(" Hello from Synarmo ", output="browser")

    assert output.backend == "browser"
    assert output.text == "Hello from Synarmo"
    assert output.audio is None


def test_openai_voice_returns_wav(monkeypatch) -> None:
    requested: dict[str, str] = {}

    class Response:
        def __enter__(self):
            return self

        def __exit__(self, *args) -> None:
            return None

        def read(self) -> bytes:
            return b"RIFF-openai-wav"

    class Speech:
        with_streaming_response = None

    def create(**kwargs):
        requested.update(kwargs)
        return Response()

    Speech.with_streaming_response = SimpleNamespace(create=create)
    fake_openai = SimpleNamespace(OpenAI=lambda: SimpleNamespace(audio=SimpleNamespace(speech=Speech())))
    monkeypatch.setitem(sys.modules, "openai", fake_openai)

    output = VoiceService(
        backend="openai",
        openai_model="gpt-4o-mini-tts",
        openai_voice="marin",
    ).synthesize("Hello", backend="openai")

    assert output.backend == "openai"
    assert output.audio == b"RIFF-openai-wav"
    assert requested["response_format"] == "wav"


def test_voice_rejects_empty_text() -> None:
    with pytest.raises(ValueError, match="Text is required"):
        VoiceService(backend="browser").synthesize("   ")
