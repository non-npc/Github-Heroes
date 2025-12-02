"""
Core in-memory game state.
"""
from typing import Optional
from data.models import Player, RepoWorld, Enemy, DungeonRoom
from data.repositories import PlayerRepository, RepoWorldRepository, EnemyRepository, DungeonRoomRepository

class GameState:
    """
    Manages the current game state.
    """
    
    def __init__(self):
        self.current_player: Optional[Player] = None
        self.current_world: Optional[RepoWorld] = None
        self.current_enemy: Optional[Enemy] = None
        self.current_room: Optional[DungeonRoom] = None
        self.in_combat: bool = False
    
    def set_player(self, player: Player):
        """Set the current player."""
        self.current_player = player
    
    def set_world(self, world: RepoWorld):
        """Set the current world."""
        self.current_world = world
    
    def set_enemy(self, enemy: Enemy):
        """Set the current enemy (enters combat)."""
        self.current_enemy = enemy
        self.in_combat = True
    
    def clear_enemy(self):
        """Clear current enemy (exits combat)."""
        self.current_enemy = None
        self.in_combat = False
    
    def set_room(self, room: DungeonRoom):
        """Set the current room."""
        self.current_room = room
    
    def load_player(self, player_id: int) -> bool:
        """Load a player by ID."""
        player = PlayerRepository.get_by_id(player_id)
        if player:
            self.current_player = player
            return True
        return False
    
    def load_world(self, world_id: int) -> bool:
        """Load a world by ID."""
        world = RepoWorldRepository.get_by_id(world_id)
        if world:
            self.current_world = world
            return True
        return False

# Global game state instance
_game_state = GameState()

def get_game_state() -> GameState:
    """Get the global game state."""
    return _game_state

