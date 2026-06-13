"""Button — reusable tlačítko pro menu a UI.

# TODO Lane A
Hover stav, klik, callback.
"""
from __future__ import annotations

from typing import Callable

import pygame


class Button:
    def __init__(self, rect: pygame.Rect, label: str,
                 on_click: Callable[[], None]) -> None:
        # TODO Lane A
        self.rect = rect
        self.label = label
        self.on_click = on_click
        self.hovered = False

    def handle_event(self, event: pygame.event.Event) -> None:
        """Zpracuje pohyb myši (hover) a klik (on_click)."""
        # TODO Lane A
        pass

    def render(self, surface: pygame.Surface) -> None:
        # TODO Lane A
        pass
