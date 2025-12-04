"""
Player profile view showing stats, inventory, and progress.
"""

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QProgressBar,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from github_heroes.core.config import get_resource_path
from github_heroes.core.logging_utils import get_logger
from github_heroes.data.models import EquipmentTypes, Stats
from github_heroes.data.repositories import (
    ItemRepository,
    QuestRepository,
    RepoWorldRepository,
)
from github_heroes.game.achievements import get_player_achievements
from github_heroes.game.logic import bonus_as_string, calculate_inventory_space
from github_heroes.game.state import get_game_state

logger = get_logger(__name__)


class PlayerView(QWidget):
    """
    Player profile view.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        """Initialize UI."""
        layout = QVBoxLayout()

        # Title
        title = QLabel("Player Profile")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(title)

        # Create tab widget
        self.tabs = QTabWidget()

        # Stats tab
        stats_tab = QWidget()
        stats_tab_layout = QHBoxLayout()

        # Left column: Stats content
        stats_left_layout = QVBoxLayout()

        self.name_label = QLabel("-")
        self.name_label.setStyleSheet("font-size: 24px; font-weight: bold;")
        self.class_label = QLabel("Class: -")
        self.level_label = QLabel("Level: -")
        self.xp_label = QLabel("XP: -")
        self.xp_bar = QProgressBar()
        self.xp_bar.setMaximum(100)
        # Set XP bar color to yellow
        self.xp_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #333;
                border-radius: 3px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #FFC107;
                border-radius: 2px;
            }
        """)

        self.stats_labels = {}
        for stat in Stats:
            name = stat.name.capitalize() if len(stat.name) > 2 else stat.name.upper()
            self.stats_labels[stat] = QLabel(f"{name}: -")

        # Equipped items labels
        self.equipped_labels = {}
        for equipmentType in EquipmentTypes:
            self.equipped_labels[equipmentType] = QLabel(
                f"{equipmentType.name.capitalize()}: None"
            )

        stats_left_layout.addWidget(self.name_label)
        stats_left_layout.addWidget(self.class_label)
        stats_left_layout.addWidget(self.level_label)
        stats_left_layout.addWidget(self.xp_label)
        stats_left_layout.addWidget(self.xp_bar)
        stats_left_layout.addWidget(QLabel("---"))
        for label_widget in self.stats_labels.values():
            stats_left_layout.addWidget(label_widget)
        stats_left_layout.addWidget(QLabel("---"))
        stats_left_layout.addWidget(QLabel("<b>Equipped Items:</b>"))
        for label_widget in self.equipped_labels.values():
            stats_left_layout.addWidget(label_widget)
        stats_left_layout.addStretch()

        # Right column: Player image
        stats_right_layout = QVBoxLayout()
        stats_right_layout.setAlignment(
            Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter
        )

        self.player_image = QLabel()
        self.player_image.setFixedSize(256, 256)
        self.player_image.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.player_image.setStyleSheet("background-color: transparent;")
        stats_right_layout.addWidget(self.player_image)
        stats_right_layout.addStretch()

        stats_tab_layout.addLayout(stats_left_layout, stretch=1)
        stats_tab_layout.addLayout(stats_right_layout, stretch=1)
        stats_tab.setLayout(stats_tab_layout)

        # Inventory tab
        inventory_tab = QWidget()
        inventory_tab_layout = QVBoxLayout()

        # Inventory space label
        self.inventory_space_label = QLabel("Inventory: 0/10")
        inventory_tab_layout.addWidget(self.inventory_space_label)

        # Recycler button
        recycler_btn = QPushButton("Open Recycler")
        recycler_btn.clicked.connect(self.open_recycler)
        recycler_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
                border: none;
                padding: 8px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        inventory_tab_layout.addWidget(recycler_btn)

        self.inventory_table = QTableWidget()
        self.inventory_table.setColumnCount(6)
        self.inventory_table.setHorizontalHeaderLabels(
            ["Name", "Rarity", "Bonuses", "Quantity", "Equipped", "Actions"]
        )

        # Set column widths - make Bonuses column wider
        header = self.inventory_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # Name
        header.setSectionResizeMode(
            1, QHeaderView.ResizeMode.ResizeToContents
        )  # Rarity
        header.setSectionResizeMode(
            2, QHeaderView.ResizeMode.Interactive
        )  # Bonuses - resizable
        header.setSectionResizeMode(
            3, QHeaderView.ResizeMode.ResizeToContents
        )  # Quantity
        header.setSectionResizeMode(
            4, QHeaderView.ResizeMode.ResizeToContents
        )  # Equipped
        header.setSectionResizeMode(
            5, QHeaderView.ResizeMode.ResizeToContents
        )  # Actions

        # Set minimum width for Bonuses column
        self.inventory_table.setColumnWidth(2, 250)  # Bonuses column default width

        # Allow last section to stretch
        header.setStretchLastSection(False)

        inventory_tab_layout.addWidget(self.inventory_table)
        inventory_tab.setLayout(inventory_tab_layout)

        # Achievements tab
        achievements_tab = QWidget()
        achievements_tab_layout = QVBoxLayout()

        self.achievements_label = QLabel("No achievements yet")
        self.achievements_label.setWordWrap(True)
        achievements_tab_layout.addWidget(self.achievements_label)
        achievements_tab_layout.addStretch()
        achievements_tab.setLayout(achievements_tab_layout)

        # Add tabs
        self.tabs.addTab(stats_tab, "Stats")
        self.tabs.addTab(inventory_tab, "Inventory")
        self.tabs.addTab(achievements_tab, "Achievements")

        layout.addWidget(self.tabs)
        self.setLayout(layout)

    def refresh(self):
        """Refresh player data."""
        # Check achievements periodically
        from github_heroes.game.state import get_game_state

        game_state = get_game_state()
        if game_state.current_player:
            from github_heroes.game.achievements import check_achievements

            check_achievements(game_state.current_player)
        game_state = get_game_state()
        player = game_state.current_player

        if not player:
            self.name_label.setText("No player selected")
            self.class_label.setText("Class: -")
            for equipment_type, qlabel in self.equipped_labels.items():
                qlabel.setText(f"{equipment_type.name.capitalize()}: None")
            self.load_player_image(None)
            return

        # Update stats
        self.name_label.setText(player.name)
        class_name = player.player_class or "Adventurer"
        self.class_label.setText(f"Class: {class_name}")
        self.level_label.setText(f"Level: {player.level}")
        self.xp_label.setText(f"XP: {player.xp} / {player.level * 100}")
        self.xp_bar.setMaximum(player.level * 100)
        self.xp_bar.setValue(player.xp)

        # Load player image
        self.load_player_image(player)

        # Calculate stats with equipped items
        base_stats = player.stats()

        inventory = ItemRepository.get_player_inventory(player.id)
        equipped_bonuses = {stat: 0 for stat in Stats}

        # Track equipped items by slot
        equipped_items = {
            equipment_type.name: None for equipment_type in EquipmentTypes
        }

        for item, quantity, equipped in inventory:
            if equipped:
                bonuses = item.stats()
                for stat, bonus in bonuses.items():
                    if stat in equipped_bonuses:
                        equipped_bonuses[stat] += bonus

                # Track equipped item by slot
                if item.equipment_type and item.equipment_type in equipped_items:
                    equipped_items[item.equipment_type] = item

        # Display stats with bonuses
        total_stats = {
            stat: base_stats[stat] + equipped_bonuses[stat] for stat in Stats
        }

        for stat, qlabel in self.stats_labels.items():
            name = stat.name.capitalize() if len(stat.name) > 2 else stat.name.upper()
            label = f"{name}: {total_stats[stat]} ({base_stats[stat]} + {equipped_bonuses[stat]})"
            qlabel.setText(label)

        # Update equipped items display
        for equipment_type, qlabel in self.equipped_labels.items():
            label = "None"
            if equipped_items[equipment_type.name]:
                label = f"{equipment_type.name.capitalize()}: {equipped_items[equipment_type.name].name} ({bonus_as_string(equipped_items[equipment_type.name].get_stat_bonuses())})"
            qlabel.setText(label)

        # Update inventory space
        inventory_count = ItemRepository.get_inventory_count(player.id)
        max_inventory = calculate_inventory_space(player.level)
        self.inventory_space_label.setText(
            f"Inventory: {inventory_count}/{max_inventory}"
        )

        # Update inventory table
        self.inventory_table.setRowCount(0)

        for item, quantity, equipped in inventory:
            row = self.inventory_table.rowCount()
            self.inventory_table.insertRow(row)

            # Name
            name_text = item.name
            if equipped:
                name_text += " [EQUIPPED]"
            self.inventory_table.setItem(row, 0, QTableWidgetItem(name_text))

            # Rarity
            self.inventory_table.setItem(row, 1, QTableWidgetItem(item.rarity.name))

            # Bonuses
            bonuses = item.get_stat_bonuses()
            bonuses_str = bonus_as_string(bonuses)
            self.inventory_table.setItem(row, 2, QTableWidgetItem(bonuses_str))

            # Quantity
            self.inventory_table.setItem(row, 3, QTableWidgetItem(str(quantity)))

            # Equipped status
            self.inventory_table.setItem(
                row, 4, QTableWidgetItem("Yes" if equipped else "No")
            )

            # Actions (Equip/Unequip button)
            action_widget = QWidget()
            action_layout = QHBoxLayout()
            action_layout.setContentsMargins(2, 2, 2, 2)

            if equipped:
                unequip_btn = QPushButton("Unequip")
                unequip_btn.clicked.connect(
                    lambda checked, item_id=item.id: self.unequip_item(item_id)
                )
                action_layout.addWidget(unequip_btn)
            else:
                equip_btn = QPushButton("Equip")
                equip_btn.clicked.connect(
                    lambda checked, item_id=item.id: self.equip_item(item_id)
                )
                action_layout.addWidget(equip_btn)

            action_widget.setLayout(action_layout)
            self.inventory_table.setCellWidget(row, 5, action_widget)

        # Update achievements
        unlocked_achievements = get_player_achievements(player.id)

        achievement_text = []
        achievement_text.append("=== UNLOCKED ACHIEVEMENTS ===\n")

        if unlocked_achievements:
            # Group by category
            by_category = {}
            for ach in unlocked_achievements:
                cat = ach["category"]
                if cat not in by_category:
                    by_category[cat] = []
                by_category[cat].append(ach)

            for category in sorted(by_category.keys()):
                achievement_text.append(f"\n{category}:")
                for ach in sorted(
                    by_category[category], key=lambda x: x["unlocked_at"]
                ):
                    achievement_text.append(f"  ✓ {ach['name']} - {ach['description']}")
        else:
            achievement_text.append("No achievements unlocked yet.")

        achievement_text.append("\n\n=== PROGRESS ===")
        worlds = RepoWorldRepository.get_all()
        completed_quests = sum(
            1
            for w in worlds
            for q in QuestRepository.get_by_world_id(w.id)
            if q.status == "completed"
        )
        achievement_text.append(f"Worlds Discovered: {len(worlds)}")
        achievement_text.append(f"Quests Completed: {completed_quests}")

        # Show progress for some key achievements
        achievement_text.append("\n\n=== TRACKING ===")
        unlocked_ids = {ach["id"] for ach in unlocked_achievements}

        # Level achievements
        if player.level < 10:
            achievement_text.append(
                f"Progress to Level 10 Hero: Level {player.level}/10"
            )
        elif player.level < 25:
            achievement_text.append(
                f"Progress to Level 25 Veteran: Level {player.level}/25"
            )
        elif player.level < 50:
            achievement_text.append(
                f"Progress to Level 50 Legend: Level {player.level}/50"
            )
        elif player.level < 100:
            achievement_text.append(
                f"Progress to Level 100 Master: Level {player.level}/100"
            )

        # Combat stats
        from github_heroes.data.repositories import PlayerStatsRepository

        stats = PlayerStatsRepository.get_or_create(player.id)
        if "first_blood" not in unlocked_ids:
            achievement_text.append(
                f"Progress to First Blood: {stats['enemies_defeated']}/1 enemies defeated"
            )
        if "elite_hunter" not in unlocked_ids:
            achievement_text.append(
                f"Progress to Elite Hunter: {stats['enemies_defeated']}/50 enemies defeated"
            )
        if "unstoppable" not in unlocked_ids:
            achievement_text.append(
                f"Progress to Unstoppable: {stats['enemies_defeated']}/100 enemies defeated"
            )

        self.achievements_label.setText("\n".join(achievement_text))

    def load_player_image(self, player):
        """Load and display the player character image."""
        if player and player.player_image_id:
            # Format image ID as 001, 002, etc.
            image_id_str = f"{player.player_image_id:03d}"
            image_path = get_resource_path(f"assets/player/{image_id_str}.png")

            if image_path.exists():
                pixmap = QPixmap(str(image_path))
                # Scale to 256x256 while maintaining aspect ratio
                scaled_pixmap = pixmap.scaled(
                    256,
                    256,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
                self.player_image.setPixmap(scaled_pixmap)
            else:
                logger.warning(f"Player image not found: {image_path}")
                self.player_image.clear()
        else:
            # Clear image if no player or no image ID
            self.player_image.clear()

    def equip_item(self, item_id: int):
        """Equip an item."""
        game_state = get_game_state()
        if not game_state.current_player:
            return

        ItemRepository.equip_item(game_state.current_player.id, item_id)
        self.refresh()

    def unequip_item(self, item_id: int):
        """Unequip an item."""
        game_state = get_game_state()
        if not game_state.current_player:
            return

        ItemRepository.unequip_item(game_state.current_player.id, item_id)
        self.refresh()

    def open_recycler(self):
        """Open the recycler dialog."""
        from github_heroes.ui.widgets.recycler_dialog import RecyclerDialog

        dialog = RecyclerDialog(self)
        dialog.exec()
        # Refresh after closing recycler
        self.refresh()
