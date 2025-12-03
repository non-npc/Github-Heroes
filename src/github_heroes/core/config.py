"""
Configuration constants and settings for Github Heroes.
"""

import sys
from importlib.metadata import version
from pathlib import Path

# Application info
APP_NAME = "Github Heroes"
APP_VERSION = version("github-heroes")


def get_resource_path(relative_path):
    """
    Get resource path that works for both development and PyInstaller.
    When running from PyInstaller, sys._MEIPASS contains the path to the temp folder.
    """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = Path(sys._MEIPASS)
    except AttributeError:
        # Running in development mode
        base_path = Path(__file__).parent.parent
    return base_path / relative_path


# Paths
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
ASSETS_DIR = BASE_DIR / "assets"
LOGS_DIR = BASE_DIR / "logs"

# Icon paths (works for both development and compiled)
APP_ICON_ICO = get_resource_path("assets/appicons/GitHubRPG.ico")
APP_ICON_PNG = get_resource_path("assets/appicons/GitHubRPG.png")
APP_ICON_SVG = get_resource_path(
    "assets/appicons/GithubRPG.svg"
)  # Note: lowercase 'h' in Github

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
DEFAULT_PLAYER_STATS = {"hp": 100, "attack": 10, "defense": 5, "speed": 8, "luck": 5}

XP_PER_LEVEL = 100
STAT_INCREASE_PER_LEVEL = 2

# Player classes (mix of classic RPG and silly ones)
PLAYER_CLASSES = [
    # Classic RPG Classes
    "Warrior",
    "Paladin",
    "Ranger",
    "Rogue",
    "Mage",
    "Wizard",
    "Cleric",
    "Druid",
    "Bard",
    "Monk",
    "Barbarian",
    "Necromancer",
    "Assassin",
    "Knight",
    "Sorcerer",
    "Warlock",
    "Shaman",
    "Priest",
    "Fighter",
    "Thief",
    # Silly/Fun Classes
    "BBQ Pit Chef",
    "Code Wizard",
    "Bug Hunter",
    "Stack Overflow Navigator",
    "Coffee Addict",
    "Keyboard Warrior",
    "Git Master",
    "Merge Conflict Resolver",
    "Documentation Reader",
    "Indentation Enforcer",
    "Variable Namer",
    "Comment Writer",
    "Test Coverage Champion",
    "Deploy Friday Survivor",
    "Legacy Code Maintainer",
    "API Key Finder",
    "Error Message Decoder",
    "Stack Trace Reader",
    "Dependency Manager",
    "Build Fixer",
]

# Keyword groups for README analysis
KEYWORD_GROUPS = {
    "web": [
        "html",
        "css",
        "javascript",
        "react",
        "frontend",
        "vue",
        "angular",
        "dom",
        "browser",
    ],
    "backend": [
        "api",
        "server",
        "database",
        "django",
        "flask",
        "node",
        "express",
        "backend",
        "rest",
    ],
    "cli": ["cli", "command-line", "terminal", "console", "shell", "bash"],
    "scraping": ["scrape", "crawler", "spider", "parsing", "extract"],
    "ai": [
        "machine learning",
        "neural",
        "deep learning",
        "ai",
        "artificial intelligence",
        "ml",
        "tensorflow",
        "pytorch",
    ],
}

# Enemy name generation: Prefixes and Suffixes
# These combine to create unique enemy names (prefix_count * suffix_count combinations)
ENEMY_PREFIXES = {
    # Generic prefixes (work with any keyword)
    "generic": [
        "Ancient",
        "Corrupted",
        "Dark",
        "Eternal",
        "Forgotten",
        "Hidden",
        "Lost",
        "Mystic",
        "Shadow",
        "Twisted",
        "Void",
        "Wandering",
        "Ancient",
        "Cursed",
        "Fallen",
        "Grim",
        "Hollow",
        "Silent",
        "Vengeful",
        "Withering",
        "Broken",
        "Chaotic",
        "Dread",
        "Frozen",
        "Glimmering",
        "Haunted",
        "Infernal",
        "Jagged",
        "Keen",
        "Luminous",
        "Muted",
        "Noxious",
    ],
    # AI-themed prefixes
    "ai": [
        "Neural",
        "Quantum",
        "Digital",
        "Synthetic",
        "Binary",
        "Algorithmic",
        "Computational",
        "Cybernetic",
        "Data",
        "Logic",
        "Matrix",
        "Protocol",
        "Virtual",
        "Analytical",
        "Cognitive",
    ],
    # Web-themed prefixes
    "web": [
        "Frontend",
        "Browser",
        "DOM",
        "CSS",
        "JavaScript",
        "React",
        "Vue",
        "Angular",
        "Web",
        "HTML",
        "Client",
        "UI",
        "UX",
        "Interface",
        "Markup",
        "Stylish",
    ],
    # Backend-themed prefixes
    "backend": [
        "Server",
        "API",
        "Database",
        "Daemon",
        "Service",
        "Backend",
        "REST",
        "GraphQL",
        "Microservice",
        "Container",
        "Docker",
        "Kubernetes",
        "Node",
        "Express",
        "Django",
        "Flask",
    ],
    # CLI-themed prefixes
    "cli": [
        "Terminal",
        "Console",
        "Command",
        "Shell",
        "CLI",
        "Bash",
        "Prompt",
        "Script",
        "Command-Line",
        "Interactive",
        "Text",
        "ASCII",
        "TTY",
        "Shell",
        "Executable",
    ],
    # Scraping-themed prefixes
    "scraping": [
        "Web",
        "Crawler",
        "Spider",
        "Scraper",
        "Parser",
        "Extractor",
        "Harvester",
        "Collector",
        "Bot",
        "Agent",
        "Hunter",
        "Gatherer",
        "Indexer",
        "Searcher",
        "Tracker",
    ],
}

ENEMY_SUFFIXES = {
    # Generic suffixes (work with any keyword)
    "generic": [
        "Spirit",
        "Entity",
        "Wraith",
        "Specter",
        "Phantom",
        "Guardian",
        "Warden",
        "Keeper",
        "Sentinel",
        "Defender",
        "Protector",
        "Watcher",
        "Beast",
        "Creature",
        "Fiend",
        "Demon",
        "Monster",
        "Horror",
        "Abomination",
        "Terror",
        "Archon",
        "Lord",
        "Master",
        "Ruler",
        "King",
        "Queen",
        "Prince",
        "Princess",
        "Champion",
        "Warrior",
        "Knight",
        "Paladin",
    ],
    # AI-themed suffixes
    "ai": [
        "Archon",
        "Network",
        "Core",
        "Matrix",
        "Node",
        "Processor",
        "Engine",
        "System",
        "Intelligence",
        "Mind",
        "Brain",
        "Neural Net",
        "AI",
        "Machine",
        "Bot",
        "Agent",
    ],
    # Web-themed suffixes
    "web": [
        "Elemental",
        "Renderer",
        "Component",
        "Widget",
        "View",
        "Template",
        "Page",
        "Site",
        "App",
        "Interface",
        "Display",
        "Canvas",
        "Frame",
        "Window",
        "Panel",
        "Screen",
    ],
    # Backend-themed suffixes
    "backend": [
        "Warden",
        "Server",
        "Daemon",
        "Service",
        "API",
        "Endpoint",
        "Handler",
        "Controller",
        "Router",
        "Gateway",
        "Proxy",
        "Cache",
        "Database",
        "Store",
        "Repository",
        "Engine",
    ],
    # CLI-themed suffixes
    "cli": [
        "Shade",
        "Shell",
        "Terminal",
        "Console",
        "Prompt",
        "CLI",
        "Command",
        "Script",
        "Executor",
        "Runner",
        "Interpreter",
        "Parser",
        "Processor",
        "Handler",
        "Tool",
    ],
    # Scraping-themed suffixes
    "scraping": [
        "Crawler",
        "Spider",
        "Bot",
        "Scraper",
        "Parser",
        "Extractor",
        "Harvester",
        "Collector",
        "Hunter",
        "Seeker",
        "Tracker",
        "Gatherer",
        "Agent",
        "Drone",
        "Scout",
        "Probe",
    ],
}

# Health state thresholds (days since last commit)
HEALTH_VIBRANT = 14
HEALTH_STABLE = 90
HEALTH_FRAIL = 365
