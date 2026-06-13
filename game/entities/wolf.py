"""Wolf entity with chase AI and respawn handling."""
from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
import pygame

from game import settings
from game.animation import Animation
from game.assets import AssetManager

if TYPE_CHECKING:
    from game.session import GameSession
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


def _wolf_placeholder() -> pygame.Surface:
    surface = pygame.Surface((48, 48), pygame.SRCALPHA)
    pygame.draw.ellipse(surface, (100, 105, 110), pygame.Rect(7, 15, 33, 23))
    pygame.draw.circle(surface, (75, 78, 82), (31, 15), 11)
    pygame.draw.circle(surface, (20, 20, 20), (36, 14), 2)
    pygame.draw.polygon(surface, (75, 78, 82), [(23, 8), (28, 2), (31, 10)])
    return surface


class Wolf(pygame.sprite.Sprite):
    def __init__(self, pos: tuple[float, float], base_speed: float,
                 assets: AssetManager) -> None:
        super().__init__()
        self.pos = np.array(pos, dtype=float)
        self.base_speed = base_speed
        self.respawn_remaining = 0.0
        self.animation_time = 0.0
        self.animation: Animation | None = assets.animation("sprites/wolf")

        first_frame = self.animation.current_frame(0.0)
        if _looks_like_missing_asset(first_frame):
            self.animation = None
            self._visible_image = _wolf_placeholder()
        else:
            self._visible_image = first_frame

        self._hidden_image = pygame.Surface((1, 1), pygame.SRCALPHA)
        self.image = self._visible_image
        self.rect = self.image.get_rect()
        self._sync_rect()

    @property
    def is_active(self) -> bool:
        """True when the wolf moves, renders and participates in collisions."""
        return self.respawn_remaining <= 0.0

    def update(self, dt: float, session: "GameSession") -> None:
        """Chase the nearest living sheep while active."""
        if self.respawn_remaining > 0.0:
            self.respawn_remaining = max(0.0, self.respawn_remaining - dt)
            if self.respawn_remaining <= 0.0:
                self._show()
            return

        target = self._nearest_living_sheep(session)
        if target is None:
            self._update_image()
            return

        offset = target.pos - self.pos
        distance = float(np.linalg.norm(offset))
        if distance > 0.0:
            direction = offset / distance
            speed = self.base_speed * session.wolf_speed_multiplier
            movement = direction * speed * dt
            self._move_axis(0, float(movement[0]), session.tilemap)
            self._move_axis(1, float(movement[1]), session.tilemap)
            self.animation_time += dt

        self._update_image()

    def trigger_respawn(self, delay: float,
                        new_position: tuple[float, float]) -> None:
        """Move the wolf to a new spawn and hide it until delay expires."""
        self.pos = np.array(new_position, dtype=float)
        self.respawn_remaining = max(0.0, delay)
        if self.respawn_remaining > 0.0:
            self.image = self._hidden_image
            self.rect = self.image.get_rect()
            self._sync_rect()
        else:
            self._show()

    def _nearest_living_sheep(self, session: "GameSession"):
        living_sheep = [
            sheep for sheep in session.sheep_group
            if getattr(sheep, "alive", False)
        ]
        if not living_sheep:
            return None

        positions = np.array([sheep.pos for sheep in living_sheep], dtype=float)
        distances = np.linalg.norm(positions - self.pos, axis=1)
        return living_sheep[int(np.argmin(distances))]

    def _move_axis(self, axis: int, amount: float, tilemap: "TileMap") -> None:
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

    def _show(self) -> None:
        self.image = self._visible_image
        self.rect = self.image.get_rect()
        self._sync_rect()

    def _update_image(self) -> None:
        if self.animation is None:
            return

        frame = self.animation.current_frame(self.animation_time)
        if _looks_like_missing_asset(frame):
            return

        self._visible_image = frame
        if self.is_active:
            self.image = frame
            self.rect = self.image.get_rect()
            self._sync_rect()
