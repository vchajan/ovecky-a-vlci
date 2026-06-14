"""Small audio wrapper around AssetManager."""
from __future__ import annotations

import pygame

from game import settings
from game.assets import AssetManager


SOUND_VOLUMES: dict[str, float] = {
    "audio/wave_start": settings.VOLUME_WAVE_START,
    "audio/wolf_howl": settings.VOLUME_WOLF_HOWL,
    "audio/wolf_growl": settings.VOLUME_WOLF_GROWL,
    "audio/wolf_flee": settings.VOLUME_WOLF_FLEE,
    "audio/sheep_bleat": settings.VOLUME_SHEEP_BLEAT,
    "audio/sheep_panic": settings.VOLUME_SHEEP_PANIC,
    "audio/sheep_loss": settings.VOLUME_SHEEP_LOSS,
    "audio/dog_bark": settings.VOLUME_DOG_BARK,
    "audio/game_over": settings.VOLUME_GAME_OVER,
}


class AudioSystem:
    """Plays named sounds while keeping audio failures harmless."""

    def __init__(self, assets: AssetManager) -> None:
        self.assets = assets

    def play(self, key: str) -> None:
        """Play a sound by asset key if audio is available."""
        try:
            sound = self.assets.sound(key)
            sound.set_volume(SOUND_VOLUMES.get(key, 1.0))
            sound.play()
        except pygame.error:
            return None
