"""HUD — herní rozhraní (skóre, level obtížnosti, čas, počet ovcí).

Layout:
- Levý horní roh: score velkým fontem, pod ním difficulty_level + elapsed_time
- Pravý horní roh: ikonky ovcí ukazující session.sheep_alive
- Volitelně: indikátor aktuálního wolf_speed_multiplier
"""
from __future__ import annotations

import pygame

from game import settings
from game.assets import AssetManager
from game.session import GameSession


class HUD:
    _MARGIN = 20
    _ICON_SIZE = 32
    _ICON_GAP = 6

    def __init__(self, assets: AssetManager) -> None:
        self._score_font = assets.font(48)
        self._info_font = assets.font(24)
        self._sheep_icon = self._create_sheep_icon()

    @classmethod
    def _create_sheep_icon(cls) -> pygame.Surface:
        icon = pygame.Surface((cls._ICON_SIZE, cls._ICON_SIZE), pygame.SRCALPHA)
        wool = settings.COLOR_TEXT
        head = settings.COLOR_FENCE
        pygame.draw.circle(icon, wool, (14, 16), 10)
        pygame.draw.circle(icon, wool, (8, 13), 6)
        pygame.draw.circle(icon, wool, (19, 11), 6)
        pygame.draw.ellipse(icon, head, (20, 13, 10, 11))
        pygame.draw.line(icon, head, (11, 23), (10, 30), 3)
        pygame.draw.line(icon, head, (19, 23), (20, 30), 3)
        return icon

    def render(self, surface: pygame.Surface, session: GameSession) -> None:
        """Vykreslí HUD na surface."""
        score = self._score_font.render(
            str(session.score), True, settings.COLOR_ACCENT,
        )
        surface.blit(score, (self._MARGIN, self._MARGIN))

        elapsed = max(0, int(session.elapsed_time))
        minutes, seconds = divmod(elapsed, 60)
        info = self._info_font.render(
            f"Level {session.difficulty_level}   {minutes:02d}:{seconds:02d}",
            True,
            settings.COLOR_TEXT,
        )
        surface.blit(info, (self._MARGIN, self._MARGIN + score.get_height()))

        speed = self._info_font.render(
            f"Wolf speed {session.wolf_speed_multiplier:.1f}x",
            True,
            settings.COLOR_TEXT_DIM,
        )
        surface.blit(
            speed,
            (self._MARGIN, self._MARGIN + score.get_height() + info.get_height()),
        )

        step = self._ICON_SIZE + self._ICON_GAP
        right = surface.get_width() - self._MARGIN
        for index in range(max(0, session.sheep_alive)):
            x = right - self._ICON_SIZE - index * step
            surface.blit(self._sheep_icon, (x, self._MARGIN))
