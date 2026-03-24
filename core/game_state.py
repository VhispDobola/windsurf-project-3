"""
Game state management system
"""

from enum import Enum


class GameState(Enum):
    MENU = "menu"
    LOBBY = "lobby"
    JOIN_SETUP = "join_setup"
    CUSTOMIZATION = "customization"
    PROGRESSION = "progression"
    BOSS_INTRO = "boss_intro"
    FIGHTING = "fighting"
    UPGRADE = "upgrade"
    VICTORY = "victory"
    GAME_OVER = "game_over"


class StateManager:
    """Manages game state transitions and logic"""
    
    def __init__(self):
        self.current_state = GameState.MENU
    
    def change_state(self, new_state):
        """Change to a new state"""
        if isinstance(new_state, GameState):
            self.current_state = new_state
            return True
        return False
    
    def is_state(self, state):
        """Check if currently in a specific state"""
        return self.current_state == state
