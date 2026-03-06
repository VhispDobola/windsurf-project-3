"""
Utility functions and helper classes
"""

import os
import pygame

from .performance_logger import PerformanceLogger
from .boss_scaling import position_boss_pair
from .error_handler import GameErrorHandler, validate_game_config
from .balance_monitor import load_log_driven_balance
from .boss_tuning import load_boss_profile

def get_project_root():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def asset_path(*parts):
    return os.path.join(get_project_root(), *parts)


def load_image(*parts):
    return pygame.image.load(asset_path(*parts)).convert_alpha()


def load_image_with_transparency(*parts, transparent_color=None):
    """Load image and optionally set a color as transparent"""
    image = pygame.image.load(asset_path(*parts)).convert_alpha()
    
    if transparent_color:
        # Set the specified color to be fully transparent
        image.set_colorkey(transparent_color)
    
    return image


__all__ = [
    'PerformanceLogger', 'position_boss_pair', 'GameErrorHandler', 'validate_game_config',
    'get_project_root', 'asset_path', 'load_image', 'load_image_with_transparency',
    'load_log_driven_balance', 'load_boss_profile'
]
