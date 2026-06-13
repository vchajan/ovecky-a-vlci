"""Pravidla hry — game over check a aplikace kolizních eventů.

"""
from __future__ import annotations

import random

from game import settings
from game.session import GameSession
from game.systems.collision import CollisionEvent


def check_game_over(session: GameSession) -> bool:
    """True, když padla poslední ovce."""
    return session.sheep_alive == 0


def apply_collision_events(events: list[CollisionEvent],
                           session: GameSession,
                           rng: random.Random) -> None:
    """Aplikuje efekty detekovaných kolizí.

    - ``wolf_eats_sheep``  -> sheep.kill_sheep() + sheep_alive -= 1
    - ``dog_repels_wolf``  -> wolf.trigger_respawn(WOLF_RESPAWN_DELAY,
                                session.tilemap.edge_spawn_position(rng))

    Skóre se zde NEZAPOČÍTÁVÁ — to dělá ScoreSystem nad stejnou listou eventů.
    """
    for event in events:
        if event.kind == "wolf_eats_sheep":
            event.sheep.kill_sheep()
            session.sheep_alive -= 1
        elif event.kind == "dog_repels_wolf":
            event.wolf.trigger_respawn(
                settings.WOLF_RESPAWN_DELAY,
                session.tilemap.edge_spawn_position(rng),
            )
