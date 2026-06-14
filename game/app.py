"""Main pygame application and game state machine."""
from __future__ import annotations

import random

import pygame

from game import settings
from game.assets import AssetManager
from game.audio import AudioSystem
from game.session import GameSession, create_session
from game.states import GameState
from game.systems.collision import detect_collisions
from game.systems.difficulty import DifficultyManager, normalize_difficulty
from game.systems.rules import apply_collision_events, check_game_over
from game.systems.score import ScoreSystem
from game.ui.game_over import GameOverScreen
from game.ui.hud import HUD
from game.ui.menu import MenuScreen
from game.ui.splash import SplashScreen
from game.world.tilemap import TileMap


class PlayingState:
    """Actual gameplay state for Sheep Defender."""

    def __init__(
        self,
        assets: AssetManager,
        difficulty: str = settings.DEFAULT_DIFFICULTY,
    ) -> None:
        self.assets = assets
        self.rng = random.Random(42)
        self.tilemap = TileMap()
        self.session: GameSession = create_session(
            assets,
            self.tilemap,
            self.rng,
            difficulty,
        )
        self.score_system = ScoreSystem()
        self.difficulty_manager = DifficultyManager()
        self.hud = HUD(assets)
        self.audio = AudioSystem(assets)
        self.show_herd_debug = False
        self._sheep_bleat_timer = self._next_sheep_bleat_time()
        self._sheep_panic_cooldown = 0.0
        self._pending_wolf_howl_delay: float | None = None

    @property
    def final_score(self) -> int:
        return self.session.score

    def handle_event(self, event: pygame.event.Event) -> GameState | None:
        if event.type == pygame.KEYDOWN and event.key == pygame.K_F3:
            self.show_herd_debug = not self.show_herd_debug
        return None

    def update(self, dt: float) -> GameState | None:
        keys = pygame.key.get_pressed()
        previous_sheep_alive = self.session.sheep_alive

        self.session.player.update(dt, keys, self.tilemap)

        for sheep in list(self.session.sheep_group):
            sheep.update(
                dt,
                self.tilemap,
                self.session.player,
                self.session.sheep_group,
            )

        for wolf in list(self.session.wolf_group):
            wolf.update(dt, self.session)

        events = detect_collisions(
            self.session.player,
            self.session.sheep_group,
            self.session.wolf_group,
        )
        self.score_system.process_events(events, self.session)
        apply_collision_events(events, self.session, self.rng)
        self._play_collision_audio(events)

        self.session.elapsed_time += dt
        self.score_system.tick(dt, self.session)
        self._update_delayed_wave_audio(dt)
        previous_wave = self.session.wave
        self.difficulty_manager.update(dt, self.session)
        if self.session.wave != previous_wave:
            self.audio.play("audio/wave_start")
            if self.session.wave_action == "new_wolf":
                self._pending_wolf_howl_delay = settings.WOLF_HOWL_DELAY
        self._update_loss_marks(dt)
        self._update_proximity_audio(dt)
        self._update_bleat_audio(dt)

        self.session.sheep_alive = sum(
            1 for sheep in self.session.sheep_group
            if getattr(sheep, "alive", False)
        )
        if (
            self.session.sheep_alive == settings.MINIMUM_SHEEP_TO_CONTINUE
            and previous_sheep_alive > self.session.sheep_alive
        ):
            self.session.sheep_warning_remaining = 2.0
        elif self.session.sheep_warning_remaining > 0.0:
            self.session.sheep_warning_remaining = max(
                0.0,
                self.session.sheep_warning_remaining - dt,
            )
        self.session.game_over = check_game_over(self.session)
        if self.session.game_over:
            self.audio.play("audio/game_over")
            return GameState.GAME_OVER

        return None

    def render(self, surface: pygame.Surface) -> None:
        self.tilemap.render(surface)
        for mark in self.session.sheep_loss_marks or []:
            mark.render(surface)
        self.session.sheep_group.draw(surface)

        for wolf in self.session.wolf_group:
            if wolf.is_visible:
                surface.blit(wolf.image, wolf.rect)

        surface.blit(self.session.player.image, self.session.player.rect)
        if self.show_herd_debug:
            self._render_herd_debug(surface)
        self.hud.render(surface, self.session)

    def _play_collision_audio(self, events) -> None:
        played_repel = False
        played_sheep_loss = False
        for event in events:
            if event.kind == "dog_repels_wolf" and not played_repel:
                self.audio.play("audio/dog_bark")
                self.audio.play("audio/wolf_flee")
                played_repel = True
            elif event.kind == "wolf_eats_sheep" and not played_sheep_loss:
                self.audio.play("audio/sheep_loss")
                played_sheep_loss = True

    def _update_loss_marks(self, dt: float) -> None:
        marks = self.session.sheep_loss_marks
        if marks is None:
            return
        for mark in marks:
            mark.update(dt)
        self.session.sheep_loss_marks = [
            mark for mark in marks if not mark.expired
        ]

    def _update_bleat_audio(self, dt: float) -> None:
        self._sheep_bleat_timer -= dt
        if self._sheep_bleat_timer > 0.0:
            return

        living_sheep = [
            sheep for sheep in self.session.sheep_group
            if getattr(sheep, "alive", False)
        ]
        if living_sheep:
            self.rng.choice(living_sheep)
            self.audio.play("audio/sheep_bleat")
        self._sheep_bleat_timer = self._next_sheep_bleat_time()

    def _update_proximity_audio(self, dt: float) -> None:
        self._sheep_panic_cooldown = max(0.0, self._sheep_panic_cooldown - dt)
        sheep = [
            item for item in self.session.sheep_group
            if getattr(item, "alive", False)
        ]
        wolves = [
            wolf for wolf in self.session.wolf_group
            if getattr(wolf, "is_active", False)
        ]
        if not sheep or not wolves:
            return

        panic_played = False
        for wolf in wolves:
            cooldown = max(0.0, getattr(wolf, "growl_cooldown_remaining", 0.0) - dt)
            wolf.growl_cooldown_remaining = cooldown
            nearest = min(
                float(((target.pos - wolf.pos) ** 2).sum() ** 0.5)
                for target in sheep
            )
            if (
                nearest < settings.WOLF_GROWL_DISTANCE
                and wolf.growl_cooldown_remaining <= 0.0
            ):
                self.audio.play("audio/wolf_growl")
                wolf.growl_cooldown_remaining = settings.WOLF_GROWL_COOLDOWN

            if (
                not panic_played
                and nearest < settings.SHEEP_PANIC_DISTANCE
                and self._sheep_panic_cooldown <= 0.0
            ):
                self.audio.play("audio/sheep_panic")
                self._sheep_panic_cooldown = settings.SHEEP_PANIC_SOUND_COOLDOWN
                panic_played = True

    def _update_delayed_wave_audio(self, dt: float) -> None:
        if self._pending_wolf_howl_delay is None:
            return

        self._pending_wolf_howl_delay -= dt
        if self._pending_wolf_howl_delay <= 0.0:
            self.audio.play("audio/wolf_howl")
            self._pending_wolf_howl_delay = None

    def _next_sheep_bleat_time(self) -> float:
        return self.rng.uniform(*settings.SHEEP_BLEAT_INTERVAL_RANGE)

    def _render_herd_debug(self, surface: pygame.Surface) -> None:
        overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        center = self.session.player.rect.center
        pygame.draw.circle(
            overlay,
            (220, 220, 120, 55),
            center,
            round(settings.DOG_HERD_RADIUS),
            width=2,
        )
        pygame.draw.circle(
            overlay,
            (255, 160, 80, 65),
            center,
            round(settings.DOG_HERD_STRONG_RADIUS),
            width=2,
        )
        surface.blit(overlay, (0, 0))


class Game:
    """Pygame window, loop and state transitions."""

    def __init__(self) -> None:
        pygame.init()
        self.screen = pygame.display.set_mode(settings.WINDOW_SIZE)
        pygame.display.set_caption(settings.WINDOW_TITLE)
        self.clock = pygame.time.Clock()
        self.running = True
        self.assets = AssetManager()
        self.selected_difficulty = settings.DEFAULT_DIFFICULTY
        self._states: dict[GameState, object] = {
            GameState.SPLASH: SplashScreen(self.assets),
            GameState.MAIN_MENU: MenuScreen(self.assets, self.selected_difficulty),
            GameState.PLAYING: PlayingState(self.assets, self.selected_difficulty),
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
            self._states[GameState.MAIN_MENU] = MenuScreen(
                self.assets,
                self.selected_difficulty,
            )
        elif new_state == GameState.PLAYING:
            if self.current_state == GameState.MAIN_MENU:
                menu = self._states[GameState.MAIN_MENU]
                difficulty = getattr(
                    menu,
                    "selected_difficulty",
                    self.selected_difficulty,
                )
                self.selected_difficulty = normalize_difficulty(difficulty)
            self._states[GameState.PLAYING] = PlayingState(
                self.assets,
                self.selected_difficulty,
            )
        elif new_state == GameState.GAME_OVER:
            playing = self._states[GameState.PLAYING]
            score = getattr(playing, "final_score", 0)
            self._states[GameState.GAME_OVER] = GameOverScreen(
                self.assets,
                final_score=score,
            )

        self.current_state = new_state
