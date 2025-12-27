"""Data models, constants, and pure utilities for Cactus."""

import random
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path


# Configuration
NUM_LINES_CAPTURE = 8
CHECK_INTERVAL = 2.5
EXPORT_CAPTURED = False

# Paths
CACTUS_DIR = Path.home() / ".cactus"
PATHS_FILE = CACTUS_DIR / "paths.txt"

# Theme
ACCENT_COLOR = "#5cb85c"

# Random name generation
ADJECTIVES = [
    "swift", "bright", "quiet", "bold", "cool", "calm", "wild", "deep",
    "keen", "wise", "pure", "warm", "fresh", "smooth", "sharp", "clear"
]

NOUNS = [
    "fox", "hawk", "wolf", "bear", "lynx", "eagle", "raven", "otter",
    "spark", "wave", "node", "pixel", "cloud", "forge", "vertex", "prism"
]


def generate_random_name() -> str:
    """Generate a random session name like 'swift-fox' or 'bright-node'."""
    return f"{random.choice(ADJECTIVES)}-{random.choice(NOUNS)}"


class Status(Enum):
    WORKING = "yellow"
    WAITING = "red"
    READY = "green"
    READ = "white"


@dataclass
class Session:
    name: str
    path: str
    tmux_session_name: str
    last_content: str = ""
    status: Status = Status.READY
    is_active: bool = False
    last_visited: datetime = field(default_factory=datetime.now)


def format_time_ago(last_visited: datetime) -> str:
    """Format elapsed time since last visit as a compact string."""
    total_seconds = int((datetime.now() - last_visited).total_seconds())

    if total_seconds < 60:
        return "now"
    elif total_seconds < 3600:
        return f"{total_seconds // 60}m"
    elif total_seconds < 86400:
        return f"{total_seconds // 3600}h"
    elif total_seconds < 604800:
        return f"{total_seconds // 86400}d"
    else:
        return f"{total_seconds // 604800}w"


def load_paths() -> list[str]:
    """Load paths from ~/.cactus/paths.txt."""
    if not PATHS_FILE.exists():
        return []
    try:
        return [line.strip() for line in PATHS_FILE.read_text().splitlines() if line.strip()]
    except Exception:
        return []


def save_path(path: str) -> None:
    """Add a path to ~/.cactus/paths.txt if it doesn't exist."""
    CACTUS_DIR.mkdir(parents=True, exist_ok=True)
    existing = load_paths()
    normalized = str(Path(path).expanduser().resolve())

    for p in existing:
        if str(Path(p).expanduser().resolve()) == normalized:
            return

    existing.insert(0, path)
    PATHS_FILE.write_text("\n".join(existing) + "\n")


def delete_path(path: str) -> None:
    """Remove a path from ~/.cactus/paths.txt."""
    existing = load_paths()
    if path in existing:
        existing.remove(path)
        if existing:
            PATHS_FILE.write_text("\n".join(existing) + "\n")
        else:
            PATHS_FILE.unlink(missing_ok=True)
