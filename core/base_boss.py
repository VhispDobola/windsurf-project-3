import pygame
import math
import random
from config.constants import WIDTH, HEIGHT, WHITE

class BaseBossMixin:
    """Mixin class providing common boss functionality"""
    
    def __init__(self):
        if not hasattr(self, 'movement_speed'):
            self.movement_speed = 2.0
        if not hasattr(self, 'boundary_margin'):
            self.boundary_margin = 50
    
    def safe_movement(self, dx=0, dy=0):
        """Apply movement with boundary checking"""
        self.x += dx
        self.y += dy
        
        # Keep within bounds
        self.x = max(self.boundary_margin, 
                    min(WIDTH - self.width - self.boundary_margin, self.x))
        self.y = max(self.boundary_margin, 
                    min(HEIGHT - self.height - self.boundary_margin, self.y))
        self.update_rect()
    
    def sine_wave_movement(self, amplitude_x=50, amplitude_y=30, freq_x=0.001, freq_y=0.0015):
        """Generate sine wave movement offsets"""
        time = pygame.time.get_ticks()
        dx = math.sin(time * freq_x) * amplitude_x
        dy = math.cos(time * freq_y) * amplitude_y
        return dx, dy
    
    def circular_movement(self, radius=60, speed=0.0015):
        """Generate circular movement offsets"""
        time = pygame.time.get_ticks()
        dx = math.cos(time * speed) * radius
        dy = math.sin(time * speed) * radius
        return dx, dy
    
    def random_teleport_movement(self, chance=0.02):
        """Random teleportation movement"""
        if random.random() < chance:
            self.x = random.randint(self.boundary_margin, 
                                  WIDTH - self.width - self.boundary_margin)
            self.y = random.randint(self.boundary_margin, 
                                  HEIGHT - self.height - self.boundary_margin)
            self.update_rect()
    
    def chase_player_movement(self, speed_multiplier=1.0):
        """Basic movement towards player"""
        if not self.game or not self.game.player:
            return 0, 0
            
        dx = self.game.player.x - self.x
        dy = self.game.player.y - self.y
        dist = math.sqrt(dx**2 + dy**2)
        
        if dist > 0:
            move_speed = self.movement_speed * speed_multiplier
            return (dx / dist) * move_speed, (dy / dist) * move_speed
        return 0, 0
    
    def update_attack_cooldowns(self, cooldown_dict):
        """Update multiple attack cooldowns from a dictionary"""
        for key in cooldown_dict:
            if cooldown_dict[key] > 0:
                cooldown_dict[key] -= 1
    
    def create_standard_projectile(self, target_x=None, target_y=None, speed=5.0, damage=10, size=8):
        """Create a standard projectile towards target or player"""
        from core.projectile import Projectile
        
        if target_x is None and self.game and self.game.player:
            target_x = self.game.player.x + self.game.player.width // 2
        if target_y is None and self.game and self.game.player:
            target_y = self.game.player.y + self.game.player.height // 2
            
        if target_x is not None and target_y is not None:
            # Calculate direction to target
            dx = target_x - (self.x + self.width // 2)
            dy = target_y - (self.y + self.height // 2)
            dist = math.sqrt(dx**2 + dy**2)
            
            if dist > 0:
                # Normalize and apply speed
                vel_x = (dx / dist) * speed
                vel_y = (dy / dist) * speed
                
                projectile = Projectile(
                    self.x + self.width // 2,
                    self.y + self.height // 2,
                    vel_x, vel_y, damage, getattr(self, 'color', WHITE), radius=size
                )
                self.projectiles.append(projectile)
                return projectile
        return None
    
    def create_radial_projectiles(self, count=8, speed=4.0, damage=8, size=6):
        """Create projectiles in all directions"""
        from core.projectile import Projectile
        
        for i in range(count):
            angle = (360 / count) * i
            rad = math.radians(angle)
            vel_x = math.cos(rad) * speed
            vel_y = math.sin(rad) * speed
            
            projectile = Projectile(
                self.x + self.width // 2,
                self.y + self.height // 2,
                vel_x, vel_y, damage, getattr(self, 'color', WHITE), radius=size
            )
            self.projectiles.append(projectile)
    
    def create_telegraphed_attack(self, x, y, width, height, duration=60, color=(255, 0, 0)):
        """Create a telegraphed attack warning"""
        from core.effect import Telegraph
        
        telegraph = Telegraph(x, y, width, height, color)
        telegraph.active_start = duration
        self.effects.append(telegraph)
        return telegraph
