"""Score handling for survival time and wolf repels."""
from __future__ import annotations

from game import settings
from game.session import GameSession
from game.systems.collision import CollisionEvent


class ScoreSystem:
    def __init__(self) -> None:
        self._second_accumulator = 0.0

    def process_events(self, events: list[CollisionEvent],
                       session: GameSession) -> None:
        """Apply score changes for valid collision events."""
        repelled_wolves = {
            event.wolf
            for event in events
            if (
                event.kind == "dog_repels_wolf"
                and event.wolf is not None
                and event.wolf.is_active
            )
        }

        count = len(repelled_wolves)
        session.score += count * settings.SCORE_PER_WOLF_REPELLED
        session.wolves_repelled += count

    def tick(self, dt: float, session: GameSession) -> None:
        """Add SCORE_PER_SECOND for each full survived second."""
        self._second_accumulator += dt
        elapsed_seconds = int(self._second_accumulator)
        if elapsed_seconds:
            session.score += elapsed_seconds * settings.SCORE_PER_SECOND
            self._second_accumulator -= elapsed_seconds
