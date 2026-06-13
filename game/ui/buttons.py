"""Reusable tlačítko pro menu a UI.

Lane A: hover stav + klik s callbackem. Jednoduchá třída — žádný layout
engine, žádné animace. Pozice se předává jako pygame.Rect.

Použití::

    def on_play_clicked() -> None:
        # např. nastavit flag, který MenuScreen.update přečte a vrátí PLAYING
        ...

    button = Button(
        rect=pygame.Rect(540, 320, 200, 64),
        label="Hrát",
        on_click=on_play_clicked,
        font=assets.font(36),
    )

    # v handle_event obrazovky:
    button.handle_event(event)

    # v render obrazovky:
    button.render(surface)
"""
from __future__ import annotations

from typing import Callable

import pygame

from game import settings


class Button:
    """Obdélníkové tlačítko s hover stavem a callbackem při kliknutí."""

    def __init__(self, rect: pygame.Rect, label: str,
                 on_click: Callable[[], None],
                 font: pygame.font.Font) -> None:
        self.rect = rect
        self.label = label
        self.on_click = on_click
        self.font = font
        self.hovered = False

    def handle_event(self, event: pygame.event.Event) -> None:
        """Aktualizuje hover stav a zavolá on_click při levém kliku v rectu."""
        if event.type == pygame.MOUSEMOTION:
            self.hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.on_click()

    def render(self, surface: pygame.Surface) -> None:
        """Vykreslí tlačítko se zaobleným pozadím, rámečkem a vycentrovaným textem.

        Barva pozadí a textu se mění podle hover stavu, aby uživatel viděl,
        kde je myš.
        """
        if self.hovered:
            bg_color = settings.COLOR_ACCENT
            text_color = settings.COLOR_BACKGROUND
        else:
            bg_color = settings.COLOR_FENCE
            text_color = settings.COLOR_TEXT

        # Zaoblený obdélník (border_radius je v Pygame od 2.0).
        pygame.draw.rect(surface, bg_color, self.rect, border_radius=8)
        # Tenký rámeček v decentní barvě pro vizuální oddělení od pozadí.
        pygame.draw.rect(surface, settings.COLOR_TEXT_DIM, self.rect,
                         width=2, border_radius=8)

        # Text vycentrovaný uvnitř rectu.
        text_surf = self.font.render(self.label, True, text_color)
        surface.blit(text_surf, text_surf.get_rect(center=self.rect.center))
