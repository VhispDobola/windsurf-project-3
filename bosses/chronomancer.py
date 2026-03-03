import pygame
import math
import random
from bosses.boss_base import BaseBoss
from core.projectile import Projectile, ProjectileBehavior
from core.effect import Telegraph
from core.particle_system import ParticleSystem, TimeOrb
from core.entity import DamageType
from config.constants import WIDTH, HEIGHT, RED, BLUE, GREEN, YELLOW, PURPLE, ORANGE, CYAN, WHITE
from utils import load_image_with_transparency

class Chronomancer(BaseBoss):
    def __init__(self):
        super().__init__(WIDTH // 2 - 50, 100, 100, 100, 750, "Chronomancer")
        self.color = CYAN
        self.time_orbs = []
        self.time_field_active = False
        self.time_field_timer = 0
        self.rewind_cooldown = 0
        self.freeze_cooldown = 0
        self.time_bullets = []
        self.paradox_mode = False
        self.paradox_timer = 0
        self.time_stop_active = False
        self.time_stop_duration = 0
        self.time_stop_cooldown = 0
        self.time_stop_warning = 0  # Add warning timer
        self.phantom_mode = False
        self.clockwork_cooldown = 0
        self.particle_system = ParticleSystem()
        
        # Load the Chronomancer sprite
        try:
            self.sprite = load_image_with_transparency("assets", "sprites", "chronomancer.png", transparent_color=(0, 0, 0))
            # Scale sprite to fit the boss dimensions
            self.sprite = pygame.transform.scale(self.sprite, (self.width, self.height))
            self.use_sprite = True
            self.logger.info("Chronomancer sprite loaded successfully")
        except Exception as e:
            # Fallback to drawn version if sprite not found
            self.use_sprite = False
            self.logger.warning("Chronomancer sprite not found - %s", e)

        try:
            self.time_orb_sprite = load_image_with_transparency("assets", "sprites", "time_orbs.png", transparent_color=(0, 0, 0))
        except Exception:
            self.time_orb_sprite = None
        
    def run_attacks(self):
        self.time_field_timer -= 1
        self.rewind_cooldown -= 1
        self.freeze_cooldown -= 1
        self.paradox_timer -= 1
        self.time_stop_cooldown -= 1
        self.time_stop_duration -= 1
        self.time_stop_warning -= 1
        self.clockwork_cooldown -= 1
        
        if self.time_stop_duration <= 0:
            self.time_stop_active = False
        
        if self.phase == 1:
            if self.time_field_timer <= 0:
                self.create_time_field("slow")
                self.time_field_timer = 150
            elif self.rewind_cooldown <= 0:
                self.time_rewind_bullets()
                self.rewind_cooldown = 120
            elif self.clockwork_cooldown <= 0:
                self.clockwork_barrage()
                self.clockwork_cooldown = 180
            elif self.time_stop_cooldown <= 0:
                self.time_stop_cooldown = 300
                self.time_stop_warning = 60  # 1 second warning
                
        elif self.phase == 2:
            if self.time_field_timer <= 0:
                field_type = "slow" if random.random() < 0.5 else "fast"
                self.create_time_field(field_type)
                self.time_field_timer = 100
            elif self.rewind_cooldown <= 0:
                self.time_rewind_bullets()
                self.rewind_cooldown = 90
            elif self.freeze_cooldown <= 0:
                self.time_freeze_burst()
                self.freeze_cooldown = 180
            elif self.clockwork_cooldown <= 0:
                self.clockwork_barrage(denser=True)
                self.clockwork_cooldown = 150
            elif self.time_stop_cooldown <= 0:
                self.time_stop_cooldown = 250
                self.time_stop_warning = 60
                
        else:  # phase 3
            if self.time_field_timer <= 0:
                self.create_time_field("slow")
                self.create_time_field("fast")
                self.time_field_timer = 80
            elif self.rewind_cooldown <= 0:
                self.advanced_rewind_pattern()
                self.rewind_cooldown = 70
            elif self.freeze_cooldown <= 0:
                self.time_freeze_burst()
                self.freeze_cooldown = 120
            elif self.paradox_timer <= 0:
                self.paradox_mode = True
                self.paradox_timer = 240
                self.create_paradox_field()
            elif self.clockwork_cooldown <= 0:
                self.clockwork_barrage(denser=True, homing=True)
                self.clockwork_cooldown = 110
            elif self.time_stop_cooldown <= 0:
                self.time_stop_cooldown = 200
                self.time_stop_warning = 60
                
        # Activate time stop after warning
        if self.time_stop_warning <= 0 and self.time_stop_warning > -1:
            self.activate_time_stop()
                
        self.movement()
        self.update_time_orbs()
        self.update_time_bullets()
        
    def create_time_field(self, field_type):
        orb_x = random.randint(100, WIDTH - 100)
        orb_y = random.randint(100, HEIGHT - 200)
        self.particle_system.add_time_orb(orb_x, orb_y, field_type, sprite=self.time_orb_sprite)
        self.effects.append(Telegraph(orb_x, orb_y, 60, 60, CYAN if field_type == "slow" else ORANGE))
        
    def time_rewind_bullets(self):
        for i in range(6):
            angle = (math.pi * 2 * i) / 6
            dx = math.cos(angle) * 3
            dy = math.sin(angle) * 3
            bullet = Projectile(
                self.x + self.width // 2, self.y + self.height // 2,
                dx, dy, 8, CYAN, 6
            )
            bullet.rewind = True
            self.time_bullets.append(bullet)
            
    def advanced_rewind_pattern(self):
        # Spiral pattern with rewind bullets
        for i in range(12):
            angle = (math.pi * 2 * i) / 12 + pygame.time.get_ticks() * 0.001
            dx = math.cos(angle) * 4
            dy = math.sin(angle) * 4
            bullet = Projectile(
                self.x + self.width // 2, self.y + self.height // 2,
                dx, dy, 10, CYAN, 7
            )
            bullet.rewind = True
            self.time_bullets.append(bullet)
            
    def time_freeze_burst(self):
        if self.game and self.game.player:
            # Create freeze effect around player
            player_x = self.game.player.x + self.game.player.width // 2
            player_y = self.game.player.y + self.game.player.height // 2
            
            for i in range(16):
                angle = (math.pi * 2 * i) / 16
                dx = math.cos(angle) * 2
                dy = math.sin(angle) * 2
                bullet = Projectile(
                    player_x, player_y,
                    dx, dy, 5, (150, 150, 255), 4
                )
                bullet.freeze = True
                self.time_bullets.append(bullet)
                
            self.effects.append(Telegraph(player_x, player_y, 80, 80, (150, 150, 255)))
            
    def activate_time_stop(self):
        # Check if player is dashing - if so, cancel time stop
        if self.game and self.game.player and self.game.player.dash_duration > 0:
            return  # Player avoided time stop by dashing
            
        # Reduced duration and added counterplay
        self.time_stop_active = True
        self.time_stop_duration = 60  # Reduced from 120 to 60 (1 second instead of 2)
        
        # Create time stop visual effect with better warning
        for i in range(24):
            angle = (math.pi * 2 * i) / 24
            x = self.x + self.width // 2 + math.cos(angle) * 100
            y = self.y + self.height // 2 + math.sin(angle) * 100
            self.effects.append(Telegraph(x, y, 30, 30, (255, 255, 255)))
            
        # Add screen shake
        if self.game:
            self.game.screen_shake.start(2, 8)
            
    def create_paradox_field(self):
        # Create multiple overlapping time fields
        for i in range(3):
            orb_x = self.x + (i - 1) * 150
            orb_y = self.y + 50
            self.particle_system.add_time_orb(orb_x, orb_y, "paradox", sprite=self.time_orb_sprite)

    def clockwork_barrage(self, denser=False, homing=False):
        """Launch temporal clockwork shards that can slightly home in phase 3."""
        ring = 10 if denser else 7
        speed = 4.6 if denser else 4.0
        cx = self.x + self.width // 2
        cy = self.y + self.height // 2
        for i in range(ring):
            angle = (math.pi * 2 * i) / ring + random.uniform(-0.08, 0.08)
            bullet = Projectile(cx, cy, math.cos(angle) * speed, math.sin(angle) * speed, 9, CYAN, 6)
            bullet.clockwork = True
            bullet.mini_time_stop = True
            bullet.homing_temporal = homing
            self.time_bullets.append(bullet)
            
    def movement(self):
        self.x += math.sin(pygame.time.get_ticks() * 0.0008) * 3
        self.y += math.cos(pygame.time.get_ticks() * 0.0012) * 2
        
        self.x = max(50, min(WIDTH - 150, self.x))
        self.y = max(50, min(HEIGHT - 200, self.y))
        self.update_rect()
        
    def update_time_orbs(self):
        self.particle_system.update()
        
        # Apply time effects to player if in range
        player = self.game.player if self.game and hasattr(self.game, 'player') and self.game.player else None
        if player:
            for particle in self.particle_system.particles:
                if isinstance(particle, TimeOrb):
                    dist = math.sqrt((player.x - particle.x)**2 + (player.y - particle.y)**2)
                    if dist < particle.size + 20:
                        if particle.orb_type == "slow":
                            player.add_speed_modifier(0.5, 60)  # Slow to 50% for 1 second
                        elif particle.orb_type == "fast":
                            player.add_speed_modifier(2.0, 60)  # Speed up to 200% for 1 second
                            
        # Apply time stop effect to all game elements with reduced impact
        if self.time_stop_active and self.game and self.game.player:
            self.game.player.time_stopped = True
            self.game.player.set_speed_override(0.7, 60)  # Reduced from 0.5 to 0.7, less severe
            
            # Freeze player projectiles but allow some movement
            for projectile in self.game.player.projectiles[:]:
                if not hasattr(projectile, 'original_dx'):
                    projectile.original_dx = projectile.dx
                    projectile.original_dy = projectile.dy
                projectile.time_stopped = True
                # Allow slow movement instead of complete freeze
                if hasattr(projectile, 'dx'):
                    projectile.dx *= 0.1
                    projectile.dy *= 0.1
                
            # Freeze boss projectiles with reduced effect
            for projectile in self.projectiles[:]:
                if not hasattr(projectile, 'original_dx'):
                    projectile.original_dx = projectile.dx
                    projectile.original_dy = projectile.dy
                projectile.time_stopped = True
                if hasattr(projectile, 'dx'):
                    projectile.dx *= 0.2
                    projectile.dy *= 0.2
                
        elif self.game and self.game.player:
            self.game.player.time_stopped = False
            # Don't reset speed here - let the status effect system handle it
            
            # Unfreeze all projectiles and restore original speeds
            for projectile in self.game.player.projectiles[:]:
                projectile.time_stopped = False
                if hasattr(projectile, 'original_dx'):
                    projectile.dx = projectile.original_dx
                    projectile.dy = projectile.original_dy
                    delattr(projectile, 'original_dx')
                    delattr(projectile, 'original_dy')
                
            for projectile in self.projectiles[:]:
                projectile.time_stopped = False
                if hasattr(projectile, 'original_dx'):
                    projectile.dx = projectile.original_dx
                    projectile.dy = projectile.original_dy
                    delattr(projectile, 'original_dx')
                    delattr(projectile, 'original_dy')
                            
    def update_time_bullets(self):
        for bullet in self.time_bullets[:]:
            if hasattr(bullet, 'homing_temporal') and bullet.homing_temporal and self.game and self.game.player:
                tx = self.game.player.x + self.game.player.width // 2
                ty = self.game.player.y + self.game.player.height // 2
                if hasattr(bullet, "steer_towards"):
                    bullet.steer_towards(tx, ty, desired_speed=4.2, max_turn=0.06, accel=0.18)

            if hasattr(bullet, 'rewind') and bullet.rewind:
                # Rewind bullets move in reverse pattern
                bullet.dy *= -0.98
                bullet.dx *= 0.98

            if hasattr(bullet, 'mini_time_stop') and bullet.mini_time_stop and self.game and self.game.player:
                if bullet.get_rect().colliderect(self.game.player.get_rect()):
                    self.game.player.add_speed_modifier(0.6, 35)

            bullet.update()
            if bullet.is_off_screen():
                self.time_bullets.remove(bullet)
                
    def draw(self, screen):
        # Draw time stop warning
        if self.time_stop_warning > 0:
            # Draw pulsing warning circle around boss
            warning_radius = 120 + (60 - self.time_stop_warning) * 2
            warning_alpha = self.time_stop_warning / 60
            for i in range(3):
                radius = warning_radius - i * 20
                if radius > 0:
                    color = (255, int(255 * warning_alpha), int(100 * warning_alpha))
                    pygame.draw.circle(screen, color, 
                                     (self.x + self.width // 2, self.y + self.height // 2), 
                                     radius, 3)
            
            # Draw warning text
            if self.time_stop_warning > 30:
                font = pygame.font.Font(None, 36)
                text = font.render("TIME STOP!", True, (255, 255, 0))
                text_rect = text.get_rect(center=(WIDTH // 2, 100))
                screen.blit(text, text_rect)
        
        # Draw time fields
        self.particle_system.draw(screen)
            
        # Draw main boss with paradox effect and sprite support
        if self.paradox_mode:
            # Draw multiple ghost images
            for i in range(3):
                offset_x = math.sin(pygame.time.get_ticks() * 0.01 + i * 2) * 10
                offset_y = math.cos(pygame.time.get_ticks() * 0.01 + i * 2) * 10
                alpha = 0.3 + 0.2 * math.sin(pygame.time.get_ticks() * 0.02 + i)
                color = tuple(int(c * alpha) for c in self.color)
                pygame.draw.rect(screen, color, (self.x + offset_x, self.y + offset_y, self.width, self.height))
                
        # Draw the sprite or fallback
        if hasattr(self, 'use_sprite') and self.use_sprite:
            # Draw the Chronomancer sprite
            self.draw_sprite_to_hitbox(screen)
        else:
            # Fallback to default boss drawing
            pygame.draw.rect(screen, self.color, (self.x, self.y, self.width, self.height))
        
        # Draw time bullets
        for bullet in self.time_bullets:
            bullet.draw(screen)
            
        # Draw effects
        for effect in self.effects:
            effect.draw(screen)
            
        # Use the base health bar drawing
        self.draw_health_bar(screen)


