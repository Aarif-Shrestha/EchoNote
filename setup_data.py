#!/usr/bin/env python3
"""Create missing data/ files with safe defaults.

Run this once after cloning the repo so the app has the JSON files it expects.
It will NOT overwrite existing files.
"""
from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"

DEFAULTS = {
    "users.json": {},
    "transcripts.json": {},
    "audios.json": {},
    "bot_meetings.json": {}
}


def ensure_data_dir():
    if not DATA_DIR.exists():
        print(f"Creating data directory at: {DATA_DIR}")
        DATA_DIR.mkdir(parents=True, exist_ok=True)


def write_defaults():
    created = []
    skipped = []
    for name, default in DEFAULTS.items():
        path = DATA_DIR / name
        if path.exists():
            skipped.append(name)
            continue
        try:
            with path.open("w", encoding="utf-8") as f:
                json.dump(default, f, indent=2, ensure_ascii=False)
            created.append(name)
        except Exception as e:
            print(f"Failed to create {path}: {e}")
    return created, skipped


def main():
    ensure_data_dir()
    created, skipped = write_defaults()
    if created:
        print("Created files:")
        for f in created:
            print(f"  - {f}")
    if skipped:
        print("Skipped (already exist):")
        for f in skipped:
            print(f"  - {f}")
    if not created and not skipped:
        print("No files created or found. Check permissions.")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print("Error during setup:", e)
        sys.exit(1)
