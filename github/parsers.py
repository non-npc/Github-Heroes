"""
HTML parsers for GitHub pages.
"""
import re
from typing import List, Optional
from bs4 import BeautifulSoup
from data.models import RepoMeta, TreeEntry, IssueData, PullRequestData, CommitData
from core.logging_utils import get_logger

logger = get_logger(__name__)

def _parse_count_with_suffix(text: str) -> int:
    """Parse count text that may have k (thousands) or M (millions) suffix."""
    if not text:
        return 0
    text = text.replace(',', '').strip().lower()
    # Match number with optional k/M suffix (e.g., "23.7k", "104k", "1.5k")
    # Pattern: optional digits, optional decimal point and digits, optional k/M suffix
    match = re.search(r'([\d]+\.?[\d]*)\s*([km])?', text)
    if match:
        number_str = match.group(1)
        suffix = match.group(2) if len(match.groups()) >= 2 and match.group(2) else None
        try:
            number = float(number_str)
            if suffix == 'k':
                return int(number * 1000)
            elif suffix == 'm':
                return int(number * 1000000)
            else:
                return int(number)
        except ValueError:
            return 0
    return 0

def parse_repo_metadata(html: str) -> Optional[RepoMeta]:
    """
    Parse repository metadata from home page HTML.
    """
    try:
        soup = BeautifulSoup(html, 'html.parser')
        meta = RepoMeta()
        
        # Extract name
        name_elem = soup.select_one('strong[itemprop="name"] a, h1 strong a')
        if name_elem:
            meta.name = name_elem.get_text(strip=True)
        
        # Extract description
        desc_elem = soup.select_one('p[itemprop="about"], .f4.mb-3')
        if desc_elem:
            meta.description = desc_elem.get_text(strip=True)
        
        # Extract primary language
        lang_elem = soup.select_one('.d-inline-block.mb-3 .color-fg-default.text-bold')
        if lang_elem:
            meta.primary_language = lang_elem.get_text(strip=True)
        
        # Extract stars, forks, watchers - try multiple selectors
        # Look for social count buttons/links with various patterns
        # Try button elements first (GitHub's newer UI)
        for button in soup.select('button[data-view-component*="true"]'):
            text = button.get_text(strip=True)
            aria_label = button.get('aria-label', '')
            # Check aria-label for type
            if 'star' in aria_label.lower() or 'stargazer' in aria_label.lower():
                count = _parse_count_with_suffix(text)
                if count > 0:
                    meta.stars = count
            elif 'fork' in aria_label.lower():
                count = _parse_count_with_suffix(text)
                if count > 0:
                    meta.forks = count
            elif 'watch' in aria_label.lower() and 'fork' not in aria_label.lower():
                count = _parse_count_with_suffix(text)
                if count > 0:
                    meta.watchers = count
        
        # Try link elements
        for link in soup.select('a[href*="/stargazers"], a[href*="/watchers"], a[href*="/network/members"], a[href*="/forks"]'):
            text = link.get_text(strip=True)
            href = link.get('href', '')
            if '/stargazers' in href or 'stargazers' in href:
                count = _parse_count_with_suffix(text)
                if count > 0:
                    meta.stars = count
            elif '/network/members' in href or '/forks' in href or 'forks' in href:
                count = _parse_count_with_suffix(text)
                if count > 0:
                    meta.forks = count
            elif '/watchers' in href or 'watchers' in href:
                count = _parse_count_with_suffix(text)
                if count > 0:
                    meta.watchers = count
        
        # Try alternative selectors for stats - look for button text patterns
        if meta.stars == 0:
            for elem in soup.select('a[href*="stargazers"], button[data-view-component*="stargazers"], [aria-label*="star"]'):
                text = elem.get_text(strip=True)
                if not text:
                    text = elem.get('aria-label', '') or elem.get('title', '')
                count = _parse_count_with_suffix(text)
                if count > 0:
                    meta.stars = count
                    break
        
        if meta.forks == 0:
            # Try multiple fork-related selectors
            for elem in soup.select('a[href*="network"], a[href*="forks"], button[data-view-component*="fork"], [aria-label*="fork"]'):
                text = elem.get_text(strip=True)
                if not text:
                    text = elem.get('aria-label', '') or elem.get('title', '')
                count = _parse_count_with_suffix(text)
                if count > 0:
                    meta.forks = count
                    break
        
        # Try finding by aria-label or title attributes
        if meta.forks == 0:
            for elem in soup.select('[aria-label*="fork"], [title*="fork"]'):
                text = elem.get_text(strip=True) or elem.get('aria-label', '') or elem.get('title', '')
                count = _parse_count_with_suffix(text)
                if count > 0:
                    meta.forks = count
                    break
        
        if meta.watchers == 0:
            for elem in soup.select('a[href*="watchers"], button[data-view-component*="watch"], [aria-label*="watch"]'):
                text = elem.get_text(strip=True)
                if not text:
                    text = elem.get('aria-label', '') or elem.get('title', '')
                count = _parse_count_with_suffix(text)
                if count > 0:
                    meta.watchers = count
                    break
        
        return meta
    except Exception as e:
        logger.error(f"Error parsing repo metadata: {e}")
        return None

def parse_tree(html: str) -> List[TreeEntry]:
    """
    Parse repository tree structure.
    """
    entries = []
    seen_paths = set()  # Track seen paths to avoid duplicates
    
    try:
        soup = BeautifulSoup(html, 'html.parser')
        
        # Find all file/directory links in the tree
        for link in soup.select('a[href*="/blob/"], a[href*="/tree/"]'):
            href = link.get('href', '')
            text = link.get_text(strip=True)
            
            if '/blob/' in href or '/tree/' in href:
                # Skip if we've already seen this path
                if text in seen_paths:
                    continue
                seen_paths.add(text)
                
                entry = TreeEntry()
                entry.path = text
                entry.is_dir = '/tree/' in href
                
                if not entry.is_dir:
                    # Extract file extension
                    if '.' in text:
                        entry.file_type = text.split('.')[-1].lower()
                
                entries.append(entry)
        
        # Alternative: look for table rows or list items
        if not entries:
            for row in soup.select('tr, .js-navigation-item'):
                link = row.select_one('a[href*="/blob/"], a[href*="/tree/"]')
                if link:
                    href = link.get('href', '')
                    text = link.get_text(strip=True)
                    
                    # Skip if we've already seen this path
                    if text in seen_paths:
                        continue
                    seen_paths.add(text)
                    
                    entry = TreeEntry()
                    entry.path = text
                    entry.is_dir = '/tree/' in href
                    if not entry.is_dir and '.' in text:
                        entry.file_type = text.split('.')[-1].lower()
                    entries.append(entry)
        
        return entries
    except Exception as e:
        logger.error(f"Error parsing tree: {e}")
        return []

def parse_issues(html: str) -> List[IssueData]:
    """
    Parse issues from issues page HTML.
    """
    issues = []
    try:
        soup = BeautifulSoup(html, 'html.parser')
        
        # Find issue list items
        for item in soup.select('.js-issue-row, .Box-row'):
            issue = IssueData()
            
            # Extract issue number and title
            title_link = item.select_one('a[href*="/issues/"]')
            if title_link:
                href = title_link.get('href', '')
                match = re.search(r'/issues/(\d+)', href)
                if match:
                    issue.issue_number = int(match.group(1))
                issue.title = title_link.get_text(strip=True)
            
            # Extract labels
            for label in item.select('.IssueLabel, .Label'):
                issue.labels.append(label.get_text(strip=True))
            
            # Extract comment count
            comment_link = item.select_one('a[href*="#issuecomment"]')
            if comment_link:
                text = comment_link.get_text(strip=True)
                match = re.search(r'(\d+)', text)
                if match:
                    issue.comment_count = int(match.group(1))
            
            # Check if open or closed
            if item.select_one('.State--open, .octicon-issue-opened'):
                issue.is_open = True
            elif item.select_one('.State--closed, .octicon-issue-closed'):
                issue.is_open = False
            
            if issue.issue_number > 0:
                issues.append(issue)
        
        return issues
    except Exception as e:
        logger.error(f"Error parsing issues: {e}")
        return []

def parse_pulls(html: str) -> List[PullRequestData]:
    """
    Parse pull requests from pulls page HTML.
    """
    pulls = []
    try:
        soup = BeautifulSoup(html, 'html.parser')
        
        # Find PR list items
        for item in soup.select('.js-issue-row, .Box-row'):
            pr = PullRequestData()
            
            # Extract PR number and title
            title_link = item.select_one('a[href*="/pull/"]')
            if title_link:
                href = title_link.get('href', '')
                match = re.search(r'/pull/(\d+)', href)
                if match:
                    pr.pr_number = int(match.group(1))
                pr.title = title_link.get_text(strip=True)
            
            # Extract comment count
            comment_link = item.select_one('a[href*="#issuecomment"]')
            if comment_link:
                text = comment_link.get_text(strip=True)
                match = re.search(r'(\d+)', text)
                if match:
                    pr.comment_count = int(match.group(1))
            
            # Check if open, closed, or merged
            if item.select_one('.State--open, .octicon-git-pull-request'):
                pr.is_open = True
            elif item.select_one('.State--merged, .octicon-git-merge'):
                pr.is_merged = True
                pr.is_open = False
            elif item.select_one('.State--closed'):
                pr.is_open = False
            
            # Try to extract additions/deletions
            for text_elem in item.select('.text-green, .text-red'):
                text = text_elem.get_text(strip=True)
                if '+' in text:
                    match = re.search(r'\+(\d+)', text)
                    if match:
                        pr.additions = int(match.group(1))
                elif '-' in text:
                    match = re.search(r'-(\d+)', text)
                    if match:
                        pr.deletions = int(match.group(1))
            
            if pr.pr_number > 0:
                pulls.append(pr)
        
        return pulls
    except Exception as e:
        logger.error(f"Error parsing pulls: {e}")
        return []

def parse_commits(html: str) -> List[CommitData]:
    """
    Parse commits from commits page HTML.
    """
    commits = []
    try:
        soup = BeautifulSoup(html, 'html.parser')
        
        # Find commit list items
        for item in soup.select('.commit-group-item, .Box-row'):
            commit = CommitData()
            
            # Extract hash
            hash_link = item.select_one('a[href*="/commit/"]')
            if hash_link:
                href = hash_link.get('href', '')
                match = re.search(r'/commit/([a-f0-9]+)', href)
                if match:
                    commit.short_hash = match.group(1)[:7]
            
            # Extract message
            message_elem = item.select_one('.commit-message, a[href*="/commit/"]')
            if message_elem:
                commit.message = message_elem.get_text(strip=True)
            
            # Extract author
            author_elem = item.select_one('.commit-author, .user-mention')
            if author_elem:
                commit.author = author_elem.get_text(strip=True)
            
            # Extract date
            time_elem = item.select_one('time-ago, relative-time, time')
            if time_elem:
                commit.date = time_elem.get('datetime') or time_elem.get_text(strip=True)
            
            if commit.short_hash:
                commits.append(commit)
        
        return commits
    except Exception as e:
        logger.error(f"Error parsing commits: {e}")
        return []

