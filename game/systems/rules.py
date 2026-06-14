"""Gameplay rules: game-over checks and collision event effects."""
from __future__ import annotations

import random

from game.session import GameSession
from game.systems.collision import CollisionEvent


def check_game_over(session: GameSession) -> bool:
    """Return True when no sheep remain alive."""
    return session.sheep_alive == 0


def apply_collision_events(events: list[CollisionEvent],
                           session: GameSession,
                           rng: random.Random) -> None:
    """Apply collision effects after scoring has processed the same events."""
    for event in events:
        if event.kind == "wolf_eats_sheep":
            if event.sheep is None or not event.sheep.alive:
                continue
            event.sheep.kill_sheep()
            session.sheep_alive = max(0, session.sheep_alive - 1)
        elif event.kind == "dog_repels_wolf":
            if event.wolf is None or not event.wolf.is_active:
                continue
            event.wolf.start_fleeing(session.player.pos)
