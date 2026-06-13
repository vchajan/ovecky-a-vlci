"""Small audio wrapper around AssetManager."""
from __future__ import annotations

import pygame

from game.assets import AssetManager


class AudioSystem:
    """Plays named sounds while keeping audio failures harmless."""

    def __init__(self, assets: AssetManager) -> None:
        self.assets = assets

    def play(self, key: str) -> None:
        """Play a sound by asset key if audio is available."""
        try:
            self.assets.sound(key).play()
        except pygame.error:
            return None
