"""
Data access layer for database operations.
"""

from datetime import datetime
from typing import Dict, List, Optional

from github_heroes.core.logging_utils import get_logger
from github_heroes.data.database import get_db
from github_heroes.data.models import (
    Achievement,
    DungeonRoom,
    Enemy,
    Item,
    ItemRarity,
    Player,
    Quest,
    RepoWorld,
)

logger = get_logger(__name__)


class PlayerRepository:
    """Repository for player operations."""

    @staticmethod
    def create(player: Player) -> Player:
        """Create a new player."""
        db = get_db()
        now = datetime.now().isoformat()
        cursor = db.execute(
            """
            INSERT INTO players (name, level, xp, hp, attack, defense, speed, luck, player_class, player_image_id, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                player.name,
                player.level,
                player.xp,
                player.hp,
                player.attack,
                player.defense,
                player.speed,
                player.luck,
                player.player_class,
                player.player_image_id,
                now,
                now,
            ),
        )
        db.commit()
        player.id = cursor.lastrowid
        player.created_at = now
        player.updated_at = now
        logger.info(f"Created player: {player.name} (ID: {player.id})")
        return player

    @staticmethod
    def get_by_id(player_id: int) -> Optional[Player]:
        """Get player by ID."""
        db = get_db()
        cursor = db.execute("SELECT * FROM players WHERE id = ?", (player_id,))
        row = cursor.fetchone()
        if row:
            try:
                player_image_id = row["player_image_id"]
            except (KeyError, IndexError):
                player_image_id = None
            try:
                player_class = row["player_class"]
            except (KeyError, IndexError):
                player_class = None
            return Player(
                id=row["id"],
                name=row["name"],
                level=row["level"],
                xp=row["xp"],
                hp=row["hp"],
                attack=row["attack"],
                defense=row["defense"],
                speed=row["speed"],
                luck=row["luck"],
                player_class=player_class,
                player_image_id=player_image_id,
                created_at=row["created_at"],
                updated_at=row["updated_at"],
            )
        return None

    @staticmethod
    def update(player: Player) -> Player:
        """Update player."""
        db = get_db()
        player.updated_at = datetime.now().isoformat()
        db.execute(
            """
            UPDATE players SET name=?, level=?, xp=?, hp=?, attack=?, defense=?, speed=?, luck=?, player_class=?, player_image_id=?, updated_at=?
            WHERE id=?
        """,
            (
                player.name,
                player.level,
                player.xp,
                player.hp,
                player.attack,
                player.defense,
                player.speed,
                player.luck,
                player.player_class,
                player.player_image_id,
                player.updated_at,
                player.id,
            ),
        )
        db.commit()
        return player

    @staticmethod
    def get_all() -> List[Player]:
        """Get all players."""
        db = get_db()
        cursor = db.execute("SELECT * FROM players ORDER BY created_at DESC")
        result = []
        for row in cursor.fetchall():
            try:
                player_image_id = row["player_image_id"]
            except (KeyError, IndexError):
                player_image_id = None
            try:
                player_class = row["player_class"]
            except (KeyError, IndexError):
                player_class = None
            result.append(
                Player(
                    id=row["id"],
                    name=row["name"],
                    level=row["level"],
                    xp=row["xp"],
                    hp=row["hp"],
                    attack=row["attack"],
                    defense=row["defense"],
                    speed=row["speed"],
                    luck=row["luck"],
                    player_class=player_class,
                    player_image_id=player_image_id,
                    created_at=row["created_at"],
                    updated_at=row["updated_at"],
                )
            )
        return result


class RepoWorldRepository:
    """Repository for repo world operations."""

    @staticmethod
    def create(world: RepoWorld) -> RepoWorld:
        """Create a new repo world."""
        db = get_db()
        now = datetime.now().isoformat()
        cursor = db.execute(
            """
            INSERT INTO repo_worlds (owner, repo, full_name, primary_language, stars, forks, watchers,
                activity_score, health_state, main_enemy_id, readme_features_json, structure_features_json,
                discovered_at, last_scraped_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                world.owner,
                world.repo,
                world.full_name,
                world.primary_language,
                world.stars,
                world.forks,
                world.watchers,
                world.activity_score,
                world.health_state,
                world.main_enemy_id,
                world.readme_features_json,
                world.structure_features_json,
                now,
                world.last_scraped_at or now,
            ),
        )
        db.commit()
        world.id = cursor.lastrowid
        world.discovered_at = now
        logger.info(f"Created repo world: {world.full_name} (ID: {world.id})")
        return world

    @staticmethod
    def get_by_id(world_id: int) -> Optional[RepoWorld]:
        """Get repo world by ID."""
        db = get_db()
        cursor = db.execute("SELECT * FROM repo_worlds WHERE id = ?", (world_id,))
        row = cursor.fetchone()
        if row:
            return RepoWorld(
                id=row["id"],
                owner=row["owner"],
                repo=row["repo"],
                full_name=row["full_name"],
                primary_language=row["primary_language"],
                stars=row["stars"],
                forks=row["forks"],
                watchers=row["watchers"],
                activity_score=row["activity_score"],
                health_state=row["health_state"],
                main_enemy_id=row["main_enemy_id"],
                readme_features_json=row["readme_features_json"],
                structure_features_json=row["structure_features_json"],
                discovered_at=row["discovered_at"],
                last_scraped_at=row["last_scraped_at"],
            )
        return None

    @staticmethod
    def get_by_full_name(full_name: str) -> Optional[RepoWorld]:
        """Get repo world by full name."""
        db = get_db()
        cursor = db.execute(
            "SELECT * FROM repo_worlds WHERE full_name = ?", (full_name,)
        )
        row = cursor.fetchone()
        if row:
            return RepoWorld(
                id=row["id"],
                owner=row["owner"],
                repo=row["repo"],
                full_name=row["full_name"],
                primary_language=row["primary_language"],
                stars=row["stars"],
                forks=row["forks"],
                watchers=row["watchers"],
                activity_score=row["activity_score"],
                health_state=row["health_state"],
                main_enemy_id=row["main_enemy_id"],
                readme_features_json=row["readme_features_json"],
                structure_features_json=row["structure_features_json"],
                discovered_at=row["discovered_at"],
                last_scraped_at=row["last_scraped_at"],
            )
        return None

    @staticmethod
    def update(world: RepoWorld) -> RepoWorld:
        """Update repo world."""
        db = get_db()
        world.last_scraped_at = datetime.now().isoformat()
        db.execute(
            """
            UPDATE repo_worlds SET owner=?, repo=?, full_name=?, primary_language=?, stars=?, forks=?,
                watchers=?, activity_score=?, health_state=?, main_enemy_id=?, readme_features_json=?,
                structure_features_json=?, last_scraped_at=?
            WHERE id=?
        """,
            (
                world.owner,
                world.repo,
                world.full_name,
                world.primary_language,
                world.stars,
                world.forks,
                world.watchers,
                world.activity_score,
                world.health_state,
                world.main_enemy_id,
                world.readme_features_json,
                world.structure_features_json,
                world.last_scraped_at,
                world.id,
            ),
        )
        db.commit()
        return world

    @staticmethod
    def remove_by_id(world_id: int) -> bool:
        """Remove repo world."""
        db = get_db()
        cursor = db.execute("SELECT * FROM repo_worlds WHERE id = ?", (world_id,))
        row = cursor.fetchone()
        if row:
            # Remove completely
            db.execute(
                """
                DELETE FROM repo_worlds
                WHERE id = ?
            """,
                (world_id,),
            )
            db.commit()
            return True
        return False

    @staticmethod
    def remove_by_full_name(full_name: str) -> bool:
        """Remove repo world."""
        db = get_db()
        cursor = db.execute(
            "SELECT * FROM repo_worlds WHERE full_name = ?", (full_name,)
        )
        row = cursor.fetchone()
        if row:
            # Remove completely
            db.execute(
                """
                DELETE FROM repo_worlds
                WHERE full_name = ?
            """,
                (full_name,),
            )
            db.commit()
            return True
        return False

    @staticmethod
    def get_all() -> List[RepoWorld]:
        """Get all repo worlds."""
        db = get_db()
        cursor = db.execute("SELECT * FROM repo_worlds ORDER BY discovered_at DESC")
        return [
            RepoWorld(
                id=row["id"],
                owner=row["owner"],
                repo=row["repo"],
                full_name=row["full_name"],
                primary_language=row["primary_language"],
                stars=row["stars"],
                forks=row["forks"],
                watchers=row["watchers"],
                activity_score=row["activity_score"],
                health_state=row["health_state"],
                main_enemy_id=row["main_enemy_id"],
                readme_features_json=row["readme_features_json"],
                structure_features_json=row["structure_features_json"],
                discovered_at=row["discovered_at"],
                last_scraped_at=row["last_scraped_at"],
            )
            for row in cursor.fetchall()
        ]


class EnemyRepository:
    """Repository for enemy operations."""

    @staticmethod
    def create(enemy: Enemy) -> Enemy:
        """Create a new enemy."""
        db = get_db()
        cursor = db.execute(
            """
            INSERT INTO enemies (world_id, name, level, hp, attack, defense, speed, tags_json, is_boss, creature_image_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                enemy.world_id,
                enemy.name,
                enemy.level,
                enemy.hp,
                enemy.attack,
                enemy.defense,
                enemy.speed,
                enemy.tags_json,
                1 if enemy.is_boss else 0,
                enemy.creature_image_id,
            ),
        )
        db.commit()
        enemy.id = cursor.lastrowid
        return enemy

    @staticmethod
    def get_by_id(enemy_id: int) -> Optional[Enemy]:
        """Get enemy by ID."""
        db = get_db()
        cursor = db.execute("SELECT * FROM enemies WHERE id = ?", (enemy_id,))
        row = cursor.fetchone()
        if row:
            try:
                creature_image_id = row["creature_image_id"]
            except (KeyError, IndexError):
                creature_image_id = None
            return Enemy(
                id=row["id"],
                world_id=row["world_id"],
                name=row["name"],
                level=row["level"],
                hp=row["hp"],
                attack=row["attack"],
                defense=row["defense"],
                speed=row["speed"],
                tags_json=row["tags_json"],
                is_boss=bool(row["is_boss"]),
                creature_image_id=creature_image_id,
            )
        return None

    @staticmethod
    def get_by_world_id(world_id: int) -> List[Enemy]:
        """Get all enemies for a world."""
        db = get_db()
        cursor = db.execute("SELECT * FROM enemies WHERE world_id = ?", (world_id,))
        result = []
        for row in cursor.fetchall():
            try:
                creature_image_id = row["creature_image_id"]
            except (KeyError, IndexError):
                creature_image_id = None
            result.append(
                Enemy(
                    id=row["id"],
                    world_id=row["world_id"],
                    name=row["name"],
                    level=row["level"],
                    hp=row["hp"],
                    attack=row["attack"],
                    defense=row["defense"],
                    speed=row["speed"],
                    tags_json=row["tags_json"],
                    is_boss=bool(row["is_boss"]),
                    creature_image_id=creature_image_id,
                )
            )
        return result


class DungeonRoomRepository:
    """Repository for dungeon room operations."""

    @staticmethod
    def create(room: DungeonRoom) -> DungeonRoom:
        """Create a new dungeon room."""
        db = get_db()
        cursor = db.execute(
            """
            INSERT INTO dungeon_rooms (world_id, zone_name, file_path, danger_level, loot_quality, visited)
            VALUES (?, ?, ?, ?, ?, ?)
        """,
            (
                room.world_id,
                room.zone_name,
                room.file_path,
                room.danger_level,
                room.loot_quality,
                1 if room.visited else 0,
            ),
        )
        db.commit()
        room.id = cursor.lastrowid
        return room

    @staticmethod
    def get_by_id(room_id: int) -> Optional[DungeonRoom]:
        """Get room by ID."""
        db = get_db()
        cursor = db.execute("SELECT * FROM dungeon_rooms WHERE id = ?", (room_id,))
        row = cursor.fetchone()
        if row:
            return DungeonRoom(
                id=row["id"],
                world_id=row["world_id"],
                zone_name=row["zone_name"],
                file_path=row["file_path"],
                danger_level=row["danger_level"],
                loot_quality=row["loot_quality"],
                visited=bool(row["visited"]),
            )
        return None

    @staticmethod
    def get_by_world_id(world_id: int) -> List[DungeonRoom]:
        """Get all rooms for a world."""
        db = get_db()
        cursor = db.execute(
            "SELECT * FROM dungeon_rooms WHERE world_id = ?", (world_id,)
        )
        return [
            DungeonRoom(
                id=row["id"],
                world_id=row["world_id"],
                zone_name=row["zone_name"],
                file_path=row["file_path"],
                danger_level=row["danger_level"],
                loot_quality=row["loot_quality"],
                visited=bool(row["visited"]),
            )
            for row in cursor.fetchall()
        ]

    @staticmethod
    def update(room: DungeonRoom) -> DungeonRoom:
        """Update dungeon room."""
        db = get_db()
        db.execute(
            """
            UPDATE dungeon_rooms SET visited=?
            WHERE id=?
        """,
            (1 if room.visited else 0, room.id),
        )
        db.commit()
        return room


class QuestRepository:
    """Repository for quest operations."""

    @staticmethod
    def create(quest: Quest) -> Quest:
        """Create a new quest."""
        db = get_db()
        cursor = db.execute(
            """
            INSERT INTO quests (world_id, source_type, source_number, title, difficulty, status)
            VALUES (?, ?, ?, ?, ?, ?)
        """,
            (
                quest.world_id,
                quest.source_type,
                quest.source_number,
                quest.title,
                quest.difficulty,
                quest.status,
            ),
        )
        db.commit()
        quest.id = cursor.lastrowid
        return quest

    @staticmethod
    def get_by_id(quest_id: int) -> Optional[Quest]:
        """Get quest by ID."""
        db = get_db()
        cursor = db.execute("SELECT * FROM quests WHERE id = ?", (quest_id,))
        row = cursor.fetchone()
        if row:
            return Quest(
                id=row["id"],
                world_id=row["world_id"],
                source_type=row["source_type"],
                source_number=row["source_number"],
                title=row["title"],
                difficulty=row["difficulty"],
                status=row["status"],
            )
        return None

    @staticmethod
    def get_by_world_id(world_id: int) -> List[Quest]:
        """Get all quests for a world."""
        db = get_db()
        cursor = db.execute("SELECT * FROM quests WHERE world_id = ?", (world_id,))
        return [
            Quest(
                id=row["id"],
                world_id=row["world_id"],
                source_type=row["source_type"],
                source_number=row["source_number"],
                title=row["title"],
                difficulty=row["difficulty"],
                status=row["status"],
            )
            for row in cursor.fetchall()
        ]

    @staticmethod
    def update(quest: Quest) -> Quest:
        """Update quest."""
        db = get_db()
        db.execute(
            """
            UPDATE quests SET status=?
            WHERE id=?
        """,
            (quest.status, quest.id),
        )
        db.commit()
        return quest


class ItemRepository:
    """Repository for item operations."""

    @staticmethod
    def create(item: Item) -> Item:
        """Create a new item."""
        db = get_db()
        cursor = db.execute(
            """
            INSERT INTO items (name, rarity, stat_bonuses_json, description, equipment_type)
            VALUES (?, ?, ?, ?, ?)
        """,
            (
                item.name,
                item.rarity.name,
                item.stat_bonuses_json,
                item.description,
                item.equipment_type,
            ),
        )
        db.commit()
        item.id = cursor.lastrowid
        return item

    @staticmethod
    def get_by_id(item_id: int) -> Optional[Item]:
        """Get item by ID."""
        db = get_db()
        cursor = db.execute("SELECT * FROM items WHERE id = ?", (item_id,))
        row = cursor.fetchone()
        if row:
            # Handle equipment_type - may not exist for old items
            try:
                equipment_type = row["equipment_type"]
            except (KeyError, IndexError):
                equipment_type = None
            return Item(
                id=row["id"],
                name=row["name"],
                rarity=ItemRarity[row["rarity"]],
                stat_bonuses_json=row["stat_bonuses_json"],
                description=row["description"],
                equipment_type=equipment_type,
            )
        return None

    @staticmethod
    def add_to_inventory(player_id: int, item_id: int, quantity: int = 1):
        """Add item to player inventory."""
        db = get_db()
        db.execute(
            """
            INSERT INTO player_inventory (player_id, item_id, quantity, equipped)
            VALUES (?, ?, ?, 0)
            ON CONFLICT(player_id, item_id) DO UPDATE SET quantity = quantity + ?
        """,
            (player_id, item_id, quantity, quantity),
        )
        db.commit()

    @staticmethod
    def get_player_inventory(player_id: int) -> List[tuple[Item, int, bool]]:
        """Get player inventory (item, quantity, equipped)."""
        db = get_db()
        cursor = db.execute(
            """
            SELECT i.*, pi.quantity, pi.equipped
            FROM items i
            JOIN player_inventory pi ON i.id = pi.item_id
            WHERE pi.player_id = ?
        """,
            (player_id,),
        )
        result = []
        for row in cursor.fetchall():
            # Handle equipment_type - may not exist for old items
            try:
                equipment_type = row["equipment_type"]
            except (KeyError, IndexError):
                equipment_type = None
            result.append(
                (
                    Item(
                        id=row["id"],
                        name=row["name"],
                        rarity=ItemRarity[row["rarity"]],
                        stat_bonuses_json=row["stat_bonuses_json"],
                        description=row["description"],
                        equipment_type=equipment_type,
                    ),
                    row["quantity"],
                    bool(row["equipped"]),
                )
            )
        return result

    @staticmethod
    def equip_item(player_id: int, item_id: int):
        """Equip an item. Unequips any existing item of the same equipment type."""
        db = get_db()

        # Get the item to find its equipment type
        item = ItemRepository.get_by_id(item_id)
        if not item or not item.equipment_type:
            # If item has no equipment type, just equip it (backward compatibility)
            db.execute(
                """
                UPDATE player_inventory SET equipped = 1
                WHERE player_id = ? AND item_id = ?
            """,
                (player_id, item_id),
            )
            db.commit()
            return

        # First, unequip any existing item of the same equipment type (excluding the item we're equipping)
        db.execute(
            """
            UPDATE player_inventory SET equipped = 0
            WHERE player_id = ? AND item_id != ? AND item_id IN (
                SELECT pi.item_id
                FROM player_inventory pi
                JOIN items i ON pi.item_id = i.id
                WHERE pi.player_id = ? AND pi.equipped = 1 AND i.equipment_type = ?
            )
        """,
            (player_id, item_id, player_id, item.equipment_type),
        )

        # Then equip the new item
        db.execute(
            """
            UPDATE player_inventory SET equipped = 1
            WHERE player_id = ? AND item_id = ?
        """,
            (player_id, item_id),
        )
        db.commit()

    @staticmethod
    def unequip_item(player_id: int, item_id: int):
        """Unequip an item."""
        db = get_db()
        db.execute(
            """
            UPDATE player_inventory SET equipped = 0
            WHERE player_id = ? AND item_id = ?
        """,
            (player_id, item_id),
        )
        db.commit()

    @staticmethod
    def remove_from_inventory(player_id: int, item_id: int, quantity: int = 1):
        """Remove item from inventory (for selling/recycling)."""
        db = get_db()
        # Get current quantity
        cursor = db.execute(
            """
            SELECT quantity FROM player_inventory
            WHERE player_id = ? AND item_id = ?
        """,
            (player_id, item_id),
        )
        row = cursor.fetchone()

        if row:
            current_quantity = row["quantity"]
            if current_quantity <= quantity:
                # Remove completely
                db.execute(
                    """
                    DELETE FROM player_inventory
                    WHERE player_id = ? AND item_id = ?
                """,
                    (player_id, item_id),
                )
            else:
                # Reduce quantity
                db.execute(
                    """
                    UPDATE player_inventory SET quantity = quantity - ?
                    WHERE player_id = ? AND item_id = ?
                """,
                    (quantity, player_id, item_id),
                )
            db.commit()
            return True
        return False

    @staticmethod
    def get_inventory_count(player_id: int) -> int:
        """Get number of unique items in inventory (for space checking)."""
        db = get_db()
        cursor = db.execute(
            """
            SELECT COUNT(*) as count FROM player_inventory
            WHERE player_id = ?
        """,
            (player_id,),
        )
        row = cursor.fetchone()
        return row["count"] if row else 0


class AchievementRepository:
    """Repository for achievement operations."""

    @staticmethod
    def create(achievement: Achievement) -> Achievement:
        """Create a new achievement unlock."""
        db = get_db()
        now = datetime.now().isoformat()
        cursor = db.execute(
            """
            INSERT OR IGNORE INTO achievements (player_id, achievement_id, unlocked_at)
            VALUES (?, ?, ?)
        """,
            (achievement.player_id, achievement.achievement_id, now),
        )
        db.commit()
        if cursor.lastrowid:
            achievement.id = cursor.lastrowid
            achievement.unlocked_at = now
            logger.info(
                f"Unlocked achievement: {achievement.achievement_id} for player {achievement.player_id}"
            )
        return achievement

    @staticmethod
    def get_by_player(player_id: int) -> List[Achievement]:
        """Get all achievements for a player."""
        db = get_db()
        cursor = db.execute(
            """
            SELECT * FROM achievements WHERE player_id = ? ORDER BY unlocked_at DESC
        """,
            (player_id,),
        )
        result = []
        for row in cursor.fetchall():
            result.append(
                Achievement(
                    id=row["id"],
                    player_id=row["player_id"],
                    achievement_id=row["achievement_id"],
                    unlocked_at=row["unlocked_at"],
                )
            )
        return result

    @staticmethod
    def has_achievement(player_id: int, achievement_id: str) -> bool:
        """Check if player has unlocked a specific achievement."""
        db = get_db()
        cursor = db.execute(
            """
            SELECT COUNT(*) as count FROM achievements
            WHERE player_id = ? AND achievement_id = ?
        """,
            (player_id, achievement_id),
        )
        row = cursor.fetchone()
        return (row["count"] if row else 0) > 0


class PlayerStatsRepository:
    """Repository for tracking player statistics for achievements."""

    @staticmethod
    def get_or_create(player_id: int) -> Dict:
        """Get player stats or create if doesn't exist."""
        db = get_db()
        cursor = db.execute(
            "SELECT * FROM player_stats WHERE player_id = ?", (player_id,)
        )
        row = cursor.fetchone()
        if row:
            return {
                "player_id": row["player_id"],
                "enemies_defeated": row["enemies_defeated"],
                "bosses_defeated": row["bosses_defeated"],
                "quests_completed": row["quests_completed"],
                "issues_completed": row["issues_completed"],
                "prs_completed": row["prs_completed"],
                "rooms_explored": row["rooms_explored"],
                "items_collected": row["items_collected"],
                "total_xp_earned": row["total_xp_earned"],
                "perfect_victories": row["perfect_victories"],
            }
        # Create new stats
        db.execute(
            """
            INSERT INTO player_stats (player_id) VALUES (?)
        """,
            (player_id,),
        )
        db.commit()
        return {
            "player_id": player_id,
            "enemies_defeated": 0,
            "bosses_defeated": 0,
            "quests_completed": 0,
            "issues_completed": 0,
            "prs_completed": 0,
            "rooms_explored": 0,
            "items_collected": 0,
            "total_xp_earned": 0,
            "perfect_victories": 0,
        }

    @staticmethod
    def increment_stat(player_id: int, stat_name: str, amount: int = 1):
        """Increment a player stat."""
        db = get_db()
        # Ensure stats exist
        PlayerStatsRepository.get_or_create(player_id)
        db.execute(
            f"""
            UPDATE player_stats SET {stat_name} = {stat_name} + ?
            WHERE player_id = ?
        """,
            (amount, player_id),
        )
        db.commit()

    @staticmethod
    def set_stat(player_id: int, stat_name: str, value: int):
        """Set a player stat to a specific value."""
        db = get_db()
        # Ensure stats exist
        PlayerStatsRepository.get_or_create(player_id)
        db.execute(
            f"""
            UPDATE player_stats SET {stat_name} = ?
            WHERE player_id = ?
        """,
            (value, player_id),
        )
        db.commit()
