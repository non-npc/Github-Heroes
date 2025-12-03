"""
Analysis and feature extraction from processed GitHub data.
"""

import hashlib
import re
from collections import Counter
from typing import Dict, List

from github_heroes.core.config import (
    KEYWORD_GROUPS,
)
from github_heroes.core.logging_utils import get_logger
from github_heroes.data.models import (
    CommitData,
    IssueData,
    PullRequestData,
    ReadmeFeatures,
    TreeEntry,
)

logger = get_logger(__name__)


def compute_readme_features(text: str) -> ReadmeFeatures:
    """
    Compute features from README text.
    """
    features = ReadmeFeatures()

    if not text:
        return features

    # Basic counts
    features.char_count = len(text)
    features.word_count = len(text.split())

    # Count headings (Markdown headers)
    heading_pattern = re.compile(r"^#+\s", re.MULTILINE)
    features.heading_count = len(heading_pattern.findall(text))

    # Word frequencies (lowercase, alphanumeric only)
    words = re.findall(r"\b[a-zA-Z0-9]+\b", text.lower())
    features.word_frequencies = dict(Counter(words))

    # Keyword hits
    # Only match keywords with 3+ characters to avoid false positives (e.g., "ai" matching in "main", "said")
    text_lower = text.lower()
    for group_name, keywords in KEYWORD_GROUPS.items():
        hits = 0
        for keyword in keywords:
            keyword_lower = keyword.lower()
            # Skip keywords shorter than 3 characters
            if len(keyword_lower) < 3:
                continue
            # Use word boundaries to match whole words only
            # This prevents "ai" from matching in "main", "said", "again", etc.
            pattern = r"\b" + re.escape(keyword_lower) + r"\b"
            matches = re.findall(pattern, text_lower)
            hits += len(matches)
        features.keyword_hits[group_name] = hits

    # Generate deterministic seed from README hash
    seed_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
    features.seed = int(seed_hash[:16], 16)

    return features


def compute_structure_features(tree_entries: List[TreeEntry]) -> Dict:
    """
    Compute features from repository structure.
    """
    features = {
        "total_files": 0,
        "total_dirs": 0,
        "files_by_extension": {},
        "zones": {},
    }

    file_extensions = Counter()
    zones = {}

    for entry in tree_entries:
        if entry.is_dir:
            features["total_dirs"] += 1
            # Track directory zones
            zone_name = entry.path.split("/")[0] if "/" in entry.path else entry.path
            if zone_name not in zones:
                zones[zone_name] = {"files": 0, "dirs": 0}
            zones[zone_name]["dirs"] += 1
        else:
            features["total_files"] += 1
            if entry.file_type:
                file_extensions[entry.file_type] += 1

            # Track file zones
            zone_name = entry.path.split("/")[0] if "/" in entry.path else "root"
            if zone_name not in zones:
                zones[zone_name] = {"files": 0, "dirs": 0}
            zones[zone_name]["files"] += 1

    features["files_by_extension"] = dict(file_extensions)
    features["zones"] = zones

    return features


def compute_activity_features(commits: List[CommitData], repo_meta) -> Dict:
    """
    Compute activity and reputation features.
    """
    features = {
        "commit_count_recent": len(commits),
        "repo_age": None,
        "activity_score": 0,
        "stars": repo_meta.stars if repo_meta else 0,
        "forks": repo_meta.forks if repo_meta else 0,
        "watchers": repo_meta.watchers if repo_meta else 0,
        "health_state": "Unknown",
    }

    # Calculate activity score
    # Base score from commits (each commit = 10 points)
    commit_score = len(commits) * 10

    # Add reputation points (stars, forks, watchers)
    reputation_score = (
        features["stars"] + (features["forks"] * 2) + (features["watchers"] * 3)
    )

    # Total activity score
    features["activity_score"] = commit_score + reputation_score

    # Determine health state from commits and reputation
    if len(commits) >= 10 or features["stars"] > 1000:
        features["health_state"] = "Vibrant"
    elif len(commits) >= 5 or features["stars"] > 100:
        features["health_state"] = "Stable"
    elif len(commits) >= 1 or features["stars"] > 10:
        features["health_state"] = "Frail"
    else:
        features["health_state"] = "Undead"

    return features


def compute_issue_difficulty(issue: IssueData) -> int:
    """
    Compute difficulty score for an issue.
    """
    difficulty = 1

    # Base difficulty from comment count
    difficulty += issue.comment_count // 2

    # Bonus for labels
    if "bug" in [label.lower() for label in issue.labels]:
        difficulty += 2
    if "enhancement" in [label.lower() for label in issue.labels] or "feature" in [
        label.lower() for label in issue.labels
    ]:
        difficulty += 1

    # Age factor (simplified - would need proper date parsing)
    if not issue.is_open:
        difficulty += 1

    return min(difficulty, 20)  # Cap at 20


def compute_pr_boss_level(pr: PullRequestData, base_repo_level: int = 1) -> int:
    """
    Compute boss level for a pull request.
    PR bosses should scale with the repository's overall difficulty.

    Args:
        pr: Pull request data
        base_repo_level: Base level from main enemy (indicates repo size/activity)
    """
    # Base level scales with repository difficulty
    # PRs in larger repos should be more challenging
    level = max(1, base_repo_level // 2)  # Start at half the main enemy level, min 1

    # Increase based on comment count (indicates discussion/complexity)
    level += pr.comment_count // 3

    # Increase based on diff size (larger changes = harder)
    if pr.additions and pr.deletions:
        total_changes = pr.additions + pr.deletions
        if total_changes > 1000:
            level += 10
        elif total_changes > 500:
            level += 5
        elif total_changes > 100:
            level += 2

    # Cap relative to repo level (PRs shouldn't be way harder than main boss)
    max_level = min(base_repo_level + 10, 50)
    return min(level, max_level)
