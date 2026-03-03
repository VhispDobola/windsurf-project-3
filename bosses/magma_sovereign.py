import pygame
import math
import random
from core.boss import Boss
from core.effect import Telegraph
from core.entity import DamageType
from core.movement_system import BossMovementController, SineWaveMovement, CircularMovement
from config.constants import WIDTH, HEIGHT, RED, ORANGE, YELLOW, WHITE
from utils import load_image_with_transparency

class MagmaSovereign(Boss):
    def __init__(self):
        super().__init__(WIDTH // 2 - 75, 100, 150, 150, 800, "Magma Sovereign")
        self.color = (139, 69, 19)
        self.lava_pools = []
        self.eruption_timer = 0
        self.lava_wave_timer = 0
        self.molten_ground = []
        self.heat_aura = False
        
        # New attack timers
        # Staggered startup so phase 1 doesn't front-load every attack at once.
        self.magma_bomb_timer = 90
        self.geyser_timer = 140
        self.molten_rain_timer = 190
        self.heat_wave_timer = 240
        self.tracking_magma_timer = 0
        self.lava_wall_timer = 0
        self.volcanic_chain_timer = 0
        self.vortex_timer = 0
        self.cascade_timer = 0
        self.tsunami_timer = 0
        self.inferno_timer = 0
        
        # New attack storage
        self.magma_bombs = []
        self.lava_geysers = []
        self.molten_raindrops = []
        self.heat_waves = []
        self.tracking_projectiles = []
        self.lava_walls = []
        self.chain_eruptions = []
        self.vortex_active = False
        self.vortex_center = None
        self.tsunami_wave = None
        self.inferno_mode = False
        
        # Initialize movement system
        self.movement_controller = BossMovementController(self)
        self.movement_controller.add_pattern(SineWaveMovement(self, amplitude_x=40, amplitude_y=25))
        self.movement_controller.add_pattern(CircularMovement(self, radius=60, speed=0.0015))

        try:
            self.sprite = load_image_with_transparency("assets", "sprites", "magma_sovereign.png", transparent_color=(0, 0, 0))
            self.sprite = pygame.transform.scale(self.sprite, (self.width, self.height))
            self.use_sprite = True
        except Exception:
            self.use_sprite = False
        
    def run_attacks(self):
        # Update all timers
        self.eruption_timer = max(0, self.eruption_timer - 1)
        self.lava_wave_timer = max(0, self.lava_wave_timer - 1)
        self.magma_bomb_timer = max(0, self.magma_bomb_timer - 1)
        self.geyser_timer = max(0, self.geyser_timer - 1)
        self.molten_rain_timer = max(0, self.molten_rain_timer - 1)
        self.heat_wave_timer = max(0, self.heat_wave_timer - 1)
        self.tracking_magma_timer = max(0, self.tracking_magma_timer - 1)
        self.lava_wall_timer = max(0, self.lava_wall_timer - 1)
        self.volcanic_chain_timer = max(0, self.volcanic_chain_timer - 1)
        self.vortex_timer = max(0, self.vortex_timer - 1)
        self.cascade_timer = max(0, self.cascade_timer - 1)
        self.tsunami_timer = max(0, self.tsunami_timer - 1)
        self.inferno_timer = max(0, self.inferno_timer - 1)
        
        if self.phase == 1:
            # Phase 1: staggered foundation (one trigger at a time)
            if self.magma_bomb_timer <= 0:
                self.create_magma_bombs()
                self.magma_bomb_timer = 100
            elif self.geyser_timer <= 0:
                self.create_lava_geysers()
                self.geyser_timer = 140
            elif self.molten_rain_timer <= 0:
                self.create_molten_rain()
                self.molten_rain_timer = 175
            elif self.heat_wave_timer <= 0:
                self.create_heat_waves()
                self.heat_wave_timer = 220
                
        elif self.phase == 2:
            # Phase 2: Pressure Tactics
            if self.tracking_magma_timer <= 0:
                self.create_tracking_magma()
                self.tracking_magma_timer = 70
            if self.lava_wall_timer <= 0:
                self.create_lava_walls()
                self.lava_wall_timer = 120
            if self.volcanic_chain_timer <= 0:
                self.create_volcanic_chain()
                self.volcanic_chain_timer = 90
            self.heat_aura = True
            
        else:  # phase 3
            # Phase 3: Ultimate Devastation
            if self.vortex_timer <= 0:
                self.create_magma_vortex()
                self.vortex_timer = 150
            if self.cascade_timer <= 0:
                self.create_cascade_eruptions()
                self.cascade_timer = 180
            if self.tsunami_timer <= 0:
                self.create_lava_tsunami()
                self.tsunami_timer = 200
            if self.inferno_timer <= 0:
                self.activate_final_inferno()
                self.inferno_timer = 300
            self.heat_aura = True
            
        self.movement()
        self.update_all_effects()
        
    def create_lava_eruption(self):
        # Create eruption at random location with better telegraph
        eruption_x = random.randint(100, WIDTH - 100)
        eruption_y = random.randint(200, HEIGHT - 100)
        
        # Add warning telegraph with pulsing effect
        warning = Telegraph(eruption_x, eruption_y, 90, 60, ORANGE, warning_type="pulse")
        warning.active_start = 30  # Danger starts after 30 frames
        self.effects.append(warning)
        
        # Schedule the actual eruption
        self.lava_pools.append({
            'x': eruption_x, 'y': eruption_y,
            'radius': 20, 'max_radius': 60,
            'growing': True, 'damage': 25,
            'lifetime': 300, 'delay': 30  # Start growing after warning
        })
        
    def create_multiple_eruptions(self):
        # Create 3 eruptions in a pattern
        for i in range(3):
            x = WIDTH // 2 + (i - 1) * 150
            y = random.randint(150, HEIGHT - 150)
            
            self.lava_pools.append({
                'x': x, 'y': y,
                'radius': 25, 'max_radius': 70,
                'growing': True, 'damage': 30,
                'lifetime': 240
            })
            self.effects.append(Telegraph(x, y, 70, 70, RED))
            
    def create_volcanic_blast(self):
        # Massive eruption at boss position with extended warning
        blast_x = self.x + self.width // 2
        blast_y = self.y + self.height // 2
        
        # Extended warning for ultimate attack
        warning = Telegraph(blast_x, blast_y, 120, 120, RED, warning_type="pulse")
        warning.active_start = 60  # Danger starts after 1 second
        self.effects.append(warning)
        
        # Schedule the actual blast
        self.lava_pools.append({
            'x': blast_x, 'y': blast_y,
            'radius': 40, 'max_radius': 120,
            'growing': True, 'damage': 40,
            'lifetime': 180, 'delay': 60  # Start growing after warning
        })
        
    def create_lava_pool(self):
        # Create stationary lava pool
        pool_x = random.randint(100, WIDTH - 100)
        pool_y = random.randint(200, HEIGHT - 100)
        
        self.molten_ground.append({
            'x': pool_x, 'y': pool_y,
            'radius': 40, 'damage': 15,
            'lifetime': 400
        })
        
    def create_spreading_lava(self):
        # Create lava that spreads outward
        center_x = random.randint(150, WIDTH - 150)
        center_y = random.randint(150, HEIGHT - 150)
        
        for angle in range(0, 360, 45):
            rad = math.radians(angle)
            x = center_x + math.cos(rad) * 60
            y = center_y + math.sin(rad) * 60
            
            self.molten_ground.append({
                'x': x, 'y': y,
                'radius': 30, 'damage': 20,
                'lifetime': 300
            })
        self.effects.append(Telegraph(center_x, center_y, 100, 100, ORANGE))
        
    def create_lava_flood(self):
        # Fill bottom portion of screen with lava
        for i in range(5):
            x = random.randint(50, WIDTH - 50)
            y = HEIGHT - 100 - random.randint(0, 50)
            
            self.molten_ground.append({
                'x': x, 'y': y,
                'radius': 50, 'damage': 35,
                'lifetime': 250
            })
            
    # === NEW PHASE 1 ATTACKS ===
    
    def create_magma_bombs(self):
        # Fast-moving projectiles that create lingering pools
        if not self.game:
            return
            
        player_x = self.game.player.x + self.game.player.width // 2
        player_y = self.game.player.y + self.game.player.height // 2
        
        for i in range(3):
            angle = math.atan2(player_y - (self.y + self.height // 2), 
                              player_x - (self.x + self.width // 2))
            angle += random.uniform(-0.3, 0.3)  # Add some spread
            
            self.magma_bombs.append({
                'x': self.x + self.width // 2,
                'y': self.y + self.height // 2,
                'vx': math.cos(angle) * 5,
                'vy': math.sin(angle) * 5,
                'radius': 8,
                'damage': 35,
                'lifetime': 120
            })
    
    def create_lava_geysers(self):
        # Quick eruptions with minimal warning
        for i in range(2):
            geyser_x = random.randint(100, WIDTH - 100)
            geyser_y = random.randint(200, HEIGHT - 100)
            
            # Very short warning
            warning = Telegraph(geyser_x, geyser_y, 50, 40, RED, warning_type="flash")
            warning.active_start = 10  # Only 10 frame warning
            self.effects.append(warning)
            
            self.lava_geysers.append({
                'x': geyser_x, 'y': geyser_y,
                'radius': 15, 'max_radius': 45,
                'growing': True, 'damage': 40,
                'lifetime': 180, 'delay': 10
            })
    
    def create_molten_rain(self):
        # Area-wide falling lava drops
        for i in range(8):
            self.molten_raindrops.append({
                'x': random.randint(50, WIDTH - 50),
                'y': -20,
                'vy': random.uniform(3, 6),
                'radius': 6,
                'damage': 25,
                'lifetime': 200
            })
    
    def create_heat_waves(self):
        # Expanding rings of fire from boss position
        boss_center_x = self.x + self.width // 2
        boss_center_y = self.y + self.height // 2
        
        self.heat_waves.append({
            'x': boss_center_x,
            'y': boss_center_y,
            'radius': 20,
            'max_radius': 200,
            'damage': 30,
            'lifetime': 100,
            'expanding': True
        })
    
    # === NEW PHASE 2 ATTACKS ===
    
    def create_tracking_magma(self):
        # Homing projectiles that speed up over time
        if not self.game:
            return
            
        for i in range(2):
            self.tracking_projectiles.append({
                'x': self.x + self.width // 2,
                'y': self.y + self.height // 2,
                'vx': random.uniform(-2, 2),
                'vy': random.uniform(-2, 2),
                'acceleration': 0.08,
                'max_speed': 5,
                'radius': 10,
                'damage': 25,
                'lifetime': 180
            })
    
    def create_lava_walls(self):
        # Create barriers that shrink playable area
        side = random.choice(['left', 'right', 'top'])
        
        if side == 'left':
            wall = {'x': 0, 'y': 100, 'width': 30, 'height': HEIGHT - 200, 'vx': 2}
        elif side == 'right':
            wall = {'x': WIDTH - 30, 'y': 100, 'width': 30, 'height': HEIGHT - 200, 'vx': -2}
        else:  # top
            wall = {'x': 100, 'y': 0, 'width': WIDTH - 200, 'height': 30, 'vy': 2}
            
        wall['damage'] = 50
        wall['lifetime'] = 240
        self.lava_walls.append(wall)
    
    def create_volcanic_chain(self):
        # Eruptions that trigger nearby eruptions
        start_x = random.randint(150, WIDTH - 150)
        start_y = random.randint(150, HEIGHT - 150)
        
        # Initial eruption
        self.chain_eruptions.append({
            'x': start_x, 'y': start_y,
            'radius': 20, 'max_radius': 50,
            'growing': True, 'damage': 35,
            'lifetime': 200, 'delay': 0,
            'chain_count': 0
        })
    
    # === NEW PHASE 3 ATTACKS ===
    
    def create_magma_vortex(self):
        # Pulling player toward center while damaging
        self.vortex_active = True
        self.vortex_center = {
            'x': WIDTH // 2,
            'y': HEIGHT // 2,
            'radius': 150,
            'pull_strength': 3,
            'damage': 15,
            'lifetime': 180
        }
    
    def create_cascade_eruptions(self):
        # Screen-filling chain reaction
        for i in range(5):
            x = (i + 1) * (WIDTH // 6)
            y = random.randint(100, HEIGHT - 100)
            
            self.chain_eruptions.append({
                'x': x, 'y': y,
                'radius': 25, 'max_radius': 80,
                'growing': True, 'damage': 55,
                'lifetime': 250, 'delay': i * 15,
                'chain_count': 0
            })
    
    def create_lava_tsunami(self):
        # Massive wave crossing screen
        side = random.choice(['left', 'right'])
        
        self.tsunami_wave = {
            'x': 0 if side == 'left' else WIDTH,
            'y': HEIGHT - 150,
            'width': 40,
            'height': 100,
            'vx': 4 if side == 'left' else -4,
            'damage': 60,
            'lifetime': 300
        }
    
    def activate_final_inferno(self):
        # Combination of all attack types
        self.inferno_mode = True
        
        # Trigger multiple attacks simultaneously
        self.create_magma_bombs()
        self.create_molten_rain()
        self.create_heat_waves()
        self.create_tracking_magma()
        
        # Add extra lava pools
        for i in range(4):
            x = random.randint(100, WIDTH - 100)
            y = random.randint(200, HEIGHT - 100)
            self.lava_pools.append({
                'x': x, 'y': y,
                'radius': 30, 'max_radius': 70,
                'growing': True, 'damage': 65,
                'lifetime': 200, 'delay': 0
            })
            
    def movement(self):
        # Use new movement system
        dx, dy = self.movement_controller.update()
        self.movement_controller.set_phase(self.phase)
        
        self.x += dx
        self.y += dy
        
        # Keep within bounds
        self.x = max(50, min(WIDTH - 200, self.x))
        self.y = max(50, min(HEIGHT - 250, self.y))
        self.update_rect()
        
    def update_all_effects(self):
        if not self.game:
            return
            
        # Update existing lava effects
        self.update_lava_effects()
        
        # Update magma bombs
        for bomb in self.magma_bombs[:]:
            bomb['lifetime'] -= 1
            if bomb['lifetime'] <= 0:
                self.magma_bombs.remove(bomb)
            else:
                bomb['x'] += bomb['vx']
                bomb['y'] += bomb['vy']
                
                # Check collision with player
                player_rect = self.game.player.get_rect()
                bomb_rect = pygame.Rect(bomb['x'] - bomb['radius'], 
                                       bomb['y'] - bomb['radius'],
                                       bomb['radius'] * 2, bomb['radius'] * 2)
                
                if bomb_rect.colliderect(player_rect):
                    self.game.player.take_damage(bomb['damage'])
                    self.magma_bombs.remove(bomb)
                    # Create lava pool where bomb hit
                    self.lava_pools.append({
                        'x': bomb['x'], 'y': bomb['y'],
                        'radius': 15, 'max_radius': 35,
                        'growing': True, 'damage': 20,
                        'lifetime': 150, 'delay': 0
                    })
        
        # Update lava geysers
        for geyser in self.lava_geysers[:]:
            geyser['lifetime'] -= 1
            if geyser['lifetime'] <= 0:
                self.lava_geysers.remove(geyser)
            else:
                if geyser.get('delay', 0) > 0:
                    geyser['delay'] -= 1
                    continue
                    
                if geyser['growing'] and geyser['radius'] < geyser['max_radius']:
                    geyser['radius'] += 2
                    
                player_rect = self.game.player.get_rect()
                geyser_rect = pygame.Rect(geyser['x'] - geyser['radius'], 
                                         geyser['y'] - geyser['radius'],
                                         geyser['radius'] * 2, geyser['radius'] * 2)
                
                if geyser_rect.colliderect(player_rect):
                    if not hasattr(geyser, 'damage_cooldown') or geyser['damage_cooldown'] <= 0:
                        self.game.player.take_damage(geyser['damage'])
                        geyser['damage_cooldown'] = 30
                    else:
                        geyser['damage_cooldown'] -= 1
        
        # Update molten rain
        for drop in self.molten_raindrops[:]:
            drop['lifetime'] -= 1
            if drop['lifetime'] <= 0 or drop['y'] > HEIGHT:
                self.molten_raindrops.remove(drop)
            else:
                drop['y'] += drop['vy']
                
                player_rect = self.game.player.get_rect()
                drop_rect = pygame.Rect(drop['x'] - drop['radius'], 
                                       drop['y'] - drop['radius'],
                                       drop['radius'] * 2, drop['radius'] * 2)
                
                if drop_rect.colliderect(player_rect):
                    self.game.player.take_damage(drop['damage'])
                    self.molten_raindrops.remove(drop)
        
        # Update heat waves
        for wave in self.heat_waves[:]:
            wave['lifetime'] -= 1
            if wave['lifetime'] <= 0:
                self.heat_waves.remove(wave)
            else:
                if wave['expanding'] and wave['radius'] < wave['max_radius']:
                    wave['radius'] += 3
                    
                player_rect = self.game.player.get_rect()
                wave_rect = pygame.Rect(wave['x'] - wave['radius'], 
                                       wave['y'] - wave['radius'],
                                       wave['radius'] * 2, wave['radius'] * 2)
                
                if wave_rect.colliderect(player_rect):
                    if not hasattr(wave, 'damage_cooldown') or wave['damage_cooldown'] <= 0:
                        self.game.player.take_damage(wave['damage'])
                        wave['damage_cooldown'] = 20
                    else:
                        wave['damage_cooldown'] -= 1
        
        # Update tracking projectiles
        for proj in self.tracking_projectiles[:]:
            proj['lifetime'] -= 1
            if proj['lifetime'] <= 0:
                self.tracking_projectiles.remove(proj)
            else:
                # Home towards player
                if self.game and self.game.player:
                    player_x = self.game.player.x + self.game.player.width // 2
                    player_y = self.game.player.y + self.game.player.height // 2
                    
                    dx = player_x - proj['x']
                    dy = player_y - proj['y']
                    dist = math.sqrt(dx**2 + dy**2)
                    
                    if dist > 0:
                        dx /= dist
                        dy /= dist
                        
                        proj['vx'] += dx * proj['acceleration']
                        proj['vy'] += dy * proj['acceleration']
                        
                        # Limit speed
                        speed = math.sqrt(proj['vx']**2 + proj['vy']**2)
                        if speed > proj['max_speed']:
                            proj['vx'] = (proj['vx'] / speed) * proj['max_speed']
                            proj['vy'] = (proj['vy'] / speed) * proj['max_speed']
                
                proj['x'] += proj['vx']
                proj['y'] += proj['vy']
                
                player_rect = self.game.player.get_rect()
                proj_rect = pygame.Rect(proj['x'] - proj['radius'], 
                                       proj['y'] - proj['radius'],
                                       proj['radius'] * 2, proj['radius'] * 2)
                
                if proj_rect.colliderect(player_rect):
                    self.game.player.take_damage(proj['damage'])
                    self.tracking_projectiles.remove(proj)
        
        # Update lava walls
        for wall in self.lava_walls[:]:
            wall['lifetime'] -= 1
            if wall['lifetime'] <= 0:
                self.lava_walls.remove(wall)
            else:
                if 'vx' in wall:
                    wall['x'] += wall['vx']
                if 'vy' in wall:
                    wall['y'] += wall['vy']
                    
                wall_rect = pygame.Rect(wall['x'], wall['y'], wall['width'], wall['height'])
                player_rect = self.game.player.get_rect()
                
                if wall_rect.colliderect(player_rect):
                    if not hasattr(wall, 'damage_cooldown') or wall['damage_cooldown'] <= 0:
                        self.game.player.take_damage(wall['damage'])
                        wall['damage_cooldown'] = 40
                    else:
                        wall['damage_cooldown'] -= 1
        
        # Update chain eruptions
        for chain in self.chain_eruptions[:]:
            chain['lifetime'] -= 1
            if chain['lifetime'] <= 0:
                self.chain_eruptions.remove(chain)
            else:
                if chain.get('delay', 0) > 0:
                    chain['delay'] -= 1
                    continue
                    
                if chain['growing'] and chain['radius'] < chain['max_radius']:
                    chain['radius'] += 1.5
                    
                player_rect = self.game.player.get_rect()
                chain_rect = pygame.Rect(chain['x'] - chain['radius'], 
                                        chain['y'] - chain['radius'],
                                        chain['radius'] * 2, chain['radius'] * 2)
                
                if chain_rect.colliderect(player_rect):
                    if not hasattr(chain, 'damage_cooldown') or chain['damage_cooldown'] <= 0:
                        self.game.player.take_damage(chain['damage'])
                        chain['damage_cooldown'] = 35
                    else:
                        chain['damage_cooldown'] -= 1
                
                # Chain reaction - trigger nearby eruptions
                if chain['chain_count'] < 2 and random.random() < 0.02:
                    chain['chain_count'] += 1
                    new_x = chain['x'] + random.randint(-100, 100)
                    new_y = chain['y'] + random.randint(-100, 100)
                    
                    self.chain_eruptions.append({
                        'x': new_x, 'y': new_y,
                        'radius': 15, 'max_radius': 40,
                        'growing': True, 'damage': chain['damage'] - 5,
                        'lifetime': 150, 'delay': 20,
                        'chain_count': chain['chain_count']
                    })
        
        # Update vortex
        if self.vortex_active and self.vortex_center:
            self.vortex_center['lifetime'] -= 1
            if self.vortex_center['lifetime'] <= 0:
                self.vortex_active = False
                self.vortex_center = None
            else:
                # Pull player toward center
                if self.game and self.game.player:
                    player_x = self.game.player.x + self.game.player.width // 2
                    player_y = self.game.player.y + self.game.player.height // 2
                    
                    dx = self.vortex_center['x'] - player_x
                    dy = self.vortex_center['y'] - player_y
                    dist = math.sqrt(dx**2 + dy**2)
                    
                    if dist < self.vortex_center['radius'] and dist > 20:
                        dx /= dist
                        dy /= dist
                        
                        self.game.player.x += dx * self.vortex_center['pull_strength']
                        self.game.player.y += dy * self.vortex_center['pull_strength']
                        
                        # Damage if close to center
                        if dist < 50:
                            if not hasattr(self, 'vortex_damage_cooldown') or self.vortex_damage_cooldown <= 0:
                                self.game.player.take_damage(self.vortex_center['damage'])
                                self.vortex_damage_cooldown = 30
                            else:
                                self.vortex_damage_cooldown -= 1
        
        # Update tsunami
        if self.tsunami_wave:
            self.tsunami_wave['lifetime'] -= 1
            if self.tsunami_wave['lifetime'] <= 0:
                self.tsunami_wave = None
            else:
                self.tsunami_wave['x'] += self.tsunami_wave['vx']
                
                tsunami_rect = pygame.Rect(self.tsunami_wave['x'], self.tsunami_wave['y'], 
                                         self.tsunami_wave['width'], self.tsunami_wave['height'])
                player_rect = self.game.player.get_rect()
                
                if tsunami_rect.colliderect(player_rect):
                    if not hasattr(self, 'tsunami_damage_cooldown') or self.tsunami_damage_cooldown <= 0:
                        self.game.player.take_damage(self.tsunami_wave['damage'])
                        self.tsunami_damage_cooldown = 20
                    else:
                        self.tsunami_damage_cooldown -= 1
                        
    def update_lava_effects(self):
        if not self.game:
            return
            
        # Update lava pools (growing eruptions)
        for pool in self.lava_pools[:]:
            pool['lifetime'] -= 1
            if pool['lifetime'] <= 0:
                self.lava_pools.remove(pool)
            else:
                # Handle delayed activation
                if pool.get('delay', 0) > 0:
                    pool['delay'] -= 1
                    continue  # Skip damage/growth this frame
                    
                if pool['growing'] and pool['radius'] < pool['max_radius']:
                    pool['radius'] += 1
                    
                # Check player collision
                player_rect = self.game.player.get_rect()
                pool_rect = pygame.Rect(pool['x'] - pool['radius'], 
                                       pool['y'] - pool['radius'],
                                       pool['radius'] * 2, pool['radius'] * 2)
                
                if pool_rect.colliderect(player_rect):
                    if not hasattr(pool, 'damage_cooldown') or pool['damage_cooldown'] <= 0:
                        self.game.player.take_damage(pool['damage'])
                        pool['damage_cooldown'] = 60
                    else:
                        pool['damage_cooldown'] -= 1
                        
        # Update molten ground (stationary pools)
        for ground in self.molten_ground[:]:
            ground['lifetime'] -= 1
            if ground['lifetime'] <= 0:
                self.molten_ground.remove(ground)
            else:
                # Check player collision
                player_rect = self.game.player.get_rect()
                ground_rect = pygame.Rect(ground['x'] - ground['radius'], 
                                         ground['y'] - ground['radius'],
                                         ground['radius'] * 2, ground['radius'] * 2)
                
                if ground_rect.colliderect(player_rect):
                    if not hasattr(ground, 'damage_cooldown') or ground['damage_cooldown'] <= 0:
                        self.game.player.take_damage(ground['damage'])
                        ground['damage_cooldown'] = 90
                    else:
                        ground['damage_cooldown'] -= 1
                        
        # Heat aura damage
        if self.heat_aura and self.game:
            player_rect = self.game.player.get_rect()
            boss_rect = self.get_rect()
            if boss_rect.inflate(100, 100).colliderect(player_rect):
                if not hasattr(self, 'aura_cooldown') or self.aura_cooldown <= 0:
                    self.game.player.take_damage(10)
                    self.aura_cooldown = 30
                else:
                    self.aura_cooldown -= 1
                    
    def draw(self, screen):
        # Draw molten ground
        for ground in self.molten_ground:
            alpha = ground['lifetime'] / 400
            color = (255, int(100 * alpha), 0)
            pygame.draw.circle(screen, color, (ground['x'], ground['y']), ground['radius'])
            pygame.draw.circle(screen, ORANGE, (ground['x'], ground['y']), ground['radius'], 3)
            
        # Draw lava pools
        for pool in self.lava_pools:
            alpha = pool['lifetime'] / 300
            color = (255, int(50 * alpha), 0)
            pygame.draw.circle(screen, color, (pool['x'], pool['y']), pool['radius'])
            pygame.draw.circle(screen, RED, (pool['x'], pool['y']), pool['radius'], 4)
            
            # Draw lava bubbles
            for i in range(3):
                bubble_x = pool['x'] + random.randint(-pool['radius']//2, pool['radius']//2)
                bubble_y = pool['y'] + random.randint(-pool['radius']//2, pool['radius']//2)
                pygame.draw.circle(screen, YELLOW, (bubble_x, bubble_y), 3)
        
        # Draw magma bombs
        for bomb in self.magma_bombs:
            pygame.draw.circle(screen, ORANGE, (int(bomb['x']), int(bomb['y'])), bomb['radius'])
            pygame.draw.circle(screen, RED, (int(bomb['x']), int(bomb['y'])), bomb['radius'], 2)
            # Add glow effect
            for i in range(1, 4):
                glow_color = (255, 100 - i*20, 0)
                pygame.draw.circle(screen, glow_color, (int(bomb['x']), int(bomb['y'])), bomb['radius'] + i*2, 1)
        
        # Draw lava geysers
        for geyser in self.lava_geysers:
            if geyser.get('delay', 0) <= 0:
                alpha = geyser['lifetime'] / 180
                color = (255, int(150 * alpha), 0)
                pygame.draw.circle(screen, color, (geyser['x'], geyser['y']), geyser['radius'])
                pygame.draw.circle(screen, YELLOW, (geyser['x'], geyser['y']), geyser['radius'], 3)
        
        # Draw molten rain
        for drop in self.molten_raindrops:
            pygame.draw.circle(screen, ORANGE, (int(drop['x']), int(drop['y'])), drop['radius'])
            # Add trail effect
            for i in range(1, 4):
                trail_y = drop['y'] - i * 5
                trail_alpha = 1 - (i * 0.3)
                trail_color = (255, int(100 * trail_alpha), 0)
                pygame.draw.circle(screen, trail_color, (int(drop['x']), int(trail_y)), drop['radius'] - i)
        
        # Draw heat waves
        for wave in self.heat_waves:
            alpha = wave['lifetime'] / 100
            for i in range(3):
                ring_radius = wave['radius'] - i * 10
                if ring_radius > 0:
                    ring_alpha = alpha * (1 - i * 0.3)
                    ring_color = (255, int(100 * ring_alpha), 0)
                    pygame.draw.circle(screen, ring_color, (wave['x'], wave['y']), ring_radius, 3)
        
        # Draw tracking projectiles
        for proj in self.tracking_projectiles:
            pygame.draw.circle(screen, RED, (int(proj['x']), int(proj['y'])), proj['radius'])
            # Add tracking indicator
            pygame.draw.circle(screen, YELLOW, (int(proj['x']), int(proj['y'])), proj['radius'] + 3, 2)
        
        # Draw lava walls
        for wall in self.lava_walls:
            wall_color = (200, 50, 0)
            pygame.draw.rect(screen, wall_color, (wall['x'], wall['y'], wall['width'], wall['height']))
            pygame.draw.rect(screen, ORANGE, (wall['x'], wall['y'], wall['width'], wall['height']), 3)
            # Add warning stripes
            for i in range(0, wall.get('height', wall.get('width', 100)), 10):
                if (i // 10) % 2 == 0:
                    if 'height' in wall:
                        pygame.draw.line(screen, YELLOW, (wall['x'], wall['y'] + i), 
                                       (wall['x'] + wall['width'], wall['y'] + i), 2)
                    else:
                        pygame.draw.line(screen, YELLOW, (wall['x'] + i, wall['y']), 
                                       (wall['x'] + i, wall['y'] + wall['height']), 2)
        
        # Draw chain eruptions
        for chain in self.chain_eruptions:
            if chain.get('delay', 0) <= 0:
                alpha = chain['lifetime'] / 200
                color = (255, int(120 * alpha), 0)
                pygame.draw.circle(screen, color, (chain['x'], chain['y']), chain['radius'])
                pygame.draw.circle(screen, RED, (chain['x'], chain['y']), chain['radius'], 2)
        
        # Draw vortex
        if self.vortex_active and self.vortex_center:
            alpha = self.vortex_center['lifetime'] / 180
            # Draw swirling vortex
            for angle in range(0, 360, 30):
                rad = math.radians(angle + pygame.time.get_ticks() * 0.1)
                x = self.vortex_center['x'] + math.cos(rad) * self.vortex_center['radius'] * alpha
                y = self.vortex_center['y'] + math.sin(rad) * self.vortex_center['radius'] * alpha
                pygame.draw.circle(screen, (255, int(100 * alpha), 0), (int(x), int(y)), 5)
            # Draw center
            pygame.draw.circle(screen, RED, (self.vortex_center['x'], self.vortex_center['y']), 20, 3)
        
        # Draw tsunami
        if self.tsunami_wave:
            wave_color = (150, 30, 0)
            pygame.draw.rect(screen, wave_color, 
                           (self.tsunami_wave['x'], self.tsunami_wave['y'], 
                            self.tsunami_wave['width'], self.tsunami_wave['height']))
            # Add wave crest
            for i in range(0, self.tsunami_wave['width'], 5):
                wave_y = self.tsunami_wave['y'] + math.sin((self.tsunami_wave['x'] + i) * 0.05 + pygame.time.get_ticks() * 0.01) * 10
                pygame.draw.circle(screen, ORANGE, 
                                 (self.tsunami_wave['x'] + i, int(wave_y)), 3)
                
        # Draw heat aura
        if self.heat_aura:
            aura_radius = 120 + 10 * math.sin(pygame.time.get_ticks() * 0.01)
            aura_alpha = 0.2
            aura_color = tuple(int(c * aura_alpha) for c in (255, 100, 0))
            pygame.draw.circle(screen, aura_color, 
                             (self.x + self.width // 2, self.y + self.height // 2), 
                             int(aura_radius))
            
        # Draw main boss body
        if hasattr(self, "use_sprite") and self.use_sprite:
            self.draw_sprite_to_hitbox(screen)
        else:
            pygame.draw.rect(screen, self.color, self.get_rect())

        # Draw telegraphs/effects and health bar.
        for effect in self.effects:
            effect.draw(screen)
        self.draw_health_bar(screen)

