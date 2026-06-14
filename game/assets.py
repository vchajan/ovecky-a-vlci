"""Asset loading and safe fallbacks for images, animations, fonts and sounds."""
from __future__ import annotations

from pathlib import Path

import pygame

from game import settings
from game.animation import Animation, slice_spritesheet

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ASSET_ROOT = PROJECT_ROOT / "assets"

IMAGE_FILES: dict[str, Path] = {
    "tiles/grass": ASSET_ROOT / "tiles" / "grass.png",
    "tiles/fence_h": ASSET_ROOT / "tiles" / "fence_h.png",
    "tiles/fence_v": ASSET_ROOT / "tiles" / "fence_v.png",
    "tiles/fence_corner": ASSET_ROOT / "tiles" / "fence_corner.png",
    "sprites/dog": ASSET_ROOT / "sprites" / "dog.png",
    "sprites/sheep": ASSET_ROOT / "sprites" / "sheep.png",
    "sprites/wolf": ASSET_ROOT / "sprites" / "wolf.png",
    "sprites/dog_sheet": ASSET_ROOT / "sprites" / "dog_sheet.png",
    "sprites/sheep_sheet": ASSET_ROOT / "sprites" / "sheep_sheet.png",
    "sprites/wolf_sheet": ASSET_ROOT / "sprites" / "wolf_sheet.png",
    "ui/logo": ASSET_ROOT / "ui" / "logo.png",
}

SOUND_FILES: dict[str, Path] = {
    "audio/bark": ASSET_ROOT / "audio" / "bark.wav",
    "audio/sheep_loss": ASSET_ROOT / "audio" / "sheep_loss.wav",
    "audio/wolf_stun": ASSET_ROOT / "audio" / "wolf_stun.wav",
    "audio/game_over": ASSET_ROOT / "audio" / "game_over.wav",
}

IMAGE_SIZES: dict[str, tuple[int, int]] = {
    "tiles/grass": (settings.TILE_SIZE, settings.TILE_SIZE),
    "tiles/fence_h": (settings.TILE_SIZE, settings.TILE_SIZE),
    "tiles/fence_v": (settings.TILE_SIZE, settings.TILE_SIZE),
    "tiles/fence_corner": (settings.TILE_SIZE, settings.TILE_SIZE),
    "sprites/dog": (48, 48),
    "sprites/sheep": (40, 40),
    "sprites/wolf": (48, 48),
    "sprites/dog_sheet": (
        settings.SPRITE_FRAME_WIDTH * settings.SPRITE_FRAME_COUNT,
        settings.SPRITE_FRAME_HEIGHT * len(settings.SPRITE_DIRECTIONS),
    ),
    "sprites/sheep_sheet": (
        settings.SPRITE_FRAME_WIDTH * settings.SPRITE_FRAME_COUNT,
        settings.SPRITE_FRAME_HEIGHT * len(settings.SPRITE_DIRECTIONS),
    ),
    "sprites/wolf_sheet": (
        settings.SPRITE_FRAME_WIDTH * settings.SPRITE_FRAME_COUNT,
        settings.SPRITE_FRAME_HEIGHT * (len(settings.SPRITE_DIRECTIONS) * 2),
    ),
    "ui/logo": (320, 120),
}

SPRITESHEET_ANIMATIONS: dict[str, tuple[str, int]] = {}
for _direction, _row in settings.SPRITE_WALK_ROWS.items():
    SPRITESHEET_ANIMATIONS[f"sprites/dog/walk/{_direction}"] = (
        "sprites/dog_sheet",
        _row,
    )
    SPRITESHEET_ANIMATIONS[f"sprites/sheep/walk/{_direction}"] = (
        "sprites/sheep_sheet",
        _row,
    )
    SPRITESHEET_ANIMATIONS[f"sprites/wolf/walk/{_direction}"] = (
        "sprites/wolf_sheet",
        _row,
    )
    SPRITESHEET_ANIMATIONS[f"sprites/wolf/flee/{_direction}"] = (
        "sprites/wolf_sheet",
        _row + settings.SPRITE_WOLF_FLEE_ROW_OFFSET,
    )


class SilentSound:
    """Sound object used when audio is unavailable."""

    def play(self) -> None:
        """Do nothing and keep the game running."""
        return None


class AssetManager:
    """Loads assets from disk and returns visible placeholders on failure."""

    def __init__(self) -> None:
        pygame.font.init()
        self._image_cache: dict[str, pygame.Surface] = {}
        self._animation_cache: dict[str, Animation] = {}
        self._font_cache: dict[int, pygame.font.Font] = {}
        self._sound_cache: dict[str, pygame.mixer.Sound | SilentSound] = {}
        self._silent_sound = SilentSound()

    def image(self, key: str) -> pygame.Surface:
        """Return an image for key, or a cached placeholder if it is missing."""
        if key not in self._image_cache:
            self._image_cache[key] = self._load_image(key)
        return self._image_cache[key]

    def animation(self, key: str) -> Animation:
        """Return a cached animation for key."""
        if key not in self._animation_cache:
            self._animation_cache[key] = self._load_animation(key)
        return self._animation_cache[key]

    def font(self, size: int) -> pygame.font.Font:
        """Return a cached font with a reliable default fallback."""
        if size not in self._font_cache:
            self._font_cache[size] = pygame.font.Font(None, size)
        return self._font_cache[size]

    def sound(self, key: str) -> pygame.mixer.Sound | SilentSound:
        """Return a cached sound or SilentSound when audio cannot be used."""
        if key not in self._sound_cache:
            self._sound_cache[key] = self._load_sound(key)
        return self._sound_cache[key]

    def _load_image(self, key: str) -> pygame.Surface:
        path = IMAGE_FILES.get(key)
        size = IMAGE_SIZES.get(key, (settings.TILE_SIZE, settings.TILE_SIZE))

        if path is None or not path.is_file():
            return self._placeholder_image(key, size)

        try:
            image = pygame.image.load(str(path))
            if pygame.display.get_init() and pygame.display.get_surface() is not None:
                image = image.convert_alpha()
            else:
                image = image.copy()
        except (OSError, pygame.error):
            return self._placeholder_image(key, size)

        if key in IMAGE_SIZES and image.get_size() != size:
            image = pygame.transform.smoothscale(image, size)
        return image

    def _load_sound(self, key: str) -> pygame.mixer.Sound | SilentSound:
        path = SOUND_FILES.get(key)
        if path is None or not path.is_file() or not pygame.mixer.get_init():
            return self._silent_sound

        try:
            return pygame.mixer.Sound(str(path))
        except (OSError, pygame.error):
            return self._silent_sound

    def _load_animation(self, key: str) -> Animation:
        spec = SPRITESHEET_ANIMATIONS.get(key)
        if spec is None:
            return Animation([self.image(key)])

        sheet_key, row = spec
        path = IMAGE_FILES.get(sheet_key)
        if path is None or not path.is_file():
            return Animation(
                self._placeholder_animation_frames(key),
                settings.SPRITE_FRAME_DURATION,
            )

        sheet = self.image(sheet_key)
        frames = slice_spritesheet(
            sheet,
            settings.SPRITE_FRAME_WIDTH,
            settings.SPRITE_FRAME_HEIGHT,
            row,
            settings.SPRITE_FRAME_COUNT,
        )
        return Animation(frames, settings.SPRITE_FRAME_DURATION)

    def _placeholder_image(self, key: str, size: tuple[int, int]) -> pygame.Surface:
        if key.startswith("tiles/grass"):
            return self._tile_surface(settings.COLOR_GRASS, (94, 150, 70), size)
        if key.startswith("tiles/fence"):
            return self._fence_surface(size)
        if key == "sprites/dog":
            return self._dog_surface(size)
        if key == "sprites/sheep":
            return self._sheep_surface(size)
        if key == "sprites/wolf":
            return self._wolf_surface(size)
        if key.endswith("_sheet"):
            return self._missing_surface(size)
        if key == "ui/logo":
            return self._logo_surface(size)
        return self._missing_surface(size)

    def _placeholder_animation_frames(self, key: str) -> list[pygame.Surface]:
        frame = self._entity_placeholder_for_animation(key)
        return [frame.copy() for _ in range(settings.SPRITE_FRAME_COUNT)]

    def _entity_placeholder_for_animation(self, key: str) -> pygame.Surface:
        size = (settings.SPRITE_FRAME_WIDTH, settings.SPRITE_FRAME_HEIGHT)
        if key.startswith("sprites/dog/"):
            return pygame.transform.smoothscale(self._dog_surface((48, 48)), size)
        if key.startswith("sprites/sheep/"):
            return pygame.transform.smoothscale(self._sheep_surface((40, 40)), size)
        if key.startswith("sprites/wolf/"):
            return pygame.transform.smoothscale(self._wolf_surface((48, 48)), size)
        return self._missing_surface(size)

    @staticmethod
    def _tile_surface(
        base_color: tuple[int, int, int],
        accent_color: tuple[int, int, int],
        size: tuple[int, int],
    ) -> pygame.Surface:
        surface = pygame.Surface(size)
        surface.fill(base_color)
        step = max(8, size[0] // 4)
        for x in range(0, size[0], step):
            pygame.draw.line(surface, accent_color, (x, 0), (x + step // 2, size[1]))
        return surface

    @staticmethod
    def _fence_surface(size: tuple[int, int]) -> pygame.Surface:
        surface = pygame.Surface(size)
        surface.fill(settings.COLOR_GRASS)
        rail_color = settings.COLOR_FENCE
        post_color = (120, 82, 44)
        y1 = size[1] // 3
        y2 = 2 * size[1] // 3
        pygame.draw.rect(surface, rail_color, pygame.Rect(0, y1 - 4, size[0], 8))
        pygame.draw.rect(surface, rail_color, pygame.Rect(0, y2 - 4, size[0], 8))
        for x in (size[0] // 4, size[0] // 2, 3 * size[0] // 4):
            pygame.draw.rect(surface, post_color, pygame.Rect(x - 4, 8, 8, size[1] - 16))
        return surface

    @staticmethod
    def _dog_surface(size: tuple[int, int]) -> pygame.Surface:
        surface = pygame.Surface(size, pygame.SRCALPHA)
        pygame.draw.ellipse(surface, (125, 82, 46), surface.get_rect().inflate(-12, -18))
        pygame.draw.circle(surface, (92, 58, 34), (size[0] * 3 // 5, size[1] // 3), 10)
        pygame.draw.circle(surface, (25, 20, 18), (size[0] * 2 // 3, size[1] // 3), 2)
        return surface

    @staticmethod
    def _sheep_surface(size: tuple[int, int]) -> pygame.Surface:
        surface = pygame.Surface(size, pygame.SRCALPHA)
        pygame.draw.ellipse(surface, (245, 245, 235), surface.get_rect().inflate(-8, -12))
        pygame.draw.circle(surface, (235, 235, 225), (size[0] * 2 // 3, size[1] // 3), 8)
        pygame.draw.circle(surface, (35, 35, 35), (size[0] * 3 // 4, size[1] // 3), 2)
        return surface

    @staticmethod
    def _wolf_surface(size: tuple[int, int]) -> pygame.Surface:
        surface = pygame.Surface(size, pygame.SRCALPHA)
        pygame.draw.ellipse(surface, (100, 105, 110), surface.get_rect().inflate(-10, -18))
        pygame.draw.circle(surface, (75, 78, 82), (size[0] * 2 // 3, size[1] // 3), 11)
        pygame.draw.circle(surface, (20, 20, 20), (size[0] * 3 // 4, size[1] // 3), 2)
        return surface

    @staticmethod
    def _logo_surface(size: tuple[int, int]) -> pygame.Surface:
        surface = pygame.Surface(size)
        surface.fill(settings.COLOR_BACKGROUND)
        pygame.draw.rect(surface, settings.COLOR_ACCENT, surface.get_rect(), 4)
        font = pygame.font.Font(None, 42)
        text = font.render("Sheep Defender", True, settings.COLOR_TEXT)
        surface.blit(text, text.get_rect(center=surface.get_rect().center))
        return surface

    @staticmethod
    def _missing_surface(size: tuple[int, int]) -> pygame.Surface:
        surface = pygame.Surface(size)
        surface.fill(settings.COLOR_PLACEHOLDER)
        block = max(8, min(size) // 4)
        for y in range(0, size[1], block):
            for x in range(0, size[0], block):
                if (x // block + y // block) % 2 == 0:
                    pygame.draw.rect(surface, (20, 20, 20), pygame.Rect(x, y, block, block))
        return surface
