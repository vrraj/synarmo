from synarmo.contexts import ContextPresetStore


def test_context_preset_store_saves_and_replaces_case_insensitive_names(tmp_path) -> None:
    store = ContextPresetStore(tmp_path / "contexts.yaml")

    store.save("Doctor's office", "Asking for help at an appointment.")
    store.save("doctor's office", "Asking for a prescription refill.")

    assert store.list()[0].name == "doctor's office"
    assert store.list()[0].text == "Asking for a prescription refill."
