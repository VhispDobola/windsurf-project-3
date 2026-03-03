"""
Common imports and base functionality for all bosses.
This module reduces import duplication across boss files.
"""

import pygame
import math
import random
from core.boss import Boss
from core.projectile import Projectile, ProjectileBehavior
from core.effect import Telegraph
from core.entity import DamageType
from core.base_boss import BaseBossMixin
from core.attack_patterns import AttackPattern
from core.movement_system import BossMovementController, SineWaveMovement, CircularMovement
from config.constants import WIDTH, HEIGHT, RED, BLUE, GREEN, YELLOW, PURPLE, ORANGE, CYAN, WHITE, BLACK

class BaseBoss(Boss, BaseBossMixin):
    """Base class for all bosses with common functionality"""
    
    def __init__(self, x, y, width, height, health, name):
        super().__init__(x, y, width, height, health, name)
        BaseBossMixin.__init__(self)
    
    def update(self):
        """Standard update with common functionality"""
        super().update()
        
        # Update custom projectile lists
        self._update_custom_projectiles()
        
        # Update arena hazards
        if hasattr(self, 'arena_hazards'):
            self._update_arena_hazards()
    
    def _update_custom_projectiles(self):
        """Update any custom projectile lists the boss might have"""
        custom_lists = [
            'mirror_blades', 'time_bullets', 'lasers', 'fire_breath',
            'ice_shards', 'crystal_shards', 'prism_beams', 'lightning_bolts'
        ]
        
        for list_name in custom_lists:
            if hasattr(self, list_name):
                projectile_list = getattr(self, list_name)
                active_projectiles = []
                for projectile in projectile_list:
                    projectile.update()
                    if not (hasattr(projectile, 'is_off_screen') and projectile.is_off_screen()):
                        active_projectiles.append(projectile)
                setattr(self, list_name, active_projectiles)
    
    def _update_arena_hazards(self):
        """Update arena hazards and their lifetimes"""
        active_hazards = []
        for hazard in self.arena_hazards:
            hazard['lifetime'] -= 1
            if hazard['lifetime'] > 0:
                active_hazards.append(hazard)
        self.arena_hazards = active_hazards
