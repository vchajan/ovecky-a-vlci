"""Preview dog herding, sheep cohesion and separation."""
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
    def __init__(self) -> None:
        margin = settings.TILE_SIZE
        self.grass_rect = pygame.Rect(
            margin,
            margin,
            settings.WINDOW_WIDTH - margin * 2,
            settings.WINDOW_HEIGHT - margin * 2,
        )

    def render(self, surface: pygame.Surface) -> None:
        surface.fill(settings.COLOR_BACKGROUND)
        pygame.draw.rect(surface, settings.COLOR_FENCE, self.grass_rect.inflate(36, 36))
        pygame.draw.rect(surface, settings.COLOR_GRASS, self.grass_rect)

    def is_blocked_rect(self, rect: pygame.Rect) -> bool:
        return not self.grass_rect.contains(rect)

    def random_grass_position(self, rng: random.Random) -> tuple[float, float]:
        return (
            rng.uniform(self.grass_rect.left + 80, self.grass_rect.right - 80),
            rng.uniform(self.grass_rect.top + 80, self.grass_rect.bottom - 80),
        )


def main() -> None:
    pygame.init()
    screen = pygame.display.set_mode(settings.WINDOW_SIZE)
    pygame.display.set_caption("Sheep Defender - herding preview")
    clock = pygame.time.Clock()
    rng = random.Random(12)
    max_frames = _preview_frame_limit()
    frame_count = 0
    show_debug = True

    assets = AssetManager()
    tilemap = PreviewTileMap()
    player = Player((settings.WINDOW_WIDTH * 0.35, settings.WINDOW_HEIGHT * 0.5), assets)
    sheep_group = pygame.sprite.Group(
        *[
            Sheep(
                (
                    settings.WINDOW_WIDTH * 0.58 + rng.uniform(-90, 90),
                    settings.WINDOW_HEIGHT * 0.50 + rng.uniform(-70, 70),
                ),
                assets,
            )
            for _ in range(settings.INITIAL_SHEEP_COUNT)
        ],
    )

    running = True
    while running:
        dt = min(clock.tick(settings.FPS) / 1000.0, settings.MAX_DELTA_TIME)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_F3:
                    show_debug = not show_debug

        keys = pygame.key.get_pressed()
        player.update(dt, keys, tilemap)
        for sheep in sheep_group:
            sheep.update(dt, tilemap, player, sheep_group)

        tilemap.render(screen)
        if show_debug:
            _render_herding_zone(screen, player)
        sheep_group.draw(screen)
        screen.blit(player.image, player.rect)
        pygame.display.flip()

        frame_count += 1
        if max_frames is not None and frame_count >= max_frames:
            running = False

    pygame.quit()


def _render_herding_zone(surface: pygame.Surface, player: Player) -> None:
    overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
    pygame.draw.circle(
        overlay,
        (220, 220, 120, 55),
        player.rect.center,
        round(settings.DOG_HERD_RADIUS),
        width=2,
    )
    pygame.draw.circle(
        overlay,
        (255, 160, 80, 65),
        player.rect.center,
        round(settings.DOG_HERD_STRONG_RADIUS),
        width=2,
    )
    surface.blit(overlay, (0, 0))


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
