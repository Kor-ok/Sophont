"""Seeded pseudo-random number generation with counter-based reproducibility.

This module provides a deterministic random number generator that can reproduce
sequences given a seed and counter value. Useful for:
- Reproducing dice roll history
- Peeking at future rolls without consuming them
- Testing with deterministic outcomes
"""

from __future__ import annotations

from typing import Optional

from typing_extensions import TypeAlias

Seed: TypeAlias = int
"""The initial seed value for the RNG."""

Counter: TypeAlias = int
"""The number of values consumed from the RNG stream."""


class SeededRNG:
    """A seeded pseudo-random number generator with counter tracking.

    Uses a linear congruential generator (LCG) for simplicity and speed.
    The counter allows reproducing any point in the sequence.

    Attributes:
        seed: The initial seed value.
        counter: The number of values consumed from the stream.

    Example:
        >>> rng = SeededRNG(seed=12345)
        >>> values = [rng.randint(1, 6) for _ in range(5)]
        >>> print(rng.counter)  # 5

        # Reproduce from the same point
        >>> rng2 = SeededRNG(seed=12345)
        >>> same_values = [rng2.randint(1, 6) for _ in range(5)]
        >>> assert values == same_values

        # Peek at position 3 without consuming
        >>> peeked = SeededRNG.peek_at(seed=12345, position=3, low=1, high=6)
    """

    # LCG parameters (same as MINSTD)
    _MULTIPLIER = 48271
    _MODULUS = 2**31 - 1

    def __init__(self, seed: Optional[Seed] = None) -> None:
        """Initialize the RNG with a seed.

        Args:
            seed: The seed value. If None, uses a time-based seed.
        """
        if seed is None:
            import time

            seed = int(time.time() * 1000) & 0x7FFFFFFF
        self._initial_seed = seed
        self._state = seed if seed != 0 else 1  # LCG can't use 0
        self._counter = 0

    @property
    def seed(self) -> Seed:
        """The initial seed used for this RNG."""
        return self._initial_seed

    @property
    def counter(self) -> Counter:
        """The number of random values consumed."""
        return self._counter

    def _next_state(self) -> int:
        """Advance the internal state and return a raw value."""
        self._state = (self._state * self._MULTIPLIER) % self._MODULUS
        self._counter += 1
        return self._state

    def _raw_float(self) -> float:
        """Return a float in [0, 1)."""
        return self._next_state() / self._MODULUS

    def randint(self, low: int, high: int) -> int:
        """Return a random integer in [low, high] inclusive.

        Args:
            low: The minimum value (inclusive).
            high: The maximum value (inclusive).

        Returns:
            A random integer between low and high.
        """
        if low > high:
            low, high = high, low
        range_size = high - low + 1
        return low + int(self._raw_float() * range_size)

    def reset(self) -> None:
        """Reset the RNG to its initial state."""
        self._state = self._initial_seed if self._initial_seed != 0 else 1
        self._counter = 0

    def set_counter(self, position: Counter) -> None:
        """Fast-forward or rewind to a specific counter position.

        Args:
            position: The counter position to move to (0-based).
        """
        self.reset()
        for _ in range(position):
            self._next_state()

    def fork(self) -> SeededRNG:
        """Create a copy of this RNG at the current position.

        Returns:
            A new SeededRNG with the same seed and counter.
        """
        new_rng = SeededRNG(self._initial_seed)
        new_rng.set_counter(self._counter)
        return new_rng

    def peek(self, low: int, high: int, offset: int = 0) -> int:
        """Peek at a future value without consuming it.

        Args:
            low: The minimum value (inclusive).
            high: The maximum value (inclusive).
            offset: How many positions ahead to peek (0 = next value).

        Returns:
            The value that would be generated at the given offset.
        """
        # Save current state
        saved_state = self._state
        saved_counter = self._counter

        # Fast-forward
        for _ in range(offset):
            self._next_state()

        result = self.randint(low, high)

        # Restore state
        self._state = saved_state
        self._counter = saved_counter

        return result

    def peek_sequence(self, low: int, high: int, count: int, offset: int = 0) -> tuple[int, ...]:
        """Peek at a sequence of future values without consuming them.

        Args:
            low: The minimum value (inclusive).
            high: The maximum value (inclusive).
            count: Number of values to peek.
            offset: How many positions ahead to start (0 = next value).

        Returns:
            Tuple of values that would be generated.
        """
        # Save current state
        saved_state = self._state
        saved_counter = self._counter

        # Fast-forward to offset
        for _ in range(offset):
            self._next_state()

        # Collect values
        result = tuple(self.randint(low, high) for _ in range(count))

        # Restore state
        self._state = saved_state
        self._counter = saved_counter

        return result

    @classmethod
    def peek_at(
        cls, seed: Seed, position: Counter, low: int, high: int, count: int = 1
    ) -> tuple[int, ...]:
        """Peek at values at a specific position without creating a persistent RNG.

        Args:
            seed: The seed value.
            position: The counter position to read from.
            low: The minimum value (inclusive).
            high: The maximum value (inclusive).
            count: Number of values to read.

        Returns:
            Tuple of values at the given position.
        """
        rng = cls(seed)
        rng.set_counter(position)
        return tuple(rng.randint(low, high) for _ in range(count))

    @classmethod
    def reproduce_sequence(
        cls, seed: Seed, start: Counter, end: Counter, low: int, high: int
    ) -> tuple[int, ...]:
        """Reproduce a range of values from the sequence.

        Args:
            seed: The seed value.
            start: The starting counter position (inclusive).
            end: The ending counter position (exclusive).
            low: The minimum value (inclusive).
            high: The maximum value (inclusive).

        Returns:
            Tuple of values from start to end.
        """
        if end <= start:
            return ()
        return cls.peek_at(seed, start, low, high, count=end - start)

    def get_state(self) -> tuple[Seed, Counter]:
        """Get the current state for later reproduction.

        Returns:
            Tuple of (seed, counter) that can be used to reproduce from this point.
        """
        return (self._initial_seed, self._counter)

    def __repr__(self) -> str:
        return f"SeededRNG(seed={self._initial_seed}, counter={self._counter})"


# Module-level default RNG instance (can be replaced by user)
_default_rng: Optional[SeededRNG] = None


def get_default_rng() -> SeededRNG:
    """Get the module-level default RNG, creating one if needed."""
    global _default_rng
    if _default_rng is None:
        _default_rng = SeededRNG()
    return _default_rng


def set_default_rng(rng: Optional[SeededRNG]) -> None:
    """Set the module-level default RNG.

    Args:
        rng: The RNG to use as default, or None to clear.
    """
    global _default_rng
    _default_rng = rng


def set_seed(seed: Seed) -> SeededRNG:
    """Set the default RNG to a new instance with the given seed.

    Args:
        seed: The seed value.

    Returns:
        The new default RNG.
    """
    global _default_rng
    _default_rng = SeededRNG(seed)
    return _default_rng


def randint(low: int, high: int) -> int:
    """Generate a random integer using the default RNG.

    Args:
        low: The minimum value (inclusive).
        high: The maximum value (inclusive).

    Returns:
        A random integer between low and high.
    """
    return get_default_rng().randint(low, high)


def get_state() -> tuple[Seed, Counter]:
    """Get the current state of the default RNG."""
    return get_default_rng().get_state()
