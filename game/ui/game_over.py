"""Game over screen.

Lane A — implementace.

Zobrazí nadpis, finální skóre a tři tlačítka:
- Hrát znovu -> GameState.PLAYING (Game._change_state vytvoří novou session)
- Menu       -> GameState.MAIN_MENU
- Konec      -> pygame.QUIT event, Game ukončí smyčku
"""
from __future__ import annotations

import pygame

from game import settings
from game.assets import AssetManager
from game.states import GameState
from game.ui.buttons import Button


class GameOverScreen:
    def __init__(self, assets: AssetManager, final_score: int = 0) -> None:
        self.assets = assets
        self.final_score = final_score
        self._next_state: GameState | None = None

        self._font_title = assets.font(72)
        self._font_score_label = assets.font(28)
        self._font_score_value = assets.font(96)
        self._font_button = assets.font(30)

        # Tři tlačítka vedle sebe horizontálně, vycentrovaná.
        button_w, button_h = 200, 56
        button_gap = 24
        total_w = button_w * 3 + button_gap * 2
        start_x = (settings.WINDOW_WIDTH - total_w) // 2
        button_y = int(settings.WINDOW_HEIGHT * 0.72)

        self._buttons: list[Button] = [
            Button(
                rect=pygame.Rect(start_x, button_y, button_w, button_h),
                label="Hrát znovu",
                on_click=self._on_replay,
                font=self._font_button,
            ),
            Button(
                rect=pygame.Rect(
                    start_x + button_w + button_gap,
                    button_y, button_w, button_h,
                ),
                label="Menu",
                on_click=self._on_menu,
                font=self._font_button,
            ),
            Button(
                rect=pygame.Rect(
                    start_x + (button_w + button_gap) * 2,
                    button_y, button_w, button_h,
                ),
                label="Konec",
                on_click=self._on_quit,
                font=self._font_button,
            ),
        ]

    # ----------- button callbacks
    def _on_replay(self) -> None:
        self._next_state = GameState.PLAYING

    def _on_menu(self) -> None:
        self._next_state = GameState.MAIN_MENU

    def _on_quit(self) -> None:
        pygame.event.post(pygame.event.Event(pygame.QUIT))

    # ----------- state protokol
    def handle_event(self, event: pygame.event.Event) -> GameState | None:
        for btn in self._buttons:
            btn.handle_event(event)
        if self._next_state is not None:
            result = self._next_state
            self._next_state = None
            return result
        return None

    def update(self, dt: float) -> GameState | None:
        return None

    def render(self, surface: pygame.Surface) -> None:
        surface.fill(settings.COLOR_BACKGROUND)

        # Nadpis "KONEC HRY" — krémová barva, ne moc agresivní
        title = self._font_title.render(
            "KONEC HRY", True, settings.COLOR_TEXT,
        )
        title_rect = title.get_rect(
            center=(settings.WINDOW_WIDTH // 2,
                    int(settings.WINDOW_HEIGHT * 0.20)),
        )
        surface.blit(title, title_rect)

        # Popisek skóre
        score_label = self._font_score_label.render(
            "Tvé skóre:", True, settings.COLOR_TEXT_DIM,
        )
        score_label_rect = score_label.get_rect(
            center=(settings.WINDOW_WIDTH // 2,
                    int(settings.WINDOW_HEIGHT * 0.36)),
        )
        surface.blit(score_label, score_label_rect)

        # Hodnota skóre velkým fontem v akcentové barvě
        score_value = self._font_score_value.render(
            str(self.final_score), True, settings.COLOR_ACCENT,
        )
        score_value_rect = score_value.get_rect(
            center=(settings.WINDOW_WIDTH // 2,
                    int(settings.WINDOW_HEIGHT * 0.50)),
        )
        surface.blit(score_value, score_value_rect)

        # Tlačítka
        for btn in self._buttons:
            btn.render(surface)
