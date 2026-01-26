"""Sandbox for testing and demonstrating the t5humanise package."""

from __future__ import annotations

import sys
from pathlib import Path

# Add the src directory to sys.path for local development
_src_path = Path(__file__).parent.parent.parent.parent / "src"
if str(_src_path) not in sys.path:
    sys.path.insert(0, str(_src_path))

# Now we can import with full IDE support
from t5humanise.chance.dice import D, Outcome  # noqa: E402


def format_outcome(outcome: Outcome, label: str = "") -> str:
    """Format an Outcome tuple for display."""
    total, dice, feedback = outcome
    prefix = f"{label}: " if label else ""
    dice_str = ", ".join(str(d) for d in dice) if dice else "none"
    return f"{prefix}Total={total}, Dice=[{dice_str}], Feedback={feedback!r}"


def demo_standard_rolls() -> None:
    """Demonstrate standard dice rolling with detailed output."""
    print("=== Standard Dice Rolls (Detailed) ===")

    # Quick class method for common rolls
    print(f"2D6 simple: {D.roll_nd(2)}")

    # Detailed output
    outcome = D.roll_nd_detailed(2)
    print(format_outcome(outcome, "2D6 detailed"))

    outcome = D.roll_nd_detailed(4)
    print(format_outcome(outcome, "4D6 detailed"))

    outcome = D.roll_nd_detailed(6)
    print(format_outcome(outcome, "6D6 detailed"))

    # Instance-based approach
    dice_3d = D(n=3)
    print(f"\n3D6 instance: {dice_3d}")
    for i in range(3):
        total, per_die, feedback = dice_3d.roll_detailed()
        print(f"  Roll {i + 1}: {total} from {per_die} - {feedback}")
    print()


def demo_flux_rolls() -> None:
    """Demonstrate flux roll variants with detailed output."""
    print("=== Flux Rolls (Detailed) ===")

    print("Flux (range -5 to +5):")
    for _ in range(5):
        outcome = D.flux_detailed()
        print(f"  {format_outcome(outcome)}")

    print("\nGood Flux (range 0 to +5):")
    for _ in range(5):
        outcome = D.good_flux_detailed()
        print(f"  {format_outcome(outcome)}")

    print("\nBad Flux (range -5 to 0):")
    for _ in range(5):
        outcome = D.bad_flux_detailed()
        print(f"  {format_outcome(outcome)}")
    print()


def demo_dd_roll() -> None:
    """Demonstrate DD (two-digit concatenation) rolls with detailed output."""
    print("=== DD Rolls (Detailed) ===")

    for _ in range(8):
        outcome = D.dd_detailed()
        print(f"  {format_outcome(outcome)}")
    print()


def demo_task_rolls() -> None:
    """Demonstrate task-based difficulty rolls with detailed output."""
    print("=== Task Difficulty Rolls (Detailed) ===")

    for diff in D.Difficulties:
        if diff == D.Difficulties.AUTOMATIC:
            outcome = D.task_detailed(diff)
            print(f"{diff.name:20} ({diff}D6): {format_outcome(outcome)}")
        else:
            outcome = D.task_detailed(diff)
            print(f"{diff.name:20} ({diff}D6): {format_outcome(outcome)}")
    print()


def demo_haste_modifiers() -> None:
    """Demonstrate haste modifiers on task difficulty with detailed output."""
    print("=== Haste Modifiers (Detailed) ===")

    base_difficulty = D.Difficulties.AVERAGE

    for haste in D.Haste:
        effective_dice = max(0, base_difficulty + haste)
        outcome = D.task_detailed(base_difficulty, haste)
        total, dice, feedback = outcome
        print(
            f"AVERAGE + {haste.name:12} = {effective_dice}D6 -> "
            f"Total={total}, Dice={dice}, Feedback={feedback!r}"
        )
    print()


def demo_special_feedback() -> None:
    """Demonstrate various feedback scenarios by forcing specific dice outcomes.

    Note: This uses internal methods to show feedback for specific dice patterns
    that might be rare in random rolls.
    """
    print("=== Feedback Examples (Simulated Patterns) ===")

    # Create a dice roller instance to access feedback generation
    roller = D(n=4)

    # Simulate various patterns and show their feedback
    patterns = [
        ((1, 1, 1, 1), "All ones"),
        ((6, 6, 6, 6), "All sixes"),
        ((3, 3, 3, 3), "All threes"),
        ((1, 6, 1, 6), "Mixed 1s and 6s (equal)"),
        ((1, 1, 6, 6), "Mixed 1s and 6s (equal, grouped)"),
        ((1, 6, 6, 6), "One 1, three 6s"),
        ((1, 1, 1, 6), "Three 1s, one 6"),
        ((1, 2, 3, 4), "Small straight"),
        ((2, 3, 4, 5), "Small straight (middle)"),
        ((3, 3, 3, 5), "Three of a kind"),
        ((2, 2, 5, 5), "Two pair"),
        ((1, 1, 1, 1), "Minimum roll (4D6)"),
        ((6, 6, 6, 6), "Maximum roll (4D6)"),
    ]

    for dice_pattern, description in patterns:
        total = roller._compute_total(dice_pattern)
        feedback = roller._generate_feedback(dice_pattern, total)
        print(f"  {description:35} {dice_pattern} -> Total={total}, {feedback!r}")
    print()


def demo_many_rolls() -> None:
    """Roll many times to see variety of feedback messages."""
    print("=== Random Rolls Seeking Interesting Feedback ===")

    interesting_rolls: list[tuple[Outcome, str]] = []

    # Roll many times and collect interesting ones
    for _ in range(100):
        outcome = D.roll_nd_detailed(4)
        total, dice, feedback = outcome
        if feedback != "Normal roll.":
            interesting_rolls.append((outcome, "4D6"))

        outcome = D.roll_nd_detailed(6)
        total, dice, feedback = outcome
        if feedback != "Normal roll.":
            interesting_rolls.append((outcome, "6D6"))

    if interesting_rolls:
        print(f"Found {len(interesting_rolls)} interesting rolls out of 200:")
        for outcome, label in interesting_rolls[:15]:  # Show first 15
            print(f"  {label}: {format_outcome(outcome)}")
    else:
        print("No particularly interesting patterns in this batch.")
    print()


def main() -> None:
    """Run all demonstrations."""
    print("T5 Dice Module Demonstration")
    print("=" * 60)
    print()

    demo_standard_rolls()
    demo_flux_rolls()
    demo_dd_roll()
    demo_task_rolls()
    demo_haste_modifiers()
    demo_special_feedback()
    demo_many_rolls()


if __name__ == "__main__":
    main()
