"""DifficultyManager — postupné zvyšování obtížnosti přes rychlost vlků.

Každých DIFFICULTY_RAMP_INTERVAL sekund zvedne ``session.wolf_speed_multiplier``
o DIFFICULTY_SPEED_INCREMENT (cap na DIFFICULTY_SPEED_MAX) a inkrementuje
``session.difficulty_level``.

DŮLEŽITÉ: NEMĚNÍ POČET VLKŮ — ten je konstantně WOLF_COUNT po celou hru.
"""
from __future__ import annotations

from game import settings
from game.session import GameSession


class DifficultyManager:
    def __init__(self) -> None:
        self._time_to_next_ramp = settings.DIFFICULTY_RAMP_INTERVAL

    def update(self, dt: float, session: GameSession) -> None:
        """Spravuje časovač a aplikuje ramp na multiplikátor rychlosti vlků."""
        self._time_to_next_ramp -= dt

        if self._time_to_next_ramp <= 0:
            interval = settings.DIFFICULTY_RAMP_INTERVAL
            ramps = int(-self._time_to_next_ramp // interval) + 1
            session.difficulty_level += ramps
            session.wolf_speed_multiplier = min(
                session.wolf_speed_multiplier
                + ramps * settings.DIFFICULTY_SPEED_INCREMENT,
                settings.DIFFICULTY_SPEED_MAX,
            )
            self._time_to_next_ramp += ramps * interval
