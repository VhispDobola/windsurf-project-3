import pygame
from .entity import Entity
from .projectile import Projectile
from .render_layers import RenderLayer
from config.constants import (
    WIDTH, HEIGHT,
    BLUE, GREEN, RED, YELLOW, WHITE, CYAN,
    PLAYER_BASE_SPEED, PLAYER_BASE_HEALTH, PLAYER_DASH_SPEED, 
    PLAYER_DASH_DURATION, PLAYER_DASH_COOLDOWN, PLAYER_SHOOT_COOLDOWN,
    PLAYER_PROJECTILE_DAMAGE, PLAYER_PROJECTILE_SPEED, DAMAGE_INVINCIBILITY_FRAMES,
    HIT_FLASH_DURATION, PLAYER_HEALTH_BAR_WIDTH, PLAYER_HEALTH_BAR_HEIGHT
)

class Player(Entity):
    def __init__(self, x, y):
        super().__init__(x, y, 30, 30)
        self.color = BLUE
        self.gravity_reversed = False
        self.time_stopped = False
        self.render_layer = RenderLayer.ENTITIES
        self.glow = True
        self.last_move_dir = (0, -1)
        self.dash_dir = (0, -1)
        self.username = ""
        self.hat_style = "None"
        # Status effect system
        self.speed_modifiers = []  # List of (multiplier, duration) tuples
        self.speed_override = None  # Direct speed override with duration
        self.speed_override_duration = 0
        self.reset_to_run_base_stats()

    def reset_to_run_base_stats(self):
        self.speed = PLAYER_BASE_SPEED
        self.base_speed = PLAYER_BASE_SPEED
        self.health = PLAYER_BASE_HEALTH
        self.max_health = PLAYER_BASE_HEALTH
        self.projectiles = []
        self.shoot_cooldown = 0
        self.shoot_cooldown_frames = PLAYER_SHOOT_COOLDOWN
        self.projectile_damage = PLAYER_PROJECTILE_DAMAGE
        self.projectile_speed = PLAYER_PROJECTILE_SPEED
        self.dash_cooldown = 0
        self.dash_cooldown_frames = PLAYER_DASH_COOLDOWN
        self.dash_speed = PLAYER_DASH_SPEED
        self.dash_duration = 0
        self.invincible_time = 0
        self.hit_flash = 0
        self.spread_shot_level = 0
        self.spread_shot_damage_multiplier = 0.67
        self.reflect_shield = False
        self.reflect_charges = 0
        self.reflect_cooldown = 0
        self.regen_level = 0
        self.regen_timer = 0
        self.piercing_shots = False
        self.damage_taken_multiplier = 1.0
        self.shield_max = 0
        self.shield_health = 0
        self.shield_regen_delay_frames = 0
        self.shield_regen_rate = 0
        self.shield_regen_cooldown = 0
        self.speed_modifiers.clear()
        self.speed_override = None
        self.speed_override_duration = 0

    def apply_meta_modifier_bundle(self, modifiers):
        self.base_speed = max(1.5, self.base_speed + float(modifiers.get("base_speed_flat", 0.0)))
        self.max_health = max(20, int(round(self.max_health + modifiers.get("max_health_flat", 0))))
        self.health = self.max_health
        self.dash_speed = max(4.0, self.dash_speed * float(modifiers.get("dash_speed_mult", 1.0)))
        self.dash_cooldown_frames = max(
            20,
            int(round(self.dash_cooldown_frames * float(modifiers.get("dash_cooldown_mult", 1.0)))),
        )
        self.shoot_cooldown_frames = max(
            3,
            int(round(self.shoot_cooldown_frames * float(modifiers.get("shoot_cooldown_mult", 1.0)))),
        )
        self.projectile_damage = max(
            1, int(round(self.projectile_damage + modifiers.get("projectile_damage_flat", 0)))
        )
        self.projectile_speed = max(
            4.0, self.projectile_speed + float(modifiers.get("projectile_speed_flat", 0.0))
        )
        self.damage_taken_multiplier = max(
            0.25, float(modifiers.get("damage_taken_mult", 1.0))
        )
        self.reflect_charges = max(
            0, int(round(self.reflect_charges + modifiers.get("reflect_charges_flat", 0)))
        )
        self.reflect_shield = self.reflect_charges > 0
        self.regen_level = max(0, int(round(self.regen_level + modifiers.get("regen_level_flat", 0))))
        self.spread_shot_level = max(
            0, min(2, int(round(self.spread_shot_level + modifiers.get("spread_shot_level_flat", 0))))
        )
        self.piercing_shots = self.piercing_shots or bool(modifiers.get("piercing_shots", False))
        self.shield_max = max(
            0, int(round(self.shield_max + modifiers.get("shield_max_flat", 0)))
        )
        self.shield_health = self.shield_max
        self.shield_regen_delay_frames = max(
            self.shield_regen_delay_frames,
            int(round(modifiers.get("shield_regen_delay_frames", 0))),
        )
        self.shield_regen_rate = max(
            self.shield_regen_rate,
            int(round(modifiers.get("shield_regen_rate_flat", 0))),
        )
        self.shield_regen_cooldown = 0
        self.health = min(
            self.max_health,
            self.health + max(0, int(round(modifiers.get("starting_heal_flat", 0)))),
        )
        self.calculate_speed()
        
    def _is_binding_pressed(self, keys, binding):
        if isinstance(keys, dict):
            if isinstance(binding, (list, tuple, set)):
                return any(bool(keys.get(key, False)) for key in binding)
            return bool(keys.get(binding, False))
        if isinstance(binding, (list, tuple, set)):
            return any(keys[key] for key in binding)
        return keys[binding]

    def move(self, keys, controls=None):
        dx = dy = 0
        controls = controls or {}
        
        # Check if time is stopped
        if hasattr(self, 'time_stopped') and self.time_stopped:
            return  # Can't move during time stop
            
        # Handle dash movement
        if self.dash_duration > 0:
            # Keep dash direction stable for the whole dash window.
            dx = self.dash_dir[0] * self.dash_speed
            dy = self.dash_dir[1] * self.dash_speed
        else:
            # Normal movement
            left_bind = controls.get("left", (pygame.K_LEFT, pygame.K_a))
            right_bind = controls.get("right", (pygame.K_RIGHT, pygame.K_d))
            up_bind = controls.get("up", (pygame.K_UP, pygame.K_w))
            down_bind = controls.get("down", (pygame.K_DOWN, pygame.K_s))

            if self._is_binding_pressed(keys, left_bind):
                dx = -self.speed
            if self._is_binding_pressed(keys, right_bind):
                dx = self.speed
            if self._is_binding_pressed(keys, up_bind):
                dy = -self.speed
            if self._is_binding_pressed(keys, down_bind):
                dy = self.speed

            # Normalize diagonal movement to prevent speed boost
            if dx != 0 and dy != 0:
                dx *= 0.707
                dy *= 0.707
            if dx != 0 or dy != 0:
                length = (dx * dx + dy * dy) ** 0.5
                if length > 0:
                    self.last_move_dir = (dx / length, dy / length)
            
        # Apply movement
        self.x += dx
        self.y += dy
        
        # Apply wind force if present
        if hasattr(self, 'wind_force_x') and hasattr(self, 'wind_force_y'):
            self.x += self.wind_force_x
            self.y += self.wind_force_y
            
            # Decay wind force over time
            self.wind_force_x *= 0.9
            self.wind_force_y *= 0.9
            
            # Remove wind force when it becomes negligible
            if abs(self.wind_force_x) < 0.1 and abs(self.wind_force_y) < 0.1:
                self.wind_force_x = 0
                self.wind_force_y = 0
        
        # Keep player on screen - use dynamic dimensions
        if hasattr(self, '_game_ref') and self._game_ref and hasattr(self._game_ref, 'screen'):
            screen_width = self._game_ref.screen.get_width()
            screen_height = self._game_ref.screen.get_height()
        else:
            screen_width = WIDTH
            screen_height = HEIGHT
            
        self.x = max(0, min(screen_width - self.width, self.x))
        self.y = max(0, min(screen_height - self.height, self.y))
        
        self.update_rect()
        
    def dash(self):
        if self.dash_cooldown <= 0 and self.dash_duration <= 0:
            if self.last_move_dir[0] == 0 and self.last_move_dir[1] == 0:
                self.dash_dir = (0, -1)
            else:
                self.dash_dir = self.last_move_dir
            self.dash_duration = PLAYER_DASH_DURATION
            self.dash_cooldown = self.dash_cooldown_frames
            self.invincible_time = DAMAGE_INVINCIBILITY_FRAMES  # Increased for full dash coverage
            
    def shoot(self, target_x=None, target_y=None):
        if self.shoot_cooldown <= 0:
            origin_x = self.x + self.width // 2
            origin_y = self.y + self.height // 2

            if target_x is None or target_y is None:
                dx, dy = 0, -self.projectile_speed
            else:
                vx = target_x - origin_x
                vy = target_y - origin_y
                dist = (vx * vx + vy * vy) ** 0.5
                if dist <= 0.001:
                    dx, dy = 0, -self.projectile_speed
                else:
                    dx = (vx / dist) * self.projectile_speed
                    dy = (vy / dist) * self.projectile_speed

            shot_vectors = [(dx, dy)]
            damage_multiplier = 1.0
            if self.spread_shot_level > 0:
                damage_multiplier = self.spread_shot_damage_multiplier
                base_angle = pygame.math.Vector2(dx, dy).as_polar()[1] if (dx != 0 or dy != 0) else -90
                spread_pattern = {
                    1: (-12, 12),
                    2: (-18, -6, 6, 18),
                }.get(self.spread_shot_level, (-22, -10, 10, 22))
                for offset in spread_pattern:
                    vector = pygame.math.Vector2()
                    vector.from_polar((self.projectile_speed, base_angle + offset))
                    shot_vectors.append((vector.x, vector.y))

            for shot_dx, shot_dy in shot_vectors:
                shot_damage = max(1, int(round(self.projectile_damage * damage_multiplier)))
                projectile = Projectile(
                    origin_x,
                    origin_y,
                    shot_dx, shot_dy, shot_damage, YELLOW
                )
                if self.piercing_shots:
                    projectile.set_piercing(2)
                self.projectiles.append(projectile)
            self.shoot_cooldown = self.shoot_cooldown_frames
            
    def add_speed_modifier(self, multiplier, duration):
        """Add a speed modifier (multiplier, duration in frames)"""
        self.speed_modifiers.append((multiplier, duration))
        
    def set_speed_override(self, speed, duration):
        """Set a direct speed override"""
        self.speed_override = speed
        self.speed_override_duration = duration
        
    def clear_speed_effects(self):
        """Clear all speed effects"""
        self.speed_modifiers.clear()
        self.speed_override = None
        self.speed_override_duration = 0
        self.calculate_speed()
        
    def calculate_speed(self):
        """Calculate current speed based on modifiers and overrides"""
        if self.speed_override is not None:
            self.speed = self.speed_override
        else:
            speed = self.base_speed
            for multiplier, _ in self.speed_modifiers:
                speed *= multiplier
            self.speed = max(0.5, speed)  # Minimum speed threshold
            
    def update(self):
        """Update player status effects and cooldowns"""
        # Update speed modifiers
        modifiers_to_remove = []
        for i, (multiplier, duration) in enumerate(self.speed_modifiers):
            if duration <= 1:
                modifiers_to_remove.append(i)
            else:
                self.speed_modifiers[i] = (multiplier, duration - 1)
        
        # Remove expired modifiers in reverse order
        for i in reversed(modifiers_to_remove):
            self.speed_modifiers.pop(i)
        
        # Update speed override
        if self.speed_override_duration > 0:
            self.speed_override_duration -= 1
            if self.speed_override_duration <= 0:
                self.speed_override = None
        
        # Calculate current speed
        self.calculate_speed()
        
        # Update other cooldowns
        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1
        if self.dash_cooldown > 0:
            self.dash_cooldown -= 1
        if self.dash_duration > 0:
            self.dash_duration -= 1
        if self.invincible_time > 0:
            self.invincible_time -= 1
        if self.hit_flash > 0:
            self.hit_flash -= 1
        if self.reflect_cooldown > 0:
            self.reflect_cooldown -= 1
        if self.shield_max > 0:
            if self.shield_regen_cooldown > 0:
                self.shield_regen_cooldown -= 1
            elif self.shield_health < self.shield_max and self.shield_regen_rate > 0:
                self.shield_health = min(
                    self.shield_max, self.shield_health + self.shield_regen_rate
                )
        if self.regen_level > 0 and self.health > 0 and self.health < self.max_health:
            self.regen_timer += 1
            regen_interval = max(45, 160 - self.regen_level * 35)
            if self.regen_timer >= regen_interval:
                self.health = min(self.max_health, self.health + self.regen_level)
                self.regen_timer = 0
        elif self.regen_level <= 0 or self.health >= self.max_health:
            self.regen_timer = 0
            
        # Update projectiles
        active_projectiles = []
        for projectile in self.projectiles:
            projectile.update()
            if not projectile.is_off_screen():
                active_projectiles.append(projectile)
        self.projectiles = active_projectiles
                
    def take_damage(self, damage):
        if self.invincible_time <= 0:
            scaled_damage = max(1, int(round(damage * self.damage_taken_multiplier)))
            if self.shield_health > 0:
                absorbed = min(self.shield_health, scaled_damage)
                self.shield_health -= absorbed
                scaled_damage -= absorbed
                self.shield_regen_cooldown = self.shield_regen_delay_frames
            if scaled_damage > 0:
                self.health -= scaled_damage
            self.invincible_time = DAMAGE_INVINCIBILITY_FRAMES
            self.hit_flash = HIT_FLASH_DURATION
            return True
        return False
        
    def draw(self, screen):
        # Draw projectiles first (they should always be visible)
        for projectile in self.projectiles:
            projectile.draw(screen)
            
        # Draw player with invincibility flashing
        color = WHITE if self.hit_flash > 0 and self.hit_flash % 4 < 2 else self.color
        
        if self.invincible_time > 0 and self.invincible_time % 4 < 2:
            # Player is invisible during invincibility frames, but projectiles still show
            pass
        else:
            rect = self.get_rect()

            if self.glow:
                glow_w = rect.width + 22
                glow_h = rect.height + 22
                glow = pygame.Surface((glow_w, glow_h), pygame.SRCALPHA)
                pygame.draw.rect(glow, (self.color[0], self.color[1], self.color[2], 55), (0, 0, glow_w, glow_h), border_radius=10)
                screen.blit(glow, (rect.centerx - glow_w // 2, rect.centery - glow_h // 2))

            pygame.draw.rect(screen, (0, 0, 0), rect.inflate(6, 6), border_radius=8)
            pygame.draw.rect(screen, color, rect, border_radius=6)
            self._draw_hat(screen, rect)

        self._draw_username(screen)
            
        # Draw health bar
        health_bar_width = PLAYER_HEALTH_BAR_WIDTH
        health_bar_height = PLAYER_HEALTH_BAR_HEIGHT
        health_percentage = max(0, self.health / self.max_health)
        pygame.draw.rect(screen, RED, (self.x, self.y - 10, health_bar_width, health_bar_height))
        pygame.draw.rect(screen, GREEN, (self.x, self.y - 10, health_bar_width * health_percentage, health_bar_height))
        if self.shield_max > 0:
            shield_percentage = max(0, self.shield_health / self.shield_max)
            pygame.draw.rect(screen, (28, 44, 90), (self.x, self.y - 16, health_bar_width, health_bar_height))
            pygame.draw.rect(screen, CYAN, (self.x, self.y - 16, health_bar_width * shield_percentage, health_bar_height))

        if self.reflect_shield:
            shield_color = CYAN if self.reflect_cooldown <= 0 else (120, 180, 220)
            pygame.draw.circle(screen, shield_color, (int(self.x + self.width // 2), int(self.y + self.height // 2)), 24, 2)
        if self.shield_max > 0:
            shield_ring_color = (120, 220, 255) if self.shield_regen_cooldown <= 0 else (90, 120, 170)
            pygame.draw.circle(screen, shield_ring_color, (int(self.x + self.width // 2), int(self.y + self.height // 2)), 18, 2)

    def _draw_username(self, screen):
        username = (self.username or "").strip()
        if not username:
            return
        label_font = pygame.font.Font(None, 18)
        text = label_font.render(username, True, WHITE)
        text_rect = text.get_rect(center=(int(self.x + self.width // 2), int(self.y - 22)))
        screen.blit(text, text_rect)

    def _draw_hat(self, screen, rect):
        hat = (self.hat_style or "None").lower()
        if hat == "none":
            return
        if hat == "cap":
            pygame.draw.ellipse(screen, (30, 30, 30), (rect.x + 4, rect.y - 10, rect.width - 8, 7))
            pygame.draw.rect(screen, (220, 70, 70), (rect.x + 6, rect.y - 15, rect.width - 12, 7), border_radius=3)
        elif hat == "crown":
            points = [
                (rect.x + 5, rect.y - 2),
                (rect.x + 8, rect.y - 12),
                (rect.x + rect.width // 2, rect.y - 5),
                (rect.x + rect.width - 8, rect.y - 12),
                (rect.x + rect.width - 5, rect.y - 2),
            ]
            pygame.draw.polygon(screen, (240, 200, 70), points)
            pygame.draw.rect(screen, (200, 160, 50), (rect.x + 5, rect.y - 4, rect.width - 10, 3))
        elif hat == "beanie":
            pygame.draw.ellipse(screen, (80, 180, 255), (rect.x + 3, rect.y - 12, rect.width - 6, 10))
            pygame.draw.circle(screen, (240, 240, 240), (rect.centerx, rect.y - 12), 3)
