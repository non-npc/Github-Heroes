"""
Dungeon view for exploring repository structure.
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTreeWidget, QTreeWidgetItem, QComboBox, QMessageBox, QGroupBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from data.repositories import RepoWorldRepository, DungeonRoomRepository
from game.state import get_game_state
from core.logging_utils import get_logger

logger = get_logger(__name__)

class DungeonView(QWidget):
    """
    Dungeon view showing repository structure as rooms.
    """
    
    room_selected = pyqtSignal(int)  # room_id
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        self.refresh_worlds()
    
    def init_ui(self):
        """Initialize UI."""
        layout = QVBoxLayout()
        
        # Title
        title = QLabel("Dungeon Explorer")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(title)
        
        # World selector
        world_layout = QHBoxLayout()
        world_layout.addWidget(QLabel("Select World:"))
        self.world_combo = QComboBox()
        self.world_combo.currentIndexChanged.connect(self.on_world_changed)
        world_layout.addWidget(self.world_combo)
        layout.addLayout(world_layout)
        
        # Rooms tree
        self.rooms_tree = QTreeWidget()
        self.rooms_tree.setHeaderLabels(["Zone", "File", "Danger", "Loot", "Status"])
        self.rooms_tree.itemClicked.connect(self.on_room_clicked)
        self.rooms_tree.itemDoubleClicked.connect(self.on_room_double_clicked)
        layout.addWidget(self.rooms_tree)
        
        # Room details
        details_group = QGroupBox("Room Details")
        details_layout = QVBoxLayout()
        
        self.details_label = QLabel("Select a room to view details")
        self.details_label.setWordWrap(True)
        details_layout.addWidget(self.details_label)
        
        self.explore_btn = QPushButton("Explore Room")
        self.explore_btn.clicked.connect(self.on_explore_room)
        self.explore_btn.setEnabled(False)
        self.explore_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
                border: none;
                padding: 8px;
                border-radius: 4px;
            }
            QPushButton:hover:enabled {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        details_layout.addWidget(self.explore_btn)
        
        details_group.setLayout(details_layout)
        layout.addWidget(details_group)
        
        self.setLayout(layout)
        self.current_world_id = None
        self.current_room_id = None
    
    def refresh_worlds(self):
        """Refresh world combo box."""
        self.world_combo.clear()
        worlds = RepoWorldRepository.get_all()
        for world in worlds:
            self.world_combo.addItem(world.full_name, world.id)
    
    def on_world_changed(self, index: int):
        """Handle world selection change."""
        if index >= 0:
            world_id = self.world_combo.itemData(index)
            self.current_world_id = world_id
            self.refresh_rooms(world_id)
    
    def refresh_rooms(self, world_id: int):
        """Refresh rooms for selected world."""
        self.rooms_tree.clear()
        rooms = DungeonRoomRepository.get_by_world_id(world_id)
        
        # Group by zone
        zones = {}
        for room in rooms:
            if room.zone_name not in zones:
                zones[room.zone_name] = []
            zones[room.zone_name].append(room)
        
        # Create tree structure
        for zone_name, zone_rooms in zones.items():
            zone_item = QTreeWidgetItem(self.rooms_tree)
            zone_item.setText(0, zone_name)
            zone_item.setExpanded(True)
            
            for room in zone_rooms:
                room_item = QTreeWidgetItem(zone_item)
                room_item.setText(0, zone_name)
                room_item.setText(1, room.file_path.split('/')[-1])
                room_item.setText(2, str(room.danger_level))
                room_item.setText(3, str(room.loot_quality))
                room_item.setText(4, "✓ Explored" if room.visited else "○ Unexplored")
                room_item.setData(0, Qt.ItemDataRole.UserRole, room.id)
    
    def on_room_clicked(self, item: QTreeWidgetItem, column: int):
        """Handle room single click - show details."""
        # Only process if this is a room item (has a parent), not a zone header
        if item.parent() is None:
            # This is a zone header, clear selection
            self.details_label.setText("Select a room to view details")
            self.explore_btn.setEnabled(False)
            self.current_room_id = None
            return
        
        room_id = item.data(0, Qt.ItemDataRole.UserRole)
        if room_id:
            self.current_room_id = room_id
            room = DungeonRoomRepository.get_by_id(room_id)
            if room:
                # Update details display
                details = f"<b>Room: {room.file_path.split('/')[-1]}</b><br><br>"
                details += f"<b>Zone:</b> {room.zone_name}<br>"
                details += f"<b>Danger Level:</b> {room.danger_level}<br>"
                details += f"<b>Loot Quality:</b> {room.loot_quality}<br>"
                details += f"<b>Status:</b> {'✓ Explored' if room.visited else '○ Unexplored'}<br>"
                
                if not room.visited:
                    details += "<br><i>This dungeon contains enemies. Click 'Explore Room' to enter combat.</i>"
                else:
                    details += "<br><i>This dungeon has already been explored.</i>"
                
                self.details_label.setText(details)
                self.explore_btn.setEnabled(not room.visited)
    
    def on_room_double_clicked(self, item: QTreeWidgetItem, column: int):
        """Handle room double click - directly explore if not visited."""
        # Only process if this is a room item (has a parent), not a zone header
        if item.parent() is None:
            return
        
        room_id = item.data(0, Qt.ItemDataRole.UserRole)
        if room_id:
            room = DungeonRoomRepository.get_by_id(room_id)
            if room and not room.visited:
                self.current_room_id = room_id
                self.on_explore_room()
    
    def on_explore_room(self):
        """Handle explore room button."""
        if self.current_room_id:
            self.room_selected.emit(self.current_room_id)

