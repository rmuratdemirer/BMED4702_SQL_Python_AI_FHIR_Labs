"""Run only the Week 1 table-count demonstration."""

from pathlib import Path

from src.presentation_demos import run


def main() -> None:
    project_root = Path(__file__).resolve().parent
    output_directory = run(project_root, "tables")
    print("Table-count demo completed.")
    print("New output directory:", output_directory)


if __name__ == "__main__":
    main()
