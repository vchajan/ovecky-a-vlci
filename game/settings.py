"""Sdílené konstanty pro celý projekt Sheep Defender.

Po Phase 0 se konstanty zde NEMĚNÍ bez konzultace s týmem.
Pro ladění obtížnosti během Phase 3 je naopak toto jediné správné místo
pro úpravy — nikdy magic numbers v jednotlivých modulech.
"""

# ============================================================================
# Okno a smyčka
# ============================================================================
WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 720
WINDOW_SIZE = (WINDOW_WIDTH, WINDOW_HEIGHT)
WINDOW_TITLE = "Sheep Defender"
FPS = 60
MAX_DELTA_TIME = 0.1  # clamping abnormálně velkých dt
SPLASH_DURATION = 10

# ============================================================================
# Mapa
# ============================================================================
TILE_SIZE = 64

# ============================================================================
# Barvy (RGB)
# ============================================================================
COLOR_BACKGROUND = (40, 60, 30)
COLOR_GRASS = (80, 130, 60)
COLOR_FENCE = (90, 60, 30)
COLOR_TEXT = (240, 240, 230)
COLOR_TEXT_DIM = (180, 180, 170)
COLOR_ACCENT = (220, 200, 80)
COLOR_PLACEHOLDER = (255, 0, 255)  # zářivě růžová pro chybějící assety

# ============================================================================
# Pocty entit a vlny
# ============================================================================
INITIAL_SHEEP_COUNT = 8
SHEEP_COUNT = INITIAL_SHEEP_COUNT  # backwards-compatible alias
MINIMUM_SHEEP_TO_CONTINUE = 3
INITIAL_WOLF_COUNT = 3
WOLF_COUNT = INITIAL_WOLF_COUNT  # backwards-compatible alias
WOLF_MAX_COUNT = 8
WAVE_INTERVAL = 12.0
WAVE_MESSAGE_DURATION = 1.5

# ============================================================================
# Pohyb
# ============================================================================
PLAYER_SPEED = 220.0           # px/s
SHEEP_SPEED = 60.0             # px/s
SHEEP_IDLE_RANGE = (0.8, 2.4)  # (min, max) doba pauzy mezi pohyby v sekundách
WOLF_BASE_SPEED = 60.0         # px/s, stejny velmi pomaly start pro vsechny obtiznosti

# ============================================================================
# Pastevecka mechanika psa a stado
# ============================================================================
DOG_HERD_RADIUS = 145.0
DOG_HERD_STRONG_RADIUS = 75.0
DOG_HERD_FORCE = 1.0
DOG_HERD_STRONG_FORCE = 1.5
SHEEP_HERD_SPEED_MULTIPLIER = 1.25
SHEEP_HERD_MEMORY_TIME = 0.8

SHEEP_NEIGHBOR_RADIUS = 170.0
SHEEP_SEPARATION_RADIUS = 38.0
SHEEP_COHESION_WEIGHT = 0.18
SHEEP_SEPARATION_WEIGHT = 0.35
SHEEP_HERDING_WEIGHT = 1.0

BLOOD_STAIN_SIZE = (56, 40)
BLOOD_DARK = (105, 10, 15)
BLOOD_MAIN = (155, 18, 25)
BLOOD_LIGHT = (190, 35, 40)
MAX_BLOOD_STAINS = 30

# ============================================================================
# Obtiznost a postupne vlny
# ============================================================================
DEFAULT_DIFFICULTY = "medium"
DIFFICULTIES = ("easy", "medium", "hard")

WOLF_SPEED_INCREASE_EASY = 0.15
WOLF_SPEED_INCREASE_MEDIUM = 0.22
WOLF_SPEED_INCREASE_HARD = 0.32

WOLF_SPEED_MAX_EASY = 2.2
WOLF_SPEED_MAX_MEDIUM = 3.0
WOLF_SPEED_MAX_HARD = 4.0

DIFFICULTY_CONFIG = {
    "easy": {
        "speed_increase": WOLF_SPEED_INCREASE_EASY,
        "max_multiplier": WOLF_SPEED_MAX_EASY,
    },
    "medium": {
        "speed_increase": WOLF_SPEED_INCREASE_MEDIUM,
        "max_multiplier": WOLF_SPEED_MAX_MEDIUM,
    },
    "hard": {
        "speed_increase": WOLF_SPEED_INCREASE_HARD,
        "max_multiplier": WOLF_SPEED_MAX_HARD,
    },
}

INITIAL_SPEEDUPS_BEFORE_SPAWN = 1

# ============================================================================
# Respawn a utek vlka po srazce se psem
# ============================================================================
WOLF_FLEE_DURATION = 2.0
WOLF_RESPAWN_DELAY = 3.0
WOLF_FLEE_SPEED_MULTIPLIER = 1.35
WOLF_HOWL_DELAY = 0.35
WOLF_GROWL_DISTANCE = 180.0
WOLF_GROWL_COOLDOWN = 4.0

SHEEP_BLEAT_INTERVAL_RANGE = (6.0, 14.0)
SHEEP_PANIC_DISTANCE = 150.0
SHEEP_PANIC_SOUND_COOLDOWN = 3.0

VOLUME_WAVE_START = 0.45
VOLUME_WOLF_HOWL = 0.40
VOLUME_WOLF_GROWL = 0.35
VOLUME_WOLF_FLEE = 0.45
VOLUME_SHEEP_BLEAT = 0.30
VOLUME_SHEEP_PANIC = 0.40
VOLUME_SHEEP_LOSS = 0.45
VOLUME_DOG_BARK = 0.45
VOLUME_GAME_OVER = 0.45

# Backwards-compatible names from the old speed-only ramp.
DIFFICULTY_RAMP_INTERVAL = WAVE_INTERVAL
DIFFICULTY_SPEED_INCREMENT = WOLF_SPEED_INCREASE_MEDIUM
DIFFICULTY_SPEED_MAX = WOLF_SPEED_MAX_MEDIUM

# ============================================================================
# Spritesheet animace
# ============================================================================
SPRITE_FRAME_WIDTH = 64
SPRITE_FRAME_HEIGHT = 64
SPRITE_FRAME_COUNT = 4
SPRITE_DIRECTIONS = ("down", "left", "right", "up")
SPRITE_WALK_ROWS = {
    "down": 0,
    "left": 1,
    "right": 2,
    "up": 3,
}
SPRITE_WOLF_FLEE_ROW_OFFSET = 4
SPRITE_FRAME_DURATION = 0.12

# ============================================================================
# Skóre
# ============================================================================
SCORE_PER_SECOND = 1            # body za sekundu přežití
SCORE_PER_WOLF_REPELLED = 10    # bonus za odražení vlka
