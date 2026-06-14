"""Entry point hry Sheep Defender.

Spusteni: python main.py
"""
from __future__ import annotations

from pathlib import Path
import sys
import traceback

from game.app import Game


def main() -> None:
    game = Game()
    game.run()


def error_log_path() -> Path:
    """Return a writable log path for uncaught errors."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent / "sheep_defender_error.log"
    return Path(__file__).resolve().parent / "sheep_defender_error.log"


def _show_windowed_error(log_path: Path) -> None:
    if sys.platform != "win32" or not getattr(sys, "frozen", False):
        return

    try:
        import ctypes

        ctypes.windll.user32.MessageBoxW(
            None,
            f"Sheep Defender crashed.\n\nDetails were written to:\n{log_path}",
            "Sheep Defender",
            0x10,
        )
    except Exception:
        return


if __name__ == "__main__":
    try:
        main()
    except Exception:
        log_path = error_log_path()
        log_path.write_text(traceback.format_exc(), encoding="utf-8")
        _show_windowed_error(log_path)
        if not getattr(sys, "frozen", False):
            raise
        sys.exit(1)
