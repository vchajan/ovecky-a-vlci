"""Animace — sekvence framů s fixní rychlostí přehrávání.

# TODO Lane B
"""
from __future__ import annotations

import pygame


class Animation:
    """Drží list framů + per-frame trvání; vrací aktuální frame dle uplynulého času."""

    def __init__(self, frames: list[pygame.Surface], frame_duration: float = 0.12) -> None:
        # TODO Lane B
        self.frames = frames
        self.frame_duration = frame_duration

    def current_frame(self, elapsed: float) -> pygame.Surface:
        """Vrátí frame odpovídající uplynulému času (loop)."""
        # TODO Lane B — minimální placeholder
        if not self.frames:
            return pygame.Surface((1, 1), pygame.SRCALPHA)
        index = int(elapsed / self.frame_duration) % len(self.frames)
        return self.frames[index]
