import pygame
import math
import random
from core.boss import Boss
from core.projectile import Projectile
from core.effect import Telegraph
from config.constants import WIDTH, HEIGHT, RED, BLUE, GREEN, YELLOW, PURPLE, ORANGE, CYAN
from utils import load_image_with_transparency

class TempestLord(Boss):
    def __init__(self):
        # Log-driven tuning: reduce burst lethality and smooth pacing.
        super().__init__(WIDTH // 2 - 60, 100, 120, 120, 760, "Tempest Lord")
        self.color = (100, 100, 255)
        self.lightning_bolts = []
        self.wind_zones = []
        self.rain_drops = []
        self.storm_intensity = 1
        self.thunder_cooldown = 0
        self.tornado_timer = 0
        self.lightning_network = []
        self.chain_reaction_cooldown = 0
        self.storm_front_timer = 0
        self.wind_shear_timer = 0
        self.charge_line_timer = 0
        self.storm_fronts = []
        
        # Load the Tempest Lord sprite
        try:
            self.sprite = load_image_with_transparency("assets", "sprites", "tempest_lord.png", transparent_color=(0, 0, 0))
            # Scale sprite to fit the boss dimensions
            self.sprite = pygame.transform.scale(self.sprite, (self.width, self.height))
            self.use_sprite = True
            self.logger.info("Tempest Lord sprite loaded successfully")
        except Exception as e:
            # Fallback to drawn version if sprite not found
            self.use_sprite = False
            self.logger.warning("Tempest Lord sprite not found - %s", e)
        
    def run_attacks(self):
        self.thunder_cooldown -= 1
        self.tornado_timer -= 1
        self.chain_reaction_cooldown -= 1
        self.storm_front_timer -= 1
        self.wind_shear_timer -= 1
        self.charge_line_timer -= 1
        
        if self.phase == 1:
            if self.thunder_cooldown <= 0:
                self.lightning_strike()
                self.thunder_cooldown = 110
            elif self.tornado_timer <= 0:
                self.create_tornado()
                self.tornado_timer = 190
            elif self.chain_reaction_cooldown <= 0:
                self.lightning_chain_reaction()
                self.chain_reaction_cooldown = 260
            elif self.storm_front_timer <= 0:
                self.create_storm_front()
                self.storm_front_timer = 240
                
        elif self.phase == 2:
            if self.thunder_cooldown <= 0:
                self.chain_lightning()
                self.thunder_cooldown = 90
            elif self.tornado_timer <= 0:
                self.create_tornado_cluster()
                self.tornado_timer = 140
            elif self.charge_line_timer <= 0:
                self.charge_line_strike()
                self.charge_line_timer = 220
            elif self.wind_shear_timer <= 0:
                self.create_wind_shear()
                self.wind_shear_timer = 180
                
        else:  # phase 3
            if self.thunder_cooldown <= 0:
                self.lightning_storm()
                self.thunder_cooldown = 65
            elif self.tornado_timer <= 0:
                self.mass_tornado_field()
                self.tornado_timer = 100
            elif self.storm_front_timer <= 0:
                self.create_storm_front(stronger=True)
                self.storm_front_timer = 160
            self.create_hurricane()
                
        self.movement()
        self.update_weather_effects()
        
    def lightning_strike(self):
        if self.game and self.game.player:
            target_x = self.game.player.x + self.game.player.width // 2
            target_y = self.game.player.y + self.game.player.height // 2
            
            # Create lightning bolt effect
            self.effects.append(Telegraph(target_x, target_y, 100, 100, (255, 255, 0)))
            
            # Actual lightning damage
            lightning = Projectile(
                self.x + self.width // 2, self.y + self.height // 2,
                0, 0, 12, (255, 255, 100), 13
            )
            lightning.lightning = True
            lightning.target_x = target_x
            lightning.target_y = target_y
            lightning.lifetime = 60
            self.lightning_bolts.append(lightning)
            
    def chain_lightning(self):
        # Create chain lightning that bounces
        if self.game and self.game.player:
            start_x = self.game.player.x + self.game.player.width // 2
            start_y = self.game.player.y + self.game.player.height // 2
        else:
            start_x = self.x + self.width // 2
            start_y = self.y + self.height // 2

        for i in range(4):
            angle = random.uniform(0, math.pi * 2)
            distance = 140 + i * 35
            end_x = start_x + math.cos(angle) * distance
            end_y = start_y + math.sin(angle) * distance
            end_x = max(60, min(WIDTH - 60, end_x))
            end_y = max(80, min(HEIGHT - 60, end_y))
            
            lightning = Projectile(start_x, start_y, 0, 0, 11, (200, 200, 255), 12)
            lightning.chain = True
            lightning.chain_end_x = end_x
            lightning.chain_end_y = end_y
            lightning.lifetime = 100
            lightning.segment_width = 20
            lightning.damage_cooldown = 0
            self.lightning_network.append(lightning)
            
            start_x, start_y = end_x, end_y
            
    def lightning_storm(self):
        # Massive lightning attack
        for i in range(8):
            angle = (math.pi * 2 * i) / 8
            dist = random.uniform(100, 250)
            target_x = self.x + self.width // 2 + math.cos(angle) * dist
            target_y = self.y + self.height // 2 + math.sin(angle) * dist
            
            lightning = Projectile(
                self.x + self.width // 2, self.y + self.height // 2,
                0, 0, 14, (255, 200, 100), 16
            )
            lightning.lightning = True
            lightning.target_x = target_x
            lightning.target_y = target_y
            lightning.lifetime = 80
            self.lightning_bolts.append(lightning)
            
    def lightning_chain_reaction(self):
        # Create initial lightning strike
        if self.game and self.game.player:
            target_x = self.game.player.x + self.game.player.width // 2
            target_y = self.game.player.y + self.game.player.height // 2
            
            # Create chain of lightning explosions
            chain_points = []
            current_x = self.x + self.width // 2
            current_y = self.y + self.height // 2
            
            for i in range(5):
                # Calculate next point in chain
                if i < 4:
                    # Move towards player with some randomness
                    dx = target_x - current_x
                    dy = target_y - current_y
                    dist = math.sqrt(dx**2 + dy**2)
                    if dist > 0:
                        next_x = current_x + (dx / dist) * 100 + random.randint(-30, 30)
                        next_y = current_y + (dy / dist) * 100 + random.randint(-30, 30)
                    else:
                        next_x = current_x + random.randint(-50, 50)
                        next_y = current_y + random.randint(-50, 50)
                else:
                    # Final strike at player position
                    next_x = target_x
                    next_y = target_y
                    
                chain_points.append((current_x, current_y, next_x, next_y))
                
                # Create explosion at each point
                for j in range(8):
                    angle = (math.pi * 2 * j) / 8
                    dx = math.cos(angle) * 4
                    dy = math.sin(angle) * 4
                    lightning = Projectile(
                        next_x, next_y, dx, dy, 8, (255, 255, 100), 7
                    )
                    lightning.chain = True
                    lightning.lifetime = 40
                    self.lightning_bolts.append(lightning)
                    
                # Create telegraph for next strike
                if i < 4:
                    self.effects.append(Telegraph(next_x, next_y, 40, 40, (255, 255, 0)))
                    
                current_x = next_x
                current_y = next_y
                
        # Add screen shake for chain reaction
        if self.game:
            self.game.screen_shake.start(4, 18)
            
    def create_tornado(self):
        tornado_x = random.randint(100, WIDTH - 200)
        tornado_y = random.randint(100, HEIGHT - 200)
        self.wind_zones.append({
            'x': tornado_x, 'y': tornado_y,
            'radius': 60, 'lifetime': 300,
            'pull_strength': 2
        })
        self.effects.append(Telegraph(tornado_x, tornado_y, 120, 120, (150, 150, 255)))
        
    def create_storm_front(self, stronger=False):
        # Horizontal storm front that sweeps across the arena
        y = random.randint(140, HEIGHT - 140)
        direction = random.choice([-1, 1])
        front = {
            'x': 0 if direction > 0 else WIDTH,
            'y': y,
            'width': 40,
            'height': 140,
            'vx': 4 if stronger else 3,
            'damage': 12 if stronger else 8,
            'lifetime': 180
        }
        self.storm_fronts.append(front)
        self.effects.append(Telegraph(WIDTH // 2, y, 45, 160, (150, 150, 255)))
        
    def charge_line_strike(self):
        # Telegraph a line; after a delay, fire a fast strike down it
        x = random.randint(120, WIDTH - 120)
        self.effects.append(Telegraph(x, HEIGHT // 2, 50, 200, (255, 255, 0), warning_type="cross"))
        self.lightning_bolts.append({
            'x': x, 'y': 0,
            'vy': 10,
            'width': 12, 'height': HEIGHT,
            'damage': 12,
            'lifetime': 80,
            'line_strike': True,
            'damage_cooldown': 0
        })
        
    def create_tornado_cluster(self):
        for i in range(3):
            angle = (math.pi * 2 * i) / 3
            tornado_x = int(self.x + self.width // 2 + math.cos(angle) * 150)
            tornado_y = int(self.y + self.height // 2 + math.sin(angle) * 150)
            self.wind_zones.append({
                'x': tornado_x, 'y': tornado_y,
                'radius': 80, 'lifetime': 240,
                'pull_strength': 3
            })
            
    def mass_tornado_field(self):
        for i in range(5):
            tornado_x = random.randint(50, WIDTH - 100)
            tornado_y = random.randint(50, HEIGHT - 150)
            self.wind_zones.append({
                'x': tornado_x, 'y': tornado_y,
                'radius': 100, 'lifetime': 300,
                'pull_strength': 4
            })
            
    def create_wind_shear(self):
        # Apply gentle wind force that player can resist with movement
        if self.game and self.game.player:
            dx = self.game.player.x - self.x
            dy = self.game.player.y - self.y
            dist = math.sqrt(dx**2 + dy**2)
            if dist > 0 and dist < 300:  # Only affect if within range
                # Apply gentle push force (much weaker than before)
                push_x = (dx / dist) * 2  # Reduced from 9 to 2
                push_y = (dy / dist) * 2  # Reduced from 9 to 2
                
                # Apply force as a temporary speed modifier instead of direct position change
                if not hasattr(self.game.player, 'wind_force_x'):
                    self.game.player.wind_force_x = 0
                    self.game.player.wind_force_y = 0
                    
                self.game.player.wind_force_x += push_x
                self.game.player.wind_force_y += push_y
                
                # Cap the wind force to prevent being too strong
                max_wind = 3
                self.game.player.wind_force_x = max(-max_wind, min(max_wind, self.game.player.wind_force_x))
                self.game.player.wind_force_y = max(-max_wind, min(max_wind, self.game.player.wind_force_y))
                
    def create_hurricane(self):
        # Constant circular wind effect
        if self.game and self.game.player:
            center_x = self.x + self.width // 2
            center_y = self.y + self.height // 2
            dx = self.game.player.x - center_x
            dy = self.game.player.y - center_y
            dist = math.sqrt(dx**2 + dy**2)
            
            if dist < 180 and dist > 0:
                # Circular motion
                angle = math.atan2(dy, dx) + 0.06
                new_x = center_x + math.cos(angle) * dist
                new_y = center_y + math.sin(angle) * dist
                # Keep player within bounds
                self.game.player.x = max(0, min(WIDTH - self.game.player.width, new_x))
                self.game.player.y = max(0, min(HEIGHT - self.game.player.height, new_y))
                self.game.player.update_rect()
                
    def movement(self):
        # Floating movement
        self.x += math.sin(pygame.time.get_ticks() * 0.001) * 2
        self.y += math.cos(pygame.time.get_ticks() * 0.0015) * 1.5
        
        self.x = max(50, min(WIDTH - 170, self.x))
        self.y = max(50, min(HEIGHT - 220, self.y))
        self.update_rect()
        
    def update_weather_effects(self):
        # Update lightning bolts
        for bolt in self.lightning_bolts[:]:
            if isinstance(bolt, dict) and bolt.get('line_strike'):
                bolt['y'] += bolt['vy']
                bolt['lifetime'] -= 1
                if bolt['damage_cooldown'] > 0:
                    bolt['damage_cooldown'] -= 1
                if bolt['lifetime'] <= 0:
                    self.lightning_bolts.remove(bolt)
                elif self.game and self.game.player:
                    strike_rect = pygame.Rect(bolt['x'] - bolt['width']//2, 0, bolt['width'], HEIGHT)
                    if strike_rect.colliderect(self.game.player.get_rect()):
                        if bolt['damage_cooldown'] <= 0:
                            self.game.player.take_damage(bolt['damage'])
                            bolt['damage_cooldown'] = 25
                continue

            if hasattr(bolt, 'lightning') and bolt.lightning:
                # Move towards target
                if hasattr(bolt, 'target_x'):
                    dx = bolt.target_x - bolt.x
                    dy = bolt.target_y - bolt.y
                    dist = math.sqrt(dx**2 + dy**2)
                    if dist > 5:
                        bolt.x += (dx / dist) * 20
                        bolt.y += (dy / dist) * 20
                        
            bolt.update()
            # Remove if off screen or lifetime expired
            if bolt.is_off_screen() or (hasattr(bolt, 'lifetime') and bolt.lifetime <= 0):
                self.lightning_bolts.remove(bolt)
            elif hasattr(bolt, 'lifetime'):
                bolt.lifetime -= 1
                
        # Update lightning network
        for lightning in self.lightning_network[:]:
            lightning.update()
            if hasattr(lightning, 'damage_cooldown') and lightning.damage_cooldown > 0:
                lightning.damage_cooldown -= 1
            if self.game and self.game.player and self._segment_hits_player(lightning):
                if getattr(lightning, 'damage_cooldown', 0) <= 0:
                    self.game.player.take_damage(lightning.damage)
                    lightning.damage_cooldown = 20
            # Remove if off screen or lifetime expired
            if lightning.is_off_screen() or (hasattr(lightning, 'lifetime') and lightning.lifetime <= 0):
                self.lightning_network.remove(lightning)
            elif hasattr(lightning, 'lifetime'):
                lightning.lifetime -= 1
                
        # Update wind zones
        for zone in self.wind_zones[:]:
            zone['lifetime'] -= 1
            if zone['lifetime'] <= 0:
                self.wind_zones.remove(zone)
            elif self.game and self.game.player:
                # Apply wind effect
                dx = self.game.player.x - zone['x']
                dy = self.game.player.y - zone['y']
                dist = math.sqrt(dx**2 + dy**2)
                
                if dist < zone['radius'] and dist > 0:
                    pull_x = -(dx / dist) * zone['pull_strength']
                    pull_y = -(dy / dist) * zone['pull_strength']
                    new_x = self.game.player.x + pull_x
                    new_y = self.game.player.y + pull_y
                    # Keep player within bounds
                    self.game.player.x = max(0, min(WIDTH - self.game.player.width, new_x))
                    self.game.player.y = max(0, min(HEIGHT - self.game.player.height, new_y))
                    self.game.player.update_rect()
                    
        # Update storm fronts
        for front in self.storm_fronts[:]:
            front['lifetime'] -= 1
            if front['lifetime'] <= 0:
                self.storm_fronts.remove(front)
            else:
                front['x'] += front['vx']
                rect = pygame.Rect(front['x'], front['y'] - front['height']//2, front['width'], front['height'])
                if self.game and self.game.player and rect.colliderect(self.game.player.get_rect()):
                    if not front.get('damage_cooldown') or front['damage_cooldown'] <= 0:
                        self.game.player.take_damage(front['damage'])
                        front['damage_cooldown'] = 40
                    else:
                        front['damage_cooldown'] -= 1
                    
        # Create rain effect
        if random.random() < 0.3:
            for _ in range(3):
                rain_x = random.randint(0, WIDTH)
                rain_y = 0
                self.rain_drops.append({
                    'x': rain_x, 'y': rain_y,
                    'speed': random.uniform(5, 8),
                    'lifetime': 100
                })
                
        # Update rain
        for drop in self.rain_drops[:]:
            drop['y'] += drop['speed']
            drop['lifetime'] -= 1
            if drop['lifetime'] <= 0 or drop['y'] > HEIGHT:
                self.rain_drops.remove(drop)
                
    def draw(self, screen):
        # Draw rain
        for drop in self.rain_drops:
            pygame.draw.line(screen, (150, 150, 255), 
                           (drop['x'], drop['y']), 
                           (drop['x'], drop['y'] + 10), 2)
            
        # Draw wind zones
        for zone in self.wind_zones:
            alpha = zone['lifetime'] / 300
            color = (int(100 * alpha), int(100 * alpha), int(255 * alpha))
            pygame.draw.circle(screen, color, (int(zone['x']), int(zone['y'])), zone['radius'], 3)
            
        # Draw storm fronts
        for front in self.storm_fronts:
            pygame.draw.rect(screen, (120, 120, 255), 
                           (front['x'], front['y'] - front['height']//2, front['width'], front['height']))
            
        # Draw lightning bolts
        for bolt in self.lightning_bolts:
            if isinstance(bolt, Projectile):
                bolt.draw(screen)
                if hasattr(bolt, 'target_x') and bolt.target_x is not None and hasattr(bolt, 'target_y') and bolt.target_y is not None:
                    pygame.draw.line(screen, (255, 255, 100),
                                   (bolt.x, bolt.y),
                                   (bolt.target_x, bolt.target_y), 3)
            elif isinstance(bolt, dict) and bolt.get('line_strike'):
                pygame.draw.line(screen, (255, 255, 100), (bolt['x'], 0), (bolt['x'], HEIGHT), 4)
                               
        # Draw lightning network
        for lightning in self.lightning_network:
            lightning.draw(screen)
            if hasattr(lightning, 'chain_end_x') and lightning.chain_end_x is not None and hasattr(lightning, 'chain_end_y') and lightning.chain_end_y is not None:
                pygame.draw.line(screen, (200, 200, 255),
                               (lightning.x, lightning.y),
                               (lightning.chain_end_x, lightning.chain_end_y), 2)
                               
        # Draw main boss using sprite or fallback
        if hasattr(self, 'use_sprite') and self.use_sprite:
            # Draw the Tempest Lord sprite
            self.draw_sprite_to_hitbox(screen)
        else:
            # Fallback to default boss drawing
            Boss.draw(self, screen)

        for effect in self.effects:
            effect.draw(screen)
        
        # Draw storm aura
        aura_radius = 80 + self.phase * 20
        aura_alpha = 0.2 + 0.1 * math.sin(pygame.time.get_ticks() * 0.01)
        aura_color = tuple(int(c * aura_alpha) for c in (100, 100, 255))
        pygame.draw.circle(screen, aura_color, 
                         (self.x + self.width // 2, self.y + self.height // 2), 
                         aura_radius, 4)
                         
        # Use the base health bar drawing with custom color
        self.health_bar_color = (100, 100, 255)
        self.draw_health_bar(screen)

    def _segment_hits_player(self, lightning):
        if not (hasattr(lightning, 'chain_end_x') and hasattr(lightning, 'chain_end_y')):
            return False
        player = self.game.player
        points = [
            (player.x, player.y),
            (player.x + player.width, player.y),
            (player.x, player.y + player.height),
            (player.x + player.width, player.y + player.height),
            (player.x + player.width // 2, player.y + player.height // 2),
        ]
        start = (lightning.x, lightning.y)
        end = (lightning.chain_end_x, lightning.chain_end_y)
        threshold = getattr(lightning, 'segment_width', 18)
        return any(self._point_to_segment_distance(px, py, start, end) <= threshold for px, py in points)

    @staticmethod
    def _point_to_segment_distance(px, py, start, end):
        x1, y1 = start
        x2, y2 = end
        dx = x2 - x1
        dy = y2 - y1
        if dx == 0 and dy == 0:
            return math.sqrt((px - x1) ** 2 + (py - y1) ** 2)
        t = ((px - x1) * dx + (py - y1) * dy) / float(dx * dx + dy * dy)
        t = max(0.0, min(1.0, t))
        cx = x1 + t * dx
        cy = y1 + t * dy
        return math.sqrt((px - cx) ** 2 + (py - cy) ** 2)


