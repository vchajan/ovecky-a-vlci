"""Hlavní třída aplikace s herním stavovým strojem.

Lane A vlastní pygame okno, hlavní smyčku a přepínání stavů.

Stavy:
- SPLASH:    SplashScreen — auto-přechod na MAIN_MENU po SPLASH_DURATION
- MAIN_MENU: MenuScreen   — tlačítko Hrát -> PLAYING, Konec -> ukončí hru
- PLAYING:   PlayingPlaceholder (Phase 1) -> v Phase 2 ho integrace nahradí
             skutečnou herní smyčkou (create_session, kolize, render entit, HUD).
             V Phase 1: stiskni R pro simulaci game over.
- GAME_OVER: GameOverScreen — Hrát znovu -> PLAYING, Menu -> MAIN_MENU,
             Konec -> ukončí hru

Kontrakt state objektu (každá obrazovka splňuje):
- handle_event(event) -> GameState | None      (volitelné, fallback přes getattr)
- update(dt: float)   -> GameState | None
- render(surface)     -> None

Když handle_event nebo update vrátí GameState, Game přepne na ten stav.
Některé přechody (PLAYING, GAME_OVER, MAIN_MENU) recreatují instanci kvůli
čistému resetu stavu nebo předání aktuálních dat.
"""
from __future__ import annotations

import pygame

from game import settings
from game.assets import AssetManager
from game.states import GameState
from game.ui.game_over import GameOverScreen
from game.ui.menu import MenuScreen
from game.ui.splash import SplashScreen


class PlayingPlaceholder:
    """Phase 1 placeholder pro PLAYING stav.

    V Phase 2 integrace tuto třídu nahradí (resp. doplní) skutečnou herní
    smyčkou s GameSession (vytvořenou přes ``create_session(...)``),
    updatem entit, detekcí kolizí, skórováním a HUDem.

    V Phase 1:
    - akumuluje ``final_score`` rychlostí SCORE_PER_SECOND (simulace
      ScoreSystem.tick, který v Phase 2 dělá totéž)
    - klávesa R simuluje konec hry (přechod na GAME_OVER)
    - vykreslí placeholder text a live skóre (simulace HUDu)
    """

    def __init__(self, assets: AssetManager) -> None:
        self.assets = assets
        # final_score je atribut, který Game._change_state čte při přechodu
        # na GAME_OVER. V Phase 2 to bude session.score.
        self.final_score: int = 0
        # Akumulátor je float, aby se score plynule zvedalo i při dt < 1s.
        self._score_accumulator: float = 0.0
        self._font_big = assets.font(56)
        self._font_small = assets.font(28)
        self._font_hud = assets.font(32)

    def handle_event(self, event: pygame.event.Event) -> GameState | None:
        if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
            return GameState.GAME_OVER
        return None

    def update(self, dt: float) -> GameState | None:
        # Simulace skórování za přežitý čas. V Phase 2 toto dělá
        # ScoreSystem.tick nad session.score.
        self._score_accumulator += dt * settings.SCORE_PER_SECOND
        self.final_score = int(self._score_accumulator)
        return None

    def render(self, surface: pygame.Surface) -> None:
        # Vlastní pozadí (světlejší zelená "tráva"), aby byl přechod stavu vidět.
        surface.fill(settings.COLOR_GRASS)

        # Hlavní placeholder text (centered)
        title = self._font_big.render(
            "PLACEHOLDER PLAYING", True, settings.COLOR_TEXT,
        )
        hint = self._font_small.render(
            "R = simulovat konec hry   |   Esc = ukončit",
            True, settings.COLOR_TEXT_DIM,
        )
        cx = settings.WINDOW_WIDTH // 2
        cy = settings.WINDOW_HEIGHT // 2
        surface.blit(title, title.get_rect(center=(cx, cy - 20)))
        surface.blit(hint, hint.get_rect(center=(cx, cy + 40)))

        # Live skóre v levém horním rohu (simulace HUDu; v Phase 2 přebírá HUD).
        score_text = self._font_hud.render(
            f"Skóre: {self.final_score}", True, settings.COLOR_TEXT,
        )
        surface.blit(score_text, (20, 20))


class Game:
    """Hlavní třída aplikace — pygame okno, hodiny, hlavní smyčka, state machine."""

    def __init__(self) -> None:
        pygame.init()
        self.screen = pygame.display.set_mode(settings.WINDOW_SIZE)
        pygame.display.set_caption(settings.WINDOW_TITLE)
        self.clock = pygame.time.Clock()
        self.running = True

        # Sdílený AssetManager pro všechny obrazovky.
        self.assets = AssetManager()

        # State objekty držené v slovníku. SPLASH se nikdy nerecreatuje
        # (je jednorázový). MAIN_MENU, PLAYING a GAME_OVER se při každém
        # vstupu vyměňují za novou instanci v _change_state (kvůli čistému
        # resetu stavu a předání aktuálních dat).
        self._states: dict[GameState, object] = {
            GameState.SPLASH: SplashScreen(self.assets),
            GameState.MAIN_MENU: MenuScreen(self.assets),
            GameState.PLAYING: PlayingPlaceholder(self.assets),
            GameState.GAME_OVER: GameOverScreen(self.assets, final_score=0),
        }
        self.current_state: GameState = GameState.SPLASH

    @property
    def state(self):
        """Vrátí aktuální state objekt — zkratka pro self._states[self.current_state]."""
        return self._states[self.current_state]

    def run(self) -> None:
        """Hlavní smyčka. Iteruje, dokud self.running == True."""
        while self.running:
            dt = min(self.clock.tick(settings.FPS) / 1000.0,
                     settings.MAX_DELTA_TIME)
            self._handle_events()
            self._update(dt)
            self._render()
        pygame.quit()

    def _handle_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                continue

            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self.running = False
                continue

            # Některé stavy nemusí mít handle_event (např. čistě časovaný
            # splash). getattr s fallbackem ho elegantně přeskočí.
            handler = getattr(self.state, "handle_event", None)
            if handler is not None:
                next_state = handler(event)
                if next_state is not None:
                    self._change_state(next_state)

    def _update(self, dt: float) -> None:
        next_state = self.state.update(dt)
        if next_state is not None:
            self._change_state(next_state)

    def _render(self) -> None:
        # Default pozadí — pro stavy, jejichž render nic nekreslí, se aspoň
        # ukáže čistá barva místo garbage bufferu. State objekty mohou
        # pozadí přemalovat (viz PlayingPlaceholder).
        self.screen.fill(settings.COLOR_BACKGROUND)
        self.state.render(self.screen)
        pygame.display.flip()

    def _change_state(self, new_state: GameState) -> None:
        """Přepne na nový stav. Některé přechody potřebují speciální setup."""
        if new_state == GameState.MAIN_MENU:
            # Recreate kvůli resetu hover stavu tlačítek a _next_state.
            self._states[GameState.MAIN_MENU] = MenuScreen(self.assets)
        elif new_state == GameState.PLAYING:
            # Reset PLAYING — nová instance = čistý herní stav.
            # V Phase 2 zde místo placeholderu zavoláme create_session(...)
            # a vytvoříme skutečný PlayingState s GameSession.
            self._states[GameState.PLAYING] = PlayingPlaceholder(self.assets)
        elif new_state == GameState.GAME_OVER:
            # Přečteme finální skóre z PLAYING (v Phase 2 to bude session.score)
            # a předáme ho game-over obrazovce.
            playing = self._states[GameState.PLAYING]
            score = getattr(playing, "final_score", 0)
            self._states[GameState.GAME_OVER] = GameOverScreen(
                self.assets, final_score=score,
            )
        # SPLASH se nerecreatuje — je jednorázový, nikdy se do něj nevracíme.
        self.current_state = new_state
