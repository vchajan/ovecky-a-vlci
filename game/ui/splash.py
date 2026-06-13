"""Splash screen s animovanou pastvinou (pasoucí se ovce) a credits.

Lane A — implementace.

Animace je čistě procedurální (pygame.draw kruhy + obdélníky + elipsy),
nevyžaduje žádné assety od Lane B. Tím je splash robustní vůči neúplnému
asset balíčku v rané fázi projektu.

Stádo 6 ovcí se prochází po pastvině, každá s vlastní fází bobbingu
a kroku, aby pohyb nebyl synchronní. Titul mírně osciluje vertikálně.
Credit týmu je u dolního okraje.
"""
from __future__ import annotations

import math
import random

import pygame

from game import settings
from game.assets import AssetManager
from game.states import GameState


CREDITS_TEXT = "Unicorn Python class — Team 7"
SHEEP_COUNT = 6
SHEEP_SEED = 42  # deterministicky → splash vypadá konzistentně každý běh


class _GrazingSheep:
    """Procedurálně kreslená ovce procházející se po pastvině.

    Tělo je shluk překrývajících se bílých kruhů (čupřinatý vzhled), hlava
    je menší elipsa, nohy jsou 4 obdélníky s walk animací — každá noha má
    vlastní fázi sinu, takže vypadají jako kroky.
    """

    BODY_COLOR = (250, 250, 245)
    HEAD_COLOR = (180, 170, 165)
    LEG_COLOR = (50, 50, 50)
    EAR_COLOR = (160, 150, 145)
    EYE_COLOR = (20, 20, 20)

    def __init__(self, x: float, y: float, speed: float, scale: float) -> None:
        self.x = x
        self.y = y
        self.speed = speed     # px/s; znaménko určuje směr
        self.scale = scale     # 1.0 = referenční velikost
        # Náhodný fázový posun, aby ovce nehopsaly synchronně
        self._phase = random.random() * math.pi * 2
        self._time = 0.0

    def update(self, dt: float, screen_width: int) -> None:
        self.x += self.speed * dt
        self._time += dt
        # Wrap kolem hran — když ovce zmizí vlevo, objeví se vpravo (a naopak)
        margin = 60 * self.scale
        if self.x > screen_width + margin:
            self.x = -margin
        elif self.x < -margin:
            self.x = screen_width + margin

    def render(self, surface: pygame.Surface) -> None:
        s = self.scale
        # Bobbing — vertikální poskakování při chůzi
        bob = math.sin(self._time * 3 + self._phase) * 1.5 * s
        cx = int(self.x)
        cy = int(self.y + bob)
        facing_right = self.speed > 0

        # --- Nohy (kreslíme první, aby tělo bylo nad nimi)
        leg_w = max(2, int(3 * s))
        leg_h = int(7 * s)
        leg_y = cy + int(8 * s)
        for i, lx in enumerate((-8, -2, 4, 10)):
            # Každá noha posunutá fáze → vypadají jako střídavé kroky
            walk = math.sin(self._time * 8 + self._phase + i * math.pi / 2) * 2 * s
            leg_rect = pygame.Rect(
                cx + int(lx * s) - leg_w // 2,
                leg_y,
                leg_w, leg_h + int(walk),
            )
            pygame.draw.rect(surface, self.LEG_COLOR, leg_rect)

        # --- Tělo: shluk bílých kruhů
        for dx, dy, r in [(0, 0, 14), (-10, -2, 12), (10, -2, 12),
                          (-5, -8, 10), (5, -8, 10)]:
            pygame.draw.circle(
                surface, self.BODY_COLOR,
                (cx + int(dx * s), cy + int(dy * s)),
                int(r * s),
            )

        # --- Hlava: menší tmavá elipsa směřující dle směru pohybu
        head_dx = 14 if facing_right else -14
        head_w, head_h = int(14 * s), int(10 * s)
        head_rect = pygame.Rect(
            cx + int(head_dx * s) - head_w // 2,
            cy + int(-4 * s) - head_h // 2,
            head_w, head_h,
        )
        pygame.draw.ellipse(surface, self.HEAD_COLOR, head_rect)

        # --- Ucho: malý kruh nad hlavou
        ear_dx = head_dx + (-2 if facing_right else 2)
        pygame.draw.circle(
            surface, self.EAR_COLOR,
            (cx + int(ear_dx * s), cy + int(-10 * s)),
            max(1, int(2 * s)),
        )

        # --- Oko: malá černá tečka
        eye_dx = head_dx + (3 if facing_right else -3)
        pygame.draw.circle(
            surface, self.EYE_COLOR,
            (cx + int(eye_dx * s), cy + int(-5 * s)),
            max(1, int(1 * s)),
        )


class SplashScreen:
    """Splash screen s animovaným stádem a credits týmu."""

    def __init__(self, assets: AssetManager) -> None:
        self.assets = assets
        self.elapsed = 0.0

        # Fonty (cachované přes AssetManager, takže další SplashScreen je dostane zdarma)
        self._font_title = assets.font(96)
        self._font_subtitle = assets.font(28)
        self._font_credits = assets.font(24)
        self._font_hint = assets.font(20)

        # Pre-render statických textů (subtitle / credits / hint se nemění).
        # Title se nerendurje předem, protože ho jemně bobeme vertikálně —
        # to ale neznamená re-render, jen jiná pozice; takže ho taky cachneme.
        self._title_surf = self._font_title.render(
            "SHEEP DEFENDER", True, settings.COLOR_ACCENT,
        )
        self._subtitle_surf = self._font_subtitle.render(
            "Pes brání stádo před vlky", True, settings.COLOR_TEXT_DIM,
        )
        self._credits_surf = self._font_credits.render(
            CREDITS_TEXT, True, settings.COLOR_TEXT,
        )
        self._hint_surf = self._font_hint.render(
            "(stiskni libovolnou klávesu nebo klikni pro přeskočení)",
            True, settings.COLOR_TEXT_DIM,
        )

        # Stádo ovcí — deterministicky náhodné parametry kvůli konzistenci
        self._sheep: list[_GrazingSheep] = self._create_sheep()

    def _create_sheep(self) -> list[_GrazingSheep]:
        rng = random.Random(SHEEP_SEED)
        flock: list[_GrazingSheep] = []
        # Pastvinový pruh je mezi 62 % a 76 % výšky — ovce v něm chodí
        # ve dvou neformálních "řadách" (různé y → vrstvení)
        for _ in range(SHEEP_COUNT):
            x = rng.uniform(0, settings.WINDOW_WIDTH)
            y = rng.uniform(settings.WINDOW_HEIGHT * 0.62,
                            settings.WINDOW_HEIGHT * 0.76)
            speed = rng.uniform(18, 38) * rng.choice([-1, 1])
            scale = rng.uniform(0.9, 1.3)
            flock.append(_GrazingSheep(x, y, speed, scale))
        return flock

    # ---------------------------------------------------------- state protokol
    def handle_event(self, event: pygame.event.Event) -> GameState | None:
        """Libovolná klávesa nebo klik přeskočí splash."""
        if event.type == pygame.KEYDOWN:
            return GameState.MAIN_MENU
        if event.type == pygame.MOUSEBUTTONDOWN:
            return GameState.MAIN_MENU
        return None

    def update(self, dt: float) -> GameState | None:
        self.elapsed += dt
        for sheep in self._sheep:
            sheep.update(dt, settings.WINDOW_WIDTH)
        if self.elapsed >= settings.SPLASH_DURATION:
            return GameState.MAIN_MENU
        return None

    def render(self, surface: pygame.Surface) -> None:
        # === Pozadí: dvouvrstvé — tmavá obloha nahoře, tráva dole
        surface.fill(settings.COLOR_BACKGROUND)
        grass_y = int(settings.WINDOW_HEIGHT * 0.55)
        pygame.draw.rect(
            surface, settings.COLOR_GRASS,
            pygame.Rect(0, grass_y, settings.WINDOW_WIDTH,
                        settings.WINDOW_HEIGHT - grass_y),
        )

        # === Titulek s velmi jemným vertikálním bobem (±3 px)
        title_bob = int(math.sin(self.elapsed * 1.5) * 3)
        title_rect = self._title_surf.get_rect(
            center=(settings.WINDOW_WIDTH // 2,
                    int(settings.WINDOW_HEIGHT * 0.22) + title_bob),
        )
        surface.blit(self._title_surf, title_rect)

        # === Podtitulek
        subtitle_rect = self._subtitle_surf.get_rect(
            center=(settings.WINDOW_WIDTH // 2, title_rect.bottom + 16),
        )
        surface.blit(self._subtitle_surf, subtitle_rect)

        # === Animované ovce
        for sheep in self._sheep:
            sheep.render(surface)

        # === Progress bar (zaplňuje se v průběhu splash)
        bar_w, bar_h = 360, 4
        bar_x = (settings.WINDOW_WIDTH - bar_w) // 2
        bar_y = int(settings.WINDOW_HEIGHT * 0.85)
        progress = min(self.elapsed / settings.SPLASH_DURATION, 1.0)
        pygame.draw.rect(surface, settings.COLOR_TEXT_DIM,
                         pygame.Rect(bar_x, bar_y, bar_w, bar_h))
        pygame.draw.rect(surface, settings.COLOR_ACCENT,
                         pygame.Rect(bar_x, bar_y, int(bar_w * progress), bar_h))

        # === Credits týmu (povinný kredit autorům)
        credits_rect = self._credits_surf.get_rect(
            center=(settings.WINDOW_WIDTH // 2,
                    int(settings.WINDOW_HEIGHT * 0.91)),
        )
        surface.blit(self._credits_surf, credits_rect)

        # === Skip hint
        hint_rect = self._hint_surf.get_rect(
            center=(settings.WINDOW_WIDTH // 2,
                    int(settings.WINDOW_HEIGHT * 0.95)),
        )
        surface.blit(self._hint_surf, hint_rect)
