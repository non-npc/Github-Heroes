"""
Status bar widget for game status information.
"""
from PyQt6.QtWidgets import QStatusBar, QLabel
from PyQt6.QtCore import Qt

class GameStatusBar(QStatusBar):
    """
    Custom status bar for game information.
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.status_label = QLabel("Ready")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.addWidget(self.status_label)
        
        self.connection_label = QLabel("● Connected")
        self.connection_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.addPermanentWidget(self.connection_label)
    
    def set_status(self, message: str):
        """Set status message."""
        self.status_label.setText(message)
    
    def set_connection_status(self, connected: bool):
        """Set connection status."""
        if connected:
            self.connection_label.setText("● Connected")
            self.connection_label.setStyleSheet("color: green;")
        else:
            self.connection_label.setText("● Disconnected")
            self.connection_label.setStyleSheet("color: red;")

