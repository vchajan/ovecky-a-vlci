"""Hlavní menu.

Lane A — implementace.

Tlačítka:
- Hrát:  vrátí GameState.PLAYING, Game._change_state vytvoří novou herní session
- Konec: pošle pygame.QUIT event, Game._handle_events ukončí smyčku
"""
from __future__ import annotations

import pygame

from game import settings
from game.assets import AssetManager
from game.states import GameState
from game.ui.buttons import Button


class MenuScreen:
    def __init__(self, assets: AssetManager) -> None:
        self.assets = assets
        # Příští stav nastavený callbackem tlačítka; přečte se a vyresetuje
        # v handle_event po doručení.
        self._next_state: GameState | None = None

        self._font_title = assets.font(72)
        self._font_subtitle = assets.font(28)
        self._font_button = assets.font(36)

        # Layout — dvě tlačítka vycentrovaná pod podtitulkem.
        button_w, button_h = 280, 64
        button_gap = 20
        cx = settings.WINDOW_WIDTH // 2
        start_y = int(settings.WINDOW_HEIGHT * 0.50)

        self._buttons: list[Button] = [
            Button(
                rect=pygame.Rect(cx - button_w // 2, start_y, button_w, button_h),
                label="Hrát",
                on_click=self._on_play,
                font=self._font_button,
            ),
            Button(
                rect=pygame.Rect(
                    cx - button_w // 2,
                    start_y + button_h + button_gap,
                    button_w, button_h,
                ),
                label="Konec",
                on_click=self._on_quit,
                font=self._font_button,
            ),
        ]

    # ----------- button callbacks
    def _on_play(self) -> None:
        self._next_state = GameState.PLAYING

    def _on_quit(self) -> None:
        # Pygame-idiomatická cesta k ukončení — pošli QUIT event a nech ho
        # zachytit Game._handle_events. Vyhneme se přímému zásahu do Game.
        pygame.event.post(pygame.event.Event(pygame.QUIT))

    # ----------- state protokol (handle_event / update / render)
    def handle_event(self, event: pygame.event.Event) -> GameState | None:
        for btn in self._buttons:
            btn.handle_event(event)

        # _next_state mohl být právě nastaven callbackem během btn.handle_event.
        # Po doručení ho resetujeme, aby se přechod nepoužil opakovaně.
        if self._next_state is not None:
            result = self._next_state
            self._next_state = None
            return result
        return None

    def update(self, dt: float) -> GameState | None:
        return None

    def render(self, surface: pygame.Surface) -> None:
        surface.fill(settings.COLOR_BACKGROUND)

        # Titulek
        title = self._font_title.render(
            "SHEEP DEFENDER", True, settings.COLOR_ACCENT,
        )
        title_rect = title.get_rect(
            center=(settings.WINDOW_WIDTH // 2,
                    int(settings.WINDOW_HEIGHT * 0.20)),
        )
        surface.blit(title, title_rect)

        # Podtitulek
        subtitle = self._font_subtitle.render(
            "Pes brání stádo před vlky", True, settings.COLOR_TEXT_DIM,
        )
        subtitle_rect = subtitle.get_rect(
            center=(settings.WINDOW_WIDTH // 2, title_rect.bottom + 16),
        )
        surface.blit(subtitle, subtitle_rect)

        # Tlačítka
        for btn in self._buttons:
            btn.render(surface)
