"""ScoreSystem — počítání bodů.

# TODO Lane D
Pravidla:
- ``dog_repels_wolf`` -> +SCORE_PER_WOLF_REPELLED a inkrement ``session.wolves_repelled``
- ``wolf_eats_sheep`` -> žádný score impact (sheep_alive sníží Rules)
- ``tick(dt)`` -> přičítá SCORE_PER_SECOND bodů za sekundu přežití (lineárně dt)
"""
from __future__ import annotations

from game.session import GameSession
from game.systems.collision import CollisionEvent


class ScoreSystem:
    def __init__(self) -> None:
        # TODO Lane D
        self._second_accumulator = 0.0

    def process_events(self, events: list[CollisionEvent],
                       session: GameSession) -> None:
        """Aplikuje skóre podle eventů."""
        # TODO Lane D
        pass

    def tick(self, dt: float, session: GameSession) -> None:
        """Lineárně přičítá SCORE_PER_SECOND bodů za sekundu přežití."""
        # TODO Lane D
        pass
