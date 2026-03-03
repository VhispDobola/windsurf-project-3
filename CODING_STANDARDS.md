# Coding Standards and Naming Conventions

## Naming Conventions

### Variables and Functions
- Use **snake_case** for all variables and function names
- Examples: `player_health`, `get_random_upgrades()`, `handle_collisions()`

### Classes
- Use **PascalCase** for all class names
- Examples: `Player`, `BossManager`, `CollisionSystem`

### Constants
- Use **UPPER_SNAKE_CASE** for all constants
- Examples: `PLAYER_BASE_SPEED`, `SCREEN_WIDTH`, `BOSS_INTRO_DURATION`

### Private Members
- Use **single underscore prefix** for protected members
- Examples: `_internal_method()`, `_private_variable`

### File Names
- Use **snake_case** for all Python files
- Examples: `collision_system.py`, `boss_patterns.py`

## Code Organization

### Import Order
1. Standard library imports
2. Third-party imports
3. Local application imports (core, ui, utils, bosses, config)

### Class Structure
```python
class ClassName:
    """Docstring describing the class"""
    
    def __init__(self):
        """Initialize the class"""
        pass
    
    def public_method(self):
        """Public method with docstring"""
        pass
    
    def _private_method(self):
        """Private method with docstring"""
        pass
```

## Best Practices

- Keep methods under 50 lines when possible
- Use descriptive variable names
- Add docstrings to all classes and public methods
- Avoid magic numbers - use constants instead
- Handle errors gracefully
- Use type hints when appropriate
