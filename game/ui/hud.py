"""HUD — herní rozhraní (skóre, level obtížnosti, čas, počet ovcí).

# TODO Lane D
Layout:
- Levý horní roh: score velkým fontem, pod ním difficulty_level + elapsed_time
- Pravý horní roh: ikonky ovcí ukazující session.sheep_alive
- Volitelně: indikátor aktuálního wolf_speed_multiplier
"""
from __future__ import annotations

import pygame

from game.session import GameSession


class HUD:
    def __init__(self, assets) -> None:
        # TODO Lane D
        self.assets = assets

    def render(self, surface: pygame.Surface, session: GameSession) -> None:
        """Vykreslí HUD na surface."""
        # TODO Lane D
        pass
