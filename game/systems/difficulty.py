"""Difficulty settings and progressive wolf wave management."""
from __future__ import annotations

from game import settings
from game.session import GameSession


def normalize_difficulty(difficulty: str) -> str:
    """Return a supported difficulty key."""
    value = difficulty.lower()
    if value in settings.DIFFICULTY_CONFIG:
        return value
    return settings.DEFAULT_DIFFICULTY


def get_speed_increase(difficulty: str) -> float:
    """Return the per-speed-up multiplier increase for a difficulty."""
    key = normalize_difficulty(difficulty)
    return float(settings.DIFFICULTY_CONFIG[key]["speed_increase"])


def get_speed_maximum(difficulty: str) -> float:
    """Return the maximum wolf speed multiplier for a difficulty."""
    key = normalize_difficulty(difficulty)
    return float(settings.DIFFICULTY_CONFIG[key]["max_multiplier"])


class DifficultyManager:
    """Advance waves by alternating speed-ups and wolf spawns."""

    def __init__(self) -> None:
        self._time_to_next_wave = settings.WAVE_INTERVAL

    def update(self, dt: float, session: GameSession) -> None:
        """Advance due waves and age the transient HUD notice."""
        if session.wave_notice_remaining > 0.0:
            session.wave_notice_remaining = max(
                0.0,
                session.wave_notice_remaining - dt,
            )

        self._time_to_next_wave -= dt
        while self._time_to_next_wave <= 0.0:
            self.advance_wave(session)
            self._time_to_next_wave += settings.WAVE_INTERVAL

    def advance_wave(self, session: GameSession) -> str:
        """Advance exactly one wave and return its action name."""
        session.wave += 1
        session.difficulty_level = session.wave - 1

        if session.speedups_completed < session.speedups_required:
            action = self._apply_speed_up(session)
        else:
            action = self._apply_spawn_wave(session)

        session.wave_action = action
        session.wave_notice_remaining = 1.0
        return action

    def _apply_speed_up(self, session: GameSession) -> str:
        increase = get_speed_increase(session.difficulty)
        maximum = get_speed_maximum(session.difficulty)
        session.wolf_speed_multiplier = min(
            session.wolf_speed_multiplier + increase,
            maximum,
        )
        session.speedups_completed += 1
        return "speed_up"

    def _apply_spawn_wave(self, session: GameSession) -> str:
        if len(session.wolf_group) < settings.WOLF_MAX_COUNT:
            self._spawn_wolf(session)

        session.speedups_required += 1
        session.speedups_completed = 0
        return "new_wolf"

    def _spawn_wolf(self, session: GameSession) -> None:
        if session.assets is None or session.rng is None:
            return

        from game.entities.wolf import Wolf

        position = session.tilemap.edge_spawn_position(session.rng)
        session.wolf_group.add(
            Wolf(position, settings.WOLF_BASE_SPEED, session.assets),
        )
