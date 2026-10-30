"""Lake Constance (Bodensee) forecasting."""

from pathlib import Path

# Project root = two levels above this file (src/bodensee/__init__.py -> project root)
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
