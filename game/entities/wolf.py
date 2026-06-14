"""Wolf entity with chase, flee and respawn behaviour."""
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


CHASING = "chasing"
FLEEING = "fleeing"
RESPAWNING = "respawning"


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


def _normalized(vector: np.ndarray) -> np.ndarray:
    length = float(np.linalg.norm(vector))
    if length <= 0.0:
        return np.array([0.0, 0.0], dtype=float)
    return vector / length


class Wolf(pygame.sprite.Sprite):
    """Wolf that chases sheep, flees from the dog, then respawns."""

    def __init__(
        self,
        pos: tuple[float, float],
        base_speed: float,
        assets: AssetManager,
    ) -> None:
        super().__init__()
        self.pos = np.array(pos, dtype=float)
        self.base_speed = base_speed
        self.state = CHASING
        self.direction = "down"
        self.last_move_direction = np.array([0.0, 0.0], dtype=float)
        self.flee_direction = np.array([0.0, 0.0], dtype=float)
        self.flee_remaining = 0.0
        self.respawn_remaining = 0.0
        self.growl_cooldown_remaining = 0.0
        self.animation_time = 0.0

        self.animations: dict[str, dict[str, Animation]] = {
            "walk": {
                direction: assets.animation(f"sprites/wolf/walk/{direction}")
                for direction in settings.SPRITE_DIRECTIONS
            },
            "flee": {
                direction: assets.animation(f"sprites/wolf/flee/{direction}")
                for direction in settings.SPRITE_DIRECTIONS
            },
        }
        self.animation: Animation | None = self.animations["walk"][self.direction]

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
        """True when the wolf can collide with sheep and the dog."""
        return self.state == CHASING

    @property
    def is_visible(self) -> bool:
        """True when the wolf should be rendered."""
        return self.state != RESPAWNING

    def update(self, dt: float, session: "GameSession") -> None:
        """Update the current wolf state."""
        if self.state == RESPAWNING:
            self._update_respawning(dt)
            return

        if self.state == FLEEING:
            self._update_fleeing(dt, session)
            return

        self._update_chasing(dt, session)

    def start_fleeing(self, player_pos: np.ndarray) -> bool:
        """Start the two-second flee state after a valid dog repel."""
        if self.state != CHASING:
            return False

        flee_direction = -self.last_move_direction
        if float(np.linalg.norm(flee_direction)) <= 0.0:
            flee_direction = self.pos - player_pos
        flee_direction = _normalized(flee_direction)
        if float(np.linalg.norm(flee_direction)) <= 0.0:
            flee_direction = np.array([1.0, 0.0], dtype=float)

        self.state = FLEEING
        self.flee_direction = flee_direction
        self.flee_remaining = settings.WOLF_FLEE_DURATION
        self.respawn_remaining = 0.0
        self.animation_time = 0.0
        self._update_direction_from_vector(flee_direction)
        self._update_image(moving=True)
        return True

    def trigger_respawn(
        self,
        delay: float,
        new_position: tuple[float, float],
    ) -> None:
        """Move the wolf to a new spawn and hide it until delay expires."""
        self.pos = np.array(new_position, dtype=float)
        self.state = RESPAWNING
        self.flee_remaining = 0.0
        self.respawn_remaining = max(0.0, delay)
        self.image = self._hidden_image
        self.rect = self.image.get_rect()
        self._sync_rect()
        if self.respawn_remaining <= 0.0:
            self._finish_respawn()

    def _update_chasing(self, dt: float, session: "GameSession") -> None:
        target = self._nearest_living_sheep(session)
        if target is None:
            self._update_image(moving=False)
            return

        offset = target.pos - self.pos
        direction = _normalized(offset)
        if float(np.linalg.norm(direction)) > 0.0:
            speed = self._effective_speed(session)
            movement = direction * speed * dt
            self._move_with_slide(movement, session.tilemap)
            self.last_move_direction = direction
            self._update_direction_from_vector(direction)
            self.animation_time += dt
            self._update_image(moving=True)
        else:
            self._update_image(moving=False)

    def _update_fleeing(self, dt: float, session: "GameSession") -> None:
        self.flee_remaining = max(0.0, self.flee_remaining - dt)
        if self.flee_remaining <= 0.0:
            rng = session.rng
            if rng is None:
                import random

                rng = random.Random(0)
            self.trigger_respawn(
                settings.WOLF_RESPAWN_DELAY,
                session.tilemap.edge_spawn_position(rng),
            )
            return

        speed = self._effective_speed(session) * settings.WOLF_FLEE_SPEED_MULTIPLIER
        movement = self.flee_direction * speed * dt
        moved = self._move_with_slide(movement, session.tilemap)
        if not moved:
            self.flee_direction = self._find_open_flee_direction(session.tilemap)
            self._update_direction_from_vector(self.flee_direction)
            self._move_with_slide(self.flee_direction * speed * dt, session.tilemap)

        self.animation_time += dt
        self._update_image(moving=True)

    def _update_respawning(self, dt: float) -> None:
        self.respawn_remaining = max(0.0, self.respawn_remaining - dt)
        if self.respawn_remaining <= 0.0:
            self._finish_respawn()

    def _finish_respawn(self) -> None:
        self.state = CHASING
        self.flee_remaining = 0.0
        self.respawn_remaining = 0.0
        self.animation_time = 0.0
        self._update_image(moving=False)

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

    def _move_with_slide(self, movement: np.ndarray, tilemap: "TileMap") -> bool:
        moved = False
        if float(movement[0]) != 0.0:
            moved = self._move_axis(0, float(movement[0]), tilemap) or moved
        if float(movement[1]) != 0.0:
            moved = self._move_axis(1, float(movement[1]), tilemap) or moved
        return moved

    def _move_axis(self, axis: int, amount: float, tilemap: "TileMap") -> bool:
        if amount == 0.0:
            return False

        next_pos = self.pos.copy()
        next_pos[axis] += amount

        test_rect = self.rect.copy()
        if axis == 0:
            test_rect.centerx = round(float(next_pos[0]))
        else:
            test_rect.centery = round(float(next_pos[1]))

        if tilemap.is_blocked_rect(test_rect):
            return False

        self.pos[axis] = next_pos[axis]
        self._sync_rect()
        return True

    def _find_open_flee_direction(self, tilemap: "TileMap") -> np.ndarray:
        current = _normalized(self.flee_direction)
        candidates = (
            np.array([-current[1], current[0]], dtype=float),
            np.array([current[1], -current[0]], dtype=float),
            -current,
            np.array([1.0, 0.0], dtype=float),
            np.array([-1.0, 0.0], dtype=float),
            np.array([0.0, 1.0], dtype=float),
            np.array([0.0, -1.0], dtype=float),
        )
        probe_distance = settings.TILE_SIZE * 0.25
        for candidate in candidates:
            candidate = _normalized(candidate)
            if float(np.linalg.norm(candidate)) <= 0.0:
                continue
            probe_rect = self.rect.copy()
            probe_rect.centerx = round(float(self.pos[0] + candidate[0] * probe_distance))
            probe_rect.centery = round(float(self.pos[1] + candidate[1] * probe_distance))
            if not tilemap.is_blocked_rect(probe_rect):
                return candidate
        return np.array([1.0, 0.0], dtype=float)

    def _effective_speed(self, session: "GameSession") -> float:
        return self.base_speed * session.wolf_speed_multiplier

    def _sync_rect(self) -> None:
        self.rect.center = (
            round(float(self.pos[0])),
            round(float(self.pos[1])),
        )

    def _update_direction_from_vector(self, movement: np.ndarray) -> None:
        if abs(float(movement[0])) >= abs(float(movement[1])):
            self.direction = "right" if movement[0] > 0.0 else "left"
        else:
            self.direction = "down" if movement[1] > 0.0 else "up"

    def _update_image(self, moving: bool) -> None:
        mode = "flee" if self.state == FLEEING else "walk"
        self.animation = self.animations[mode][self.direction]
        elapsed = self.animation_time if moving else 0.0
        frame = self.animation.current_frame(elapsed)
        if _looks_like_missing_asset(frame):
            frame = _wolf_placeholder()

        self._visible_image = frame
        if self.is_visible:
            center = self.rect.center
            self.image = frame
            self.rect = self.image.get_rect(center=center)
            self._sync_rect()
        else:
            self.image = self._hidden_image
            self.rect = self.image.get_rect()
            self._sync_rect()
