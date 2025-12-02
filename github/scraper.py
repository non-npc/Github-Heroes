"""
GitHub processor for fetching repository data via HTTP.
"""
import requests
from typing import Optional
from core.config import (
    GITHUB_RAW_BASE, GITHUB_BASE, GITHUB_SEARCH_BASE,
    REQUEST_TIMEOUT, REQUEST_HEADERS, DEFAULT_BRANCHES
)
from core.logging_utils import get_logger

logger = get_logger(__name__)

class GitHubScraper:
    """
    Processor for GitHub repository data via HTTP.
    """
    
    def __init__(self, api_token: Optional[str] = None):
        self.api_token = api_token
        self.session = requests.Session()
        self.session.headers.update(REQUEST_HEADERS)
        if api_token:
            self.session.headers.update({"Authorization": f"token {api_token}"})
    
    def fetch_readme(self, owner: str, repo: str, branch: Optional[str] = None) -> Optional[str]:
        """
        Fetch README.md content from raw GitHub URL.
        """
        if not branch:
            branch = self._detect_branch(owner, repo)
        
        if not branch:
            return None
        
        url = f"{GITHUB_RAW_BASE}/{owner}/{repo}/{branch}/README.md"
        try:
            response = self.session.get(url, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            logger.info(f"Fetched README for {owner}/{repo}")
            return response.text
        except requests.RequestException as e:
            logger.warning(f"Failed to fetch README for {owner}/{repo}: {e}")
            return None
    
    def fetch_repo_home(self, owner: str, repo: str) -> Optional[str]:
        """
        Fetch repository home page HTML.
        """
        url = f"{GITHUB_BASE}/{owner}/{repo}"
        try:
            response = self.session.get(url, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            logger.info(f"Fetched repo home for {owner}/{repo}")
            return response.text
        except requests.RequestException as e:
            logger.warning(f"Failed to fetch repo home for {owner}/{repo}: {e}")
            return None
    
    def fetch_tree_html(self, owner: str, repo: str, branch: Optional[str] = None) -> Optional[str]:
        """
        Fetch repository tree HTML.
        """
        if not branch:
            branch = self._detect_branch(owner, repo)
        
        if not branch:
            return None
        
        url = f"{GITHUB_BASE}/{owner}/{repo}/tree/{branch}"
        try:
            response = self.session.get(url, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            logger.info(f"Fetched tree for {owner}/{repo}")
            return response.text
        except requests.RequestException as e:
            logger.warning(f"Failed to fetch tree for {owner}/{repo}: {e}")
            return None
    
    def fetch_issues_html(self, owner: str, repo: str) -> Optional[str]:
        """
        Fetch issues page HTML.
        """
        url = f"{GITHUB_BASE}/{owner}/{repo}/issues"
        try:
            response = self.session.get(url, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            logger.info(f"Fetched issues for {owner}/{repo}")
            return response.text
        except requests.RequestException as e:
            logger.warning(f"Failed to fetch issues for {owner}/{repo}: {e}")
            return None
    
    def fetch_pulls_html(self, owner: str, repo: str) -> Optional[str]:
        """
        Fetch pull requests page HTML.
        """
        url = f"{GITHUB_BASE}/{owner}/{repo}/pulls"
        try:
            response = self.session.get(url, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            logger.info(f"Fetched pulls for {owner}/{repo}")
            return response.text
        except requests.RequestException as e:
            logger.warning(f"Failed to fetch pulls for {owner}/{repo}: {e}")
            return None
    
    def fetch_commits_html(self, owner: str, repo: str, branch: Optional[str] = None) -> Optional[str]:
        """
        Fetch commits page HTML.
        """
        if not branch:
            branch = self._detect_branch(owner, repo)
        
        if not branch:
            return None
        
        url = f"{GITHUB_BASE}/{owner}/{repo}/commits/{branch}"
        try:
            response = self.session.get(url, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            logger.info(f"Fetched commits for {owner}/{repo}")
            return response.text
        except requests.RequestException as e:
            logger.warning(f"Failed to fetch commits for {owner}/{repo}: {e}")
            return None
    
    def search_repos_html(self, query: str) -> Optional[str]:
        """
        Search repositories via GitHub search page.
        """
        url = f"{GITHUB_SEARCH_BASE}?q={query}&type=repositories"
        try:
            response = self.session.get(url, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            logger.info(f"Searched repos: {query}")
            return response.text
        except requests.RequestException as e:
            logger.warning(f"Failed to search repos: {e}")
            return None
    
    def _detect_branch(self, owner: str, repo: str) -> Optional[str]:
        """
        Detect default branch by trying main, then master, or use override from settings.
        """
        # Check for branch override in settings
        from data.database import get_db
        db = get_db()
        override_branch = db.get_setting("default_branch", "")
        if override_branch:
            logger.info(f"Using override branch {override_branch} for {owner}/{repo}")
            return override_branch
        
        # Try default branches
        for branch in DEFAULT_BRANCHES:
            url = f"{GITHUB_BASE}/{owner}/{repo}/tree/{branch}"
            try:
                response = self.session.head(url, timeout=REQUEST_TIMEOUT, allow_redirects=True)
                if response.status_code == 200:
                    logger.info(f"Detected branch {branch} for {owner}/{repo}")
                    return branch
            except requests.RequestException:
                continue
        
        logger.warning(f"Could not detect branch for {owner}/{repo}")
        return None

