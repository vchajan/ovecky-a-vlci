# Sheep Defender

Semestrální projekt v Pygame — hra, kde pes brání stádo ovcí před vlky.

## Spuštění

```bash
python -m venv .venv
source .venv/bin/activate     # Linux/Mac
# .venv\Scripts\activate      # Windows
pip install -r requirements.txt
python main.py
```

## Windows EXE

1. Dvakrat kliknete na `build_exe.bat`.
2. Po dokonceni otevrete slozku `dist`.
3. Dvakrat kliknete na `SheepDefender.exe`.

Vysledny hrac nepotrebuje nainstalovany Python, terminal ani PyInstaller.
Build vytvori jeden windowed soubor `dist/SheepDefender.exe`, ktery pri
neocekavane chybe zapise `sheep_defender_error.log` vedle `.exe`.

## Ovládání

- WASD nebo šipky: pohyb psa
- Esc: konec hry / pauza

## Obtiznosti a vlny

Hlavni menu nabizi tri obtiznosti: Easy, Medium a Hard. Vychozi volba je
Medium. Tlacitko `Hrat` spusti novou hru s aktualne zvolenou obtiznosti,
`Hrat znovu` zachova obtiznost posledni hry a navrat do menu dovoli vybrat
jinou obtiznost.

Vsechny obtiznosti zacinaji stejne:

- Wave 1
- 3 vlci
- rychlostni multiplikator 1.00
- efektivni rychlost vlka `WOLF_BASE_SPEED * 1.0`, tedy 60 px/s

Obtiznost ovlivnuje az speed-up vlny:

- Easy: +0.05 za speed-up, maximum 1.8
- Medium: +0.08 za speed-up, maximum 2.3
- Hard: +0.12 za speed-up, maximum 2.8

Vlna se posouva kazdych 15 sekund. Kazda nova vlna udela prave jednu akci:
bud zvysi rychlost vlku, nebo prida jednoho vlka az do maxima 8. Cyklus se
postupne prodluzuje:

```text
Wave 1: start, 3 vlci, speed 1.00
Wave 2: speed-up
Wave 3: novy vlk
Wave 4: speed-up 1/2
Wave 5: speed-up 2/2
Wave 6: novy vlk
Wave 7-9: tri speed-upy
Wave 10: novy vlk
```

## Animace

Postavy pouzivaji generovane spritesheety v `assets/sprites/`:

- `dog_sheet.png`: 256 x 256 px, 4 radky walk animaci
- `sheep_sheet.png`: 256 x 256 px, 4 radky walk animaci
- `wolf_sheet.png`: 256 x 512 px, 4 radky walk animaci a 4 radky flee animaci

Kazdy frame ma 64 x 64 px a kazdy smer ma 4 framy. Radky jsou vzdy:
down, left, right, up. Vlk ma navic flee radky ve stejnem poradi.

PNG se generuji deterministicky pres Pygame:

```bash
python tools/generate_spritesheets.py
```

Po odrazeni psem vlk dve sekundy utika pomoci flee animace, nemuze zrat ovce
ani znovu pridavat skore, potom zmizi, respawnuje se na validni edge pozici a
vrati se do stavu chasing.

## Struktura projektu

Detailní popis architektury, kontraktů a rozdělení rolí najdete v `docs/Sheep_Defender_team_plan.md`.

## Tým

- Lane A — Aplikační skeleton & state machine: _doplň jméno_
- Lane B — World, assety a animace: _doplň jméno_
- Lane C — Entity a entitní AI: _doplň jméno_
- Lane D — Herní systémy, HUD a dokumentace: _doplň jméno_
