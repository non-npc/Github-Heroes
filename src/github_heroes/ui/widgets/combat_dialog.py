"""
Combat dialog for turn-based combat.
"""

from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QColor, QPainter, QPixmap
from PyQt6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from github_heroes.core.config import get_resource_path
from github_heroes.core.logging_utils import get_logger
from github_heroes.data.database import get_db
from github_heroes.data.models import Enemy, Player, Stats
from github_heroes.data.repositories import PlayerRepository
from github_heroes.game.logic import combat_turn, handle_defeat, handle_victory

logger = get_logger(__name__)


class ColoredRectangleWidget(QWidget):
    """A simple widget that displays a colored rectangle."""

    def __init__(self, color: QColor, size: int = 48, parent=None):
        super().__init__(parent)
        self.color = color
        self.setFixedSize(size, size)
        self.setStyleSheet(f"background-color: {color.name()}; border: 1px solid #333;")

    def paintEvent(self, event):
        """Paint the colored rectangle."""
        painter = QPainter(self)
        painter.fillRect(self.rect(), self.color)
        super().paintEvent(event)


class CombatDialog(QDialog):
    """
    Combat dialog for turn-based battles.
    """

    combat_ended = pyqtSignal(str, object)  # result, data

    def __init__(
        self, player: Player, enemy: Enemy, loot_quality: int = 1, parent=None
    ):
        super().__init__(parent)
        self.player = player
        self.enemy = enemy
        self.loot_quality = loot_quality
        self.turn_count = 0
        self.damage_taken = 0
        self.starting_hp = player.hp

        # Calculate equipped item bonuses
        from github_heroes.data.repositories import ItemRepository

        self.equipped_bonuses = {stat: 0 for stat in Stats}
        inventory = ItemRepository.get_player_inventory(player.id)
        for item, quantity, equipped in inventory:
            if equipped:
                bonuses = item.stats()
                for stat, bonus in bonuses.items():
                    if stat in self.equipped_bonuses:
                        self.equipped_bonuses[stat] += bonus

        # Create combat player with bonuses applied
        self.combat_player = Player(
            id=player.id,
            name=player.name,
            level=player.level,
            xp=player.xp,
            hp=player.hp + self.equipped_bonuses[Stats.hp],
            attack=player.attack + self.equipped_bonuses[Stats.attack],
            defense=player.defense + self.equipped_bonuses[Stats.defense],
            speed=player.speed + self.equipped_bonuses[Stats.speed],
            luck=player.luck + self.equipped_bonuses[Stats.luck],
            player_class=player.player_class,
        )

        # Store initial max HP for progress bars
        self.player_max_hp = self.combat_player.hp
        self.enemy_max_hp = self.enemy.hp

        self.init_ui()
        self.update_display()

    def init_ui(self):
        """Initialize UI."""
        layout = QVBoxLayout()

        # Title
        title = QLabel(f"Combat: {self.enemy.name}")
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(title)

        # Two-column layout for player and enemy
        combat_layout = QHBoxLayout()
        combat_layout.setSpacing(20)  # Add spacing between columns

        # Left column: Player info
        player_group = QVBoxLayout()
        player_group.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Player character image (48x48)
        self.player_image = QLabel()
        self.player_image.setFixedSize(48, 48)
        self.player_image.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.player_image.setStyleSheet("background-color: transparent;")
        self.load_player_image()
        player_group.addWidget(
            self.player_image, alignment=Qt.AlignmentFlag.AlignCenter
        )

        self.player_name_label = QLabel()
        self.player_name_label.setStyleSheet("font-weight: bold;")
        self.player_hp_bar = QProgressBar()
        # Use initial max HP for the maximum value
        self.player_hp_bar.setMaximum(max(self.player_max_hp, 1))
        player_initial_hp = max(self.combat_player.hp, 0)
        self.player_hp_bar.setValue(player_initial_hp)
        # Set initial HP bar color
        self.set_hp_bar_color(self.player_hp_bar, player_initial_hp, self.player_max_hp)
        self.player_stats_label = QLabel()
        player_group.addWidget(self.player_name_label)
        player_group.addWidget(self.player_hp_bar)
        player_group.addWidget(self.player_stats_label)

        player_widget = QWidget()
        player_widget.setLayout(player_group)
        combat_layout.addWidget(
            player_widget, stretch=1
        )  # Equal stretch for both columns

        # Right column: Enemy info with creature image
        enemy_group = QVBoxLayout()
        enemy_group.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Enemy creature image (48x48)
        self.enemy_image = QLabel()
        self.enemy_image.setFixedSize(48, 48)
        self.enemy_image.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.enemy_image.setStyleSheet("background-color: transparent;")
        self.load_enemy_image()
        enemy_group.addWidget(self.enemy_image, alignment=Qt.AlignmentFlag.AlignCenter)

        self.enemy_name_label = QLabel()
        self.enemy_name_label.setStyleSheet("font-weight: bold;")
        self.enemy_hp_bar = QProgressBar()
        # Use initial max HP for the maximum value
        self.enemy_hp_bar.setMaximum(max(self.enemy_max_hp, 1))
        enemy_initial_hp = max(self.enemy.hp, 0)
        self.enemy_hp_bar.setValue(enemy_initial_hp)
        # Set initial HP bar color
        self.set_hp_bar_color(self.enemy_hp_bar, enemy_initial_hp, self.enemy_max_hp)
        self.enemy_stats_label = QLabel()
        enemy_group.addWidget(self.enemy_name_label)
        enemy_group.addWidget(self.enemy_hp_bar)
        enemy_group.addWidget(self.enemy_stats_label)

        enemy_widget = QWidget()
        enemy_widget.setLayout(enemy_group)
        combat_layout.addWidget(
            enemy_widget, stretch=1
        )  # Equal stretch for both columns

        layout.addLayout(combat_layout)

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

    def load_player_image(self):
        """Load and display the player character image."""
        if self.player.player_image_id:
            # Format image ID as 001, 002, etc.
            image_id_str = f"{self.player.player_image_id:03d}"
            image_path = get_resource_path(f"assets/player/{image_id_str}.png")

            if image_path.exists():
                pixmap = QPixmap(str(image_path))
                # Scale to 48x48 while maintaining aspect ratio
                scaled_pixmap = pixmap.scaled(
                    48,
                    48,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
                self.player_image.setPixmap(scaled_pixmap)
            else:
                # Fallback to colored rectangle if image not found
                logger.warning(f"Player image not found: {image_path}")
                player_color = QColor(50, 100, 200)
                self.player_image.setStyleSheet(
                    f"background-color: {player_color.name()};"
                )
        else:
            # Fallback to colored rectangle if no image ID
            player_color = QColor(50, 100, 200)
            self.player_image.setStyleSheet(f"background-color: {player_color.name()};")

    def load_enemy_image(self):
        """Load and display the enemy creature image."""
        if self.enemy.creature_image_id:
            # Format image ID as 001, 002, etc.
            image_id_str = f"{self.enemy.creature_image_id:03d}"
            image_path = get_resource_path(f"assets/creatures/{image_id_str}.png")

            if image_path.exists():
                pixmap = QPixmap(str(image_path))
                # Scale to 48x48 while maintaining aspect ratio
                scaled_pixmap = pixmap.scaled(
                    48,
                    48,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
                self.enemy_image.setPixmap(scaled_pixmap)
            else:
                # Fallback to colored rectangle if image not found
                logger.warning(f"Creature image not found: {image_path}")
                enemy_color = QColor(200, 50, 50)
                self.enemy_image.setStyleSheet(
                    f"background-color: {enemy_color.name()};"
                )
        else:
            # Fallback to colored rectangle if no image ID
            enemy_color = QColor(200, 50, 50)
            self.enemy_image.setStyleSheet(f"background-color: {enemy_color.name()};")

    def set_hp_bar_color(
        self, progress_bar: QProgressBar, current_hp: int, max_hp: int
    ):
        """Set HP bar color based on HP percentage."""
        if max_hp <= 0:
            percentage = 0
        else:
            percentage = (current_hp / max_hp) * 100

        # Color thresholds:
        # Green: > 60%
        # Yellow: 30-60%
        # Orange: 15-30%
        # Red: < 15%
        if percentage > 60:
            color = "#4CAF50"  # Green
        elif percentage > 30:
            color = "#FFC107"  # Yellow/Amber
        elif percentage > 15:
            color = "#FF9800"  # Orange
        else:
            color = "#F44336"  # Red

        # Set stylesheet for the progress bar chunk
        progress_bar.setStyleSheet(f"""
            QProgressBar {{
                border: 1px solid #333;
                border-radius: 3px;
                text-align: center;
            }}
            QProgressBar::chunk {{
                background-color: {color};
                border-radius: 2px;
            }}
        """)

    def update_display(self):
        """Update display with current stats."""
        self.enemy_name_label.setText(f"{self.enemy.name} (Level {self.enemy.level})")
        # Keep maximum at initial HP, only update the value
        self.enemy_hp_bar.setMaximum(max(self.enemy_max_hp, 1))
        enemy_current_hp = max(self.enemy.hp, 0)
        self.enemy_hp_bar.setValue(enemy_current_hp)
        # Update HP bar color based on percentage
        self.set_hp_bar_color(self.enemy_hp_bar, enemy_current_hp, self.enemy_max_hp)
        self.enemy_stats_label.setText(
            f"HP: {enemy_current_hp} | Attack: {self.enemy.attack} | Defense: {self.enemy.defense}"
        )

        self.player_name_label.setText(
            f"{self.combat_player.name} (Level {self.combat_player.level})"
        )
        # Keep maximum at initial HP, only update the value
        self.player_hp_bar.setMaximum(max(self.player_max_hp, 1))
        player_current_hp = max(self.combat_player.hp, 0)
        self.player_hp_bar.setValue(player_current_hp)
        # Update HP bar color based on percentage
        self.set_hp_bar_color(self.player_hp_bar, player_current_hp, self.player_max_hp)
        self.player_stats_label.setText(
            f"HP: {player_current_hp} | Attack: {self.combat_player.attack} | Defense: {self.combat_player.defense}"
        )

    def execute_action(self, action: str):
        """Execute a combat action."""
        old_hp = self.combat_player.hp
        message, continues, result = combat_turn(self.combat_player, self.enemy, action)
        self.turn_count += 1
        self.damage_taken += max(0, old_hp - self.combat_player.hp)

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
                self.player.hp = max(
                    1, self.combat_player.hp - self.equipped_bonuses[Stats.hp]
                )

                # Build combat context for achievements
                combat_context = {
                    "turns": self.turn_count,
                    "damage_taken": self.damage_taken,
                    "final_hp": self.combat_player.hp,
                    "total_hp": self.combat_player.hp + self.equipped_bonuses[Stats.hp],
                    "total_attack": self.combat_player.attack,
                }

                # Track perfect victory
                if self.damage_taken == 0:
                    from github_heroes.data.repositories import PlayerStatsRepository

                    PlayerStatsRepository.increment_stat(
                        self.player.id, "perfect_victories", 1
                    )

                loot, xp, leveled_up, achievement_context = handle_victory(
                    self.player, self.enemy, self.loot_quality, combat_context
                )

                # Check achievements
                from github_heroes.game.achievements import check_achievements

                newly_unlocked = check_achievements(self.player, achievement_context)
                if newly_unlocked:
                    from github_heroes.game.achievements import ACHIEVEMENTS

                    achievement_names = [
                        ACHIEVEMENTS[ach_id]["name"]
                        for ach_id in newly_unlocked
                        if ach_id in ACHIEVEMENTS
                    ]
                    if achievement_names:
                        ach_msg = "🏆 Achievement Unlocked!\n\n" + "\n".join(
                            f"• {name}" for name in achievement_names
                        )
                        QMessageBox.information(self, "Achievement Unlocked!", ach_msg)

                PlayerRepository.update(self.player)

                result_msg = f"Victory! You gained {xp} XP!"
                if loot:
                    result_msg += f"\nYou obtained: {loot.name} ({loot.rarity.name})"
                else:
                    # Check if inventory was full
                    from github_heroes.data.repositories import ItemRepository
                    from github_heroes.game.logic import calculate_inventory_space

                    inventory_count = ItemRepository.get_inventory_count(self.player.id)
                    max_inventory = calculate_inventory_space(self.player.level)
                    if inventory_count >= max_inventory:
                        result_msg += "\n⚠ Inventory full! Item could not be added."

                QMessageBox.information(self, "Victory!", result_msg)

                # Show level-up popup if player leveled up
                if leveled_up:
                    level_up_msg = "🎉 LEVEL UP! 🎉\n\n"
                    level_up_msg += f"Congratulations, {self.player.name}!\n"
                    level_up_msg += f"You have reached Level {self.player.level}!\n\n"
                    level_up_msg += "Your stats have increased:\n"
                    level_up_msg += "• HP: +10\n"
                    level_up_msg += "• Attack: +2\n"
                    level_up_msg += "• Defense: +1\n"
                    level_up_msg += "• Speed: +1\n"
                    level_up_msg += "• Luck: +1\n\n"
                    level_up_msg += "Keep fighting to become even stronger!"

                    QMessageBox.information(self, "Level Up!", level_up_msg)

                self.combat_ended.emit(
                    "victory", {"loot": loot, "xp": xp, "leveled_up": leveled_up}
                )
                self.accept()

            elif result == "defeat":
                # Update base player HP from combat player
                self.player.hp = max(
                    1, self.combat_player.hp - self.equipped_bonuses[Stats.hp]
                )
                penalties = handle_defeat(self.player)
                PlayerRepository.update(self.player)

                result_msg = f"Defeat! You lost {penalties['xp_lost']} XP."
                QMessageBox.warning(self, "Defeat", result_msg)
                self.combat_ended.emit("defeat", penalties)
                self.reject()

            elif result == "fled":
                self.combat_ended.emit("fled", {})
                self.reject()
