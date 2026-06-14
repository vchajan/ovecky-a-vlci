"""Generate legacy deterministic WAV placeholders for local development.

These generated sounds are not production assets. Real game audio should be
placed in ``assets/audio`` with the filenames registered by ``game.assets``.
"""
from __future__ import annotations

import math
import random
import struct
import wave
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
AUDIO_DIR = ROOT_DIR / "assets" / "audio"
SAMPLE_RATE = 22050
MAX_AMPLITUDE = 32767


def main() -> None:
    AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    _write_effect("bark.wav", _bark())
    _write_effect("sheep_bleat.wav", _bleat(base=520.0, panic=False))
    _write_effect("sheep_panic.wav", _bleat(base=700.0, panic=True))
    _write_effect("sheep_loss.wav", _falling_tone(360.0, 160.0, 0.45, 0.34))
    _write_effect("wolf_growl.wav", _growl())
    _write_effect("wolf_howl.wav", _howl())
    _write_effect("wolf_flee.wav", _flee_yelp())


def _write_effect(filename: str, samples: list[float]) -> None:
    path = AUDIO_DIR / filename
    if path.exists():
        return

    with wave.open(str(path), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(SAMPLE_RATE)
        frames = bytearray()
        for value in samples:
            clamped = max(-1.0, min(1.0, value))
            frames.extend(struct.pack("<h", round(clamped * MAX_AMPLITUDE)))
        wav.writeframes(bytes(frames))


def _tone(
    duration: float,
    frequency: float,
    volume: float,
    vibrato: float = 0.0,
    seed: int = 0,
) -> list[float]:
    rng = random.Random(seed)
    count = round(duration * SAMPLE_RATE)
    samples: list[float] = []
    for index in range(count):
        t = index / SAMPLE_RATE
        attack = min(1.0, t / 0.035)
        release = min(1.0, (duration - t) / 0.08)
        envelope = max(0.0, min(attack, release))
        wobble = math.sin(t * math.tau * 6.0) * vibrato
        noise = (rng.random() * 2.0 - 1.0) * volume * 0.08
        sample = math.sin(t * math.tau * (frequency + wobble)) * volume
        samples.append((sample + noise) * envelope)
    return samples


def _concat(*parts: list[float], gap: float = 0.0) -> list[float]:
    samples: list[float] = []
    silence = [0.0] * round(gap * SAMPLE_RATE)
    for part in parts:
        if samples and silence:
            samples.extend(silence)
        samples.extend(part)
    return samples


def _bark() -> list[float]:
    return _concat(
        _tone(0.09, 210.0, 0.34, vibrato=18.0, seed=1),
        _tone(0.11, 155.0, 0.28, vibrato=12.0, seed=2),
        gap=0.035,
    )


def _bleat(base: float, panic: bool) -> list[float]:
    first = _tone(0.16, base, 0.22 if not panic else 0.28, vibrato=65.0, seed=3)
    second = _tone(0.20, base * (0.82 if not panic else 1.16), 0.20, vibrato=55.0, seed=4)
    return _concat(first, second, gap=0.03)


def _falling_tone(start: float, end: float, duration: float, volume: float) -> list[float]:
    count = round(duration * SAMPLE_RATE)
    samples: list[float] = []
    for index in range(count):
        t = index / SAMPLE_RATE
        progress = index / max(1, count - 1)
        frequency = start + (end - start) * progress
        envelope = min(1.0, t / 0.04) * max(0.0, 1.0 - progress)
        samples.append(math.sin(t * math.tau * frequency) * volume * envelope)
    return samples


def _growl() -> list[float]:
    rng = random.Random(5)
    count = round(0.55 * SAMPLE_RATE)
    samples: list[float] = []
    for index in range(count):
        t = index / SAMPLE_RATE
        envelope = min(1.0, t / 0.08) * min(1.0, (0.55 - t) / 0.12)
        rough = math.sin(t * math.tau * 82.0) + 0.45 * math.sin(t * math.tau * 121.0)
        noise = (rng.random() * 2.0 - 1.0) * 0.18
        samples.append((rough * 0.18 + noise) * envelope)
    return samples


def _howl() -> list[float]:
    count = round(0.8 * SAMPLE_RATE)
    samples: list[float] = []
    for index in range(count):
        t = index / SAMPLE_RATE
        progress = index / max(1, count - 1)
        frequency = 270.0 + math.sin(progress * math.pi) * 170.0
        envelope = min(1.0, t / 0.15) * min(1.0, (0.8 - t) / 0.22)
        samples.append(math.sin(t * math.tau * frequency) * 0.24 * envelope)
    return samples


def _flee_yelp() -> list[float]:
    return _concat(
        _tone(0.11, 620.0, 0.24, vibrato=85.0, seed=6),
        _falling_tone(460.0, 230.0, 0.18, 0.18),
        gap=0.02,
    )


if __name__ == "__main__":
    main()
