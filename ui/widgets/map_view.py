"""
World map view showing discovered repositories.
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QListWidget, QListWidgetItem, QMessageBox, QGroupBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from data.repositories import RepoWorldRepository, EnemyRepository, QuestRepository, DungeonRoomRepository
from core.logging_utils import get_logger

logger = get_logger(__name__)

class MapView(QWidget):
    """
    World map view showing repo worlds.
    """
    
    world_selected = pyqtSignal(int)  # world_id
    enter_dungeon = pyqtSignal(int)  # world_id
    open_quest_board = pyqtSignal(int)  # world_id
    refresh_world = pyqtSignal(int)  # world_id
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        self.refresh_worlds()
    
    def init_ui(self):
        """Initialize UI."""
        layout = QVBoxLayout()
        
        # Title
        title = QLabel("World Map")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(title)
        
        # Worlds list
        self.worlds_list = QListWidget()
        self.worlds_list.itemClicked.connect(self.on_world_selected)
        layout.addWidget(self.worlds_list)
        
        # Details panel
        details_group = QGroupBox("World Details")
        details_layout = QHBoxLayout()  # Changed to horizontal layout for 3 columns
        
        # Create 3 column widgets
        self.stats_label = QLabel("Select a world to view details")
        self.stats_label.setWordWrap(True)
        self.stats_label.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        self.content_label = QLabel("")
        self.content_label.setWordWrap(True)
        self.content_label.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        self.enemy_label = QLabel("")
        self.enemy_label.setWordWrap(True)
        self.enemy_label.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        details_layout.addWidget(self.stats_label, stretch=1)
        details_layout.addWidget(self.content_label, stretch=1)
        details_layout.addWidget(self.enemy_label, stretch=1)
        
        # Action buttons - stacked vertically
        buttons_layout = QVBoxLayout()
        
        self.enter_btn = QPushButton("Enter Dungeon")
        self.enter_btn.clicked.connect(self.on_enter_dungeon)
        self.enter_btn.setEnabled(False)
        self.enter_btn.setStyleSheet("""
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
        buttons_layout.addWidget(self.enter_btn)
        
        self.quest_btn = QPushButton("Quest Board")
        self.quest_btn.clicked.connect(self.on_open_quest_board)
        self.quest_btn.setEnabled(False)
        buttons_layout.addWidget(self.quest_btn)
        
        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.clicked.connect(self.on_refresh_world)
        self.refresh_btn.setEnabled(False)
        buttons_layout.addWidget(self.refresh_btn)
        
        details_layout.addLayout(buttons_layout)
        details_group.setLayout(details_layout)
        layout.addWidget(details_group)
        
        self.setLayout(layout)
        self.current_world_id = None
    
    def refresh_worlds(self):
        """Refresh the list of worlds."""
        self.worlds_list.clear()
        worlds = RepoWorldRepository.get_all()
        
        # Clear details when refreshing
        if not worlds:
            self.stats_label.setText("Select a world to view details")
            self.content_label.setText("")
            self.enemy_label.setText("")
        
        for world in worlds:
            # Get main enemy
            main_enemy = None
            if world.main_enemy_id:
                main_enemy = EnemyRepository.get_by_id(world.main_enemy_id)
            
            enemy_level = main_enemy.level if main_enemy else 0
            enemy_name = main_enemy.name if main_enemy else "Unknown"
            
            # Get quest and room counts
            quests = QuestRepository.get_by_world_id(world.id)
            rooms = DungeonRoomRepository.get_by_world_id(world.id)
            quest_count = len(quests)
            room_count = len(rooms)
            
            item_text = f"{world.full_name}\n"
            item_text += f"⭐ {world.stars} | 🍴 {world.forks} | 👁 {world.watchers}\n"
            item_text += f"Boss: {enemy_name} (Lv.{enemy_level})\n"
            item_text += f"📜 {quest_count} Quests | 🚪 {room_count} Dungeons"
            
            item = QListWidgetItem(item_text)
            item.setData(Qt.ItemDataRole.UserRole, world.id)
            self.worlds_list.addItem(item)
    
    def on_world_selected(self, item: QListWidgetItem):
        """Handle world selection."""
        world_id = item.data(Qt.ItemDataRole.UserRole)
        self.current_world_id = world_id
        
        world = RepoWorldRepository.get_by_id(world_id)
        if not world:
            return
        
        # Get main enemy
        main_enemy = None
        if world.main_enemy_id:
            main_enemy = EnemyRepository.get_by_id(world.main_enemy_id)
        
        # Get quest and room counts
        quests = QuestRepository.get_by_world_id(world_id)
        rooms = DungeonRoomRepository.get_by_world_id(world_id)
        quest_count = len(quests)
        room_count = len(rooms)
        completed_quests = sum(1 for q in quests if q.status == "completed")
        explored_rooms = sum(1 for r in rooms if r.visited)
        
        # Build stats column text
        stats_text = f"<b>Stats:</b><br>"
        stats_text += f"Stars: {world.stars}<br>"
        stats_text += f"Forks: {world.forks}<br>"
        stats_text += f"Watchers: {world.watchers}<br>"
        stats_text += f"Health State: {world.health_state or 'Unknown'}<br>"
        stats_text += f"Activity Score: {world.activity_score}<br>"
        
        # Build content column text
        content_text = f"<b>Content:</b><br>"
        content_text += f"📜 Quests: {quest_count}<br>"
        content_text += f"&nbsp;&nbsp;({completed_quests} completed)<br>"
        content_text += f"🚪 Dungeons: {room_count}<br>"
        content_text += f"&nbsp;&nbsp;({explored_rooms} explored)<br>"
        
        # Build enemy column text
        if main_enemy:
            enemy_text = f"<b>Main Enemy:</b><br>"
            enemy_text += f"Name: {main_enemy.name}<br>"
            enemy_text += f"Level: {main_enemy.level}<br>"
            enemy_text += f"HP: {main_enemy.hp}<br>"
            enemy_text += f"Attack: {main_enemy.attack}<br>"
            enemy_text += f"Defense: {main_enemy.defense}<br>"
        else:
            enemy_text = f"<b>Main Enemy:</b><br>"
            enemy_text += f"No enemy data"
        
        self.stats_label.setText(stats_text)
        self.content_label.setText(content_text)
        self.enemy_label.setText(enemy_text)
        self.enter_btn.setEnabled(True)
        self.quest_btn.setEnabled(True)
        self.refresh_btn.setEnabled(True)
    
    def on_enter_dungeon(self):
        """Handle enter dungeon button."""
        if self.current_world_id:
            self.enter_dungeon.emit(self.current_world_id)
    
    def on_open_quest_board(self):
        """Handle open quest board button."""
        if self.current_world_id:
            self.open_quest_board.emit(self.current_world_id)
    
    def on_refresh_world(self):
        """Handle refresh world button."""
        if self.current_world_id:
            self.refresh_world.emit(self.current_world_id)

