"""Detekce kolizí mezi entitami.

# TODO Lane C
Vrací seznam CollisionEvent. Vlci s ``is_active == False`` (právě probíhá
respawn) se v detekci přeskakují — nemohou útočit na ovce ani být odraženi
dalším kontaktem s psem.
"""
from __future__ import annotations

from dataclasses import dataclass

import pygame

from game.entities.player import Player
from game.entities.sheep import Sheep
from game.entities.wolf import Wolf


@dataclass
class CollisionEvent:
    kind: str  # "wolf_eats_sheep" nebo "dog_repels_wolf"
    sheep: Sheep | None = None
    wolf: Wolf | None = None


def detect_collisions(player: Player,
                      sheep_group: pygame.sprite.Group,
                      wolf_group: pygame.sprite.Group) -> list[CollisionEvent]:
    """Detekuje kolize přes ``rect.colliderect``.

    Vlci s ``is_active == False`` se přeskakují (neútočí, nelze odrazit).
    """
    # TODO Lane C
    return []
