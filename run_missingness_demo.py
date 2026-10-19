from pathlib import Path

from src.presentation_demos import run


if __name__ == "__main__":
    destination = run(Path(__file__).resolve().parent, "missingness")
    print("Missingness demo completed.")
    print("New output directory:", destination)
