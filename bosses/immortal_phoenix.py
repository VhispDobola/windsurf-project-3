import pygame
import math
import random
from core.boss import Boss
from core.projectile import Projectile
from core.effect import Telegraph
from core.attack_patterns import AttackPattern
from config.constants import WIDTH, HEIGHT, RED, BLUE, GREEN, YELLOW, PURPLE, ORANGE, CYAN, WHITE, BOSS_GLOBAL_HEALTH_MULTIPLIER
from utils import load_image_with_transparency

class BossStage:
    def __init__(self, name, health, color, intro_text):
        self.name = name
        self.health = health
        self.color = color
        self.intro_text = intro_text
        self.attack_cooldown = 0
        
    def get_intro_dialogue(self):
        return self.intro_text
        
    def run_attacks(self, boss):
        # Default implementation - does nothing
        # Individual bosses should override this in their stage logic
        pass

    def tick_cooldowns(self):
        if self.attack_cooldown > 0:
            self.attack_cooldown -= 1

    def can_attack(self) -> bool:
        return self.attack_cooldown <= 0

class MultiStageBoss(Boss):
    def __init__(self, x, y, width, height, name, stages):
        super().__init__(x, y, width, height, int(stages[0].health * BOSS_GLOBAL_HEALTH_MULTIPLIER), name)
        self.stages = stages
        self.current_stage_index = 0  # Always start at stage 0
        self.current_stage = stages[0]
        self.stage_transition_health = [int(stage.health * BOSS_GLOBAL_HEALTH_MULTIPLIER) for stage in stages[1:]]
        self.transition_effects = []
        self.intro_timer = 180
        self.showing_intro = True
        
    def check_stage_transition(self):
        if self.current_stage_index < len(self.stages) - 1:
            health_percentage = self.health / self.max_health
            # Explicit thresholds for stage transitions
            if self.current_stage_index == 0 and health_percentage <= 0.75:
                self.transition_to_stage(self.current_stage_index + 1)
            elif self.current_stage_index == 1 and health_percentage <= 0.5:
                self.transition_to_stage(self.current_stage_index + 1)
            elif self.current_stage_index == 2 and health_percentage <= 0.25:
                self.transition_to_stage(self.current_stage_index + 1)
                
    def transition_to_stage(self, stage_index):
        # Store old health percentage for smooth transition
        old_health_percentage = self.health / self.max_health if self.max_health > 0 else 1.0
        
        self.current_stage_index = stage_index
        self.current_stage = self.stages[stage_index]
        self.max_health = max(1, int(self.current_stage.health * BOSS_GLOBAL_HEALTH_MULTIPLIER))
        
        # Scale health to maintain difficulty progression
        if stage_index > 0:
            # Start new stage with 80% of max health to prevent instant defeat
            self.health = max(self.max_health * 0.8, self.max_health * old_health_percentage)
        else:
            self.health = self.max_health
            
        self.color = self.current_stage.color
        
        # Create transition effect
        for i in range(30):
            self.transition_effects.append({
                'x': self.x + self.width // 2,
                'y': self.y + self.height // 2,
                'vx': random.uniform(-10, 10),
                'vy': random.uniform(-10, 10),
                'lifetime': 90,
                'color': self.current_stage.color
            })
            
        # Add screen shake for dramatic effect
        if hasattr(self, '_game_ref') and self._game_ref:
            self._game_ref.screen_shake.start(3, 15)
            
        # Reset attack cooldowns to prevent instant attacks
        self.current_stage.attack_cooldown = max(self.current_stage.attack_cooldown, 60)
            
    def run_attacks(self):
        if self.current_stage:
            self.current_stage.tick_cooldowns()
        self.current_stage.run_attacks(self)
        self.check_stage_transition()
        self.update_transition_effects()
        
    def update_transition_effects(self):
        active_effects = []
        for effect in self.transition_effects:
            effect['x'] += effect['vx']
            effect['y'] += effect['vy']
            effect['lifetime'] -= 1
            
            if effect['lifetime'] > 0:
                active_effects.append(effect)
        self.transition_effects = active_effects
                
    def draw_intro(self, screen):
        if self.showing_intro and self.intro_timer > 0:
            font = pygame.font.Font(None, 36)
            text = font.render(self.current_stage.get_intro_dialogue(), True, WHITE)
            text_rect = text.get_rect(center=(WIDTH // 2, HEIGHT // 2))
            
            # Draw background for text
            bg_rect = text_rect.inflate(40, 20)
            pygame.draw.rect(screen, (0, 0, 0), bg_rect)
            pygame.draw.rect(screen, self.current_stage.color, bg_rect, 3)
            
            screen.blit(text, text_rect)
            self.intro_timer -= 1
            
            if self.intro_timer <= 0:
                self.showing_intro = False
                
    def draw(self, screen):
        # Skip MultiStageBoss intro - GameState handles it
        # Draw transition effects
        for effect in self.transition_effects:
            alpha = effect['lifetime'] / 60
            color = tuple(int(c * alpha) for c in effect['color'])
            pygame.draw.circle(screen, color, (int(effect['x']), int(effect['y'])), 5)
            
        # Draw main boss
        pygame.draw.rect(screen, self.color, self.get_rect())
        
        # Draw projectiles
        for projectile in self.projectiles:
            projectile.draw(screen)
            
        # Draw effects
        for effect in self.effects:
            effect.draw(screen)
            
        # Use the base health bar drawing
        self.draw_health_bar(screen)
        
        # Stage name
        if self.should_draw_single_health_bar():
            stage_text = f"Stage {self.current_stage_index + 1}: {self.current_stage.name}"
            font = pygame.font.Font(None, 24)
            text = font.render(stage_text, True, WHITE)
            text_rect = text.get_rect(center=(screen.get_width() // 2, 15))
            screen.blit(text, text_rect)

class ImmortalPhoenix(MultiStageBoss):
    def __init__(self):
        stages = [
            BossStage("Ash Form", 400, (150, 50, 50), 
                     "I am reborn from ashes... stronger than before!"),
            BossStage("Flame Form", 600, (255, 100, 0), 
                     "Feel the burn of eternal fire!"),
            BossStage("Solar Form", 800, (255, 200, 0), 
                     "Witness the power of the sun itself!"),
            BossStage("Phoenix Form", 1000, (255, 150, 255), 
                     "I am the legend... the eternal cycle!"),
        ]
        super().__init__(WIDTH // 2 - 60, 100, 120, 120, "Immortal Phoenix", stages)
        
        self.fire_waves = []
        self.ash_clouds = []
        self.solar_flare = False
        self.resurrection_count = 0
        self.wing_beats = []
        self.feather_barrage_cooldown = 0
        self.dive_cooldown = 0
        self.eternal_flame_tick = 0
        
        # Load the Immortal Phoenix sprite
        try:
            self.sprite = load_image_with_transparency("assets", "sprites", "immortal_phoenix.png", transparent_color=(0, 0, 0))
            # Scale sprite to fit the boss dimensions
            self.sprite = pygame.transform.scale(self.sprite, (self.width, self.height))
            self.use_sprite = True
            self.logger.info("Immortal Phoenix sprite loaded successfully")
        except Exception as e:
            # Fallback to drawn version if sprite not found
            self.use_sprite = False
            self.logger.warning("Immortal Phoenix sprite not found - %s", e)
        
    def create_hazard_zone(self, x, y, radius, damage, duration, hazard_type="zone"):
        """Create a persistent hazard zone using AttackPattern utility"""
        AttackPattern.create_hazard_zone(self, x, y, radius, damage, duration, hazard_type)
        
    def run_attacks(self):
        super().run_attacks()
        self.feather_barrage_cooldown -= 1
        self.dive_cooldown -= 1
        self.eternal_flame_tick -= 1
        
        # Update stage-specific hazards
        self.update_ash_clouds()
        self.update_fire_waves()
        
        # Stage-specific attacks
        if self.current_stage and self.current_stage.can_attack():
            if self.current_stage_index == 0:  # Ash Form
                self.ash_storm_attack()
                self.current_stage.attack_cooldown = 120
            elif self.current_stage_index == 1:  # Flame Form
                if self.feather_barrage_cooldown <= 0:
                    self.feather_barrage_attack()
                    self.feather_barrage_cooldown = 130
                else:
                    self.fire_wave_attack()
                self.current_stage.attack_cooldown = 120
            elif self.current_stage_index == 2:  # Solar Form
                if self.dive_cooldown <= 0:
                    self.phoenix_dive_attack()
                    self.dive_cooldown = 160
                else:
                    self.solar_flare_attack()
                self.current_stage.attack_cooldown = 150
            elif self.current_stage_index == 3:  # Phoenix Form
                self.phoenix_nova_attack()
                self.current_stage.attack_cooldown = 180

        self.apply_eternal_flame()
        self.movement()

    def feather_barrage_attack(self):
        """Golden feather spread with slight random offset."""
        cx = self.x + self.width // 2
        cy = self.y + self.height // 2
        for i in range(14):
            angle = -math.pi / 2 + (i - 6.5) * 0.14 + random.uniform(-0.03, 0.03)
            speed = random.uniform(5.0, 7.5)
            feather = Projectile(cx, cy, math.cos(angle) * speed, math.sin(angle) * speed, 9, (255, 210, 70), 7)
            feather.feather = True
            self.projectiles.append(feather)

    def phoenix_dive_attack(self):
        """Telegraphed dive to player region with impact burst."""
        if not (self.game and self.game.player):
            return
        tx = self.game.player.x + self.game.player.width // 2
        ty = self.game.player.y + self.game.player.height // 2
        self.effects.append(Telegraph(tx, ty, 85, 85, (255, 140, 0), damage=0, warning_type="pulse"))
        # Reposition quickly for dive impact.
        self.x = max(50, min(WIDTH - self.width - 50, tx - self.width // 2))
        self.y = max(50, min(HEIGHT - self.height - 50, ty - self.height // 2))
        self.update_rect()
        for i in range(18):
            angle = (math.pi * 2 * i) / 18
            p = Projectile(tx, ty, math.cos(angle) * 7, math.sin(angle) * 7, 11, (255, 130, 40), 9)
            p.dive_impact = True
            self.projectiles.append(p)

    def apply_eternal_flame(self):
        """Persistent flame aura in final forms."""
        if self.current_stage_index < 2 or not (self.game and self.game.player):
            return
        if self.eternal_flame_tick > 0:
            return
        boss_rect = self.get_rect().inflate(70, 70)
        if boss_rect.colliderect(self.game.player.get_rect()):
            self.game.player.take_damage(5 if self.current_stage_index == 2 else 7)
            self.eternal_flame_tick = 24
            
    def ash_storm_attack(self):
        # Create ash cloud hazards
        for i in range(5):
            ash_x = random.randint(100, WIDTH - 100)
            ash_y = random.randint(50, HEIGHT - 150)
            self.create_hazard_zone(ash_x, ash_y, 40, 5, 180, "ash")
            self.ash_clouds.append({
                'x': ash_x,
                'y': ash_y,
                'radius': 40,
                'lifetime': 180
            })
            
    def fire_wave_attack(self):
        # Create expanding wave hazards
        for i in range(3):
            wave_y = self.y + self.height // 2 + (i - 1) * 60
            # Create a moving hazard zone for each wave
            hazard = {
                'x': self.x + self.width // 2,
                'y': wave_y,
                'width': 200, 'height': 20,
                'lifetime': 120,
                'damage': 15,
                'type': 'wave',
                'direction': 1 if i % 2 == 0 else -1
            }
            if not hasattr(self, 'arena_hazards'):
                self.arena_hazards = []
            self.arena_hazards.append(hazard)
            self.fire_waves.append({
                'x': hazard['x'],
                'y': hazard['y'],
                'width': hazard['width'],
                'height': hazard['height'],
                'lifetime': hazard['lifetime'],
                'direction': hazard['direction'],
                'hazard': hazard,
            })
            
    def solar_flare_attack(self):
        # Massive solar explosion
        self.solar_flare = True
        flare_x = self.x + self.width // 2
        flare_y = self.y + self.height // 2
        
        for i in range(24):
            angle = (math.pi * 2 * i) / 24
            dx = math.cos(angle) * 8
            dy = math.sin(angle) * 8
            projectile = Projectile(flare_x, flare_y, dx, dy, 20, (255, 200, 0), 12)
            projectile.solar = True
            self.projectiles.append(projectile)
            
        self.effects.append(Telegraph(flare_x, flare_y, 150, 150, (255, 255, 0)))
        
    def phoenix_nova_attack(self):
        # Ultimate attack with resurrection mechanics
        nova_x = self.x + self.width // 2
        nova_y = self.y + self.height // 2
        
        # Create expanding shockwave
        for radius in range(50, 200, 30):
            self.effects.append(Telegraph(nova_x, nova_y, radius, radius, (255, 150, 255)))
            
        # Fire projectiles in all directions
        for i in range(36):
            angle = (math.pi * 2 * i) / 36
            dx = math.cos(angle) * 10
            dy = math.sin(angle) * 10
            projectile = Projectile(nova_x, nova_y, dx, dy, 25, (255, 200, 255), 15)
            projectile.phoenix = True
            self.projectiles.append(projectile)
            
    def update_ash_clouds(self):
        active_clouds = []
        for cloud in self.ash_clouds:
            cloud['lifetime'] -= 1
            if cloud['lifetime'] > 0:
                active_clouds.append(cloud)
        self.ash_clouds = active_clouds
                    
    def update_fire_waves(self):
        active_waves = []
        expired_hazards = []
        for wave in self.fire_waves:
            wave['lifetime'] -= 1
            wave['x'] += wave['direction'] * 3
            wave['width'] += wave['direction'] * 2

            # Keep collision hazards aligned with the rendered wave position.
            hazard = wave.get('hazard')
            if hazard:
                hazard['x'] = wave['x']
                hazard['y'] = wave['y']
                hazard['width'] = max(40, int(abs(wave['width'])))
                hazard['height'] = max(12, int(wave['height']))
                hazard['lifetime'] = wave['lifetime']
            
            if wave['lifetime'] <= 0:
                if hazard:
                    expired_hazards.append(hazard)
                continue
            active_waves.append(wave)
        self.fire_waves = active_waves
        if expired_hazards and hasattr(self, 'arena_hazards'):
            expired_ids = {id(h) for h in expired_hazards}
            self.arena_hazards = [h for h in self.arena_hazards if id(h) not in expired_ids]
                    
    def movement(self):
        # Phoenix movement - more aggressive in later stages
        speed = 2 + self.current_stage_index
        self.x += math.sin(pygame.time.get_ticks() * 0.001) * speed
        self.y += math.cos(pygame.time.get_ticks() * 0.0015) * speed * 0.8
        
        self.x = max(50, min(WIDTH - 170, self.x))
        self.y = max(50, min(HEIGHT - 220, self.y))
        self.update_rect()
        
    def draw(self, screen):
        # Draw ash clouds
        for cloud in self.ash_clouds:
            alpha = cloud['lifetime'] / 180
            color = tuple(int(c * alpha) for c in (100, 50, 50))
            pygame.draw.circle(screen, color, (cloud['x'], cloud['y']), cloud['radius'], 2)
            
        # Draw fire waves
        for wave in self.fire_waves:
            alpha = wave['lifetime'] / 120
            color = tuple(int(c * alpha) for c in (255, 100, 0))
            pygame.draw.ellipse(screen, color, 
                              (wave['x'] - wave['width']//2, wave['y'] - wave['height']//2, 
                               wave['width'], wave['height']))
                               
        # Draw main boss with stage-specific effects
        if self.current_stage_index == 3:  # Phoenix Form - glowing effect
            for i in range(3):
                offset_x = math.sin(pygame.time.get_ticks() * 0.02 + i * 2) * 20
                offset_y = math.cos(pygame.time.get_ticks() * 0.02 + i * 2) * 20
                alpha = 0.3 + 0.2 * math.sin(pygame.time.get_ticks() * 0.03 + i)
                color = tuple(int(c * alpha) for c in (255, 150, 255))
                pygame.draw.rect(screen, color, 
                               (self.x + offset_x, self.y + offset_y, self.width, self.height))
                               
        # Draw the sprite or fallback
        if hasattr(self, 'use_sprite') and self.use_sprite:
            # Draw the Immortal Phoenix sprite
            self.draw_sprite_to_hitbox(screen)
        else:
            # Fallback to default boss drawing
            pygame.draw.rect(screen, self.color, self.get_rect())
        
        # Draw wing beats (skip Flame Form to reduce visual clutter)
        if self.current_stage_index >= 2:
            for i in range(2):
                wing_x = self.x + (i - 0.5) * self.width
                wing_y = self.y + self.height // 2
                beat_offset = math.sin(pygame.time.get_ticks() * 0.005 + i * math.pi) * 10
                pygame.draw.ellipse(screen, (255, 150, 0), 
                                  (wing_x - 20, wing_y + beat_offset - 30, 40, 60))

        # Draw eternal flame aura so persistent contact damage is always visible.
        if self.current_stage_index >= 2:
            aura_radius = max(self.width, self.height) // 2 + 35
            center = (int(self.x + self.width // 2), int(self.y + self.height // 2))
            pygame.draw.circle(screen, (255, 120, 40), center, aura_radius, 2)
                                  
        # Draw projectiles
        for projectile in self.projectiles:
            projectile.draw(screen)
            
        # Draw effects
        for effect in self.effects:
            effect.draw(screen)
            
        # Health bar with stage indicator
        self.health_bar_color = self.current_stage.color
        self.draw_health_bar(screen)
        
        # Stage name
        if self.should_draw_single_health_bar():
            stage_text = f"Stage {self.current_stage_index + 1}: {self.current_stage.name}"
            font = pygame.font.Font(None, 24)
            text = font.render(stage_text, True, WHITE)
            text_rect = text.get_rect(center=(screen.get_width() // 2, 10))
            screen.blit(text, text_rect)


