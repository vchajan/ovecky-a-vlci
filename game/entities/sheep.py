"""Sheep entity with a small idle/wander behaviour."""
from __future__ import annotations

import random

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


def _sheep_placeholder() -> pygame.Surface:
    surface = pygame.Surface((40, 40), pygame.SRCALPHA)
    pygame.draw.ellipse(surface, (245, 245, 235), pygame.Rect(4, 9, 30, 24))
    pygame.draw.circle(surface, (235, 235, 225), (29, 16), 8)
    pygame.draw.circle(surface, (35, 35, 35), (32, 14), 2)
    return surface


def _random_timer() -> float:
    return random.uniform(*settings.SHEEP_IDLE_RANGE)


class Sheep(pygame.sprite.Sprite):
    """Sheep that alternates between standing and wandering."""

    def __init__(self, pos: tuple[float, float], assets: AssetManager) -> None:
        super().__init__()
        self.pos = np.array(pos, dtype=float)
        self.direction = np.array([0.0, 0.0], dtype=float)
        self.speed = settings.SHEEP_SPEED
        self.alive = True
        self.state = "idle"
        self.state_timer = _random_timer()
        self.animation_time = 0.0
        self.animation: Animation | None = assets.animation("sprites/sheep")

        first_frame = self.animation.current_frame(0.0)
        if _looks_like_missing_asset(first_frame):
            self.animation = None
            self.image = _sheep_placeholder()
        else:
            self.image = first_frame

        self.rect = self.image.get_rect()
        self._sync_rect()

    def update(self, dt: float, tilemap: TileMap) -> None:
        """Update the sheep random walk."""
        if not self.alive:
            return

        self.state_timer -= dt

        if self.state == "idle":
            if self.state_timer <= 0.0:
                self._start_wander()
        elif self.state == "wander":
            collided = self._move(tilemap, dt)
            if collided or self.state_timer <= 0.0:
                self._start_idle()
            else:
                self.animation_time += dt
        else:
            self._start_idle()

        self._update_image()

    def kill_sheep(self) -> None:
        """Mark the sheep as dead and remove it from sprite groups."""
        if not self.alive:
            return

        self.alive = False
        self.kill()

    def _start_idle(self) -> None:
        self.state = "idle"
        self.direction = np.array([0.0, 0.0], dtype=float)
        self.state_timer = _random_timer()

    def _start_wander(self) -> None:
        self.state = "wander"
        angle = random.uniform(0.0, 2.0 * np.pi)
        self.direction = np.array(
            [np.cos(angle), np.sin(angle)],
            dtype=float,
        )
        self.state_timer = _random_timer()

    def _move(self, tilemap: TileMap, dt: float) -> bool:
        offset = self.direction * self.speed * dt
        collided = False

        if float(offset[0]) != 0.0:
            collided = self._move_axis(0, float(offset[0]), tilemap) or collided
        if float(offset[1]) != 0.0:
            collided = self._move_axis(1, float(offset[1]), tilemap) or collided

        return collided

    def _move_axis(self, axis: int, amount: float, tilemap: TileMap) -> bool:
        next_pos = self.pos.copy()
        next_pos[axis] += amount

        test_rect = self.rect.copy()
        if axis == 0:
            test_rect.centerx = round(float(next_pos[0]))
        else:
            test_rect.centery = round(float(next_pos[1]))

        if tilemap.is_blocked_rect(test_rect):
            return True

        self.pos[axis] = next_pos[axis]
        self._sync_rect()
        return False

    def _sync_rect(self) -> None:
        self.rect.center = (
            round(float(self.pos[0])),
            round(float(self.pos[1])),
        )

    def _update_image(self) -> None:
        if self.animation is None:
            return

        frame = self.animation.current_frame(self.animation_time)
        if _looks_like_missing_asset(frame):
            return

        center = self.rect.center
        self.image = frame
        self.rect = self.image.get_rect(center=center)
