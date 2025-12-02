"""
Player profile view showing stats, inventory, and progress.
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QProgressBar,
    QTableWidget, QTableWidgetItem, QGroupBox, QHeaderView, QPushButton, QWidget
)
from PyQt6.QtCore import Qt
from data.repositories import ItemRepository, RepoWorldRepository, QuestRepository, PlayerRepository
from game.state import get_game_state
from game.logic import calculate_inventory_space, apply_item_stats
from core.logging_utils import get_logger

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
        
        # Stats section
        stats_group = QGroupBox("Stats")
        stats_layout = QVBoxLayout()
        
        self.name_label = QLabel("Name: -")
        self.level_label = QLabel("Level: -")
        self.xp_label = QLabel("XP: -")
        self.xp_bar = QProgressBar()
        self.xp_bar.setMaximum(100)
        
        self.hp_label = QLabel("HP: -")
        self.attack_label = QLabel("Attack: -")
        self.defense_label = QLabel("Defense: -")
        self.speed_label = QLabel("Speed: -")
        self.luck_label = QLabel("Luck: -")
        
        stats_layout.addWidget(self.name_label)
        stats_layout.addWidget(self.level_label)
        stats_layout.addWidget(self.xp_label)
        stats_layout.addWidget(self.xp_bar)
        stats_layout.addWidget(QLabel("---"))
        stats_layout.addWidget(self.hp_label)
        stats_layout.addWidget(self.attack_label)
        stats_layout.addWidget(self.defense_label)
        stats_layout.addWidget(self.speed_label)
        stats_layout.addWidget(self.luck_label)
        
        stats_group.setLayout(stats_layout)
        layout.addWidget(stats_group)
        
        # Inventory section
        inventory_group = QGroupBox("Inventory")
        inventory_layout = QVBoxLayout()
        
        # Inventory space label
        self.inventory_space_label = QLabel("Inventory: 0/10")
        inventory_layout.addWidget(self.inventory_space_label)
        
        # Recycler button
        recycler_btn = QPushButton("Open Recycler")
        recycler_btn.clicked.connect(self.open_recycler)
        inventory_layout.addWidget(recycler_btn)
        
        self.inventory_table = QTableWidget()
        self.inventory_table.setColumnCount(6)
        self.inventory_table.setHorizontalHeaderLabels(["Name", "Rarity", "Bonuses", "Quantity", "Equipped", "Actions"])
        
        # Set column widths - make Bonuses column wider
        header = self.inventory_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # Name
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)  # Rarity
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive)  # Bonuses - resizable
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # Quantity
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)  # Equipped
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)  # Actions
        
        # Set minimum width for Bonuses column
        self.inventory_table.setColumnWidth(2, 250)  # Bonuses column default width
        
        # Allow last section to stretch
        header.setStretchLastSection(False)
        
        inventory_layout.addWidget(self.inventory_table)
        
        inventory_group.setLayout(inventory_layout)
        layout.addWidget(inventory_group)
        
        # Achievements section
        achievements_group = QGroupBox("Achievements")
        achievements_layout = QVBoxLayout()
        
        self.achievements_label = QLabel("No achievements yet")
        self.achievements_label.setWordWrap(True)
        achievements_layout.addWidget(self.achievements_label)
        
        achievements_group.setLayout(achievements_layout)
        layout.addWidget(achievements_group)
        
        layout.addStretch()
        self.setLayout(layout)
    
    def refresh(self):
        """Refresh player data."""
        game_state = get_game_state()
        player = game_state.current_player
        
        if not player:
            self.name_label.setText("Name: No player selected")
            return
        
        # Update stats
        self.name_label.setText(f"Name: {player.name}")
        self.level_label.setText(f"Level: {player.level}")
        self.xp_label.setText(f"XP: {player.xp} / {player.level * 100}")
        self.xp_bar.setMaximum(player.level * 100)
        self.xp_bar.setValue(player.xp)
        
        # Calculate stats with equipped items
        base_hp = player.hp
        base_attack = player.attack
        base_defense = player.defense
        base_speed = player.speed
        base_luck = player.luck
        
        inventory = ItemRepository.get_player_inventory(player.id)
        equipped_bonuses = {"hp": 0, "attack": 0, "defense": 0, "speed": 0, "luck": 0}
        
        for item, quantity, equipped in inventory:
            if equipped:
                bonuses = item.get_stat_bonuses()
                for stat, bonus in bonuses.items():
                    if stat in equipped_bonuses:
                        equipped_bonuses[stat] += bonus
        
        # Display stats with bonuses
        total_hp = base_hp + equipped_bonuses["hp"]
        total_attack = base_attack + equipped_bonuses["attack"]
        total_defense = base_defense + equipped_bonuses["defense"]
        total_speed = base_speed + equipped_bonuses["speed"]
        total_luck = base_luck + equipped_bonuses["luck"]
        
        self.hp_label.setText(f"HP: {total_hp} ({base_hp} + {equipped_bonuses['hp']})")
        self.attack_label.setText(f"Attack: {total_attack} ({base_attack} + {equipped_bonuses['attack']})")
        self.defense_label.setText(f"Defense: {total_defense} ({base_defense} + {equipped_bonuses['defense']})")
        self.speed_label.setText(f"Speed: {total_speed} ({base_speed} + {equipped_bonuses['speed']})")
        self.luck_label.setText(f"Luck: {total_luck} ({base_luck} + {equipped_bonuses['luck']})")
        
        # Update inventory space
        inventory_count = ItemRepository.get_inventory_count(player.id)
        max_inventory = calculate_inventory_space(player.level)
        self.inventory_space_label.setText(f"Inventory: {inventory_count}/{max_inventory}")
        
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
            self.inventory_table.setItem(row, 1, QTableWidgetItem(item.rarity))
            
            # Bonuses
            bonuses = item.get_stat_bonuses()
            bonuses_str = ", ".join([f"{k}: +{v}" for k, v in bonuses.items()])
            self.inventory_table.setItem(row, 2, QTableWidgetItem(bonuses_str))
            
            # Quantity
            self.inventory_table.setItem(row, 3, QTableWidgetItem(str(quantity)))
            
            # Equipped status
            self.inventory_table.setItem(row, 4, QTableWidgetItem("Yes" if equipped else "No"))
            
            # Actions (Equip/Unequip button)
            action_widget = QWidget()
            action_layout = QHBoxLayout()
            action_layout.setContentsMargins(2, 2, 2, 2)
            
            if equipped:
                unequip_btn = QPushButton("Unequip")
                unequip_btn.clicked.connect(lambda checked, item_id=item.id: self.unequip_item(item_id))
                action_layout.addWidget(unequip_btn)
            else:
                equip_btn = QPushButton("Equip")
                equip_btn.clicked.connect(lambda checked, item_id=item.id: self.equip_item(item_id))
                action_layout.addWidget(equip_btn)
            
            action_widget.setLayout(action_layout)
            self.inventory_table.setCellWidget(row, 5, action_widget)
        
        # Update achievements
        worlds = RepoWorldRepository.get_all()
        completed_quests = sum(1 for w in worlds for q in QuestRepository.get_by_world_id(w.id) if q.status == "completed")
        
        achievements = []
        achievements.append(f"Worlds Discovered: {len(worlds)}")
        achievements.append(f"Quests Completed: {completed_quests}")
        
        self.achievements_label.setText("\n".join(achievements))
    
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
        from ui.widgets.recycler_dialog import RecyclerDialog
        dialog = RecyclerDialog(self)
        dialog.exec()
        # Refresh after closing recycler
        self.refresh()

