import pygame
import math
import random
from core.boss import Boss
from core.projectile import Projectile
from core.effect import Telegraph
from core.particle_system import ParticleSystem
from core.clone_system import CloneSystem
from config.constants import WIDTH, HEIGHT, RED, BLUE, GREEN, YELLOW, PURPLE, ORANGE, CYAN, WHITE
from utils import load_image

class BladeMaster(Boss):
    def __init__(self):
        super().__init__(WIDTH // 2 - 50, 150, 100, 100, 700, "Blade Master")
        self.color = ORANGE
        self.charge_cooldown = 0
        self.blade_cooldown = 0
        self.charge_speed = 6  # Reduced from 10 to make it slower
        self.is_charging = False
        self.charge_direction = 1
        self.charge_duration = 0
        self.clone_timer = 0
        self.clone_system = CloneSystem()
        self.retreat_timer = 0
        self.returning_blade = None
        self.mirror_blades = []
        self.parry_stance = False
        self.parry_cooldown = 0
        self.parry_counter_ready = False
        self.flurry_attack_cooldown = 0
        self.phase_2_unlocked = False
        self.phase_3_unlocked = False
        self.particle_system = ParticleSystem()
        self.knockback_x = 0
        self.knockback_y = 0
        self.is_knocked_back = False
        self.is_stunned = False
        self.stun_duration = 0
        
        # Load the Blade Master sprite
        try:
            self.sprite = load_image("assets", "sprites", "blade_master.png")
            # Scale sprite to fit the boss dimensions
            self.sprite = pygame.transform.scale(self.sprite, (self.width, self.height))
            self.use_sprite = True
            self.logger.info("Blade Master sprite loaded successfully")
        except Exception as e:
            # Fallback to drawn version if sprite not found
            self.use_sprite = False
            self.logger.warning("Blade Master sprite not found - %s", e)
        
    def run_attacks(self):
        self.charge_cooldown -= 1
        self.blade_cooldown -= 1
        self.clone_timer -= 1
        self.parry_cooldown -= 1
        self.flurry_attack_cooldown -= 1
        self.retreat_timer -= 1
        
        # Handle stun duration
        if self.stun_duration > 0:
            self.stun_duration -= 1
            if self.stun_duration <= 0:
                self.is_stunned = False
            return  # Skip all other actions while stunned
        
        # Handle charge duration
        if self.charge_duration > 0:
            self.charge_duration -= 1
            if self.charge_duration <= 0:
                self.is_charging = False
                self.retreat_timer = 30  # Retreat for 0.5 seconds
        
        if self.phase == 1:
            if self.charge_cooldown <= 0 and not self.is_charging:
                self.charge_attack()
                self.charge_cooldown = 150  # Increased from 90
            elif self.blade_cooldown <= 0:
                self.multi_blade_attack()
                self.blade_cooldown = 120  # Increased from 75
            elif self.clone_timer <= 0:
                self.create_enhanced_clones(2)
                self.clone_timer = 240  # Increased from 180
                
        elif self.phase == 2:
            if not self.phase_2_unlocked:
                self.unlock_phase_2_attacks()
                self.phase_2_unlocked = True
                
            if self.charge_cooldown <= 0 and not self.is_charging:
                self.rapid_charge_attack()
                self.charge_cooldown = 120  # Increased from 70
            elif self.blade_cooldown <= 0:
                self.blade_nova_attack()
                self.blade_cooldown = 100  # Increased from 60
            elif self.clone_timer <= 0:
                self.create_enhanced_clones(3)
                self.clone_timer = 200  # Increased from 140
            elif self.parry_cooldown <= 0:
                self.enter_parry_stance()
                self.parry_cooldown = 300  # Increased from 240
                
        else:  # phase 3
            if not self.phase_3_unlocked:
                self.unlock_phase_3_attacks()
                self.phase_3_unlocked = True
                
            if self.charge_cooldown <= 0 and not self.is_charging:
                self.phantom_charge_attack()
                self.charge_cooldown = 100  # Increased from 50
            elif self.blade_cooldown <= 0:
                self.blade_storm_attack()
                self.blade_cooldown = 90  # Increased from 50
            elif self.clone_timer <= 0:
                self.create_mirror_clones(4)
                self.clone_timer = 180  # Increased from 100
            elif self.flurry_attack_cooldown <= 0:
                self.blade_flurry_attack()
                self.flurry_attack_cooldown = 240  # Increased from 180
                
        self.movement()
        self.update_blades()
        self.update_clones()
        
    def unlock_phase_2_attacks(self):
        self.particle_system.add_burst(
            self.x + self.width // 2, self.y + self.height // 2,
            20, RED, 40, (4, 8)
        )
            
    def unlock_phase_3_attacks(self):
        self.particle_system.add_burst(
            self.x + self.width // 2, self.y + self.height // 2,
            30, (255, 100, 0), 50, (6, 10)
        )
            
    def charge_attack(self):
        self.is_charging = True
        self.charge_speed = 8  # Base charge speed
        self.charge_duration = 60  # Charge for 1 second max
        self.effects.append(Telegraph(self.x + self.width // 2, self.y + self.height // 2, 60, 60, ORANGE))
        if self.game and hasattr(self.game, "audio_manager"):
            self.game.audio_manager.play_custom_sound("blade_dash", volume_scale=0.75)
        
    def multi_blade_attack(self):
        angles = [-30, 0, 30]
        for angle in angles:
            rad = math.radians(angle)
            dx = math.sin(rad) * 8
            dy = -math.cos(rad) * 8
            blade = Projectile(
                self.x + self.width // 2,
                self.y + self.height // 2,
                dx, dy, 8, CYAN, 8  # Reduced damage from 12 to 8
            )
            blade.returning = True
            self.mirror_blades.append(blade)
            
    def blade_nova_attack(self):
        for i in range(12):
            angle = (math.pi * 2 * i) / 12
            dx = math.cos(angle) * 7
            dy = math.sin(angle) * 7
            blade = Projectile(
                self.x + self.width // 2,
                self.y + self.height // 2,
                dx, dy, 10, (255, 200, 0), 10  # Reduced damage from 15 to 10
            )
            self.projectiles.append(blade)
            
    def rapid_charge_attack(self):
        self.is_charging = True
        self.charge_speed = 10  # Reduced from 15 to make it slower
        self.charge_duration = 45  # Charge for 0.75 seconds max
        self.effects.append(Telegraph(self.x + self.width // 2, self.y + self.height // 2, 70, 70, RED))
        if self.game and hasattr(self.game, "audio_manager"):
            self.game.audio_manager.play_custom_sound("blade_dash", volume_scale=0.8)
        
    def phantom_charge_attack(self):
        self.is_charging = True
        self.charge_speed = 14  # Reduced from 20 to make it slower
        self.charge_duration = 30  # Charge for 0.5 seconds max
        self.phantom_mode = True
        self.effects.append(Telegraph(self.x + self.width // 2, self.y + self.height // 2, 90, 90, (255, 0, 100)))
        if self.game and hasattr(self.game, "audio_manager"):
            self.game.audio_manager.play_custom_sound("blade_dash", volume_scale=0.9)
        
    def blade_storm_attack(self):
        for i in range(20):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(5, 10)
            dx = math.cos(angle) * speed
            dy = math.sin(angle) * speed
            blade = Projectile(
                self.x + self.width // 2,
                self.y + self.height // 2,
                dx, dy, 12, (255, 150, 0), 12  # Reduced damage from 18 to 12
            )
            self.projectiles.append(blade)
            
    def blade_flurry_attack(self):
        if self.game and self.game.player:
            target_x = self.game.player.x + self.game.player.width // 2
            target_y = self.game.player.y + self.game.player.height // 2
            
            for i in range(8):
                angle = (math.pi * 2 * i) / 8
                dx = math.cos(angle) * 3
                dy = math.sin(angle) * 3
                blade = Projectile(
                    target_x, target_y,
                    dx, dy, 8, (255, 100, 100), 6
                )
                self.projectiles.append(blade)
                
    def enter_parry_stance(self):
        self.parry_stance = True
        self.parry_duration = 60
        self.parry_counter_ready = True
        self.effects.append(Telegraph(self.x + self.width // 2, self.y + self.height // 2, 60, 60, (255, 255, 0)))
        
    def parry_counter_attack(self):
        if self.game and self.game.player:
            target_x = self.game.player.x + self.game.player.width // 2
            target_y = self.game.player.y + self.game.player.height // 2
            
            for i in range(12):
                angle = (math.pi * 2 * i) / 12
                dx = math.cos(angle) * 8
                dy = math.sin(angle) * 8
                counter_blade = Projectile(
                    target_x, target_y,
                    dx, dy, 8, (255, 200, 0), 10
                )
                counter_blade.counter = True
                self.projectiles.append(counter_blade)
                
            if self.game:
                self.game.screen_shake.start(3, 15)
                
        # Apply stun to self after successful parry
        self.is_stunned = True
        self.stun_duration = 120  # 2 seconds at 60 FPS
        self.is_charging = False  # Stop charging if stunned
        
        self.parry_counter_ready = False
        self.parry_stance = False
        
    def create_enhanced_clones(self, count):
        for i in range(count):
            is_real = (i == count - 1)
            clone_x = self.x + (i - count/2) * 120
            clone_y = self.y + random.randint(-80, 80)
            clone_x = max(50, min(WIDTH - 150, clone_x))
            clone_y = max(50, min(HEIGHT - 180, clone_y))
            self.clone_system.add_clone(clone_x, clone_y, is_real, self.phase, "normal")
            
    def create_mirror_clones(self, count):
        for i in range(count):
            is_real = (i == count - 1)
            if self.game and self.game.player:
                clone_x = self.game.player.x + random.randint(-100, 100)
                clone_y = self.game.player.y + random.randint(-100, 100)
            else:
                clone_x = self.x + random.randint(-150, 150)
                clone_y = self.y + random.randint(-100, 100)
            clone_x = max(50, min(WIDTH - 150, clone_x))
            clone_y = max(50, min(HEIGHT - 180, clone_y))
            self.clone_system.add_clone(clone_x, clone_y, is_real, self.phase, "mirror")
            
    def movement(self):
        # Handle stun state - no movement while stunned
        if self.is_stunned:
            # Add visual stun effect (slight wobble)
            wobble = math.sin(pygame.time.get_ticks() * 0.02) * 2
            self.x += wobble
            self.x = max(50, min(WIDTH - 150, self.x))
            self.update_rect()
            return
            
        # Handle knockback first
        if self.is_knocked_back:
            self.x += self.knockback_x
            self.y += self.knockback_y
            self.knockback_x *= 0.9  # Friction
            self.knockback_y *= 0.9
            
            # Stop knockback when velocity is very small
            if abs(self.knockback_x) < 0.5 and abs(self.knockback_y) < 0.5:
                self.is_knocked_back = False
                self.knockback_x = 0
                self.knockback_y = 0
                
            # Keep within bounds
            self.x = max(50, min(WIDTH - 150, self.x))
            self.y = max(50, min(HEIGHT - 200, self.y))
            self.update_rect()
            return
            
        # Handle retreat behavior
        if self.retreat_timer > 0:
            # Move away from player during retreat
            if self.game and self.game.player:
                dx = self.x - self.game.player.x
                dy = self.y - self.game.player.y
                dist = math.sqrt(dx**2 + dy**2)
                if dist > 0:
                    retreat_speed = 6
                    self.x += (dx / dist) * retreat_speed
                    self.y += (dy / dist) * retreat_speed
            
            self.x = max(50, min(WIDTH - 150, self.x))
            self.y = max(50, min(HEIGHT - 200, self.y))
            self.update_rect()
            return
            
        if not self.is_charging:
            # Normal floating movement when not charging
            self.x += math.sin(pygame.time.get_ticks() * 0.002) * 4
            self.y += math.cos(pygame.time.get_ticks() * 0.003) * 3
            
            self.x = max(50, min(WIDTH - 150, self.x))
            self.y = max(50, min(HEIGHT - 200, self.y))
            self.update_rect()
        else:
            # Charge toward player
            if self.game and self.game.player:
                dx = self.game.player.x - self.x
                dy = self.game.player.y - self.y
                dist = math.sqrt(dx**2 + dy**2)
                if dist > 0:
                    self.x += (dx / dist) * self.charge_speed
                    self.y += (dy / dist) * self.charge_speed
                    self.update_rect()
                    
    def update_blades(self):
        for blade in self.mirror_blades[:]:
            blade.update()
            if hasattr(blade, 'returning') and blade.returning:
                if blade.y < 50 or blade.y > HEIGHT - 50:
                    dx = self.x - blade.x
                    dy = self.y - blade.y
                    dist = math.sqrt(dx**2 + dy**2)
                    if dist > 0:
                        blade.dx = (dx / dist) * 10
                        blade.dy = (dy / dist) * 10
                        
            if blade.is_off_screen():
                self.mirror_blades.remove(blade)
                
        if hasattr(self, 'parry_duration'):
            self.parry_duration -= 1
            if self.parry_duration <= 0:
                self.parry_stance = False
                
    def update_clones(self):
        clone_projectiles = self.clone_system.update(self.x, self.y, self.game)
        self.projectiles.extend(clone_projectiles)
                
    def take_damage(self, damage):
        self.health -= damage
        self.hit_flash = 5
        
        # Apply knockback if player is dashing and Blade Master is charging
        if self.game and self.game.player and self.is_charging and self.game.player.dash_duration > 0:
            # Calculate knockback direction (away from player)
            dx = self.x - self.game.player.x
            dy = self.y - self.game.player.y
            dist = math.sqrt(dx**2 + dy**2)
            if dist > 0:
                # Apply 3x knockback force
                knockback_force = 45  # 3 times the normal 15
                self.knockback_x = (dx / dist) * knockback_force
                self.knockback_y = (dy / dist) * knockback_force
                self.is_knocked_back = True
                self.is_charging = False  # Stop charging when knocked back
        
        # Check for parry counter (only for Blade Master)
        if hasattr(self, 'parry_stance') and self.parry_stance and hasattr(self, 'parry_counter_ready') and self.parry_counter_ready:
            self.parry_counter_attack()
                
    def draw(self, screen):
        # Draw particles
        self.particle_system.update()
        self.particle_system.draw(screen)
                
        # Draw clones
        self.clone_system.draw(screen)
                
        # Draw stun effects
        if self.is_stunned:
            # Draw stun stars around the boss
            center_x = self.x + self.width // 2
            center_y = self.y + self.height // 2
            for i in range(8):
                angle = (math.pi * 2 * i) / 8 + pygame.time.get_ticks() * 0.003
                star_x = center_x + math.cos(angle) * 40
                star_y = center_y + math.sin(angle) * 40
                # Draw spinning stars
                pygame.draw.circle(screen, (255, 255, 0), (int(star_x), int(star_y)), 4)
                pygame.draw.circle(screen, (255, 200, 0), (int(star_x), int(star_y)), 4, 2)
                
        # Draw main boss using sprite or fallback
        # Change color when stunned
        if self.is_stunned:
            original_color = self.color
            self.color = (150, 150, 150)  # Gray color when stunned
            
        # Draw the actual sprite or fallback
        if hasattr(self, 'use_sprite') and self.use_sprite:
            # Draw the Blade Master sprite
            self.draw_sprite_to_hitbox(screen)
            for projectile in self.projectiles:
                projectile.draw(screen)
            for effect in self.effects:
                effect.draw(screen)
        else:
            # Fallback: Draw boss rectangle
            Boss.draw(self, screen)
            
        if self.is_stunned:
            self.color = original_color
        
        # Draw mirror blades
        for blade in self.mirror_blades:
            blade.draw(screen)

        self.health_bar_color = ORANGE
        self.draw_health_bar(screen)


