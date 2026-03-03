"""
Centralized input management system
"""

import pygame
import logging
from typing import Dict, Callable, List, Tuple, Optional
from enum import Enum


class InputAction(Enum):
    """Standardized input actions"""
    MOVE_UP = "move_up"
    MOVE_DOWN = "move_down"
    MOVE_LEFT = "move_left"
    MOVE_RIGHT = "move_right"
    DASH = "dash"
    SHOOT = "shoot"
    CONFIRM = "confirm"
    CANCEL = "cancel"
    PAUSE = "pause"
    FULLSCREEN = "fullscreen"
    RESTART = "restart"


class InputManager:
    """Centralized input management with rebinding support"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.key_bindings: Dict[InputAction, List[int]] = {
            InputAction.MOVE_UP: [pygame.K_w, pygame.K_UP],
            InputAction.MOVE_DOWN: [pygame.K_s, pygame.K_DOWN],
            InputAction.MOVE_LEFT: [pygame.K_a, pygame.K_LEFT],
            InputAction.MOVE_RIGHT: [pygame.K_d, pygame.K_RIGHT],
            InputAction.DASH: [pygame.K_LSHIFT, pygame.K_RSHIFT],
            InputAction.SHOOT: [pygame.K_SPACE],
            InputAction.CONFIRM: [pygame.K_SPACE, pygame.K_RETURN],
            InputAction.CANCEL: [pygame.K_ESCAPE],
            InputAction.PAUSE: [pygame.K_ESCAPE, pygame.K_p],
            InputAction.FULLSCREEN: [pygame.K_F11],
            InputAction.RESTART: [pygame.K_r],
        }
        
        self.action_handlers: Dict[InputAction, List[Callable]] = {}
        self.current_keys = set()
        self.previous_keys = set()
        self.mouse_pos = (0, 0)
        self.previous_mouse_pos = (0, 0)
        self.mouse_buttons = set()
        self.previous_mouse_buttons = set()
    
    def bind_key(self, action: InputAction, key: int):
        """Bind a key to an action"""
        if action not in self.key_bindings:
            self.key_bindings[action] = []
        
        if key not in self.key_bindings[action]:
            self.key_bindings[action].append(key)
    
    def unbind_key(self, action: InputAction, key: int):
        """Unbind a key from an action"""
        if action in self.key_bindings and key in self.key_bindings[action]:
            self.key_bindings[action].remove(key)
    
    def add_action_handler(self, action: InputAction, handler: Callable):
        """Add a handler for an action"""
        if action not in self.action_handlers:
            self.action_handlers[action] = []
        self.action_handlers[action].append(handler)
    
    def remove_action_handler(self, action: InputAction, handler: Callable):
        """Remove a handler for an action"""
        if action in self.action_handlers and handler in self.action_handlers[action]:
            self.action_handlers[action].remove(handler)
    
    def update(self):
        """Update input state"""
        # Store previous state
        self.previous_keys = self.current_keys.copy()
        self.previous_mouse_pos = self.mouse_pos
        self.previous_mouse_buttons = self.mouse_buttons.copy()
        
        # Update current state
        keys = pygame.key.get_pressed()
        self.current_keys = {key for key, pressed in enumerate(keys) if pressed}
        
        self.mouse_pos = pygame.mouse.get_pos()
        mouse_buttons = pygame.mouse.get_pressed()
        self.mouse_buttons = {i for i, pressed in enumerate(mouse_buttons) if pressed}
        
        # Process action handlers
        self._process_actions()
    
    def is_action_pressed(self, action: InputAction) -> bool:
        """Check if an action is currently pressed"""
        if action not in self.key_bindings:
            return False
        
        return any(key in self.current_keys for key in self.key_bindings[action])
    
    def is_action_just_pressed(self, action: InputAction) -> bool:
        """Check if an action was just pressed this frame"""
        if action not in self.key_bindings:
            return False
        
        return any(key in self.current_keys and key not in self.previous_keys 
                  for key in self.key_bindings[action])
    
    def is_action_just_released(self, action: InputAction) -> bool:
        """Check if an action was just released this frame"""
        if action not in self.key_bindings:
            return False
        
        return any(key in self.previous_keys and key not in self.current_keys 
                  for key in self.key_bindings[action])
    
    def is_mouse_button_pressed(self, button: int) -> bool:
        """Check if a mouse button is currently pressed"""
        return button in self.mouse_buttons
    
    def is_mouse_button_just_pressed(self, button: int) -> bool:
        """Check if a mouse button was just pressed this frame"""
        return button in self.mouse_buttons and button not in self.previous_mouse_buttons
    
    def is_mouse_button_just_released(self, button: int) -> bool:
        """Check if a mouse button was just released this frame"""
        return button in self.previous_mouse_buttons and button not in self.mouse_buttons
    
    def get_mouse_movement(self) -> Tuple[int, int]:
        """Get mouse movement since last frame"""
        return (self.mouse_pos[0] - self.previous_mouse_pos[0],
                self.mouse_pos[1] - self.previous_mouse_pos[1])
    
    def _process_actions(self):
        """Process action handlers"""
        for action, handlers in self.action_handlers.items():
            if self.is_action_just_pressed(action):
                for handler in handlers:
                    try:
                        handler(action, True)
                    except Exception as e:
                        self.logger.error("Error in action handler for %s: %s", action, e)
            
            elif self.is_action_just_released(action):
                for handler in handlers:
                    try:
                        handler(action, False)
                    except Exception as e:
                        self.logger.error("Error in action handler for %s: %s", action, e)
    
    def get_movement_vector(self) -> Tuple[float, float]:
        """Get normalized movement vector from movement keys"""
        dx = dy = 0
        
        if self.is_action_pressed(InputAction.MOVE_LEFT):
            dx -= 1
        if self.is_action_pressed(InputAction.MOVE_RIGHT):
            dx += 1
        if self.is_action_pressed(InputAction.MOVE_UP):
            dy -= 1
        if self.is_action_pressed(InputAction.MOVE_DOWN):
            dy += 1
        
        # Normalize diagonal movement
        if dx != 0 and dy != 0:
            dx *= 0.707  # 1/sqrt(2)
            dy *= 0.707
        
        return (dx, dy)
    
    def load_config(self, config_path: str):
        """Load key bindings from config file"""
        try:
            import json
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                
            for action_name, keys in config.get('key_bindings', {}).items():
                try:
                    action = InputAction(action_name)
                    self.key_bindings[action] = keys
                except ValueError:
                    self.logger.warning("Unknown action: %s", action_name)
        except Exception as e:
            self.logger.error("Error loading input config: %s", e)
    
    def save_config(self, config_path: str):
        """Save current key bindings to config file"""
        try:
            import json
            config = {
                'key_bindings': {
                    action.value: keys for action, keys in self.key_bindings.items()
                }
            }
            
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            self.logger.error("Error saving input config: %s", e)
