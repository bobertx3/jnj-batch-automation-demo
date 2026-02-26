"""Compatibility wrapper. Primary seed script now lives in db_setup/seed_db.py."""

from pathlib import Path
import runpy


if __name__ == "__main__":
    runpy.run_path(str(Path(__file__).parent / "db_setup" / "seed_db.py"), run_name="__main__")
