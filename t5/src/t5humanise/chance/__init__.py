"""Chance and randomness utilities for Traveller 5.

This package provides dice rolling and pseudo-random number generation
with support for reproducibility via seeding and counter tracking.
"""

from t5humanise.chance.dice import (
    D,
    Feedback,
    Outcome,
    PerDieResults,
    RollEvent,
    RollEventHandler,
    RollEventType,
    TotalRollResult,
    clear_event_handlers,
    register_event_handler,
    unregister_event_handler,
)
from t5humanise.chance.pseudo_random import (
    Counter,
    Seed,
    SeededRNG,
    get_default_rng,
    get_state,
    randint,
    set_default_rng,
    set_seed,
)

__all__ = [
    # Dice
    "D",
    "Feedback",
    "Outcome",
    "PerDieResults",
    "RollEvent",
    "RollEventHandler",
    "RollEventType",
    "TotalRollResult",
    "clear_event_handlers",
    "register_event_handler",
    "unregister_event_handler",
    # Pseudo-random
    "Counter",
    "Seed",
    "SeededRNG",
    "get_default_rng",
    "get_state",
    "randint",
    "set_default_rng",
    "set_seed",
]
