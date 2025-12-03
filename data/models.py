"""
Data models for Github Heroes.
"""
from dataclasses import dataclass, field
from typing import Optional, Dict, List, Any
from datetime import datetime
import json

@dataclass
class Player:
    """Player character model."""
    id: Optional[int] = None
    name: str = "Hero"
    level: int = 1
    xp: int = 0
    hp: int = 100
    attack: int = 10
    defense: int = 5
    speed: int = 8
    luck: int = 5
    player_class: Optional[str] = None
    player_image_id: Optional[int] = None  # Image ID from 1-116
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "level": self.level,
            "xp": self.xp,
            "hp": self.hp,
            "attack": self.attack,
            "defense": self.defense,
            "speed": self.speed,
            "luck": self.luck,
            "player_class": self.player_class,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Player":
        """Create from dictionary."""
        return cls(**data)

@dataclass
class RepoWorld:
    """Repository world model."""
    id: Optional[int] = None
    owner: str = ""
    repo: str = ""
    full_name: str = ""
    primary_language: Optional[str] = None
    stars: int = 0
    forks: int = 0
    watchers: int = 0
    activity_score: int = 0
    health_state: Optional[str] = None
    main_enemy_id: Optional[int] = None
    readme_features_json: Optional[str] = None
    structure_features_json: Optional[str] = None
    discovered_at: Optional[str] = None
    last_scraped_at: Optional[str] = None
    
    def get_readme_features(self) -> Optional[Dict[str, Any]]:
        """Get parsed README features."""
        if self.readme_features_json:
            return json.loads(self.readme_features_json)
        return None
    
    def get_structure_features(self) -> Optional[Dict[str, Any]]:
        """Get parsed structure features."""
        if self.structure_features_json:
            return json.loads(self.structure_features_json)
        return None

@dataclass
class Enemy:
    """Enemy model."""
    id: Optional[int] = None
    world_id: Optional[int] = None
    name: str = ""
    level: int = 1
    hp: int = 50
    attack: int = 5
    defense: int = 5
    speed: int = 10
    tags_json: Optional[str] = None
    is_boss: bool = False
    creature_image_id: Optional[int] = None  # Image ID from 1-120
    
    def get_tags(self) -> List[str]:
        """Get parsed tags."""
        if self.tags_json:
            return json.loads(self.tags_json)
        return []
    
    def set_tags(self, tags: List[str]):
        """Set tags."""
        self.tags_json = json.dumps(tags)

@dataclass
class DungeonRoom:
    """Dungeon room model."""
    id: Optional[int] = None
    world_id: int = 0
    zone_name: str = ""
    file_path: str = ""
    danger_level: int = 1
    loot_quality: int = 1
    visited: bool = False

@dataclass
class Quest:
    """Quest model."""
    id: Optional[int] = None
    world_id: int = 0
    source_type: str = "issue"  # "issue" or "pr"
    source_number: int = 0
    title: str = ""
    difficulty: int = 1
    status: str = "new"  # "new", "in_progress", "completed"

@dataclass
class Item:
    """Item model."""
    id: Optional[int] = None
    name: str = ""
    rarity: str = "common"  # "common", "uncommon", "rare", "epic", "legendary"
    stat_bonuses_json: str = "{}"
    description: Optional[str] = None
    equipment_type: Optional[str] = None  # "weapon", "shield", "armor", "ring", "amulet", "boots"
    
    def get_stat_bonuses(self) -> Dict[str, int]:
        """Get parsed stat bonuses."""
        return json.loads(self.stat_bonuses_json)
    
    def set_stat_bonuses(self, bonuses: Dict[str, int]):
        """Set stat bonuses."""
        self.stat_bonuses_json = json.dumps(bonuses)

# Helper data classes for parsing
@dataclass
class RepoMeta:
    """Repository metadata from processing."""
    name: str = ""
    description: str = ""
    primary_language: Optional[str] = None
    stars: int = 0
    forks: int = 0
    watchers: int = 0
    last_update: Optional[str] = None

@dataclass
class TreeEntry:
    """File/directory entry from tree parsing."""
    path: str = ""
    is_dir: bool = False
    file_type: Optional[str] = None
    size: Optional[int] = None

@dataclass
class IssueData:
    """Issue data from parsing."""
    issue_number: int = 0
    title: str = ""
    labels: List[str] = field(default_factory=list)
    comment_count: int = 0
    is_open: bool = True
    created_at: Optional[str] = None
    author: Optional[str] = None

@dataclass
class PullRequestData:
    """Pull request data from parsing."""
    pr_number: int = 0
    title: str = ""
    comment_count: int = 0
    is_open: bool = True
    is_merged: bool = False
    additions: Optional[int] = None
    deletions: Optional[int] = None

@dataclass
class CommitData:
    """Commit data from parsing."""
    short_hash: str = ""
    author: str = ""
    message: str = ""
    date: Optional[str] = None
    diff_size: str = "small"  # "small", "medium", "large"

@dataclass
class ReadmeFeatures:
    """Features extracted from README."""
    word_count: int = 0
    char_count: int = 0
    heading_count: int = 0
    word_frequencies: Dict[str, int] = field(default_factory=dict)
    keyword_hits: Dict[str, int] = field(default_factory=dict)
    seed: int = 0

@dataclass
class Achievement:
    """Achievement model."""
    id: Optional[int] = None
    player_id: int = 0
    achievement_id: str = ""  # Unique identifier like "first_blood"
    unlocked_at: Optional[str] = None

