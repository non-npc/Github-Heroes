"""
Main window for Github Heroes.
"""
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QStackedWidget, QMenuBar,
    QToolBar, QStatusBar, QMessageBox, QDialog, QDialogButtonBox,
    QLabel, QLineEdit, QPushButton, QComboBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QAction, QIcon, QPixmap
from core.config import DEFAULT_WINDOW_WIDTH, DEFAULT_WINDOW_HEIGHT, APP_ICON_ICO, APP_ICON_PNG, APP_VERSION
from core.logging_utils import get_logger
from data.database import get_db
from data.repositories import PlayerRepository
from data.models import Player
from game.state import get_game_state
from game.generators import build_repo_world
from github.scraper import GitHubScraper
from ui.widgets.status_bar import GameStatusBar
from ui.widgets.search_panel import SearchPanel
from ui.widgets.map_view import MapView
from ui.widgets.quest_board import QuestBoardView
from ui.widgets.dungeon_view import DungeonView
from ui.widgets.player_view import PlayerView
from ui.widgets.combat_dialog import CombatDialog
from ui.widgets.progress_dialog import ScrapingProgressDialog
from data.repositories import (
    RepoWorldRepository, QuestRepository, EnemyRepository, DungeonRoomRepository
)
from game.logic import handle_victory

logger = get_logger(__name__)

class ScrapingThread(QThread):
    """Thread for processing GitHub data."""
    
    finished = pyqtSignal(object)  # RepoWorld or None
    error = pyqtSignal(str)
    progress = pyqtSignal(int, str)  # value, status message
    
    def __init__(self, owner: str, repo: str, scraper: GitHubScraper):
        super().__init__()
        self.owner = owner
        self.repo = repo
        self.scraper = scraper
    
    def run(self):
        """Run processing in background."""
        try:
            world = build_repo_world(self.owner, self.repo, self.scraper, self.progress_callback)
            self.finished.emit(world)
        except Exception as e:
            logger.error(f"Error in processing thread: {e}", exc_info=True)
            self.error.emit(str(e))
    
    def progress_callback(self, value: int, status: str):
        """Callback for progress updates."""
        self.progress.emit(value, status)

class NewPlayerDialog(QDialog):
    """Dialog for creating a new player."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("New Player")
        self.setModal(True)
        self.setMinimumWidth(600)
        self.setMinimumHeight(500)
        
        layout = QVBoxLayout()
        
        name_label = QLabel("Player Name:")
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Enter your name")
        layout.addWidget(name_label)
        layout.addWidget(self.name_input)
        
        class_label = QLabel("Class:")
        self.class_combo = QComboBox()
        from core.config import PLAYER_CLASSES
        self.class_combo.addItems(PLAYER_CLASSES)
        self.class_combo.setCurrentIndex(0)  # Default to first class
        layout.addWidget(class_label)
        layout.addWidget(self.class_combo)
        
        # Player image selector
        from ui.widgets.player_image_selector import PlayerImageSelector
        self.image_selector = PlayerImageSelector()
        self.image_selector.image_selected.connect(self.on_image_selected)
        layout.addWidget(self.image_selector)
        
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
        self.setLayout(layout)
        self.selected_image_id = None
    
    def on_image_selected(self, image_id: int):
        """Handle image selection."""
        self.selected_image_id = image_id
    
    def get_player_data(self):
        """Get player data from dialog."""
        from core.config import PLAYER_CLASSES
        selected_class = self.class_combo.currentText()
        return {
            "name": self.name_input.text().strip() or "Hero",
            "player_class": selected_class if selected_class in PLAYER_CLASSES else PLAYER_CLASSES[0],
            "player_image_id": self.selected_image_id
        }

class MainWindow(QMainWindow):
    """
    Main application window.
    """
    
    def __init__(self):
        super().__init__()
        self.scraper = GitHubScraper()
        self.scraping_thread = None
        self.progress_dialog = None
        self.init_ui()
        self.load_settings()
        self.check_player()
        self.check_repositories()
    
    def init_ui(self):
        """Initialize UI."""
        self.setWindowTitle("Github Heroes")
        self.setGeometry(100, 100, DEFAULT_WINDOW_WIDTH, DEFAULT_WINDOW_HEIGHT)
        
        # Set window icon (prefer ICO on Windows, PNG otherwise)
        import sys
        if sys.platform == "win32" and APP_ICON_ICO.exists():
            self.setWindowIcon(QIcon(str(APP_ICON_ICO)))
        elif APP_ICON_PNG.exists():
            self.setWindowIcon(QIcon(str(APP_ICON_PNG)))
        
        # Menu bar
        self.create_menu_bar()
        
        # Toolbar
        self.create_toolbar()
        
        # Central widget with stacked views
        central_widget = QWidget()
        central_layout = QVBoxLayout()
        
        self.stacked_widget = QStackedWidget()
        
        # Create views
        self.map_view = MapView()
        self.map_view.world_selected.connect(self.on_world_selected)
        self.map_view.enter_dungeon.connect(self.on_enter_dungeon)
        self.map_view.open_quest_board.connect(self.on_open_quest_board)
        self.map_view.refresh_world.connect(self.on_refresh_world)
        self.stacked_widget.addWidget(self.map_view)
        
        self.quest_board = QuestBoardView()
        self.quest_board.quest_started.connect(self.on_start_quest)
        self.stacked_widget.addWidget(self.quest_board)
        
        self.dungeon_view = DungeonView()
        self.dungeon_view.room_selected.connect(self.on_room_selected)
        self.stacked_widget.addWidget(self.dungeon_view)
        
        self.player_view = PlayerView()
        self.stacked_widget.addWidget(self.player_view)
        
        # Search panel (dockable)
        self.search_panel = SearchPanel()
        self.search_panel.repo_selected.connect(self.on_repo_selected)
        search_dock = self.addDockWidget(
            Qt.DockWidgetArea.RightDockWidgetArea,
            self.create_dock_widget("Add Repository", self.search_panel)
        )
        
        central_layout.addWidget(self.stacked_widget)
        central_widget.setLayout(central_layout)
        self.setCentralWidget(central_widget)
        
        # Status bar
        self.status_bar = GameStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.set_status("Ready")
    
    def create_menu_bar(self):
        """Create menu bar."""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("File")
        
        settings_action = QAction("Settings", self)
        settings_action.triggered.connect(self.show_settings)
        file_menu.addAction(settings_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Player menu
        player_menu = menubar.addMenu("Player")
        
        new_game_action = QAction("New Game", self)
        new_game_action.triggered.connect(self.new_game)
        player_menu.addAction(new_game_action)
        
        load_player_action = QAction("Load Player", self)
        load_player_action.triggered.connect(self.load_player_dialog)
        player_menu.addAction(load_player_action)
        
        # View menu
        view_menu = menubar.addMenu("View")
        
        map_action = QAction("World Map", self)
        map_action.triggered.connect(lambda: self.stacked_widget.setCurrentIndex(0))
        view_menu.addAction(map_action)
        
        quest_action = QAction("Quest Board", self)
        quest_action.triggered.connect(lambda: self.stacked_widget.setCurrentIndex(1))
        view_menu.addAction(quest_action)
        
        dungeon_action = QAction("Dungeon View", self)
        dungeon_action.triggered.connect(lambda: self.stacked_widget.setCurrentIndex(2))
        view_menu.addAction(dungeon_action)
        
        player_action = QAction("Player Profile", self)
        player_action.triggered.connect(lambda: self.stacked_widget.setCurrentIndex(3))
        view_menu.addAction(player_action)
        
        # Help menu
        help_menu = menubar.addMenu("Help")
        
        about_action = QAction("About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def create_toolbar(self):
        """Create toolbar."""
        toolbar = QToolBar()
        self.addToolBar(toolbar)
        
        map_action = QAction("Map", self)
        map_action.triggered.connect(lambda: self.stacked_widget.setCurrentIndex(0))
        toolbar.addAction(map_action)
        
        quest_action = QAction("Quests", self)
        quest_action.triggered.connect(lambda: self.stacked_widget.setCurrentIndex(1))
        toolbar.addAction(quest_action)
        
        dungeon_action = QAction("Dungeon", self)
        dungeon_action.triggered.connect(lambda: self.stacked_widget.setCurrentIndex(2))
        toolbar.addAction(dungeon_action)
        
        player_action = QAction("Player", self)
        player_action.triggered.connect(lambda: self.stacked_widget.setCurrentIndex(3))
        toolbar.addAction(player_action)
    
    def create_dock_widget(self, title: str, widget: QWidget):
        """Create a dock widget."""
        from PyQt6.QtWidgets import QDockWidget
        dock = QDockWidget(title, self)
        dock.setWidget(widget)
        return dock
    
    def check_player(self):
        """Check if player exists, prompt to create if not."""
        game_state = get_game_state()
        db = get_db()
        
        last_player_id = db.get_setting("last_player_id")
        if last_player_id:
            if game_state.load_player(int(last_player_id)):
                self.status_bar.set_status(f"Loaded player: {game_state.current_player.name}")
                self.player_view.refresh()
                return
        
        # No player found, prompt to create
        self.new_game()
    
    def check_repositories(self):
        """Check if repositories exist, show message if empty."""
        worlds = RepoWorldRepository.get_all()
        if not worlds:
            QMessageBox.information(
                self,
                "Welcome to Github Heroes!",
                "Welcome to Github Heroes!\n\n"
                "To begin your adventure, you need to add a GitHub repository.\n\n"
                "You can add a repository by:\n"
                "• Pasting a repository URL in the 'Add Repository' panel on the right\n"
                "• Using the search function to find repositories\n\n"
                "Once you add a repository, it will be converted into a dungeon world "
                "with enemies, quests, and loot for you to explore!\n\n"
                "Get started by adding your first repository now!"
            )
    
    def new_game(self):
        """Create a new game."""
        dialog = NewPlayerDialog(self)
        if dialog.exec():
            data = dialog.get_player_data()
            player = Player(
                name=data["name"],
                player_class=data.get("player_class"),
                player_image_id=data.get("player_image_id")
            )
            player = PlayerRepository.create(player)
            
            game_state = get_game_state()
            game_state.set_player(player)
            
            db = get_db()
            db.set_setting("last_player_id", str(player.id))
            
            self.status_bar.set_status(f"Created new player: {player.name}")
            self.player_view.refresh()
    
    def load_player_dialog(self):
        """Show dialog to load a player."""
        players = PlayerRepository.get_all()
        if not players:
            QMessageBox.information(self, "No Players", "No players found. Create a new game first.")
            return
        
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QListWidget, QDialogButtonBox
        dialog = QDialog(self)
        dialog.setWindowTitle("Load Player")
        layout = QVBoxLayout()
        
        list_widget = QListWidget()
        for player in players:
            list_widget.addItem(f"{player.name} (Level {player.level})")
        layout.addWidget(list_widget)
        
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        
        dialog.setLayout(layout)
        
        if dialog.exec():
            selected = list_widget.currentRow()
            if selected >= 0:
                player = players[selected]
                game_state = get_game_state()
                game_state.set_player(player)
                
                db = get_db()
                db.set_setting("last_player_id", str(player.id))
                
                self.status_bar.set_status(f"Loaded player: {player.name}")
                self.player_view.refresh()
    
    def on_repo_selected(self, owner: str, repo: str):
        """Handle repository selection from search panel."""
        self.status_bar.set_status(f"Processing {owner}/{repo}...")
        self.status_bar.set_connection_status(False)
        
        # Show progress dialog
        self.progress_dialog = ScrapingProgressDialog(f"{owner}/{repo}", self)
        self.progress_dialog.show()
        
        # Start processing in background thread
        self.scraping_thread = ScrapingThread(owner, repo, self.scraper)
        self.scraping_thread.finished.connect(self.on_scraping_finished)
        self.scraping_thread.error.connect(self.on_scraping_error)
        self.scraping_thread.progress.connect(self.on_scraping_progress)
        self.scraping_thread.start()
    
    def on_scraping_progress(self, value: int, status: str):
        """Handle processing progress updates."""
        if self.progress_dialog:
            self.progress_dialog.update_progress(value, status)
    
    def on_scraping_finished(self, world):
        """Handle processing completion."""
        # Close progress dialog
        if self.progress_dialog:
            self.progress_dialog.close()
            self.progress_dialog = None
        
        self.status_bar.set_connection_status(True)
        if world:
            self.status_bar.set_status(f"Successfully added {world.full_name}")
            self.map_view.refresh_worlds()
            self.quest_board.refresh_worlds()
            self.dungeon_view.refresh_worlds()
            
            # Check achievements for repository addition
            game_state = get_game_state()
            if game_state.current_player:
                from game.achievements import check_achievements
                from game.achievements import ACHIEVEMENTS
                context = {"repository_added": True}
                newly_unlocked = check_achievements(game_state.current_player, context)
                if newly_unlocked:
                    achievement_names = [ACHIEVEMENTS[ach_id]["name"] for ach_id in newly_unlocked if ach_id in ACHIEVEMENTS]
                    if achievement_names:
                        ach_msg = "🏆 Achievement Unlocked!\n\n" + "\n".join(f"• {name}" for name in achievement_names)
                        QMessageBox.information(self, "Achievement Unlocked!", ach_msg)
                self.player_view.refresh()
        else:
            self.status_bar.set_status("Failed to process repository")
            QMessageBox.warning(self, "Error", "Failed to process repository. Please check the URL and try again.")
    
    def on_scraping_error(self, error_msg: str):
        """Handle processing error."""
        # Close progress dialog
        if self.progress_dialog:
            self.progress_dialog.close()
            self.progress_dialog = None
        
        self.status_bar.set_connection_status(False)
        self.status_bar.set_status(f"Processing error: {error_msg}")
        QMessageBox.warning(self, "Error", f"Processing failed: {error_msg}")
    
    def on_world_selected(self, world_id: int):
        """Handle world selection."""
        game_state = get_game_state()
        game_state.load_world(world_id)
    
    def on_enter_dungeon(self, world_id: int):
        """Handle enter dungeon."""
        # Auto-refresh if enabled
        if self.should_auto_refresh():
            world = RepoWorldRepository.get_by_id(world_id)
            if world:
                self.on_repo_selected(world.owner, world.repo)
                # Wait for processing to complete before switching view
                # (This is a simple implementation - in production you'd use signals)
                return
        
        self.stacked_widget.setCurrentIndex(2)  # Dungeon view
        self.dungeon_view.refresh_worlds()
        # Find and select the world
        for i in range(self.dungeon_view.world_combo.count()):
            if self.dungeon_view.world_combo.itemData(i) == world_id:
                self.dungeon_view.world_combo.setCurrentIndex(i)
                break
    
    def on_open_quest_board(self, world_id: int):
        """Handle open quest board."""
        self.stacked_widget.setCurrentIndex(1)  # Quest board
        self.quest_board.refresh_worlds()
        # Find and select the world
        for i in range(self.quest_board.world_combo.count()):
            if self.quest_board.world_combo.itemData(i) == world_id:
                self.quest_board.world_combo.setCurrentIndex(i)
                break
    
    def on_refresh_world(self, world_id: int):
        """Handle refresh world."""
        world = RepoWorldRepository.get_by_id(world_id)
        if world:
            self.on_repo_selected(world.owner, world.repo)
    
    def should_auto_refresh(self) -> bool:
        """Check if auto-refresh is enabled."""
        db = get_db()
        auto_refresh = db.get_setting("auto_refresh", "false")
        return auto_refresh.lower() == "true"
    
    def on_start_quest(self, quest_id: int):
        """Handle quest start."""
        quest = QuestRepository.get_by_id(quest_id)
        if not quest:
            QMessageBox.warning(self, "Error", "Quest not found.")
            return
        
        # Find enemy for this quest
        enemies = EnemyRepository.get_by_world_id(quest.world_id)
        enemy = None
        
        if quest.source_type == "pr":
            # Find boss enemy for PR
            for e in enemies:
                if e.is_boss and str(quest.source_number) in e.name:
                    enemy = e
                    break
        
        if not enemy:
            # Use main enemy as fallback
            world = RepoWorldRepository.get_by_id(quest.world_id)
            if world and world.main_enemy_id:
                enemy = EnemyRepository.get_by_id(world.main_enemy_id)
        
        if enemy:
            game_state = get_game_state()
            if game_state.current_player:
                dialog = CombatDialog(game_state.current_player, enemy, parent=self)
                dialog.combat_ended.connect(lambda result, data: self.on_combat_ended(quest_id, result, data))
                dialog.exec()
            else:
                QMessageBox.warning(self, "No Player", "Please create or load a player first.")
        else:
            QMessageBox.warning(self, "Error", "Could not find enemy for this quest.")
    
    def on_room_selected(self, room_id: int):
        """Handle room selection."""
        from data.repositories import DungeonRoomRepository
        from game.generators import generate_room_enemy
        room = DungeonRoomRepository.get_by_id(room_id)
        
        if not room:
            QMessageBox.warning(self, "Error", "Room not found.")
            return
        
        if not room.visited:
            game_state = get_game_state()
            if not game_state.current_player:
                QMessageBox.warning(self, "No Player", "Please create or load a player first.")
                return
            
            # Restore player HP before combat
            from game.logic import restore_player_hp
            restore_player_hp(game_state.current_player)
            
            # Generate room-specific enemy scaled to danger level
            world = RepoWorldRepository.get_by_id(room.world_id)
            base_enemy = None
            if world and world.main_enemy_id:
                base_enemy = EnemyRepository.get_by_id(world.main_enemy_id)
            
            # Generate scaled enemy for this room
            enemy = generate_room_enemy(room.danger_level, room.world_id, base_enemy)
            
            dialog = CombatDialog(game_state.current_player, enemy, room.loot_quality, parent=self)
            dialog.combat_ended.connect(lambda result, data: self.on_room_combat_ended(room_id, result, data))
            dialog.exec()
    
    def on_combat_ended(self, quest_id: int, result: str, data: dict):
        """Handle combat end for quest."""
        if result == "victory":
            quest = QuestRepository.get_by_id(quest_id)
            if quest:
                quest.status = "completed"
                QuestRepository.update(quest)
                
                # Track quest completion stats
                from data.repositories import PlayerStatsRepository
                from game.achievements import check_achievements
                game_state = get_game_state()
                if game_state.current_player:
                    PlayerStatsRepository.increment_stat(game_state.current_player.id, "quests_completed", 1)
                    if quest.source_type == "issue":
                        PlayerStatsRepository.increment_stat(game_state.current_player.id, "issues_completed", 1)
                    elif quest.source_type == "pr":
                        PlayerStatsRepository.increment_stat(game_state.current_player.id, "prs_completed", 1)
                    
                    # Check achievements
                    newly_unlocked = check_achievements(game_state.current_player)
                    if newly_unlocked:
                        from game.achievements import ACHIEVEMENTS
                        achievement_names = [ACHIEVEMENTS[ach_id]["name"] for ach_id in newly_unlocked if ach_id in ACHIEVEMENTS]
                        if achievement_names:
                            ach_msg = "🏆 Achievement Unlocked!\n\n" + "\n".join(f"• {name}" for name in achievement_names)
                            from PyQt6.QtWidgets import QMessageBox
                            QMessageBox.information(self, "Achievement Unlocked!", ach_msg)
                
                self.quest_board.refresh_quests(quest.world_id)
                self.map_view.refresh_worlds()  # Update quest/room counts
        
        self.player_view.refresh()
    
    def on_room_combat_ended(self, room_id: int, result: str, data: dict):
        """Handle combat end for room."""
        if result == "victory":
            from data.repositories import DungeonRoomRepository, PlayerStatsRepository
            from game.achievements import check_achievements
            game_state = get_game_state()
            room = DungeonRoomRepository.get_by_id(room_id)
            if room:
                if not room.visited and game_state.current_player:
                    PlayerStatsRepository.increment_stat(game_state.current_player.id, "rooms_explored", 1)
                room.visited = True
                DungeonRoomRepository.update(room)
                
                # Check for zone completion achievement
                if game_state.current_player:
                    newly_unlocked = check_achievements(game_state.current_player)
                    if newly_unlocked:
                        from game.achievements import ACHIEVEMENTS
                        achievement_names = [ACHIEVEMENTS[ach_id]["name"] for ach_id in newly_unlocked if ach_id in ACHIEVEMENTS]
                        if achievement_names:
                            ach_msg = "🏆 Achievement Unlocked!\n\n" + "\n".join(f"• {name}" for name in achievement_names)
                            from PyQt6.QtWidgets import QMessageBox
                            QMessageBox.information(self, "Achievement Unlocked!", ach_msg)
                
                self.dungeon_view.refresh_rooms(room.world_id)
                self.map_view.refresh_worlds()  # Update quest/room counts
        
        self.player_view.refresh()
    
    def show_settings(self):
        """Show settings dialog."""
        from ui.widgets.settings_dialog import SettingsDialog
        dialog = SettingsDialog(self)
        if dialog.exec():
            # Reload scraper with new token if changed
            db = get_db()
            token = db.get_setting("github_token", "")
            self.scraper = GitHubScraper(api_token=token if token else None)
            logger.info("Settings updated, processor reloaded")
    
    def show_about(self):
        """Show about dialog."""
        about_box = QMessageBox(self)
        about_box.setWindowTitle("About Github Heroes")
        about_box.setText(
            f"Github Heroes v{APP_VERSION}\n\n"
            "Game concept by non-npc"
        )
        
        # Set the application icon
        import sys
        icon_path = None
        if sys.platform == "win32" and APP_ICON_ICO.exists():
            icon_path = APP_ICON_ICO
        elif APP_ICON_PNG.exists():
            icon_path = APP_ICON_PNG
        
        if icon_path:
            pixmap = QPixmap(str(icon_path))
            # Scale the icon to a reasonable size for the dialog (e.g., 64x64 or 128x128)
            scaled_pixmap = pixmap.scaled(128, 128, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            about_box.setIconPixmap(scaled_pixmap)
        else:
            # Fallback to information icon if app icon not found
            about_box.setIcon(QMessageBox.Icon.Information)
        
        about_box.exec()
    
    def load_settings(self):
        """Load window settings."""
        db = get_db()
        width = db.get_setting("window_width")
        height = db.get_setting("window_height")
        x = db.get_setting("window_x")
        y = db.get_setting("window_y")
        
        if width and height:
            self.resize(int(width), int(height))
        if x and y:
            self.move(int(x), int(y))
    
    def save_settings(self):
        """Save window settings."""
        db = get_db()
        geometry = self.geometry()
        db.set_setting("window_width", str(geometry.width()))
        db.set_setting("window_height", str(geometry.height()))
        db.set_setting("window_x", str(geometry.x()))
        db.set_setting("window_y", str(geometry.y()))
    
    def closeEvent(self, event):
        """Handle window close event."""
        self.save_settings()
        event.accept()

