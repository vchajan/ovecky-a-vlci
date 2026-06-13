"""Small standalone preview for Player and Sheep."""
from __future__ import annotations

import os
import random
import sys
from pathlib import Path

import pygame

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from game import settings
from game.assets import AssetManager
from game.entities.player import Player
from game.entities.sheep import Sheep


class PreviewTileMap:
    """Tiny local map stub with a rectangular fence."""

    def __init__(self) -> None:
        self.tile_size = settings.TILE_SIZE
        self.width = settings.WINDOW_WIDTH // self.tile_size
        self.height = settings.WINDOW_HEIGHT // self.tile_size
        self.outer_rect = pygame.Rect(
            self.tile_size,
            self.tile_size,
            settings.WINDOW_WIDTH - 2 * self.tile_size,
            settings.WINDOW_HEIGHT - 2 * self.tile_size,
        )
        self.grass_rect = self.outer_rect.inflate(
            -self.tile_size,
            -self.tile_size,
        )

    def render(self, surface: pygame.Surface) -> None:
        """Draw the preview pasture."""
        surface.fill(settings.COLOR_BACKGROUND)
        pygame.draw.rect(surface, settings.COLOR_FENCE, self.outer_rect)
        pygame.draw.rect(surface, settings.COLOR_GRASS, self.grass_rect)

    def is_blocked_rect(self, rect: pygame.Rect) -> bool:
        """Return True when a sprite would leave the fenced pasture."""
        return not self.grass_rect.contains(rect)

    def random_grass_position(self, rng: random.Random) -> tuple[float, float]:
        """Return a random free position inside the preview pasture."""
        margin = settings.TILE_SIZE // 2
        x = rng.uniform(self.grass_rect.left + margin, self.grass_rect.right - margin)
        y = rng.uniform(self.grass_rect.top + margin, self.grass_rect.bottom - margin)
        return (x, y)


def main() -> None:
    """Run the entity preview until Escape or window close."""
    pygame.init()
    screen = pygame.display.set_mode(settings.WINDOW_SIZE)
    pygame.display.set_caption("Sheep Defender - entity preview")
    clock = pygame.time.Clock()
    rng = random.Random()
    max_frames = _preview_frame_limit()
    frame_count = 0

    assets = AssetManager()
    tilemap = PreviewTileMap()
    player = Player(tilemap.random_grass_position(rng), assets)
    sheep_group = pygame.sprite.Group(*(
        Sheep(tilemap.random_grass_position(rng), assets)
        for _ in range(settings.SHEEP_COUNT)
    ))

    running = True
    while running:
        dt = min(clock.tick(settings.FPS) / 1000.0, settings.MAX_DELTA_TIME)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False

        keys = pygame.key.get_pressed()
        player.update(dt, keys, tilemap)
        sheep_group.update(dt, tilemap)

        tilemap.render(screen)
        sheep_group.draw(screen)
        screen.blit(player.image, player.rect)
        pygame.display.flip()
        frame_count += 1
        if max_frames is not None and frame_count >= max_frames:
            running = False

    pygame.quit()


def _preview_frame_limit() -> int | None:
    value = os.environ.get("SHEEP_DEFENDER_PREVIEW_FRAMES")
    if value is None:
        return None

    try:
        frame_limit = int(value)
    except ValueError:
        return None

    if frame_limit <= 0:
        return None
    return frame_limit


if __name__ == "__main__":
    main()
