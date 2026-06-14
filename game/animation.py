"""Simple frame-based animations."""
from __future__ import annotations

import pygame


def slice_spritesheet(
    sheet: pygame.Surface,
    frame_width: int,
    frame_height: int,
    row: int,
    frame_count: int,
) -> list[pygame.Surface]:
    """Return copied frames from one row of a spritesheet."""
    frames: list[pygame.Surface] = []
    y = row * frame_height
    for index in range(frame_count):
        rect = pygame.Rect(index * frame_width, y, frame_width, frame_height)
        frame = pygame.Surface((frame_width, frame_height), pygame.SRCALPHA)
        frame.blit(sheet, (0, 0), rect)
        frames.append(frame)
    return frames


class Animation:
    """Stores animation frames and returns the frame for elapsed time."""

    def __init__(
        self,
        frames: list[pygame.Surface],
        frame_duration: float = 0.12,
        loop: bool = True,
    ) -> None:
        if not frames:
            raise ValueError("Animation needs at least one frame.")
        if frame_duration <= 0.0:
            raise ValueError("frame_duration must be greater than zero.")

        self.frames = frames
        self.frame_duration = frame_duration
        self.loop = loop

    def current_frame(self, elapsed: float) -> pygame.Surface:
        """Return the frame that belongs to the elapsed animation time."""
        if elapsed <= 0.0:
            return self.frames[0]

        index = int(elapsed / self.frame_duration)
        if self.loop:
            index %= len(self.frames)
        else:
            index = min(index, len(self.frames) - 1)

        return self.frames[index]
