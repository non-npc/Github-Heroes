"""
Quest board view for issues and PRs.
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTableWidget, QTableWidgetItem, QComboBox, QMessageBox, QHeaderView
)
from PyQt6.QtCore import Qt, pyqtSignal
from data.repositories import RepoWorldRepository, QuestRepository, EnemyRepository
from game.state import get_game_state
from core.logging_utils import get_logger

logger = get_logger(__name__)

class QuestBoardView(QWidget):
    """
    Quest board showing issues and PRs as quests.
    """
    
    quest_started = pyqtSignal(int)  # quest_id
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        self.refresh_worlds()
    
    def init_ui(self):
        """Initialize UI."""
        layout = QVBoxLayout()
        
        # Title
        title = QLabel("Quest Board")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(title)
        
        # World selector
        world_layout = QHBoxLayout()
        world_layout.addWidget(QLabel("Select World:"))
        self.world_combo = QComboBox()
        self.world_combo.currentIndexChanged.connect(self.on_world_changed)
        world_layout.addWidget(self.world_combo)
        layout.addLayout(world_layout)
        
        # Quests table
        self.quests_table = QTableWidget()
        self.quests_table.setColumnCount(5)
        self.quests_table.setHorizontalHeaderLabels(["Type", "Title", "Difficulty", "Status", "Actions"])
        self.quests_table.horizontalHeader().setStretchLastSection(True)
        self.quests_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        layout.addWidget(self.quests_table)
        
        self.setLayout(layout)
        self.current_world_id = None
    
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
            self.refresh_quests(world_id)
    
    def refresh_quests(self, world_id: int):
        """Refresh quests for selected world."""
        self.quests_table.setRowCount(0)
        quests = QuestRepository.get_by_world_id(world_id)
        
        for quest in quests:
            row = self.quests_table.rowCount()
            self.quests_table.insertRow(row)
            
            # Type
            type_item = QTableWidgetItem(quest.source_type.upper())
            self.quests_table.setItem(row, 0, type_item)
            
            # Title
            title_item = QTableWidgetItem(quest.title)
            self.quests_table.setItem(row, 1, title_item)
            
            # Difficulty
            difficulty_item = QTableWidgetItem(str(quest.difficulty))
            self.quests_table.setItem(row, 2, difficulty_item)
            
            # Status
            status_item = QTableWidgetItem(quest.status)
            self.quests_table.setItem(row, 3, status_item)
            
            # Actions button
            action_btn = QPushButton("Start Quest")
            action_btn.clicked.connect(lambda checked, qid=quest.id: self.on_start_quest(qid))
            if quest.status == "completed":
                action_btn.setEnabled(False)
                action_btn.setText("Completed")
            self.quests_table.setCellWidget(row, 4, action_btn)
    
    def on_start_quest(self, quest_id: int):
        """Handle start quest button."""
        self.quest_started.emit(quest_id)

