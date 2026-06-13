"""TileMap — herní mapa pastviny + plotu.

# TODO Lane B
Layout je dán v ``pasture_map.py`` jako 2D matice. Mapa je statická,
žádné procedurální generování.
"""
from __future__ import annotations

import random

import pygame

from game import settings
from game.world.pasture_map import PASTURE_LAYOUT


class TileMap:
    def __init__(self) -> None:
        # TODO Lane B
        self.layout = PASTURE_LAYOUT
        self.tile_size = settings.TILE_SIZE
        self.height = len(self.layout)
        self.width = len(self.layout[0]) if self.layout else 0

    def render(self, surface: pygame.Surface) -> None:
        """Vykreslí celou mapu na surface."""
        # TODO Lane B — minimální placeholder (jednolitá tráva)
        surface.fill(settings.COLOR_GRASS)

    def is_blocked_pixel(self, x: float, y: float) -> bool:
        """True, pokud je na dané pozici neprůchozí dlaždice (plot)."""
        # TODO Lane B
        return False

    def is_blocked_rect(self, rect: pygame.Rect) -> bool:
        """True, pokud obdélník koliduje s neprůchozí dlaždicí."""
        # TODO Lane B
        return False

    def random_grass_position(self, rng: random.Random) -> tuple[float, float]:
        """Náhodná volná pozice na trávě (uvnitř plotu) pro spawn ovce / hráče."""
        # TODO Lane B
        return (settings.WINDOW_WIDTH / 2.0, settings.WINDOW_HEIGHT / 2.0)

    def edge_spawn_position(self, rng: random.Random) -> tuple[float, float]:
        """Pozice na okraji mapy mimo plot — pro spawn / respawn vlků."""
        # TODO Lane B
        return (0.0, settings.WINDOW_HEIGHT / 2.0)
