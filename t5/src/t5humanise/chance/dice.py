"""Dice rolling utilities for Traveller 5 (T5).

This module provides the `D` class for rolling dice according to T5 rules,
including standard rolls, task difficulty modifiers, flux rolls, and DD rolls.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, IntEnum, auto
from typing import TYPE_CHECKING, Callable, Optional

from t5humanise.chance.pseudo_random import SeededRNG, get_default_rng
from typing_extensions import TypeAlias

if TYPE_CHECKING:
    pass

TotalRollResult: TypeAlias = int
PerDieResults: TypeAlias = tuple[int, ...]
"""Values of individual dice rolled."""
Feedback: TypeAlias = str
"""Descriptive feedback about the roll outcome and properties of the throw if any."""

Outcome: TypeAlias = tuple[TotalRollResult, PerDieResults, Feedback]


# -----------------------------------------------------------------------------
# Roll Events - External event system for side effects
# -----------------------------------------------------------------------------


class RollEventType(Enum):
    """Types of events that can be triggered during dice rolls."""

    DANGEROUS_HASTE = auto()
    """The roll was made with DANGEROUS haste - may injure the task user."""

    DESTRUCTIVE_HASTE = auto()
    """The roll was made with DESTRUCTIVE haste - may damage equipment."""

    CRITICAL_SUCCESS = auto()
    """Placeholder: The roll achieved a critical success (all 1s, etc.)."""

    CRITICAL_FAILURE = auto()
    """Placeholder: The roll achieved a critical failure (all 6s, etc.)."""

    # Add future event types here


@dataclass
class RollEvent:
    """An event generated during a dice roll that may require external handling.

    Attributes:
        event_type: The type of event that occurred.
        roll_outcome: The outcome of the roll that triggered the event.
        haste: The haste level used (if applicable).
        difficulty: The difficulty level used (if applicable).
        metadata: Additional context for the event handler.
    """

    event_type: RollEventType
    roll_outcome: Optional[Outcome] = None
    haste: Optional[D.Haste] = None
    difficulty: Optional[D.Difficulties] = None
    metadata: dict = field(default_factory=dict)


# Type alias for event handler callbacks
RollEventHandler: TypeAlias = Callable[[RollEvent], None]

# Module-level event handlers registry
_event_handlers: dict[RollEventType, list[RollEventHandler]] = {}


def register_event_handler(event_type: RollEventType, handler: RollEventHandler) -> None:
    """Register a handler for a specific roll event type.

    Args:
        event_type: The type of event to handle.
        handler: A callable that receives a RollEvent.

    Example:
        >>> def on_dangerous(event: RollEvent):
        ...     print(f"Dangerous roll! Outcome: {event.roll_outcome}")
        >>> register_event_handler(RollEventType.DANGEROUS_HASTE, on_dangerous)
    """
    if event_type not in _event_handlers:
        _event_handlers[event_type] = []
    _event_handlers[event_type].append(handler)


def unregister_event_handler(event_type: RollEventType, handler: RollEventHandler) -> bool:
    """Unregister a handler for a specific roll event type.

    Args:
        event_type: The type of event.
        handler: The handler to remove.

    Returns:
        True if the handler was found and removed, False otherwise.
    """
    if event_type in _event_handlers and handler in _event_handlers[event_type]:
        _event_handlers[event_type].remove(handler)
        return True
    return False


def clear_event_handlers(event_type: Optional[RollEventType] = None) -> None:
    """Clear event handlers.

    Args:
        event_type: The specific event type to clear, or None to clear all.
    """
    if event_type is None:
        _event_handlers.clear()
    elif event_type in _event_handlers:
        _event_handlers[event_type].clear()


def _dispatch_event(event: RollEvent) -> None:
    """Dispatch an event to all registered handlers."""
    handlers = _event_handlers.get(event.event_type, [])
    for handler in handlers:
        handler(event)


class D:
    """A dice roller supporting T5 dice mechanics.

    Supports standard xD6 rolls, difficulty-based task rolls with optional
    haste modifiers, flux rolls, and DD (percentile-style) rolls.

    Examples:
        >>> D.roll_nd(2)           # Roll 2D6
        >>> D.flux()               # Roll flux (-5 to +5)
        >>> D.good_flux()          # Roll good flux (0 to +5)
        >>> D.bad_flux()           # Roll bad flux (-5 to 0)
        >>> D.dd()                 # Roll DD (11-66)
        >>> D.task(D.Difficulties.AVERAGE)  # Roll 2D6 for an Average task
        >>> D(n=3).roll()          # Roll 3D6
    """

    class Difficulties(IntEnum):
        """Defines the number of dice to roll based on the selected Difficulty.

        The numeric value corresponds to how many D6 are rolled for task checks.
        """

        AUTOMATIC = 0
        EASY = 1
        AVERAGE = 2
        DIFFICULT = 3
        FORMIDABLE = 4
        STAGGERING = 5
        HOPELESS = 6
        IMPOSSIBLE = 7
        BEYOND_IMPOSSIBLE = 8

    class Haste(IntEnum):
        """Modifier applied to difficulty level based on time pressure.

        Positive values increase difficulty (more dice), negative values decrease it.

        Note: EXTRA_HASTY, DANGEROUS, and DESTRUCTIVE all add +2 dice, but have
        different semantic meanings. Use the `haste_flags` property or pass
        `HasteSideEffect` separately for side effect handling.

        Special haste levels (side effects handled via events):
            - DANGEROUS: May injure the task user.
            - DESTRUCTIVE: May damage an associated device.
        """

        CAUTIOUS = -1
        HASTY = +1
        EXTRA_HASTY = +2
        # DANGEROUS and DESTRUCTIVE use +2 but are tracked via HasteSideEffect

    class HasteSideEffect(Enum):
        """Side effects that may accompany a haste modifier.

        These are separate from the dice modifier value and trigger events.
        """

        NONE = auto()
        """No side effects."""

        DANGEROUS = auto()
        """May injure the task user."""

        DESTRUCTIVE = auto()
        """May damage an associated device."""

    class Type(Enum):
        """The type of dice roll to perform."""

        STANDARD = auto()
        """Roll N dice and sum the results."""

        FLUX = auto()
        """Roll 2D6, subtract second from first. Range: -5 to +5."""

        GOOD_FLUX = auto()
        """Roll 2D6, subtract smaller from larger. Range: 0 to +5."""

        BAD_FLUX = auto()
        """Roll 2D6, subtract larger from smaller. Range: -5 to 0."""

        DD = auto()
        """Roll 2D6 and concatenate digits. Range: 11-66."""

    def __init__(
        self,
        n: Optional[int] = None,
        difficulty: Optional[Difficulties] = None,
        haste: Optional[Haste] = None,
        side_effect: Optional[HasteSideEffect] = None,
        roll_type: Type = Type.STANDARD,
        rng: Optional[SeededRNG] = None,
    ) -> None:
        """Initialize a dice roller.

        Args:
            n: Explicit number of dice to roll. Takes precedence over difficulty.
            difficulty: Task difficulty level (determines base number of dice).
            haste: Haste modifier applied to difficulty.
            side_effect: Optional side effect (DANGEROUS, DESTRUCTIVE) that triggers events.
            roll_type: The type of roll (STANDARD, FLUX, GOOD_FLUX, BAD_FLUX, DD).
            rng: Optional SeededRNG instance. If None, uses the module default.

        If no arguments are provided, defaults to 2D6 standard roll.
        """
        self._type = roll_type
        self._haste = haste
        self._side_effect = side_effect or D.HasteSideEffect.NONE
        self._difficulty = difficulty
        self._rng = rng  # None means use default

        # Flux-type rolls always use 2 dice (internally)
        if roll_type in (D.Type.FLUX, D.Type.GOOD_FLUX, D.Type.BAD_FLUX, D.Type.DD):
            self._number_of_dice = 2
            return

        # Explicit dice count takes precedence
        if n is not None:
            self._number_of_dice = max(0, n)
            return

        # Calculate from difficulty and haste
        if difficulty is not None:
            base = int(difficulty)
            if haste is not None:
                base += int(haste)
            # Clamp to valid range
            self._number_of_dice = max(
                D.Difficulties.AUTOMATIC, min(base, D.Difficulties.BEYOND_IMPOSSIBLE)
            )
        else:
            # Default: 2D6
            self._number_of_dice = 2

    @property
    def n(self) -> int:
        """The number of dice configured for this roller."""
        return self._number_of_dice

    @property
    def roll_type(self) -> Type:
        """The type of roll this dice roller will perform."""
        return self._type

    @property
    def haste(self) -> Optional[Haste]:
        """The haste modifier used for this roller, if any."""
        return self._haste

    @property
    def side_effect(self) -> HasteSideEffect:
        """The side effect associated with this roll."""
        return self._side_effect

    @property
    def difficulty(self) -> Optional[Difficulties]:
        """The difficulty level used for this roller, if any."""
        return self._difficulty

    def _get_rng(self) -> SeededRNG:
        """Get the RNG to use for this roll."""
        return self._rng if self._rng is not None else get_default_rng()

    def roll(self) -> int:
        """Perform the dice roll and return the result.

        Returns:
            The result of the roll based on the configured roll type.
        """
        total, _, _ = self.roll_detailed()
        return total

    def roll_detailed(self) -> Outcome:
        """Perform the dice roll and return detailed results.

        Also dispatches any events triggered by the roll configuration
        (e.g., DANGEROUS or DESTRUCTIVE haste).

        Returns:
            An Outcome tuple containing:
                - TotalRollResult: The computed result (sum, difference, etc.)
                - PerDieResults: Tuple of individual die values
                - Feedback: Descriptive string about the roll outcome
        """
        dice = self._roll_dice()
        total = self._compute_total(dice)
        feedback = self._generate_feedback(dice, total)
        outcome = (total, dice, feedback)

        # Dispatch events for special conditions
        self._dispatch_roll_events(outcome)

        return outcome

    def _dispatch_roll_events(self, outcome: Outcome) -> None:
        """Dispatch events based on roll configuration and outcome.

        Override or extend this method to add custom event triggers.
        """
        # Check for side effects (DANGEROUS, DESTRUCTIVE, etc.)
        if self._side_effect == D.HasteSideEffect.DANGEROUS:
            event = RollEvent(
                event_type=RollEventType.DANGEROUS_HASTE,
                roll_outcome=outcome,
                haste=self._haste,
                difficulty=self._difficulty,
                metadata={
                    "dice_count": self._number_of_dice,
                    "side_effect": self._side_effect,
                },
            )
            _dispatch_event(event)

        elif self._side_effect == D.HasteSideEffect.DESTRUCTIVE:
            event = RollEvent(
                event_type=RollEventType.DESTRUCTIVE_HASTE,
                roll_outcome=outcome,
                haste=self._haste,
                difficulty=self._difficulty,
                metadata={
                    "dice_count": self._number_of_dice,
                    "side_effect": self._side_effect,
                },
            )
            _dispatch_event(event)

        # Check for critical success (all 1s) - placeholder
        total, dice, _ = outcome
        if dice and len(set(dice)) == 1:
            if dice[0] == 1 and len(dice) >= 2:
                event = RollEvent(
                    event_type=RollEventType.CRITICAL_SUCCESS,
                    roll_outcome=outcome,
                    haste=self._haste,
                    difficulty=self._difficulty,
                    metadata={"all_ones": True},
                )
                _dispatch_event(event)
        elif dice[0] == 6 and len(dice) >= 2:
            event = RollEvent(
                event_type=RollEventType.CRITICAL_FAILURE,
                roll_outcome=outcome,
                haste=self._haste,
                difficulty=self._difficulty,
                metadata={"all_sixes": True},
            )
            _dispatch_event(event)

    def _roll_dice(self) -> PerDieResults:
        """Roll the dice and return individual results."""
        if self._number_of_dice == 0:
            return ()
        rng = self._get_rng()
        return tuple(rng.randint(1, 6) for _ in range(self._number_of_dice))

    def _compute_total(self, dice: PerDieResults) -> TotalRollResult:
        """Compute the total based on roll type and dice values."""
        if not dice:
            return 0

        if self._type == D.Type.FLUX:
            # Subtract second from first. Range: -5 to +5
            return dice[0] - dice[1]

        if self._type == D.Type.GOOD_FLUX:
            # Subtract smaller from larger. Range: 0 to +5
            return abs(dice[0] - dice[1])

        if self._type == D.Type.BAD_FLUX:
            # Subtract larger from smaller. Range: -5 to 0
            return -abs(dice[0] - dice[1])

        if self._type == D.Type.DD:
            # Concatenate into a two-digit number. Range: 11-66
            return dice[0] * 10 + dice[1]

        # Standard roll: sum all dice
        return sum(dice)

    def _generate_feedback(self, dice: PerDieResults, total: TotalRollResult) -> Feedback:
        """Generate descriptive feedback based on dice patterns and results.

        Args:
            dice: The individual die results.
            total: The computed total.

        Returns:
            A feedback string describing notable aspects of the roll.
        """
        if not dice:
            return "No dice rolled."

        n = len(dice)

        # Single die has limited feedback
        if n == 1:
            return self._single_die_feedback(dice[0])

        # Analyze dice patterns
        ones = dice.count(1)
        sixes = dice.count(6)
        unique_values = set(dice)

        # Check for special patterns (priority order)
        feedback_parts: list[str] = []

        # All same value patterns
        if len(unique_values) == 1:
            feedback_parts.append(self._all_same_feedback(dice[0], n))
        else:
            # Mixed extreme patterns (1s and 6s together)
            if ones > 0 and sixes > 0:
                feedback_parts.append(self._mixed_extremes_feedback(ones, sixes, n))
            else:
                # Only 1s (but not all)
                if ones > 0:
                    feedback_parts.append(self._partial_ones_feedback(ones, n))
                # Only 6s (but not all)
                if sixes > 0:
                    feedback_parts.append(self._partial_sixes_feedback(sixes, n))

            # Sequential patterns (straights)
            straight = self._check_straight(dice)
            if straight:
                feedback_parts.append(straight)

            # Pairs, triples, etc.
            multiples = self._check_multiples(dice)
            if multiples:
                feedback_parts.append(multiples)

        # Roll-type specific feedback
        type_feedback = self._roll_type_feedback(dice, total)
        if type_feedback:
            feedback_parts.append(type_feedback)

        # Statistical observation
        if self._type == D.Type.STANDARD and n >= 2:
            stat_feedback = self._statistical_feedback(total, n)
            if stat_feedback:
                feedback_parts.append(stat_feedback)

        return (
            " ".join(part for part in feedback_parts if part) if feedback_parts else "Normal roll."
        )

    def _single_die_feedback(self, value: int) -> Feedback:
        """Feedback for a single die roll."""
        if value == 1:
            return "Critical low!"
        if value == 6:
            return "Critical high!"
        return "Normal roll."

    def _all_same_feedback(self, value: int, count: int) -> Feedback:
        """Feedback when all dice show the same value."""
        if value == 1:
            return f"Outstanding! All {count} dice show 1!"
        if value == 6:
            return f"Disastrous! All {count} dice show 6!"
        return f"Remarkable! All {count} dice show {value}!"

    def _mixed_extremes_feedback(self, ones: int, sixes: int, total_dice: int) -> Feedback:
        """Feedback when roll contains both 1s and 6s."""
        if ones + sixes == total_dice:
            # Only 1s and 6s, nothing in between
            if ones == sixes:
                return "Goofy! Equal parts triumph and disaster!"
            elif ones > sixes:
                return "Chaotic luck! More highs than lows!"
            else:
                return "Chaotic doom! More lows than highs!"
        return "Wild swing! Mix of 1s and 6s."

    def _partial_ones_feedback(self, ones: int, total_dice: int) -> Feedback:
        """Feedback for rolls with some (but not all) 1s."""
        if ones >= total_dice // 2 and total_dice >= 2:
            return f"Lucky streak! {ones} of {total_dice} dice are 1s."
        return ""

    def _partial_sixes_feedback(self, sixes: int, total_dice: int) -> Feedback:
        """Feedback for rolls with some (but not all) 6s."""
        if sixes >= total_dice // 2 and total_dice >= 2:
            return f"Unlucky streak! {sixes} of {total_dice} dice are 6s."
        return ""

    def _check_straight(self, dice: PerDieResults) -> Feedback:
        """Check for sequential dice (straights)."""
        if len(dice) < 3:
            return ""

        unique_sorted = sorted(set(dice))

        # Check for consecutive sequence
        if len(unique_sorted) >= 3:
            # Find longest consecutive run
            max_run = 1
            current_run = 1
            for i in range(1, len(unique_sorted)):
                if unique_sorted[i] == unique_sorted[i - 1] + 1:
                    current_run += 1
                    max_run = max(max_run, current_run)
                else:
                    current_run = 1

            if max_run >= 4:
                return "Straight! Four or more in sequence!"
            if max_run == 3 and len(dice) <= 4:
                return "Small straight! Three in sequence."

        return ""

    def _check_multiples(self, dice: PerDieResults) -> Feedback:
        """Check for pairs, triples, etc."""
        if len(dice) < 2:
            return ""

        from collections import Counter

        counts = Counter(dice)
        max_count = max(counts.values())
        num_pairs = sum(1 for c in counts.values() if c >= 2)

        if max_count >= 4:
            value = [k for k, v in counts.items() if v >= 4][0]
            return f"Four of a kind! ({value}s)"
        if max_count == 3:
            value = [k for k, v in counts.items() if v == 3][0]
            if num_pairs >= 2:  # Full house
                return f"Full house! Three {value}s and a pair."
            return f"Three of a kind! ({value}s)"
        if num_pairs >= 2:
            return "Two pair!"

        return ""

    def _roll_type_feedback(self, dice: PerDieResults, total: TotalRollResult) -> Feedback:
        """Generate feedback specific to the roll type."""
        if self._type == D.Type.FLUX:
            if total == 5:
                return "Maximum positive flux!"
            if total == -5:
                return "Maximum negative flux!"
            if total == 0:
                return "Neutral flux."

        if self._type == D.Type.GOOD_FLUX:
            if total == 5:
                return "Maximum good flux!"
            if total == 0:
                return "Zero flux - perfectly balanced."

        if self._type == D.Type.BAD_FLUX:
            if total == -5:
                return "Maximum bad flux!"
            if total == 0:
                return "Zero flux - escaped the worst."

        if self._type == D.Type.DD:
            if dice[0] == dice[1]:
                return f"Doubles! ({dice[0]}{dice[1]})"
            if total == 11:
                return "Minimum DD roll."
            if total == 66:
                return "Maximum DD roll!"

        return ""

    def _statistical_feedback(self, total: TotalRollResult, n: int) -> Feedback:
        """Feedback based on statistical likelihood."""
        # Expected value for nD6 is n * 3.5
        expected = n * 3.5
        min_possible = n
        max_possible = n * 6

        if total == min_possible:
            return "Minimum possible roll!"
        if total == max_possible:
            return "Maximum possible roll!"

        # Extreme deviation (roughly beyond 2 standard deviations)
        # Std dev for nD6 ≈ sqrt(n * 35/12) ≈ 1.71 * sqrt(n)
        std_dev = 1.71 * (n**0.5)
        deviation = abs(total - expected)

        if deviation > 2.5 * std_dev:
            if total < expected:
                return "Exceptionally low roll!"
            return "Exceptionally high roll!"
        if deviation > 2 * std_dev:
            if total < expected:
                return "Very low roll."
            return "Very high roll."

        return ""

    def __repr__(self) -> str:
        if self._type == D.Type.STANDARD:
            return f"D(n={self._number_of_dice})"
        return f"D(roll_type={self._type.name})"

    # -------------------------------------------------------------------------
    # Convenience class methods for common roll patterns
    # -------------------------------------------------------------------------

    @classmethod
    def roll_nd(cls, n: int, rng: Optional[SeededRNG] = None) -> int:
        """Roll N standard D6 and return the sum.

        Args:
            n: Number of dice to roll.
            rng: Optional SeededRNG instance.

        Returns:
            Sum of N D6 rolls.

        Example:
            >>> D.roll_nd(3)  # Roll 3D6
        """
        return cls(n=n, rng=rng).roll()

    @classmethod
    def flux(cls, rng: Optional[SeededRNG] = None) -> int:
        """Roll flux: 1D6 - 1D6.

        Args:
            rng: Optional SeededRNG instance.

        Returns:
            Result in range -5 to +5.
        """
        return cls(roll_type=cls.Type.FLUX, rng=rng).roll()

    @classmethod
    def good_flux(cls, rng: Optional[SeededRNG] = None) -> int:
        """Roll good flux: |1D6 - 1D6|.

        Args:
            rng: Optional SeededRNG instance.

        Returns:
            Result in range 0 to +5.
        """
        return cls(roll_type=cls.Type.GOOD_FLUX, rng=rng).roll()

    @classmethod
    def bad_flux(cls, rng: Optional[SeededRNG] = None) -> int:
        """Roll bad flux: -|1D6 - 1D6|.

        Args:
            rng: Optional SeededRNG instance.

        Returns:
            Result in range -5 to 0.
        """
        return cls(roll_type=cls.Type.BAD_FLUX, rng=rng).roll()

    @classmethod
    def dd(cls, rng: Optional[SeededRNG] = None) -> int:
        """Roll DD: concatenate two D6 digits.

        Args:
            rng: Optional SeededRNG instance.

        Returns:
            Two-digit result in range 11-66.
        """
        return cls(roll_type=cls.Type.DD, rng=rng).roll()

    @classmethod
    def task(
        cls,
        difficulty: Difficulties = Difficulties.AVERAGE,
        haste: Optional[Haste] = None,
        side_effect: Optional[HasteSideEffect] = None,
        rng: Optional[SeededRNG] = None,
    ) -> int:
        """Roll dice for a task check at the given difficulty.

        Args:
            difficulty: The base difficulty level.
            haste: Optional haste modifier.
            side_effect: Optional side effect (DANGEROUS, DESTRUCTIVE) for event handling.
            rng: Optional SeededRNG instance.

        Returns:
            Sum of dice rolled (number of dice = difficulty + haste).

        Example:
            >>> D.task(D.Difficulties.DIFFICULT)  # Roll 3D6
            >>> D.task(D.Difficulties.AVERAGE, D.Haste.EXTRA_HASTY,
            ...        D.HasteSideEffect.DANGEROUS)  # 4D6 with danger
        """
        return cls(difficulty=difficulty, haste=haste, side_effect=side_effect, rng=rng).roll()

    # -------------------------------------------------------------------------
    # Detailed roll convenience methods (return Outcome tuples)
    # -------------------------------------------------------------------------

    @classmethod
    def roll_nd_detailed(cls, n: int, rng: Optional[SeededRNG] = None) -> Outcome:
        """Roll N standard D6 and return detailed results.

        Args:
            n: Number of dice to roll.
            rng: Optional SeededRNG instance.

        Returns:
            Outcome tuple with (total, per-die results, feedback).

        Example:
            >>> total, dice, feedback = D.roll_nd_detailed(3)
        """
        return cls(n=n, rng=rng).roll_detailed()

    @classmethod
    def flux_detailed(cls, rng: Optional[SeededRNG] = None) -> Outcome:
        """Roll flux and return detailed results.

        Args:
            rng: Optional SeededRNG instance.

        Returns:
            Outcome tuple with (result, per-die results, feedback).
        """
        return cls(roll_type=cls.Type.FLUX, rng=rng).roll_detailed()

    @classmethod
    def good_flux_detailed(cls, rng: Optional[SeededRNG] = None) -> Outcome:
        """Roll good flux and return detailed results.

        Args:
            rng: Optional SeededRNG instance.

        Returns:
            Outcome tuple with (result, per-die results, feedback).
        """
        return cls(roll_type=cls.Type.GOOD_FLUX, rng=rng).roll_detailed()

    @classmethod
    def bad_flux_detailed(cls, rng: Optional[SeededRNG] = None) -> Outcome:
        """Roll bad flux and return detailed results.

        Args:
            rng: Optional SeededRNG instance.

        Returns:
            Outcome tuple with (result, per-die results, feedback).
        """
        return cls(roll_type=cls.Type.BAD_FLUX, rng=rng).roll_detailed()

    @classmethod
    def dd_detailed(cls, rng: Optional[SeededRNG] = None) -> Outcome:
        """Roll DD and return detailed results.

        Args:
            rng: Optional SeededRNG instance.

        Returns:
            Outcome tuple with (result, per-die results, feedback).
        """
        return cls(roll_type=cls.Type.DD, rng=rng).roll_detailed()

    @classmethod
    def task_detailed(
        cls,
        difficulty: Difficulties = Difficulties.AVERAGE,
        haste: Optional[Haste] = None,
        side_effect: Optional[HasteSideEffect] = None,
        rng: Optional[SeededRNG] = None,
    ) -> Outcome:
        """Roll dice for a task check and return detailed results.

        Args:
            difficulty: The base difficulty level.
            haste: Optional haste modifier.
            side_effect: Optional side effect (DANGEROUS, DESTRUCTIVE) for event handling.
            rng: Optional SeededRNG instance.

        Returns:
            Outcome tuple with (total, per-die results, feedback).

        Example:
            >>> total, dice, feedback = D.task_detailed(D.Difficulties.DIFFICULT)
        """
        return cls(
            difficulty=difficulty, haste=haste, side_effect=side_effect, rng=rng
        ).roll_detailed()
