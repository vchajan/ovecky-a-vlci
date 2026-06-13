"""GameSession — sdílený kontejner herního stavu během hraní.

Po Phase 0 se dataclass NEMĚNÍ bez konzultace s týmem.
Atributy lze přidávat po dohodě, nelze měnit typ ani odebírat.

Factory ``create_session`` se implementuje v Phase 2 (integrace),
když Lane C má hotové Player/Sheep/Wolf. V Phase 1 si Lane A vystačí
s placeholder PLAYING obrazovkou.
"""
from __future__ import annotations

import random
from dataclasses import dataclass
from typing import TYPE_CHECKING

import pygame

if TYPE_CHECKING:
    from game.assets import AssetManager
    from game.entities.player import Player
    from game.world.tilemap import TileMap


@dataclass
class GameSession:
    """Sdílený kontejner stavu během stavu PLAYING."""

    tilemap: "TileMap"
    player: "Player"
    sheep_group: pygame.sprite.Group
    wolf_group: pygame.sprite.Group
    score: int = 0
    elapsed_time: float = 0.0
    wolf_speed_multiplier: float = 1.0   # roste s časem, řízeno DifficultyManagerem
    difficulty_level: int = 0            # kolikrát už proběhl ramp-up (pro HUD)
    wolves_repelled: int = 0             # statistika pro skóre
    sheep_alive: int = 0                 # cache pro rychlou kontrolu game-over
    game_over: bool = False


def create_session(assets: "AssetManager",
                   tilemap: "TileMap",
                   rng: random.Random) -> GameSession:
    """Vytvoří kompletní GameSession s počátečními entitami.

    Spawnuje SHEEP_COUNT ovcí na trávě a WOLF_COUNT vlků na okraji mapy.

    Implementace v Phase 2 integraci, kdy budou hotové Player/Sheep/Wolf.
    """
    raise NotImplementedError(
        "create_session se implementuje v Phase 2 integraci. "
        "Vyžaduje hotové Player, Sheep a Wolf z Lane C."
    )
