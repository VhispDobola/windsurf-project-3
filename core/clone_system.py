import pygame
import math
import random
from core.projectile import Projectile
from config.constants import WIDTH, HEIGHT, ORANGE, PURPLE, WHITE

class Clone:
    def __init__(self, x, y, is_real=False, phase=1, color=(100, 100, 100)):
        self.x = x
        self.y = y
        self.width = 60
        self.height = 60
        self.is_real = is_real
        self.lifetime = 240 if not is_real else 999999
        self.phase = phase
        self.alpha = 0.6 if not is_real else 1.0
        self.color = color if not is_real else (min(255, color[0] + 50), min(255, color[1] + 50), min(255, color[2] + 50))
        self.projectiles = []
        self.attack_cooldown = 0
        
    def update(self, boss_x, boss_y, game):
        self.lifetime -= 1
        self.attack_cooldown -= 1
        
        # Movement pattern
        speed = 1 + self.phase * 0.5
        self.x += math.sin(pygame.time.get_ticks() * 0.002) * speed
        self.y += math.cos(pygame.time.get_ticks() * 0.003) * speed * 0.8
        
        self.x = max(50, min(WIDTH - 110, self.x))
        self.y = max(50, min(HEIGHT - 160, self.y))
        
        # Attack logic for real clones
        if self.is_real and self.attack_cooldown <= 0 and game and game.player:
            self.attack(game.player)
            self.attack_cooldown = 120 - self.phase * 10
        else:
            # Fade effect for fake clones
            self.alpha = 0.3 + 0.3 * math.sin(self.lifetime * 0.04)
            
        active_projectiles = []
        for projectile in self.projectiles:
            projectile.update()
            if not projectile.is_off_screen():
                active_projectiles.append(projectile)
        self.projectiles = active_projectiles
                
        return self.lifetime > 0
        
    def attack(self, target):
        dx = target.x - self.x
        dy = target.y - self.y
        dist = math.sqrt(dx**2 + dy**2)
        if dist > 0:
            projectile_count = 2 + self.phase
            for i in range(projectile_count):
                angle = math.atan2(dy, dx) + (i - projectile_count//2) * 0.3
                dx = math.cos(angle) * 5
                dy = math.sin(angle) * 5
                self.projectiles.append(Projectile(
                    self.x + self.width // 2, self.y + self.height // 2,
                    dx, dy, 8, ORANGE, 5
                ))
        
    def draw(self, screen):
        color = tuple(int(c * self.alpha) for c in self.color)
        rect = pygame.Rect(int(self.x), int(self.y), self.width, self.height)
        pygame.draw.rect(screen, (0, 0, 0), rect.inflate(6, 6), border_radius=8)
        pygame.draw.rect(screen, color, rect, border_radius=6)
        if self.is_real:
            pygame.draw.rect(screen, WHITE, rect, 2, border_radius=6)
            
        for projectile in self.projectiles:
            projectile.draw(screen)

class MirrorClone(Clone):
    def __init__(self, x, y, is_real=False, phase=1):
        super().__init__(x, y, is_real, phase, (100, 50, 100))
        self.mirror_timer = 0
        
    def update(self, boss_x, boss_y, game):
        super().update(boss_x, boss_y, game)
        self.mirror_timer += 1
        
        # Mirror player movement when real
        if self.is_real and game and game.player:
            if self.mirror_timer % 30 == 0:
                target_x = game.player.x + random.randint(-50, 50)
                target_y = game.player.y + random.randint(-50, 50)
                self.x = max(50, min(WIDTH - 110, target_x))
                self.y = max(50, min(HEIGHT - 160, target_y))
                
                # Shoot at player periodically
                if random.random() < 0.2:
                    self.attack(game.player)
                    
    def draw(self, screen):
        color = tuple(int(c * self.alpha) for c in self.color)
        pygame.draw.rect(screen, color, (self.x, self.y, self.width, self.height))
        if self.is_real:
            pygame.draw.rect(screen, WHITE, (self.x, self.y, self.width, self.height), 2)
            
        for projectile in self.projectiles:
            projectile.draw(screen)

class CloneSystem:
    def __init__(self):
        self.clones = []
        
    def add_clone(self, x, y, is_real=False, phase=1, clone_type="normal"):
        if clone_type == "mirror":
            self.clones.append(MirrorClone(x, y, is_real, phase))
        else:
            self.clones.append(Clone(x, y, is_real, phase))
            
    def update(self, boss_x, boss_y, game):
        spawned_projectiles = []
        active_clones = []
        for clone in self.clones:
            if clone.update(boss_x, boss_y, game):
                active_clones.append(clone)
                # Return projectiles to main list
                if clone.projectiles:
                    spawned_projectiles.extend(clone.projectiles)
                    clone.projectiles.clear()
        self.clones = active_clones
        return spawned_projectiles
        
    def draw(self, screen):
        for clone in self.clones:
            clone.draw(screen)
            
    def clear(self):
        self.clones.clear()
