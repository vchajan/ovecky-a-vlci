from __future__ import annotations

import os
import random
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame
import numpy as np

from game import settings
from game import assets as assets_module
from game.app import Game, PlayingState
from game.assets import AssetManager, SilentSound
from game.effects import SheepLossMark
from game.entities.player import Player
from game.entities.sheep import Sheep
from game.entities.wolf import Wolf
from game.session import GameSession, create_session
from game.states import GameState
from game.systems.collision import CollisionEvent, detect_collisions
from game.systems.difficulty import (
    DifficultyManager,
    get_speed_maximum,
)
from game.systems.rules import apply_collision_events, check_game_over
from game.systems.score import ScoreSystem
from game.world.tilemap import TileMap
from tools import generate_sounds


ROOT_DIR = Path(__file__).resolve().parents[1]


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


class SpyAudio:
    def __init__(self) -> None:
        self.played: list[str] = []

    def play(self, key: str) -> None:
        self.played.append(key)


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
        difficulty: str = settings.DEFAULT_DIFFICULTY,
    ) -> GameSession:
        return GameSession(
            tilemap=self.open_map,
            player=player or Player((500.0, 500.0), self.assets),
            sheep_group=sheep_group or pygame.sprite.Group(),
            wolf_group=wolf_group or pygame.sprite.Group(),
            assets=self.assets,
            rng=random.Random(5),
            difficulty=difficulty,
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

    def test_sheep_outside_herd_radius_ignores_dog(self) -> None:
        player = Player((100.0, 100.0), self.assets)
        sheep = Sheep((400.0, 100.0), self.assets)
        sheep.state_timer = 10.0

        sheep.update(0.25, self.open_map, player, pygame.sprite.Group(sheep))

        self.assertEqual(sheep.state, "idle")
        self.assertAlmostEqual(float(sheep.pos[0]), 400.0)
        self.assertAlmostEqual(float(sheep.pos[1]), 100.0)

    def test_sheep_inside_herd_radius_moves_away_from_dog(self) -> None:
        player = Player((100.0, 100.0), self.assets)
        sheep = Sheep((180.0, 100.0), self.assets)

        sheep.update(0.25, self.open_map, player, pygame.sprite.Group(sheep))

        self.assertEqual(sheep.state, "herded")
        self.assertGreater(float(sheep.pos[0]), 180.0)
        self.assertGreater(float(sheep.direction[0]), 0.0)
        self.assertAlmostEqual(float(np.linalg.norm(sheep.direction)), 1.0)

    def test_strong_herd_radius_moves_sheep_faster(self) -> None:
        player = Player((100.0, 100.0), self.assets)
        normal = Sheep((210.0, 100.0), self.assets)
        strong = Sheep((150.0, 100.0), self.assets)

        normal.update(0.2, self.open_map, player, pygame.sprite.Group(normal))
        strong.update(0.2, self.open_map, player, pygame.sprite.Group(strong))

        normal_delta = float(normal.pos[0] - 210.0)
        strong_delta = float(strong.pos[0] - 150.0)
        self.assertGreater(strong_delta, normal_delta)
        self.assertEqual(strong.herd_force, settings.DOG_HERD_STRONG_FORCE)

    def test_herded_state_returns_to_regular_behavior(self) -> None:
        sheep = Sheep((200.0, 200.0), self.assets)
        sheep.state = "herded"
        sheep.direction = np.array([1.0, 0.0], dtype=float)
        sheep.herd_remaining = 0.01

        sheep.update(0.2, self.open_map, None, pygame.sprite.Group(sheep))

        self.assertEqual(sheep.state, "wander")

    def test_herded_sheep_respects_fence(self) -> None:
        player = Player((20.0, 100.0), self.assets)
        sheep = Sheep((80.0, 100.0), self.assets)

        sheep.update(1.0, RightFenceTileMap(), player, pygame.sprite.Group(sheep))

        self.assertLessEqual(round(float(sheep.pos[0])), 80)

    def test_flock_cohesion_pulls_wandering_sheep_toward_neighbors(self) -> None:
        sheep = Sheep((200.0, 200.0), self.assets)
        neighbor = Sheep((300.0, 200.0), self.assets)
        sheep.state = "wander"
        sheep.state_timer = 10.0
        sheep.direction = np.array([0.0, 1.0], dtype=float)

        sheep.update(0.1, self.open_map, None, pygame.sprite.Group(sheep, neighbor))

        self.assertGreater(float(sheep.direction[0]), 0.0)

    def test_flock_separation_pushes_sheep_apart(self) -> None:
        sheep = Sheep((200.0, 200.0), self.assets)
        neighbor = Sheep((210.0, 200.0), self.assets)
        sheep.state = "wander"
        sheep.state_timer = 10.0
        sheep.direction = np.array([0.0, 1.0], dtype=float)

        sheep.update(0.1, self.open_map, None, pygame.sprite.Group(sheep, neighbor))

        self.assertLess(float(sheep.direction[0]), 0.0)

    def test_sheep_update_handles_single_or_empty_neighbor_group(self) -> None:
        sheep = Sheep((200.0, 200.0), self.assets)
        sheep.state = "wander"
        sheep.state_timer = 10.0
        sheep.direction = np.array([1.0, 0.0], dtype=float)

        sheep.update(0.1, self.open_map, None, pygame.sprite.Group(sheep))
        sheep.update(0.1, self.open_map, None, pygame.sprite.Group())

        self.assertTrue(sheep.alive)

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

        difficulty.update(settings.WAVE_INTERVAL, session)

        self.assertEqual(session.wave, 2)
        self.assertEqual(session.difficulty_level, 1)
        self.assertAlmostEqual(
            session.wolf_speed_multiplier,
            1.0 + settings.WOLF_SPEED_INCREASE_MEDIUM,
        )

    def test_create_session_builds_playable_groups(self) -> None:
        tilemap = TileMap()
        session = create_session(self.assets, tilemap, random.Random(7))

        self.assertEqual(len(session.sheep_group), settings.INITIAL_SHEEP_COUNT)
        self.assertEqual(len(session.wolf_group), settings.INITIAL_WOLF_COUNT)
        self.assertEqual(session.wave, 1)
        self.assertEqual(session.wolf_speed_multiplier, 1.0)
        self.assertEqual(session.sheep_alive, settings.INITIAL_SHEEP_COUNT)
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

    def test_game_over_uses_minimum_safe_sheep_count(self) -> None:
        session = self.make_session()

        session.sheep_alive = settings.INITIAL_SHEEP_COUNT
        self.assertFalse(check_game_over(session))

        session.sheep_alive = settings.MINIMUM_SHEEP_TO_CONTINUE
        self.assertFalse(check_game_over(session))

        session.sheep_alive = settings.MINIMUM_SHEEP_TO_CONTINUE - 1
        self.assertTrue(check_game_over(session))

        session.sheep_alive = 0
        self.assertTrue(check_game_over(session))

    def test_restart_restores_initial_sheep_count(self) -> None:
        game = Game()

        game._change_state(GameState.PLAYING)
        for sheep in list(game.state.session.sheep_group)[:6]:
            sheep.kill_sheep()
        game.state.session.sheep_alive = 2
        self.assertTrue(check_game_over(game.state.session))

        game._change_state(GameState.GAME_OVER)
        game._change_state(GameState.PLAYING)

        self.assertEqual(len(game.state.session.sheep_group), settings.INITIAL_SHEEP_COUNT)
        self.assertEqual(game.state.session.sheep_alive, settings.INITIAL_SHEEP_COUNT)
        self.assertEqual(game.state.session.sheep_loss_marks, [])
        game.running = False

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
        self.assertEqual(len(session.sheep_loss_marks or []), 1)
        self.assertEqual((session.sheep_loss_marks or [])[0].position, (100.0, 100.0))

    def test_sheep_loss_mark_persists_for_current_session(self) -> None:
        state = PlayingState(self.assets)
        state.session.sheep_loss_marks = [SheepLossMark((120.0, 140.0))]

        state._update_loss_marks(999.0)

        self.assertEqual(len(state.session.sheep_loss_marks), 1)
        self.assertEqual(state.session.sheep_loss_marks[0].position, (120.0, 140.0))

    def test_sheep_loss_mark_count_is_capped(self) -> None:
        sheep = [
            Sheep((100.0 + index * 5.0, 100.0), self.assets)
            for index in range(settings.MAX_BLOOD_STAINS + 5)
        ]
        wolf = Wolf((100.0, 100.0), 10.0, self.assets)
        session = self.make_session(
            sheep_group=pygame.sprite.Group(*sheep),
            wolf_group=pygame.sprite.Group(wolf),
        )
        session.sheep_alive = len(sheep)

        apply_collision_events(
            [
                CollisionEvent("wolf_eats_sheep", sheep=item, wolf=wolf)
                for item in sheep
            ],
            session,
            random.Random(4),
        )

        self.assertLessEqual(len(session.sheep_loss_marks or []), settings.MAX_BLOOD_STAINS)

    def test_sheep_loss_marks_do_not_affect_collisions(self) -> None:
        player = Player((500.0, 500.0), self.assets)
        sheep = Sheep((100.0, 100.0), self.assets)
        wolf = Wolf((100.0, 100.0), 10.0, self.assets)
        session = self.make_session(
            player=player,
            sheep_group=pygame.sprite.Group(sheep),
            wolf_group=pygame.sprite.Group(wolf),
        )
        session.sheep_loss_marks = [SheepLossMark((100.0, 100.0))]

        events = detect_collisions(player, session.sheep_group, session.wolf_group)

        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].kind, "wolf_eats_sheep")

    def test_sheep_loss_mark_renders_between_map_and_entities(self) -> None:
        state = PlayingState(self.assets)
        marker_position = (640.0, 360.0)
        state.session.sheep_loss_marks = [SheepLossMark(marker_position)]
        state.session.sheep_group.empty()
        state.session.wolf_group.empty()

        surface = pygame.Surface(settings.WINDOW_SIZE)
        state.render(surface)
        map_and_mark_pixel = surface.get_at((640, 360))[:3]

        sheep_sprite = pygame.sprite.Sprite()
        sheep_sprite.image = pygame.Surface((20, 20))
        sheep_sprite.image.fill((20, 40, 220))
        sheep_sprite.rect = sheep_sprite.image.get_rect(center=(640, 360))
        state.session.sheep_group = pygame.sprite.Group(sheep_sprite)

        state.render(surface)
        entity_pixel = surface.get_at((640, 360))[:3]

        self.assertNotEqual(map_and_mark_pixel, settings.COLOR_GRASS)
        self.assertEqual(entity_pixel, (20, 40, 220))

    def test_difficulties_share_initial_speed_wolves_and_wave(self) -> None:
        effective_speeds: list[float] = []
        for difficulty in settings.DIFFICULTIES:
            session = create_session(
                self.assets,
                self.open_map,
                random.Random(7),
                difficulty,
            )
            wolf = next(iter(session.wolf_group))
            effective_speeds.append(wolf.base_speed * session.wolf_speed_multiplier)
            self.assertEqual(len(session.wolf_group), settings.INITIAL_WOLF_COUNT)
            self.assertEqual(session.wave, 1)
            self.assertEqual(session.wolf_speed_multiplier, 1.0)

        self.assertEqual(
            effective_speeds,
            [settings.WOLF_BASE_SPEED] * len(settings.DIFFICULTIES),
        )

    def test_first_speedup_uses_configured_difficulty_values(self) -> None:
        multipliers: dict[str, float] = {}
        for difficulty in settings.DIFFICULTIES:
            session = create_session(
                self.assets,
                self.open_map,
                random.Random(8),
                difficulty,
            )
            DifficultyManager().advance_wave(session)
            multipliers[difficulty] = session.wolf_speed_multiplier

        self.assertAlmostEqual(
            multipliers["easy"],
            1.0 + settings.WOLF_SPEED_INCREASE_EASY,
        )
        self.assertAlmostEqual(
            multipliers["medium"],
            1.0 + settings.WOLF_SPEED_INCREASE_MEDIUM,
        )
        self.assertAlmostEqual(
            multipliers["hard"],
            1.0 + settings.WOLF_SPEED_INCREASE_HARD,
        )

    def test_wave_sequence_alternates_speedups_and_spawns(self) -> None:
        session = create_session(
            self.assets,
            self.open_map,
            random.Random(9),
            "medium",
        )
        manager = DifficultyManager()
        records = [
            (session.wave, len(session.wolf_group), session.wolf_speed_multiplier),
        ]
        actions: list[str] = []

        for _ in range(9):
            before_multiplier = session.wolf_speed_multiplier
            before_count = len(session.wolf_group)
            action = manager.advance_wave(session)
            actions.append(action)
            records.append(
                (
                    session.wave,
                    len(session.wolf_group),
                    session.wolf_speed_multiplier,
                ),
            )
            if action == "new_wolf":
                self.assertAlmostEqual(session.wolf_speed_multiplier, before_multiplier)
            if action == "speed_up":
                self.assertEqual(len(session.wolf_group), before_count)

        self.assertEqual([record[0] for record in records], list(range(1, 11)))
        self.assertEqual(
            [record[1] for record in records],
            [3, 3, 4, 4, 4, 5, 5, 5, 5, 6],
        )
        self.assertEqual(
            actions,
            [
                "speed_up",
                "new_wolf",
                "speed_up",
                "speed_up",
                "new_wolf",
                "speed_up",
                "speed_up",
                "speed_up",
                "new_wolf",
            ],
        )

    def test_spawn_sequence_is_same_for_all_difficulties(self) -> None:
        sequences: list[list[int]] = []
        for difficulty in settings.DIFFICULTIES:
            session = create_session(
                self.assets,
                self.open_map,
                random.Random(10),
                difficulty,
            )
            manager = DifficultyManager()
            counts = [len(session.wolf_group)]
            for _ in range(9):
                manager.advance_wave(session)
                counts.append(len(session.wolf_group))
            sequences.append(counts)

        self.assertEqual(sequences[0], sequences[1])
        self.assertEqual(sequences[1], sequences[2])

    def test_spawn_wave_resets_speedup_cycle(self) -> None:
        session = create_session(
            self.assets,
            self.open_map,
            random.Random(11),
            "medium",
        )
        manager = DifficultyManager()

        manager.advance_wave(session)
        manager.advance_wave(session)

        self.assertEqual(session.wave, 3)
        self.assertEqual(session.speedups_required, 2)
        self.assertEqual(session.speedups_completed, 0)

    def test_wolf_count_and_speed_multiplier_are_capped(self) -> None:
        session = create_session(
            self.assets,
            self.open_map,
            random.Random(12),
            "hard",
        )
        manager = DifficultyManager()

        for _ in range(80):
            manager.advance_wave(session)

        self.assertLessEqual(len(session.wolf_group), settings.WOLF_MAX_COUNT)
        self.assertLessEqual(
            session.wolf_speed_multiplier,
            get_speed_maximum("hard"),
        )

    def test_new_wolf_spawn_uses_valid_edge_position(self) -> None:
        tilemap = TileMap()
        session = create_session(self.assets, tilemap, random.Random(13), "medium")
        manager = DifficultyManager()

        manager.advance_wave(session)
        manager.advance_wave(session)
        new_wolf = list(session.wolf_group)[-1]

        self.assertFalse(tilemap.is_blocked_rect(new_wolf.rect))

    def test_replay_preserves_difficulty_and_resets_multiplier(self) -> None:
        game = Game()
        game.selected_difficulty = "hard"

        game._change_state(GameState.PLAYING)
        state = game.state
        state.difficulty_manager.advance_wave(state.session)
        self.assertGreater(state.session.wolf_speed_multiplier, 1.0)

        game._change_state(GameState.GAME_OVER)
        game._change_state(GameState.PLAYING)

        replay_state = game.state
        self.assertEqual(replay_state.session.difficulty, "hard")
        self.assertEqual(replay_state.session.wolf_speed_multiplier, 1.0)
        self.assertEqual(replay_state.session.wave, 1)
        game.running = False

    def test_menu_selection_changes_next_game_difficulty(self) -> None:
        game = Game()
        game._change_state(GameState.MAIN_MENU)
        menu = game.state
        menu._set_difficulty("easy")

        game._change_state(GameState.PLAYING)

        self.assertEqual(game.selected_difficulty, "easy")
        self.assertEqual(game.state.session.difficulty, "easy")
        game.running = False

    def test_spritesheet_pngs_exist_with_expected_sizes(self) -> None:
        expected = {
            "dog_sheet.png": (256, 256),
            "sheep_sheet.png": (256, 256),
            "wolf_sheet.png": (256, 512),
        }

        for filename, size in expected.items():
            path = ROOT_DIR / "assets" / "sprites" / filename
            self.assertTrue(path.is_file(), filename)
            image = pygame.image.load(str(path))
            self.assertEqual(image.get_size(), size)

    def test_directional_animations_have_four_distinct_frames(self) -> None:
        for key in (
            "sprites/dog/walk/down",
            "sprites/sheep/walk/right",
            "sprites/wolf/walk/left",
            "sprites/wolf/flee/up",
        ):
            animation = self.assets.animation(key)
            self.assertEqual(len(animation.frames), settings.SPRITE_FRAME_COUNT)
            self.assertTrue(
                all(
                    frame.get_size()
                    == (settings.SPRITE_FRAME_WIDTH, settings.SPRITE_FRAME_HEIGHT)
                    for frame in animation.frames
                ),
            )
            frame_bytes = {
                pygame.image.tostring(frame, "RGBA")
                for frame in animation.frames
            }
            self.assertGreater(len(frame_bytes), 1)

    def test_asset_manager_caches_sliced_animations(self) -> None:
        first = self.assets.animation("sprites/wolf/flee/right")
        second = self.assets.animation("sprites/wolf/flee/right")

        self.assertIs(first, second)

    def test_required_audio_keys_are_registered(self) -> None:
        expected = {
            "audio/wave_start",
            "audio/wolf_howl",
            "audio/wolf_growl",
            "audio/wolf_flee",
            "audio/sheep_bleat",
            "audio/sheep_panic",
            "audio/sheep_loss",
            "audio/dog_bark",
            "audio/game_over",
        }

        self.assertTrue(expected.issubset(assets_module.SOUND_FILES))

    def test_generate_sounds_does_not_overwrite_existing_wav_files(self) -> None:
        original_audio_dir = generate_sounds.AUDIO_DIR
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            existing = temp_path / "bark.wav"
            existing.write_bytes(b"real sound placeholder")
            generate_sounds.AUDIO_DIR = temp_path
            try:
                generate_sounds.main()
            finally:
                generate_sounds.AUDIO_DIR = original_audio_dir

            self.assertEqual(existing.read_bytes(), b"real sound placeholder")

        def test_asset_manager_loads_real_sound_files(self):
        """Real MP3 effects must be loaded instead of SilentSound."""
        if not pygame.mixer.get_init():
            try:
                pygame.mixer.init()
            except pygame.error as error:
                self.skipTest(f"Audio mixer is unavailable: {error}")

        assets = AssetManager()

        required_audio = [
            "audio/wave_start",
            "audio/wolf_howl",
            "audio/wolf_growl",
            "audio/wolf_flee",
            "audio/sheep_bleat",
            "audio/sheep_panic",
            "audio/sheep_loss",
            "audio/dog_bark",
            "audio/game_over",
        ]

        for key in required_audio:
            sound = assets.sound(key)

            self.assertNotIsInstance(
                sound,
                SilentSound,
                msg=f"{key} unexpectedly returned SilentSound",
            )

            duration = sound.get_length()

            self.assertGreater(
                duration,
                0.1,
                msg=f"{key} is empty or too short",
            )
            self.assertLessEqual(
                duration,
                3.05,
                msg=f"{key} is longer than 3 seconds: {duration:.2f}s",
            )
            
    required_audio = [
        "audio/wave_start",
        "audio/wolf_howl",
        "audio/wolf_growl",
        "audio/wolf_flee",
        "audio/sheep_bleat",
        "audio/sheep_panic",
        "audio/sheep_loss",
        "audio/dog_bark",
        "audio/game_over",
    ]

    for key in required_audio:
        sound = assets.sound(key)

        self.assertNotIsInstance(
            sound,
            SilentSound,
            msg=f"{key} unexpectedly returned SilentSound",
        )

        duration = sound.get_length()

        self.assertGreater(
            duration,
            0.1,
            msg=f"{key} is empty or too short",
        )
        self.assertLessEqual(
            duration,
            3.05,
            msg=f"{key} is longer than 3 seconds: {duration:.2f}s",
        )

    def test_asset_manager_uses_silent_sound_without_mixer(self) -> None:
        was_initialized = pygame.mixer.get_init() is not None
        pygame.mixer.quit()
        try:
            manager = AssetManager()
            sound = manager.sound("audio/sheep_bleat")
        finally:
            if was_initialized:
                try:
                    pygame.mixer.init()
                except pygame.error:
                    pass

        self.assertIsInstance(sound, SilentSound)

    def test_silent_sound_accepts_volume_api(self) -> None:
        sound = SilentSound()

        sound.set_volume(0.25)
        sound.play()

        self.assertIsNone(sound.play())

    def test_collision_audio_plays_once_per_event_kind(self) -> None:
        state = PlayingState(self.assets)
        state.audio = SpyAudio()
        sheep = Sheep((100.0, 100.0), self.assets)
        wolf = Wolf((100.0, 100.0), 10.0, self.assets)

        state._play_collision_audio(
            [
                CollisionEvent("dog_repels_wolf", wolf=wolf),
                CollisionEvent("dog_repels_wolf", wolf=wolf),
                CollisionEvent("wolf_eats_sheep", sheep=sheep, wolf=wolf),
                CollisionEvent("wolf_eats_sheep", sheep=sheep, wolf=wolf),
            ],
        )

        self.assertEqual(state.audio.played.count("audio/dog_bark"), 1)
        self.assertEqual(state.audio.played.count("audio/wolf_flee"), 1)
        self.assertEqual(state.audio.played.count("audio/sheep_loss"), 1)

    def test_wave_start_plays_once_when_wave_advances(self) -> None:
        state = PlayingState(self.assets)
        state.audio = SpyAudio()
        state._sheep_bleat_timer = 999.0
        state._sheep_panic_cooldown = 999.0
        state.session.wolf_group.empty()

        state.update(settings.WAVE_INTERVAL)

        self.assertEqual(state.audio.played.count("audio/wave_start"), 1)
        self.assertEqual(state.audio.played.count("audio/wolf_howl"), 0)

    def test_spawn_wave_plays_delayed_howl_once(self) -> None:
        state = PlayingState(self.assets)
        state.audio = SpyAudio()
        state._sheep_bleat_timer = 999.0
        state._sheep_panic_cooldown = 999.0
        state.session.wolf_group.empty()

        state.update(settings.WAVE_INTERVAL)
        state.update(settings.WAVE_INTERVAL)
        state.update(settings.WOLF_HOWL_DELAY - 0.01)
        self.assertEqual(state.audio.played.count("audio/wolf_howl"), 0)

        state.update(0.02)
        state.update(0.02)

        self.assertEqual(state.audio.played.count("audio/wolf_howl"), 1)

    def test_proximity_audio_cooldowns_prevent_frame_spam(self) -> None:
        state = PlayingState(self.assets)
        state.audio = SpyAudio()
        sheep = Sheep((100.0, 100.0), self.assets)
        wolf = Wolf((120.0, 100.0), 10.0, self.assets)
        state.session.sheep_group = pygame.sprite.Group(sheep)
        state.session.wolf_group = pygame.sprite.Group(wolf)

        state._update_proximity_audio(0.0)
        state._update_proximity_audio(0.1)

        self.assertEqual(state.audio.played.count("audio/wolf_growl"), 1)
        self.assertEqual(state.audio.played.count("audio/sheep_panic"), 1)

    def test_random_sheep_bleat_uses_shared_timer(self) -> None:
        state = PlayingState(self.assets)
        state.audio = SpyAudio()
        state._sheep_bleat_timer = 0.0

        state._update_bleat_audio(0.1)
        state._update_bleat_audio(0.1)

        self.assertEqual(state.audio.played.count("audio/sheep_bleat"), 1)

    def test_missing_spritesheet_uses_animation_fallback(self) -> None:
        old_path = assets_module.IMAGE_FILES["sprites/dog_sheet"]
        assets_module.IMAGE_FILES["sprites/dog_sheet"] = (
            ROOT_DIR / "assets" / "sprites" / "missing_dog_sheet.png"
        )
        try:
            manager = AssetManager()
            animation = manager.animation("sprites/dog/walk/down")
        finally:
            assets_module.IMAGE_FILES["sprites/dog_sheet"] = old_path

        self.assertEqual(len(animation.frames), settings.SPRITE_FRAME_COUNT)
        self.assertEqual(
            animation.frames[0].get_size(),
            (settings.SPRITE_FRAME_WIDTH, settings.SPRITE_FRAME_HEIGHT),
        )

    def test_wolf_starts_fleeing_opposite_last_direction(self) -> None:
        wolf = Wolf((100.0, 100.0), 10.0, self.assets)
        wolf.last_move_direction = np.array([1.0, 0.0], dtype=float)

        started = wolf.start_fleeing(np.array([90.0, 100.0], dtype=float))

        self.assertTrue(started)
        self.assertEqual(wolf.state, "fleeing")
        self.assertAlmostEqual(float(wolf.flee_direction[0]), -1.0)
        self.assertAlmostEqual(float(wolf.flee_direction[1]), 0.0)
        self.assertFalse(wolf.is_active)
        self.assertTrue(wolf.is_visible)

    def test_fleeing_wolf_does_not_create_collision_events(self) -> None:
        player = Player((100.0, 100.0), self.assets)
        sheep = Sheep((100.0, 100.0), self.assets)
        wolf = Wolf((100.0, 100.0), 10.0, self.assets)
        wolf.start_fleeing(player.pos)

        events = detect_collisions(
            player,
            pygame.sprite.Group(sheep),
            pygame.sprite.Group(wolf),
        )

        self.assertEqual(events, [])

    def test_wolf_flee_respawn_cycle(self) -> None:
        player = Player((100.0, 100.0), self.assets)
        sheep = Sheep((300.0, 100.0), self.assets)
        wolf = Wolf((120.0, 100.0), 10.0, self.assets)
        session = self.make_session(
            player=player,
            sheep_group=pygame.sprite.Group(sheep),
            wolf_group=pygame.sprite.Group(wolf),
        )

        wolf.last_move_direction = np.array([1.0, 0.0], dtype=float)
        wolf.start_fleeing(player.pos)
        wolf.update(0.5, session)

        self.assertEqual(wolf.state, "fleeing")
        self.assertIs(wolf.animation, wolf.animations["flee"][wolf.direction])

        wolf.update(settings.WOLF_FLEE_DURATION, session)

        self.assertEqual(wolf.state, "respawning")
        self.assertFalse(wolf.is_active)
        self.assertFalse(wolf.is_visible)
        self.assertEqual(wolf.respawn_remaining, settings.WOLF_RESPAWN_DELAY)

        wolf.update(settings.WOLF_RESPAWN_DELAY, session)

        self.assertEqual(wolf.state, "chasing")
        self.assertTrue(wolf.is_active)
        self.assertTrue(wolf.is_visible)
        self.assertEqual(tuple(wolf.rect.center), (32, 352))

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
