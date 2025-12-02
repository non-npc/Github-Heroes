"""
Configuration constants and settings for Github Heroes.
"""
import os
from pathlib import Path

# Application info
APP_NAME = "Github Heroes"
APP_VERSION = "1.0.0"

# Paths
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
ASSETS_DIR = BASE_DIR / "assets"
LOGS_DIR = BASE_DIR / "logs"

# Ensure directories exist
DATA_DIR.mkdir(exist_ok=True)
ASSETS_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)

# Database
DB_PATH = DATA_DIR / "github_heroes.db"

# Window defaults
DEFAULT_WINDOW_WIDTH = 1280
DEFAULT_WINDOW_HEIGHT = 720

# GitHub scraping
DEFAULT_BRANCHES = ["main", "master"]
GITHUB_RAW_BASE = "https://raw.githubusercontent.com"
GITHUB_BASE = "https://github.com"
GITHUB_SEARCH_BASE = "https://github.com/search"

# Request settings
REQUEST_TIMEOUT = 30
REQUEST_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

# Game constants
DEFAULT_PLAYER_STATS = {
    "hp": 100,
    "attack": 10,
    "defense": 5,
    "speed": 8,
    "luck": 5
}

XP_PER_LEVEL = 100
STAT_INCREASE_PER_LEVEL = 2

# Keyword groups for README analysis
KEYWORD_GROUPS = {
    "web": ["html", "css", "javascript", "react", "frontend", "vue", "angular", "dom", "browser"],
    "backend": ["api", "server", "database", "django", "flask", "node", "express", "backend", "rest"],
    "cli": ["cli", "command-line", "terminal", "console", "shell", "bash"],
    "scraping": ["scrape", "crawler", "spider", "parsing", "extract"],
    "ai": ["machine learning", "neural", "deep learning", "ai", "artificial intelligence", "ml", "tensorflow", "pytorch"]
}

# Health state thresholds (days since last commit)
HEALTH_VIBRANT = 14
HEALTH_STABLE = 90
HEALTH_FRAIL = 365

