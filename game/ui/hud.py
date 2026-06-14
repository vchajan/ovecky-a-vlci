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
        elapsed = max(0, int(session.elapsed_time))
        minutes, seconds = divmod(elapsed, 60)
        lines = (
            f"Difficulty: {session.difficulty.upper()}",
            f"Wave: {session.wave}",
            f"Wolves: {len(session.wolf_group)}",
            f"Speed: {session.wolf_speed_multiplier:.2f}x",
            f"Score: {session.score}",
            f"Time: {minutes:02d}:{seconds:02d}",
            f"Sheep: {session.sheep_alive} / {settings.INITIAL_SHEEP_COUNT}",
            f"Minimum: {settings.MINIMUM_SHEEP_TO_CONTINUE}",
            f"Speed-ups: {session.speedups_completed} / {session.speedups_required}",
        )

        y = self._MARGIN
        for index, line in enumerate(lines):
            color = settings.COLOR_ACCENT if index == 4 else settings.COLOR_TEXT
            if index in (3, 8):
                color = settings.COLOR_TEXT_DIM
            if index in (6, 7) and session.sheep_alive <= settings.MINIMUM_SHEEP_TO_CONTINUE:
                color = (235, 95, 75)
            text = self._info_font.render(line, True, color)
            surface.blit(text, (self._MARGIN, y))
            y += text.get_height() + 2

        step = self._ICON_SIZE + self._ICON_GAP
        right = surface.get_width() - self._MARGIN
        for index in range(max(0, session.sheep_alive)):
            x = right - self._ICON_SIZE - index * step
            surface.blit(self._sheep_icon, (x, self._MARGIN))

        if session.wave_notice_remaining > 0.0 and session.wave_action:
            self._render_wave_notice(surface, session)
        if session.sheep_warning_remaining > 0.0:
            self._render_sheep_warning(surface)

    def _render_wave_notice(
        self,
        surface: pygame.Surface,
        session: GameSession,
    ) -> None:
        action = (
            "WOLVES SPEED UP"
            if session.wave_action == "speed_up"
            else "NEW WOLF"
        )
        title = self._score_font.render(
            f"WAVE {session.wave}",
            True,
            settings.COLOR_ACCENT,
        )
        subtitle = self._info_font.render(action, True, settings.COLOR_TEXT)
        speed_line = None
        if session.wave_action == "speed_up":
            speed_line = self._info_font.render(
                (
                    f"Speed {session.wave_speed_before:.2f}x "
                    f"-> {session.wave_speed_after:.2f}x"
                ),
                True,
                settings.COLOR_TEXT_DIM,
            )
        center_x = surface.get_width() // 2
        center_y = int(surface.get_height() * 0.22)
        title_rect = title.get_rect(center=(center_x, center_y))
        subtitle_rect = subtitle.get_rect(center=(center_x, title_rect.bottom + 18))
        surface.blit(title, title_rect)
        surface.blit(subtitle, subtitle_rect)
        if speed_line is not None:
            speed_rect = speed_line.get_rect(
                center=(center_x, subtitle_rect.bottom + 16),
            )
            surface.blit(speed_line, speed_rect)

    def _render_sheep_warning(self, surface: pygame.Surface) -> None:
        warning = self._info_font.render(
            "WARNING: LAST SAFE SHEEP",
            True,
            (245, 120, 70),
        )
        rect = warning.get_rect(
            center=(surface.get_width() // 2, int(surface.get_height() * 0.34)),
        )
        surface.blit(warning, rect)
