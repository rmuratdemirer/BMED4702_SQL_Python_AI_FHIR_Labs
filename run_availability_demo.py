from pathlib import Path

from src.presentation_demos import run


if __name__ == "__main__":
    destination = run(Path(__file__).resolve().parent, "availability")
    print("Availability-lag demo completed.")
    print("New output directory:", destination)
