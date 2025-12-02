"""
Recycler dialog for selling items.
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QSpinBox, QMessageBox, QHeaderView, QWidget
)
from PyQt6.QtCore import Qt
from data.repositories import ItemRepository
from game.state import get_game_state
from core.logging_utils import get_logger

logger = get_logger(__name__)

class RecyclerDialog(QDialog):
    """
    Dialog for recycling (selling) items.
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Recycler - Sell Items")
        self.setModal(True)
        self.setMinimumWidth(600)
        self.setMinimumHeight(400)
        self.init_ui()
        self.refresh_inventory()
    
    def init_ui(self):
        """Initialize UI."""
        layout = QVBoxLayout()
        
        # Title
        title = QLabel("Recycler - Sell Items for Space")
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(title)
        
        # Info label
        info_label = QLabel("Select items to sell. You'll receive XP based on item rarity.")
        layout.addWidget(info_label)
        
        # Inventory table
        self.inventory_table = QTableWidget()
        self.inventory_table.setColumnCount(5)
        self.inventory_table.setHorizontalHeaderLabels(["Name", "Rarity", "Bonuses", "Quantity", "Sell"])
        self.inventory_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        
        # Set column widths
        header = self.inventory_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        
        layout.addWidget(self.inventory_table)
        
        # Buttons
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        buttons_layout.addWidget(close_btn)
        
        layout.addLayout(buttons_layout)
        
        self.setLayout(layout)
    
    def refresh_inventory(self):
        """Refresh inventory display."""
        self.inventory_table.setRowCount(0)
        
        game_state = get_game_state()
        if not game_state.current_player:
            return
        
        inventory = ItemRepository.get_player_inventory(game_state.current_player.id)
        
        for item, quantity, equipped in inventory:
            row = self.inventory_table.rowCount()
            self.inventory_table.insertRow(row)
            
            # Name (with equipped indicator)
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
            quantity_item = QTableWidgetItem(str(quantity))
            self.inventory_table.setItem(row, 3, quantity_item)
            
            # Sell button
            sell_widget = QWidget()
            sell_layout = QHBoxLayout()
            sell_layout.setContentsMargins(2, 2, 2, 2)
            
            quantity_spin = QSpinBox()
            quantity_spin.setMinimum(1)
            quantity_spin.setMaximum(quantity)
            quantity_spin.setValue(1)
            sell_layout.addWidget(quantity_spin)
            
            sell_btn = QPushButton("Sell")
            sell_btn.clicked.connect(lambda checked, item_id=item.id, spin=quantity_spin: self.sell_item(item_id, spin.value()))
            sell_layout.addWidget(sell_btn)
            
            sell_widget.setLayout(sell_layout)
            self.inventory_table.setCellWidget(row, 4, sell_widget)
    
    def sell_item(self, item_id: int, quantity: int):
        """Sell an item."""
        game_state = get_game_state()
        if not game_state.current_player:
            return
        
        # Get item to calculate XP value
        item = ItemRepository.get_by_id(item_id)
        if not item:
            return
        
        # Calculate XP reward based on rarity
        rarity_xp = {
            "common": 5,
            "uncommon": 10,
            "rare": 25,
            "epic": 50,
            "legendary": 100
        }
        xp_reward = rarity_xp.get(item.rarity, 5) * quantity
        
        # Remove from inventory
        ItemRepository.remove_from_inventory(game_state.current_player.id, item_id, quantity)
        
        # Award XP
        from game.logic import award_xp
        from data.repositories import PlayerRepository
        old_level = game_state.current_player.level
        leveled_up = award_xp(game_state.current_player, xp_reward)
        PlayerRepository.update(game_state.current_player)
        
        # Refresh display
        self.refresh_inventory()
        
        # Show message
        message = f"Sold {quantity}x {item.name} for {xp_reward} XP!"
        QMessageBox.information(self, "Item Sold", message)
        
        # Show level-up popup if player leveled up
        if leveled_up:
            level_up_msg = f"🎉 LEVEL UP! 🎉\n\n"
            level_up_msg += f"Congratulations, {game_state.current_player.name}!\n"
            level_up_msg += f"You have reached Level {game_state.current_player.level}!\n\n"
            level_up_msg += f"Your stats have increased:\n"
            level_up_msg += f"• HP: +10\n"
            level_up_msg += f"• Attack: +2\n"
            level_up_msg += f"• Defense: +1\n"
            level_up_msg += f"• Speed: +1\n"
            level_up_msg += f"• Luck: +1\n\n"
            level_up_msg += f"Keep fighting to become even stronger!"
            
            QMessageBox.information(self, "Level Up!", level_up_msg)

