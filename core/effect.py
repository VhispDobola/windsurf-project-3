import pygame
import math
from config.constants import WHITE

class Effect:
    def __init__(self, x, y, duration, color):
        self.x = x
        self.y = y
        self.duration = duration
        self.max_duration = duration
        self.color = color
        
    def update(self):
        self.duration -= 1
        return self.duration > 0
        
    def draw(self, screen):
        alpha = self.duration / self.max_duration
        size = int(20 * (1 - alpha) + 10)
        pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), size, 2)

class Telegraph(Effect):
    def __init__(self, x, y, duration, radius, color, damage=0, warning_type="circle"):
        super().__init__(x, y, duration, color)
        self.radius = int(radius)
        self.damage = damage
        self.active_start = 0
        self.active_end = 0
        self.warning_type = warning_type  # "circle", "cross", "arrow", "pulse"
        self.pulse_phase = 0
        
    def update(self):
        self.duration -= 1
        self.pulse_phase += 0.2
        return self.duration > 0
        
    def draw(self, screen):
        alpha = self.duration / self.max_duration
        elapsed = self.max_duration - self.duration
        is_active = elapsed >= self.active_start and (self.active_end <= 0 or elapsed <= self.active_end)
        
        if self.warning_type == "circle":
            # Pulsing circle with clear warning
            pulse = 1 + 0.3 * math.sin(self.pulse_phase)
            width = max(1, int(4 * alpha * pulse))
            pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), self.radius, width)
            
            # Inner circle for danger indication
            if self.duration < self.max_duration * 0.3:  # Last 30% of duration
                danger_width = max(2, int(6 * alpha))
                pygame.draw.circle(screen, (255, 100, 100), (int(self.x), int(self.y)), self.radius // 2, danger_width)

            if is_active:
                pygame.draw.circle(screen, (255, 50, 50), (int(self.x), int(self.y)), max(4, self.radius // 3), 0)
                
        elif self.warning_type == "cross":
            # Cross pattern for directional attacks
            width = max(2, int(4 * alpha))
            cross_size = self.radius
            pygame.draw.line(screen, self.color, 
                           (self.x - cross_size, self.y), 
                           (self.x + cross_size, self.y), width)
            pygame.draw.line(screen, self.color, 
                           (self.x, self.y - cross_size), 
                           (self.x, self.y + cross_size), width)
            if is_active:
                pygame.draw.circle(screen, (255, 50, 50), (int(self.x), int(self.y)), max(6, self.radius // 4), 0)
                           
        elif self.warning_type == "arrow":
            # Arrow pointing to danger direction
            width = max(2, int(4 * alpha))
            pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), self.radius, width)
            # Draw arrow pointing outward
            for angle in range(0, 360, 90):
                end_x = self.x + math.cos(math.radians(angle)) * (self.radius + 20)
                end_y = self.y + math.sin(math.radians(angle)) * (self.radius + 20)
                pygame.draw.line(screen, self.color, (self.x, self.y), (end_x, end_y), width)
            if is_active:
                pygame.draw.circle(screen, (255, 50, 50), (int(self.x), int(self.y)), max(6, self.radius // 4), 0)
                
        elif self.warning_type == "pulse":
            # Rapid pulsing effect
            pulse_size = self.radius * (1 + 0.5 * math.sin(self.pulse_phase * 2))
            width = max(1, int(3 * alpha))
            pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), int(pulse_size), width)
            if is_active:
                pygame.draw.circle(screen, (255, 50, 50), (int(self.x), int(self.y)), max(6, self.radius // 4), 0)

    def check_collision(self, target_rect: pygame.Rect) -> int:
        if self.damage <= 0:
            return 0

        elapsed = self.max_duration - self.duration
        if elapsed < self.active_start:
            return 0
        if self.active_end > 0 and elapsed > self.active_end:
            return 0

        dx = target_rect.centerx - self.x
        dy = target_rect.centery - self.y
        if (dx * dx + dy * dy) <= (self.radius * self.radius):
            return self.damage

        return 0
