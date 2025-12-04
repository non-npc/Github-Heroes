"""
Recycler dialog for selling items.
"""

from PyQt6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from github_heroes.core.logging_utils import get_logger
from github_heroes.data.models import ItemRarityXP
from github_heroes.data.repositories import ItemRepository, PlayerRepository
from github_heroes.game.logic import award_xp, bonus_as_string
from github_heroes.game.state import get_game_state

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
        info_label = QLabel(
            "Select items to sell. You'll receive XP based on item rarity."
        )
        layout.addWidget(info_label)

        # Inventory table
        self.inventory_table = QTableWidget()
        self.inventory_table.setColumnCount(5)
        self.inventory_table.setHorizontalHeaderLabels(
            ["Name", "Rarity", "Bonuses", "Quantity", "Sell"]
        )
        self.inventory_table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )

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

        recycle_all_btn = QPushButton("Recycle All")
        recycle_all_btn.clicked.connect(self.recycle_all)
        buttons_layout.addWidget(recycle_all_btn)

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
            # Only show items that are not equipped
            if equipped:
                continue

            row = self.inventory_table.rowCount()
            self.inventory_table.insertRow(row)

            # Name (with equipped indicator)
            self.inventory_table.setItem(row, 0, QTableWidgetItem(item.name))

            # Rarity
            self.inventory_table.setItem(row, 1, QTableWidgetItem(item.rarity.name))

            # Bonuses
            bonuses = item.get_stat_bonuses()
            bonuses_str = bonus_as_string(bonuses)
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
            sell_btn.clicked.connect(
                lambda checked, item_id=item.id, spin=quantity_spin: self.sell_item(
                    item_id, spin.value()
                )
            )
            sell_layout.addWidget(sell_btn)

            sell_widget.setLayout(sell_layout)
            self.inventory_table.setCellWidget(row, 4, sell_widget)

    def sell_item(self, item_id: int, quantity: int):
        """Sell an item."""
        game_state = get_game_state()
        if not game_state.current_player:
            return

        # Delegate to shared recycle logic
        self._recycle_items([(item_id, quantity)], show_per_item_message=True)

    def recycle_all(self):
        """Recycle all non-equipped items in the inventory."""
        game_state = get_game_state()
        if not game_state.current_player:
            return

        inventory = ItemRepository.get_player_inventory(game_state.current_player.id)
        # Build list of (item_id, quantity) for non-equipped items
        items_to_recycle = [
            (item.id, quantity)
            for item, quantity, equipped in inventory
            if not equipped
        ]

        if not items_to_recycle:
            QMessageBox.information(
                self, "Recycler", "No non-equipped items to recycle."
            )
            return

        self._recycle_items(items_to_recycle, show_per_item_message=False)

    def _recycle_items(
        self, items: list[tuple[int, int]], show_per_item_message: bool = False
    ):
        """
        Core recycle logic.
        items: list of (item_id, quantity) tuples.
        show_per_item_message: whether to show a message per item or a single summary.
        """
        game_state = get_game_state()
        if not game_state.current_player:
            return

        total_xp = 0
        total_items = 0
        messages = []

        for item_id, quantity in items:
            item = ItemRepository.get_by_id(item_id)
            if not item or quantity <= 0:
                continue

            try:
                rarity_xp = ItemRarityXP[item.rarity.name].value
            except KeyError:
                rarity_xp = 5
            xp_reward = rarity_xp * quantity

            # Remove from inventory
            removed = ItemRepository.remove_from_inventory(
                game_state.current_player.id, item_id, quantity
            )
            if not removed:
                continue

            total_xp += xp_reward
            total_items += quantity
            if show_per_item_message:
                messages.append(f"Sold {quantity}x {item.name} for {xp_reward} XP!")

        leveled_up = False
        if total_xp > 0:
            leveled_up = award_xp(game_state.current_player, total_xp)
            PlayerRepository.update(game_state.current_player)

        # Refresh display
        self.refresh_inventory()

        # Show messages
        if show_per_item_message and messages:
            # Show last message (or you could join them)
            QMessageBox.information(self, "Item Sold", messages[-1])
        elif not show_per_item_message and total_items > 0:
            QMessageBox.information(
                self,
                "Items Recycled",
                f"Recycled {total_items} items for {total_xp} XP!",
            )

        # Show level-up popup if player leveled up
        if leveled_up:
            level_up_msg = "🎉 LEVEL UP! 🎉\n\n"
            level_up_msg += f"Congratulations, {game_state.current_player.name}!\n"
            level_up_msg += (
                f"You have reached Level {game_state.current_player.level}!\n\n"
            )
            level_up_msg += "Your stats have increased:\n"
            level_up_msg += "• HP: +10\n"
            level_up_msg += "• Attack: +2\n"
            level_up_msg += "• Defense: +1\n"
            level_up_msg += "• Speed: +1\n"
            level_up_msg += "• Luck: +1\n\n"
            level_up_msg += "Keep fighting to become even stronger!"

            QMessageBox.information(self, "Level Up!", level_up_msg)
