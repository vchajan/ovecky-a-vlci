"""Player — pes ovládaný hráčem.

# TODO Lane C
WASD/šipky -> pohyb, kontrola kolize s plotem přes tilemap.is_blocked_rect,
animace ve 4 směrech.
"""
from __future__ import annotations

import pygame

from game import settings
from game.assets import AssetManager
from game.world.tilemap import TileMap


class Player(pygame.sprite.Sprite):
    def __init__(self, pos: tuple[float, float], assets: AssetManager) -> None:
        super().__init__()
        # TODO Lane C: načti animace, nastav rect podle reálného sprite
        self.pos = pygame.math.Vector2(pos)
        self.image = pygame.Surface((48, 48), pygame.SRCALPHA)
        self.image.fill(settings.COLOR_PLACEHOLDER)
        self.rect = self.image.get_rect(center=(int(self.pos.x), int(self.pos.y)))

    def update(self, dt: float, keys: pygame.key.ScancodeWrapper,
               tilemap: TileMap) -> None:
        """Zpracuje WASD/šipky, posouvá pozici, kontroluje kolize s plotem."""
        # TODO Lane C
        pass
