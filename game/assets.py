"""AssetManager — načítání a cachování obrázků, animací a fontů.

# TODO Lane B
Klíče assetů viz sekce 3.4 týmového plánu (docs/Sheep_Defender_team_plan.md).

Při chybějícím souboru vrátí placeholder (růžový čtverec / prázdnou animaci),
nikdy nepádá.
"""
from __future__ import annotations

import pygame

from game import settings
from game.animation import Animation


class AssetManager:
    def __init__(self) -> None:
        pygame.font.init()
        # TODO Lane B: načti spritesheety a animace dle klíčů ze sekce 3.4
        self._image_cache: dict[str, pygame.Surface] = {}
        self._animation_cache: dict[str, Animation] = {}
        self._font_cache: dict[int, pygame.font.Font] = {}

    def image(self, key: str) -> pygame.Surface:
        """Vrátí obrázek pro daný klíč. Při chybějícím vrátí placeholder."""
        # TODO Lane B
        if key in self._image_cache:
            return self._image_cache[key]
        placeholder = pygame.Surface((settings.TILE_SIZE, settings.TILE_SIZE))
        placeholder.fill(settings.COLOR_PLACEHOLDER)
        return placeholder

    def animation(self, key: str) -> Animation:
        """Vrátí animaci pro daný klíč. Při chybějícím vrátí placeholder animaci."""
        # TODO Lane B
        if key in self._animation_cache:
            return self._animation_cache[key]
        placeholder = pygame.Surface((settings.TILE_SIZE, settings.TILE_SIZE))
        placeholder.fill(settings.COLOR_PLACEHOLDER)
        return Animation([placeholder])

    def font(self, size: int) -> pygame.font.Font:
        """Vrátí (cachovaný) font dané velikosti."""
        # TODO Lane B: vlastní font, prozatím defaultní
        if size not in self._font_cache:
            self._font_cache[size] = pygame.font.Font(None, size)
        return self._font_cache[size]
