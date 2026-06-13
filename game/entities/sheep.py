"""Sheep — ovce s pomalým náhodným pohybem (random walk se stavy IDLE/WANDER).

# TODO Lane C
V IDLE stojí náhodně 0.8–2.4 s (viz SHEEP_IDLE_RANGE), pak si vybere
náhodný cíl ve vzdálenosti ~80–200 px a jde tam (omezeno tilemap).
"""
from __future__ import annotations

import pygame

from game import settings
from game.assets import AssetManager
from game.world.tilemap import TileMap


class Sheep(pygame.sprite.Sprite):
    def __init__(self, pos: tuple[float, float], assets: AssetManager) -> None:
        super().__init__()
        # TODO Lane C
        self.pos = pygame.math.Vector2(pos)
        self.alive = True
        self.image = pygame.Surface((40, 40), pygame.SRCALPHA)
        self.image.fill(settings.COLOR_PLACEHOLDER)
        self.rect = self.image.get_rect(center=(int(self.pos.x), int(self.pos.y)))

    def update(self, dt: float, tilemap: TileMap) -> None:
        """Pomalý random walk se stavy IDLE/WANDER."""
        # TODO Lane C
        pass

    def kill_sheep(self) -> None:
        """Označí ovci jako mrtvou a odstraní ji ze všech sprite groups.

        Pojmenováno explicitně, aby nedošlo k záměně s pygame.sprite.Sprite.kill,
        které pouze odstraňuje z groups, ale neoznačuje stav.
        """
        # TODO Lane C
        self.alive = False
        self.kill()  # pygame: odstranění ze všech sprite groups
