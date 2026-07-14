from __future__ import annotations


class PromptBuilder:
    def build(
        self,
        *,
        assembled_context: str,
        typed_text: str,
        max_suggestions: int,
        max_words: int | None = 4,
    ) -> str:
        """Build a base-model prompt that ends exactly with the typed text."""
        del max_suggestions, max_words
        return self.build_autocomplete(
            assembled_context=assembled_context,
            typed_text=typed_text,
        )

    def build_autocomplete(self, *, assembled_context: str, typed_text: str) -> str:
        """Build the stable prompt used for next-token probability prediction."""
        context_lines = [
            line
            for line in assembled_context.rstrip().splitlines()
            if not line.lower().startswith("current typed text:")
        ]
        context_block = "\n".join(context_lines).strip()
        return f"{context_block}\n\n{typed_text}" if context_block else typed_text

    def build_instruct_messages(
        self,
        *,
        assembled_context: str,
        typed_text: str,
        max_suggestions: int,
        max_words: int | None = 4,
    ) -> list[dict[str, str]]:
        """Build role messages for an instruction-tuned model's native template."""
        max_words = _positive_word_limit(max_words)
        context_lines = [
            line
            for line in assembled_context.rstrip().splitlines()
            if not line.lower().startswith("current typed text:")
        ]
        context = "\n".join(context_lines).strip()
        user_content = f"Context:\n{context}\n\n" if context else ""
        user_content += f"Typed text:\n{typed_text}"
        return [
            {
                "role": "system",
                "content": (
                    "Return exactly "
                    f"{max_suggestions} distinct continuations of the typed text. "
                    f"Each continuation must be 1 to {max_words} words. "
                    "Return only the continuations, one per line; do not answer the user."
                ),
            },
            {"role": "user", "content": user_content},
        ]


def _positive_word_limit(value: int | None) -> int:
    if value is None:
        return 1
    return max(1, value)
