"""Preview the Lane B tile map and spawn positions."""
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
from game.world.tilemap import TileMap


def main() -> None:
    """Open a diagnostic map window until Escape or close."""
    pygame.init()
    screen = pygame.display.set_mode(settings.WINDOW_SIZE)
    pygame.display.set_caption("Sheep Defender - map preview")
    clock = pygame.time.Clock()
    font = pygame.font.Font(None, 26)
    rng = random.Random(42)
    tilemap = TileMap()
    max_frames = _preview_frame_limit()
    frame_count = 0

    grass_positions = [tilemap.random_grass_position(rng) for _ in range(12)]
    spawn_positions = [tilemap.edge_spawn_position(rng) for _ in range(6)]

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False

        tilemap.render(screen)
        for position in grass_positions:
            pygame.draw.circle(screen, (245, 245, 235), _round_pos(position), 7)
        for position in spawn_positions:
            pygame.draw.circle(screen, (210, 60, 60), _round_pos(position), 9, 2)

        label = font.render(
            "ESC closes | white = grass spawn | red = wolf spawn",
            True,
            settings.COLOR_TEXT,
        )
        screen.blit(label, (16, 16))
        pygame.display.flip()
        frame_count += 1
        if max_frames is not None and frame_count >= max_frames:
            running = False
        clock.tick(settings.FPS)

    pygame.quit()


def _round_pos(position: tuple[float, float]) -> tuple[int, int]:
    return (round(position[0]), round(position[1]))


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
