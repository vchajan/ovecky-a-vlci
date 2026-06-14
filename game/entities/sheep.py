"""Sheep entity with a small idle/wander behaviour."""
from __future__ import annotations

import random
from typing import TYPE_CHECKING

import numpy as np
import pygame

from game import settings
from game.animation import Animation
from game.assets import AssetManager
from game.world.tilemap import TileMap

if TYPE_CHECKING:
    from game.entities.player import Player


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


def _normalized(vector: np.ndarray) -> np.ndarray:
    length = float(np.linalg.norm(vector))
    if length <= 0.0:
        return np.array([0.0, 0.0], dtype=float)
    return vector / length


class Sheep(pygame.sprite.Sprite):
    """Sheep that alternates between standing and wandering."""

    def __init__(self, pos: tuple[float, float], assets: AssetManager) -> None:
        super().__init__()
        self.pos = np.array(pos, dtype=float)
        self.direction = np.array([0.0, 0.0], dtype=float)
        self.facing_direction = "down"
        self.speed = settings.SHEEP_SPEED
        self.alive = True
        self.state = "idle"
        self.state_timer = _random_timer()
        self.herd_remaining = 0.0
        self.herd_force = settings.DOG_HERD_FORCE
        self.animation_time = 0.0
        self.animations: dict[str, Animation] = {
            direction: assets.animation(f"sprites/sheep/walk/{direction}")
            for direction in settings.SPRITE_DIRECTIONS
        }
        self.animation: Animation | None = self.animations[self.facing_direction]

        first_frame = self.animation.current_frame(0.0)
        if _looks_like_missing_asset(first_frame):
            self.animation = None
            self.image = _sheep_placeholder()
        else:
            self.image = first_frame

        self.rect = self.image.get_rect()
        self._sync_rect()

    def update(
        self,
        dt: float,
        tilemap: TileMap,
        player: "Player | None" = None,
        sheep_group: pygame.sprite.Group | None = None,
    ) -> None:
        """Update random walking, herding response and flock behavior."""
        if not self.alive:
            return

        self.state_timer -= dt
        away_from_dog, herd_force = self._herding_vector(player)
        if float(np.linalg.norm(away_from_dog)) > 0.0:
            self._start_herded(away_from_dog, herd_force)

        if self.state == "idle":
            if self.state_timer <= 0.0:
                self._start_wander()
        elif self.state == "wander":
            self._apply_flock_direction(sheep_group, None)
            collided = self._move(tilemap, dt, self.speed)
            if collided or self.state_timer <= 0.0:
                self._start_idle()
            else:
                self.animation_time += dt
        elif self.state == "herded":
            self.herd_remaining = max(0.0, self.herd_remaining - dt)
            self._apply_flock_direction(sheep_group, away_from_dog)
            speed = (
                self.speed
                * settings.SHEEP_HERD_SPEED_MULTIPLIER
                * self.herd_force
            )
            collided = self._move(tilemap, dt, speed)
            if collided:
                self._start_wander()
            elif self.herd_remaining <= 0.0:
                self._start_wander()
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
        self.herd_remaining = 0.0
        self.herd_force = settings.DOG_HERD_FORCE
        self.animation_time = 0.0

    def _start_wander(self) -> None:
        self.state = "wander"
        angle = random.uniform(0.0, 2.0 * np.pi)
        self.direction = np.array(
            [np.cos(angle), np.sin(angle)],
            dtype=float,
        )
        self._update_facing_direction(self.direction)
        self.state_timer = _random_timer()

    def _start_herded(self, direction: np.ndarray, force: float) -> None:
        self.state = "herded"
        self.direction = _normalized(direction)
        self.herd_force = force
        self.herd_remaining = settings.SHEEP_HERD_MEMORY_TIME
        self._update_facing_direction(self.direction)

    def _move(self, tilemap: TileMap, dt: float, speed: float) -> bool:
        offset = self.direction * speed * dt
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

    def _herding_vector(
        self,
        player: "Player | None",
    ) -> tuple[np.ndarray, float]:
        if player is None:
            return np.array([0.0, 0.0], dtype=float), settings.DOG_HERD_FORCE

        difference = self.pos - player.pos
        distance = float(np.linalg.norm(difference))
        if distance >= settings.DOG_HERD_RADIUS:
            return np.array([0.0, 0.0], dtype=float), settings.DOG_HERD_FORCE

        if distance <= 0.0:
            direction = np.array([1.0, 0.0], dtype=float)
        else:
            direction = difference / distance

        force = (
            settings.DOG_HERD_STRONG_FORCE
            if distance < settings.DOG_HERD_STRONG_RADIUS
            else settings.DOG_HERD_FORCE
        )
        return direction, force

    def _apply_flock_direction(
        self,
        sheep_group: pygame.sprite.Group | None,
        away_from_dog: np.ndarray | None,
    ) -> None:
        cohesion = np.array([0.0, 0.0], dtype=float)
        separation = np.array([0.0, 0.0], dtype=float)

        if sheep_group is not None:
            neighbor_positions: list[np.ndarray] = []
            for sheep in sheep_group:
                if sheep is self or not getattr(sheep, "alive", False):
                    continue
                difference = sheep.pos - self.pos
                distance = float(np.linalg.norm(difference))
                if distance <= 0.0:
                    continue
                if distance < settings.SHEEP_NEIGHBOR_RADIUS:
                    neighbor_positions.append(sheep.pos)
                if distance < settings.SHEEP_SEPARATION_RADIUS:
                    separation -= difference / distance

            if neighbor_positions:
                center = np.mean(np.array(neighbor_positions, dtype=float), axis=0)
                cohesion = _normalized(center - self.pos)

        combined = self.direction.copy()
        combined += cohesion * settings.SHEEP_COHESION_WEIGHT
        combined += _normalized(separation) * settings.SHEEP_SEPARATION_WEIGHT
        if away_from_dog is not None:
            combined += (
                _normalized(away_from_dog)
                * settings.SHEEP_HERDING_WEIGHT
                * self.herd_force
            )

        normalized = _normalized(combined)
        if float(np.linalg.norm(normalized)) > 0.0:
            self.direction = normalized
            self._update_facing_direction(self.direction)

    def _sync_rect(self) -> None:
        self.rect.center = (
            round(float(self.pos[0])),
            round(float(self.pos[1])),
        )

    def _update_facing_direction(self, movement: np.ndarray) -> None:
        if abs(float(movement[0])) >= abs(float(movement[1])):
            self.facing_direction = "right" if movement[0] > 0.0 else "left"
        else:
            self.facing_direction = "down" if movement[1] > 0.0 else "up"

    def _update_image(self) -> None:
        if not self.animations:
            return

        self.animation = self.animations[self.facing_direction]
        moving = self.state in ("wander", "herded")
        elapsed = self.animation_time if moving else 0.0
        frame = self.animation.current_frame(elapsed)
        if _looks_like_missing_asset(frame):
            return

        center = self.rect.center
        self.image = frame
        self.rect = self.image.get_rect(center=center)
