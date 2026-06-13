"""Wolf — vlk s chase AI a respawn mechanikou.

# TODO Lane C
Chování:
- Když aktivní: hledá nejbližší živou ovci a pohybuje se k ní.
  Efektivní rychlost = base_speed * session.wolf_speed_multiplier.
- Při kolizi s psem volá Rules ``trigger_respawn(delay, new_position)``,
  což okamžitě přesune sprite na novou edge pozici a deaktivuje ho na delay sekund.
- Při is_active == False: nehýbe se, není vidět, neúčastní se kolizí.
- Po vypršení delaye se znovu zviditelní (na pozici, kterou mu nastavil trigger_respawn).
"""
from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

from game import settings
from game.assets import AssetManager

if TYPE_CHECKING:
    from game.session import GameSession


class Wolf(pygame.sprite.Sprite):
    def __init__(self, pos: tuple[float, float], base_speed: float,
                 assets: AssetManager) -> None:
        super().__init__()
        # TODO Lane C: načti animace ve 4 směrech
        self.pos = pygame.math.Vector2(pos)
        self.base_speed = base_speed
        self.respawn_remaining = 0.0
        # Viditelný image se použije v aktivním stavu, hidden_image během respawnu
        self._visible_image = pygame.Surface((48, 48), pygame.SRCALPHA)
        self._visible_image.fill(settings.COLOR_PLACEHOLDER)
        self._hidden_image = pygame.Surface((1, 1), pygame.SRCALPHA)
        self.image = self._visible_image
        self.rect = self.image.get_rect(center=(int(self.pos.x), int(self.pos.y)))

    @property
    def is_active(self) -> bool:
        """True = vlk se hýbe, je vidět a podléhá kolizím. False = probíhá respawn."""
        return self.respawn_remaining <= 0.0

    def update(self, dt: float, session: "GameSession") -> None:
        """Když aktivní: chase nejbližší ovce, efektivní rychlost dle multiplikátoru.
        Když neaktivní: snižuj respawn_remaining; po vypršení znovu zviditelni."""
        # TODO Lane C: skutečné chase chování
        if self.respawn_remaining > 0.0:
            self.respawn_remaining -= dt
            if self.respawn_remaining <= 0.0:
                self.image = self._visible_image

    def trigger_respawn(self, delay: float,
                        new_position: tuple[float, float]) -> None:
        """Okamžitě přesune vlka na novou pozici, schová ho a deaktivuje na delay sekund.

        Sprite zůstává v sprite_group — jen se dočasně nevykresluje
        a kolize s ním se přeskakují.
        """
        self.pos = pygame.math.Vector2(new_position)
        self.rect.center = (int(self.pos.x), int(self.pos.y))
        self.image = self._hidden_image
        self.respawn_remaining = delay
