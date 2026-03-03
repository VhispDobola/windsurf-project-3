import pygame
from config.constants import WIDTH, HEIGHT
from enum import Enum

class DamageType(Enum):
    NORMAL = "normal"
    FIRE = "fire"
    ICE = "ice"
    LIGHTNING = "lightning"
    SHADOW = "shadow"
    TIME = "time"
    VOID = "void"
    VIRAL = "viral"

class Entity:
    def __init__(self, x, y, width, height):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.rect = pygame.Rect(x, y, width, height)
        self.max_health = 100
        self.health = 100
        self.damage_cooldown = 0
        self.invulnerable = False
        self.damage_resistances = {}
        
    def update_rect(self):
        self.rect.x = self.x
        self.rect.y = self.y
        
    def get_rect(self):
        self.update_rect()
        return self.rect
    
    def check_collision(self, other):
        """Check collision with another entity"""
        return self.get_rect().colliderect(other.get_rect())
    
    def check_rect_collision(self, rect):
        """Check collision with a rectangle"""
        return self.get_rect().colliderect(rect)
    
    def take_damage(self, damage, damage_type=DamageType.NORMAL):
        """Take damage with type and resistance handling"""
        if self.invulnerable or self.damage_cooldown > 0:
            return False
            
        # Apply damage resistance
        if damage_type in self.damage_resistances:
            damage = int(damage * (1 - self.damage_resistances[damage_type]))
        
        self.health = max(0, self.health - damage)
        self.damage_cooldown = 30  # 0.5 seconds of invulnerability at 60 FPS
        return True
    
    def heal(self, amount):
        """Heal the entity"""
        self.health = min(self.max_health, self.health + amount)
    
    def set_damage_resistance(self, damage_type, resistance_percent):
        """Set damage resistance (0.0 to 1.0, where 1.0 = 100% resistance)"""
        self.damage_resistances[damage_type] = max(0, min(1.0, resistance_percent))
    
    def update_cooldowns(self):
        """Update all cooldown timers"""
        if self.damage_cooldown > 0:
            self.damage_cooldown -= 1
            if self.damage_cooldown <= 0:
                self.invulnerable = False
    
    def is_alive(self):
        """Check if entity is alive"""
        return self.health > 0
    
    def get_health_percentage(self):
        """Get health as percentage (0.0 to 1.0)"""
        return max(0, min(1.0, self.health / self.max_health))
