"""
Search panel for adding repositories.
"""

import re

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from github_heroes.core.logging_utils import get_logger
from github_heroes.github.scraper import GitHubScraper

logger = get_logger(__name__)


class SearchPanel(QWidget):
    """
    Panel for searching and adding GitHub repositories.
    """

    repo_selected = pyqtSignal(str, str)  # owner, repo

    def __init__(self, parent=None):
        super().__init__(parent)
        self.scraper = GitHubScraper()
        self.init_ui()

    def init_ui(self):
        """Initialize UI."""
        layout = QVBoxLayout()

        # URL input
        url_label = QLabel("Repository URL:")
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("https://github.com/owner/repo")
        self.url_input.returnPressed.connect(self.add_from_url)

        url_layout = QHBoxLayout()
        url_layout.addWidget(url_label)
        url_layout.addWidget(self.url_input)

        add_url_btn = QPushButton("Add Repository")
        add_url_btn.clicked.connect(self.add_from_url)

        # Search
        search_label = QLabel("Search:")
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Enter search query...")
        self.search_input.returnPressed.connect(self.search_repos)

        search_btn = QPushButton("Search")
        search_btn.clicked.connect(self.search_repos)

        # Results list
        results_label = QLabel("Search Results:")
        self.results_list = QListWidget()
        self.results_list.itemDoubleClicked.connect(self.on_result_selected)

        # Layout
        layout.addLayout(url_layout)
        layout.addWidget(add_url_btn)
        layout.addWidget(QLabel("---"))
        layout.addWidget(search_label)
        layout.addWidget(self.search_input)
        layout.addWidget(search_btn)
        layout.addWidget(results_label)
        layout.addWidget(self.results_list)

        self.setLayout(layout)

    def add_from_url(self):
        """Add repository from URL."""
        url = self.url_input.text().strip()
        if not url:
            QMessageBox.warning(self, "Error", "Please enter a repository URL")
            return

        # Parse URL
        match = re.search(r"github\.com/([^/]+)/([^/?#]+)", url)
        if not match:
            QMessageBox.warning(self, "Error", "Invalid GitHub URL")
            return

        owner, repo = match.groups()
        self.repo_selected.emit(owner, repo)
        self.url_input.clear()

    def search_repos(self):
        """Search for repositories."""
        query = self.search_input.text().strip()
        if not query:
            QMessageBox.warning(self, "Error", "Please enter a search query")
            return

        self.results_list.clear()
        self.results_list.addItem("Searching...")

        # Search (simplified - would need proper parsing)
        html = self.scraper.search_repos_html(query)
        if html:
            # Simple parsing - in production would use proper parser
            from bs4 import BeautifulSoup

            soup = BeautifulSoup(html, "html.parser")
            self.results_list.clear()

            # Find repo links
            for link in soup.select('a[href*="/"][href*="/"][href*="/"]'):
                href = link.get("href", "")
                if href.startswith("/") and href.count("/") == 2:
                    owner_repo = href.strip("/")
                    if owner_repo and "/" in owner_repo:
                        item = QListWidgetItem(owner_repo)
                        self.results_list.addItem(item)
        else:
            self.results_list.clear()
            self.results_list.addItem("No results found")

    def on_result_selected(self, item: QListWidgetItem):
        """Handle result selection."""
        text = item.text()
        if "/" in text:
            parts = text.split("/")
            if len(parts) >= 2:
                owner, repo = parts[0], parts[1]
                self.repo_selected.emit(owner, repo)
