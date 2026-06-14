"""Shared gameplay session state."""
from __future__ import annotations

import random
from dataclasses import dataclass
from typing import TYPE_CHECKING, Callable, TypeVar

import pygame

from game import settings

if TYPE_CHECKING:
    from game.assets import AssetManager
    from game.effects import SheepLossMark
    from game.entities.player import Player
    from game.world.tilemap import TileMap


@dataclass
class GameSession:
    """Container for state shared while the game is in PLAYING."""

    tilemap: "TileMap"
    player: "Player"
    sheep_group: pygame.sprite.Group
    wolf_group: pygame.sprite.Group
    assets: "AssetManager | None" = None
    rng: random.Random | None = None
    score: int = 0
    elapsed_time: float = 0.0
    difficulty: str = settings.DEFAULT_DIFFICULTY
    wave: int = 1
    wolf_speed_multiplier: float = 1.0
    difficulty_level: int = 0
    speedups_required: int = settings.INITIAL_SPEEDUPS_BEFORE_SPAWN
    speedups_completed: int = 0
    wave_action: str | None = None
    wave_speed_before: float = 1.0
    wave_speed_after: float = 1.0
    wave_notice_remaining: float = 0.0
    sheep_warning_remaining: float = 0.0
    sheep_loss_marks: list["SheepLossMark"] | None = None
    sheep_loss_mark_counter: int = 0
    wolves_repelled: int = 0
    sheep_alive: int = 0
    game_over: bool = False


T = TypeVar("T", bound=pygame.sprite.Sprite)


def create_session(assets: "AssetManager",
                   tilemap: "TileMap",
                   rng: random.Random,
                   difficulty: str = settings.DEFAULT_DIFFICULTY) -> GameSession:
    """Create a complete gameplay session with player, sheep and wolves."""
    from game.entities.player import Player
    from game.entities.sheep import Sheep
    from game.entities.wolf import Wolf

    selected_difficulty = _normalize_difficulty(difficulty)
    occupied: list[pygame.Rect] = []

    player = _spawn_entity(
        lambda pos: Player(pos, assets),
        tilemap.random_grass_position,
        tilemap,
        occupied,
        rng,
    )

    sheep = [
        _spawn_entity(
            lambda pos: Sheep(pos, assets),
            tilemap.random_grass_position,
            tilemap,
            occupied,
            rng,
        )
        for _ in range(settings.INITIAL_SHEEP_COUNT)
    ]

    wolves = [
        _spawn_entity(
            lambda pos: Wolf(pos, settings.WOLF_BASE_SPEED, assets),
            tilemap.edge_spawn_position,
            tilemap,
            occupied,
            rng,
        )
        for _ in range(settings.INITIAL_WOLF_COUNT)
    ]

    return GameSession(
        tilemap=tilemap,
        player=player,
        sheep_group=pygame.sprite.Group(sheep),
        wolf_group=pygame.sprite.Group(wolves),
        assets=assets,
        rng=rng,
        difficulty=selected_difficulty,
        sheep_loss_marks=[],
        sheep_alive=sum(1 for item in sheep if item.alive),
    )


def _normalize_difficulty(difficulty: str) -> str:
    value = difficulty.lower()
    if value in settings.DIFFICULTY_CONFIG:
        return value
    return settings.DEFAULT_DIFFICULTY


def _spawn_entity(
    factory: Callable[[tuple[float, float]], T],
    position_source: Callable[[random.Random], tuple[float, float]],
    tilemap: "TileMap",
    occupied: list[pygame.Rect],
    rng: random.Random,
) -> T:
    fallback: T | None = None

    for _ in range(100):
        entity = factory(position_source(rng))
        if fallback is None:
            fallback = entity

        if tilemap.is_blocked_rect(entity.rect):
            continue
        if any(entity.rect.colliderect(rect) for rect in occupied):
            continue

        occupied.append(entity.rect.copy())
        return entity

    if fallback is None:
        fallback = factory(position_source(rng))
    occupied.append(fallback.rect.copy())
    return fallback
