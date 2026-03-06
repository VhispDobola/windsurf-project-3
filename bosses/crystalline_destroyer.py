import pygame
import math
import random
from .immortal_phoenix import MultiStageBoss, BossStage
from core.projectile import Projectile
from core.effect import Telegraph
from config.constants import WIDTH, HEIGHT, RED, BLUE, GREEN, YELLOW, PURPLE, ORANGE, CYAN, WHITE, BOSS_GLOBAL_HEALTH_MULTIPLIER
from utils import load_image_with_transparency

class CrystallineDestroyer(MultiStageBoss):
    def __init__(self):
        stages = [
            BossStage("Rock Form", 320, (100, 100, 100), 
                     "The earth trembles... ancient power awakens!"),
            BossStage("Crystal Form", 430, (150, 150, 255), 
                     "Crystals resonate... pure energy flows!"),
            BossStage("Prism Form", 560, (255, 100, 255), 
                     "Light refracts... rainbow destruction awaits!"),
            BossStage("Diamond Form", 700, (200, 200, 255), 
                     "Ultimate form... unbreakable will shatter you!"),
        ]
        super().__init__(WIDTH // 2 - 80, 100, 160, 160, "Crystalline Destroyer", stages)
        
        self.crystal_shards = []
        self.resonance_waves = []
        self.prism_beams = []
        self.earthquake_active = False
        self.crystal_armor = []
        self.damage_cooldowns = {}  # Track damage cooldowns for each projectile
        self.pattern_toggle = 0

        try:
            self.sprite = load_image_with_transparency("assets", "sprites", "crystalline_destroyer.png", transparent_color=(0, 0, 0))
            self.sprite = pygame.transform.scale(self.sprite, (self.width, self.height))
            self.use_sprite = True
        except Exception:
            self.use_sprite = False
        
    def transition_to_stage(self, stage_index):
        self.current_stage_index = stage_index
        self.current_stage = self.stages[stage_index]
        self.max_health = max(1, int(self.current_stage.health * BOSS_GLOBAL_HEALTH_MULTIPLIER))
        self.health = self.max_health
        self.color = self.current_stage.color
        
        # Enhanced visual effects for stage transitions
        if stage_index == 1:  # Crystal Form
            # Add crystal spikes
            self.crystal_spikes = []
            for i in range(8):
                angle = (math.pi * 2 * i) / 8
                self.crystal_spikes.append({
                    'angle': angle,
                    'length': 20 + stage_index * 10,
                    'width': 3 + stage_index
                })
        elif stage_index == 2:  # Prism Form
            # Add rainbow aura
            self.prism_aura = True
            self.aura_rotation = 0
        elif stage_index == 3:  # Diamond Form
            # Add diamond crown and increased size
            self.width = 180
            self.height = 180
            self.update_rect()
            self.diamond_crown = True
        
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
        if self.game:
            self.game.screen_shake.start(4, 20)
        
    def run_attacks(self):
        super().run_attacks()
        
        # Update damage cooldowns
        for proj_id in list(self.damage_cooldowns.keys()):
            if self.damage_cooldowns[proj_id] > 0:
                self.damage_cooldowns[proj_id] -= 1
            else:
                del self.damage_cooldowns[proj_id]
        
        # Update stage-specific hazards
        self.update_crystal_armor()
        self.update_crystal_shards()
        self.update_prism_beams()
        self.update_resonance_waves()

        if self.current_stage and self.current_stage.can_attack():
            if self.current_stage_index == 0:  # Rock Form
                if self.pattern_toggle % 2 == 0:
                    self.earthquake_attack()
                else:
                    self.tectonic_slam_attack()
                self.pattern_toggle += 1
                self.current_stage.attack_cooldown = 110
            elif self.current_stage_index == 1:  # Crystal Form
                if self.pattern_toggle % 2 == 0:
                    self.crystal_shard_attack()
                else:
                    self.crystal_crossfire_attack()
                self.pattern_toggle += 1
                self.current_stage.attack_cooldown = 100
            elif self.current_stage_index == 2:  # Prism Form
                self.prism_rainbow_attack()
                self.current_stage.attack_cooldown = 180
            elif self.current_stage_index == 3:  # Diamond Form
                self.diamond_storm_attack()
                self.current_stage.attack_cooldown = 180
            
        self.movement()
            
    def earthquake_attack(self):
        self.earthquake_active = True
        # Denser but lower-damage falling rocks to keep phase 1 active, not spiky.
        for i in range(10):
            rock_x = random.randint(70, WIDTH - 70)
            rock_y = random.randint(20, 140)
            self.crystal_armor.append({
                'x': rock_x, 'y': rock_y,
                'vx': random.uniform(-3, 3),
                'vy': random.uniform(2.5, 5.5),
                'lifetime': 135
            })

    def tectonic_slam_attack(self):
        """Create lane pressure with clear telegraphs so movement is required."""
        lane_count = 4
        for i in range(lane_count):
            lane_x = int((i + 0.5) * (WIDTH / lane_count))
            self.effects.append(Telegraph(lane_x, HEIGHT // 2, 45, 36, (180, 180, 180), damage=0, warning_type="cross"))
            for j in range(5):
                y = 60 + j * 110
                shard = Projectile(lane_x, y, 0, random.uniform(3.5, 5.5), 8, (140, 140, 140), 7)
                shard.rockfall = True
                self.crystal_shards.append(shard)
            
    def crystal_shard_attack(self):
        # Faster rotating ring with light homing correction.
        for i in range(10):
            angle = (math.pi * 2 * i) / 10 + pygame.time.get_ticks() * 0.0015
            dx = math.cos(angle) * 6.5
            dy = math.sin(angle) * 6.5
            shard = Projectile(
                self.x + self.width // 2, self.y + self.height // 2,
                dx, dy, 11, (150, 150, 255), 7
            )
            shard.homing = True
            shard.shard_id = f"shard_{i}_{pygame.time.get_ticks()}"  # Unique ID
            self.crystal_shards.append(shard)

    def crystal_crossfire_attack(self):
        """Two-side fan that forces side-step movement."""
        if not (self.game and self.game.player):
            return
        px = self.game.player.x + self.game.player.width // 2
        py = self.game.player.y + self.game.player.height // 2
        for sx in (80, WIDTH - 80):
            base = math.atan2(py - (self.y + self.height // 2), px - sx)
            for i in range(4):
                spread = (i - 1.5) * 0.16
                dx = math.cos(base + spread) * 6.8
                dy = math.sin(base + spread) * 6.8
                shard = Projectile(sx, self.y + self.height // 2, dx, dy, 10, (170, 170, 255), 7)
                shard.crystalline = True
                self.crystal_shards.append(shard)
            
    def prism_rainbow_attack(self):
        # Create rainbow beam fan with rotating/sweeping line pressure.
        beam_x = self.x + self.width // 2
        beam_y = self.y + self.height // 2
        
        colors = [RED, ORANGE, YELLOW, GREEN, BLUE, PURPLE]
        for i, color in enumerate(colors):
            angle = (math.pi * 2 * i) / len(colors) + random.uniform(-0.08, 0.08)

            beam = Projectile(beam_x, beam_y, 0, 0, 6, color, 20)
            beam.beam = True
            beam.angle = angle
            beam.length = 320
            beam.rotation_speed = 0.015 if i % 2 == 0 else -0.015
            beam.end_x = beam_x + math.cos(beam.angle) * beam.length
            beam.end_y = beam_y + math.sin(beam.angle) * beam.length
            beam.lifetime = 220
            beam.beam_id = f"beam_{i}_{pygame.time.get_ticks()}"
            self.prism_beams.append(beam)
            self.effects.append(Telegraph(int(beam.end_x), int(beam.end_y), 40, 40, color, damage=0, warning_type="cross"))
            
    def diamond_storm_attack(self):
        # Ultimate attack with multiple effects
        # Create resonance waves
        for i in range(4):
            self.resonance_waves.append({
                'x': self.x + self.width // 2,
                'y': self.y + self.height // 2,
                'radius': 50 + i * 20,
                'lifetime': 180,
                'color': (200, 200, 255)
            })
            
        # Diamond shard explosion
        for i in range(20):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(8, 12)
            dx = math.cos(angle) * speed
            dy = math.sin(angle) * speed
            shard = Projectile(
                self.x + self.width // 2, self.y + self.height // 2,
                dx, dy, 20, (200, 200, 255), 10
            )
            shard.diamond = True
            self.crystal_shards.append(shard)
            
    def update_crystal_armor(self):
        def update_armor(armor, index):
            armor['x'] += armor['vx']
            armor['y'] += armor['vy']
            armor['vy'] += 0.3  # Gravity
            armor['lifetime'] -= 1
            
            if armor['lifetime'] <= 0:
                return False
            elif self.game and self.game.player:
                armor_rect = pygame.Rect(armor['x'], armor['y'], 20, 20)
                if armor_rect.colliderect(self.game.player.get_rect()):
                    armor_id = f"armor_{id(armor)}"
                    
                    # Only damage if not on cooldown
                    if armor_id not in self.damage_cooldowns:
                        damage = 5  # Reduced from 10 to 5
                        self.game.player.take_damage(damage)
                        self.damage_cooldowns[armor_id] = 60  # 1 second cooldown
                        
                        # Log ability damage
                        if hasattr(self.game, 'performance_logger'):
                            stage_name = ["Rock Form", "Crystal Form", "Prism Form", "Diamond Form"][self.current_stage_index]
                            self.game.performance_logger.log_ability_damage(self.name, f"{stage_name} - Crystal Armor", damage)
            return True
            
        self.safe_list_iteration(self.crystal_armor, update_armor)
                    
    def update_crystal_shards(self):
        for shard in self.crystal_shards[:]:
            if hasattr(shard, 'homing') and shard.homing:
                if self.game and self.game.player:
                    tx = self.game.player.x + self.game.player.width // 2
                    ty = self.game.player.y + self.game.player.height // 2
                    if hasattr(shard, "steer_towards"):
                        shard.steer_towards(tx, ty, desired_speed=5.5, max_turn=0.045, accel=0.18)
                        
            shard.update()
            if shard.is_off_screen():
                self.crystal_shards.remove(shard)
                
    def update_prism_beams(self):
        for beam in self.prism_beams[:]:
            beam.update()
            if hasattr(beam, 'beam') and beam.beam:
                # Rotate/sweep beam lines for persistent pressure.
                beam.angle += getattr(beam, 'rotation_speed', 0.0)
                beam.end_x = beam.x + math.cos(beam.angle) * getattr(beam, 'length', 300)
                beam.end_y = beam.y + math.sin(beam.angle) * getattr(beam, 'length', 300)

                # Beam line damage along segment with cooldown.
                if self.game and self.game.player:
                    px = self.game.player.x + self.game.player.width // 2
                    py = self.game.player.y + self.game.player.height // 2
                    dist = self._distance_point_to_segment(px, py, beam.x, beam.y, beam.end_x, beam.end_y)
                    if dist <= 16:
                        beam_id = getattr(beam, 'beam_id', f"beam_{id(beam)}")
                        if beam_id not in self.damage_cooldowns:
                            damage = 5
                            self.game.player.take_damage(damage)
                            self.damage_cooldowns[beam_id] = 20
                            if hasattr(self.game, 'performance_logger'):
                                stage_name = ["Rock Form", "Crystal Form", "Prism Form", "Diamond Form"][self.current_stage_index]
                                self.game.performance_logger.log_ability_damage(self.name, f"{stage_name} - Prism Beam", damage)
                    
            if beam.is_off_screen():
                self.prism_beams.remove(beam)

    def _distance_point_to_segment(self, px, py, x1, y1, x2, y2):
        """Return shortest distance from point to line segment."""
        vx = x2 - x1
        vy = y2 - y1
        wx = px - x1
        wy = py - y1
        c1 = vx * wx + vy * wy
        if c1 <= 0:
            return math.sqrt((px - x1) ** 2 + (py - y1) ** 2)
        c2 = vx * vx + vy * vy
        if c2 <= c1:
            return math.sqrt((px - x2) ** 2 + (py - y2) ** 2)
        b = c1 / c2
        bx = x1 + b * vx
        by = y1 + b * vy
        return math.sqrt((px - bx) ** 2 + (py - by) ** 2)
                
    def update_resonance_waves(self):
        for wave in self.resonance_waves[:]:
            wave['lifetime'] -= 1
            wave['radius'] += 2
            
            if wave['lifetime'] <= 0:
                self.resonance_waves.remove(wave)
            elif self.game and self.game.player:
                # Damage player in wave with cooldown
                dist = math.sqrt((self.game.player.x - wave['x'])**2 + 
                               (self.game.player.y - wave['y'])**2)
                if dist < wave['radius']:
                    wave_id = f"wave_{id(wave)}"
                    
                    # Only damage if not on cooldown
                    if wave_id not in self.damage_cooldowns:
                        damage = 3  # Reduced from 8 to 3
                        self.game.player.take_damage(damage)
                        self.damage_cooldowns[wave_id] = 30  # 0.5 second cooldown
                        
                        # Log ability damage
                        if hasattr(self.game, 'performance_logger'):
                            stage_name = ["Rock Form", "Crystal Form", "Prism Form", "Diamond Form"][self.current_stage_index]
                            self.game.performance_logger.log_ability_damage(self.name, f"{stage_name} - Resonance Waves", damage)
                    
    def movement(self):
        # Golem movement - slow but powerful
        if self.current_stage_index == 0:  # Rock Form - very slow
            self.x += math.sin(pygame.time.get_ticks() * 0.0005) * 1
        else:  # Crystal forms - faster
            speed = 2 + self.current_stage_index
            self.x += math.sin(pygame.time.get_ticks() * 0.001) * speed
            
        self.y += math.cos(pygame.time.get_ticks() * 0.001) * 0.5
        self.x = max(50, min(WIDTH - 210, self.x))
        self.y = max(50, min(HEIGHT - 260, self.y))
        self.update_rect()
        
    def draw(self, screen):
        # Draw resonance waves
        for wave in self.resonance_waves:
            alpha = wave['lifetime'] / 180
            color = tuple(int(c * alpha) for c in wave['color'])
            # Fill the damaging area so players can read collision volume clearly.
            fill_color = tuple(int(c * 0.18 * alpha) for c in wave['color'])
            pygame.draw.circle(screen, fill_color, (int(wave['x']), int(wave['y'])), int(wave['radius']))
            pygame.draw.circle(screen, color, (wave['x'], wave['y']), wave['radius'], 3)
            
        # Draw crystal armor
        for armor in self.crystal_armor:
            alpha = armor['lifetime'] / 120
            color = tuple(int(c * alpha) for c in (100, 100, 100))
            pygame.draw.rect(screen, color, (armor['x'], armor['y'], 20, 20))
            
        # Draw prism beams
        for beam in self.prism_beams:
            beam.draw(screen)
            if hasattr(beam, 'beam') and beam.beam:
                if hasattr(beam, 'end_x'):
                    glow = tuple(min(255, c + 60) for c in beam.color)
                    pygame.draw.line(screen, glow, (int(beam.x), int(beam.y)), (int(beam.end_x), int(beam.end_y)), 8)
                    pygame.draw.line(screen, beam.color,
                                   (int(beam.x), int(beam.y)),
                                   (int(beam.end_x), int(beam.end_y)), 4)
                                   
        # Draw main golem with stage-specific effects
        center_x = self.x + self.width // 2
        center_y = self.y + self.height // 2
        
        # Draw crystal spikes (Crystal Form and above)
        if hasattr(self, 'crystal_spikes') and self.crystal_spikes:
            for spike in self.crystal_spikes:
                angle = spike['angle']
                length = spike['length']
                width = spike['width']
                end_x = center_x + math.cos(angle) * length
                end_y = center_y + math.sin(angle) * length
                pygame.draw.line(screen, self.current_stage.color, 
                               (center_x, center_y), (end_x, end_y), width)
        
        # Draw prism aura (Prism Form)
        if hasattr(self, 'prism_aura') and self.prism_aura:
            self.aura_rotation = (self.aura_rotation + 2) % 360
            colors = [RED, ORANGE, YELLOW, GREEN, BLUE, PURPLE]
            for i, color in enumerate(colors):
                angle = math.radians(self.aura_rotation + i * 60)
                aura_x = center_x + math.cos(angle) * 60
                aura_y = center_y + math.sin(angle) * 60
                pygame.draw.circle(screen, color, (int(aura_x), int(aura_y)), 8, 2)
        
        # Draw diamond crown (Diamond Form)
        if hasattr(self, 'diamond_crown') and self.diamond_crown:
            crown_points = []
            for i in range(5):
                angle = (math.pi * 2 * i) / 5 - math.pi / 2
                crown_x = center_x + math.cos(angle) * 40
                crown_y = self.y - 10 + math.sin(angle) * 15
                crown_points.append((crown_x, crown_y))
            pygame.draw.polygon(screen, (255, 255, 255), crown_points, 3)
        
        # Draw crystal glow effect (Crystal Form and above)
        if self.current_stage_index >= 1:
            for i in range(6):
                angle = (math.pi * 2 * i) / 6 + pygame.time.get_ticks() * 0.002
                glow_x = center_x + math.cos(angle) * 40
                glow_y = center_y + math.sin(angle) * 40
                alpha = 0.3 + 0.2 * math.sin(pygame.time.get_ticks() * 0.003 + i)
                color = tuple(int(c * alpha) for c in self.current_stage.color)
                pygame.draw.circle(screen, color, (int(glow_x), int(glow_y)), 15, 2)
                               
        if hasattr(self, "use_sprite") and self.use_sprite:
            self.draw_sprite_to_hitbox(screen)
        else:
            pygame.draw.rect(screen, self.color, self.get_rect())
        
        # Draw projectiles
        for shard in self.crystal_shards:
            shard.draw(screen)
            
        # Draw effects
        for effect in self.effects:
            effect.draw(screen)
            
        # Use the base health bar drawing with custom color
        self.health_bar_color = self.current_stage.color
        self.draw_health_bar(screen)
        
        # Stage name
        if self.should_draw_single_health_bar():
            stage_text = f"Stage {self.current_stage_index + 1}: {self.current_stage.name}"
            font = pygame.font.Font(None, 24)
            text = font.render(stage_text, True, WHITE)
            text_rect = text.get_rect(center=(screen.get_width() // 2, 15))
            screen.blit(text, text_rect)


