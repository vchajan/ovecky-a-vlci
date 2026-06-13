"""ScoreSystem — počítání bodů.

Pravidla:
- ``dog_repels_wolf`` -> +SCORE_PER_WOLF_REPELLED a inkrement ``session.wolves_repelled``
- ``wolf_eats_sheep`` -> žádný score impact (sheep_alive sníží Rules)
- ``tick(dt)`` -> přičítá SCORE_PER_SECOND bodů za sekundu přežití (lineárně dt)
"""
from __future__ import annotations

from game import settings
from game.session import GameSession
from game.systems.collision import CollisionEvent


class ScoreSystem:
    def __init__(self) -> None:
        self._second_accumulator = 0.0

    def process_events(self, events: list[CollisionEvent],
                       session: GameSession) -> None:
        """Aplikuje skóre podle eventů."""
        wolves_repelled = 0
        for event in events:
            wolves_repelled += event.kind == "dog_repels_wolf"

        session.score += wolves_repelled * settings.SCORE_PER_WOLF_REPELLED
        session.wolves_repelled += wolves_repelled

    def tick(self, dt: float, session: GameSession) -> None:
        """Lineárně přičítá SCORE_PER_SECOND bodů za sekundu přežití."""
        self._second_accumulator += dt
        elapsed_seconds = int(self._second_accumulator)
        if elapsed_seconds:
            session.score += elapsed_seconds * settings.SCORE_PER_SECOND
            self._second_accumulator -= elapsed_seconds
