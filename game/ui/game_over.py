"""Game over screen.

# TODO Lane A
Zobrazí finální skóre + tlačítka:
- Hrát znovu -> GameState.PLAYING (vytvoří novou session)
- Menu       -> GameState.MAIN_MENU
"""
from __future__ import annotations

import pygame

from game.states import GameState


class GameOverScreen:
    def __init__(self, assets, final_score: int = 0) -> None:
        # TODO Lane A
        self.assets = assets
        self.final_score = final_score

    def handle_event(self, event: pygame.event.Event) -> GameState | None:
        # TODO Lane A
        return None

    def update(self, dt: float) -> GameState | None:
        # TODO Lane A
        return None

    def render(self, surface: pygame.Surface) -> None:
        # TODO Lane A
        pass
