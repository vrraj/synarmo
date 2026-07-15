from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Suggestion:
    text: str
    score: float
    source: str = "model"


class SuggestionRanker:
    def rank(
        self,
        raw_text: str,
        *,
        current_text: str,
        max_suggestions: int,
        max_words: int = 4,
    ) -> list[Suggestion]:
        candidates = self._parse(raw_text)
        seen: set[str] = set()
        ranked: list[Suggestion] = []
        for candidate in candidates:
            normalized = self._normalize(candidate, max_words=max_words)
            key = normalized.lower()
            if not normalized or key in seen:
                continue
            if not self._has_word_characters(normalized):
                continue
            if self._looks_like_instruction_echo(normalized):
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
            line = re.sub(r"^\s*(?:[-*]|\(?\d+[\].)]|\[\d+\])\s*", "", line).strip()
            line = line.strip("\"'` ")
            for part in re.split(r"\s+(?:\(?\d+[\].)]|\[\d+\])\s+", line):
                for subpart in re.split(r"[,;/]", part):
                    subpart = subpart.strip("\"'` ")
                    if subpart:
                        lines.append(subpart)
        if lines:
            return lines
        return [part.strip() for part in re.split(r"[,;/]", raw_text) if part.strip()]

    def _normalize(self, text: str, *, max_words: int) -> str:
        text = re.sub(r"\s+", " ", text).strip()
        text = re.sub(r"\s+(?:\(?\d+[\].)]|\[\d+\])\s*$", "", text)
        text = re.sub(r"\s*(?:\[\d+\]|\(\d+\))\s*$", "", text)
        text = re.sub(r"[.!?]+$", "", text)
        words = text.split()
        return " ".join(words[:max_words])

    def _duplicates_current_text(self, suggestion: str, current_text: str) -> bool:
        suggestion_words = suggestion.lower().split()
        current_words = current_text.lower().split()
        if not suggestion_words or len(suggestion_words) > len(current_words):
            return False
        suggestion_length = len(suggestion_words)
        return any(
            current_words[index : index + suggestion_length] == suggestion_words
            for index in range(len(current_words) - suggestion_length + 1)
        )

    def _has_word_characters(self, suggestion: str) -> bool:
        return bool(re.search(r"[A-Za-z0-9]", suggestion))

    def _looks_like_instruction_echo(self, suggestion: str) -> bool:
        lowered = suggestion.lower()
        blocked_phrases = (
            "answer",
            "more different",
            "plain text",
            "short lines",
            "suggestions",
            "alternatives",
        )
        return lowered.strip(": ") in blocked_phrases or any(
            phrase in lowered for phrase in blocked_phrases[1:]
        )

    def _score(self, text: str) -> float:
        word_count = len(text.split())
        if word_count == 0:
            return 0.0
        if word_count <= 4:
            return 1.0 - (word_count - 1) * 0.05
        return 0.5
