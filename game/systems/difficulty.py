"""DifficultyManager — postupné zvyšování obtížnosti přes rychlost vlků.

# TODO Lane D
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
        # TODO Lane D
        self._time_to_next_ramp = settings.DIFFICULTY_RAMP_INTERVAL

    def update(self, dt: float, session: GameSession) -> None:
        """Spravuje časovač a aplikuje ramp na multiplikátor rychlosti vlků."""
        # TODO Lane D
        pass
