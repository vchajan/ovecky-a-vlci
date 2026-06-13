"""Main pygame application and game state machine."""
from __future__ import annotations

import random

import pygame

from game import settings
from game.assets import AssetManager
from game.session import GameSession, create_session
from game.states import GameState
from game.systems.collision import detect_collisions
from game.systems.difficulty import DifficultyManager
from game.systems.rules import apply_collision_events, check_game_over
from game.systems.score import ScoreSystem
from game.ui.game_over import GameOverScreen
from game.ui.hud import HUD
from game.ui.menu import MenuScreen
from game.ui.splash import SplashScreen
from game.world.tilemap import TileMap


class PlayingState:
    """Actual gameplay state for Sheep Defender."""

    def __init__(self, assets: AssetManager) -> None:
        self.assets = assets
        self.rng = random.Random(42)
        self.tilemap = TileMap()
        self.session: GameSession = create_session(assets, self.tilemap, self.rng)
        self.score_system = ScoreSystem()
        self.difficulty_manager = DifficultyManager()
        self.hud = HUD(assets)

    @property
    def final_score(self) -> int:
        return self.session.score

    def handle_event(self, event: pygame.event.Event) -> GameState | None:
        return None

    def update(self, dt: float) -> GameState | None:
        keys = pygame.key.get_pressed()

        self.session.player.update(dt, keys, self.tilemap)

        for sheep in list(self.session.sheep_group):
            sheep.update(dt, self.tilemap)

        for wolf in list(self.session.wolf_group):
            wolf.update(dt, self.session)

        events = detect_collisions(
            self.session.player,
            self.session.sheep_group,
            self.session.wolf_group,
        )
        self.score_system.process_events(events, self.session)
        apply_collision_events(events, self.session, self.rng)

        self.session.elapsed_time += dt
        self.score_system.tick(dt, self.session)
        self.difficulty_manager.update(dt, self.session)

        self.session.sheep_alive = sum(
            1 for sheep in self.session.sheep_group
            if getattr(sheep, "alive", False)
        )
        self.session.game_over = check_game_over(self.session)
        if self.session.game_over:
            return GameState.GAME_OVER

        return None

    def render(self, surface: pygame.Surface) -> None:
        self.tilemap.render(surface)
        self.session.sheep_group.draw(surface)

        for wolf in self.session.wolf_group:
            if wolf.is_active:
                surface.blit(wolf.image, wolf.rect)

        surface.blit(self.session.player.image, self.session.player.rect)
        self.hud.render(surface, self.session)


class Game:
    """Pygame window, loop and state transitions."""

    def __init__(self) -> None:
        pygame.init()
        self.screen = pygame.display.set_mode(settings.WINDOW_SIZE)
        pygame.display.set_caption(settings.WINDOW_TITLE)
        self.clock = pygame.time.Clock()
        self.running = True
        self.assets = AssetManager()
        self._states: dict[GameState, object] = {
            GameState.SPLASH: SplashScreen(self.assets),
            GameState.MAIN_MENU: MenuScreen(self.assets),
            GameState.PLAYING: PlayingState(self.assets),
            GameState.GAME_OVER: GameOverScreen(self.assets, final_score=0),
        }
        self.current_state: GameState = GameState.SPLASH

    @property
    def state(self):
        """Return the current state object."""
        return self._states[self.current_state]

    def run(self) -> None:
        """Run the main loop until the game exits."""
        while self.running:
            dt = min(
                self.clock.tick(settings.FPS) / 1000.0,
                settings.MAX_DELTA_TIME,
            )
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
        self.screen.fill(settings.COLOR_BACKGROUND)
        self.state.render(self.screen)
        pygame.display.flip()

    def _change_state(self, new_state: GameState) -> None:
        """Switch states and recreate stateful screens when needed."""
        if new_state == GameState.MAIN_MENU:
            self._states[GameState.MAIN_MENU] = MenuScreen(self.assets)
        elif new_state == GameState.PLAYING:
            self._states[GameState.PLAYING] = PlayingState(self.assets)
        elif new_state == GameState.GAME_OVER:
            playing = self._states[GameState.PLAYING]
            score = getattr(playing, "final_score", 0)
            self._states[GameState.GAME_OVER] = GameOverScreen(
                self.assets,
                final_score=score,
            )

        self.current_state = new_state
