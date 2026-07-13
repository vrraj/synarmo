from __future__ import annotations


class PromptBuilder:
    def build(
        self,
        *,
        assembled_context: str,
        max_suggestions: int,
        max_words: int | None = 4,
    ) -> str:
        max_words = _positive_word_limit(max_words)
        return f"""You are Synarmo, a private communication assistant.
Predict exactly {max_suggestions} natural continuations for the user's typed text.
Each continuation must be 1 to {max_words} words, append directly to the typed text, and match its context and style.
Return only the continuations, one per line, with no labels, numbering, explanation, or reply to the user.

{assembled_context}

Continuations:"""

    def build_autocomplete(self, *, assembled_context: str, typed_text: str) -> str:
        """Build the stable prompt used for next-token probability prediction."""
        context_lines = [
            line
            for line in assembled_context.rstrip().splitlines()
            if not line.lower().startswith("current typed text:")
        ]
        context_block = "\n".join(context_lines).strip()
        if context_block:
            context_block = f"\n\nContext:\n{context_block}"

        return f"""You are Synarmo, a private communication assistant.
Predict only the next words of the user's message. Do not reply to the user, repeat labels, or replace earlier text.{context_block}

Message:
{typed_text}"""


def _positive_word_limit(value: int | None) -> int:
    if value is None:
        return 1
    return max(1, value)
