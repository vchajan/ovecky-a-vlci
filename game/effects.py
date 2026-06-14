"""Lightweight visual effects for gameplay."""
from __future__ import annotations

import pygame

from game import settings


class SheepLossMark:
    """A stylized red mark left where a sheep was lost."""

    def __init__(self, position: tuple[float, float]) -> None:
        self.position = (float(position[0]), float(position[1]))
        self.age = 0.0
        self.image = self._create_image()

    @property
    def expired(self) -> bool:
        return self.age >= settings.BLOOD_STAIN_DURATION

    def update(self, dt: float) -> None:
        self.age = min(settings.BLOOD_STAIN_DURATION, self.age + dt)

    def render(self, surface: pygame.Surface) -> None:
        alpha = self._alpha()
        if alpha <= 0:
            return

        image = self.image.copy()
        image.set_alpha(alpha)
        rect = image.get_rect(
            center=(round(self.position[0]), round(self.position[1])),
        )
        surface.blit(image, rect)

    def _alpha(self) -> int:
        fade_start = settings.BLOOD_STAIN_DURATION * 0.7
        if self.age <= fade_start:
            return 170

        fade_span = max(0.01, settings.BLOOD_STAIN_DURATION - fade_start)
        progress = min(1.0, (self.age - fade_start) / fade_span)
        return round(170 * (1.0 - progress))

    @staticmethod
    def _create_image() -> pygame.Surface:
        surface = pygame.Surface((42, 32), pygame.SRCALPHA)
        dark = (105, 12, 18, 165)
        mid = (150, 22, 28, 150)
        light = (190, 45, 42, 120)
        pygame.draw.ellipse(surface, dark, pygame.Rect(7, 10, 25, 13))
        pygame.draw.ellipse(surface, mid, pygame.Rect(14, 6, 16, 11))
        pygame.draw.circle(surface, light, (31, 18), 4)
        pygame.draw.circle(surface, dark, (10, 23), 3)
        pygame.draw.rect(surface, mid, pygame.Rect(22, 20, 4, 3))
        pygame.draw.rect(surface, dark, pygame.Rect(34, 14, 3, 3))
        return surface
