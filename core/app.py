"""
Application initialization and main window setup.
"""
from PyQt6.QtWidgets import QApplication
from core.logging_utils import setup_logging
from core.config import APP_NAME
from ui.main_window import MainWindow
from core.logging_utils import get_logger

logger = get_logger(__name__)

def create_app():
    """
    Create and configure the QApplication.
    """
    app = QApplication([])
    app.setApplicationName(APP_NAME)
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

