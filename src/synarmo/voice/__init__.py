"""Voice output helpers, independent of Synarmo's suggestion engine."""

from synarmo.config import VoiceBackendName
from synarmo.voice.service import VoiceOutput, VoiceService


def speak(text: str, *, output: VoiceBackendName | None = None) -> VoiceOutput:
    """Create a voice result for ``text`` using Browser or OpenAI output.

    Browser output is an instruction for a browser client and therefore has no
    audio bytes. OpenAI output contains an ``audio/wav`` payload.
    """

    return VoiceService().synthesize(text, backend=output)


__all__ = ["VoiceOutput", "VoiceService", "speak"]
