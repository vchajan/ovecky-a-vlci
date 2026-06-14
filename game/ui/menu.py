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
    def __init__(
        self,
        assets: AssetManager,
        selected_difficulty: str = settings.DEFAULT_DIFFICULTY,
    ) -> None:
        self.assets = assets
        self.selected_difficulty = (
            selected_difficulty
            if selected_difficulty in settings.DIFFICULTIES
            else settings.DEFAULT_DIFFICULTY
        )
        # Příští stav nastavený callbackem tlačítka; přečte se a vyresetuje
        # v handle_event po doručení.
        self._next_state: GameState | None = None

        self._font_title = assets.font(72)
        self._font_subtitle = assets.font(28)
        self._font_info = assets.font(26)
        self._font_button = assets.font(36)

        # Layout - difficulty row, then play/quit.
        button_w, button_h = 280, 64
        button_gap = 20
        cx = settings.WINDOW_WIDTH // 2
        difficulty_y = int(settings.WINDOW_HEIGHT * 0.45)
        start_y = int(settings.WINDOW_HEIGHT * 0.62)

        difficulty_w = 180
        difficulty_gap = 18
        difficulty_total = difficulty_w * 3 + difficulty_gap * 2
        difficulty_x = cx - difficulty_total // 2

        self._difficulty_buttons: list[Button] = [
            Button(
                rect=pygame.Rect(
                    difficulty_x + index * (difficulty_w + difficulty_gap),
                    difficulty_y,
                    difficulty_w,
                    52,
                ),
                label=difficulty.upper(),
                on_click=lambda value=difficulty: self._set_difficulty(value),
                font=self._font_info,
            )
            for index, difficulty in enumerate(settings.DIFFICULTIES)
        ]

        self._buttons: list[Button] = [
            *self._difficulty_buttons,
            Button(
                rect=pygame.Rect(cx - button_w // 2, start_y, button_w, button_h),
                label="Hrat",
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

    def _set_difficulty(self, difficulty: str) -> None:
        if difficulty in settings.DIFFICULTIES:
            self.selected_difficulty = difficulty

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

        difficulty = self._font_info.render(
            f"Difficulty: {self.selected_difficulty.upper()}",
            True,
            settings.COLOR_TEXT,
        )
        difficulty_rect = difficulty.get_rect(
            center=(settings.WINDOW_WIDTH // 2, int(settings.WINDOW_HEIGHT * 0.39)),
        )
        surface.blit(difficulty, difficulty_rect)

        # Tlačítka
        for btn in self._buttons:
            btn.render(surface)
            if (
                btn in self._difficulty_buttons
                and btn.label.lower() == self.selected_difficulty
            ):
                pygame.draw.rect(
                    surface,
                    settings.COLOR_ACCENT,
                    btn.rect.inflate(6, 6),
                    width=4,
                    border_radius=8,
                )
