import pygame
import math
import logging
from .entity import Entity, DamageType
from .effect import Effect
from .render_layers import RenderLayer
from config.constants import WIDTH, HEIGHT, RED, GREEN, WHITE

class Boss(Entity):
    def __init__(self, x, y, width, height, health, name, game=None):
        super().__init__(x, y, width, height)
        self.logger = logging.getLogger(__name__)
        self.max_health = max(1, health)  # Ensure health is at least 1
        self.health = self.max_health
        self.name = name
        self.phase = 1  # Always start at phase 1
        self.projectiles = []
        self.effects = []
        self.attack_timer = 0
        self.color = RED
        self.game = game
        self.render_layer = RenderLayer.ENTITIES
        self.hit_flash = 0
        
        # Balance adjustment multipliers
        self._damage_multiplier = 1.0
        self._speed_multiplier = 1.0
        
    def handle_phase_change(self):
        old_phase = self.phase
        if self.health <= self.max_health * 0.3:
            self.phase = 3
        elif self.health <= self.max_health * 0.6:
            self.phase = 2
            
        if old_phase != self.phase:
            self.on_phase_change()
            # Log phase change if performance logger is available
            if self.game and hasattr(self.game, 'performance_logger'):
                self.game.performance_logger.log_phase_change(self.name)
            
    def on_phase_change(self):
        pass
        
    def update(self):
        self.handle_phase_change()
        self.run_attacks()
        self.update_cooldowns()  # Update entity cooldowns
        
        active_projectiles = []
        for projectile in self.projectiles:
            projectile.update()
            if not projectile.is_off_screen():
                active_projectiles.append(projectile)
        self.projectiles = active_projectiles

        active_effects = []
        for effect in self.effects:
            if effect.update():
                active_effects.append(effect)
        self.effects = active_effects
                
        # Update hit flash
        if self.hit_flash > 0:
            self.hit_flash -= 1
                
    def run_attacks(self):
        pass
        
    def get_all_projectiles(self):
        """Get all projectiles from the boss, including custom lists"""
        all_projectiles = list(self.projectiles)
        
        # Add common custom projectile lists
        if hasattr(self, 'mirror_blades'):
            all_projectiles.extend(self.mirror_blades)
        if hasattr(self, 'time_bullets'):
            all_projectiles.extend(self.time_bullets)
        if hasattr(self, 'lasers'):
            all_projectiles.extend(self.lasers)
        if hasattr(self, 'drones'):
            # Drones are not projectiles, but they might have projectiles
            for drone in self.drones:
                if isinstance(drone, dict) and 'projectiles' in drone:
                    all_projectiles.extend(drone['projectiles'])
                elif hasattr(drone, 'projectiles'):
                    all_projectiles.extend(drone.projectiles)
        if hasattr(self, 'fire_breath'):
            all_projectiles.extend(self.fire_breath)
        if hasattr(self, 'ice_shards'):
            all_projectiles.extend(self.ice_shards)
        if hasattr(self, 'crystal_shards'):
            all_projectiles.extend(self.crystal_shards)
        if hasattr(self, 'prism_beams'):
            all_projectiles.extend(self.prism_beams)
        if hasattr(self, 'lightning_bolts'):
            all_projectiles.extend(self.lightning_bolts)
            
        return all_projectiles

    def get_projectile_parent_list(self, projectile):
        """Find the owning list for a projectile (default to main list)."""
        if projectile in self.projectiles:
            return self.projectiles

        custom_lists = [
            'mirror_blades', 'time_bullets', 'lasers', 'drones',
            'fire_breath', 'ice_shards', 'crystal_shards',
            'prism_beams', 'lightning_bolts'
        ]

        for list_name in custom_lists:
            if hasattr(self, list_name):
                lst = getattr(self, list_name)
                if list_name == 'drones':
                    # Drones may contain projectiles inside them
                    for drone in lst:
                        if isinstance(drone, dict) and 'projectiles' in drone and projectile in drone['projectiles']:
                            return drone['projectiles']
                        if hasattr(drone, 'projectiles') and projectile in drone.projectiles:
                            return drone.projectiles
                else:
                    if projectile in lst:
                        return lst

        return self.projectiles
        
    def take_damage(self, damage, damage_type=DamageType.NORMAL):
        """Bosses take damage on each valid hit (no default entity i-frames)."""
        if self.invulnerable:
            return False

        if damage_type in self.damage_resistances:
            damage = int(damage * (1 - self.damage_resistances[damage_type]))

        if damage <= 0:
            return False

        self.health = max(0, self.health - damage)
        self.hit_flash = 5
        return True

    def draw_sprite_to_hitbox(self, screen):
        """Draw sprite scaled to the current hitbox size."""
        if not (hasattr(self, "use_sprite") and self.use_sprite and hasattr(self, "sprite") and self.sprite):
            return False

        # Keep an internal immutable source so repeated resizes stay consistent.
        if not hasattr(self, "_sprite_original"):
            self._sprite_original = self.sprite.copy()

        target_size = (max(1, int(self.width)), max(1, int(self.height)))
        if not hasattr(self, "_sprite_scaled_size") or self._sprite_scaled_size != target_size:
            self._sprite_scaled = pygame.transform.smoothscale(self._sprite_original, target_size)
            self._sprite_scaled_size = target_size

        screen.blit(self._sprite_scaled, (int(self.x), int(self.y)))
        return True
        
    def draw(self, screen):
        color = WHITE if self.hit_flash > 0 else self.color

        rect = self.get_rect()
        if not self.draw_sprite_to_hitbox(screen):
            pygame.draw.rect(screen, (0, 0, 0), rect.inflate(6, 6))
            pygame.draw.rect(screen, color, rect)

            shade = (
                max(0, int(color[0] * 0.75)),
                max(0, int(color[1] * 0.75)),
                max(0, int(color[2] * 0.75)),
            )
            pygame.draw.rect(screen, shade, (rect.x + 4, rect.y + 4, max(0, rect.width - 8), max(0, rect.height - 8)), 2)

        for projectile in self.projectiles:
            projectile.draw(screen)

        for effect in self.effects:
            effect.draw(screen)
            
        self.draw_health_bar(screen)
        
    def draw_health_bar(self, screen):
        """Draw health bar - can be overridden for custom styling"""
        if not self.should_draw_single_health_bar():
            return

        health_bar_width = 300
        health_bar_height = 8
        max_health = max(1, self.max_health)
        health_percentage = max(0.0, min(1.0, self.health / max_health))
        screen_width = screen.get_width() if hasattr(screen, "get_width") else WIDTH
        bar_x = screen_width // 2 - health_bar_width // 2
        bar_y = 30
        
        # Background and border keep the fill readable even for red-themed bosses.
        background_rect = pygame.Rect(bar_x, bar_y, health_bar_width, health_bar_height)
        pygame.draw.rect(screen, (45, 10, 10), background_rect)
        pygame.draw.rect(screen, WHITE, background_rect, 1)
        
        # Health fill - use boss color or green
        health_color = getattr(self, 'health_bar_color', GREEN)
        fill_width = int(health_bar_width * health_percentage)
        if self.health > 0 and fill_width <= 0:
            fill_width = 1
        pygame.draw.rect(screen, health_color, (bar_x, bar_y, fill_width, health_bar_height))
        
        # Phase markers (60% and 30%)
        marker_color = (30, 30, 30)
        for threshold in (0.6, 0.3):
            marker_x = bar_x + int(health_bar_width * threshold)
            pygame.draw.line(screen, marker_color, (marker_x, bar_y - 2), (marker_x, bar_y + health_bar_height + 2), 2)
        
        # Boss name
        font = pygame.font.Font(None, 24)
        text = font.render(self.name, True, WHITE)
        text_rect = text.get_rect(center=(screen_width // 2, bar_y - 15))
        screen.blit(text, text_rect)

    def should_draw_single_health_bar(self):
        """Single boss bars are hidden when the UI is rendering multi-boss bars."""
        if not self.game or not hasattr(self.game, "current_bosses"):
            return True
        return len(self.game.current_bosses) <= 1
        
    def safe_list_iteration(self, lst, update_func):
        """Safely iterate and update a list, removing items during iteration"""
        items_to_remove = []
        for i, item in enumerate(lst):
            if not update_func(item, i):
                items_to_remove.append(i)
        
        # Remove items in reverse order to maintain indices
        for i in reversed(items_to_remove):
            lst.pop(i)
            
    def get_player_distance(self):
        """Get distance to player with safety checks"""
        if not self.game:
            return float('inf')

        if hasattr(self.game, "get_target_player"):
            player = self.game.get_target_player(self)
        else:
            player = getattr(self.game, "player", None)
        if not player:
            return float('inf')

        dx = (self.x + self.width // 2) - (player.x + player.width // 2)
        dy = (self.y + self.height // 2) - (player.y + player.height // 2)
        return math.sqrt(dx * dx + dy * dy)
        
    def apply_balance_adjustments(self, adjustments):
        """Apply balance adjustments to this boss"""
        if 'health_multiplier' in adjustments:
            original_max_health = getattr(self, '_original_max_health', self.max_health)
            if not hasattr(self, '_original_max_health'):
                self._original_max_health = self.max_health
            self.max_health = int(original_max_health * adjustments['health_multiplier'])
            self.health = min(self.health, self.max_health)
            
        if 'damage_multiplier' in adjustments:
            self._damage_multiplier = adjustments['damage_multiplier']
            
        if 'speed_multiplier' in adjustments:
            self._speed_multiplier = adjustments['speed_multiplier']
            
    def get_adjusted_damage(self, base_damage):
        """Get damage adjusted by balance multiplier"""
        return int(base_damage * self._damage_multiplier)
        
    def get_adjusted_speed(self, base_speed):
        """Get speed adjusted by balance multiplier"""
        return base_speed * self._speed_multiplier
