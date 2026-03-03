"""
Game state management system
"""

from enum import Enum


class GameState(Enum):
    MENU = "menu"
    BOSS_INTRO = "boss_intro"
    FIGHTING = "fighting"
    UPGRADE = "upgrade"
    VICTORY = "victory"
    GAME_OVER = "game_over"


class StateManager:
    """Manages game state transitions and logic"""
    
    def __init__(self):
        self.current_state = GameState.MENU
        self.state_handlers = {}
    
    def register_handler(self, state, handler):
        """Register a handler function for a specific state"""
        self.state_handlers[state] = handler
    
    def change_state(self, new_state):
        """Change to a new state"""
        if new_state in GameState:
            self.current_state = new_state
            return True
        return False
    
    def update(self, *args, **kwargs):
        """Update current state"""
        handler = self.state_handlers.get(self.current_state)
        if handler:
            return handler(*args, **kwargs)
        return None
    
    def is_state(self, state):
        """Check if currently in a specific state"""
        return self.current_state == state
