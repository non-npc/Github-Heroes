"""
Game rules, combat system, loot generation, XP, and leveling.
"""

import random
from typing import Dict, Optional, Tuple

from github_heroes.core.logging_utils import get_logger
from github_heroes.data.models import (
    Enemy,
    Item,
    ItemRarity,
    ItemTypes,
    Player,
    Stats,
    itemTypeToEquipment,
)
from github_heroes.data.repositories import (
    ItemRepository,
    PlayerRepository,
    PlayerStatsRepository,
)

logger = get_logger(__name__)


def bonus_as_string(bonuses: dict[str, str]) -> str:
    return ", ".join(sorted([f"{k}: +{v}" for k, v in bonuses.items()]))


def calculate_inventory_space(level: int) -> int:
    """
    Calculate inventory space based on level.
    Base: 10 slots, +10 every 10 levels.
    Level 1-9: 10 slots
    Level 10-19: 20 slots
    Level 20-29: 30 slots
    etc.
    """
    base_slots = 10
    additional_slots = (level // 10) * 10
    return base_slots + additional_slots


def calculate_damage(attacker_attack: int, defender_defense: int) -> int:
    """
    Calculate damage dealt.
    """
    base_damage = max(1, attacker_attack - (defender_defense // 2))
    variance = random.randint(-2, 2)
    damage = max(1, base_damage + variance)
    return damage


def combat_turn(
    player: Player, enemy: Enemy, action: str
) -> Tuple[str, bool, Optional[str]]:
    """
    Execute a combat turn.

    Returns: (message, combat_continues, result)
    - message: Description of what happened
    - combat_continues: Whether combat should continue
    - result: "victory", "defeat", or None
    """
    messages = []
    result = None

    if action == "attack":
        # Player attacks
        damage = calculate_damage(player.attack, enemy.defense)
        enemy.hp -= damage
        messages.append(f"You attack {enemy.name} for {damage} damage!")

        if enemy.hp <= 0:
            messages.append(f"You defeated {enemy.name}!")
            result = "victory"
            return ("\n".join(messages), False, result)

        # Enemy attacks back
        damage = calculate_damage(enemy.attack, player.defense)
        player.hp -= damage
        messages.append(f"{enemy.name} attacks you for {damage} damage!")

        if player.hp <= 0:
            messages.append("You have been defeated!")
            result = "defeat"
            return ("\n".join(messages), False, result)

    elif action == "defend":
        # Player defends (reduces incoming damage)
        damage = calculate_damage(enemy.attack, player.defense * 2)
        player.hp -= damage
        messages.append(
            f"You defend! {enemy.name} attacks you for {damage} damage (reduced)."
        )

        if player.hp <= 0:
            messages.append("You have been defeated!")
            result = "defeat"
            return ("\n".join(messages), False, result)

    elif action == "flee":
        messages.append("You attempt to flee...")
        # 70% chance to flee successfully
        if random.random() < 0.7:
            messages.append("You successfully fled from battle!")
            result = "fled"
            return ("\n".join(messages), False, result)
        else:
            messages.append("You couldn't escape! The enemy attacks!")
            damage = calculate_damage(enemy.attack, player.defense)
            player.hp -= damage
            messages.append(f"{enemy.name} attacks you for {damage} damage!")

            if player.hp <= 0:
                messages.append("You have been defeated!")
                result = "defeat"
                return ("\n".join(messages), False, result)

    return ("\n".join(messages), True, result)


def calculate_xp_reward(enemy: Enemy) -> int:
    """
    Calculate XP reward for defeating an enemy.
    """
    base_xp = enemy.level * 10
    if enemy.is_boss:
        base_xp *= 3
    return base_xp


def award_xp(player: Player, xp: int) -> bool:
    """
    Award XP to player and check for level up.
    Returns True if player leveled up.
    """
    player.xp += xp
    leveled_up = False

    # Check for level up
    xp_needed = player.level * 100
    while player.xp >= xp_needed:
        player.xp -= xp_needed
        player.level += 1
        leveled_up = True

        # Increase stats on level up
        player.hp += 10
        player.attack += 2
        player.defense += 1
        player.speed += 1
        player.luck += 1

        xp_needed = player.level * 100

    if leveled_up:
        PlayerRepository.update(player)
        logger.info(f"Player {player.name} leveled up to level {player.level}")

    return leveled_up


def generate_loot(enemy: Enemy, loot_quality: int = 1) -> Optional[Item]:
    """
    Generate a loot item based on enemy and loot quality.
    """
    # Determine rarity based on loot quality and enemy level
    rarity_roll = random.random()

    if loot_quality >= 6 or (enemy.is_boss and rarity_roll < 0.3):
        rarity = ItemRarity.legendary
    elif loot_quality >= 4 or (enemy.is_boss and rarity_roll < 0.5):
        rarity = ItemRarity.epic
    elif loot_quality >= 3 or rarity_roll < 0.3:
        rarity = ItemRarity.rare
    elif loot_quality >= 2 or rarity_roll < 0.5:
        rarity = ItemRarity.uncommon
    else:
        rarity = ItemRarity.common

    # Generate item name based on enemy tags
    tags = enemy.get_tags()
    item_name_parts = []

    if "ai" in tags:
        item_name_parts.append("Neural")
    elif "web" in tags:
        item_name_parts.append("Web")
    elif "backend" in tags:
        item_name_parts.append("Server")
    elif "cli" in tags:
        item_name_parts.append("Terminal")
    else:
        item_name_parts.append("Code")

    # Item type
    item_type = random.choice(list(ItemTypes))
    item_name = f"{item_name_parts[0]} {item_type.name}"

    # Generate stat bonuses
    stat_bonuses = {}
    bonus_points = loot_quality * 2

    for _ in range(bonus_points):
        stat = random.choice(list(Stats))
        stat_bonuses[stat.name] = stat_bonuses.get(stat.name, 0) + 1

    # Create item
    item = Item(
        name=item_name,
        rarity=rarity,
        stat_bonuses_json="",
        description=f"A {rarity} item dropped by {enemy.name}",
        equipment_type=itemTypeToEquipment[item_type].name,
    )
    item.set_stat_bonuses(stat_bonuses)

    return item


def apply_item_stats(player: Player, item: Item):
    """
    Apply item stat bonuses to player (temporary during combat or permanent if equipped).
    """
    bonuses = item.get_stat_bonuses()
    for stat, bonus in bonuses.items():
        if hasattr(player, stat):
            setattr(player, stat, getattr(player, stat) + bonus)


def handle_victory(
    player: Player,
    enemy: Enemy,
    loot_quality: int = 1,
    combat_context: Optional[Dict] = None,
) -> Tuple[Item, int, bool, Dict]:
    """
    Handle player victory: award XP and generate loot.
    Returns: (loot_item, xp_gained, leveled_up, achievement_context)
    """
    xp = calculate_xp_reward(enemy)
    leveled_up = award_xp(player, xp)

    # Track stats for achievements
    PlayerStatsRepository.increment_stat(player.id, "enemies_defeated", 1)
    PlayerStatsRepository.increment_stat(player.id, "total_xp_earned", xp)
    if enemy.is_boss:
        PlayerStatsRepository.increment_stat(player.id, "bosses_defeated", 1)

    # Only generate loot 20% of the time (1 in 5 chance)
    loot = None
    if random.random() < 0.2:
        loot = generate_loot(enemy, loot_quality)

    achievement_context = {}

    if loot:
        # Check inventory space before adding
        inventory_count = ItemRepository.get_inventory_count(player.id)
        max_inventory = calculate_inventory_space(player.level)

        if inventory_count >= max_inventory:
            # Inventory full - don't add item
            logger.warning(f"Player {player.name} inventory full, cannot add loot")
            return (None, xp, leveled_up, achievement_context)

        loot = ItemRepository.create(loot)
        ItemRepository.add_to_inventory(player.id, loot.id, 1)
        PlayerStatsRepository.increment_stat(player.id, "items_collected", 1)
        achievement_context["item_rarity"] = loot.rarity

    # Build achievement context
    achievement_context.update({"enemy_level": enemy.level, "enemy": enemy})
    if combat_context:
        achievement_context.update(combat_context)

    PlayerRepository.update(player)

    return (loot, xp, leveled_up, achievement_context)


def handle_defeat(player: Player) -> Dict:
    """
    Handle player defeat: apply penalties.
    Returns: penalty information
    """
    # Reset HP to 50% of max, lose some XP
    max_hp = player.level * 10 + 90
    xp_loss = min(player.xp, player.level * 10)
    player.xp = max(0, player.xp - xp_loss)
    player.hp = max(1, max_hp // 2)  # Restore to 50% HP instead of 1

    PlayerRepository.update(player)

    return {"xp_lost": xp_loss, "hp_reset": True}


def restore_player_hp(player: Player):
    """
    Restore player HP to maximum before entering combat.
    """
    max_hp = player.level * 10 + 90
    if player.hp < max_hp:
        player.hp = max_hp
        PlayerRepository.update(player)
