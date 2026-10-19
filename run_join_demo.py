from pathlib import Path

from src.presentation_demos import run


if __name__ == "__main__":
    destination = run(Path(__file__).resolve().parent, "join")
    print("JOIN audit completed.")
    print("New output directory:", destination)
