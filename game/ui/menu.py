"""Hlavní menu.

# TODO Lane A
Tlačítko Hrát (povinné) a volitelně Konec / Jak hrát.
"""
from __future__ import annotations

import pygame

from game.states import GameState


class MenuScreen:
    def __init__(self, assets) -> None:
        # TODO Lane A
        self.assets = assets

    def handle_event(self, event: pygame.event.Event) -> GameState | None:
        """Klik na Hrát -> GameState.PLAYING."""
        # TODO Lane A
        return None

    def update(self, dt: float) -> GameState | None:
        # TODO Lane A
        return None

    def render(self, surface: pygame.Surface) -> None:
        # TODO Lane A
        pass
