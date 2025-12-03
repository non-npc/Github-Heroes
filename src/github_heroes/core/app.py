"""
Application initialization and main window setup.
"""

from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QApplication

from github_heroes.core.config import APP_ICON_ICO, APP_ICON_PNG, APP_NAME
from github_heroes.core.logging_utils import get_logger, setup_logging
from github_heroes.ui.main_window import MainWindow

logger = get_logger(__name__)


def create_app():
    """
    Create and configure the QApplication.
    """
    app = QApplication([])
    app.setApplicationName(APP_NAME)

    # Set application icon (prefer ICO on Windows, PNG otherwise)
    import sys

    if sys.platform == "win32" and APP_ICON_ICO.exists():
        app.setWindowIcon(QIcon(str(APP_ICON_ICO)))
    elif APP_ICON_PNG.exists():
        app.setWindowIcon(QIcon(str(APP_ICON_PNG)))
    else:
        logger.warning("Application icon not found")

    return app


def run_app():
    """
    Initialize and run the application.
    """
    setup_logging()
    logger.info("Starting Github Heroes")

    app = create_app()
    window = MainWindow()
    window.show()

    logger.info("Application started")
    return app.exec()
