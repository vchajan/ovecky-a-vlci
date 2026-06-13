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
SPLASH_DURATION = 2.5

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
# Počty entit (konstantní po celou hru)
# ============================================================================
SHEEP_COUNT = 8
WOLF_COUNT = 4

# ============================================================================
# Pohyb
# ============================================================================
PLAYER_SPEED = 220.0           # px/s
SHEEP_SPEED = 60.0             # px/s
SHEEP_IDLE_RANGE = (0.8, 2.4)  # (min, max) doba pauzy mezi pohyby v sekundách
WOLF_BASE_SPEED = 140.0        # px/s, výchozí (před aplikací multiplikátoru)

# ============================================================================
# Respawn vlka po srážce se psem
# ============================================================================
WOLF_RESPAWN_DELAY = 3.0       # sekund, po které je vlk neviditelný a neaktivní

# ============================================================================
# Postupné zvyšování obtížnosti (jen rychlost vlků, NIKDY počet)
# ============================================================================
DIFFICULTY_RAMP_INTERVAL = 15.0       # každých X sekund se zvedne rychlost
DIFFICULTY_SPEED_INCREMENT = 0.10     # +10 % multiplikátoru na ramp
DIFFICULTY_SPEED_MAX = 2.0            # cap multiplikátoru (max 2× rychlost)

# ============================================================================
# Skóre
# ============================================================================
SCORE_PER_SECOND = 1            # body za sekundu přežití
SCORE_PER_WOLF_REPELLED = 10    # bonus za odražení vlka
