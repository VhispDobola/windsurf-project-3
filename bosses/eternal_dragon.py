import pygame
import math
import random
from .immortal_phoenix import MultiStageBoss, BossStage
from core.projectile import Projectile
from core.effect import Telegraph
from config.constants import WIDTH, HEIGHT, RED, BLUE, GREEN, YELLOW, PURPLE, ORANGE, CYAN, WHITE
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
        self.lightning_storm = False
        self.wing_flaps = []
        self.elemental_orbs = []
        self.stage_attack_toggle = 0

        try:
            self.sprite = load_image_with_transparency("assets", "sprites", "eternal_dragon.png", transparent_color=(0, 0, 0))
            self.sprite = pygame.transform.scale(self.sprite, (self.width, self.height))
            self.use_sprite = True
        except Exception:
            self.use_sprite = False
        
    def run_attacks(self):
        super().run_attacks()
        
        # Update stage-specific hazards
        self.update_fire_breath()
        self.update_ice_shards()

        if self.current_stage and self.current_stage.can_attack():
            if self.current_stage_index == 0:  # Young Dragon
                if self.stage_attack_toggle == 0:
                    self.claw_attack()
                else:
                    self.wing_gust_attack()
                self.stage_attack_toggle = 1 - self.stage_attack_toggle
                self.current_stage.attack_cooldown = 90
            elif self.current_stage_index == 1:  # Fire Dragon
                if self.stage_attack_toggle == 0:
                    self.fire_breath_attack()
                else:
                    self.sweeping_fire_breath()
                self.stage_attack_toggle = 1 - self.stage_attack_toggle
                self.current_stage.attack_cooldown = 120
            elif self.current_stage_index == 2:  # Ice Dragon
                if self.stage_attack_toggle == 0:
                    self.ice_storm_attack()
                else:
                    self.ice_wall_sweep()
                self.stage_attack_toggle = 1 - self.stage_attack_toggle
                self.current_stage.attack_cooldown = 150
            elif self.current_stage_index == 3:  # Ancient Dragon
                if self.stage_attack_toggle == 0:
                    self.elemental_cataclysm()
                else:
                    self.ancient_crossfire()
                self.stage_attack_toggle = 1 - self.stage_attack_toggle
                self.current_stage.attack_cooldown = 180
            
        self.movement()
            
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
        # Massive fire breath cone
        breath_x = self.x + self.width // 2
        breath_y = self.y + self.height
        
        for i in range(20):
            angle = random.uniform(-math.pi/4, math.pi/4)
            dx = math.cos(angle) * random.uniform(3, 8)
            dy = math.sin(angle) * random.uniform(3, 8) + 2
            fire = Projectile(breath_x, breath_y, dx, dy, 15, (255, 100, 0), 8)
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
            dx = math.cos(angle) * random.uniform(3, 7)
            dy = math.sin(angle) * random.uniform(3, 7) + 2
            fire = Projectile(breath_x, breath_y, dx, dy, 14, (255, 120, 0), 7)
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
            
    def update_fire_breath(self):
        for fire in self.fire_breath[:]:
            fire.update()
            if fire.is_off_screen():
                self.fire_breath.remove(fire)
                
    def update_ice_shards(self):
        for ice in self.ice_shards[:]:
            ice.update()
            if ice.is_off_screen():
                self.ice_shards.remove(ice)
            elif self.game and self.game.player:
                # Check collision with player
                if self.game.player.get_rect().colliderect(ice.get_rect()):
                    self.game.player.take_damage(ice.damage)
                    self.game.player.add_speed_modifier(0.25, 90)  # Slow to 25% for 1.5 seconds
                    self.ice_shards.remove(ice)
                    
    def movement(self):
        # Dragon flight pattern
        speed = 3 + self.current_stage_index
        self.x += math.sin(pygame.time.get_ticks() * 0.001) * speed
        self.y += math.cos(pygame.time.get_ticks() * 0.0015) * speed
        
        # Wing flaps
        if self.current_stage_index >= 1:
            flap_offset = math.sin(pygame.time.get_ticks() * 0.01) * 20
            self.wing_flaps.append({
                'x': self.x - 40, 'y': self.y + flap_offset,
                'lifetime': 20
            })
            
        self.x = max(50, min(WIDTH - 250, self.x))
        self.y = max(30, min(HEIGHT - 300, self.y))
        self.update_rect()
        
    def draw(self, screen):
        # Draw wing flaps
        for flap in self.wing_flaps[:]:
            flap['lifetime'] -= 1
            if flap['lifetime'] > 0:
                pygame.draw.ellipse(screen, (0, 100, 0), 
                                  (flap['x'], flap['y'], 80, 40))
            else:
                self.wing_flaps.remove(flap)
                
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


