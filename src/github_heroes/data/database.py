"""
SQLite database connection and schema initialization.
"""

import sqlite3
from pathlib import Path
from typing import Optional

from github_heroes.core.config import DB_PATH
from github_heroes.core.logging_utils import get_logger

logger = get_logger(__name__)


class Database:
    """
    Database connection and management.
    """

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or DB_PATH
        self.conn: Optional[sqlite3.Connection] = None
        self._initialize()

    def _initialize(self):
        """Initialize database connection and create schema."""
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._create_schema()
        logger.info(f"Database initialized at {self.db_path}")

    def _create_schema(self):
        """Create all database tables."""
        cursor = self.conn.cursor()

        # Settings table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        """)

        # Players table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS players (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                level INTEGER NOT NULL DEFAULT 1,
                xp INTEGER NOT NULL DEFAULT 0,
                hp INTEGER NOT NULL DEFAULT 100,
                attack INTEGER NOT NULL DEFAULT 10,
                defense INTEGER NOT NULL DEFAULT 5,
                speed INTEGER NOT NULL DEFAULT 8,
                luck INTEGER NOT NULL DEFAULT 5,
                player_class TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)

        # Repo worlds table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS repo_worlds (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                owner TEXT NOT NULL,
                repo TEXT NOT NULL,
                full_name TEXT NOT NULL UNIQUE,
                primary_language TEXT,
                stars INTEGER DEFAULT 0,
                forks INTEGER DEFAULT 0,
                watchers INTEGER DEFAULT 0,
                activity_score INTEGER DEFAULT 0,
                health_state TEXT,
                main_enemy_id INTEGER,
                readme_features_json TEXT,
                structure_features_json TEXT,
                discovered_at TEXT NOT NULL,
                last_scraped_at TEXT
            )
        """)

        # Enemies table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS enemies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                world_id INTEGER,
                name TEXT NOT NULL,
                level INTEGER NOT NULL,
                hp INTEGER NOT NULL,
                attack INTEGER NOT NULL,
                defense INTEGER NOT NULL,
                speed INTEGER NOT NULL,
                tags_json TEXT,
                is_boss INTEGER NOT NULL DEFAULT 0,
                FOREIGN KEY (world_id) REFERENCES repo_worlds(id)
            )
        """)

        # Dungeon rooms table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS dungeon_rooms (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                world_id INTEGER NOT NULL,
                zone_name TEXT NOT NULL,
                file_path TEXT NOT NULL,
                danger_level INTEGER NOT NULL DEFAULT 1,
                loot_quality INTEGER NOT NULL DEFAULT 1,
                visited INTEGER NOT NULL DEFAULT 0,
                FOREIGN KEY (world_id) REFERENCES repo_worlds(id)
            )
        """)

        # Quests table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS quests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                world_id INTEGER NOT NULL,
                source_type TEXT NOT NULL,
                source_number INTEGER NOT NULL,
                title TEXT NOT NULL,
                difficulty INTEGER NOT NULL DEFAULT 1,
                status TEXT NOT NULL DEFAULT 'new',
                FOREIGN KEY (world_id) REFERENCES repo_worlds(id)
            )
        """)

        # Items table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                rarity TEXT NOT NULL,
                stat_bonuses_json TEXT NOT NULL,
                description TEXT
            )
        """)

        # Player inventory table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS player_inventory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                player_id INTEGER NOT NULL,
                item_id INTEGER NOT NULL,
                quantity INTEGER NOT NULL DEFAULT 1,
                equipped INTEGER NOT NULL DEFAULT 0,
                FOREIGN KEY (player_id) REFERENCES players(id),
                FOREIGN KEY (item_id) REFERENCES items(id),
                UNIQUE(player_id, item_id)
            )
        """)

        # Add equipped column if it doesn't exist (migration)
        try:
            cursor.execute(
                "ALTER TABLE player_inventory ADD COLUMN equipped INTEGER NOT NULL DEFAULT 0"
            )
            self.conn.commit()
        except sqlite3.OperationalError:
            pass  # Column already exists

        # Add equipment_type column to items table if it doesn't exist (migration)
        try:
            cursor.execute("ALTER TABLE items ADD COLUMN equipment_type TEXT")
            self.conn.commit()
        except sqlite3.OperationalError:
            pass  # Column already exists

        # Add creature_image_id column to enemies table if it doesn't exist (migration)
        try:
            cursor.execute("ALTER TABLE enemies ADD COLUMN creature_image_id INTEGER")
            self.conn.commit()
        except sqlite3.OperationalError:
            pass  # Column already exists

        # Add player_image_id column to players table if it doesn't exist (migration)
        try:
            cursor.execute("ALTER TABLE players ADD COLUMN player_image_id INTEGER")
            self.conn.commit()
        except sqlite3.OperationalError:
            pass  # Column already exists

        # Migrate github_handle to player_class if needed
        try:
            cursor.execute("ALTER TABLE players ADD COLUMN player_class TEXT")
            # Copy github_handle to player_class for existing records
            cursor.execute(
                "UPDATE players SET player_class = github_handle WHERE player_class IS NULL AND github_handle IS NOT NULL"
            )
            self.conn.commit()
        except sqlite3.OperationalError:
            pass  # Column already exists

        # Achievements table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS achievements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                player_id INTEGER NOT NULL,
                achievement_id TEXT NOT NULL,
                unlocked_at TEXT NOT NULL,
                FOREIGN KEY (player_id) REFERENCES players(id),
                UNIQUE(player_id, achievement_id)
            )
        """)

        # Player stats tracking table (for achievement calculations)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS player_stats (
                player_id INTEGER PRIMARY KEY,
                enemies_defeated INTEGER DEFAULT 0,
                bosses_defeated INTEGER DEFAULT 0,
                quests_completed INTEGER DEFAULT 0,
                issues_completed INTEGER DEFAULT 0,
                prs_completed INTEGER DEFAULT 0,
                rooms_explored INTEGER DEFAULT 0,
                items_collected INTEGER DEFAULT 0,
                total_xp_earned INTEGER DEFAULT 0,
                perfect_victories INTEGER DEFAULT 0,
                FOREIGN KEY (player_id) REFERENCES players(id)
            )
        """)

        # Create indices
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_repo_worlds_full_name ON repo_worlds(full_name)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_enemies_world_id ON enemies(world_id)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_dungeon_rooms_world_id ON dungeon_rooms(world_id)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_quests_world_id ON quests(world_id)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_player_inventory_player_id ON player_inventory(player_id)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_achievements_player_id ON achievements(player_id)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_achievements_achievement_id ON achievements(achievement_id)"
        )

        self.conn.commit()
        logger.info("Database schema created/verified")

    def get_connection(self) -> sqlite3.Connection:
        """Get the database connection."""
        if self.conn is None:
            self._initialize()
        return self.conn

    def close(self):
        """Close the database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None
            logger.info("Database connection closed")

    def execute(self, query: str, params: tuple = ()):
        """Execute a query and return cursor."""
        cursor = self.conn.cursor()
        cursor.execute(query, params)
        return cursor

    def commit(self):
        """Commit the current transaction."""
        self.conn.commit()

    def get_setting(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Get a setting value."""
        cursor = self.execute("SELECT value FROM settings WHERE key = ?", (key,))
        row = cursor.fetchone()
        return row[0] if row else default

    def set_setting(self, key: str, value: str):
        """Set a setting value."""
        self.execute(
            "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value)
        )
        self.commit()


# Global database instance
_db_instance: Optional[Database] = None


def get_db() -> Database:
    """Get the global database instance."""
    global _db_instance
    if _db_instance is None:
        _db_instance = Database()
    return _db_instance
