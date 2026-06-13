"""Entry point hry Sheep Defender.

Spuštění: python main.py
"""
from game.app import Game


def main() -> None:
    game = Game()
    game.run()


if __name__ == "__main__":
    main()
