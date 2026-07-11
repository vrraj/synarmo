from __future__ import annotations

from synarmo.models.base import GenerationOptions


class MockBackend:
    name = "mock"

    def generate(self, prompt: str, options: GenerationOptions) -> str:
        lower = prompt.lower()
        if "my goals are" in lower:
            return "to build strength\nto run upstairs\nto improve endurance\nwithout tiring"
        if "i want to" in lower:
            return "go outside\nhave some water\ntalk to you\nrest for now"
        if "can you" in lower:
            return "please help me\ncome over here\ncheck this again"
        return "please help me\nI need that\nthank you very much\nlet me think"
