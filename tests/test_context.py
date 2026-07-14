from synarmo.context import ContextAssembler
from synarmo.memory import UserMemory


def test_context_assembler_trims_without_losing_field_labels() -> None:
    assembler = ContextAssembler(max_chars=90)
    context = " ".join(f"detail-{index}" for index in range(20))

    assembled = assembler.assemble(
        text="I want to",
        context=context,
        memory=UserMemory(
            profile="test",
            style_summary="warm and direct",
            preferences={"tone": "plain"},
        ),
    )

    assert len(assembled) <= 90
    assert "Current context:" in assembled
    assert assembled.endswith("Current typed text: I want to")


def test_context_assembler_preserves_current_typed_text_when_text_is_long() -> None:
    assembler = ContextAssembler(max_chars=45)

    assembled = assembler.assemble(
        text="I want to explain this carefully",
        context="At home",
        memory=UserMemory(profile="test"),
    )

    assert assembled.startswith("Current typed text:")
    assert assembled.endswith("explain this carefully")


def test_context_assembler_preserves_typed_trailing_space() -> None:
    assembled = ContextAssembler().assemble(
        text="I want ",
        context=None,
        memory=UserMemory(profile="test"),
    )

    assert assembled.endswith("Current typed text: I want ")
