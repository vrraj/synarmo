from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Suggestion:
    text: str
    score: float
    source: str = "model"


class SuggestionRanker:
    def rank(self, raw_text: str, *, current_text: str, max_suggestions: int) -> list[Suggestion]:
        candidates = self._parse(raw_text)
        seen: set[str] = set()
        ranked: list[Suggestion] = []
        for candidate in candidates:
            normalized = self._normalize(candidate)
            key = normalized.lower()
            if not normalized or key in seen:
                continue
            if self._duplicates_current_text(normalized, current_text):
                continue
            seen.add(key)
            score = self._score(normalized)
            ranked.append(Suggestion(text=normalized, score=score))
        ranked.sort(key=lambda item: item.score, reverse=True)
        return ranked[:max_suggestions]

    def _parse(self, raw_text: str) -> list[str]:
        lines = []
        for line in raw_text.splitlines():
            line = re.sub(r"^\s*[-*\d.)]+\s*", "", line).strip()
            line = line.strip("\"'` ")
            if line:
                lines.append(line)
        if lines:
            return lines
        return [part.strip() for part in re.split(r"[,;/]", raw_text) if part.strip()]

    def _normalize(self, text: str) -> str:
        text = re.sub(r"\s+", " ", text).strip()
        text = re.sub(r"[.!?]+$", "", text)
        words = text.split()
        return " ".join(words[:4])

    def _duplicates_current_text(self, suggestion: str, current_text: str) -> bool:
        current_tail = " ".join(current_text.lower().split()[-4:])
        return bool(current_tail) and suggestion.lower() == current_tail

    def _score(self, text: str) -> float:
        word_count = len(text.split())
        if word_count == 0:
            return 0.0
        if word_count <= 4:
            return 1.0 - (word_count - 1) * 0.05
        return 0.5
