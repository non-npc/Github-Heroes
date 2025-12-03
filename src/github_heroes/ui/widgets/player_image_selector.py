"""
Player image selector widget with scrolling grid.
"""

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QGridLayout,
    QScrollArea,
    QLabel,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPixmap, QMouseEvent
from github_heroes.core.config import get_resource_path
from github_heroes.core.logging_utils import get_logger

logger = get_logger(__name__)


class ImageButton(QLabel):
    """Clickable image label for image selection."""

    clicked = pyqtSignal(int)  # Emits image_id when clicked

    def __init__(self, image_id: int, parent=None):
        super().__init__(parent)
        self.image_id = image_id
        self.setFixedSize(48, 48)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setStyleSheet("""
            QLabel {
                border: 2px solid #ccc;
                background-color: #f0f0f0;
            }
            QLabel:hover {
                border: 2px solid #4CAF50;
                background-color: #e8f5e9;
            }
        """)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.load_image()

    def load_image(self):
        """Load and display the player image."""
        image_id_str = f"{self.image_id:03d}"
        image_path = get_resource_path(f"assets/player/{image_id_str}.png")

        if image_path.exists():
            pixmap = QPixmap(str(image_path))
            scaled_pixmap = pixmap.scaled(
                48,
                48,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            self.setPixmap(scaled_pixmap)
        else:
            logger.warning(f"Player image not found: {image_path}")
            self.setText(f"{self.image_id}")

    def mousePressEvent(self, event: QMouseEvent):
        """Handle mouse click."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.image_id)
        super().mousePressEvent(event)

    def set_selected(self, selected: bool):
        """Set selected state."""
        if selected:
            self.setStyleSheet("""
                QLabel {
                    border: 3px solid #2196F3;
                    background-color: #e3f2fd;
                }
                QLabel:hover {
                    border: 3px solid #2196F3;
                    background-color: #e3f2fd;
                }
            """)
        else:
            self.setStyleSheet("""
                QLabel {
                    border: 2px solid #ccc;
                    background-color: #f0f0f0;
                }
                QLabel:hover {
                    border: 2px solid #4CAF50;
                    background-color: #e8f5e9;
                }
            """)


class PlayerImageSelector(QWidget):
    """Widget for selecting a player image from a scrolling grid."""

    image_selected = pyqtSignal(int)  # Emits image_id when an image is selected

    def __init__(self, parent=None):
        super().__init__(parent)
        self.selected_image_id = None
        self.image_buttons = {}
        self.init_ui()

    def init_ui(self):
        """Initialize UI."""
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        # Title
        title = QLabel("Select Character Image:")
        title.setStyleSheet("font-weight: bold; font-size: 12px;")
        layout.addWidget(title)

        # Scroll area for the grid
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setMinimumHeight(300)
        scroll.setMaximumHeight(400)

        # Container widget for the grid
        grid_container = QWidget()
        grid_layout = QGridLayout()
        grid_layout.setSpacing(5)
        grid_layout.setContentsMargins(10, 10, 10, 10)

        # Create image buttons for images 001-116
        columns = 8  # 8 columns for a nice grid
        for i in range(1, 117):  # 1 to 116
            row = (i - 1) // columns
            col = (i - 1) % columns

            image_btn = ImageButton(i)
            image_btn.clicked.connect(self.on_image_clicked)
            self.image_buttons[i] = image_btn
            grid_layout.addWidget(image_btn, row, col)

        grid_container.setLayout(grid_layout)
        scroll.setWidget(grid_container)

        layout.addWidget(scroll)
        self.setLayout(layout)

    def on_image_clicked(self, image_id: int):
        """Handle image click."""
        # Deselect previous
        if self.selected_image_id and self.selected_image_id in self.image_buttons:
            self.image_buttons[self.selected_image_id].set_selected(False)

        # Select new
        self.selected_image_id = image_id
        if image_id in self.image_buttons:
            self.image_buttons[image_id].set_selected(True)

        self.image_selected.emit(image_id)

    def get_selected_image_id(self) -> int:
        """Get the currently selected image ID."""
        return self.selected_image_id
