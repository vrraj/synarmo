from __future__ import annotations

from dataclasses import dataclass

from synarmo.config import (
    VoiceBackendName,
    configured_openai_tts_instructions,
    configured_openai_tts_model,
    configured_openai_tts_voice,
    configured_voice_backend,
    load_env_file,
)


@dataclass(frozen=True, slots=True)
class VoiceOutput:
    """The result of synthesizing text.

    Browser output intentionally has no audio bytes: the browser owns its native
    speech engine. API output contains a WAV payload suitable for REST or MCP.
    """

    backend: VoiceBackendName
    text: str
    audio: bytes | None = None
    media_type: str | None = None


class VoiceService:
    """A standalone browser-or-API text-to-speech entry point."""

    def __init__(
        self,
        *,
        backend: VoiceBackendName | None = None,
        openai_model: str | None = None,
        openai_voice: str | None = None,
        openai_instructions: str | None = None,
    ) -> None:
        load_env_file()
        self.backend = backend or configured_voice_backend()
        self.openai_model = openai_model or configured_openai_tts_model()
        self.openai_voice = openai_voice or configured_openai_tts_voice()
        self.openai_instructions = (
            openai_instructions
            if openai_instructions is not None
            else configured_openai_tts_instructions()
        )

    def synthesize(self, text: str, *, backend: VoiceBackendName | None = None) -> VoiceOutput:
        normalized = text.strip()
        if not normalized:
            raise ValueError("Text is required for voice synthesis")
        selected_backend = backend or self.backend
        if selected_backend == "browser":
            return VoiceOutput(backend="browser", text=normalized)
        return self._synthesize_openai(normalized)

    def _synthesize_openai(self, text: str) -> VoiceOutput:
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise RuntimeError(
                "OpenAI TTS requires: pip install -e '.[voice-openai]'"
            ) from exc

        options: dict[str, str] = {
            "model": self.openai_model,
            "voice": self.openai_voice,
            "input": text,
            "response_format": "wav",
        }
        if self.openai_instructions:
            options["instructions"] = self.openai_instructions
        try:
            client = OpenAI()
            with client.audio.speech.with_streaming_response.create(**options) as response:
                audio = response.read()
        except Exception as exc:
            raise RuntimeError("OpenAI TTS request failed") from exc
        if not audio:
            raise RuntimeError("OpenAI TTS returned an empty audio response")
        return VoiceOutput(backend="openai", text=text, audio=audio, media_type="audio/wav")
