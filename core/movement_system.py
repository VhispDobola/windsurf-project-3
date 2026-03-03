import pygame
import math
import random
from config.constants import WIDTH, HEIGHT

class MovementPattern:
    """Base class for boss movement patterns"""
    def __init__(self, boss):
        self.boss = boss
        self.time = 0
        self.phase = 0
        
    def update(self):
        self.time += 1
        return 0, 0  # Return dx, dy
        
class SineWaveMovement(MovementPattern):
    """Enhanced sine wave with variable parameters"""
    def __init__(self, boss, amplitude_x=50, amplitude_y=30, frequency_x=0.001, frequency_y=0.0015):
        super().__init__(boss)
        self.amplitude_x = amplitude_x
        self.amplitude_y = amplitude_y
        self.frequency_x = frequency_x
        self.frequency_y = frequency_y
        
    def update(self):
        super().update()
        dx = math.sin(self.time * self.frequency_x) * self.amplitude_x
        dy = math.cos(self.time * self.frequency_y) * self.amplitude_y
        return dx, dy

class CircularMovement(MovementPattern):
    """Circular movement pattern"""
    def __init__(self, boss, radius=80, speed=0.002):
        super().__init__(boss)
        self.radius = radius
        self.speed = speed
        self.center_x = boss.x
        self.center_y = boss.y
        
    def update(self):
        super().update()
        angle = self.time * self.speed
        dx = math.cos(angle) * self.radius - (self.boss.x - self.center_x)
        dy = math.sin(angle) * self.radius - (self.boss.y - self.center_y)
        return dx, dy

class AggressiveChaseMovement(MovementPattern):
    """Aggressive movement towards player with prediction"""
    def __init__(self, boss, chase_speed=2, prediction_strength=0.3):
        super().__init__(boss)
        self.chase_speed = chase_speed
        self.prediction_strength = prediction_strength
        self.last_player_x = 0
        self.last_player_y = 0
        
    def update(self):
        super().update()
        if not self.boss.game or not self.boss.game.player:
            return 0, 0
            
        # Calculate player velocity for prediction
        player = self.boss.game.player
        player_vx = player.x - self.last_player_x
        player_vy = player.y - self.last_player_y
        
        # Predict future player position
        predicted_x = player.x + player_vx * self.prediction_strength * 10
        predicted_y = player.y + player_vy * self.prediction_strength * 10
        
        # Move towards predicted position
        dx = predicted_x - self.boss.x
        dy = predicted_y - self.boss.y
        dist = math.sqrt(dx**2 + dy**2)
        
        if dist > 0:
            dx = (dx / dist) * self.chase_speed
            dy = (dy / dist) * self.chase_speed
        else:
            dx, dy = 0, 0
            
        self.last_player_x = player.x
        self.last_player_y = player.y
        
        return dx, dy

class ErraticTeleportMovement(MovementPattern):
    """Erratic movement with teleportation"""
    def __init__(self, boss, teleport_chance=0.02, move_speed=1):
        super().__init__(boss)
        self.teleport_chance = teleport_chance
        self.move_speed = move_speed
        self.teleport_cooldown = 0
        
    def update(self):
        super().update()
        
        # Handle teleport cooldown
        if self.teleport_cooldown > 0:
            self.teleport_cooldown -= 1
            
        # Random teleportation
        if self.teleport_cooldown <= 0 and random.random() < self.teleport_chance:
            new_x = random.randint(50, WIDTH - self.boss.width - 50)
            new_y = random.randint(50, HEIGHT - self.boss.height - 50)
            return new_x - self.boss.x, new_y - self.boss.y
            
        # Normal erratic movement
        dx = math.sin(self.time * 0.0008) * self.move_speed
        dy = math.cos(self.time * 0.0012) * self.move_speed
        return dx, dy

class FigureEightMovement(MovementPattern):
    """Figure-8 movement pattern"""
    def __init__(self, boss, scale=60, speed=0.001):
        super().__init__(boss)
        self.scale = scale
        self.speed = speed
        
    def update(self):
        super().update()
        t = self.time * self.speed
        dx = math.sin(t) * self.scale
        dy = math.sin(t * 2) * self.scale * 0.5
        return dx, dy

class BossMovementController:
    """Controls boss movement with pattern switching"""
    def __init__(self, boss):
        self.boss = boss
        self.patterns = []
        self.current_pattern = 0
        self.pattern_timer = 0
        self.pattern_duration = 300  # 5 seconds per pattern
        
    def add_pattern(self, pattern):
        """Add a movement pattern to the rotation"""
        self.patterns.append(pattern)
        
    def update(self):
        """Update current movement pattern"""
        if not self.patterns:
            return 0, 0
            
        # Switch patterns periodically
        self.pattern_timer += 1
        if self.pattern_timer >= self.pattern_duration:
            self.pattern_timer = 0
            self.current_pattern = (self.current_pattern + 1) % len(self.patterns)
            
        # Get movement from current pattern
        pattern = self.patterns[self.current_pattern]
        return pattern.update()
        
    def set_phase(self, phase):
        """Change movement patterns based on boss phase"""
        # More aggressive patterns in later phases
        if phase >= 2:
            self.pattern_duration = 200  # Faster pattern switching
        if phase >= 3:
            self.pattern_duration = 150  # Even faster
