# Sheep Defender — týmový plán a sdílený AI prompt

Dokument pro 4členný tým pracující paralelně s různými AI nástroji (Claude, ChatGPT, Gemini, Copilot, Codex). Jeho účelem je, aby výstupy všech členů byly **kompatibilní** a integrace neskončila chaosem.

Obsah:
1. [Sdílený prompt pro AI nástroje](#1-sdílený-prompt-pro-ai-nástroje)
2. [Architektura projektu](#2-architektura-projektu)
3. [Sdílené kontrakty (interfacy)](#3-sdílené-kontrakty-interfacy)
4. [Rozdělení práce do 4 lan](#4-rozdělení-práce-do-4-lan)
5. [Fáze projektu a harmonogram](#5-fáze-projektu-a-harmonogram)
6. [Pravidla spolupráce s Gitem](#6-pravidla-spolupráce-s-gitem)
7. [Checklist před odevzdáním](#7-checklist-před-odevzdáním)

---

## 1. Sdílený prompt pro AI nástroje

**Každý člen týmu zkopíruje tento blok na začátek každé nové konverzace s AI asistentem.** Spodní část (Moje aktuální role + Aktuální úkol) přizpůsobí své lane a aktuálnímu úkolu.

> ```
> Jsi zkušený Python vývojář pomáhající studentskému týmu s magisterskou
> semestrální prací z Pythonu. Generuj čistý, čitelný a obhájitelný kód.
> Student musí být schopen kód ústně vysvětlit vyučujícímu — žádné
> nadbytečné abstrakce ani magie.
>
> ## Projekt: Sheep Defender
>
> Hra v Pygame. Hráč ovládá psa a brání stádo ovcí před vlnami vlků.
> Pohled shora, jedna scéna (ohraničená pastvina), rostoucí obtížnost.
>
> ### Herní pravidla
> - Hráč (pes) se pohybuje pomocí WASD nebo šipek
> - Ovce se pohybují náhodným pomalým "pasením" po pastvině
> - Po mapě se trvale pohybuje konstantní počet vlků (definován konstantou WOLF_COUNT)
> - Vlci hledají nejbližší živou ovci a běží k ní
> - Obtížnost stoupá tak, že se v čase zvyšuje rychlost vlků (počet zůstává konstantní)
> - Kolize vlk × ovce → ovce zmizí
> - Kolize pes × vlk → vlk je teleportován na novou náhodnou pozici na okraji mapy a
>   po dobu WOLF_RESPAWN_DELAY je neviditelný a neaktivní; sprite se nemaže, jen
>   změní pozici a dočasně se nevykresluje, pak se opět zobrazí
> - Hra končí, když padne poslední ovce
> - Skóre = přežitý čas v sekundách + bonus za odražené vlky
> - Hra je bez zvuku
>
> ### Technická omezení (absolutně závazná)
> - Python 3.11 nebo novější
> - Externí knihovny POUZE: pygame, numpy
> - Žádné jiné non-stdlib importy
> - Hra se spouští: `python main.py`
> - Cíl 60 FPS, delta time clamping na 0.1 s
>
> ### Architektura souborů
> sheep-defender/
> ├── main.py
> ├── requirements.txt
> ├── game/
> │   ├── app.py            (Game class, hlavní smyčka, state machine)
> │   ├── settings.py       (sdílené konstanty)
> │   ├── states.py         (GameState enum)
> │   ├── session.py        (GameSession dataclass)
> │   ├── animation.py
> │   ├── assets.py         (AssetManager)
> │   ├── entities/         (player.py, sheep.py, wolf.py)
> │   ├── systems/          (collision.py, difficulty.py, score.py, rules.py)
> │   ├── world/            (tilemap.py, pasture_map.py)
> │   └── ui/               (buttons.py, splash.py, menu.py, game_over.py, hud.py)
> ├── assets/               (sprites/, tiles/, ui/)
> └── docs/
>
> ### Konvence
> - snake_case pro proměnné a funkce, PascalCase pro třídy
> - Konstanty UPPER_SNAKE_CASE v game/settings.py
> - Type hints, kde to zlepší srozumitelnost (nemusí být všude)
> - Komentáře česky jsou v pořádku
> - Souřadnice v pixelech, počátek (0,0) vlevo nahoře
> - Delta time vždy float v sekundách
> - Barvy jako RGB tuple
> - Entity dědí z pygame.sprite.Sprite a mají image, rect, update(dt, ...)
>
> ### Sdílené konstanty (game/settings.py)
> WINDOW_WIDTH = 1280
> WINDOW_HEIGHT = 720
> WINDOW_TITLE = "Sheep Defender"
> FPS = 60
> MAX_DELTA_TIME = 0.1
> TILE_SIZE = 64
> SPLASH_DURATION = 2.5
>
> # Počty entit (volně konfigurovatelné — počet vlků zůstává po celou hru konstantní)
> SHEEP_COUNT = 8
> WOLF_COUNT = 4
>
> # Pohyb
> PLAYER_SPEED = 220.0
> SHEEP_SPEED = 60.0
> SHEEP_IDLE_RANGE = (0.8, 2.4)
> WOLF_BASE_SPEED = 140.0
>
> # Respawn vlka po srážce se psem
> WOLF_RESPAWN_DELAY = 3.0   # vteřiny, po které je vlk neviditelný a neaktivní
>
> # Postupné zvyšování obtížnosti (jen rychlost vlků, nikdy počet)
> DIFFICULTY_RAMP_INTERVAL = 15.0      # každých X sekund se rychlost vlků zvedne
> DIFFICULTY_SPEED_INCREMENT = 0.10    # přírůstek multiplikátoru rychlosti (0.10 = +10 %)
> DIFFICULTY_SPEED_MAX = 2.0           # cap multiplikátoru, aby hra zůstala hratelná
>
> ### GameSession (game/session.py)
> from dataclasses import dataclass, field
> import pygame
>
> @dataclass
> class GameSession:
>     tilemap: "TileMap"
>     player: "Player"
>     sheep_group: pygame.sprite.Group
>     wolf_group: pygame.sprite.Group
>     score: int = 0
>     elapsed_time: float = 0.0
>     wolf_speed_multiplier: float = 1.0   # roste s časem, řízeno DifficultyManagerem
>     difficulty_level: int = 0            # kolikrát už proběhl ramp-up (jen pro HUD)
>     wolves_repelled: int = 0             # statistika pro skóre
>     sheep_alive: int = 0                 # cache pro rychlou kontrolu game-over
>     game_over: bool = False
>
> ### Co dělat
> - Drž se popsané struktury souborů
> - Importuj konstanty z game.settings, nepoužívej magic numbers
> - Vrať vždy kompletní soubor, ne diff
> - Když si nejsi jistý kontraktem, ZEPTEJ SE, nehadej
> - Generuj kód jednoduchý natolik, že ho student obhájí ústně
>
> ### Co NEdělat
> - Nepřidávej nové externí závislosti
> - Nepoužívej threading, asyncio, multiprocessing
> - Nezavádej ECS, A* pathfinding, raycasting, BSP, event bus, DI containery,
>   service locators, state pattern přes 5 souborů
> - Nepiš třídy delší než ~150 řádků
> - Negeneruj testy, pokud o ně nepožádám
> - Neměň signatury sdílených tříd nebo klíče v GameSession bez upozornění
> - Nepoužívej cizí assety bez uvedení licence; držme se kenney.nl / OpenGameArt
>
> ## Moje aktuální role: Lane [A / B / C / D]
> [Sem zkopíruj popis své lane ze sekce 4 týmového dokumentu]
>
> ## Aktuální úkol
> [Sem napiš konkrétní požadavek pro tuto session.]
> ```

---

## 2. Architektura projektu

Struktura repozitáře (Phase 0 ji vytváří jako prázdné stuby):

```
sheep-defender/
├── main.py
├── requirements.txt
├── README.md
├── game/
│   ├── __init__.py
│   ├── app.py
│   ├── settings.py
│   ├── states.py
│   ├── session.py
│   ├── animation.py
│   ├── assets.py
│   ├── entities/
│   │   ├── __init__.py
│   │   ├── player.py
│   │   ├── sheep.py
│   │   └── wolf.py
│   ├── systems/
│   │   ├── __init__.py
│   │   ├── collision.py
│   │   ├── difficulty.py
│   │   ├── score.py
│   │   └── rules.py
│   ├── world/
│   │   ├── __init__.py
│   │   ├── tilemap.py
│   │   └── pasture_map.py
│   └── ui/
│       ├── __init__.py
│       ├── buttons.py
│       ├── splash.py
│       ├── menu.py
│       ├── game_over.py
│       └── hud.py
├── assets/
│   ├── sprites/
│   ├── tiles/
│   └── ui/
└── docs/
    ├── README.md
    └── prezentace.pdf  (vznikne v Phase 4)
```

**Princip:** každý soubor má jednoho vlastníka. Cizí lane se souboru nedotýká, jen ho importuje.

---

## 3. Sdílené kontrakty (interfacy)

Tyto signatury **vznikají v Phase 0** a od té chvíle jsou zmrazené. Kdo je chce změnit, musí informovat tým.

### 3.1 GameState enum (game/states.py)

```python
from enum import Enum, auto

class GameState(Enum):
    SPLASH = auto()
    MAIN_MENU = auto()
    PLAYING = auto()
    GAME_OVER = auto()
```

### 3.2 GameSession dataclass (game/session.py)

Viz prompt výše. Atributy lze přidávat (s informováním), nelze měnit typ ani odebrat.

**Vytvoření session na startu hry.** Při přechodu do `PLAYING` se volá tovární funkce, která vytvoří všechny počáteční entity podle konstant `SHEEP_COUNT` a `WOLF_COUNT`. Doporučená pozice: `game/session.py` (vedle dataclass). Příklad:

```python
def create_session(assets: AssetManager, tilemap: TileMap, rng: random.Random) -> GameSession:
    player = Player(tilemap.random_grass_position(rng), assets)

    sheep_group = pygame.sprite.Group()
    for _ in range(SHEEP_COUNT):
        sheep_group.add(Sheep(tilemap.random_grass_position(rng), assets))

    wolf_group = pygame.sprite.Group()
    for _ in range(WOLF_COUNT):
        wolf_group.add(Wolf(tilemap.edge_spawn_position(rng), WOLF_BASE_SPEED, assets))

    return GameSession(
        tilemap=tilemap, player=player,
        sheep_group=sheep_group, wolf_group=wolf_group,
        sheep_alive=SHEEP_COUNT,
    )
```

Tato funkce vzniká až v Phase 2 (integrace), v Phase 1 si Lane A vystačí s placeholder PLAYING stavem.

### 3.3 TileMap (game/world/tilemap.py) — vlastní Lane B

```python
class TileMap:
    width: int   # počet sloupců
    height: int  # počet řádků
    tile_size: int  # = settings.TILE_SIZE

    def render(self, surface: pygame.Surface) -> None: ...
    def is_blocked_pixel(self, x: float, y: float) -> bool: ...
    def is_blocked_rect(self, rect: pygame.Rect) -> bool: ...
    def random_grass_position(self, rng: random.Random) -> tuple[float, float]: ...
    def edge_spawn_position(self, rng: random.Random) -> tuple[float, float]: ...
```

`random_grass_position` vrací volnou pozici na trávě (uvnitř plotu).
`edge_spawn_position` vrací pozici na okraji mapy mimo plot (pro spawn vlků).

### 3.4 AssetManager (game/assets.py) — vlastní Lane B

```python
class AssetManager:
    def __init__(self) -> None: ...
    def image(self, key: str) -> pygame.Surface: ...
    def animation(self, key: str) -> "Animation": ...
    def font(self, size: int) -> pygame.font.Font: ...
```

Při chybějícím souboru vrátí placeholder (růžovo-černý čtverec). Nepádá.

**Sdílený seznam klíčů** (Lane B garantuje, Lane C/D používá):

| key | typ | popis |
|---|---|---|
| `tiles/grass` | image | dlaždice trávy |
| `tiles/fence_h` | image | plot horizontální |
| `tiles/fence_v` | image | plot vertikální |
| `tiles/fence_corner` | image | roh plotu |
| `sprites/dog` | animation (4 směry) | pes |
| `sprites/sheep` | animation (4 směry) | ovce |
| `sprites/wolf` | animation (4 směry) | vlk |
| `ui/logo` | image | logo na splash |

### 3.5 Player (game/entities/player.py) — vlastní Lane C

```python
class Player(pygame.sprite.Sprite):
    pos: pygame.math.Vector2
    rect: pygame.Rect
    image: pygame.Surface

    def __init__(self, pos: tuple[float, float], assets: AssetManager): ...
    def update(self, dt: float, keys: pygame.key.ScancodeWrapper, tilemap: TileMap) -> None: ...
```

### 3.6 Sheep (game/entities/sheep.py) — vlastní Lane C

```python
class Sheep(pygame.sprite.Sprite):
    pos: pygame.math.Vector2
    rect: pygame.Rect
    alive: bool

    def __init__(self, pos: tuple[float, float], assets: AssetManager): ...
    def update(self, dt: float, tilemap: TileMap) -> None: ...
    def kill_sheep(self) -> None: ...   # NE pygame.sprite.Sprite.kill, to dělá hodně víc
```

### 3.7 Wolf (game/entities/wolf.py) — vlastní Lane C

```python
class Wolf(pygame.sprite.Sprite):
    pos: pygame.math.Vector2
    rect: pygame.Rect
    base_speed: float                 # výchozí rychlost; efektivní = base_speed * session.wolf_speed_multiplier
    respawn_remaining: float = 0.0    # > 0 = vlk je dočasně neviditelný a neaktivní

    @property
    def is_active(self) -> bool:
        """True = vlk se hýbe, je vidět a podléhá kolizím.
        False = právě probíhá respawn delay."""
        ...

    def __init__(self, pos: tuple[float, float], base_speed: float, assets: AssetManager): ...

    def update(self, dt: float, session: "GameSession") -> None:
        """Pokud is_active: hledá nejbližší živou ovci a posouvá se k ní efektivní rychlostí.
        Pokud neaktivní: snižuje respawn_remaining; když doběhne na nulu, znovu zviditelní vlka."""
        ...

    def trigger_respawn(self, delay: float, new_position: tuple[float, float]) -> None:
        """Okamžitě přesune sprite na new_position, schová ho (image → transparentní)
        a deaktivuje na delay sekund. Sprite zůstává v sprite_group, jen se nevykresluje
        a nepočítají se s ním kolize. Po vypršení delaye se vlk znovu objeví na nové pozici."""
        ...
```

**Poznámka k vykreslování:** Lane A v render smyčce iteruje `session.wolf_group` a vlky s `is_active == False` nekreslí (jednodušší než upravovat `image.set_alpha`). Lze taky řešit v rámci samotné `Wolf.trigger_respawn` — záměnou `self.image` za transparentní surface.

### 3.8 Collision (game/systems/collision.py) — vlastní Lane C

```python
@dataclass
class CollisionEvent:
    kind: str  # "wolf_eats_sheep" nebo "dog_repels_wolf"
    sheep: Sheep | None = None
    wolf: Wolf | None = None

def detect_collisions(player: Player,
                      sheep_group: pygame.sprite.Group,
                      wolf_group: pygame.sprite.Group) -> list[CollisionEvent]:
    """Detekuje kolize přes rect.colliderect. Vlci, u kterých je is_active == False
    (probíhá respawn delay), se v detekci přeskakují — ani neútočí na ovce,
    ani je nelze odrazit dalším kontaktem s psem."""
    ...
```

### 3.9 DifficultyManager (game/systems/difficulty.py) — vlastní Lane D

```python
class DifficultyManager:
    """Spravuje obtížnost: každých DIFFICULTY_RAMP_INTERVAL sekund zvýší
    session.wolf_speed_multiplier o DIFFICULTY_SPEED_INCREMENT (cap na DIFFICULTY_SPEED_MAX)
    a inkrementuje session.difficulty_level.
    Počet vlků NEMĚNÍ — zůstává konstantně na WOLF_COUNT po celou hru."""

    def __init__(self) -> None: ...
    def update(self, dt: float, session: GameSession) -> None: ...
```

Počáteční populace vlků a ovcí vzniká jednorázově při startu hry přes `create_session` (viz sekce 3.2), nikoli v této třídě.

### 3.10 Score (game/systems/score.py) — vlastní Lane D

```python
class ScoreSystem:
    def process_events(self, events: list[CollisionEvent], session: GameSession) -> None: ...
    def tick(self, dt: float, session: GameSession) -> None: ...
```

### 3.11 Rules (game/systems/rules.py) — vlastní Lane D

```python
def check_game_over(session: GameSession) -> bool:
    """True, když session.sheep_alive == 0."""
    ...

def apply_collision_events(events: list[CollisionEvent],
                           session: GameSession,
                           rng: random.Random) -> None:
    """Aplikuje efekty detekovaných kolizí:
    - 'wolf_eats_sheep' → sheep.kill_sheep(), session.sheep_alive -= 1
    - 'dog_repels_wolf' → wolf.trigger_respawn(WOLF_RESPAWN_DELAY,
                          session.tilemap.edge_spawn_position(rng))
    Score se NEZdvíhá zde — to dělá ScoreSystem.process_events nad stejnou listou."""
    ...
```

### 3.12 HUD (game/ui/hud.py) — vlastní Lane D

```python
class HUD:
    def __init__(self, assets: AssetManager) -> None: ...
    def render(self, surface: pygame.Surface, session: GameSession) -> None: ...
```

### 3.13 Splash / Menu / GameOver / Buttons — vlastní Lane A

Lane A si vnitřní strukturu UI obrazovek řídí sama. Důležité je jen, že vrací do `Game` třídy další stav přes známý mechanismus (např. `next_state: GameState | None`).

---

## 4. Rozdělení práce do 4 lan

Cíl: co nejvíc disjunktní práce, minimální merge konflikty. Každá lane má **exkluzivní vlastnictví** určitých souborů — nikdo jiný do nich nezapisuje.

### Lane A — Aplikační skeleton & state machine

**Vlastník: [doplň jméno]**

**Vlastněné soubory (exkluzivní):**
- `main.py`
- `game/app.py`
- `game/states.py`
- `game/ui/buttons.py`
- `game/ui/splash.py`
- `game/ui/menu.py`
- `game/ui/game_over.py`

**Co dělá:**
- Hlavní třída `Game` s init Pygame, hlavní smyčkou Event → Update → Render
- Přepínání stavů SPLASH → MAIN_MENU → PLAYING → GAME_OVER
- Splash screen (logo, 2.5 s, automatický přechod)
- Hlavní menu s tlačítkem „Hrát" (a volitelně „Konec", „Jak hrát")
- Game over obrazovka s tlačítky „Hrát znovu" a „Menu" + zobrazení score
- Reusable `Button` třída (hover, klik)
- Volá `update(dt)` a `render(surface)` na aktuálním stavu
- Při vstupu do PLAYING volá `create_session(...)` (viz sekce 3.2), drží referenci a v každém frame ji updatuje
- Playing loop pořadí: input → `player.update` → `sheep_group.update` → `wolf_group.update(session)` → `detect_collisions` → `apply_collision_events` → `score.process_events` + `score.tick` → `difficulty.update` → render
- Render: tilemap, ovce, vlci (vykreslit jen ty s `is_active == True`), hráč, HUD
- Při game over přečte score ze session a předá ho game over obrazovce

**Co konzumuje:**
- `GameSession` (z `game/session.py`) — k vytvoření a předání playing logice
- `AssetManager` (Lane B) — pro splash logo, fonty, tlačítka
- Volání do "playing loopu" (viz integrace) — během Phase 1 si Lane A udělá stub PLAYING obrazovku, která jen vykresluje „PLACEHOLDER PLAYING — stiskni R pro game over". Skutečnou integraci dělá Phase 2.

**Akceptační kritérium konce Phase 1:**
- `python main.py` otevře okno, přejde ze splash do menu, kliknutí na „Hrát" otevře placeholder PLAYING obrazovku, klávesa R → GAME_OVER, kliknutí na „Menu" se vrátí do menu.

---

### Lane B — World, assety a animace

**Vlastník: [doplň jméno]**

**Vlastněné soubory (exkluzivní):**
- `game/assets.py`
- `game/animation.py`
- `game/world/tilemap.py`
- `game/world/pasture_map.py`
- celý adresář `assets/` (PNG, fonty)

**Co dělá:**
- `AssetManager` — načte obrázky, animace a fonty podle sdíleného seznamu klíčů (sekce 3.4). Při chybějícím souboru vrátí placeholder, neselže. Žádné zvuky.
- `Animation` třída — drží list framů + per-frame trvání, metoda `current_frame(elapsed: float)`. Použije Lane C.
- `TileMap` — drží layout pastviny, umí ji vykreslit, odpovídá na `is_blocked_*` dotazy.
- `pasture_map.py` — data layoutu jako 2D matice (např. 20×12 dlaždic). Travnatá plocha uvnitř, plot kolem dokola. Jedna konkrétní mapa, žádné generování.
- Nasourcuje grafiku (kenney.nl Top-Down Survivor / Tiny Town / Animal Pack jsou ideální) a uloží ji do `assets/`.
- Napíše stručný `assets/CREDITS.md` se zdrojem a licencí.

**Co konzumuje:**
- `game/settings.py` (sdílené konstanty: TILE_SIZE)

**Akceptační kritérium konce Phase 1:**
- Krátký debug skript v `tools/` (např. `tools/map_preview.py`) otevře okno a vykreslí pastvinu s plotem. `is_blocked_rect` správně hlásí kolize s plotem.
- `AssetManager.image("sprites/dog")` vrátí použitelný Surface (nebo viditelný placeholder).

---

### Lane C — Entity a entitní AI

**Vlastník: [doplň jméno]**

**Vlastněné soubory (exkluzivní):**
- `game/entities/player.py`
- `game/entities/sheep.py`
- `game/entities/wolf.py`
- `game/systems/collision.py`

**Co dělá:**
- `Player` (Pes): WASD/šipky, pohyb v pixelech, kontroluje kolize s plotem přes `tilemap.is_blocked_rect`, animuje směr pohybu (4 směry).
- `Sheep`: random walk s pauzami. Stavy IDLE / WANDER. V IDLE stojí 0.8–2.4 s, pak si vybere náhodný cíl ve vzdálenosti ~80–200 px, jde tam (omezeno tilemapou), pak zase IDLE.
- `Wolf`: každý frame najde nejbližší živou ovci a normalizovaným vektorem se k ní posouvá. Efektivní rychlost = `base_speed * session.wolf_speed_multiplier`. Při `respawn_remaining > 0` je vlk neaktivní — sprite existuje, ale neaktualizuje pozici, nevykresluje se a neúčastní se kolizí. Když timer doběhne, vlk se znovu zviditelní (na pozici, kterou mu nastavil `trigger_respawn`).
- `collision.detect_collisions(...)` → seznam `CollisionEvent` se dvěma druhy: `wolf_eats_sheep` a `dog_repels_wolf`. Detekce přes `rect.colliderect`. Vlci s `is_active == False` se v detekci přeskakují (aby je nebylo možné znovu „odrazit" během respawn delaye).

**Co konzumuje:**
- `AssetManager` (Lane B) — pro animace
- `TileMap` (Lane B) — pro kolize s plotem
- `GameSession` (Lane A / Phase 0) — Wolf čte `wolf_speed_multiplier`
- `game/settings.py` — pro rychlosti, WOLF_RESPAWN_DELAY

**Mock dependencies během Phase 1:**
- Pokud Lane B ještě nemá hotové animace, použij `pygame.Surface((48, 48))` vyplněný barvou (pes hnědý, ovce bílá, vlk šedý). Jakmile dorazí finální assety, jen prohodíš zdroj v `__init__`.

**Akceptační kritérium konce Phase 1:**
- Debug skript `tools/entities_preview.py` otevře okno, vytvoří TileMap, Player, `SHEEP_COUNT` ovcí a `WOLF_COUNT` vlků. Hráč se pohne WASD, ovce se pasou, vlci honí. Tisk událostí kolize do konzole. Po srážce pes×vlk vlk na chvíli zmizí a po `WOLF_RESPAWN_DELAY` se objeví jinde na okraji.

---

### Lane D — Herní systémy, HUD, dokumentace

**Vlastník: [doplň jméno]**

**Vlastněné soubory (exkluzivní):**
- `game/systems/difficulty.py`
- `game/systems/score.py`
- `game/systems/rules.py`
- `game/ui/hud.py`
- `docs/README.md`
- pomocné dokumentační materiály

**Co dělá:**
- `DifficultyManager`: každých `DIFFICULTY_RAMP_INTERVAL` sekund zvedne `session.wolf_speed_multiplier` o `DIFFICULTY_SPEED_INCREMENT` (cap na `DIFFICULTY_SPEED_MAX`) a inkrementuje `session.difficulty_level`. Nevytváří ani neodstraňuje vlky — jejich počet je konstantně `WOLF_COUNT`.
- `ScoreSystem`: čte `CollisionEvent` list a navyšuje skóre. Pravidla: `dog_repels_wolf` → +10 a inkrement `session.wolves_repelled`, `wolf_eats_sheep` → žádný score impact (Rules sníží `sheep_alive`). V `tick(dt)` přičítá k score 1 bod za sekundu přežití.
- `rules.check_game_over(session)`: vrací True, když `session.sheep_alive == 0`.
- `rules.apply_collision_events(events, session, rng)`: aplikuje efekty kolizí — pro `wolf_eats_sheep` zavolá `sheep.kill_sheep()` a sníží `session.sheep_alive`; pro `dog_repels_wolf` zavolá `wolf.trigger_respawn(WOLF_RESPAWN_DELAY, session.tilemap.edge_spawn_position(rng))`.
- `HUD`: levý horní roh: score velkým fontem, pod ním obtížnostní level (`difficulty_level`) a uplynulý čas. Pravý horní roh: ikonky ovcí ukazující počet zbývajících. Volitelně: malý indikátor aktuálního `wolf_speed_multiplier`.
- Dokumentace: `docs/README.md` s herní mechanikou, ovládáním, screenshoty. Plán prezentace (10–20 slidů).

**Co konzumuje:**
- `GameSession`, `Wolf` (Lane C), `AssetManager` (Lane B), `TileMap` (Lane B), `CollisionEvent` (Lane C)
- `game/settings.py` — pro DIFFICULTY_* a WOLF_RESPAWN_DELAY konstanty

**Mock dependencies během Phase 1:**
- Pokud Lane C ještě nemá hotového `Wolf`, vytvoř lokální stub class s `base_speed` a `respawn_remaining`, aby šly testovat události kolize. Po integraci přepneš na import z Lane C.

**Akceptační kritérium konce Phase 1:**
- DifficultyManager v 60s simulaci posouvá `session.wolf_speed_multiplier` očekávaným způsobem (1.0 → 1.1 → 1.2 → … do capu 2.0). ScoreSystem správně reaguje na podstrčené eventy. `apply_collision_events` po `dog_repels_wolf` zavolá `trigger_respawn` se správnou edge pozicí. HUD se vykreslí proti mock session a vypadá čitelně.

---

## 5. Fáze projektu a harmonogram

Předpoklad: 4 lidé, ~16 osobohodin každý, celkem ~64 osobohodin. Realistická wall-clock doba 3–5 dní podle koordinace.

### Phase 0 — Společná příprava (1.5–2 h, **všichni společně** — ideálně call/sezení)

Bez tohoto kroku se Phase 1 rozpadne. Sednout si společně, projít sekce 2 a 3 tohoto dokumentu, dohodnout změny.

Konkrétní výstupy:
1. Inicializovat Git repository (GitHub / GitLab), nastavit `.gitignore` (Python, .venv, __pycache__, .vscode, atd.)
2. Vytvořit prázdnou strukturu složek dle sekce 2
3. Napsat `requirements.txt` (pygame, numpy)
4. Napsat `game/settings.py` s konstantami ze sdíleného promptu
5. Napsat `game/states.py` a `game/session.py` přesně podle sekce 3
6. Vytvořit prázdné `__init__.py` ve všech package
7. Vytvořit prázdné stuby pro všechny soubory s `# TODO Lane X` komentářem na první řádku
8. Vytvořit větve `lane-a`, `lane-b`, `lane-c`, `lane-d` z `main`
9. Rozdělit role (kdo je A/B/C/D) a založit sdílený dokument s úkoly (Trello/Notion/Excel)
10. Každý člen si zkopíruje sdílený prompt + sekci své lane a uloží lokálně

**Hard rule:** po Phase 0 už nikdo nemění `settings.py`, `states.py`, ani `session.py` bez konzultace s týmem.

### Phase 1 — Paralelní implementace (každý ~9–12 h, **disjunktně**)

Každý člen pracuje výhradně na svých vlastněných souborech v Sekci 4. Používá mock implementace cizích kontraktů, aby se neblokovali.

Doporučený sled úkolů uvnitř každé lane:
- Začni od základů (např. Lane A: nejdřív Game třída + smyčka, pak až tlačítka)
- Po každém logickém celku spusť `python main.py` (nebo svůj debug skript) — funguje?
- Commituj často (po každém funkčním celku), pushuj na svou větev
- Akceptační kritérium z konce sekce své lane = signál, že je čas na merge

### Phase 2 — Integrace (3–4 h, **všichni společně**)

1. Merge `lane-b` (assety + tilemap) jako první do `main` — má nejmíň závislostí
2. Lane C rebase, otestuj, že entity fungují s reálnými assety, merge do `main`
3. Lane D rebase, otestuj DifficultyManager + HUD se skutečnými entitami, merge do `main`
4. Lane A rebase, otestuj plný flow splash → menu → playing (s reálnými entitami a HUD) → game over, merge do `main`
5. Společný bug-fix maraton — typické problémy:
   - Vlci se po respawnu objeví uvnitř plotu místo na okraji
   - Ovce uvíznou v rohu
   - Score se neaktualizuje při kolizi
   - Vlk po respawnu zůstává neviditelný (zapomenuté zviditelnění)
   - Hra padá při game over (entity z předchozí runy se správně neuvolnily)
   - Velikosti spritů nesedí na rect, kolize se chovají divně

### Phase 3 — Balance & polish (2–3 h, **všichni**)

- Hrát hru opakovaně, zapisovat problémy s obtížností
- Doladit konstanty v `settings.py` — především: `SHEEP_COUNT`, `WOLF_COUNT`, `WOLF_BASE_SPEED`, `DIFFICULTY_RAMP_INTERVAL`, `DIFFICULTY_SPEED_INCREMENT`, `WOLF_RESPAWN_DELAY`
- Cílem je hra, která trvá 1.5–3 minuty pro průměrného hráče (ne 10 vteřin, ne 10 minut)
- Drobné UI vylepšení (kontrast, čitelnost, hover stavy)
- Vytvořit 6–10 screenshotů pro prezentaci a pro případ že hra na obhajobě nepoběží

### Phase 4 — Odevzdání (2–3 h, **rozděleno**)

- **Lane A**: pročistit kód v `app.py` a UI, doplnit docstringy
- **Lane B**: finální `CREDITS.md`, ujistit se že assety lze nahradit bez změny kódu
- **Lane C**: pročistit AI vlka a sheep wander logiku, doplnit komentáře
- **Lane D**: napsat dokumentaci (PDF), prezentaci (PDF, 10–20 slidů), screenshoty
- **Všichni**: vyplnit úvodní slide s rolemi (kdo dělal jakou část kódu)
- Finální `python main.py` test na čistém prostředí (ideálně někoho mimo tým)
- Zabalit projekt do ZIP + nahrát do odevzdávacího systému

### Souhrnný harmonogram (sample, sjednocujte v týmu)

| Den | Phase | Účastníci | Hodin |
|---|---|---|---|
| 1, večer | 0 | všichni | 2 |
| 2 | 1 | každý sám | 4–6 |
| 3 | 1 | každý sám | 4–6 |
| 4, dopoledne | 2 | všichni | 3–4 |
| 4, odpoledne | 3 | všichni | 2 |
| 5 | 4 | rozděleno | 2–3 |

---

## 6. Pravidla spolupráce s Gitem

- **Větvení**: každý pracuje na `lane-a/b/c/d`. Žádné přímé pushe do `main`.
- **Komity**: malé, často. Anglicky nebo česky, ale konzistentně.
- **Pull requesty**: před mergem do `main` musí kód projít `python main.py` bez výjimky.
- **Nesahej do cizích souborů.** Pokud potřebuješ jejich úpravu, napiš vlastníkovi do týmového chatu, ať to udělá on. Tímto se vyhneme 90 % merge konfliktů.
- **Jediné výjimky:** `settings.py`, `session.py`, `states.py` — měnit může kdokoli, ale jen po krátké konzultaci v chatu.
- **AI generovaný kód projdi očima** předtím než ho commitneš. Halucinované Pygame API se stávají často.

---

## 7. Checklist před odevzdáním

Funkčnost:
- [ ] `python main.py` spustí hru bez chyb
- [ ] Splash → menu přechod proběhne automaticky
- [ ] Menu má funkční tlačítko Hrát
- [ ] Hráč se pohybuje WASD i šipkami
- [ ] Hráč nemůže projít plotem
- [ ] Ovce se náhodně pasou
- [ ] Na mapě je konstantní počet vlků (WOLF_COUNT)
- [ ] Vlci honí nejbližší živou ovci
- [ ] Vlci se časem zrychlují (wolf_speed_multiplier roste)
- [ ] Kolize vlk × ovce ovci odstraní
- [ ] Kolize pes × vlk → vlk zmizí a po WOLF_RESPAWN_DELAY se objeví na novém místě na okraji mapy
- [ ] Respawnující se vlk není během respawn delaye vidět ani se nezúčastní kolizí
- [ ] HUD ukazuje score, level obtížnosti, čas, počet zbývajících ovcí
- [ ] Game over nastane, když padne poslední ovce
- [ ] Game over screen ukazuje finální score
- [ ] Restart z game over funguje
- [ ] `SHEEP_COUNT` a `WOLF_COUNT` v `settings.py` lze změnit a hra to respektuje bez dalších úprav

Splnění zadání:
- [ ] Úvodní obrazovka + auto přechod do menu
- [ ] Menu s tlačítkem Hrát
- [ ] Více typů spritů (pes, ovce, vlk = 3 typy)
- [ ] Spritesheety / tiles (pastvina z dlaždic)
- [ ] Animace (chůze entit)
- [ ] Zpracování vstupů (klávesnice)
- [ ] Kolize + reakce (2 druhy: vlk×ovce, pes×vlk)
- [ ] Počítání bodů a vykreslení
- [ ] Pouze pygame + numpy v `requirements.txt`
- [ ] (Pozn.: zvuk záměrně neimplementujeme — volitelný bod ze zadání vynecháváme)

Odevzdávané artefakty:
- [ ] ZIP s kódem (bez .venv, bez __pycache__)
- [ ] PDF dokumentace
- [ ] PDF prezentace 10–20 slidů
- [ ] Úvodní slide s jmény všech 4 členů týmu a popisem co kdo dělal (lane = jasná stopa)
- [ ] Sada screenshotů ze hry (6–10 ks) pro případ že vyučujícímu hra nepůjde spustit
- [ ] `CREDITS.md` se zdroji assetů a licencemi

Pro obhajobu:
- [ ] Každý člen umí vysvětlit svou lane (architektura, klíčové třídy, rozhodnutí)
- [ ] Tým ví, jak by vysvětlil sdílené části (settings, session, state machine)
- [ ] Mít v záloze odpovědi na: „Proč jste použili XYZ?", „Co byste udělali jinak?", „Jak byste rozšířili o další úroveň?"

---

**Poslední rada:** dokument berte jako kontrakt, ale ne dogma. Pokud někomu konkrétní detail v praxi nesedí, napište do týmového chatu, dohodněte se a aktualizujte tento dokument. Co se ale nesmí stát: ticho měnit kontrakty (`session.py`, `settings.py`, signatury sdílených tříd) bez ostatních.
