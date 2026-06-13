"""Tile map for the fenced Sheep Defender pasture."""
from __future__ import annotations

import random

import numpy as np
import pygame

from game import settings
from game.assets import AssetManager
from game.world.pasture_map import FENCE, GATE, GRASS, MAP_DATA


class TileMap:
    """Static map that knows how to render tiles and answer collision queries."""

    def __init__(self) -> None:
        self.data = np.array(MAP_DATA, copy=True)
        self.tile_size = settings.TILE_SIZE
        self.height, self.width = self.data.shape
        self._visible_rect = pygame.Rect(0, 0, settings.WINDOW_WIDTH, settings.WINDOW_HEIGHT)
        self._grass_tiles = self._visible_tile_candidates(GRASS)
        self._spawn_tiles = self._spawn_candidates()

        assets = AssetManager()
        self._grass_image = assets.image("tiles/grass")
        self._fence_h_image = assets.image("tiles/fence_h")
        self._fence_v_image = assets.image("tiles/fence_v")
        self._fence_corner_image = assets.image("tiles/fence_corner")
        self._gate_image = self._make_gate_image()

    def render(self, surface: pygame.Surface) -> None:
        """Draw the whole map to surface."""
        surface.fill(settings.COLOR_BACKGROUND)
        for row in range(self.height):
            for column in range(self.width):
                rect = pygame.Rect(
                    column * self.tile_size,
                    row * self.tile_size,
                    self.tile_size,
                    self.tile_size,
                )
                surface.blit(self._image_for_tile(row, column), rect)

    def is_blocked_pixel(self, x: float, y: float) -> bool:
        """Return True when a pixel lies outside the map or on a blocking tile."""
        if x < 0.0 or y < 0.0:
            return True

        column = int(x // self.tile_size)
        row = int(y // self.tile_size)
        if row < 0 or row >= self.height or column < 0 or column >= self.width:
            return True

        return int(self.data[row, column]) == FENCE

    def is_blocked_rect(self, rect: pygame.Rect) -> bool:
        """Return True when any checked corner touches a blocked tile."""
        left = rect.left + 1
        right = rect.right - 2
        top = rect.top + 1
        bottom = rect.bottom - 2

        if right < left:
            left = right = rect.centerx
        if bottom < top:
            top = bottom = rect.centery

        points = (
            (left, top),
            (right, top),
            (left, bottom),
            (right, bottom),
        )
        return any(self.is_blocked_pixel(float(x), float(y)) for x, y in points)

    def random_grass_position(self, rng: random.Random) -> tuple[float, float]:
        """Return the center of a random grass tile inside the pasture."""
        return self._random_tile_center(rng, self._grass_tiles)

    def edge_spawn_position(self, rng: random.Random) -> tuple[float, float]:
        """Return the center of a passable gate tile for wolf spawning."""
        return self._random_tile_center(rng, self._spawn_tiles)

    def _tile_candidates(self, tile_id: int) -> list[tuple[int, int]]:
        positions = np.argwhere(self.data == tile_id)
        return [(int(row), int(column)) for row, column in positions]

    def _visible_tile_candidates(self, tile_id: int) -> list[tuple[int, int]]:
        return [
            (row, column)
            for row, column in self._tile_candidates(tile_id)
            if self._is_visible_tile_center(row, column)
        ]

    def _spawn_candidates(self) -> list[tuple[int, int]]:
        candidates: list[tuple[int, int]] = []
        for row, column in self._tile_candidates(GATE):
            if (
                self._is_visible_tile_center(row, column)
                and self._has_visible_passable_neighbor(row, column)
            ):
                candidates.append((row, column))
                continue

            neighbor = self._first_visible_passable_neighbor(row, column)
            if neighbor is not None:
                candidates.append(neighbor)

        return candidates

    def _random_tile_center(
        self,
        rng: random.Random,
        candidates: list[tuple[int, int]],
    ) -> tuple[float, float]:
        if not candidates:
            raise ValueError("TileMap has no valid position candidates.")

        row, column = rng.choice(candidates)
        return (
            (column + 0.5) * self.tile_size,
            (row + 0.5) * self.tile_size,
        )

    def _tile_center(self, row: int, column: int) -> tuple[float, float]:
        return (
            (column + 0.5) * self.tile_size,
            (row + 0.5) * self.tile_size,
        )

    def _is_visible_tile_center(self, row: int, column: int) -> bool:
        x, y = self._tile_center(row, column)
        return self._visible_rect.collidepoint(x, y)

    def _has_visible_passable_neighbor(self, row: int, column: int) -> bool:
        return self._first_visible_passable_neighbor(row, column) is not None

    def _first_visible_passable_neighbor(
        self,
        row: int,
        column: int,
    ) -> tuple[int, int] | None:
        for next_row, next_column in (
            (row - 1, column),
            (row + 1, column),
            (row, column - 1),
            (row, column + 1),
        ):
            if not self._is_inside_map(next_row, next_column):
                continue
            if int(self.data[next_row, next_column]) == FENCE:
                continue
            if not self._is_visible_tile_center(next_row, next_column):
                continue
            return (next_row, next_column)
        return None

    def _is_inside_map(self, row: int, column: int) -> bool:
        return 0 <= row < self.height and 0 <= column < self.width

    def _image_for_tile(self, row: int, column: int) -> pygame.Surface:
        tile = int(self.data[row, column])
        if tile == GRASS:
            return self._grass_image
        if tile == GATE:
            return self._gate_image
        if self._is_corner(row, column):
            return self._fence_corner_image
        if column == 0 or column == self.width - 1:
            return self._fence_v_image
        return self._fence_h_image

    def _is_corner(self, row: int, column: int) -> bool:
        top_or_bottom = row == 0 or row == self.height - 1
        left_or_right = column == 0 or column == self.width - 1
        return top_or_bottom and left_or_right

    def _make_gate_image(self) -> pygame.Surface:
        image = self._grass_image.copy()
        gate_rect = pygame.Rect(0, self.tile_size // 2 - 5, self.tile_size, 10)
        pygame.draw.rect(image, (145, 110, 60), gate_rect)
        return image
