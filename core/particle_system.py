import pygame
import math
import random

class Particle:
    def __init__(self, x, y, dx, dy, color, lifetime, size=3):
        self.x = x
        self.y = y
        self.dx = dx
        self.dy = dy
        self.color = color
        self.lifetime = lifetime
        self.max_lifetime = lifetime
        self.size = size
        
    def update(self):
        self.x += self.dx
        self.y += self.dy
        self.lifetime -= 1
        self.dx *= 0.98  # Friction
        self.dy *= 0.98
        return self.lifetime > 0
        
    def draw(self, screen):
        alpha = self.lifetime / self.max_lifetime
        size = int(self.size * alpha)
        if size > 0:
            pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), size)

class TimeOrb(Particle):
    def __init__(self, x, y, orb_type="slow", sprite=None):
        super().__init__(x, y, 0, 0, (0, 255, 255), 180, 20)
        self.orb_type = orb_type
        self.pulse = 0
        self.sprite = sprite
        
    def update(self):
        super().update()
        self.pulse += 0.1
        return self.lifetime > 0
        
    def draw(self, screen):
        pulse_size = int(self.size + 5 * math.sin(self.pulse))
        color = (0, 255, 255) if self.orb_type == "slow" else (255, 165, 0) if self.orb_type == "fast" else (0, 255, 0)
        if self.sprite:
            sprite_size = max(10, pulse_size * 2)
            scaled = pygame.transform.smoothscale(self.sprite, (sprite_size, sprite_size))
            rect = scaled.get_rect(center=(int(self.x), int(self.y)))
            screen.blit(scaled, rect)
            return
        pygame.draw.circle(screen, color, (int(self.x), int(self.y)), pulse_size, 2)
        pygame.draw.circle(screen, color, (int(self.x), int(self.y)), pulse_size // 2)

class ParticleSystem:
    def __init__(self):
        self.particles = []
        
    def add_particle(self, x, y, dx, dy, color, lifetime, size=3):
        self.particles.append(Particle(x, y, dx, dy, color, lifetime, size))
        
    def add_time_orb(self, x, y, orb_type="slow", sprite=None):
        self.particles.append(TimeOrb(x, y, orb_type, sprite=sprite))
        
    def add_burst(self, x, y, count, color, lifetime=40, speed_range=(2, 6)):
        for _ in range(count):
            dx = random.uniform(-speed_range[1], speed_range[1])
            dy = random.uniform(-speed_range[1], speed_range[1])
            size = random.randint(2, 5)
            self.particles.append(Particle(x, y, dx, dy, color, lifetime, size))
            
    def update(self):
        for particle in self.particles[:]:
            if not particle.update():
                self.particles.remove(particle)
                
    def draw(self, screen):
        for particle in self.particles:
            particle.draw(screen)
            
    def clear(self):
        self.particles.clear()
