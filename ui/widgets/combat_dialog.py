"""
Combat dialog for turn-based combat.
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QProgressBar, QTextEdit, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from data.models import Player, Enemy
from data.repositories import PlayerRepository
from game.logic import combat_turn, handle_victory, handle_defeat
from game.state import get_game_state
from data.repositories import PlayerRepository, DungeonRoomRepository
from data.database import get_db
from core.logging_utils import get_logger
from PyQt6.QtCore import QTimer

logger = get_logger(__name__)

class CombatDialog(QDialog):
    """
    Combat dialog for turn-based battles.
    """
    
    combat_ended = pyqtSignal(str, object)  # result, data
    
    def __init__(self, player: Player, enemy: Enemy, loot_quality: int = 1, parent=None):
        super().__init__(parent)
        self.player = player
        self.enemy = enemy
        self.loot_quality = loot_quality
        
        # Calculate equipped item bonuses
        from data.repositories import ItemRepository
        self.equipped_bonuses = {"hp": 0, "attack": 0, "defense": 0, "speed": 0, "luck": 0}
        inventory = ItemRepository.get_player_inventory(player.id)
        for item, quantity, equipped in inventory:
            if equipped:
                bonuses = item.get_stat_bonuses()
                for stat, bonus in bonuses.items():
                    if stat in self.equipped_bonuses:
                        self.equipped_bonuses[stat] += bonus
        
        # Create combat player with bonuses applied
        self.combat_player = Player(
            id=player.id, name=player.name, level=player.level, xp=player.xp,
            hp=player.hp + self.equipped_bonuses["hp"],
            attack=player.attack + self.equipped_bonuses["attack"],
            defense=player.defense + self.equipped_bonuses["defense"],
            speed=player.speed + self.equipped_bonuses["speed"],
            luck=player.luck + self.equipped_bonuses["luck"],
            github_handle=player.github_handle
        )
        
        self.init_ui()
        self.update_display()
    
    def init_ui(self):
        """Initialize UI."""
        layout = QVBoxLayout()
        
        # Title
        title = QLabel(f"Combat: {self.enemy.name}")
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(title)
        
        # Enemy info
        enemy_group = QVBoxLayout()
        self.enemy_name_label = QLabel()
        self.enemy_hp_bar = QProgressBar()
        self.enemy_hp_bar.setMaximum(self.enemy.hp)
        self.enemy_hp_bar.setValue(self.enemy.hp)
        self.enemy_stats_label = QLabel()
        enemy_group.addWidget(self.enemy_name_label)
        enemy_group.addWidget(self.enemy_hp_bar)
        enemy_group.addWidget(self.enemy_stats_label)
        layout.addLayout(enemy_group)
        
        # Player info
        player_group = QVBoxLayout()
        self.player_name_label = QLabel()
        self.player_hp_bar = QProgressBar()
        self.player_hp_bar.setMaximum(self.player.hp)
        self.player_hp_bar.setValue(self.player.hp)
        self.player_stats_label = QLabel()
        player_group.addWidget(self.player_name_label)
        player_group.addWidget(self.player_hp_bar)
        player_group.addWidget(self.player_stats_label)
        layout.addLayout(player_group)
        
        # Combat log
        log_label = QLabel("Combat Log:")
        layout.addWidget(log_label)
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(150)
        layout.addWidget(self.log_text)
        
        # Action buttons
        buttons_layout = QHBoxLayout()
        
        self.attack_btn = QPushButton("Attack")
        self.attack_btn.clicked.connect(lambda: self.execute_action("attack"))
        buttons_layout.addWidget(self.attack_btn)
        
        self.defend_btn = QPushButton("Defend")
        self.defend_btn.clicked.connect(lambda: self.execute_action("defend"))
        buttons_layout.addWidget(self.defend_btn)
        
        self.flee_btn = QPushButton("Flee")
        self.flee_btn.clicked.connect(lambda: self.execute_action("flee"))
        buttons_layout.addWidget(self.flee_btn)
        
        layout.addLayout(buttons_layout)
        
        self.setLayout(layout)
        self.setWindowTitle("Combat")
        self.setMinimumWidth(500)
    
    def update_display(self):
        """Update display with current stats."""
        self.enemy_name_label.setText(f"{self.enemy.name} (Level {self.enemy.level})")
        self.enemy_hp_bar.setMaximum(max(self.enemy.hp, 1))
        self.enemy_hp_bar.setValue(max(self.enemy.hp, 0))
        self.enemy_stats_label.setText(
            f"HP: {max(self.enemy.hp, 0)} | Attack: {self.enemy.attack} | Defense: {self.enemy.defense}"
        )
        
        self.player_name_label.setText(f"{self.combat_player.name} (Level {self.combat_player.level})")
        self.player_hp_bar.setMaximum(max(self.combat_player.hp, 1))
        self.player_hp_bar.setValue(max(self.combat_player.hp, 0))
        self.player_stats_label.setText(
            f"HP: {max(self.combat_player.hp, 0)} | Attack: {self.combat_player.attack} | Defense: {self.combat_player.defense}"
        )
    
    def execute_action(self, action: str):
        """Execute a combat action."""
        message, continues, result = combat_turn(self.combat_player, self.enemy, action)
        
        # Get combat text speed setting
        db = get_db()
        speed_delay = int(db.get_setting("combat_text_speed", "0"))
        
        if speed_delay > 0:
            # Add message with delay
            self.log_text.append(message)
            QTimer.singleShot(speed_delay, lambda: self.update_display())
        else:
            # Instant display
            self.log_text.append(message)
            self.update_display()
        
        if not continues:
            # Combat ended
            self.attack_btn.setEnabled(False)
            self.defend_btn.setEnabled(False)
            self.flee_btn.setEnabled(False)
            
            if result == "victory":
                # Update base player HP from combat player (but keep equipped bonuses separate)
                self.player.hp = max(1, self.combat_player.hp - self.equipped_bonuses["hp"])
                old_level = self.player.level
                loot, xp, leveled_up = handle_victory(self.player, self.enemy, self.loot_quality)
                PlayerRepository.update(self.player)
                
                result_msg = f"Victory! You gained {xp} XP!"
                if loot:
                    result_msg += f"\nYou obtained: {loot.name} ({loot.rarity})"
                else:
                    # Check if inventory was full
                    from data.repositories import ItemRepository
                    from game.logic import calculate_inventory_space
                    inventory_count = ItemRepository.get_inventory_count(self.player.id)
                    max_inventory = calculate_inventory_space(self.player.level)
                    if inventory_count >= max_inventory:
                        result_msg += f"\n⚠ Inventory full! Item could not be added."
                
                QMessageBox.information(self, "Victory!", result_msg)
                
                # Show level-up popup if player leveled up
                if leveled_up:
                    level_up_msg = f"🎉 LEVEL UP! 🎉\n\n"
                    level_up_msg += f"Congratulations, {self.player.name}!\n"
                    level_up_msg += f"You have reached Level {self.player.level}!\n\n"
                    level_up_msg += f"Your stats have increased:\n"
                    level_up_msg += f"• HP: +10\n"
                    level_up_msg += f"• Attack: +2\n"
                    level_up_msg += f"• Defense: +1\n"
                    level_up_msg += f"• Speed: +1\n"
                    level_up_msg += f"• Luck: +1\n\n"
                    level_up_msg += f"Keep fighting to become even stronger!"
                    
                    QMessageBox.information(self, "Level Up!", level_up_msg)
                
                self.combat_ended.emit("victory", {"loot": loot, "xp": xp, "leveled_up": leveled_up})
                self.accept()
            
            elif result == "defeat":
                # Update base player HP from combat player
                self.player.hp = max(1, self.combat_player.hp - self.equipped_bonuses["hp"])
                penalties = handle_defeat(self.player)
                PlayerRepository.update(self.player)
                
                result_msg = f"Defeat! You lost {penalties['xp_lost']} XP."
                QMessageBox.warning(self, "Defeat", result_msg)
                self.combat_ended.emit("defeat", penalties)
                self.reject()
            
            elif result == "fled":
                self.combat_ended.emit("fled", {})
                self.reject()

