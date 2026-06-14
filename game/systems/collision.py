"""Collision detection between gameplay entities."""
from __future__ import annotations

from dataclasses import dataclass

import pygame

from game.entities.player import Player
from game.entities.sheep import Sheep
from game.entities.wolf import Wolf


@dataclass
class CollisionEvent:
    kind: str
    sheep: Sheep | None = None
    wolf: Wolf | None = None


def detect_collisions(player: Player,
                      sheep_group: pygame.sprite.Group,
                      wolf_group: pygame.sprite.Group) -> list[CollisionEvent]:
    """Return collision events detected through sprite rect overlap."""
    events: list[CollisionEvent] = []
    eaten_sheep: set[Sheep] = set()
    wolves_with_sheep_event: set[Wolf] = set()
    wolves_with_dog_event: set[Wolf] = set()

    for wolf in wolf_group:
        if not getattr(wolf, "is_active", False):
            continue

        if (
            wolf not in wolves_with_dog_event
            and player.rect.colliderect(wolf.rect)
        ):
            events.append(CollisionEvent("dog_repels_wolf", wolf=wolf))
            wolves_with_dog_event.add(wolf)
            continue

        if wolf in wolves_with_sheep_event:
            continue

        for sheep in sheep_group:
            if sheep in eaten_sheep or not getattr(sheep, "alive", False):
                continue
            if not wolf.rect.colliderect(sheep.rect):
                continue

            events.append(CollisionEvent("wolf_eats_sheep", sheep=sheep, wolf=wolf))
            eaten_sheep.add(sheep)
            wolves_with_sheep_event.add(wolf)
            break

    return events
