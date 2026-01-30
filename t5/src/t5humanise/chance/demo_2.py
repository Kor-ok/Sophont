"""Sandbox for testing and demonstrating the t5humanise package."""

from __future__ import annotations

import sys
from pathlib import Path

# Add the src directory to sys.path for local development
_src_path = Path(__file__).parent / "src"
if str(_src_path) not in sys.path:
    sys.path.insert(0, str(_src_path))

# Now we can import with full IDE support
from t5humanise.chance.dice import (  # noqa: E402
    D,
    Outcome,
    RollEvent,
    RollEventType,
    clear_event_handlers,
    register_event_handler,
)
from t5humanise.chance.pseudo_random import SeededRNG, set_seed  # noqa: E402


def format_outcome(outcome: Outcome, label: str = "") -> str:
    """Format an Outcome tuple for display."""
    total, dice, feedback = outcome
    prefix = f"{label}: " if label else ""
    dice_str = ", ".join(str(d) for d in dice) if dice else "none"
    return f"{prefix}Total={total}, Dice=[{dice_str}], Feedback={feedback!r}"


# -----------------------------------------------------------------------------
# Event Handlers Demo
# -----------------------------------------------------------------------------


def demo_event_handlers() -> None:
    """Demonstrate the event system for DANGEROUS/DESTRUCTIVE haste."""
    print("=== Event Handlers Demo ===")

    # Track events that occurred
    events_received: list[RollEvent] = []

    def on_dangerous(event: RollEvent) -> None:
        events_received.append(event)
        print("  [EVENT] DANGEROUS haste triggered!")
        print(f"          Outcome: {event.roll_outcome}")
        print(f"          Metadata: {event.metadata}")

    def on_destructive(event: RollEvent) -> None:
        events_received.append(event)
        print("  [EVENT] DESTRUCTIVE haste triggered!")
        print(f"          Outcome: {event.roll_outcome}")
        print(f"          Metadata: {event.metadata}")

    def on_critical_success(event: RollEvent) -> None:
        events_received.append(event)
        print("  [EVENT] CRITICAL SUCCESS! All 1s!")
        print(f"          Outcome: {event.roll_outcome}")

    def on_critical_failure(event: RollEvent) -> None:
        events_received.append(event)
        print("  [EVENT] CRITICAL FAILURE! All 6s!")
        print(f"          Outcome: {event.roll_outcome}")

    # Register handlers
    register_event_handler(RollEventType.DANGEROUS_HASTE, on_dangerous)
    register_event_handler(RollEventType.DESTRUCTIVE_HASTE, on_destructive)
    register_event_handler(RollEventType.CRITICAL_SUCCESS, on_critical_success)
    register_event_handler(RollEventType.CRITICAL_FAILURE, on_critical_failure)

    print("\nRolling with DANGEROUS haste (EXTRA_HASTY + side effect):")
    result = D.task(
        D.Difficulties.AVERAGE,
        D.Haste.EXTRA_HASTY,
        side_effect=D.HasteSideEffect.DANGEROUS,
    )
    print(f"  Result: {result}")

    print("\nRolling with DESTRUCTIVE haste (EXTRA_HASTY + side effect):")
    result = D.task(
        D.Difficulties.DIFFICULT,
        D.Haste.EXTRA_HASTY,
        side_effect=D.HasteSideEffect.DESTRUCTIVE,
    )
    print(f"  Result: {result}")

    print("\nRolling normally (no side effects):")
    result = D.task(D.Difficulties.AVERAGE, D.Haste.HASTY)
    print(f"  Result: {result}")

    print(f"\nTotal events received: {len(events_received)}")

    # Clean up handlers
    clear_event_handlers()
    print()


# -----------------------------------------------------------------------------
# Seeded RNG Demo
# -----------------------------------------------------------------------------


def demo_seeded_rng() -> None:
    """Demonstrate seeded pseudo-random number generation."""
    print("=== Seeded RNG Demo ===")

    # Create a seeded RNG
    seed = 42
    rng = SeededRNG(seed=seed)
    print(f"Created RNG with seed={seed}")

    # Roll some dice
    print("\nFirst sequence of 5 rolls (2D6 each):")
    results1 = []
    for i in range(5):
        outcome = D.roll_nd_detailed(2, rng=rng)
        results1.append(outcome)
        print(f"  Roll {i + 1} (counter={rng.counter - 2}): {format_outcome(outcome)}")

    # Reset and reproduce
    print("\nResetting RNG and reproducing the same sequence:")
    rng.reset()
    results2 = []
    for i in range(5):
        outcome = D.roll_nd_detailed(2, rng=rng)
        results2.append(outcome)
        total1, dice1, _ = results1[i]
        total2, dice2, _ = outcome
        match = "✓" if dice1 == dice2 else "✗"
        print(f"  Roll {i + 1}: {dice2} {match}")

    # Demonstrate peeking
    print("\nPeeking at future values without consuming:")
    rng2 = SeededRNG(seed=12345)
    print(f"  Current counter: {rng2.counter}")
    peeked = rng2.peek_sequence(1, 6, count=5)
    print(f"  Peeked next 5 values: {peeked}")
    print(f"  Counter after peek: {rng2.counter} (unchanged)")

    # Now actually roll and verify
    actual = tuple(rng2.randint(1, 6) for _ in range(5))
    print(f"  Actual next 5 values: {actual}")
    print(f"  Match: {'✓' if peeked == actual else '✗'}")
    print()


def demo_reproducible_history() -> None:
    """Demonstrate reproducing dice roll history."""
    print("=== Reproducible History Demo ===")

    seed = 98765
    rng = SeededRNG(seed=seed)

    print(f"Rolling 10 task checks with seed={seed}:")
    history: list[tuple[int, Outcome]] = []

    for i in range(10):
        counter_before = rng.counter
        outcome = D.task_detailed(D.Difficulties.AVERAGE, rng=rng)
        history.append((counter_before, outcome))
        total, dice, _ = outcome
        print(f"  [{counter_before:2}] Roll {i + 1}: {dice} = {total}")

    # Reproduce a specific roll from history
    print("\nReproducing roll #5 from history:")
    counter_at_5, original_outcome = history[4]
    print(f"  Original: counter={counter_at_5}, outcome={original_outcome[1]}")

    # Use peek_at to reproduce
    reproduced_dice = SeededRNG.peek_at(seed, counter_at_5, 1, 6, count=2)
    print(f"  Reproduced dice: {reproduced_dice}")
    print(f"  Match: {'✓' if reproduced_dice == original_outcome[1] else '✗'}")
    print()


def demo_module_default_rng() -> None:
    """Demonstrate using the module-level default RNG."""
    print("=== Module Default RNG Demo ===")

    # Set a seed for the module default
    rng = set_seed(11111)
    print("Set module default seed to 11111")

    # All rolls will use this seed now (unless rng= is specified)
    print("\nRolling with module default RNG:")
    for i in range(5):
        result = D.roll_nd(2)
        print(f"  Roll {i + 1} (counter={rng.counter}): {result}")

    # Reset and verify reproducibility
    print("\nResetting and reproducing:")
    rng.reset()
    for i in range(5):
        result = D.roll_nd(2)
        print(f"  Roll {i + 1} (counter={rng.counter}): {result}")
    print()


def main() -> None:
    """Run all demonstrations."""
    print("T5 Dice Module - Advanced Features Demo")
    print("=" * 60)
    print()

    demo_event_handlers()
    demo_seeded_rng()
    demo_reproducible_history()
    demo_module_default_rng()


if __name__ == "__main__":
    main()
