"""
Application initialization and main window setup.
"""

import logging
import click
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


@click.command(context_settings=dict(help_option_names=["-h", "--help"]))
@click.option(
    "-l",
    "--log",
    default="info",
    type=click.Choice(["critical", "error", "warn", "warning", "info", "debug"]),
    help="Logging level",
)
def run_app(log: str):
    """
    Initialize and run the application.
    """
    loglevel = getattr(logging, log.upper())
    setup_logging(loglevel)
    logger.info("Starting Github Heroes")

    app = create_app()
    window = MainWindow()
    window.show()

    logger.info("Application started")
    return app.exec()
