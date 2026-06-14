"""Lightweight visual effects for gameplay."""
from __future__ import annotations

import random

import pygame

from game import settings


class SheepLossMark:
    """A stylized red mark left where a sheep was lost."""

    def __init__(self, position: tuple[float, float], variant: int = 0) -> None:
        self.position = (float(position[0]), float(position[1]))
        self.variant = int(variant)
        self.image = self._create_image(self.variant)
        self.rect = self.image.get_rect(
            center=(round(self.position[0]), round(self.position[1])),
        )

    @property
    def expired(self) -> bool:
        return False

    def update(self, dt: float) -> None:
        return None

    def render(self, surface: pygame.Surface) -> None:
        surface.blit(self.image, self.rect)

    @staticmethod
    def _create_image(variant: int) -> pygame.Surface:
        width, height = settings.BLOOD_STAIN_SIZE
        surface = pygame.Surface((width, height), pygame.SRCALPHA)
        rng = random.Random(variant)
        dark = (*settings.BLOOD_DARK, 235)
        mid = (*settings.BLOOD_MAIN, 220)
        light = (*settings.BLOOD_LIGHT, 170)

        center = (width // 2, height // 2)
        pygame.draw.ellipse(
            surface,
            mid,
            pygame.Rect(5, 8, width - 12, height - 16),
        )
        pygame.draw.ellipse(
            surface,
            dark,
            pygame.Rect(11, 12, width - 24, height - 22),
        )

        for _ in range(7):
            radius_x = rng.randint(4, 10)
            radius_y = rng.randint(3, 7)
            x = rng.randint(4, width - radius_x - 4)
            y = rng.randint(4, height - radius_y - 4)
            color = mid if rng.random() < 0.7 else dark
            pygame.draw.ellipse(
                surface,
                color,
                pygame.Rect(x, y, radius_x * 2, radius_y * 2),
            )

        for _ in range(6):
            offset_x = rng.randint(-width // 2 + 4, width // 2 - 4)
            offset_y = rng.randint(-height // 2 + 3, height // 2 - 3)
            radius = rng.randint(2, 5)
            color = light if rng.random() < 0.35 else dark
            pygame.draw.circle(
                surface,
                color,
                (center[0] + offset_x, center[1] + offset_y),
                radius,
            )

        return surface
