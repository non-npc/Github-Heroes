# Github Heroes

An incremental RPG "Github Repo" game that turns GitHub repositories into dungeons, enemies, quests, and loot.

![Github Heroes Screenshot](screenshot.png)

## Description

Github Heroes is a single-player incremental RPG/exploration game built with Python and PyQt6. It parses public GitHub repositories and procedurally generates:

- **Repo Worlds**: Each GitHub repository becomes a dungeon/zone
- **Enemies**: Generated from README content and repository features
- **Dungeon Rooms**: Created from repository file structure
- **Quests**: Issues become regular quests, Pull Requests become boss battles
- **Loot**: Items themed by repository language and features

## Features

- Explore GitHub repositories as RPG dungeons
- Turn-based combat system
- Player progression with XP and leveling
- Inventory system with stat-boosting items
- Quest board for issues and PRs
- World map showing discovered repositories
- Persistent game state in SQLite database

## Requirements

- Python 3.10 or higher
- PyQt6 6.10.0
- requests
- beautifulsoup4
- lxml

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

## Running

```bash
python main.py
```

## How to Play

1. **Create a Player**: Start a new game and create your character
2. **Discover Repositories**: Use the search panel to add GitHub repositories
3. **Explore Dungeons**: Enter dungeons to explore repository structure
4. **Fight Enemies**: Battle enemies in rooms and complete quests
5. **Level Up**: Gain XP and level up to become stronger
6. **Complete Quests**: Take on issues and PRs as quests and boss battles

## Game Mechanics

- **Enemies**: Generated deterministically from README content
- **Combat**: Turn-based with Attack, Defend, and Flee options
- **Loot**: Items drop after victories, with rarity based on repository stars and health
- **Progression**: Gain XP from defeating enemies, level up to increase stats
- **Quests**: Issues become quests, PRs become boss battles

## Technical Details

- Built with PyQt6 for the GUI
- SQLite for persistent game data
- HTTP process repo data
- Background threading for network operations
- Deterministic procedural generation

## License

This project is provided as-is for educational and entertainment purposes.

