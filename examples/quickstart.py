from synarmo import SynarmoEngine


def main() -> None:
    engine = SynarmoEngine.load(profile="demo")
    suggestions = engine.suggest(
        text="I want to",
        context="Talking with a caregiver at home after lunch.",
    )
    for suggestion in suggestions:
        print(f"{suggestion.text} ({suggestion.score:.2f})")


if __name__ == "__main__":
    main()
