from __future__ import annotations

from enum import Enum

from game.characteristic import Characteristic

SECONDS_PER_HOUR = 3600

class ActivityState(Enum):
    """Whether the character is currently awake or asleep."""

    AWAKE = "Awake"
    ASLEEP = "Asleep"


class EnergyLevel(Enum):
    """Discrete energy states based on remaining pool fraction."""

    OPTIMAL = "Optimal"
    ORDINARY = "Ordinary"
    TIRED = "Tired"
    SLEEPY = "Sleepy"


# Thresholds as fractions of max pool (upper bounds, descending order).
# OPTIMAL: 100% -> 75%, ORDINARY: 75% -> 50%, TIRED: 50% -> 25%, SLEEPY: 25% -> 0%
ENERGY_THRESHOLDS: dict[EnergyLevel, float] = {
    EnergyLevel.OPTIMAL: 0.75,
    EnergyLevel.ORDINARY: 0.50,
    EnergyLevel.TIRED: 0.25,
    EnergyLevel.SLEEPY: 0.00,
}

# Recovery rate multipliers when sleeping at each energy level.
# Lower energy = slower recovery (diminishing returns when exhausted).
SLEEP_RECOVERY_RATES: dict[EnergyLevel, float] = {
    EnergyLevel.OPTIMAL: 24/3,
    EnergyLevel.ORDINARY: 24/3,
    EnergyLevel.TIRED: 24/4,
    EnergyLevel.SLEEPY: 24/6,
}

class TraitType(Enum):
    """Character trait archetypes with base waking-day durations."""

    ENDURANCE = Characteristic.by_name("Endurance")
    STAMINA = Characteristic.by_name("Stamina")
    VIGOUR = Characteristic.by_name("Vigour")


BASE_HOURS_BY_TRAIT: dict[TraitType, float] = {
    TraitType.ENDURANCE: 24.0,
    TraitType.STAMINA: 48.0,
    TraitType.VIGOUR: 12.0,
}

class PersonalDay:
    """A character with an energy pool that depletes/recovers over time."""

    def __init__(self, upp_3_characteristic: Characteristic) -> None:
        if upp_3_characteristic not in TraitType._value2member_map_:
            raise ValueError(f"Custom characteristic not yet implemented: {upp_3_characteristic.get_name()}")
        self.trait_type = TraitType(upp_3_characteristic)
        self._max_pool_seconds: int = int(BASE_HOURS_BY_TRAIT[self.trait_type] * SECONDS_PER_HOUR)
        self._current_pool_seconds: float = float(self._max_pool_seconds)
        self._energy_level: EnergyLevel = EnergyLevel.OPTIMAL
        self._activity_state: ActivityState = ActivityState.AWAKE

    @property
    def max_pool_seconds(self) -> int:
        """Maximum energy pool capacity in seconds."""
        return self._max_pool_seconds

    @property
    def current_pool_seconds(self) -> float:
        """Current energy pool value in seconds."""
        return self._current_pool_seconds

    @property
    def pool_fraction(self) -> float:
        """Current pool as a fraction of maximum (0.0 to 1.0)."""
        if self._max_pool_seconds == 0:
            return 0.0
        return self._current_pool_seconds / self._max_pool_seconds

    @property
    def energy_level(self) -> EnergyLevel:
        """Current energy level based on pool fraction."""
        return self._energy_level

    @property
    def activity_state(self) -> ActivityState:
        """Current activity state (awake or asleep)."""
        return self._activity_state

    def set_activity_state(self, state: ActivityState) -> None:
        """Change the character's activity state."""
        self._activity_state = state

    def set_max_pool(self, seconds: int) -> None:
        """Set maximum pool capacity and reset current pool to full."""
        self._max_pool_seconds = seconds
        self._current_pool_seconds = float(seconds)
        self._update_energy_level()

    def apply_flux(self, flux_hours: float) -> None:
        """Apply a flux modifier to the max pool (e.g., from dice rolls)."""
        new_max = self._max_pool_seconds + int(flux_hours * SECONDS_PER_HOUR)
        self.set_max_pool(max(SECONDS_PER_HOUR, new_max))  # Minimum 1 hour

    def _update_energy_level(self) -> None:
        """Recalculate energy level from current pool fraction."""
        fraction = self.pool_fraction
        for level, threshold in ENERGY_THRESHOLDS.items():
            if fraction >= threshold:
                self._energy_level = level
                return
        self._energy_level = EnergyLevel.SLEEPY

    def _deplete(self, seconds: float) -> None:
        """Deplete the energy pool (time spent awake)."""
        self._current_pool_seconds = max(0.0, self._current_pool_seconds - seconds)
        self._update_energy_level()

    def _recover(self, seconds: float) -> None:
        """Recover energy (time spent asleep), scaled by current energy level."""
        rate = SLEEP_RECOVERY_RATES[self._energy_level]
        recovery = seconds * rate
        self._current_pool_seconds = min(
            float(self._max_pool_seconds),
            self._current_pool_seconds + recovery,
        )
        self._update_energy_level()

    def pass_time(self, seconds: float) -> None:
        """
        Advance time for the character, depleting or recovering based on activity state.

        Args:
            seconds: Duration of time that has passed.
        """
        if self._activity_state is ActivityState.AWAKE:
            self._deplete(seconds)
        elif self._activity_state is ActivityState.ASLEEP:
            self._recover(seconds)

    def __repr__(self) -> str:
        hours = self._current_pool_seconds / SECONDS_PER_HOUR
        max_hours = self._max_pool_seconds / SECONDS_PER_HOUR
        return (
            f"Character({self.trait_type.name}: "
            f"{hours:.1f}/{max_hours:.1f}h, "
            f"{self._activity_state.value}, {self._energy_level.value})"
        )