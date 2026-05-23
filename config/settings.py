"""Project settings and paths."""

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]

PATHS = {
    "core": BASE_DIR / "core",
    "predictions": BASE_DIR / "predictions",
    "analytics": BASE_DIR / "analytics",
    "logs": BASE_DIR / "logs",
    "config": BASE_DIR / "config",
    "dados": BASE_DIR / "dados",
}

LOG_FILES = {
    "execution": BASE_DIR / "logs" / "execution.log",
    "errors": BASE_DIR / "logs" / "errors.log",
    "validation": BASE_DIR / "logs" / "validation.log",
}
