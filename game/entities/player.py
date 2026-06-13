"""Player entity controlled by the keyboard."""
from __future__ import annotations

import numpy as np
import pygame

from game import settings
from game.animation import Animation
from game.assets import AssetManager
from game.world.tilemap import TileMap


def _looks_like_missing_asset(surface: pygame.Surface) -> bool:
    if surface.get_width() <= 1 or surface.get_height() <= 1:
        return True

    placeholder = settings.COLOR_PLACEHOLDER
    corners = (
        (0, 0),
        (surface.get_width() - 1, 0),
        (0, surface.get_height() - 1),
        (surface.get_width() - 1, surface.get_height() - 1),
    )
    return all(surface.get_at(point)[:3] == placeholder for point in corners)


def _dog_placeholder() -> pygame.Surface:
    surface = pygame.Surface((48, 48), pygame.SRCALPHA)
    pygame.draw.ellipse(surface, (125, 82, 46), pygame.Rect(8, 14, 32, 26))
    pygame.draw.circle(surface, (92, 58, 34), (27, 14), 12)
    pygame.draw.circle(surface, (30, 24, 20), (32, 12), 3)
    return surface


class Player(pygame.sprite.Sprite):
    """Dog controlled by the player with WASD or arrow keys."""

    def __init__(self, pos: tuple[float, float], assets: AssetManager) -> None:
        super().__init__()
        self.pos = np.array(pos, dtype=float)
        self.speed = settings.PLAYER_SPEED
        self.direction = "down"
        self.animation_time = 0.0
        self.animation: Animation | None = assets.animation("sprites/dog")

        first_frame = self.animation.current_frame(0.0)
        if _looks_like_missing_asset(first_frame):
            self.animation = None
            self.image = _dog_placeholder()
        else:
            self.image = first_frame

        self.rect = self.image.get_rect()
        self._sync_rect()

    def update(self, dt: float, keys: pygame.key.ScancodeWrapper,
               tilemap: TileMap) -> None:
        """Move the player and block movement against the tile map."""
        movement = np.array([0.0, 0.0], dtype=float)

        if keys[pygame.K_w] or keys[pygame.K_UP]:
            movement[1] -= 1.0
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            movement[1] += 1.0
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            movement[0] -= 1.0
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            movement[0] += 1.0

        length = float(np.linalg.norm(movement))
        if length > 0.0:
            movement /= length
            self._update_direction(movement)
            offset = movement * self.speed * dt
            self._move_axis(0, float(offset[0]), tilemap)
            self._move_axis(1, float(offset[1]), tilemap)
            self.animation_time += dt

        self._update_image()

    def _move_axis(self, axis: int, amount: float, tilemap: TileMap) -> None:
        if amount == 0.0:
            return

        next_pos = self.pos.copy()
        next_pos[axis] += amount

        test_rect = self.rect.copy()
        if axis == 0:
            test_rect.centerx = round(float(next_pos[0]))
        else:
            test_rect.centery = round(float(next_pos[1]))

        if not tilemap.is_blocked_rect(test_rect):
            self.pos[axis] = next_pos[axis]
            self._sync_rect()

    def _sync_rect(self) -> None:
        self.rect.center = (
            round(float(self.pos[0])),
            round(float(self.pos[1])),
        )

    def _update_direction(self, movement: np.ndarray) -> None:
        if abs(float(movement[0])) >= abs(float(movement[1])):
            self.direction = "right" if movement[0] > 0.0 else "left"
        else:
            self.direction = "down" if movement[1] > 0.0 else "up"

    def _update_image(self) -> None:
        if self.animation is None:
            return

        frame = self.animation.current_frame(self.animation_time)
        if _looks_like_missing_asset(frame):
            return

        center = self.rect.center
        self.image = frame
        self.rect = self.image.get_rect(center=center)
