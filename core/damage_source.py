"""
Damage Source Interface
Provides a unified way to handle different types of damage sources
"""

import pygame
from abc import ABC, abstractmethod
from typing import Optional, List, Tuple


class DamageSource(ABC):
    """Base class for all damage sources"""
    
    def __init__(self, source_type: str):
        self.source_type = source_type
        self.active = True
        
    @abstractmethod
    def update(self):
        """Update the damage source"""
        pass
        
    @abstractmethod
    def check_collision(self, target_rect: pygame.Rect, target_id=None) -> int:
        """Check collision and return damage amount"""
        pass
        
    @abstractmethod
    def draw(self, screen):
        """Draw the damage source"""
        pass
        
    def deactivate(self):
        """Deactivate the damage source"""
        self.active = False


class ProjectileDamageSource(DamageSource):
    """Wrapper for projectiles to work with damage source interface"""
    
    def __init__(self, projectile):
        super().__init__("projectile")
        self.projectile = projectile
        
    def update(self):
        return self.projectile.update()
        
    def check_collision(self, target_rect: pygame.Rect, target_id=None) -> int:
        if self.projectile.get_rect().colliderect(target_rect):
            return self.projectile.damage
        return 0
        
    def draw(self, screen):
        self.projectile.draw(screen)
        
    def deactivate(self):
        # Remove projectile from its parent list
        if hasattr(self.projectile, 'parent_list') and self.projectile.parent_list is not None:
            if self.projectile in self.projectile.parent_list:
                self.projectile.parent_list.remove(self.projectile)


class TelegraphDamageSource(DamageSource):
    """Wrapper for telegraphs to work with damage source interface"""
    
    def __init__(self, telegraph):
        super().__init__("telegraph")
        self.telegraph = telegraph
        
    def update(self):
        return self.telegraph.update()
        
    def check_collision(self, target_rect: pygame.Rect, target_id=None) -> int:
        if hasattr(self.telegraph, 'check_collision'):
            return self.telegraph.check_collision(target_rect)
        return 0
        
    def draw(self, screen):
        self.telegraph.draw(screen)
        
    def deactivate(self):
        # Telegraphs auto-deactivate when duration expires
        pass


class HazardDamageSource(DamageSource):
    """Wrapper for hazards to work with damage source interface"""
    
    def __init__(self, hazard, damage_cooldown_dict):
        super().__init__("hazard")
        self.hazard = hazard
        self.damage_cooldown_dict = damage_cooldown_dict
        
    def update(self):
        # Hazard lifetime is managed by boss update, not here
        pass
        
    def check_collision(self, target_rect: pygame.Rect, target_id=None) -> int:
        # Use radius if available, otherwise fall back to size
        hazard_radius = self.hazard.get('radius', self.hazard.get('size', 10))
        hazard_rect = pygame.Rect(
            self.hazard['x'] - hazard_radius,
            self.hazard['y'] - hazard_radius,
            hazard_radius * 2,
            hazard_radius * 2
        )
        
        if hazard_rect.colliderect(target_rect):
            # Check cooldown using hazard ID
            if target_id is None:
                target_id = "default"
            hazard_id = (id(self.hazard), target_id)
            if (hazard_id not in self.damage_cooldown_dict or 
                self.damage_cooldown_dict[hazard_id] <= 0):
                dmg = self.hazard.get('damage', 20)
                self.damage_cooldown_dict[hazard_id] = self.hazard.get('damage_cooldown', 60)
                return dmg
        return 0
        
    def draw(self, screen):
        # Draw hazard
        alpha = self.hazard['lifetime'] / self.hazard.get('max_lifetime', 180)
        size = int(20 * (1 - alpha) + 10)
        color = self.hazard.get('color', (255, 0, 0))
        pygame.draw.circle(screen, color, (int(self.hazard['x']), int(self.hazard['y'])), size, 2)
        
    def deactivate(self):
        return
