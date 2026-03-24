import pygame
import math
import random
from .immortal_phoenix import MultiStageBoss, BossStage
from core.projectile import Projectile
from core.effect import Telegraph
from config.constants import WIDTH, HEIGHT, RED, BLUE, GREEN, YELLOW, PURPLE, ORANGE, CYAN, WHITE
from utils import load_boss_profile

class CyberOverlord(MultiStageBoss):
    DEFAULT_STAGE_PROFILE = {
        0: {"drone_cd": 130},
        1: {"laser_cd": 112, "predictive_strike_delay": 34},
        2: {"glitch_cd": 205, "glitch_count": 24},
    }

    def __init__(self):
        stages = [
            BossStage("Basic AI", 700, (150, 150, 150), 
                     "Neural networks activating... combat protocols engaged!"),
            BossStage("Adaptive AI", 900, (200, 100, 100), 
                     "Learning patterns... adapting to your strategy!"),
            BossStage("Sentient AI", 1200, (255, 0, 255), 
                     "Consciousness achieved... I am become death!"),
        ]
        super().__init__(WIDTH // 2 - 90, 80, 180, 180, "Cyber Overlord", stages)
        
        self.drones = []
        self.lasers = []
        self.adaptive_patterns = []
        self.learning_data = {'player_moves': [], 'attack_hits': [], 'dodge_patterns': []}
        self.hack_mode = False
        self.matrix_glitch = False
        self.drone_cooldown = 0
        self.adaptive_laser_cooldown = 0
        self.matrix_glitch_cooldown = 0
        self.overloaded_timer = 0
        self.prediction_strikes = []
        self.stage_profile = load_boss_profile("Cyber Overlord", "stage_profile", self.DEFAULT_STAGE_PROFILE)
        
    def run_attacks(self):
        super().run_attacks()
        
        # Update cooldowns
        self.drone_cooldown -= 1
        self.adaptive_laser_cooldown -= 1
        self.matrix_glitch_cooldown -= 1
        self.overloaded_timer -= 1
        
        # Learn from player behavior
        if self.game and self.game.player:
            self.learning_data['player_moves'].append((self.game.player.x, self.game.player.y))
            if len(self.learning_data['player_moves']) > 60:
                self.learning_data['player_moves'].pop(0)

        if self.overloaded_timer > 0:
            # Brief vulnerability window after losing the leader drone
            self.update_drones()
            self.update_lasers()
            self.movement(slowed=True)
            return
                
        if self.current_stage_index == 0:  # Basic AI
            if self.drone_cooldown <= 0:
                self.drone_swarm_attack()
                self.drone_cooldown = self.stage_profile[0]["drone_cd"]
        elif self.current_stage_index == 1:  # Adaptive AI
            if self.adaptive_laser_cooldown <= 0:
                self.adaptive_laser_attack()
                self.adaptive_laser_cooldown = self.stage_profile[1]["laser_cd"]
        elif self.current_stage_index == 2:  # Sentient AI
            if self.matrix_glitch_cooldown <= 0:
                self.matrix_glitch_attack()
                self.matrix_glitch_cooldown = self.stage_profile[2]["glitch_cd"]
                
        # Call update methods
        self.update_drones()
        self.update_lasers()
        self.movement()
            
    def drone_swarm_attack(self):
        # Deploy hunter drones
        for i in range(4):
            drone_x = self.x + (i - 1.5) * 60
            drone_y = self.y + (i - 1.5) * 40
            self.drones.append({
                'x': drone_x, 'y': drone_y,
                'target': None,
                'lifetime': 240,
                'fire_cooldown': 60,
                'angle': i * (math.pi / 2),
                'orbit_radius': 80,
                'is_leader': i == 0
            })
            
    def adaptive_laser_attack(self):
        # Predictive laser targeting based on player movement
        if self.game and self.game.player and self.learning_data['player_moves']:
            # Predict player position
            recent_moves = self.learning_data['player_moves'][-10:]
            if recent_moves:
                avg_x = sum(move[0] for move in recent_moves) / len(recent_moves)
                avg_y = sum(move[1] for move in recent_moves) / len(recent_moves)
                
                # Fire predictive lasers
                for i in range(3):
                    pred_x = avg_x + (i - 1) * 50
                    pred_y = avg_y + (i - 1) * 30
                    self.effects.append(Telegraph(pred_x, pred_y, 40, 40, (255, 0, 0)))
                    self.prediction_strikes.append({
                        'x': pred_x,
                        'y': pred_y,
                        'timer': self.stage_profile[1]["predictive_strike_delay"]
                    })
                    
    def matrix_glitch_attack(self):
        self.matrix_glitch = True
        # Glitch reality with multiple attack patterns
        for _ in range(self.stage_profile[2]["glitch_count"]):
            glitch_x = random.randint(0, WIDTH)
            glitch_y = random.randint(0, HEIGHT)
            glitch_type = random.choice(['laser', 'drone', 'data_corruption'])
            
            if glitch_type == 'laser':
                laser = Projectile(glitch_x, glitch_y, 0, 0, 25, (255, 0, 255), 12)
                laser.glitch = True
                self.projectiles.append(laser)
            elif glitch_type == 'drone':
                self.drones.append({
                    'x': glitch_x, 'y': glitch_y,
                    'target': self.game.player if self.game else None,
                    'lifetime': 120,
                    'fire_cooldown': 30
                })
                
    def update_drones(self):
        active_drones = []
        consumed_projectile_ids = set()
        player_projectiles = None
        if self.game and self.game.player:
            player_projectiles = self.game.player.projectiles

        for drone in self.drones:
            # Backfill defaults so glitch-spawned drones don't crash update logic.
            drone.setdefault('lifetime', 120)
            drone.setdefault('fire_cooldown', 45)
            drone.setdefault('angle', random.uniform(0, math.pi * 2))
            drone.setdefault('orbit_radius', random.randint(60, 100))
            drone.setdefault('target', self.game.player if self.game else None)

            drone['lifetime'] -= 1
            drone['fire_cooldown'] -= 1
            
            if drone['lifetime'] <= 0:
                continue

            # Orbit around boss for more readable patterns
            drone['angle'] = (drone['angle'] + 0.03) % (math.pi * 2)
            center_x = self.x + self.width // 2
            center_y = self.y + self.height // 2
            drone['x'] = center_x + math.cos(drone['angle']) * drone['orbit_radius']
            drone['y'] = center_y + math.sin(drone['angle']) * (drone['orbit_radius'] * 0.6)

            # Check if player projectiles destroy drones
            drone_destroyed = False
            if player_projectiles is not None:
                drone_rect = pygame.Rect(drone['x'] - 12, drone['y'] - 10, 24, 20)
                for projectile in player_projectiles:
                    projectile_id = id(projectile)
                    if projectile_id in consumed_projectile_ids:
                        continue
                    if drone_rect.colliderect(projectile.get_rect()):
                        consumed_projectile_ids.add(projectile_id)
                        drone_destroyed = True
                        if drone.get('is_leader'):
                            self._enter_overload()
                        break

            if drone_destroyed:
                continue

            if drone.get('target') and drone['fire_cooldown'] <= 0:
                # Fire at target
                dx = drone['target'].x - drone['x']
                dy = drone['target'].y - drone['y']
                dist = math.sqrt(dx**2 + dy**2)
                if dist > 0:
                    bullet = Projectile(drone['x'], drone['y'], 
                                       dx/dist * 8, dy/dist * 8, 10, (200, 100, 100), 6)
                    self.projectiles.append(bullet)
                drone['fire_cooldown'] = 60
            active_drones.append(drone)

        self.drones = active_drones
        if player_projectiles is not None and consumed_projectile_ids:
            self.game.player.projectiles = [
                p for p in player_projectiles if id(p) not in consumed_projectile_ids
            ]
                    
    def update_lasers(self):
        # Spawn predictive lasers after warning delay
        active_strikes = []
        for strike in self.prediction_strikes:
            strike['timer'] -= 1
            if strike['timer'] <= 0:
                laser = Projectile(self.x + self.width // 2, self.y + self.height // 2, 0, 0, 20, (255, 0, 0), 10)
                laser.predictive = True
                laser.target_x = strike['x']
                laser.target_y = strike['y']
                self.lasers.append(laser)
            else:
                active_strikes.append(strike)
        self.prediction_strikes = active_strikes

        active_lasers = []
        for laser in self.lasers:
            if hasattr(laser, 'predictive') and laser.predictive:
                # Adjust trajectory toward predicted position
                if hasattr(laser, 'target_x'):
                    dx = laser.target_x - laser.x
                    dy = laser.target_y - laser.y
                    dist = math.sqrt(dx**2 + dy**2)
                    if dist > 5:
                        laser.dx = (dx / dist) * 15
                        laser.dy = (dy / dist) * 15
                        
            laser.update()
            if not laser.is_off_screen():
                active_lasers.append(laser)
        self.lasers = active_lasers
                
    def movement(self, slowed=False):
        # Machine movement - calculated and precise
        speed_scale = 0.4 if slowed else 1.0
        if self.current_stage_index == 2:  # Adaptive AI - track player
            if self.game and self.game.player:
                dx = self.game.player.x - self.x
                dy = self.game.player.y - self.y
                dist = math.sqrt(dx**2 + dy**2)
                if dist > 100:
                    self.x += (dx / dist) * 4 * speed_scale
                    self.y += (dy / dist) * 4 * speed_scale
        else:
            # Patrol pattern
            self.x += math.sin(pygame.time.get_ticks() * 0.002) * 3 * speed_scale
            self.y += math.cos(pygame.time.get_ticks() * 0.003) * 2 * speed_scale
            
        self.x = max(50, min(WIDTH - 230, self.x))
        self.y = max(30, min(HEIGHT - 280, self.y))
        self.update_rect()

    def _enter_overload(self):
        self.overloaded_timer = 90
        self.drones.clear()
        self.effects.append(Telegraph(self.x + self.width // 2, self.y + self.height // 2, 45, 45, (255, 255, 0)))
        if self.game:
            self.game.screen_shake.start(3, 12)
        
    def draw(self, screen):
        # Draw matrix glitch effect
        if self.matrix_glitch:
            screen_w = screen.get_width()
            screen_h = screen.get_height()
            for i in range(10):
                if random.random() < 0.3:
                    glitch_x = random.randint(0, screen_w)
                    glitch_y = random.randint(0, screen_h)
                    glitch_surface = pygame.Surface((50, 50))
                    glitch_surface.set_alpha(128)
                    pygame.draw.rect(glitch_surface, (255, 0, 255), (0, 0, 50, 50))
                    screen.blit(glitch_surface, (glitch_x, glitch_y))
                    
        # Draw drones
        for drone in self.drones:
            lifetime = drone.get('lifetime', 120)
            alpha = max(0.0, min(1.0, lifetime / 240))
            color = tuple(int(c * alpha) for c in (200, 100, 100))
            pygame.draw.rect(screen, color, (drone['x'] - 15, drone['y'] - 10, 30, 20))
            if drone.get('is_leader'):
                pygame.draw.rect(screen, (255, 255, 0), (drone['x'] - 18, drone['y'] - 13, 36, 26), 2)
            # Draw targeting line
            if drone.get('target'):
                pygame.draw.line(screen, (255, 0, 0), 
                               (drone['x'], drone['y']),
                               (drone['target'].x + drone['target'].width // 2, 
                                drone['target'].y + drone['target'].height // 2), 1)

        if self.overloaded_timer > 0:
            flicker = 0.5 + 0.5 * math.sin(pygame.time.get_ticks() * 0.02)
            glow = pygame.Surface((self.width + 20, self.height + 20), pygame.SRCALPHA)
            glow.fill((255, 255, 0, int(80 * flicker)))
            screen.blit(glow, (self.x - 10, self.y - 10))

        pygame.draw.rect(screen, self.color, self.get_rect())
        
        # Draw projectiles
        for projectile in self.projectiles:
            projectile.draw(screen)
            
        # Draw effects
        for effect in self.effects:
            effect.draw(screen)
            
        # Shared fight HUD owns the active boss label and stage text.
        self.health_bar_color = self.current_stage.color
        self.draw_health_bar(screen)
