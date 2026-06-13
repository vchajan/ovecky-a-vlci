"""Hlavní třída aplikace.

# TODO Lane A — implementuj kompletní state machine.

Tento soubor je v Phase 0 jen MINIMÁLNÍ KOSTRA, která otevře okno
a vypíše placeholder text — slouží jen k ověření, že setup funguje.
Lane A v Phase 1 dopracuje:
- Vlastní state objekty (SplashScreen, MenuScreen, GameOverScreen)
- Přepínání stavů SPLASH -> MAIN_MENU -> PLAYING -> GAME_OVER
- Volání ``create_session(...)`` při vstupu do PLAYING
- Playing loop pořadí: input -> player.update -> sheep_group.update ->
  wolf_group.update(session) -> detect_collisions ->
  apply_collision_events -> score.process_events + score.tick ->
  difficulty.update -> render
- Render: tilemap, ovce, vlci (jen ty s ``is_active == True``), hráč, HUD
"""
from __future__ import annotations

import pygame

from game import settings
from game.states import GameState


class Game:
    """Hlavní třída — vlastní pygame okno, hodiny a smyčku."""

    def __init__(self) -> None:
        pygame.init()
        self.screen = pygame.display.set_mode(settings.WINDOW_SIZE)
        pygame.display.set_caption(settings.WINDOW_TITLE)
        self.clock = pygame.time.Clock()
        self.running = True
        self.state = GameState.SPLASH
        # TODO Lane A: instancovat state objekty, držet aktivní session

    def run(self) -> None:
        """Hlavní smyčka: Event -> Update -> Render."""
        while self.running:
            dt = min(self.clock.tick(settings.FPS) / 1000.0, settings.MAX_DELTA_TIME)
            self._handle_events()
            self._update(dt)
            self._render()
        pygame.quit()

    def _handle_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self.running = False
            # TODO Lane A: deleguj na aktuální state objekt

    def _update(self, dt: float) -> None:
        # TODO Lane A: deleguj na aktuální state objekt (jeho update vrátí
        # příští stav nebo None pro setrvání ve stávajícím)
        pass

    def _render(self) -> None:
        # TODO Lane A: deleguj na aktuální state objekt.
        # Toto je jen Phase 0 placeholder.
        self.screen.fill(settings.COLOR_BACKGROUND)
        font_big = pygame.font.Font(None, 56)
        font_small = pygame.font.Font(None, 28)
        title = font_big.render(
            f"Sheep Defender — Phase 0 skeleton",
            True, settings.COLOR_TEXT,
        )
        subtitle = font_small.render(
            f"Stav: {self.state.name}   |   Esc = konec",
            True, settings.COLOR_TEXT_DIM,
        )
        hint = font_small.render(
            "TODO Lane A: implementuj state machine, splash, menu, game over",
            True, settings.COLOR_ACCENT,
        )
        cx = settings.WINDOW_WIDTH // 2
        cy = settings.WINDOW_HEIGHT // 2
        self.screen.blit(title, title.get_rect(center=(cx, cy - 40)))
        self.screen.blit(subtitle, subtitle.get_rect(center=(cx, cy + 10)))
        self.screen.blit(hint, hint.get_rect(center=(cx, cy + 60)))
        pygame.display.flip()
