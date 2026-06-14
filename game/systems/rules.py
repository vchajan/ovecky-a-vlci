"""Gameplay rules: game-over checks and collision event effects."""
from __future__ import annotations

import random

from game import settings
from game.effects import SheepLossMark
from game.session import GameSession
from game.systems.collision import CollisionEvent


def check_game_over(session: GameSession) -> bool:
    """Return True when the flock drops below the safe minimum."""
    return session.sheep_alive < settings.MINIMUM_SHEEP_TO_CONTINUE


def apply_collision_events(events: list[CollisionEvent],
                           session: GameSession,
                           rng: random.Random) -> None:
    """Apply collision effects after scoring has processed the same events."""
    for event in events:
        if event.kind == "wolf_eats_sheep":
            if event.sheep is None or not event.sheep.alive:
                continue
            loss_position = event.sheep.rect.center
            event.sheep.kill_sheep()
            session.sheep_alive = max(0, session.sheep_alive - 1)
            _add_sheep_loss_mark(session, loss_position)
        elif event.kind == "dog_repels_wolf":
            if event.wolf is None or not event.wolf.is_active:
                continue
            event.wolf.start_fleeing(session.player.pos)


def _add_sheep_loss_mark(
    session: GameSession,
    position: tuple[float, float],
) -> None:
    if session.sheep_loss_marks is None:
        session.sheep_loss_marks = []
    variant = session.sheep_loss_mark_counter
    session.sheep_loss_mark_counter += 1
    session.sheep_loss_marks.append(SheepLossMark(position, variant))
    overflow = len(session.sheep_loss_marks) - settings.MAX_BLOOD_STAINS
    if overflow > 0:
        del session.sheep_loss_marks[:overflow]
