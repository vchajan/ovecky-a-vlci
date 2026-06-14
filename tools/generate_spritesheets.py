"""Generate deterministic pixel-art spritesheets for Sheep Defender."""
from __future__ import annotations

import os
import sys
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from game import settings


FRAME_W = settings.SPRITE_FRAME_WIDTH
FRAME_H = settings.SPRITE_FRAME_HEIGHT
FRAME_COUNT = settings.SPRITE_FRAME_COUNT
SPRITE_DIR = ROOT_DIR / "assets" / "sprites"


def main() -> None:
    pygame.init()
    SPRITE_DIR.mkdir(parents=True, exist_ok=True)

    pygame.image.save(_make_sheet("dog"), SPRITE_DIR / "dog_sheet.png")
    pygame.image.save(_make_sheet("sheep"), SPRITE_DIR / "sheep_sheet.png")
    pygame.image.save(_make_sheet("wolf"), SPRITE_DIR / "wolf_sheet.png")
    pygame.quit()


def _make_sheet(kind: str) -> pygame.Surface:
    row_count = 8 if kind == "wolf" else 4
    sheet = pygame.Surface((FRAME_W * FRAME_COUNT, FRAME_H * row_count), pygame.SRCALPHA)

    for direction, row in settings.SPRITE_WALK_ROWS.items():
        for frame in range(FRAME_COUNT):
            cell = pygame.Surface((FRAME_W, FRAME_H), pygame.SRCALPHA)
            if kind == "dog":
                _draw_dog(cell, direction, frame)
            elif kind == "sheep":
                _draw_sheep(cell, direction, frame)
            else:
                _draw_wolf(cell, direction, frame, fleeing=False)
            sheet.blit(cell, (frame * FRAME_W, row * FRAME_H))

    if kind == "wolf":
        for direction, row in settings.SPRITE_WALK_ROWS.items():
            for frame in range(FRAME_COUNT):
                cell = pygame.Surface((FRAME_W, FRAME_H), pygame.SRCALPHA)
                _draw_wolf(cell, direction, frame, fleeing=True)
                sheet.blit(
                    cell,
                    (
                        frame * FRAME_W,
                        (row + settings.SPRITE_WOLF_FLEE_ROW_OFFSET) * FRAME_H,
                    ),
                )

    return sheet


def _draw_shadow(surface: pygame.Surface, width: int = 42) -> None:
    rect = pygame.Rect(0, 0, width, 10)
    rect.center = (FRAME_W // 2, 49)
    pygame.draw.ellipse(surface, (0, 0, 0, 70), rect)


def _walk_phase(frame: int) -> int:
    return (-3, 2, 3, -2)[frame % FRAME_COUNT]


def _draw_dog(surface: pygame.Surface, direction: str, frame: int) -> None:
    _draw_shadow(surface)
    phase = _walk_phase(frame)
    fur = (139, 88, 48)
    dark = (88, 54, 31)
    tan = (190, 133, 76)
    eye = (22, 18, 15)

    if direction in ("left", "right"):
        sign = 1 if direction == "right" else -1
        body = pygame.Rect(15, 25, 34, 18)
        pygame.draw.ellipse(surface, fur, body)
        pygame.draw.ellipse(surface, tan, pygame.Rect(20, 29, 18, 10))
        tail_points = (
            [(16, 29), (6, 21), (9, 34)]
            if sign == 1
            else [(48, 29), (58, 21), (55, 34)]
        )
        pygame.draw.polygon(surface, dark, tail_points)

        leg_xs = (22, 31, 39, 46)
        for index, x in enumerate(leg_xs):
            step = phase if index % 2 == 0 else -phase
            pygame.draw.rect(surface, dark, pygame.Rect(x - 2, 39, 4, 10 + step))
            pygame.draw.rect(surface, tan, pygame.Rect(x - 3, 47 + step, 6, 3))

        head_center = (46, 23) if sign == 1 else (18, 23)
        pygame.draw.circle(surface, fur, head_center, 11)
        ear = (
            [(39, 16), (43, 5), (48, 17)]
            if sign == 1
            else [(25, 16), (21, 5), (16, 17)]
        )
        pygame.draw.polygon(surface, dark, ear)
        snout = pygame.Rect(47, 22, 12, 7) if sign == 1 else pygame.Rect(5, 22, 12, 7)
        pygame.draw.ellipse(surface, tan, snout)
        nose = (58, 25) if sign == 1 else (6, 25)
        pygame.draw.circle(surface, eye, nose, 2)
        pygame.draw.circle(surface, eye, (49, 20) if sign == 1 else (15, 20), 2)
    else:
        body = pygame.Rect(18, 24, 28, 24)
        pygame.draw.ellipse(surface, fur, body)
        for index, x in enumerate((23, 30, 37, 44)):
            step = phase if index % 2 == 0 else -phase
            pygame.draw.rect(surface, dark, pygame.Rect(x - 2, 40, 4, 9 + step))
        if direction == "down":
            pygame.draw.circle(surface, fur, (32, 20), 12)
            pygame.draw.ellipse(surface, tan, pygame.Rect(25, 22, 14, 9))
            pygame.draw.circle(surface, eye, (28, 18), 2)
            pygame.draw.circle(surface, eye, (36, 18), 2)
            pygame.draw.circle(surface, eye, (32, 28), 2)
            pygame.draw.polygon(surface, dark, [(22, 14), (18, 5), (27, 13)])
            pygame.draw.polygon(surface, dark, [(42, 14), (46, 5), (37, 13)])
            pygame.draw.line(surface, dark, (45, 32), (55, 24), 5)
        else:
            pygame.draw.circle(surface, fur, (32, 18), 11)
            pygame.draw.polygon(surface, dark, [(23, 14), (20, 5), (28, 12)])
            pygame.draw.polygon(surface, dark, [(41, 14), (44, 5), (36, 12)])
            pygame.draw.line(surface, dark, (45, 33), (55, 27), 5)


def _draw_sheep(surface: pygame.Surface, direction: str, frame: int) -> None:
    _draw_shadow(surface, 40)
    phase = _walk_phase(frame)
    wool = (244, 244, 232)
    wool_shadow = (218, 218, 205)
    face = (86, 74, 62)
    hoof = (38, 33, 29)
    eye = (12, 12, 10)

    for index, x in enumerate((22, 29, 36, 43)):
        step = phase if index % 2 == 0 else -phase
        pygame.draw.rect(surface, face, pygame.Rect(x - 2, 39, 4, 10 + step))
        pygame.draw.rect(surface, hoof, pygame.Rect(x - 3, 47 + step, 6, 3))

    for x, y, radius in (
        (23, 31, 11),
        (31, 28, 13),
        (40, 31, 11),
        (29, 37, 10),
        (37, 37, 10),
    ):
        pygame.draw.circle(surface, wool_shadow, (x + 1, y + 1), radius)
        pygame.draw.circle(surface, wool, (x, y), radius)

    if direction in ("left", "right"):
        sign = 1 if direction == "right" else -1
        head = pygame.Rect(42, 24, 15, 13) if sign == 1 else pygame.Rect(7, 24, 15, 13)
        pygame.draw.ellipse(surface, face, head)
        pygame.draw.circle(surface, face, (43, 22) if sign == 1 else (21, 22), 4)
        pygame.draw.circle(surface, eye, (52, 28) if sign == 1 else (12, 28), 2)
        tail = pygame.Rect(13, 31, 6, 6) if sign == 1 else pygame.Rect(45, 31, 6, 6)
        pygame.draw.ellipse(surface, wool, tail)
    elif direction == "down":
        pygame.draw.ellipse(surface, face, pygame.Rect(24, 20, 16, 14))
        pygame.draw.circle(surface, face, (23, 22), 4)
        pygame.draw.circle(surface, face, (41, 22), 4)
        pygame.draw.circle(surface, eye, (28, 27), 2)
        pygame.draw.circle(surface, eye, (36, 27), 2)
    else:
        pygame.draw.ellipse(surface, face, pygame.Rect(24, 18, 16, 12))
        pygame.draw.circle(surface, face, (24, 20), 4)
        pygame.draw.circle(surface, face, (40, 20), 4)


def _draw_wolf(
    surface: pygame.Surface,
    direction: str,
    frame: int,
    fleeing: bool,
) -> None:
    _draw_shadow(surface, 46 if not fleeing else 50)
    phase = (-5, 4, 5, -4)[frame % FRAME_COUNT] if fleeing else _walk_phase(frame)
    body_color = (105, 111, 116)
    dark = (62, 66, 70)
    light = (150, 154, 155)
    eye = (18, 16, 12)
    dust = (185, 164, 120, 150)

    if direction in ("left", "right"):
        sign = 1 if direction == "right" else -1
        body = pygame.Rect(13, 24, 38 if fleeing else 34, 17)
        pygame.draw.ellipse(surface, body_color, body)
        pygame.draw.line(surface, dark, (18, 28), (41, 26), 2)
        tail = (
            [(15, 29), (4, 22 if not fleeing else 35), (10, 39)]
            if sign == 1
            else [(49, 29), (60, 22 if not fleeing else 35), (54, 39)]
        )
        pygame.draw.polygon(surface, dark, tail)

        for index, x in enumerate((20, 29, 39, 47)):
            step = phase if index % 2 == 0 else -phase
            pygame.draw.rect(surface, dark, pygame.Rect(x - 2, 37, 4, 11 + step))
            pygame.draw.rect(surface, light, pygame.Rect(x - 3, 47 + step, 6, 3))

        head_center = (46, 22) if sign == 1 else (18, 22)
        pygame.draw.circle(surface, body_color, head_center, 10)
        if fleeing:
            ear = (
                [(40, 17), (34, 11), (44, 15)]
                if sign == 1
                else [(24, 17), (30, 11), (20, 15)]
            )
        else:
            ear = (
                [(39, 16), (42, 5), (48, 16)]
                if sign == 1
                else [(25, 16), (22, 5), (16, 16)]
            )
        pygame.draw.polygon(surface, dark, ear)
        snout = pygame.Rect(47, 21, 15, 7) if sign == 1 else pygame.Rect(2, 21, 15, 7)
        pygame.draw.ellipse(surface, dark, snout)
        pygame.draw.circle(surface, eye, (59, 24) if sign == 1 else (5, 24), 2)
        pygame.draw.circle(surface, eye, (49, 20) if sign == 1 else (15, 20), 2)
        if fleeing:
            pygame.draw.circle(surface, dust, (9 if sign == 1 else 55, 45), 3)
            pygame.draw.circle(surface, dust, (5 if sign == 1 else 59, 41), 2)
    else:
        body = pygame.Rect(18, 24, 28, 23 if not fleeing else 27)
        pygame.draw.ellipse(surface, body_color, body)
        for index, x in enumerate((23, 30, 37, 44)):
            step = phase if index % 2 == 0 else -phase
            pygame.draw.rect(surface, dark, pygame.Rect(x - 2, 39, 4, 10 + step))
        if direction == "down":
            pygame.draw.circle(surface, body_color, (32, 20), 11)
            pygame.draw.ellipse(surface, dark, pygame.Rect(24, 22, 16, 8))
            pygame.draw.circle(surface, eye, (28, 18), 2)
            pygame.draw.circle(surface, eye, (36, 18), 2)
            if fleeing:
                pygame.draw.polygon(surface, dark, [(22, 16), (15, 13), (26, 13)])
                pygame.draw.polygon(surface, dark, [(42, 16), (49, 13), (38, 13)])
                pygame.draw.circle(surface, dust, (48, 47), 3)
            else:
                pygame.draw.polygon(surface, dark, [(23, 14), (20, 4), (29, 13)])
                pygame.draw.polygon(surface, dark, [(41, 14), (44, 4), (35, 13)])
        else:
            pygame.draw.circle(surface, body_color, (32, 18), 10)
            if fleeing:
                pygame.draw.polygon(surface, dark, [(23, 16), (15, 14), (27, 13)])
                pygame.draw.polygon(surface, dark, [(41, 16), (49, 14), (37, 13)])
                pygame.draw.line(surface, dark, (44, 35), (51, 45), 5)
            else:
                pygame.draw.polygon(surface, dark, [(23, 14), (20, 4), (29, 12)])
                pygame.draw.polygon(surface, dark, [(41, 14), (44, 4), (35, 12)])
                pygame.draw.line(surface, dark, (44, 34), (53, 27), 5)


if __name__ == "__main__":
    main()
