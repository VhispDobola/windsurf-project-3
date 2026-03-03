import pygame
import math
import random
from core.boss import Boss
from core.effect import Telegraph
from config.constants import WIDTH, HEIGHT, BLUE, CYAN, WHITE, GREEN
from utils import load_image_with_transparency

class IceTyrant(Boss):
    def __init__(self):
        super().__init__(WIDTH // 2 - 65, 100, 130, 130, 720, "Ice Tyrant")
        self.color = (100, 150, 200)
        self.ice_zones = []
        self.frost_waves = []
        self.blizzard_timer = 0
        self.ice_spire_timer = 0
        self.freezing_aura = False
        self.slow_zones = []
        self.ice_wall_timer = 0
        self.shatter_timer = 0
        self.shatter_active = False
        self.ice_walls = []

        try:
            self.sprite = load_image_with_transparency("assets", "sprites", "ice_tyrant.png", transparent_color=(0, 0, 0))
            self.sprite = pygame.transform.scale(self.sprite, (self.width, self.height))
            self.use_sprite = True
        except Exception:
            self.use_sprite = False
        
    def run_attacks(self):
        self.blizzard_timer -= 1
        self.ice_spire_timer -= 1
        self.ice_wall_timer -= 1
        self.shatter_timer -= 1
        if self.shatter_active and self.shatter_timer <= 0:
            self.shatter_active = False
        
        if self.phase == 1:
            if self.blizzard_timer <= 0:
                self.create_frost_wave()
                self.blizzard_timer = 160
            if self.ice_spire_timer <= 0:
                self.create_ice_zone()
                self.ice_spire_timer = 200
            if self.ice_wall_timer <= 0:
                self.create_ice_wall_sweep()
                self.ice_wall_timer = 220
                
        elif self.phase == 2:
            if self.blizzard_timer <= 0:
                self.create_blizzard()
                self.blizzard_timer = 130
            if self.ice_spire_timer <= 0:
                self.create_ice_spikes()
                self.ice_spire_timer = 170
            if self.ice_wall_timer <= 0:
                self.create_ice_wall_sweep(stronger=True)
                self.ice_wall_timer = 180
            if self.shatter_timer <= 0:
                self.trigger_shatter()
                self.shatter_timer = 240
            self.freezing_aura = True
            
        else:  # phase 3
            if self.blizzard_timer <= 0:
                self.create_absolute_zero()
                self.blizzard_timer = 100
            if self.ice_spire_timer <= 0:
                self.create_ice_prison()
                self.ice_spire_timer = 140
            if self.ice_wall_timer <= 0:
                self.create_ice_wall_sweep(stronger=True)
                self.ice_wall_timer = 140
            if self.shatter_timer <= 0:
                self.trigger_shatter(duration=120)
                self.shatter_timer = 200
            self.freezing_aura = True
            
        self.movement()
        self.update_frost_effects()
        
    def create_frost_wave(self):
        # Create expanding wave of ice
        wave_x = random.randint(150, WIDTH - 150)
        wave_y = random.randint(200, HEIGHT - 100)
        
        self.frost_waves.append({
            'x': wave_x, 'y': wave_y,
            'radius': 10, 'max_radius': 100,
            'expanding': True, 'damage': 18,
            'lifetime': 120, 'slow_effect': 0.5
        })
        self.effects.append(Telegraph(wave_x, wave_y, 100, 100, CYAN))
        
    def create_blizzard(self):
        # Create multiple frost waves
        for i in range(3):
            wave_x = WIDTH // 2 + (i - 1) * 120
            wave_y = random.randint(150, HEIGHT - 150)
            
            self.frost_waves.append({
                'x': wave_x, 'y': wave_y,
                'radius': 15, 'max_radius': 80,
                'expanding': True, 'damage': 22,
                'lifetime': 100, 'slow_effect': 0.4
            })
            
        self.effects.append(Telegraph(WIDTH // 2, HEIGHT // 2, 150, 150, BLUE))
        
    def create_absolute_zero(self):
        # Massive freezing wave from boss
        wave_x = self.x + self.width // 2
        wave_y = self.y + self.height // 2
        
        self.frost_waves.append({
            'x': wave_x, 'y': wave_y,
            'radius': 20, 'max_radius': 150,
            'expanding': True, 'damage': 35,
            'lifetime': 90, 'slow_effect': 0.2
        })
        self.effects.append(Telegraph(wave_x, wave_y, 150, 150, WHITE))
        
    def create_ice_zone(self):
        # Create persistent ice area
        zone_x = random.randint(100, WIDTH - 150)
        zone_y = random.randint(150, HEIGHT - 150)
        
        self.ice_zones.append({
            'x': zone_x, 'y': zone_y,
            'radius': 50, 'lifetime': 350,
            'damage': 12, 'slow_amount': 0.6
        })
        self.effects.append(Telegraph(zone_x, zone_y, 50, 50, BLUE))
        
    def create_ice_spikes(self):
        # Create multiple ice zones in pattern
        center_x = random.randint(150, WIDTH - 150)
        center_y = random.randint(150, HEIGHT - 150)
        
        for angle in range(0, 360, 60):
            rad = math.radians(angle)
            spike_x = center_x + math.cos(rad) * 70
            spike_y = center_y + math.sin(rad) * 70
            
            self.ice_zones.append({
                'x': spike_x, 'y': spike_y,
                'radius': 35, 'lifetime': 280,
                'damage': 15, 'slow_amount': 0.5
            })
            
        self.effects.append(Telegraph(center_x, center_y, 120, 120, CYAN))
        
    def create_ice_prison(self):
        # Create grid of ice zones
        for i in range(2):
            for j in range(2):
                x = WIDTH // 2 + (i - 0.5) * 150
                y = HEIGHT // 2 + (j - 0.5) * 150
                
                self.ice_zones.append({
                    'x': x, 'y': y,
                    'radius': 60, 'lifetime': 250,
                    'damage': 20, 'slow_amount': 0.3
                })
                
        self.effects.append(Telegraph(WIDTH // 2, HEIGHT // 2, 200, 200, WHITE))
        
    def create_ice_wall_sweep(self, stronger=False):
        # Sweeping ice wall with a safe gap
        gap_y = random.randint(120, HEIGHT - 120)
        direction = random.choice([-1, 1])
        wall = {
            'x': 0 if direction > 0 else WIDTH,
            'y': HEIGHT // 2,
            'width': 30,
            'height': HEIGHT - 100,
            'vy': 0,
            'vx': 6 if stronger else 4,
            'gap_y': gap_y,
            'gap_h': 120 if stronger else 150,
            'damage': 18 if stronger else 12,
            'lifetime': 160
        }
        self.ice_walls.append(wall)
        self.effects.append(Telegraph(WIDTH // 2, gap_y, 50, 160, BLUE))
        
    def trigger_shatter(self, duration=90):
        # Temporarily remove slows; boss becomes more aggressive
        self.shatter_active = True
        self.shatter_timer = duration
        if self.game:
            self.game.screen_shake.start(3, 12)
        
    def create_slow_zone(self):
        # Create zone that only slows, no damage
        zone_x = random.randint(100, WIDTH - 150)
        zone_y = random.randint(150, HEIGHT - 150)
        
        self.slow_zones.append({
            'x': zone_x, 'y': zone_y,
            'radius': 70, 'lifetime': 400,
            'slow_amount': 0.3
        })
        
    def movement(self):
        # Slow, graceful floating movement
        self.x += math.sin(pygame.time.get_ticks() * 0.0004) * 1.5
        self.y += math.cos(pygame.time.get_ticks() * 0.0003) * 1
        
        self.x = max(50, min(WIDTH - 180, self.x))
        self.y = max(50, min(HEIGHT - 230, self.y))
        self.update_rect()
        
    def update_frost_effects(self):
        if not self.game:
            return
            
        # Update frost waves (expanding circles)
        for wave in self.frost_waves[:]:
            wave['lifetime'] -= 1
            if wave['lifetime'] <= 0:
                self.frost_waves.remove(wave)
            else:
                if wave['expanding'] and wave['radius'] < wave['max_radius']:
                    wave['radius'] += 2
                    
                # Check player collision
                player_rect = self.game.player.get_rect()
                wave_rect = pygame.Rect(wave['x'] - wave['radius'], 
                                       wave['y'] - wave['radius'],
                                       wave['radius'] * 2, wave['radius'] * 2)
                
                if wave_rect.colliderect(player_rect):
                    # Apply slow effect
                    self.game.player.add_speed_modifier(wave['slow_effect'], 30)
                    
                    # Apply damage
                    if not hasattr(wave, 'damage_cooldown') or wave['damage_cooldown'] <= 0:
                        self.game.player.take_damage(wave['damage'])
                        wave['damage_cooldown'] = 40
                    else:
                        wave['damage_cooldown'] -= 1
                        
        # Update ice zones (persistent areas)
        for zone in self.ice_zones[:]:
            zone['lifetime'] -= 1
            if zone['lifetime'] <= 0:
                self.ice_zones.remove(zone)
            else:
                if not self.shatter_active:
                    # Check player in zone
                    player_rect = self.game.player.get_rect()
                    zone_rect = pygame.Rect(zone['x'] - zone['radius'], 
                                           zone['y'] - zone['radius'],
                                           zone['radius'] * 2, zone['radius'] * 2)
                    
                    if zone_rect.colliderect(player_rect):
                        # Apply continuous slow
                        self.game.player.add_speed_modifier(zone['slow_amount'], 20)
                        
                        # Apply damage over time
                        if not hasattr(zone, 'damage_cooldown') or zone['damage_cooldown'] <= 0:
                            self.game.player.take_damage(zone['damage'])
                            zone['damage_cooldown'] = 60
                        else:
                            zone['damage_cooldown'] -= 1
                        
        # Update slow zones
        for zone in self.slow_zones[:]:
            zone['lifetime'] -= 1
            if zone['lifetime'] <= 0:
                self.slow_zones.remove(zone)
            else:
                if not self.shatter_active:
                    # Check player in zone
                    player_rect = self.game.player.get_rect()
                    zone_rect = pygame.Rect(zone['x'] - zone['radius'], 
                                           zone['y'] - zone['radius'],
                                           zone['radius'] * 2, zone['radius'] * 2)
                    
                    if zone_rect.colliderect(player_rect):
                        self.game.player.add_speed_modifier(zone['slow_amount'], 25)
                    
        # Freezing aura
        if self.freezing_aura and self.game:
            player_rect = self.game.player.get_rect()
            boss_rect = self.get_rect()
            if boss_rect.inflate(80, 80).colliderect(player_rect):
                self.game.player.add_speed_modifier(0.7, 15)
                if not hasattr(self, 'aura_damage_cooldown') or self.aura_damage_cooldown <= 0:
                    self.game.player.take_damage(8)
                    self.aura_damage_cooldown = 45
                else:
                    self.aura_damage_cooldown -= 1
                    
        # Update ice walls
        for wall in self.ice_walls[:]:
            wall['lifetime'] -= 1
            if wall['lifetime'] <= 0:
                self.ice_walls.remove(wall)
            else:
                wall['x'] += wall['vx']
                if self.game and self.game.player:
                    # Collision with wall except for the gap
                    player_rect = self.game.player.get_rect()
                    gap_rect = pygame.Rect(wall['x'] - 5, wall['gap_y'] - wall['gap_h']//2, wall['width'] + 10, wall['gap_h'])
                    wall_rect = pygame.Rect(wall['x'], wall['y'] - wall['height']//2, wall['width'], wall['height'])
                    if wall_rect.colliderect(player_rect) and not gap_rect.colliderect(player_rect):
                        if not wall.get('damage_cooldown') or wall['damage_cooldown'] <= 0:
                            self.game.player.take_damage(wall['damage'])
                            wall['damage_cooldown'] = 30
                        else:
                            wall['damage_cooldown'] -= 1
                    
    def draw(self, screen):
        # Draw slow zones
        for zone in self.slow_zones:
            alpha = zone['lifetime'] / 400
            color = tuple(int(c * alpha) for c in (150, 200, 255))
            pygame.draw.circle(screen, color, (zone['x'], zone['y']), zone['radius'], 2)
            
            # Draw snowflakes
            for i in range(6):
                angle = (math.pi * 2 * i) / 6 + pygame.time.get_ticks() * 0.005
                flake_x = zone['x'] + math.cos(angle) * zone['radius'] * 0.7
                flake_y = zone['y'] + math.sin(angle) * zone['radius'] * 0.7
                pygame.draw.circle(screen, WHITE, (int(flake_x), int(flake_y)), 3)
                
        # Draw ice zones
        for zone in self.ice_zones:
            alpha = zone['lifetime'] / 350
            
            # Draw ice circle
            color = tuple(int(c * alpha) for c in (100, 150, 255))
            pygame.draw.circle(screen, color, (zone['x'], zone['y']), zone['radius'])
            pygame.draw.circle(screen, CYAN, (zone['x'], zone['y']), zone['radius'], 4)
            
            # Draw ice crystals
            for i in range(8):
                angle = (math.pi * 2 * i) / 8
                crystal_x = zone['x'] + math.cos(angle) * zone['radius'] * 0.8
                crystal_y = zone['y'] + math.sin(angle) * zone['radius'] * 0.8
                
                # Draw 6-pointed snowflake
                for j in range(6):
                    flake_angle = angle + (math.pi * 2 * j) / 6
                    end_x = crystal_x + math.cos(flake_angle) * 8
                    end_y = crystal_y + math.sin(flake_angle) * 8
                pygame.draw.line(screen, WHITE, (crystal_x, crystal_y), (end_x, end_y), 2)
                
        # Draw ice walls
        for wall in self.ice_walls:
            pygame.draw.rect(screen, (80, 140, 220), 
                           (wall['x'], wall['y'] - wall['height']//2, wall['width'], wall['height']))
            # Draw safe gap outline
            pygame.draw.rect(screen, WHITE, 
                           (wall['x'] - 2, wall['gap_y'] - wall['gap_h']//2, wall['width'] + 4, wall['gap_h']), 2)
                    
        # Draw frost waves
        for wave in self.frost_waves:
            alpha = wave['lifetime'] / 120
            color = tuple(int(c * alpha) for c in (200, 220, 255))
            
            # Draw expanding ring
            pygame.draw.circle(screen, color, (wave['x'], wave['y']), wave['radius'], 5)
            
            # Draw ice particles
            for i in range(12):
                angle = (math.pi * 2 * i) / 12 + pygame.time.get_ticks() * 0.01
                particle_x = wave['x'] + math.cos(angle) * wave['radius']
                particle_y = wave['y'] + math.sin(angle) * wave['radius']
                pygame.draw.circle(screen, WHITE, (int(particle_x), int(particle_y)), 2)
                
        # Draw freezing aura
        if self.freezing_aura:
            aura_radius = 90 + 15 * math.sin(pygame.time.get_ticks() * 0.008)
            aura_alpha = 0.15
            aura_color = tuple(int(c * aura_alpha) for c in (150, 200, 255))
            pygame.draw.circle(screen, aura_color, 
                             (self.x + self.width // 2, self.y + self.height // 2), 
                             int(aura_radius))
            
            # Draw floating snowflakes around boss
            for i in range(6):
                angle = (math.pi * 2 * i) / 6 + pygame.time.get_ticks() * 0.003
                flake_x = self.x + self.width // 2 + math.cos(angle) * 60
                flake_y = self.y + self.height // 2 + math.sin(angle) * 60
                pygame.draw.circle(screen, WHITE, (int(flake_x), int(flake_y)), 4)
                
        if self.shatter_active:
            font = pygame.font.Font(None, 28)
            text = font.render("SHATTER!", True, WHITE)
            screen.blit(text, (WIDTH // 2 - 50, 60))
                
        # Draw main boss body
        if hasattr(self, "use_sprite") and self.use_sprite:
            self.draw_sprite_to_hitbox(screen)
        else:
            pygame.draw.rect(screen, self.color, self.get_rect())

        # Draw telegraphs/effects and health bar.
        for effect in self.effects:
            effect.draw(screen)
        self.draw_health_bar(screen)


