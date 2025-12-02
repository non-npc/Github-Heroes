"""
World map view showing discovered repositories.
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QListWidget, QListWidgetItem, QMessageBox, QGroupBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from data.repositories import RepoWorldRepository, EnemyRepository
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
        details_layout = QVBoxLayout()
        
        self.details_label = QLabel("Select a world to view details")
        self.details_label.setWordWrap(True)
        details_layout.addWidget(self.details_label)
        
        # Action buttons
        buttons_layout = QHBoxLayout()
        
        self.enter_btn = QPushButton("Enter Dungeon")
        self.enter_btn.clicked.connect(self.on_enter_dungeon)
        self.enter_btn.setEnabled(False)
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
        
        for world in worlds:
            # Get main enemy
            main_enemy = None
            if world.main_enemy_id:
                main_enemy = EnemyRepository.get_by_id(world.main_enemy_id)
            
            enemy_level = main_enemy.level if main_enemy else 0
            enemy_name = main_enemy.name if main_enemy else "Unknown"
            
            item_text = f"{world.full_name}\n"
            item_text += f"⭐ {world.stars} | 🍴 {world.forks} | 👁 {world.watchers}\n"
            item_text += f"Boss: {enemy_name} (Lv.{enemy_level})"
            
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
        
        # Build details text
        details = f"<b>{world.full_name}</b><br><br>"
        details += f"<b>Stats:</b><br>"
        details += f"Stars: {world.stars}<br>"
        details += f"Forks: {world.forks}<br>"
        details += f"Watchers: {world.watchers}<br>"
        details += f"Health State: {world.health_state or 'Unknown'}<br>"
        details += f"Activity Score: {world.activity_score}<br><br>"
        
        if main_enemy:
            details += f"<b>Main Enemy:</b><br>"
            details += f"Name: {main_enemy.name}<br>"
            details += f"Level: {main_enemy.level}<br>"
            details += f"HP: {main_enemy.hp}<br>"
            details += f"Attack: {main_enemy.attack}<br>"
            details += f"Defense: {main_enemy.defense}<br>"
        
        self.details_label.setText(details)
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

