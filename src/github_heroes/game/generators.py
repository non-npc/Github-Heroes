"""
Procedural generation of game content from GitHub data.
"""

import json
import random
from typing import List, Optional

from github_heroes.core.config import ENEMY_PREFIXES, ENEMY_SUFFIXES
from github_heroes.core.logging_utils import get_logger
from github_heroes.data.database import get_db
from github_heroes.data.models import (
    DungeonRoom,
    Enemy,
    Quest,
    ReadmeFeatures,
    RepoWorld,
)
from github_heroes.data.repositories import (
    DungeonRoomRepository,
    EnemyRepository,
    QuestRepository,
    RepoWorldRepository,
)
from github_heroes.github.analyzers import (
    compute_activity_features,
    compute_issue_difficulty,
    compute_pr_boss_level,
    compute_readme_features,
    compute_structure_features,
)
from github_heroes.github.parsers import (
    parse_commits,
    parse_issues,
    parse_pulls,
    parse_repo_metadata,
    parse_tree,
)
from github_heroes.github.scraper import GitHubScraper

logger = get_logger(__name__)


def generate_room_enemy(
    danger_level: int, world_id: int, base_enemy: Optional[Enemy] = None
) -> Enemy:
    """
    Generate an enemy for a specific room based on danger level.
    Danger level determines enemy strength, base_enemy only provides flavor (name/tags).
    """
    enemy = Enemy()
    enemy.world_id = world_id
    enemy.is_boss = False
    # Assign random creature image (1-120)
    enemy.creature_image_id = random.randint(1, 120)

    # Generate enemy stats based on danger level (1-10)
    # Danger level 1 = appropriate for level 1 player
    # Danger level 10 = appropriate for level 10+ player

    # Enemy level is roughly danger_level + some variance
    # But keep it reasonable for early game
    enemy.level = max(1, danger_level)

    # HP: Base 30 + (danger_level * 15)
    # This gives: Level 1 = 45 HP, Level 5 = 105 HP, Level 10 = 180 HP
    enemy.hp = 30 + (danger_level * 15)

    # Attack: Base 4 + danger_level
    # This gives: Level 1 = 5 attack, Level 5 = 9 attack, Level 10 = 14 attack
    enemy.attack = 4 + danger_level

    # Defense: Base 1 + (danger_level // 2)
    # This gives: Level 1 = 1 defense, Level 5 = 3 defense, Level 10 = 6 defense
    enemy.defense = 1 + (danger_level // 2)

    # Speed: Base 6 + (danger_level // 2)
    # This gives: Level 1 = 6 speed, Level 5 = 8 speed, Level 10 = 11 speed
    enemy.speed = 6 + (danger_level // 2)

    # Use base enemy for name and tags if available, otherwise generic
    if base_enemy:
        # Use themed name but indicate it's a weaker version
        if danger_level <= 2:
            enemy.name = f"Weak {base_enemy.name}"
        elif danger_level <= 5:
            enemy.name = f"Lesser {base_enemy.name}"
        else:
            enemy.name = base_enemy.name
        enemy.set_tags(base_enemy.get_tags())
    else:
        # Generate a generic enemy
        enemy.name = f"Code Fragment (Level {danger_level})"
        enemy.set_tags(["generic"])

    return enemy


def _generate_enemy_name(keyword_hits: dict, seed: int, word_count: int) -> str:
    """
    Generate a unique enemy name using prefix/suffix system.
    Uses keyword hits, seed, and word count to maximize variety.

    Returns a combination like "Neural Archon" or "Dark Web Crawler"
    """
    # Seed random for deterministic but varied selection
    random.seed(seed)

    # Get all keywords with hits > 0, sorted by hit count
    active_keywords = [(k, v) for k, v in keyword_hits.items() if v > 0]
    active_keywords.sort(key=lambda x: x[1], reverse=True)

    # Determine prefix pool
    prefix_pool = []
    suffix_pool = []

    if not active_keywords:
        # No keywords, use generic only
        prefix_pool = ENEMY_PREFIXES["generic"]
        suffix_pool = ENEMY_SUFFIXES["generic"]
    else:
        # Build weighted pools based on keyword hits
        # Keywords with more hits have higher weight in selection
        # Collect themed prefixes/suffixes based on keyword weights
        themed_prefixes = []
        themed_suffixes = []

        for keyword, hits in active_keywords:
            if keyword in ENEMY_PREFIXES:
                # Add themed prefixes multiple times based on hit count (weighted)
                weight = max(1, hits * 2)  # At least 1, more hits = more weight
                themed_prefixes.extend(ENEMY_PREFIXES[keyword] * weight)
            if keyword in ENEMY_SUFFIXES:
                # Add themed suffixes multiple times based on hit count (weighted)
                weight = max(1, hits * 2)
                themed_suffixes.extend(ENEMY_SUFFIXES[keyword] * weight)

        # Mix themed and generic (70% themed, 30% generic if we have themes)
        if themed_prefixes:
            # Use word_count to add variation to selection
            variation_seed = (seed + word_count) % 1000
            random.seed(variation_seed)

            # 70% chance to use themed, 30% generic
            if random.random() < 0.7:
                prefix_pool = (
                    themed_prefixes
                    + ENEMY_PREFIXES["generic"][: len(themed_prefixes) // 3]
                )
            else:
                prefix_pool = (
                    ENEMY_PREFIXES["generic"]
                    + themed_prefixes[: len(ENEMY_PREFIXES["generic"]) // 3]
                )
        else:
            prefix_pool = ENEMY_PREFIXES["generic"]

        if themed_suffixes:
            # Use different variation for suffix selection
            variation_seed = (seed + word_count + 100) % 1000
            random.seed(variation_seed)

            if random.random() < 0.7:
                suffix_pool = (
                    themed_suffixes
                    + ENEMY_SUFFIXES["generic"][: len(themed_suffixes) // 3]
                )
            else:
                suffix_pool = (
                    ENEMY_SUFFIXES["generic"]
                    + themed_suffixes[: len(ENEMY_SUFFIXES["generic"]) // 3]
                )
        else:
            suffix_pool = ENEMY_SUFFIXES["generic"]

    # Select prefix and suffix using seed + word_count for maximum variety
    # Use different offsets to ensure prefix and suffix are independently selected
    prefix_seed = (seed + word_count) % 10000
    suffix_seed = (seed + word_count * 2 + 500) % 10000

    random.seed(prefix_seed)
    prefix = random.choice(prefix_pool) if prefix_pool else "Generic"

    random.seed(suffix_seed)
    suffix = random.choice(suffix_pool) if suffix_pool else "Spirit"

    return f"{prefix} {suffix}"


def generate_enemy_from_readme(
    features: ReadmeFeatures,
    world_id: Optional[int] = None,
    stars: int = 0,
    forks: int = 0,
    activity_score: int = 0,
    total_files: int = 0,
    commit_count: int = 0,
) -> Enemy:
    """
    Generate main enemy from README features and repository stats.
    Uses prefix/suffix system to create maximum variety of unique enemy names.
    Boss level scales with repository size and activity, not just README length.
    """
    # Seed random with deterministic seed
    random.seed(features.seed)

    enemy = Enemy()
    enemy.world_id = world_id
    # Assign random creature image (1-120) based on seed for determinism
    enemy.creature_image_id = random.randint(1, 120)

    # Generate unique name using prefix/suffix system
    keyword_hits = features.keyword_hits
    enemy.name = _generate_enemy_name(keyword_hits, features.seed, features.word_count)

    # Calculate level based on repository size and activity (not just README length)
    # Larger, more active repos should have higher level bosses

    # Base level from activity score (scaled down)
    # Activity score = commits*10 + stars + forks*2 + watchers*3
    activity_level = min(activity_score // 100, 30)  # Max 30 from activity

    # Level from repository size (file count)
    # More files = more complex codebase = harder boss
    file_level = min(total_files // 10, 25)  # Max 25 from file count

    # Level from stars (popularity indicator)
    # Popular repos are more challenging
    stars_level = min(stars // 100, 20)  # Max 20 from stars (100 stars = level 1)

    # Level from forks (community engagement)
    forks_level = min(forks // 50, 15)  # Max 15 from forks (50 forks = level 1)

    # Level from commits (activity indicator)
    commit_level = min(
        commit_count // 5, 10
    )  # Max 10 from commits (5 commits = level 1)

    # Small bonus from README quality (but not the main factor)
    readme_bonus = min(
        features.word_count // 500, 5
    )  # Max 5 from README (500 words = +1 level)

    # Combine all factors
    enemy.level = min(
        1
        + activity_level
        + file_level
        + stars_level
        + forks_level
        + commit_level
        + readme_bonus,
        100,
    )

    # Stats scale with level and repository metrics
    base_hp = 50
    hp_from_level = enemy.level * 10
    hp_from_files = total_files * 2
    enemy.hp = base_hp + hp_from_level + hp_from_files

    base_attack = 5
    attack_from_level = enemy.level * 2
    attack_from_stars = min(stars // 50, 20)  # Max +20 from stars
    enemy.attack = base_attack + attack_from_level + attack_from_stars

    base_defense = 5
    defense_from_level = enemy.level
    defense_from_activity = min(activity_score // 200, 15)  # Max +15 from activity
    enemy.defense = base_defense + defense_from_level + defense_from_activity

    enemy.speed = random.randint(5, 20)

    # Set tags
    tags = [k for k, v in keyword_hits.items() if v > 0]
    enemy.set_tags(tags)

    enemy.is_boss = False

    return enemy


def generate_dungeon_rooms(
    tree_entries: List, world_id: int, stars: int, health_state: str
) -> List[DungeonRoom]:
    """
    Generate dungeon rooms from repository structure.
    """
    rooms = []

    # Determine base loot quality from stars and health
    base_loot = 1
    if stars > 1000:
        base_loot = 6
    elif stars > 100:
        base_loot = 4
    elif stars > 10:
        base_loot = 2

    if health_state == "Vibrant":
        base_loot += 1
    elif health_state == "Undead":
        base_loot = max(1, base_loot - 1)

    # Track zones for danger calculation
    zone_file_counts = {}

    for entry in tree_entries:
        if entry.is_dir:
            continue  # Skip directories, only create rooms for files

        # Skip entries with empty or invalid file paths
        if not entry.path or not entry.path.strip():
            continue

        room = DungeonRoom()
        room.world_id = world_id

        # Determine zone
        if "/" in entry.path:
            room.zone_name = "/".join(entry.path.split("/")[:-1])
        else:
            room.zone_name = "root"

        room.file_path = entry.path

        # Calculate danger level based on zone
        if room.zone_name not in zone_file_counts:
            zone_file_counts[room.zone_name] = 0
        zone_file_counts[room.zone_name] += 1

        # Base danger from zone file count
        room.danger_level = min(1 + zone_file_counts[room.zone_name] // 5, 10)

        # Adjust danger based on file type
        if entry.file_type:
            if entry.file_type in ["py", "js", "ts", "java", "cpp", "c"]:
                room.danger_level += 1
            elif entry.file_type in ["md", "txt"]:
                room.danger_level = max(1, room.danger_level - 1)
            elif entry.file_type in ["json", "yml", "yaml", "toml"]:
                room.danger_level += 0

        # Special zones
        if "test" in room.zone_name.lower() or "tests" in room.zone_name.lower():
            room.danger_level += 2
        if "doc" in room.zone_name.lower() or "docs" in room.zone_name.lower():
            room.danger_level = max(1, room.danger_level - 1)

        # Loot quality - simple probabilistic distribution per dungeon
        # 95% chance for quality 1-3 (uniform), 2.5% for 4, 2% for 5, 0.5% for 6
        roll = random.random()
        if roll < 0.95:
            room.loot_quality = random.randint(1, 3)
        elif roll < 0.975:
            room.loot_quality = 4
        elif roll < 0.995:
            room.loot_quality = 5
        else:
            room.loot_quality = 6

        room.visited = False

        rooms.append(room)

    return rooms


def build_repo_world(
    owner: str, repo: str, scraper: GitHubScraper, progress_callback=None
) -> Optional[RepoWorld]:
    """
    Build a complete RepoWorld from GitHub repository.

    Args:
        owner: Repository owner
        repo: Repository name
        scraper: GitHub scraper instance
        progress_callback: Optional callback function(value: int, status: str) for progress updates
    """

    def update_progress(value: int, status: str):
        """Helper to call progress callback if provided."""
        if progress_callback:
            progress_callback(value, status)

    try:
        logger.info(f"Building repo world for {owner}/{repo}")

        update_progress(5, "Initializing...")

        # Check if world already exists
        full_name = f"{owner}/{repo}"
        existing_world = RepoWorldRepository.get_by_full_name(full_name)

        # Process data
        update_progress(10, "Fetching repository information...")
        repo_html = scraper.fetch_repo_home(owner, repo)
        if not repo_html:
            logger.error(f"Failed to fetch repo home for {owner}/{repo}")
            return None

        update_progress(20, "Parsing repository metadata...")
        repo_meta = parse_repo_metadata(repo_html)
        if not repo_meta:
            logger.error(f"Failed to parse repo metadata for {owner}/{repo}")
            return None

        # Fetch README
        update_progress(30, "Fetching README...")
        readme_text = scraper.fetch_readme(owner, repo)
        update_progress(40, "Analyzing README features...")
        readme_features = (
            compute_readme_features(readme_text) if readme_text else ReadmeFeatures()
        )

        # Fetch tree
        update_progress(50, "Fetching repository structure...")
        tree_html = scraper.fetch_tree_html(owner, repo)
        update_progress(55, "Parsing file structure...")
        tree_entries = parse_tree(tree_html) if tree_html else []
        structure_features = compute_structure_features(tree_entries)

        # Fetch commits
        update_progress(60, "Fetching commit history...")
        commits_html = scraper.fetch_commits_html(owner, repo)
        commits = parse_commits(commits_html) if commits_html else []
        activity_features = compute_activity_features(commits, repo_meta)

        # Create or update RepoWorld
        update_progress(65, "Creating repository world...")
        if existing_world:
            world = existing_world
            world.stars = repo_meta.stars
            world.forks = repo_meta.forks
            world.watchers = repo_meta.watchers
            world.primary_language = repo_meta.primary_language
            world.activity_score = activity_features["activity_score"]
            world.health_state = activity_features["health_state"]
            world.readme_features_json = json.dumps(readme_features.__dict__)
            world.structure_features_json = json.dumps(structure_features)
            world.last_scraped_at = None  # Will be set by update
            RepoWorldRepository.update(world)
        else:
            world = RepoWorld(
                owner=owner,
                repo=repo,
                full_name=full_name,
                primary_language=repo_meta.primary_language,
                stars=repo_meta.stars,
                forks=repo_meta.forks,
                watchers=repo_meta.watchers,
                activity_score=activity_features["activity_score"],
                health_state=activity_features["health_state"],
                readme_features_json=json.dumps(readme_features.__dict__),
                structure_features_json=json.dumps(structure_features),
            )
            world = RepoWorldRepository.create(world)

        # Generate main enemy
        update_progress(70, "Generating main enemy...")
        main_enemy = generate_enemy_from_readme(
            readme_features,
            world.id,
            stars=repo_meta.stars,
            forks=repo_meta.forks,
            activity_score=activity_features["activity_score"],
            total_files=structure_features.get("total_files", 0),
            commit_count=len(commits),
        )
        main_enemy = EnemyRepository.create(main_enemy)
        world.main_enemy_id = main_enemy.id
        RepoWorldRepository.update(world)

        # Generate dungeon rooms
        update_progress(75, "Generating dungeon rooms...")

        # Delete existing rooms for this world if refreshing
        if existing_world:
            existing_rooms = DungeonRoomRepository.get_by_world_id(world.id)
            db = get_db()
            for old_room in existing_rooms:
                db.execute("DELETE FROM dungeon_rooms WHERE id = ?", (old_room.id,))
            db.commit()

        rooms = generate_dungeon_rooms(
            tree_entries, world.id, world.stars, world.health_state or "Unknown"
        )

        # Deduplicate rooms by file_path before creating
        seen_paths = {}
        unique_rooms = []
        for room in rooms:
            if room.file_path not in seen_paths:
                seen_paths[room.file_path] = room
                unique_rooms.append(room)

        for i, room in enumerate(unique_rooms):
            DungeonRoomRepository.create(room)
            if i % 10 == 0 and progress_callback and len(unique_rooms) > 0:
                progress_callback(
                    75 + (i * 5 // len(unique_rooms)),
                    f"Creating room {i + 1}/{len(unique_rooms)}...",
                )

        # Fetch and generate quests from issues
        update_progress(85, "Fetching issues...")
        issues_html = scraper.fetch_issues_html(owner, repo)
        if issues_html:
            update_progress(88, "Processing issues...")
            issues = parse_issues(issues_html)
            for issue in issues[:20]:  # Limit to first 20 issues
                quest = Quest(
                    world_id=world.id,
                    source_type="issue",
                    source_number=issue.issue_number,
                    title=issue.title,
                    difficulty=compute_issue_difficulty(issue),
                    status="new",
                )
                QuestRepository.create(quest)

        # Fetch and generate boss quests from PRs
        update_progress(92, "Fetching pull requests...")
        pulls_html = scraper.fetch_pulls_html(owner, repo)
        if pulls_html:
            update_progress(95, "Processing pull requests...")
            pulls = parse_pulls(pulls_html)
            # Use main enemy level as base for PR boss scaling
            base_repo_level = main_enemy.level
            for pr in pulls[:10]:  # Limit to first 10 PRs
                pr_level = compute_pr_boss_level(pr, base_repo_level)
                # Create boss enemy for PR
                boss = Enemy(
                    world_id=world.id,
                    name=f"PR #{pr.pr_number}: {pr.title[:30]}",
                    level=pr_level,
                    hp=100 + pr_level * 10,
                    attack=10 + pr_level * 2,
                    defense=5 + pr_level,
                    speed=8 + pr_level // 2,
                    is_boss=True,
                )
                boss.set_tags(["pull-request", "boss"])
                boss = EnemyRepository.create(boss)

                # Create quest
                quest = Quest(
                    world_id=world.id,
                    source_type="pr",
                    source_number=pr.pr_number,
                    title=pr.title,
                    difficulty=pr_level,
                    status="new",
                )
                QuestRepository.create(quest)

        update_progress(100, "Complete!")
        logger.info(f"Successfully built repo world for {full_name}")
        return world

    except Exception as e:
        logger.error(
            f"Error building repo world for {owner}/{repo}: {e}", exc_info=True
        )
        return None
