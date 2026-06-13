"""Výčet herních stavů.

Po Phase 0 se nemění bez konzultace s týmem.
"""
from enum import Enum, auto


class GameState(Enum):
    SPLASH = auto()
    MAIN_MENU = auto()
    PLAYING = auto()
    GAME_OVER = auto()
