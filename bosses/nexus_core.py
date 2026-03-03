import pygame
import math
import random
from core.boss import Boss
from core.projectile import Projectile
from core.effect import Telegraph
from config.constants import WIDTH, HEIGHT, PURPLE, CYAN, ORANGE, RED, GREEN
from utils import load_image

class NexusCore(Boss):
    def __init__(self):
        super().__init__(WIDTH // 2 - 50, 100, 100, 100, 600, "Nexus Core")
        self.color = RED
        self.spiral_angle = 0
        self.spiral_cooldown = 0
        self.aimed_cooldown = 0
        self.pulse_cooldown = 0
        self.shield_angle = 0
        self.shield_active = False
        self.hazard_mode = False
        self.hazard_timer = 0
        self.arena_hazards = []
        self.hitbox_scale = 0.82
        
        # Hazard damage cooldown to prevent damage spam
        self.hazard_damage_cooldown = {}
        
        # Load the Nexus Core sprite
        try:
            self.sprite = load_image("assets", "sprites", "nexus_core.png")
            # Scale sprite to fit the boss dimensions
            self.sprite = pygame.transform.scale(self.sprite, (self.width, self.height))
            self.use_sprite = True
            self.logger.info("Nexus Core sprite loaded successfully")
        except Exception as e:
            # Fallback to drawn version if sprite not found
            self.use_sprite = False
            self.logger.warning("Nexus Core sprite not found - %s", e)
        
    def run_attacks(self):
        self.spiral_cooldown -= 1
        self.aimed_cooldown -= 1
        self.pulse_cooldown -= 1
        self.hazard_timer -= 1
        
        if self.phase == 1:
            if self.spiral_cooldown <= 0:
                self.spiral_pattern()
                self.spiral_cooldown = 55
            if self.aimed_cooldown <= 0:
                self.targeted_burst(count=4, spread=0.35, speed=5.8, damage=8)
                self.aimed_cooldown = 110
                
        elif self.phase == 2:
            if self.spiral_cooldown <= 0:
                self.double_spiral()
                self.spiral_cooldown = 45
            if self.aimed_cooldown <= 0:
                self.targeted_burst(count=6, spread=0.5, speed=6.2, damage=10)
                self.aimed_cooldown = 90
            if not self.shield_active:
                self.activate_shields()
            if self.pulse_cooldown <= 0:
                self.shield_pulse(damage=10, speed=5.5)
                self.pulse_cooldown = 130
                
        else:  # phase 3
            if self.spiral_cooldown <= 0:
                self.triple_spiral()
                self.spiral_cooldown = 30
            if self.aimed_cooldown <= 0:
                self.targeted_burst(count=8, spread=0.65, speed=6.8, damage=11)
                self.aimed_cooldown = 70
            if not self.shield_active:
                self.activate_shields()
            if self.pulse_cooldown <= 0:
                self.shield_pulse(damage=12, speed=6.2)
                self.pulse_cooldown = 100
            if self.hazard_timer <= 0:
                self.hazard_mode = True
                self.hazard_timer = 300
                self.create_arena_hazards()
                
        self.spiral_angle += 0.05
        self.shield_angle += 0.03
        
        if self.shield_active:
            self.update_shields()
            
        if self.hazard_mode:
            self.update_hazards()
            
    def spiral_pattern(self):
        for i in range(8):
            angle = self.spiral_angle + (math.pi * 2 * i) / 8
            dx = math.cos(angle) * 4
            dy = math.sin(angle) * 4
            self.projectiles.append(Projectile(
                self.x + self.width // 2,
                self.y + self.height // 2,
                dx, dy, 8, PURPLE, 6
            ))
            
    def double_spiral(self):
        for i in range(12):
            angle = self.spiral_angle + (math.pi * 2 * i) / 12
            dx = math.cos(angle) * 5
            dy = math.sin(angle) * 5
            self.projectiles.append(Projectile(
                self.x + self.width // 2,
                self.y + self.height // 2,
                dx, dy, 10, PURPLE, 7
            ))
            
        for i in range(12):
            angle = -self.spiral_angle + (math.pi * 2 * i) / 12
            dx = math.cos(angle) * 5
            dy = math.sin(angle) * 5
            self.projectiles.append(Projectile(
                self.x + self.width // 2,
                self.y + self.height // 2,
                dx, dy, 10, CYAN, 7
            ))
            
    def triple_spiral(self):
        colors = [PURPLE, CYAN, ORANGE]
        for spiral in range(3):
            for i in range(16):
                angle = self.spiral_angle * (spiral + 1) + (math.pi * 2 * i) / 16
                dx = math.cos(angle) * 6
                dy = math.sin(angle) * 6
                self.projectiles.append(Projectile(
                    self.x + self.width // 2,
                    self.y + self.height // 2,
                    dx, dy, 12, colors[spiral], 8
                ))

    def targeted_burst(self, count=5, spread=0.4, speed=6.0, damage=9):
        if not self.game or not self.game.player:
            return

        px = self.game.player.x + self.game.player.width // 2
        py = self.game.player.y + self.game.player.height // 2
        cx = self.x + self.width // 2
        cy = self.y + self.height // 2
        base_angle = math.atan2(py - cy, px - cx)

        for i in range(count):
            t = 0 if count == 1 else (i / (count - 1))
            angle = base_angle + (t - 0.5) * spread
            dx = math.cos(angle) * speed
            dy = math.sin(angle) * speed
            self.projectiles.append(Projectile(cx, cy, dx, dy, damage, ORANGE, 6))

    def shield_pulse(self, damage=10, speed=5.5):
        if not self.shield_active:
            return

        for i in range(4):
            angle = self.shield_angle + (math.pi * 2 * i) / 4
            shield_x = self.x + self.width // 2 + math.cos(angle) * 80
            shield_y = self.y + self.height // 2 + math.sin(angle) * 80
            dx = math.cos(angle) * speed
            dy = math.sin(angle) * speed
            self.projectiles.append(Projectile(shield_x, shield_y, dx, dy, damage, CYAN, 6))
                
    def activate_shields(self):
        self.shield_active = True
        for i in range(4):
            angle = self.shield_angle + (math.pi * 2 * i) / 4
            shield_x = self.x + self.width // 2 + math.cos(angle) * 80
            shield_y = self.y + self.height // 2 + math.sin(angle) * 80
            self.effects.append(Telegraph(shield_x, shield_y, 20, 20, GREEN))
            
    def update_shields(self):
        if not self.game:
            return
        shield_rects = []
        for i in range(4):
            angle = self.shield_angle + (math.pi * 2 * i) / 4
            shield_x = self.x + self.width // 2 + math.cos(angle) * 80
            shield_y = self.y + self.height // 2 + math.sin(angle) * 80
            shield_rects.append(pygame.Rect(shield_x - 15, shield_y - 15, 30, 30))

        remaining_projectiles = []
        for projectile in self.game.player.projectiles:
            projectile_rect = projectile.get_rect()
            blocked = any(shield_rect.colliderect(projectile_rect) for shield_rect in shield_rects)
            if not blocked:
                remaining_projectiles.append(projectile)
        self.game.player.projectiles = remaining_projectiles
                    
    def create_arena_hazards(self):
        for i in range(5):
            x = random.randint(100, WIDTH - 100)
            y = random.randint(200, HEIGHT - 100)
            self.arena_hazards.append({
                'x': x,
                'y': y,
                'radius': 30,
                'lifetime': 240,
                'damage': 12,
                'damage_cooldown': 45,
                'ability_name': 'Arena Hazard',
            })
            
    def update_hazards(self):
        if not self.game:
            return
        active_hazards = []
        for hazard in self.arena_hazards:
            hazard['lifetime'] -= 1
            if hazard['lifetime'] > 0:
                active_hazards.append(hazard)
        self.arena_hazards = active_hazards
                    
        if self.hazard_timer < 60 and self.hazard_timer > 0:
            self.hazard_mode = False

    def get_rect(self):
        """Use a centered hitbox that better matches the core body."""
        hb_w = int(self.width * self.hitbox_scale)
        hb_h = int(self.height * self.hitbox_scale)
        hb_x = int(self.x + (self.width - hb_w) / 2)
        hb_y = int(self.y + (self.height - hb_h) / 2)
        self.rect = pygame.Rect(hb_x, hb_y, hb_w, hb_h)
        return self.rect
            
    def draw(self, screen):
        # Draw the sprite or fallback
        if hasattr(self, 'use_sprite') and self.use_sprite:
            # Draw the Nexus Core sprite
            self.draw_sprite_to_hitbox(screen)
            # Draw active attacks/effects in sprite mode.
            for projectile in self.projectiles:
                projectile.draw(screen)
            for effect in self.effects:
                effect.draw(screen)
        else:
            # Fallback already draws projectiles/effects.
            super().draw(screen)
        
        if self.shield_active:
            for i in range(4):
                angle = self.shield_angle + (math.pi * 2 * i) / 4
                shield_x = self.x + self.width // 2 + math.cos(angle) * 80
                shield_y = self.y + self.height // 2 + math.sin(angle) * 80
                pygame.draw.circle(screen, GREEN, (int(shield_x), int(shield_y)), 15, 3)
                
        if self.hazard_mode:
            for hazard in self.arena_hazards:
                alpha = hazard['lifetime'] / 240
                color = (255, int(100 * alpha), 0)
                pygame.draw.circle(screen, color, (hazard['x'], hazard['y']), hazard['radius'], 2)

        # Ensure HP bar always renders in sprite mode.
        self.health_bar_color = RED
        self.draw_health_bar(screen)


