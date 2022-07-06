from src.app import App
import sys


if __name__ == "__main__":
    special_args = None
    if len(sys.argv) > 1:
        special_args = sys.argv[1]
    App().run(special_args)
