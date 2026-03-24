import pygame
import math
import random
from .immortal_phoenix import MultiStageBoss, BossStage
from core.projectile import Projectile
from core.effect import Telegraph
from config.constants import WIDTH, HEIGHT, RED, BLUE, YELLOW, PURPLE, ORANGE, CYAN, WHITE
from utils import load_image_with_transparency

class EternalDragon(MultiStageBoss):
    def __init__(self):
        stages = [
            BossStage("Young Dragon", 600, (0, 100, 0), 
                     "A young dragon appears... full of youthful fury!"),
            BossStage("Fire Dragon", 800, (255, 50, 0), 
                     "The dragon breathes fire... ancient power surges!"),
            BossStage("Ice Dragon", 1000, (100, 200, 255), 
                     "Cold as ice... freezing winds blow!"),
            BossStage("Ancient Dragon", 1400, (150, 0, 150), 
                     "The elder dragon awakens... ultimate power unleashed!"),
        ]
        super().__init__(WIDTH // 2 - 100, 50, 200, 200, "Eternal Dragon", stages)
        
        self.fire_breath = []
        self.ice_shards = []
        self.dragon_marks = []
        self.lightning_storm = False
        self.elemental_orbs = []
        self.stage_attack_toggle = 0
        self.damage_cooldowns = {}

        try:
            self.sprite = load_image_with_transparency("assets", "sprites", "eternal_dragon.png", transparent_color=(0, 0, 0))
            self.sprite = pygame.transform.scale(self.sprite, (self.width, self.height))
            self.use_sprite = True
        except Exception:
            self.use_sprite = False
        
    def run_attacks(self):
        super().run_attacks()

        for attack_id in list(self.damage_cooldowns.keys()):
            self.damage_cooldowns[attack_id] -= 1
            if self.damage_cooldowns[attack_id] <= 0:
                del self.damage_cooldowns[attack_id]
        
        # Update stage-specific hazards
        self.update_fire_breath()
        self.update_ice_shards()

        if self.current_stage and self.current_stage.can_attack():
            if self.current_stage_index == 0:  # Young Dragon
                if self.stage_attack_toggle == 0:
                    self.claw_attack()
                elif self.stage_attack_toggle == 1:
                    self.wing_gust_attack()
                else:
                    self.tail_slam_attack()
                self.stage_attack_toggle = (self.stage_attack_toggle + 1) % 3
                self.current_stage.attack_cooldown = 82
            elif self.current_stage_index == 1:  # Fire Dragon
                if self.stage_attack_toggle == 0:
                    self.fire_breath_attack()
                elif self.stage_attack_toggle == 1:
                    self.sweeping_fire_breath()
                else:
                    self.ember_rain_attack()
                self.stage_attack_toggle = (self.stage_attack_toggle + 1) % 3
                self.current_stage.attack_cooldown = 104
            elif self.current_stage_index == 2:  # Ice Dragon
                if self.stage_attack_toggle == 0:
                    self.ice_storm_attack()
                elif self.stage_attack_toggle == 1:
                    self.ice_wall_sweep()
                else:
                    self.glacial_lance_attack()
                self.stage_attack_toggle = (self.stage_attack_toggle + 1) % 3
                self.current_stage.attack_cooldown = 132
            elif self.current_stage_index == 3:  # Ancient Dragon
                if self.stage_attack_toggle == 0:
                    self.elemental_cataclysm()
                elif self.stage_attack_toggle == 1:
                    self.ancient_crossfire()
                else:
                    self.starfall_breath_attack()
                self.stage_attack_toggle = (self.stage_attack_toggle + 1) % 3
                self.current_stage.attack_cooldown = 156
            
        self.movement()

    def transition_to_stage(self, stage_index):
        super().transition_to_stage(stage_index)
        self.stage_attack_toggle = 0
        self.fire_breath.clear()
        self.ice_shards.clear()
        self.dragon_marks.clear()
        self.effects = [effect for effect in self.effects if isinstance(effect, Telegraph) and effect.duration > 0][:6]
            
    def claw_attack(self):
        # Swift claw attacks
        for i in range(3):
            if self.game and self.game.player:
                target_x = self.game.player.x + self.game.player.width // 2
                target_y = self.game.player.y + self.game.player.height // 2
                dx = target_x - self.x
                dy = target_y - self.y
                
                # Create claw projectile
                claw = Projectile(self.x + self.width // 2, self.y + self.height // 2, dx/10, dy/10, 12, (100, 100, 100), 10)
                claw.claw = True
                self.projectiles.append(claw)
                
    def fire_breath_attack(self):
        # Sustained forward cone with enough width to punish late sidesteps.
        breath_x = self.x + self.width // 2
        breath_y = self.y + self.height
        
        for _ in range(24):
            angle = random.uniform(-math.pi / 3.4, math.pi / 3.4)
            speed = random.uniform(4.8, 8.2)
            dx = math.sin(angle) * speed
            dy = abs(math.cos(angle)) * speed + 1.5
            fire = Projectile(breath_x, breath_y, dx, dy, 17, (255, 100, 0), 9)
            fire.fire = True
            self.fire_breath.append(fire)

    def sweeping_fire_breath(self):
        # Sweeping breath with a rotating gap
        breath_x = self.x + self.width // 2
        breath_y = self.y + self.height
        base_angle = math.sin(pygame.time.get_ticks() * 0.002) * 0.6
        safe_gap = base_angle + random.uniform(-0.2, 0.2)
        for i in range(28):
            angle = -math.pi / 2 + (i / 27) * math.pi
            if abs(angle - safe_gap) < 0.25:
                continue
            speed = random.uniform(4.5, 7.5)
            dx = math.cos(angle) * speed
            dy = abs(math.sin(angle)) * speed + 1.5
            fire = Projectile(breath_x, breath_y, dx, dy, 16, (255, 120, 0), 8)
            fire.fire = True
            self.fire_breath.append(fire)
            
    def ice_storm_attack(self):
        # Ice shard storm with freezing effect
        for i in range(16):
            angle = (math.pi * 2 * i) / 16
            dx = math.cos(angle) * 7
            dy = math.sin(angle) * 7
            ice = Projectile(
                self.x + self.width // 2, self.y + self.height // 2,
                dx, dy, 12, (100, 200, 255), 6
            )
            ice.ice = True
            self.ice_shards.append(ice)

    def ice_wall_sweep(self):
        # Sweeping wall of ice shards across the arena
        y = random.randint(180, HEIGHT - 120)
        direction = random.choice([-1, 1])
        start_x = 0 if direction > 0 else WIDTH
        for i in range(12):
            shard = Projectile(start_x, y + (i - 6) * 12, 6 * direction, 0, 10, (120, 220, 255), 6)
            shard.ice = True
            self.ice_shards.append(shard)
            
    def elemental_cataclysm(self):
        # Ultimate attack combining all elements
        # Fire spiral
        for i in range(12):
            angle = (math.pi * 2 * i) / 12 + pygame.time.get_ticks() * 0.001
            dx = math.cos(angle) * 8
            dy = math.sin(angle) * 8
            fire = Projectile(
                self.x + self.width // 2, self.y + self.height // 2,
                dx, dy, 20, (255, 50, 0), 10
            )
            fire.ultimate = True
            self.projectiles.append(fire)
            
        # Ice explosion
        for i in range(8):
            ice_x = random.randint(100, WIDTH - 100)
            ice_y = random.randint(100, HEIGHT - 100)
            ice = Projectile(ice_x, ice_y, 0, 0, 25, (100, 200, 255), 15)
            ice.ultimate = True
            self.ice_shards.append(ice)
            
        # Lightning storm
        self.lightning_storm = True
        for i in range(6):
            strike_x = random.randint(50, WIDTH - 50)
            strike_y = random.randint(50, HEIGHT - 150)
            lightning = Projectile(strike_x, strike_y, 0, 0, 30, (255, 255, 0), 20)
            lightning.lightning = True
            self.projectiles.append(lightning)

    def ancient_crossfire(self):
        # Alternating fire and ice lanes
        center_x = self.x + self.width // 2
        center_y = self.y + self.height // 2

        for i in range(10):
            angle = (math.pi * 2 * i) / 10
            if i % 2 == 0:
                proj = Projectile(center_x, center_y, math.cos(angle) * 7, math.sin(angle) * 7, 16, (255, 80, 20), 8)
                proj.fire = True
            else:
                proj = Projectile(center_x, center_y, math.cos(angle) * 6, math.sin(angle) * 6, 14, (100, 200, 255), 7)
                proj.ice = True
                self.ice_shards.append(proj)
                continue
            self.projectiles.append(proj)

    def wing_gust_attack(self):
        # Short-range gust that pushes player away with shards
        center_x = self.x + self.width // 2
        center_y = self.y + self.height // 2
        for i in range(6):
            angle = (math.pi * 2 * i) / 6
            gust = Projectile(center_x, center_y, math.cos(angle) * 5, math.sin(angle) * 5, 10, (180, 180, 180), 6)
            gust.gust = True
            self.projectiles.append(gust)

    def tail_slam_attack(self):
        if not (self.game and self.game.player):
            return
        tx = self.game.player.x + self.game.player.width // 2
        ty = self.game.player.y + self.game.player.height // 2
        self.effects.append(Telegraph(tx, ty, 42, 72, (210, 210, 210), warning_type="pulse"))
        for i in range(8):
            angle = (math.pi * 2 * i) / 8
            shock = Projectile(tx, ty, math.cos(angle) * 4.5, math.sin(angle) * 4.5, 11, (200, 200, 200), 6)
            shock.claw = True
            self.projectiles.append(shock)

    def ember_rain_attack(self):
        lane_count = 6
        safe_lane = random.randint(0, lane_count - 1)
        lane_width = WIDTH / lane_count
        for lane in range(lane_count):
            if lane == safe_lane:
                continue
            x = int(lane * lane_width + lane_width * 0.5)
            self.effects.append(Telegraph(x, HEIGHT // 2, 34, 180, (255, 120, 40), warning_type="cross"))
            for drop in range(3):
                ember = Projectile(x + random.randint(-16, 16), -20 - drop * 28, 0, random.uniform(5.5, 7.5), 12, (255, 140, 0), 7)
                ember.fire = True
                self.fire_breath.append(ember)

    def glacial_lance_attack(self):
        if not (self.game and self.game.player):
            return
        tx = self.game.player.x + self.game.player.width // 2
        ty = self.game.player.y + self.game.player.height // 2
        for offset in (-90, -45, 0, 45, 90):
            lance_x = max(50, min(WIDTH - 50, tx + offset))
            self.effects.append(Telegraph(lance_x, ty, 36, 100, (180, 230, 255), warning_type="cross"))
            lance = Projectile(lance_x, 0, 0, 8.5, 13, (160, 230, 255), 7)
            lance.ice = True
            self.ice_shards.append(lance)

    def starfall_breath_attack(self):
        center_x = self.x + self.width // 2
        center_y = self.y + self.height // 2
        for ring in range(2):
            for i in range(12):
                angle = (math.pi * 2 * i) / 12 + ring * 0.16
                speed = 5.5 + ring * 1.4
                proj = Projectile(center_x, center_y, math.cos(angle) * speed, math.sin(angle) * speed, 18, (255, 220, 120), 8)
                proj.lightning = True
                self.projectiles.append(proj)
        for _ in range(4):
            self.dragon_marks.append({
                'x': random.randint(90, WIDTH - 90),
                'y': random.randint(130, HEIGHT - 110),
                'radius': 34,
                'timer': 42,
                'burst_done': False,
            })
            
    def update_fire_breath(self):
        for fire in self.fire_breath[:]:
            fire.update()
            if fire.is_off_screen():
                self.fire_breath.remove(fire)
            elif self.game and self.game.player and self.game.player.get_rect().colliderect(fire.get_rect()):
                fire_id = f"dragon_fire_{id(fire)}"
                if fire_id not in self.damage_cooldowns:
                    damage = fire.damage
                    self.game.player.take_damage(damage)
                    self.damage_cooldowns[fire_id] = 8
                    if hasattr(self.game, 'performance_logger'):
                        stage_name = self.current_stage.name if self.current_stage else "Dragon"
                        self.game.performance_logger.log_ability_damage(self.name, f"{stage_name} - Fire Breath", damage)
                if fire in self.fire_breath:
                    self.fire_breath.remove(fire)
                
    def update_ice_shards(self):
        for ice in self.ice_shards[:]:
            if hasattr(ice, 'ice') and self.game and self.game.player:
                tx = self.game.player.x + self.game.player.width // 2
                ty = self.game.player.y + self.game.player.height // 2
                if hasattr(ice, "steer_towards"):
                    ice.steer_towards(tx, ty, desired_speed=6.0, max_turn=0.03, accel=0.08)
            ice.update()
            if ice.is_off_screen():
                self.ice_shards.remove(ice)
            elif self.game and self.game.player:
                # Check collision with player
                if self.game.player.get_rect().colliderect(ice.get_rect()):
                    self.game.player.take_damage(ice.damage)
                    self.game.player.add_speed_modifier(0.25, 90)  # Slow to 25% for 1.5 seconds
                    if hasattr(self.game, 'performance_logger'):
                        stage_name = self.current_stage.name if self.current_stage else "Dragon"
                        self.game.performance_logger.log_ability_damage(self.name, f"{stage_name} - Ice Shards", ice.damage)
                    self.ice_shards.remove(ice)

    def update_dragon_marks(self):
        active_marks = []
        for mark in self.dragon_marks:
            mark['timer'] -= 1
            if mark['timer'] <= 0 and not mark['burst_done']:
                mark['burst_done'] = True
                for i in range(10):
                    angle = (math.pi * 2 * i) / 10
                    proj = Projectile(mark['x'], mark['y'], math.cos(angle) * 5.5, math.sin(angle) * 5.5, 14, (255, 220, 120), 7)
                    proj.lightning = True
                    self.projectiles.append(proj)
            if mark['timer'] > -6:
                active_marks.append(mark)
        self.dragon_marks = active_marks
                    
    def movement(self):
        # Dragon flight pattern
        speed = 3 + self.current_stage_index
        self.x += math.sin(pygame.time.get_ticks() * 0.001) * speed
        self.y += math.cos(pygame.time.get_ticks() * 0.0015) * speed
            
        self.x = max(50, min(WIDTH - 250, self.x))
        self.y = max(30, min(HEIGHT - 300, self.y))
        self.update_rect()
        
    def draw(self, screen):
        # Draw elemental effects
        if self.current_stage_index == 1:  # Fire aura
            for i in range(5):
                angle = (math.pi * 2 * i) / 5 + pygame.time.get_ticks() * 0.002
                flame_x = self.x + self.width // 2 + math.cos(angle) * 60
                flame_y = self.y + self.height // 2 + math.sin(angle) * 60
                pygame.draw.circle(screen, (255, 150, 0), (int(flame_x), int(flame_y)), 8, 2)
                
        elif self.current_stage_index == 2:  # Ice aura
            for i in range(4):
                angle = (math.pi * 2 * i) / 4 - pygame.time.get_ticks() * 0.001
                ice_x = self.x + self.width // 2 + math.cos(angle) * 50
                ice_y = self.y + self.height // 2 + math.sin(angle) * 50
                pygame.draw.circle(screen, (100, 200, 255), (int(ice_x), int(ice_y)), 10, 3)

        self.update_dragon_marks()
        for mark in self.dragon_marks:
            pulse_radius = int(mark['radius'] + 4 * math.sin(pygame.time.get_ticks() * 0.01))
            color = (255, 230, 170) if mark['timer'] > 0 else (255, 255, 255)
            pygame.draw.circle(screen, color, (int(mark['x']), int(mark['y'])), max(8, pulse_radius), 2)
                               
        if hasattr(self, "use_sprite") and self.use_sprite:
            self.draw_sprite_to_hitbox(screen)
        else:
            pygame.draw.rect(screen, self.color, self.get_rect())
        
        # Draw projectiles from all active attack lists
        for projectile in self.projectiles:
            projectile.draw(screen)
        for fire in self.fire_breath:
            fire.draw(screen)
        for ice in self.ice_shards:
            ice.draw(screen)
            
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


