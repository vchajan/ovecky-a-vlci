from __future__ import annotations

import os
import random
import unittest

os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame

from game import settings
from game.app import Game, PlayingState
from game.assets import AssetManager
from game.entities.player import Player
from game.entities.sheep import Sheep
from game.entities.wolf import Wolf
from game.session import GameSession, create_session
from game.states import GameState
from game.systems.collision import CollisionEvent, detect_collisions
from game.systems.difficulty import DifficultyManager
from game.systems.rules import apply_collision_events, check_game_over
from game.systems.score import ScoreSystem
from game.world.tilemap import TileMap


class KeyState:
    def __init__(self, pressed: set[int]) -> None:
        self.pressed = pressed

    def __getitem__(self, key: int) -> bool:
        return key in self.pressed


class OpenTileMap:
    def is_blocked_rect(self, rect: pygame.Rect) -> bool:
        return False

    def random_grass_position(self, rng: random.Random) -> tuple[float, float]:
        return (rng.uniform(96.0, 1184.0), rng.uniform(96.0, 624.0))

    def edge_spawn_position(self, rng: random.Random) -> tuple[float, float]:
        return (32.0, 352.0)


class RightFenceTileMap(OpenTileMap):
    def is_blocked_rect(self, rect: pygame.Rect) -> bool:
        return rect.right > 120


def setUpModule() -> None:
    pygame.init()
    pygame.display.set_mode((1, 1))


def tearDownModule() -> None:
    pygame.quit()


class Phase2IntegrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.assets = AssetManager()
        self.open_map = OpenTileMap()

    def make_session(
        self,
        player: Player | None = None,
        sheep_group: pygame.sprite.Group | None = None,
        wolf_group: pygame.sprite.Group | None = None,
    ) -> GameSession:
        return GameSession(
            tilemap=self.open_map,
            player=player or Player((500.0, 500.0), self.assets),
            sheep_group=sheep_group or pygame.sprite.Group(),
            wolf_group=wolf_group or pygame.sprite.Group(),
            sheep_alive=len(sheep_group or ()),
        )

    def test_player_diagonal_movement_is_normalized(self) -> None:
        player = Player((200.0, 200.0), self.assets)
        keys = KeyState({pygame.K_d, pygame.K_s})

        player.update(0.25, keys, self.open_map)

        moved = player.pos - [200.0, 200.0]
        self.assertAlmostEqual(
            float((moved[0] ** 2 + moved[1] ** 2) ** 0.5),
            settings.PLAYER_SPEED * 0.25,
            places=5,
        )

    def test_player_does_not_walk_through_fence(self) -> None:
        player = Player((80.0, 100.0), self.assets)

        player.update(1.0, KeyState({pygame.K_d}), RightFenceTileMap())

        self.assertEqual(round(float(player.pos[0])), 80)

    def test_sheep_switches_idle_and_wander_states(self) -> None:
        sheep = Sheep((200.0, 200.0), self.assets)

        sheep.state_timer = 0.0
        sheep.update(0.1, self.open_map)
        self.assertEqual(sheep.state, "wander")

        sheep.state_timer = 0.0
        sheep.update(0.1, self.open_map)
        self.assertEqual(sheep.state, "idle")

    def test_wolf_finds_nearest_sheep(self) -> None:
        near = Sheep((100.0, 0.0), self.assets)
        far = Sheep((0.0, 500.0), self.assets)
        wolf = Wolf((0.0, 0.0), 20.0, self.assets)
        session = self.make_session(
            sheep_group=pygame.sprite.Group(near, far),
            wolf_group=pygame.sprite.Group(wolf),
        )

        wolf.update(1.0, session)

        self.assertGreater(float(wolf.pos[0]), 0.0)
        self.assertAlmostEqual(float(wolf.pos[1]), 0.0, places=5)

    def test_wolf_moves_in_expected_direction(self) -> None:
        sheep = Sheep((0.0, 100.0), self.assets)
        wolf = Wolf((0.0, 0.0), 30.0, self.assets)
        session = self.make_session(
            sheep_group=pygame.sprite.Group(sheep),
            wolf_group=pygame.sprite.Group(wolf),
        )

        wolf.update(1.0, session)

        self.assertAlmostEqual(float(wolf.pos[0]), 0.0, places=5)
        self.assertGreater(float(wolf.pos[1]), 0.0)

    def test_inactive_wolf_is_ignored_by_collision_detection(self) -> None:
        player = Player((100.0, 100.0), self.assets)
        sheep = Sheep((100.0, 100.0), self.assets)
        wolf = Wolf((100.0, 100.0), 10.0, self.assets)
        wolf.trigger_respawn(3.0, (100.0, 100.0))

        events = detect_collisions(
            player,
            pygame.sprite.Group(sheep),
            pygame.sprite.Group(wolf),
        )

        self.assertEqual(events, [])

    def test_wolf_eats_sheep_event(self) -> None:
        player = Player((500.0, 500.0), self.assets)
        sheep = Sheep((100.0, 100.0), self.assets)
        wolf = Wolf((100.0, 100.0), 10.0, self.assets)

        events = detect_collisions(
            player,
            pygame.sprite.Group(sheep),
            pygame.sprite.Group(wolf),
        )

        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].kind, "wolf_eats_sheep")
        self.assertIs(events[0].sheep, sheep)
        self.assertIs(events[0].wolf, wolf)

    def test_dog_repels_wolf_event(self) -> None:
        player = Player((100.0, 100.0), self.assets)
        sheep = Sheep((500.0, 500.0), self.assets)
        wolf = Wolf((100.0, 100.0), 10.0, self.assets)

        events = detect_collisions(
            player,
            pygame.sprite.Group(sheep),
            pygame.sprite.Group(wolf),
        )

        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].kind, "dog_repels_wolf")
        self.assertIs(events[0].wolf, wolf)

    def test_score_system_counts_valid_repels_and_time(self) -> None:
        wolf = Wolf((100.0, 100.0), 10.0, self.assets)
        session = self.make_session(wolf_group=pygame.sprite.Group(wolf))
        score = ScoreSystem()
        event = CollisionEvent("dog_repels_wolf", wolf=wolf)

        score.process_events([event, event], session)
        score.tick(1.2, session)

        self.assertEqual(session.wolves_repelled, 1)
        self.assertEqual(
            session.score,
            settings.SCORE_PER_WOLF_REPELLED + settings.SCORE_PER_SECOND,
        )

        wolf.trigger_respawn(3.0, (32.0, 352.0))
        score.process_events([event], session)
        self.assertEqual(session.wolves_repelled, 1)

    def test_difficulty_manager_ramps_speed(self) -> None:
        session = self.make_session()
        difficulty = DifficultyManager()

        difficulty.update(settings.DIFFICULTY_RAMP_INTERVAL, session)

        self.assertEqual(session.difficulty_level, 1)
        self.assertAlmostEqual(
            session.wolf_speed_multiplier,
            1.0 + settings.DIFFICULTY_SPEED_INCREMENT,
        )

    def test_create_session_builds_playable_groups(self) -> None:
        tilemap = TileMap()
        session = create_session(self.assets, tilemap, random.Random(7))

        self.assertEqual(len(session.sheep_group), settings.SHEEP_COUNT)
        self.assertEqual(len(session.wolf_group), settings.WOLF_COUNT)
        self.assertEqual(session.sheep_alive, settings.SHEEP_COUNT)
        self.assertFalse(tilemap.is_blocked_rect(session.player.rect))

        all_sprites = [
            session.player,
            *list(session.sheep_group),
            *list(session.wolf_group),
        ]
        self.assertTrue(all(not tilemap.is_blocked_rect(sprite.rect)
                            for sprite in all_sprites))
        self.assertGreater(len({sprite.rect.center for sprite in all_sprites}), 1)

    def test_game_over_at_zero_sheep(self) -> None:
        state = PlayingState(self.assets)
        for sheep in list(state.session.sheep_group):
            sheep.kill_sheep()
        state.session.sheep_alive = 0

        self.assertEqual(state.update(1 / 60), GameState.GAME_OVER)
        self.assertTrue(check_game_over(state.session))

    def test_asset_manager_fallbacks_and_animations(self) -> None:
        fallback = self.assets.image("missing/asset")
        self.assertEqual(fallback.get_size(), (settings.TILE_SIZE, settings.TILE_SIZE))

        self.assertEqual(
            self.assets.animation("sprites/dog").current_frame(0).get_size(),
            (48, 48),
        )
        self.assertEqual(
            self.assets.animation("sprites/sheep").current_frame(0).get_size(),
            (40, 40),
        )
        self.assertEqual(
            self.assets.animation("sprites/wolf").current_frame(0).get_size(),
            (48, 48),
        )

    def test_tilemap_spawn_positions_are_visible_and_passable(self) -> None:
        tilemap = TileMap()
        rng = random.Random(11)

        for position in (
            tilemap.random_grass_position(rng),
            tilemap.edge_spawn_position(rng),
        ):
            x, y = position
            self.assertGreaterEqual(x, 0.0)
            self.assertLessEqual(x, settings.WINDOW_WIDTH)
            self.assertGreaterEqual(y, 0.0)
            self.assertLessEqual(y, settings.WINDOW_HEIGHT)
            self.assertFalse(tilemap.is_blocked_pixel(x, y))
            rect = pygame.Rect(0, 0, 10, 10)
            rect.center = (round(x), round(y))
            self.assertFalse(tilemap.is_blocked_rect(rect))

    def test_apply_collision_events_is_safe_and_clamps_sheep_alive(self) -> None:
        sheep = Sheep((100.0, 100.0), self.assets)
        wolf = Wolf((100.0, 100.0), 10.0, self.assets)
        session = self.make_session(
            sheep_group=pygame.sprite.Group(sheep),
            wolf_group=pygame.sprite.Group(wolf),
        )
        session.sheep_alive = 1

        apply_collision_events(
            [
                CollisionEvent("wolf_eats_sheep", sheep=sheep, wolf=wolf),
                CollisionEvent("wolf_eats_sheep", sheep=sheep, wolf=wolf),
                CollisionEvent("wolf_eats_sheep"),
                CollisionEvent("dog_repels_wolf"),
                CollisionEvent("dog_repels_wolf", wolf=wolf),
            ],
            session,
            random.Random(3),
        )

        self.assertEqual(session.sheep_alive, 0)
        self.assertFalse(sheep.alive)
        self.assertFalse(wolf.is_active)

    def test_dummy_video_game_smoke_flow(self) -> None:
        game = Game()

        self.assertEqual(game.current_state, GameState.SPLASH)
        game._update(settings.SPLASH_DURATION)
        self.assertEqual(game.current_state, GameState.MAIN_MENU)

        game._change_state(GameState.PLAYING)
        self.assertEqual(game.current_state, GameState.PLAYING)
        self.assertIsNotNone(game.state.session)

        for _ in range(3):
            game._update(1 / 60)
            game._render()

        game.running = False
