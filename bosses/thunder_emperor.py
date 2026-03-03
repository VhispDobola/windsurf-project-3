import pygame
import math
import random
from core.boss import Boss
from core.effect import Telegraph
from config.constants import WIDTH, HEIGHT, BLUE, CYAN, YELLOW, WHITE, PURPLE
from utils import load_image_with_transparency

class ThunderEmperor(Boss):
    def __init__(self):
        super().__init__(WIDTH // 2 - 60, 100, 120, 120, 750, "Thunder Emperor")
        self.color = (0, 50, 100)
        self.lightning_strikes = []
        self.electric_fields = []
        self.storm_timer = 0
        self.chain_lightning_timer = 0
        self.thunder_clouds = []
        self.aura_particles = []
        self.electric_aura = False
        self.thunder_charge = 0
        self.safe_lane_angle = 0
        self.safe_lane_timer = 0
        
        # Load the Thunder Emperor sprite
        try:
            self.sprite = load_image_with_transparency("assets", "sprites", "thunder_emperor.png", transparent_color=(0, 0, 0))
            # Scale sprite to fit the boss dimensions
            self.sprite = pygame.transform.scale(self.sprite, (self.width, self.height))
            self.use_sprite = True
            self.logger.info("Thunder Emperor sprite loaded successfully")
        except Exception as e:
            # Fallback to drawn version if sprite not found
            self.use_sprite = False
            self.logger.warning("Thunder Emperor sprite not found - %s", e)
        
    def run_attacks(self):
        self.storm_timer -= 1
        self.chain_lightning_timer -= 1
        self.thunder_charge -= 1
        self.safe_lane_timer -= 1
        
        if self.phase == 1:
            if self.storm_timer <= 0:
                self.create_lightning_storm()
                self.storm_timer = 150
            if self.chain_lightning_timer <= 0:
                self.create_electric_field()
                self.chain_lightning_timer = 200
                
        elif self.phase == 2:
            if self.storm_timer <= 0:
                self.create_chain_lightning()
                self.storm_timer = 120
            if self.chain_lightning_timer <= 0:
                self.create_thunder_cloud()
                self.chain_lightning_timer = 180
            self.electric_aura = True
                
        else:  # phase 3
            if self.storm_timer <= 0:
                self.create_super_storm()
                self.storm_timer = 90
            if self.chain_lightning_timer <= 0:
                self.create_lightning_matrix()
                self.chain_lightning_timer = 150
            self.electric_aura = True
            if self.thunder_charge <= 0:
                self.create_thunder_charge()
                self.thunder_charge = 60
            if self.safe_lane_timer <= 0:
                self.create_safe_lane_storm()
                self.safe_lane_timer = 180
                
        self.movement()
        self.update_storm_effects()
        self.update_aura_particles()
        
    def create_lightning_storm(self):
        # Create multiple lightning strikes
        for i in range(3):
            strike_x = random.randint(100, WIDTH - 100)
            strike_y = random.randint(150, HEIGHT - 100)
            
            self.lightning_strikes.append({
                'x': strike_x, 'y': strike_y,
                'width': 30, 'height': 150,
                'lifetime': 30, 'damage': 20,
                'charging': True, 'charge_time': 20
            })
            self.effects.append(Telegraph(strike_x, strike_y, 30, 150, CYAN))
            
    def create_chain_lightning(self):
        # Create lightning that jumps between points
        start_x = random.randint(100, WIDTH - 100)
        start_y = 100
        
        points = [(start_x, start_y)]
        for i in range(4):
            last_x, last_y = points[-1]
            new_x = last_x + random.randint(-100, 100)
            new_y = last_y + random.randint(80, 120)
            new_x = max(50, min(WIDTH - 50, new_x))
            new_y = max(150, min(HEIGHT - 50, new_y))
            points.append((new_x, new_y))
            
        self.lightning_strikes.append({
            'points': points,
            'lifetime': 40, 'damage': 25,
            'type': 'chain'
        })
        
        # Create telegraph effects for each point
        for x, y in points:
            self.effects.append(Telegraph(x, y, 20, 20, YELLOW))
            
    def create_super_storm(self):
        # Massive lightning storm covering large area
        center_x = self.x + self.width // 2
        center_y = self.y + self.height // 2
        
        for angle in range(0, 360, 30):
            rad = math.radians(angle)
            distance = random.randint(80, 200)
            strike_x = center_x + math.cos(rad) * distance
            strike_y = center_y + math.sin(rad) * distance
            
            self.lightning_strikes.append({
                'x': strike_x, 'y': strike_y,
                'width': 40, 'height': 200,
                'lifetime': 25, 'damage': 35,
                'charging': True, 'charge_time': 15
            })
            
        self.effects.append(Telegraph(center_x, center_y, 250, 250, CYAN))
        
    def create_electric_field(self):
        # Create persistent electric damage area
        field_x = random.randint(100, WIDTH - 200)
        field_y = random.randint(150, HEIGHT - 150)
        
        self.electric_fields.append({
            'x': field_x, 'y': field_y,
            'radius': 60, 'lifetime': 300,
            'damage': 15, 'pulse_timer': 0
        })
        self.effects.append(Telegraph(field_x, field_y, 60, 60, BLUE))
        
    def create_thunder_cloud(self):
        # Create moving storm cloud
        cloud_x = random.randint(50, WIDTH - 150)
        cloud_y = random.randint(50, 150)
        
        self.thunder_clouds.append({
            'x': cloud_x, 'y': cloud_y,
            'width': 100, 'height': 40,
            'lifetime': 400, 'strike_timer': 60,
            'move_x': random.choice([-1, 1]), 'move_y': 0.5
        })
        
    def create_lightning_matrix(self):
        # Create grid of lightning strikes
        grid_size = 3
        start_x = WIDTH // 2 - (grid_size - 1) * 60
        start_y = HEIGHT // 2 - (grid_size - 1) * 60
        
        for i in range(grid_size):
            for j in range(grid_size):
                x = start_x + i * 120
                y = start_y + j * 120
                
                self.lightning_strikes.append({
                    'x': x, 'y': y,
                    'width': 25, 'height': 100,
                    'lifetime': 35, 'damage': 30,
                    'charging': True, 'charge_time': 25
                })
                
        self.effects.append(Telegraph(WIDTH // 2, HEIGHT // 2, 200, 200, YELLOW))

    def create_safe_lane_storm(self):
        # Rotating storm with a safe lane
        self.safe_lane_angle = random.uniform(0, math.pi * 2)
        center_x = WIDTH // 2
        center_y = HEIGHT // 2
        for i in range(16):
            angle = (math.pi * 2 * i) / 16
            if abs((angle - self.safe_lane_angle + math.pi) % (math.pi * 2) - math.pi) < 0.3:
                continue
            strike_x = center_x + math.cos(angle) * 180
            strike_y = center_y + math.sin(angle) * 120
            self.lightning_strikes.append({
                'x': strike_x, 'y': strike_y,
                'width': 30, 'height': 160,
                'lifetime': 40, 'damage': 28,
                'charging': True, 'charge_time': 25
            })
        self.effects.append(Telegraph(center_x, center_y, 240, 240, CYAN))
        
    def movement(self):
        # Erratic movement like storm
        self.x += math.sin(pygame.time.get_ticks() * 0.0008) * 3
        self.y += math.cos(pygame.time.get_ticks() * 0.0006) * 2
        
        if random.random() < 0.01:
            self.x += random.randint(-50, 50)
            self.y += random.randint(-30, 30)
            
        self.x = max(50, min(WIDTH - 170, self.x))
        self.y = max(50, min(HEIGHT - 220, self.y))
        self.update_rect()
        
    def update_storm_effects(self):
        if not self.game:
            return
            
        # Update lightning strikes
        for strike in self.lightning_strikes[:]:
            strike['lifetime'] -= 1
            if strike['lifetime'] <= 0:
                self.lightning_strikes.remove(strike)
            else:
                if strike.get('charging'):
                    strike['charge_time'] -= 1
                    if strike['charge_time'] <= 0:
                        strike['charging'] = False
                        
                if not strike.get('charging'):
                    # Check damage
                    if strike.get('type') == 'chain':
                        # Chain lightning damage along points
                        for i, (x, y) in enumerate(strike['points']):
                            player_rect = self.game.player.get_rect()
                            strike_rect = pygame.Rect(x - 15, y - 15, 30, 30)
                            if strike_rect.colliderect(player_rect):
                                    cooldown_key = f'damage_cooldown_{i}'
                                    if cooldown_key not in strike or strike[cooldown_key] <= 0:
                                        self.game.player.take_damage(strike['damage'])
                                        strike[cooldown_key] = 20
                                    else:
                                        strike[cooldown_key] -= 1
                    else:
                        # Regular lightning strike
                        player_rect = self.game.player.get_rect()
                        strike_rect = pygame.Rect(strike['x'] - strike['width']//2, 
                                                 strike['y'] - strike['height']//2,
                                                 strike['width'], strike['height'])
                        if strike_rect.colliderect(player_rect):
                            if 'damage_cooldown' not in strike or strike['damage_cooldown'] <= 0:
                                self.game.player.take_damage(strike['damage'])
                                strike['damage_cooldown'] = 25
                            else:
                                strike['damage_cooldown'] -= 1

        # Rotate safe lane slowly for readability
        if self.safe_lane_timer > 0:
            self.safe_lane_angle += 0.01
                                
        # Update electric fields
        for field in self.electric_fields[:]:
            field['lifetime'] -= 1
            field['pulse_timer'] -= 1
            
            if field['lifetime'] <= 0:
                self.electric_fields.remove(field)
            else:
                if field['pulse_timer'] <= 0:
                    field['pulse_timer'] = 30
                    
                # Check player in field
                player_rect = self.game.player.get_rect()
                field_rect = pygame.Rect(field['x'] - field['radius'], 
                                        field['y'] - field['radius'],
                                        field['radius'] * 2, field['radius'] * 2)
                
                if field_rect.colliderect(player_rect):
                    if field['pulse_timer'] == 30:  # Damage on pulse
                        self.game.player.take_damage(field['damage'])
                        
        # Update thunder clouds
        for cloud in self.thunder_clouds[:]:
            cloud['lifetime'] -= 1
            cloud['strike_timer'] -= 1
            
            if cloud['lifetime'] <= 0:
                self.thunder_clouds.remove(cloud)
            else:
                # Move cloud
                cloud['x'] += cloud['move_x']
                cloud['y'] += cloud['move_y']
                
                # Bounce off walls
                if cloud['x'] <= 50 or cloud['x'] >= WIDTH - 150:
                    cloud['move_x'] *= -1
                    
                # Create lightning from cloud
                if cloud['strike_timer'] <= 0:
                    strike_x = cloud['x'] + cloud['width'] // 2 + random.randint(-30, 30)
                    strike_y = cloud['y'] + cloud['height']
                    
                    self.lightning_strikes.append({
                        'x': strike_x, 'y': strike_y,
                        'width': 20, 'height': 120,
                        'lifetime': 20, 'damage': 18,
                        'charging': False
                    })
                    cloud['strike_timer'] = 40
                    
    def draw(self, screen):
        # Draw electric fields
        for field in self.electric_fields:
            alpha = field['lifetime'] / 300
            pulse_alpha = 1.0 if field['pulse_timer'] > 20 else 0.5
            
            color = tuple(int(c * alpha * pulse_alpha) for c in (0, 150, 255))
            pygame.draw.circle(screen, color, (field['x'], field['y']), field['radius'], 3)
            
            # Draw electric sparks
            for i in range(8):
                angle = (math.pi * 2 * i) / 8 + pygame.time.get_ticks() * 0.01
                spark_x = field['x'] + math.cos(angle) * field['radius']
                spark_y = field['y'] + math.sin(angle) * field['radius']
                pygame.draw.circle(screen, CYAN, (int(spark_x), int(spark_y)), 2)
                
        # Draw thunder clouds
        for cloud in self.thunder_clouds:
            alpha = cloud['lifetime'] / 400
            color = tuple(int(c * alpha) for c in (50, 50, 100))
            pygame.draw.ellipse(screen, color, 
                              (cloud['x'], cloud['y'], cloud['width'], cloud['height']))
            
        # Draw lightning strikes
        for strike in self.lightning_strikes:
            if strike.get('type') == 'chain':
                # Draw chain lightning
                for i in range(len(strike['points']) - 1):
                    start = strike['points'][i]
                    end = strike['points'][i + 1]
                    
                    if strike.get('charging'):
                        color = (100, 100, 255)
                        width = 2
                    else:
                        color = WHITE
                        width = 4
                        
                    pygame.draw.line(screen, color, start, end, width)
                    
                    # Draw branches
                    if not strike.get('charging'):
                        mid_x = (start[0] + end[0]) // 2
                        mid_y = (start[1] + end[1]) // 2
                        branch_x = mid_x + random.randint(-20, 20)
                        branch_y = mid_y + random.randint(-20, 20)
                        pygame.draw.line(screen, CYAN, (mid_x, mid_y), (branch_x, branch_y), 2)
            else:
                # Draw regular lightning
                if strike.get('charging'):
                    color = (100, 100, 255)
                    width = 3
                else:
                    color = WHITE
                    width = 6
                    
                # Main bolt
                pygame.draw.line(screen, color,
                               (strike['x'], strike['y']),
                               (strike['x'], strike['y'] + strike['height']), width)
                
                # Lightning branches
                if not strike.get('charging'):
                    for i in range(3):
                        branch_y = strike['y'] + (i + 1) * strike['height'] // 4
                        branch_x = strike['x'] + random.randint(-20, 20)
                        pygame.draw.line(screen, CYAN,
                                       (strike['x'], branch_y),
                                       (branch_x, branch_y + random.randint(10, 30)), 2)

        # Draw safe lane indicator
        if self.safe_lane_timer > 0:
            center_x = WIDTH // 2
            center_y = HEIGHT // 2
            lane_x = center_x + math.cos(self.safe_lane_angle) * 200
            lane_y = center_y + math.sin(self.safe_lane_angle) * 130
            pygame.draw.line(screen, (100, 255, 255), (center_x, center_y), (lane_x, lane_y), 4)
                                       
        # Draw electric aura
        if self.electric_aura:
            aura_radius = 80 + 20 * math.sin(pygame.time.get_ticks() * 0.005)
            for i in range(8):
                angle = (math.pi * 2 * i) / 8
                x = self.x + self.width // 2 + math.cos(angle) * aura_radius
                y = self.y + self.height // 2 + math.sin(angle) * aura_radius
                alpha = 100 + 50 * math.sin(pygame.time.get_ticks() * 0.01 + i)
                color = (*CYAN[:3], alpha)
                pygame.draw.circle(screen, color, (int(x), int(y)), 4)
        
        # Draw aura particles
        for particle in self.aura_particles:
            alpha = particle['lifetime'] / 60
            color = (*particle['color'][:3], int(alpha * 255))
            pygame.draw.circle(screen, color, (int(particle['x']), int(particle['y'])), particle['size'])
        
        # Draw main boss
        if hasattr(self, 'use_sprite') and self.use_sprite:
            # Draw the Thunder Emperor sprite
            self.draw_sprite_to_hitbox(screen)
        else:
            # Fallback to default boss drawing
            Boss.draw(self, screen)
        
    def update_aura_particles(self):
        # Create electric aura particles
        if self.electric_aura and random.random() < 0.3:
            self.aura_particles.append({
                'x': self.x + self.width // 2 + random.randint(-60, 60),
                'y': self.y + self.height // 2 + random.randint(-60, 60),
                'vx': random.uniform(-2, 2),
                'vy': random.uniform(-2, 2),
                'lifetime': 60,
                'size': random.randint(2, 4),
                'color': random.choice([CYAN, YELLOW, WHITE])
            })
        
        # Update particles
        for particle in self.aura_particles[:]:
            particle['lifetime'] -= 1
            particle['x'] += particle['vx']
            particle['y'] += particle['vy']
            
            if particle['lifetime'] <= 0:
                self.aura_particles.remove(particle)
    
    def create_thunder_charge(self):
        # Create charging effect before big attack
        for i in range(12):
            angle = (math.pi * 2 * i) / 12
            dist = 100 + random.randint(-20, 20)
            x = self.x + self.width // 2 + math.cos(angle) * dist
            y = self.y + self.height // 2 + math.sin(angle) * dist
            
            self.lightning_strikes.append({
                'x': x, 'y': y,
                'width': 15, 'height': 40,
                'lifetime': 30, 'damage': 25,
                'charging': True,
                'type': 'charge',
                'charge_time': 30
            })
        
        # Add telegraph for big attack
        self.effects.append(Telegraph(self.x + self.width // 2, self.y + self.height // 2, 150, 150, PURPLE))


