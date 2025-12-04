"""
Achievement system for Github Heroes.
Tracks and unlocks achievements based on player actions.
"""

from typing import Dict, List, Optional

from github_heroes.core.logging_utils import get_logger
from github_heroes.data.models import Achievement, ItemRarity, Player
from github_heroes.data.repositories import (
    AchievementRepository,
    ItemRepository,
    PlayerStatsRepository,
    RepoWorldRepository,
)

logger = get_logger(__name__)

# Achievement definitions
ACHIEVEMENTS = {
    # Combat & Leveling
    "first_blood": {
        "name": "First Blood",
        "description": "Defeat your first enemy",
        "category": "Combat",
    },
    "level_10": {
        "name": "Level 10 Hero",
        "description": "Reach level 10",
        "category": "Leveling",
    },
    "level_25": {
        "name": "Level 25 Veteran",
        "description": "Reach level 25",
        "category": "Leveling",
    },
    "level_50": {
        "name": "Level 50 Legend",
        "description": "Reach level 50",
        "category": "Leveling",
    },
    "level_100": {
        "name": "Level 100 Master",
        "description": "Reach level 100",
        "category": "Leveling",
    },
    "perfect_victory": {
        "name": "Perfect Victory",
        "description": "Win a battle without taking damage",
        "category": "Combat",
    },
    "boss_slayer": {
        "name": "Boss Slayer",
        "description": "Defeat 10 PR bosses",
        "category": "Combat",
    },
    "elite_hunter": {
        "name": "Elite Hunter",
        "description": "Defeat 50 enemies",
        "category": "Combat",
    },
    "unstoppable": {
        "name": "Unstoppable",
        "description": "Defeat 100 enemies",
        "category": "Combat",
    },
    "giant_killer": {
        "name": "Giant Killer",
        "description": "Defeat an enemy 10+ levels above you",
        "category": "Combat",
    },
    # Exploration & Discovery
    "world_explorer": {
        "name": "World Explorer",
        "description": "Discover 5 repositories",
        "category": "Exploration",
    },
    "globe_trotter": {
        "name": "Globe Trotter",
        "description": "Discover 25 repositories",
        "category": "Exploration",
    },
    "cartographer": {
        "name": "Cartographer",
        "description": "Discover 100 repositories",
        "category": "Exploration",
    },
    "room_explorer": {
        "name": "Dungeon Explorer",
        "description": "Explore 50 dungeons",
        "category": "Exploration",
    },
    "dungeon_master": {
        "name": "Dungeon Master",
        "description": "Explore 500 dungeons",
        "category": "Exploration",
    },
    "zone_conqueror": {
        "name": "Zone Conqueror",
        "description": "Fully explore a repository (all dungeons explored)",
        "category": "Exploration",
    },
    # Quest & Completion
    "quest_novice": {
        "name": "Quest Novice",
        "description": "Complete 5 quests",
        "category": "Quests",
    },
    "quest_master": {
        "name": "Quest Master",
        "description": "Complete 25 quests",
        "category": "Quests",
    },
    "issue_resolver": {
        "name": "Issue Resolver",
        "description": "Complete 10 issue quests",
        "category": "Quests",
    },
    "pr_champion": {
        "name": "PR Champion",
        "description": "Complete 10 PR boss quests",
        "category": "Quests",
    },
    "completionist": {
        "name": "Completionist",
        "description": "Complete all quests in a repository",
        "category": "Quests",
    },
    # Collection & Loot
    "item_collector": {
        "name": "Item Collector",
        "description": "Collect 10 items",
        "category": "Collection",
    },
    "treasure_hunter": {
        "name": "Treasure Hunter",
        "description": "Collect 50 items",
        "category": "Collection",
    },
    "legendary_collector": {
        "name": "Legendary Collector",
        "description": "Collect 100 items",
        "category": "Collection",
    },
    "fully_equipped": {
        "name": "Fully Equipped",
        "description": "Equip items in all 6 slots",
        "category": "Collection",
    },
    "rare_find": {
        "name": "Rare Find",
        "description": "Obtain a rare or better item",
        "category": "Collection",
    },
    "epic_loot": {
        "name": "Epic Loot",
        "description": "Obtain an epic or better item",
        "category": "Collection",
    },
    "legendary_hero": {
        "name": "Legendary Hero",
        "description": "Obtain a legendary item",
        "category": "Collection",
    },
    # Repository-Specific
    "star_gazer": {
        "name": "Star Gazer",
        "description": "Discover a repository with 1000+ stars",
        "category": "Repository",
    },
    "mega_star": {
        "name": "Mega Star",
        "description": "Discover a repository with 10000+ stars",
        "category": "Repository",
    },
    "vibrant_explorer": {
        "name": "Vibrant Explorer",
        "description": "Discover 5 'Vibrant' health repositories",
        "category": "Repository",
    },
    "undead_hunter": {
        "name": "Undead Hunter",
        "description": "Discover 5 'Undead' health repositories",
        "category": "Repository",
    },
    "language_master": {
        "name": "Language Master",
        "description": "Discover repositories in 5 different languages",
        "category": "Repository",
    },
    "ai_specialist": {
        "name": "AI Specialist",
        "description": "Defeat 10 AI-themed enemies",
        "category": "Repository",
    },
    "web_warrior": {
        "name": "Web Warrior",
        "description": "Defeat 10 web-themed enemies",
        "category": "Repository",
    },
    "backend_brawler": {
        "name": "Backend Brawler",
        "description": "Defeat 10 backend-themed enemies",
        "category": "Repository",
    },
    # Special Challenge
    "speed_demon": {
        "name": "Speed Demon",
        "description": "Win a battle in 3 turns or less",
        "category": "Challenge",
    },
    "tank": {
        "name": "Tank",
        "description": "Win a battle with 200+ total HP",
        "category": "Challenge",
    },
    "glass_cannon": {
        "name": "Glass Cannon",
        "description": "Win a battle with 50+ attack",
        "category": "Challenge",
    },
    "lucky_strike": {
        "name": "Lucky Strike",
        "description": "Win 5 battles in a row",
        "category": "Challenge",
    },
    "survivor": {
        "name": "Survivor",
        "description": "Win a battle with 10 HP or less remaining",
        "category": "Challenge",
    },
    "xp_hoarder": {
        "name": "XP Hoarder",
        "description": "Accumulate 10,000 total XP",
        "category": "Milestone",
    },
    "xp_master": {
        "name": "XP Master",
        "description": "Accumulate 100,000 total XP",
        "category": "Milestone",
    },
    # Milestone
    "first_steps": {
        "name": "First Steps",
        "description": "Complete your first quest",
        "category": "Milestone",
    },
    "repository_rookie": {
        "name": "Repository Rookie",
        "description": "Add your first repository",
        "category": "Milestone",
    },
    "inventory_manager": {
        "name": "Inventory Manager",
        "description": "Fill your inventory to capacity",
        "category": "Milestone",
    },
    "stat_booster": {
        "name": "Stat Booster",
        "description": "Reach 50+ in any stat",
        "category": "Milestone",
    },
    "stat_master": {
        "name": "Stat Master",
        "description": "Reach 100+ in any stat",
        "category": "Milestone",
    },
}


def check_achievements(player: Player, context: Optional[Dict] = None) -> List[str]:
    """
    Check and unlock achievements for a player.
    Returns list of newly unlocked achievement IDs.

    Args:
        player: Player to check achievements for
        context: Optional context dict with event-specific data (enemy, quest, etc.)
    """
    newly_unlocked = []
    stats = PlayerStatsRepository.get_or_create(player.id)

    # Level-based achievements
    if player.level >= 10 and not AchievementRepository.has_achievement(
        player.id, "level_10"
    ):
        unlock_achievement(player.id, "level_10")
        newly_unlocked.append("level_10")
    if player.level >= 25 and not AchievementRepository.has_achievement(
        player.id, "level_25"
    ):
        unlock_achievement(player.id, "level_25")
        newly_unlocked.append("level_25")
    if player.level >= 50 and not AchievementRepository.has_achievement(
        player.id, "level_50"
    ):
        unlock_achievement(player.id, "level_50")
        newly_unlocked.append("level_50")
    if player.level >= 100 and not AchievementRepository.has_achievement(
        player.id, "level_100"
    ):
        unlock_achievement(player.id, "level_100")
        newly_unlocked.append("level_100")

    # Combat achievements
    if stats["enemies_defeated"] >= 1 and not AchievementRepository.has_achievement(
        player.id, "first_blood"
    ):
        unlock_achievement(player.id, "first_blood")
        newly_unlocked.append("first_blood")
    if stats["enemies_defeated"] >= 50 and not AchievementRepository.has_achievement(
        player.id, "elite_hunter"
    ):
        unlock_achievement(player.id, "elite_hunter")
        newly_unlocked.append("elite_hunter")
    if stats["enemies_defeated"] >= 100 and not AchievementRepository.has_achievement(
        player.id, "unstoppable"
    ):
        unlock_achievement(player.id, "unstoppable")
        newly_unlocked.append("unstoppable")
    if stats["bosses_defeated"] >= 10 and not AchievementRepository.has_achievement(
        player.id, "boss_slayer"
    ):
        unlock_achievement(player.id, "boss_slayer")
        newly_unlocked.append("boss_slayer")
    if stats["perfect_victories"] >= 1 and not AchievementRepository.has_achievement(
        player.id, "perfect_victory"
    ):
        unlock_achievement(player.id, "perfect_victory")
        newly_unlocked.append("perfect_victory")

    # Exploration achievements
    worlds = RepoWorldRepository.get_all()
    world_count = len(worlds)
    if world_count >= 5 and not AchievementRepository.has_achievement(
        player.id, "world_explorer"
    ):
        unlock_achievement(player.id, "world_explorer")
        newly_unlocked.append("world_explorer")
    if world_count >= 25 and not AchievementRepository.has_achievement(
        player.id, "globe_trotter"
    ):
        unlock_achievement(player.id, "globe_trotter")
        newly_unlocked.append("globe_trotter")
    if world_count >= 100 and not AchievementRepository.has_achievement(
        player.id, "cartographer"
    ):
        unlock_achievement(player.id, "cartographer")
        newly_unlocked.append("cartographer")
    if stats["rooms_explored"] >= 50 and not AchievementRepository.has_achievement(
        player.id, "room_explorer"
    ):
        unlock_achievement(player.id, "room_explorer")
        newly_unlocked.append("room_explorer")
    if stats["rooms_explored"] >= 500 and not AchievementRepository.has_achievement(
        player.id, "dungeon_master"
    ):
        unlock_achievement(player.id, "dungeon_master")
        newly_unlocked.append("dungeon_master")

    # Quest achievements
    if stats["quests_completed"] >= 1 and not AchievementRepository.has_achievement(
        player.id, "first_steps"
    ):
        unlock_achievement(player.id, "first_steps")
        newly_unlocked.append("first_steps")
    if stats["quests_completed"] >= 5 and not AchievementRepository.has_achievement(
        player.id, "quest_novice"
    ):
        unlock_achievement(player.id, "quest_novice")
        newly_unlocked.append("quest_novice")
    if stats["quests_completed"] >= 25 and not AchievementRepository.has_achievement(
        player.id, "quest_master"
    ):
        unlock_achievement(player.id, "quest_master")
        newly_unlocked.append("quest_master")
    if stats["issues_completed"] >= 10 and not AchievementRepository.has_achievement(
        player.id, "issue_resolver"
    ):
        unlock_achievement(player.id, "issue_resolver")
        newly_unlocked.append("issue_resolver")
    if stats["prs_completed"] >= 10 and not AchievementRepository.has_achievement(
        player.id, "pr_champion"
    ):
        unlock_achievement(player.id, "pr_champion")
        newly_unlocked.append("pr_champion")

    # Collection achievements
    item_count = ItemRepository.get_inventory_count(player.id)
    if item_count >= 10 and not AchievementRepository.has_achievement(
        player.id, "item_collector"
    ):
        unlock_achievement(player.id, "item_collector")
        newly_unlocked.append("item_collector")
    if item_count >= 50 and not AchievementRepository.has_achievement(
        player.id, "treasure_hunter"
    ):
        unlock_achievement(player.id, "treasure_hunter")
        newly_unlocked.append("treasure_hunter")
    if item_count >= 100 and not AchievementRepository.has_achievement(
        player.id, "legendary_collector"
    ):
        unlock_achievement(player.id, "legendary_collector")
        newly_unlocked.append("legendary_collector")

    # XP achievements
    if stats["total_xp_earned"] >= 10000 and not AchievementRepository.has_achievement(
        player.id, "xp_hoarder"
    ):
        unlock_achievement(player.id, "xp_hoarder")
        newly_unlocked.append("xp_hoarder")
    if stats["total_xp_earned"] >= 100000 and not AchievementRepository.has_achievement(
        player.id, "xp_master"
    ):
        unlock_achievement(player.id, "xp_master")
        newly_unlocked.append("xp_master")

    # Repository-specific achievements
    vibrant_count = sum(1 for w in worlds if w.health_state == "Vibrant")
    if vibrant_count >= 5 and not AchievementRepository.has_achievement(
        player.id, "vibrant_explorer"
    ):
        unlock_achievement(player.id, "vibrant_explorer")
        newly_unlocked.append("vibrant_explorer")

    undead_count = sum(1 for w in worlds if w.health_state == "Undead")
    if undead_count >= 5 and not AchievementRepository.has_achievement(
        player.id, "undead_hunter"
    ):
        unlock_achievement(player.id, "undead_hunter")
        newly_unlocked.append("undead_hunter")

    star_repos = [w for w in worlds if w.stars >= 1000]
    if star_repos and not AchievementRepository.has_achievement(
        player.id, "star_gazer"
    ):
        unlock_achievement(player.id, "star_gazer")
        newly_unlocked.append("star_gazer")

    mega_star_repos = [w for w in worlds if w.stars >= 10000]
    if mega_star_repos and not AchievementRepository.has_achievement(
        player.id, "mega_star"
    ):
        unlock_achievement(player.id, "mega_star")
        newly_unlocked.append("mega_star")

    # Language diversity
    languages = set(w.primary_language for w in worlds if w.primary_language)
    if len(languages) >= 5 and not AchievementRepository.has_achievement(
        player.id, "language_master"
    ):
        unlock_achievement(player.id, "language_master")
        newly_unlocked.append("language_master")

    # Stat-based achievements (exclude HP since it starts at 100 for all characters)
    # Only check combat stats: attack, defense, speed, luck
    max_stat = max(player.attack, player.defense, player.speed, player.luck)
    if max_stat >= 50 and not AchievementRepository.has_achievement(
        player.id, "stat_booster"
    ):
        unlock_achievement(player.id, "stat_booster")
        newly_unlocked.append("stat_booster")
    if max_stat >= 100 and not AchievementRepository.has_achievement(
        player.id, "stat_master"
    ):
        unlock_achievement(player.id, "stat_master")
        newly_unlocked.append("stat_master")

    # Context-specific achievements (from combat, quests, etc.)
    if context:
        # Giant Killer - enemy 10+ levels above player
        if "enemy" in context and "enemy_level" in context:
            enemy_level = context["enemy_level"]
            if (
                enemy_level >= player.level + 10
                and not AchievementRepository.has_achievement(player.id, "giant_killer")
            ):
                unlock_achievement(player.id, "giant_killer")
                newly_unlocked.append("giant_killer")

        # Perfect Victory - no damage taken
        if "damage_taken" in context and context["damage_taken"] == 0:
            if not AchievementRepository.has_achievement(player.id, "perfect_victory"):
                unlock_achievement(player.id, "perfect_victory")
                newly_unlocked.append("perfect_victory")

        # Speed Demon - 3 turns or less
        if "turns" in context and context["turns"] <= 3:
            if not AchievementRepository.has_achievement(player.id, "speed_demon"):
                unlock_achievement(player.id, "speed_demon")
                newly_unlocked.append("speed_demon")

        # Survivor - won with 10 HP or less
        if "final_hp" in context and context["final_hp"] <= 10:
            if not AchievementRepository.has_achievement(player.id, "survivor"):
                unlock_achievement(player.id, "survivor")
                newly_unlocked.append("survivor")

        # Tank - 200+ HP
        if "total_hp" in context and context["total_hp"] >= 200:
            if not AchievementRepository.has_achievement(player.id, "tank"):
                unlock_achievement(player.id, "tank")
                newly_unlocked.append("tank")

        # Glass Cannon - 50+ attack
        if "total_attack" in context and context["total_attack"] >= 50:
            if not AchievementRepository.has_achievement(player.id, "glass_cannon"):
                unlock_achievement(player.id, "glass_cannon")
                newly_unlocked.append("glass_cannon")

        # Rare/Epic/Legendary items
        if "item_rarity" in context:
            rarity: ItemRarity = context["item_rarity"]
            if (
                rarity.value >= ItemRarity.rare.value
                and not AchievementRepository.has_achievement(player.id, "rare_find")
            ):
                unlock_achievement(player.id, "rare_find")
                newly_unlocked.append("rare_find")
            if (
                rarity.value >= ItemRarity.epic.value
                and not AchievementRepository.has_achievement(player.id, "epic_loot")
            ):
                unlock_achievement(player.id, "epic_loot")
                newly_unlocked.append("epic_loot")
            if (
                rarity.value >= ItemRarity.legendary.value
                and not AchievementRepository.has_achievement(
                    player.id, "legendary_hero"
                )
            ):
                unlock_achievement(player.id, "legendary_hero")
                newly_unlocked.append("legendary_hero")

        # Repository Rookie
        if "repository_added" in context and not AchievementRepository.has_achievement(
            player.id, "repository_rookie"
        ):
            unlock_achievement(player.id, "repository_rookie")
            newly_unlocked.append("repository_rookie")

    return newly_unlocked


def unlock_achievement(player_id: int, achievement_id: str):
    """Unlock an achievement for a player."""
    achievement = Achievement(player_id=player_id, achievement_id=achievement_id)
    AchievementRepository.create(achievement)


def get_player_achievements(player_id: int) -> List[Dict]:
    """Get all unlocked achievements for a player with details."""
    achievements = AchievementRepository.get_by_player(player_id)
    result = []
    for ach in achievements:
        if ach.achievement_id in ACHIEVEMENTS:
            result.append(
                {
                    "id": ach.achievement_id,
                    "name": ACHIEVEMENTS[ach.achievement_id]["name"],
                    "description": ACHIEVEMENTS[ach.achievement_id]["description"],
                    "category": ACHIEVEMENTS[ach.achievement_id]["category"],
                    "unlocked_at": ach.unlocked_at,
                }
            )
    return result


def get_all_achievements_by_category() -> Dict[str, List[Dict]]:
    """Get all achievements organized by category."""
    categories = {}
    for ach_id, ach_data in ACHIEVEMENTS.items():
        category = ach_data["category"]
        if category not in categories:
            categories[category] = []
        categories[category].append(
            {
                "id": ach_id,
                "name": ach_data["name"],
                "description": ach_data["description"],
            }
        )
    return categories
