"""Splash screen.

# TODO Lane A
Zobrazí logo na SPLASH_DURATION sekund, pak automaticky přechází do MAIN_MENU.
"""
from __future__ import annotations

import pygame

from game import settings
from game.states import GameState


class SplashScreen:
    def __init__(self, assets) -> None:
        # TODO Lane A
        self.assets = assets
        self.elapsed = 0.0

    def update(self, dt: float) -> GameState | None:
        """Po uplynutí SPLASH_DURATION vrátí GameState.MAIN_MENU."""
        # TODO Lane A
        return None

    def render(self, surface: pygame.Surface) -> None:
        # TODO Lane A
        pass
