"""
Progress dialog for processing operations.
"""
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QProgressBar, QPushButton
from PyQt6.QtCore import Qt

class ScrapingProgressDialog(QDialog):
    """
    Progress dialog for GitHub processing operations.
    """
    
    def __init__(self, repo_name: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Processing Repository")
        self.setModal(True)
        self.setMinimumWidth(400)
        
        layout = QVBoxLayout()
        
        # Title
        title_label = QLabel(f"Processing: {repo_name}")
        title_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        layout.addWidget(title_label)
        
        # Status label
        self.status_label = QLabel("Initializing...")
        layout.addWidget(self.status_label)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)
        
        # Cancel button (optional - for future use)
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setEnabled(False)  # Not implemented yet
        layout.addWidget(self.cancel_btn)
        
        self.setLayout(layout)
    
    def update_progress(self, value: int, status: str = ""):
        """Update progress bar and status."""
        self.progress_bar.setValue(value)
        if status:
            self.status_label.setText(status)
    
    def set_maximum(self, maximum: int):
        """Set maximum progress value."""
        self.progress_bar.setMaximum(maximum)

