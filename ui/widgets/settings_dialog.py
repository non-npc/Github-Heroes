"""
Settings dialog for Github Heroes.
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QCheckBox, QSpinBox, QGroupBox, QDialogButtonBox, QMessageBox
)
from PyQt6.QtCore import Qt
from data.database import get_db
from core.logging_utils import get_logger

logger = get_logger(__name__)

class SettingsDialog(QDialog):
    """
    Settings dialog for application configuration.
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setModal(True)
        self.setMinimumWidth(500)
        self.init_ui()
        self.load_settings()
    
    def init_ui(self):
        """Initialize UI."""
        layout = QVBoxLayout()
        
        # GitHub Settings
        github_group = QGroupBox("GitHub Settings")
        github_layout = QVBoxLayout()
        
        # API Token
        token_layout = QVBoxLayout()
        token_label = QLabel("GitHub API Token (optional):")
        token_label.setToolTip("Optional GitHub API token for higher rate limits and extended metadata")
        token_layout.addWidget(token_label)
        
        token_input_layout = QHBoxLayout()
        self.token_input = QLineEdit()
        self.token_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.token_input.setPlaceholderText("Enter your GitHub personal access token")
        token_input_layout.addWidget(self.token_input)
        
        show_token_btn = QPushButton("Show")
        show_token_btn.setCheckable(True)
        show_token_btn.toggled.connect(self.toggle_token_visibility)
        token_input_layout.addWidget(show_token_btn)
        
        token_layout.addLayout(token_input_layout)
        github_layout.addLayout(token_layout)
        
        # Default Branch
        branch_layout = QVBoxLayout()
        branch_label = QLabel("Default Branch Override (optional):")
        branch_label.setToolTip("Override automatic branch detection (main/master). Leave empty for auto-detection.")
        branch_layout.addWidget(branch_label)
        
        self.branch_input = QLineEdit()
        self.branch_input.setPlaceholderText("e.g., main, master, develop")
        branch_layout.addWidget(self.branch_input)
        github_layout.addLayout(branch_layout)
        
        github_group.setLayout(github_layout)
        layout.addWidget(github_group)
        
        # Game Settings
        game_group = QGroupBox("Game Settings")
        game_layout = QVBoxLayout()
        
        # Auto-refresh
        self.auto_refresh_checkbox = QCheckBox("Auto-refresh repo data on enter")
        self.auto_refresh_checkbox.setToolTip("Automatically refresh repository data when entering a dungeon")
        game_layout.addWidget(self.auto_refresh_checkbox)
        
        # Combat text speed
        combat_speed_layout = QHBoxLayout()
        combat_speed_label = QLabel("Combat Text Speed (ms delay):")
        combat_speed_label.setToolTip("Delay between combat messages (lower = faster)")
        combat_speed_layout.addWidget(combat_speed_label)
        
        self.combat_speed_spin = QSpinBox()
        self.combat_speed_spin.setMinimum(0)
        self.combat_speed_spin.setMaximum(2000)
        self.combat_speed_spin.setSuffix(" ms")
        self.combat_speed_spin.setToolTip("0 = instant, higher = slower")
        combat_speed_layout.addWidget(self.combat_speed_spin)
        combat_speed_layout.addStretch()
        
        game_layout.addLayout(combat_speed_layout)
        
        game_group.setLayout(game_layout)
        layout.addWidget(game_group)
        
        # Database Settings
        db_group = QGroupBox("Database")
        db_layout = QVBoxLayout()
        
        reset_db_label = QLabel("Reset all game data (players, worlds, items, etc.)")
        reset_db_label.setWordWrap(True)
        db_layout.addWidget(reset_db_label)
        
        reset_db_btn = QPushButton("Reset Database")
        reset_db_btn.setStyleSheet("background-color: #d32f2f; color: white; font-weight: bold;")
        reset_db_btn.setToolTip("WARNING: This will delete all game data including players, worlds, and items!")
        reset_db_btn.clicked.connect(self.reset_database)
        db_layout.addWidget(reset_db_btn)
        
        db_group.setLayout(db_layout)
        layout.addWidget(db_group)
        
        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel | QDialogButtonBox.StandardButton.RestoreDefaults
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        buttons.button(QDialogButtonBox.StandardButton.RestoreDefaults).clicked.connect(self.restore_defaults)
        layout.addWidget(buttons)
        
        self.setLayout(layout)
    
    def toggle_token_visibility(self, checked: bool):
        """Toggle token visibility."""
        if checked:
            self.token_input.setEchoMode(QLineEdit.EchoMode.Normal)
            self.sender().setText("Hide")
        else:
            self.token_input.setEchoMode(QLineEdit.EchoMode.Password)
            self.sender().setText("Show")
    
    def load_settings(self):
        """Load settings from database."""
        db = get_db()
        
        # GitHub token
        token = db.get_setting("github_token", "")
        self.token_input.setText(token)
        
        # Default branch
        branch = db.get_setting("default_branch", "")
        self.branch_input.setText(branch)
        
        # Auto-refresh
        auto_refresh = db.get_setting("auto_refresh", "false")
        self.auto_refresh_checkbox.setChecked(auto_refresh.lower() == "true")
        
        # Combat speed
        combat_speed = db.get_setting("combat_text_speed", "0")
        try:
            self.combat_speed_spin.setValue(int(combat_speed))
        except ValueError:
            self.combat_speed_spin.setValue(0)
    
    def save_settings(self):
        """Save settings to database."""
        db = get_db()
        
        # GitHub token
        token = self.token_input.text().strip()
        if token:
            db.set_setting("github_token", token)
        else:
            db.set_setting("github_token", "")
        
        # Default branch
        branch = self.branch_input.text().strip()
        if branch:
            db.set_setting("default_branch", branch)
        else:
            db.set_setting("default_branch", "")
        
        # Auto-refresh
        db.set_setting("auto_refresh", "true" if self.auto_refresh_checkbox.isChecked() else "false")
        
        # Combat speed
        db.set_setting("combat_text_speed", str(self.combat_speed_spin.value()))
        
        logger.info("Settings saved")
    
    def restore_defaults(self):
        """Restore default settings."""
        reply = QMessageBox.question(
            self,
            "Restore Defaults",
            "Are you sure you want to restore all settings to their default values?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.token_input.clear()
            self.branch_input.clear()
            self.auto_refresh_checkbox.setChecked(False)
            self.combat_speed_spin.setValue(0)
    
    def reset_database(self):
        """Reset the database (delete all game data)."""
        reply = QMessageBox.warning(
            self,
            "Reset Database",
            "WARNING: This will permanently delete ALL game data including:\n\n"
            "• All players and their progress\n"
            "• All discovered repository worlds\n"
            "• All items and inventory\n"
            "• All quests and enemies\n"
            "• All dungeon rooms\n\n"
            "Settings will be preserved.\n\n"
            "This action CANNOT be undone!\n\n"
            "Are you absolutely sure you want to continue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # Double confirmation
            reply2 = QMessageBox.warning(
                self,
                "Final Confirmation",
                "This is your last chance to cancel.\n\n"
                "All game data will be permanently deleted.\n\n"
                "Continue with database reset?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply2 == QMessageBox.StandardButton.Yes:
                try:
                    db = get_db()
                    cursor = db.get_connection().cursor()
                    
                    # Delete all game data tables (but keep settings)
                    tables_to_clear = [
                        "player_inventory",
                        "items",
                        "quests",
                        "dungeon_rooms",
                        "enemies",
                        "repo_worlds",
                        "players"
                    ]
                    
                    for table in tables_to_clear:
                        cursor.execute(f"DELETE FROM {table}")
                    
                    db.commit()
                    
                    QMessageBox.information(
                        self,
                        "Database Reset",
                        "Database has been reset successfully.\n\n"
                        "All game data has been deleted.\n"
                        "Settings have been preserved.\n\n"
                        "Please restart the application to start fresh."
                    )
                    
                    logger.info("Database reset completed by user")
                    
                except Exception as e:
                    logger.error(f"Error resetting database: {e}", exc_info=True)
                    QMessageBox.critical(
                        self,
                        "Error",
                        f"Failed to reset database:\n{str(e)}"
                    )
    
    def accept(self):
        """Handle OK button."""
        self.save_settings()
        super().accept()

