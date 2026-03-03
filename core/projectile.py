import pygame
import math
import random
from .entity import Entity, DamageType
from .render_layers import RenderLayer
from config.constants import WIDTH, HEIGHT, PROJECTILE_DEFAULT_LIFETIME, PROJECTILE_OFFSCREEN_BUFFER

class ProjectileBehavior:
    HOMING = "homing"
    SEEKING = "seeking" 
    REWIND = "rewind"
    LASER = "laser"
    DIAMOND = "diamond"
    GLITCH = "glitch"
    PHOENIX = "phoenix"
    MUTATION = "mutation"
    ANTIBODY = "antibody"
    CHAIN = "chain"
    PIERCING = "piercing"
    SPIRAL = "spiral"
    SPIRAL_REVERSE = "spiral_reverse"
    BOUNCING = "bouncing"

class Projectile(Entity):
    def __init__(self, x, y, dx, dy, damage, color, radius=5, damage_type=DamageType.NORMAL, behavior=None):
        super().__init__(x, y, radius * 2, radius * 2)
        self.dx = dx
        self.dy = dy
        self.damage = damage
        self.color = color
        self.radius = radius
        self.damage_type = damage_type
        self.behavior = behavior
        self.time_stopped = False
        self.render_layer = RenderLayer.PROJECTILES
        self.glow = True
        self.outline = True
        self.lifetime = PROJECTILE_DEFAULT_LIFETIME
        self.age = 0
        
        # Behavior-specific properties
        self.target_x = None
        self.target_y = None
        self.piercing_count = 0
        self.max_piercing = 0

    def steer_towards(self, target_x, target_y, desired_speed=None, max_turn=0.08, accel=0.25):
        """Turn toward a target with a capped angular velocity to avoid instant reversals."""
        tx = target_x - self.x
        ty = target_y - self.y
        dist = math.sqrt(tx * tx + ty * ty)
        if dist <= 0:
            return

        current_speed = math.sqrt(self.dx * self.dx + self.dy * self.dy)
        if current_speed < 0.001:
            current_angle = math.atan2(ty, tx)
            current_speed = desired_speed if desired_speed is not None else 4.0
        else:
            current_angle = math.atan2(self.dy, self.dx)

        target_angle = math.atan2(ty, tx)
        delta = target_angle - current_angle
        while delta > math.pi:
            delta -= math.pi * 2
        while delta < -math.pi:
            delta += math.pi * 2

        delta = max(-max_turn, min(max_turn, delta))
        new_angle = current_angle + delta

        target_speed = desired_speed if desired_speed is not None else current_speed
        new_speed = current_speed + (target_speed - current_speed) * max(0.0, min(1.0, accel))

        self.dx = math.cos(new_angle) * new_speed
        self.dy = math.sin(new_angle) * new_speed
        
    def update(self):
        # Handle delay before activation
        if hasattr(self, 'delay') and self.delay > 0:
            self.delay -= 1
            self.update_cooldowns()
            self.update_rect()
            return  # Skip all other updates during delay
        
        if not self.time_stopped:
            # Basic movement
            self.x += self.dx
            self.y += self.dy
            
            # Behavior-based movement
            if self.behavior == ProjectileBehavior.HOMING and self.target_x is not None:
                self.steer_towards(self.target_x, self.target_y, desired_speed=5.6, max_turn=0.05, accel=0.18)
                    
            elif self.behavior == ProjectileBehavior.SEEKING and self.target_x is not None:
                self.steer_towards(self.target_x, self.target_y, desired_speed=7.0, max_turn=0.08, accel=0.28)
                    
            elif self.behavior == ProjectileBehavior.REWIND:
                self.dy *= -0.98
                self.dx *= 0.98
                
            elif self.behavior == ProjectileBehavior.GLITCH:
                if random.random() < 0.1:
                    self.dx += random.uniform(-2, 2)
                    self.dy += random.uniform(-2, 2)
                    
            elif self.behavior == ProjectileBehavior.MUTATION:
                if random.random() < 0.05:
                    self.damage += 1
                    self.radius = min(self.radius + 1, 15)
                    
            elif self.behavior == ProjectileBehavior.BOUNCING:
                # Bounce off walls - use screen dimensions from game if available
                screen_width = WIDTH
                screen_height = HEIGHT
                
                # Try to get actual screen dimensions
                if hasattr(self, '_game_ref') and self._game_ref and hasattr(self._game_ref, 'screen'):
                    screen_width = self._game_ref.screen.get_width()
                    screen_height = self._game_ref.screen.get_height()
                
                if self.x <= 0 or self.x >= screen_width - self.width:
                    self.dx = -self.dx
                if self.y <= 0 or self.y >= screen_height - self.height:
                    self.dy = -self.dy
                    
            elif self.behavior == ProjectileBehavior.SPIRAL:
                # Spiral movement pattern
                time = pygame.time.get_ticks() * 0.001
                angle = math.atan2(self.dy, self.dx) + time * 2
                speed = math.sqrt(self.dx**2 + self.dy**2)
                self.dx = math.cos(angle) * speed
                self.dy = math.sin(angle) * speed
                
            elif self.behavior == ProjectileBehavior.SPIRAL_REVERSE:
                # Reverse spiral movement pattern
                time = pygame.time.get_ticks() * 0.001
                angle = math.atan2(self.dy, self.dx) - time * 2
                speed = math.sqrt(self.dx**2 + self.dy**2)
                self.dx = math.cos(angle) * speed
                self.dy = math.sin(angle) * speed
        
        # Update age and lifetime
        self.age += 1
        self.update_cooldowns()
        self.update_rect()
        
    def is_expired(self):
        """Check if projectile should be removed"""
        return self.age >= self.lifetime or self.is_off_screen()
        
    def draw(self, screen):
        # Check for custom sprite first
        if hasattr(self, 'use_custom_sprite') and self.use_custom_sprite:
            # Draw custom sprite
            if hasattr(self, 'custom_sprite') and self.custom_sprite:
                # Scale sprite to appropriate size
                sprite_size = getattr(self, 'sprite_size', self.radius * 2)
                scaled_sprite = pygame.transform.scale(self.custom_sprite, (sprite_size, sprite_size))
                
                # Center the sprite on projectile position
                sprite_rect = scaled_sprite.get_rect()
                sprite_rect.center = (self.x + self.width // 2, self.y + self.height // 2)
                screen.blit(scaled_sprite, sprite_rect)
            return
        
        # Draw circle at the center of the rect
        center_x = self.x + self.width // 2
        center_y = self.y + self.height // 2
        cx = int(center_x)
        cy = int(center_y)

        if self.glow:
            glow_radius = max(self.radius + 6, 8)
            glow_surf = pygame.Surface((glow_radius * 2, glow_radius * 2), pygame.SRCALPHA)
            glow_color = (self.color[0], self.color[1], self.color[2], 70)
            pygame.draw.circle(glow_surf, glow_color, (glow_radius, glow_radius), glow_radius)
            screen.blit(glow_surf, (cx - glow_radius, cy - glow_radius))

        if self.outline:
            pygame.draw.circle(screen, (0, 0, 0), (cx, cy), self.radius + 2)

        pygame.draw.circle(screen, self.color, (cx, cy), self.radius)
        
    def is_off_screen(self):
        # Use screen dimensions from game if available, otherwise configured defaults
        screen_width = WIDTH
        screen_height = HEIGHT
        
        # Try to get actual screen dimensions
        if hasattr(self, '_game_ref') and self._game_ref and hasattr(self._game_ref, 'screen'):
            screen_width = self._game_ref.screen.get_width()
            screen_height = self._game_ref.screen.get_height()
            
        return (
            self.x < -PROJECTILE_OFFSCREEN_BUFFER
            or self.x > screen_width + PROJECTILE_OFFSCREEN_BUFFER
            or self.y < -PROJECTILE_OFFSCREEN_BUFFER
            or self.y > screen_height + PROJECTILE_OFFSCREEN_BUFFER
        )
    
    def set_piercing(self, max_piercing):
        """Set piercing behavior"""
        self.behavior = ProjectileBehavior.PIERCING
        self.max_piercing = max_piercing
        self.piercing_count = 0
    
    def on_hit(self):
        """Called when projectile hits something"""
        if self.behavior == ProjectileBehavior.PIERCING:
            self.piercing_count += 1
            if self.piercing_count >= self.max_piercing:
                return True  # Remove projectile
        return False  # Keep projectile unless it's expired
