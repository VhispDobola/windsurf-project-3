import pygame
import math
import random
from bosses.boss_base import BaseBoss
from core.attack_patterns import AttackPattern
from core.projectile import Projectile
from core.effect import Telegraph
from config.constants import WIDTH, HEIGHT, PURPLE, CYAN, ORANGE, RED, YELLOW, WHITE, BLUE
from utils import load_image

class EternalGuardian(BaseBoss):
    def __init__(self):
        super().__init__(WIDTH // 2 - 100, 80, 200, 200, 510, "Eternal Guardian")
        self.color = PURPLE
        self.laser_angle = 0
        self.laser_cooldown = 0
        self.burst_cooldown = 0
        self.dash_cooldown = 0
        self.target_x = self.x
        self.movement_speed = 2
        
        # Load the actual Eternal Guardian sprite
        try:
            self.sprite = load_image("assets", "sprites", "eternal_guardian.png")
            # Scale sprite to fit the larger boss dimensions
            self.sprite = pygame.transform.scale(self.sprite, (self.width, self.height))
            self.use_sprite = True
        except Exception:
            # Fallback to drawn version if sprite not found
            self.use_sprite = False
            self.logger.warning("Eternal Guardian sprite not found, using fallback rendering")
        
        # Load Cosmic Orb Sweep projectile sprite
        try:
            self.cosmic_orb_sprite = load_image("assets", "sprites", "eternal_guardian_cosmic_orb_sweep.png")
            self.use_cosmic_orb_sprite = True
            self.logger.info("Cosmic Orb Sweep sprite loaded successfully")
        except Exception as e:
            self.use_cosmic_orb_sprite = False
            self.logger.warning("Cosmic Orb Sweep sprite not found - %s", e)
        
        # Crystalline visual effects (for projectiles and attacks)
        self.crystal_plates = []
        self.energy_core_pulse = 0
        self.cosmic_dust_particles = []
        self.crystalline_aura_rotation = 0
        
        # Initialize crystalline structure
        self._init_crystalline_structure()
        
    def _init_crystalline_structure(self):
        """Initialize the crystalline plates and cosmic structure"""
        # Create interlocking geometric plates
        for i in range(12):
            angle = (math.pi * 2 * i) / 12
            self.crystal_plates.append({
                'angle': angle,
                'size': random.uniform(15, 25),
                'color_shift': random.uniform(0.8, 1.2),
                'pulse_offset': random.uniform(0, math.pi * 2)
            })
        
        # Initialize subtle sparkling dust particles
        for _ in range(30):
            self.cosmic_dust_particles.append({
                'x': random.uniform(-40, 40),
                'y': random.uniform(-40, 40),
                'vx': random.uniform(-0.3, 0.3),  # Slower, more subtle movement
                'vy': random.uniform(-0.3, 0.3),
                'lifetime': random.uniform(80, 160),
                'max_lifetime': 160,
                'sparkle': random.uniform(0.5, 1.0)  # Sparkle intensity
            })
        
    def update(self):
        """Update crystalline effects and base boss"""
        super().update()
        
        # Update energy core pulse
        self.energy_core_pulse = (self.energy_core_pulse + 0.05) % (math.pi * 2)
        
        # Update crystalline aura rotation
        self.crystalline_aura_rotation = (self.crystalline_aura_rotation + 1) % 360
        
        # Update cosmic dust particles
        active_particles = []
        new_particles = []
        for particle in self.cosmic_dust_particles:
            particle['x'] += particle['vx']
            particle['y'] += particle['vy']
            particle['lifetime'] -= 1
            
            if particle['lifetime'] <= 0:
                # Add new particle
                new_particles.append({
                    'x': random.uniform(-30, 30),
                    'y': random.uniform(-30, 30),
                    'vx': random.uniform(-0.5, 0.5),
                    'vy': random.uniform(-0.5, 0.5),
                    'lifetime': random.uniform(100, 200),
                    'max_lifetime': 200
                })
            else:
                active_particles.append(particle)
        self.cosmic_dust_particles = active_particles + new_particles
        
    def run_attacks(self):
        cooldowns = {
            'laser': self.laser_cooldown,
            'burst': self.burst_cooldown,
            'dash': self.dash_cooldown
        }
        self.update_attack_cooldowns(cooldowns)
        self.laser_cooldown = cooldowns['laser']
        self.burst_cooldown = cooldowns['burst']
        self.dash_cooldown = cooldowns['dash']
        
        if self.phase == 1:
            if self.laser_cooldown <= 0:
                self.cosmic_orb_sweep()
                self.laser_cooldown = 180  # Increased from 120
            elif self.burst_cooldown <= 0:
                self.radial_burst()
                self.burst_cooldown = 120  # Increased from 80
                
        elif self.phase == 2:
            if self.laser_cooldown <= 0:
                self.cosmic_orb_sweep()
                self.laser_cooldown = 140  # Increased from 90
            elif self.burst_cooldown <= 0:
                self.radial_burst()
                self.burst_cooldown = 90  # Increased from 60
                
        else:  # phase 3
            if self.laser_cooldown <= 0:
                self.twin_cosmic_orb_sweep()
                self.laser_cooldown = 100  # Increased from 70
            elif self.burst_cooldown <= 0:
                self.mega_burst()
                self.burst_cooldown = 60  # Increased from 40
                
        if self.dash_cooldown <= 0 and random.random() < 0.01:
            self.dash_attack()
            self.dash_cooldown = 150
            
        self.movement()
        
    def movement(self):
        # Check if boss is stuck (not moving toward target)
        if abs(self.x - self.target_x) < 5:
            # Target range must match safe_movement boundaries: 
            # min_x = boundary_margin (50), max_x = WIDTH - width - boundary_margin (1000 - 200 - 50 = 750)
            self.target_x = random.randint(50, WIDTH - self.width - 50)
        
        # Calculate movement direction
        dx = 0
        if self.x < self.target_x:
            dx = self.movement_speed
        elif self.x > self.target_x:
            dx = -self.movement_speed
        
        # Apply movement with boundary checking
        old_x = self.x
        self.safe_movement(dx, 0)
        
        # Failsafe: if boss didn't move (stuck at boundary), pick new target
        if abs(self.x - old_x) < 1:  # Didn't move
            self.target_x = random.randint(50, WIDTH - self.width - 50)
        
    def cosmic_orb_sweep(self):
        # Create ultimate Cosmic Orb Sweep with space-time distortion
        if self.game and self.game.player:
            # Calculate angle to player
            player_center_x = self.game.player.x + self.game.player.width // 2
            player_center_y = self.game.player.y + self.game.player.height // 2
            boss_center_x = self.x + self.width // 2
            boss_center_y = self.y + self.height
            
            # Base angle to player
            base_angle = math.atan2(player_center_y - boss_center_y, player_center_x - boss_center_x)
            
            # Create 8 large purple cosmic orbs that sweep out
            for i in range(8):
                angle = base_angle + (i - 4) * math.pi / 16
                
                # Add crystalline energy effect
                pulse_factor = 1.0 + 0.3 * math.sin(self.energy_core_pulse + i * 0.5)
                speed = 10 * pulse_factor
                
                dx = math.cos(angle) * speed
                dy = math.sin(angle) * speed
                
                # Use your Cosmic Orb Sweep sprite for large purple orbs
                if hasattr(self, 'use_cosmic_orb_sprite') and self.use_cosmic_orb_sprite:
                    # Create large cosmic orb with your cosmic orb sprite
                    orb = Projectile(boss_center_x, boss_center_y, dx, dy, 20, PURPLE, 15)
                    orb.use_custom_sprite = True
                    orb.custom_sprite = self.cosmic_orb_sprite
                    orb.sprite_size = 24  # Larger size for cosmic orbs
                    orb.laser = True
                    orb.crystalline = True  # Mark for special rendering
                    self.projectiles.append(orb)
            
            # Create space-time distortion telegraph
            t = Telegraph(boss_center_x, boss_center_y, 40, 250, PURPLE, damage=12)
            t.active_start = 24
            t.active_end = 30
            t.space_distortion = True  # Mark for special rendering
            self.effects.append(t)
        
    def twin_cosmic_orb_sweep(self):
        # Create two sets of cosmic orbs that weave through each other
        if self.game and self.game.player:
            # Calculate angle to player
            player_center_x = self.game.player.x + self.game.player.width // 2
            player_center_y = self.game.player.y + self.game.player.height // 2
            boss_center_x = self.x + self.width // 2
            boss_center_y = self.y + self.height
            
            # Base angle to player
            base_angle = math.atan2(player_center_y - boss_center_y, player_center_x - boss_center_x)
            
            # Create two sets of large purple cosmic orbs that weave in cosmic dance
            for set_offset in [-60, 60]:
                for i in range(6):
                    # Create weaving pattern
                    wave_offset = math.sin(pygame.time.get_ticks() * 0.005 + i * 0.5) * 20
                    angle = base_angle + (i - 3) * math.pi / 12 + math.radians(wave_offset + set_offset)
                    
                    # Add crystalline energy pulse
                    pulse_factor = 1.0 + 0.4 * math.sin(self.energy_core_pulse + i * 0.3)
                    speed = 8 * pulse_factor
                    
                    dx = math.cos(angle) * speed
                    dy = math.sin(angle) * speed
                    
                    # Use your Cosmic Orb Sweep sprite for weaving orbs
                    if hasattr(self, 'use_cosmic_orb_sprite') and self.use_cosmic_orb_sprite:
                        # Create large weaving cosmic orb with your cosmic orb sprite
                        orb = Projectile(boss_center_x + set_offset // 2, boss_center_y, dx, dy, 25, PURPLE, 20)
                        orb.use_custom_sprite = True
                        orb.custom_sprite = self.cosmic_orb_sprite
                        orb.sprite_size = 28  # Even larger for twin sweep
                        orb.laser = True
                        orb.crystalline = True
                        orb.weaving = True  # Mark for special rendering
                        self.projectiles.append(orb)
                
                # Create enhanced space-time distortion
                t = Telegraph(boss_center_x + set_offset // 2, boss_center_y, 35, 220, PURPLE, damage=14)
                t.active_start = 20
                t.active_end = 28
                t.space_distortion = True
                self.effects.append(t)
        
    def radial_burst(self):
        # Create crystalline shard burst that fractures into dimensions
        boss_center_x = self.x + self.width // 2
        boss_center_y = self.y + self.height // 2
        
        for i in range(8):
            angle = (math.pi * 2 * i) / 8
            
            # Create crystalline shards with different dimensional reflections
            for reflection in range(3):  # 3 dimensional reflections per shard
                reflect_angle = angle + (reflection - 1) * math.pi / 16
                speed = 5.0 + reflection * 1.5
                
                dx = math.cos(reflect_angle) * speed
                dy = math.sin(reflect_angle) * speed
                
                # Different colors for different dimensions
                colors = [PURPLE, BLUE, WHITE]
                color = colors[reflection % len(colors)]
                
                shard = Projectile(boss_center_x, boss_center_y, dx, dy, 6, color, 8)
                shard.crystalline = True
                shard.dimensional = True  # Mark for special rendering
                self.projectiles.append(shard)
            
    def mega_burst(self):
        # Ultimate crystalline cataclysm - fractures reality
        boss_center_x = self.x + self.width // 2
        boss_center_y = self.y + self.height // 2
        
        # Create massive crystalline explosion
        for i in range(12):
            angle = (math.pi * 2 * i) / 12
            
            # Multiple layers of crystalline destruction
            for layer in range(4):
                layer_angle = angle + layer * math.pi / 24
                speed = 4.0 + layer * 1.5
                
                dx = math.cos(layer_angle) * speed
                dy = math.sin(layer_angle) * speed
                
                # Evolving colors through layers
                colors = [PURPLE, BLUE, CYAN, WHITE]
                color = colors[layer % len(colors)]
                size = 8 + layer * 2
                
                shard = Projectile(boss_center_x, boss_center_y, dx, dy, size, color, 10)
                shard.crystalline = True
                shard.dimensional = True
                shard.ultimate = True  # Mark for ultimate rendering
                self.projectiles.append(shard)
            
    def dash_attack(self):
        # Dash towards player position
        if self.game and self.game.player:
            target_x = self.game.player.x + self.game.player.width // 2
            dx = 20 if target_x > self.x else -20
            self.safe_movement(dx, 0)
            
        # Create crystalline telegraph with enhanced visuals
        t = Telegraph(self.x + self.width // 2, self.y + self.height // 2, 60, 60, PURPLE, damage=15)
        t.active_start = 20
        t.active_end = 50
        t.crystalline = True  # Mark for special rendering
        self.effects.append(t)
        
    def draw(self, screen):
        """Draw Eternal Guardian with subtle sparkling dust aura"""
        center_x = self.x + self.width // 2
        center_y = self.y + self.height // 2
        
        # Draw subtle sparkling dust particles (aura effect)
        for particle in self.cosmic_dust_particles:
            alpha = particle['lifetime'] / particle['max_lifetime']
            sparkle = particle.get('sparkle', 0.7)  # Default sparkle if not present
            
            # Create subtle sparkle effect
            sparkle_alpha = alpha * sparkle * 0.6  # Subtle, not overwhelming
            size = int(2 + sparkle * 2)  # Size varies with sparkle intensity
            
            if size > 0 and sparkle_alpha > 0.1:
                # Soft purple-white sparkle color
                color = (
                    int(200 * sparkle_alpha),
                    int(180 * sparkle_alpha), 
                    int(255 * sparkle_alpha)
                )
                dust_x = center_x + particle['x']
                dust_y = center_y + particle['y']
                pygame.draw.circle(screen, color, (int(dust_x), int(dust_y)), size)
        
        # Draw the actual sprite or fallback
        if hasattr(self, 'use_sprite') and self.use_sprite:
            # Draw your actual Eternal Guardian sprite
            self.draw_sprite_to_hitbox(screen)
        else:
            # Fallback: Draw crystalline body
            body_rect = self.get_rect()
            pygame.draw.rect(screen, self.color, body_rect)
        
        # Draw enhanced projectiles with crystalline effects
        for projectile in self.projectiles:
            if hasattr(projectile, 'crystalline') and projectile.crystalline:
                # Draw crystalline projectile with special effects
                self._draw_crystalline_projectile(screen, projectile)
            elif hasattr(projectile, 'use_custom_sprite') and projectile.use_custom_sprite:
                # Draw custom sprite projectiles normally
                projectile.draw(screen)
            else:
                # Draw regular projectiles
                projectile.draw(screen)
        
        # Draw enhanced telegraphs with space-time distortion
        for effect in self.effects:
            if hasattr(effect, 'space_distortion') and effect.space_distortion:
                self._draw_space_distortion(screen, effect)
            elif hasattr(effect, 'crystalline') and effect.crystalline:
                self._draw_crystalline_telegraph(screen, effect)
            else:
                effect.draw(screen)
        
        # Draw health bar with crystalline styling
        self.health_bar_color = PURPLE
        self.draw_health_bar(screen)
        
    def _draw_crystalline_projectile(self, screen, projectile):
        """Draw enhanced crystalline projectile"""
        # Check for custom sprite first
        if hasattr(projectile, 'use_custom_sprite') and projectile.use_custom_sprite:
            # Draw custom sprite
            if hasattr(projectile, 'custom_sprite') and projectile.custom_sprite:
                # Scale sprite to appropriate size
                sprite_size = getattr(projectile, 'sprite_size', projectile.radius * 2)
                scaled_sprite = pygame.transform.scale(projectile.custom_sprite, (sprite_size, sprite_size))
                
                # Center the sprite on projectile position
                sprite_rect = scaled_sprite.get_rect()
                sprite_rect.center = (int(projectile.x + projectile.width // 2), int(projectile.y + projectile.height // 2))
                screen.blit(scaled_sprite, sprite_rect)
        else:
            # Fallback: Draw crystalline core
            pygame.draw.circle(screen, projectile.color, 
                             (int(projectile.x), int(projectile.y)), 
                             projectile.radius)
        
        # Draw crystalline facets
        if hasattr(projectile, 'dimensional') and projectile.dimensional:
            # Draw dimensional reflections
            for i in range(3):
                offset_angle = (math.pi * 2 * i) / 3
                offset_x = projectile.x + math.cos(offset_angle) * projectile.radius * 0.5
                offset_y = projectile.y + math.sin(offset_angle) * projectile.radius * 0.5
                pygame.draw.circle(screen, WHITE, 
                                 (int(offset_x), int(offset_y)), 
                                 projectile.radius // 3, 1)
        
        # Draw energy trail
        if hasattr(projectile, 'ultimate') and projectile.ultimate:
            trail_length = 20
            for i in range(trail_length):
                trail_alpha = 1.0 - (i / trail_length)
                trail_size = projectile.radius * trail_alpha
                trail_x = projectile.x - projectile.dx * i * 0.5
                trail_y = projectile.y - projectile.dy * i * 0.5
                trail_color = tuple(int(c * trail_alpha) for c in projectile.color)
                pygame.draw.circle(screen, trail_color, 
                                 (int(trail_x), int(trail_y)), 
                                 int(trail_size), 1)
    
    def _draw_space_distortion(self, screen, effect):
        """Draw space-time distortion effect"""
        if effect.duration > 0:
            # Calculate distortion parameters
            progress = 1.0 - (effect.duration / effect.max_duration)
            distortion_radius = effect.radius * (1.0 + progress * 0.5)
            
            # Draw rippling space-time
            for ring in range(3):
                ring_radius = distortion_radius + ring * 10
                ring_alpha = 0.5 - ring * 0.15
                ring_color = tuple(int(c * ring_alpha) for c in effect.color)
                pygame.draw.circle(screen, ring_color, 
                                 (int(effect.x), int(effect.y)), 
                                 int(ring_radius), 2)
            
            # Draw gravitational lensing effect
            elapsed = effect.max_duration - effect.duration
            if effect.active_start <= elapsed <= effect.active_end:
                # Distortion waves
                for wave in range(4):
                    wave_angle = (math.pi * 2 * wave) / 4 + pygame.time.get_ticks() * 0.01
                    wave_x = effect.x + math.cos(wave_angle) * distortion_radius
                    wave_y = effect.y + math.sin(wave_angle) * distortion_radius
                    pygame.draw.circle(screen, WHITE, (int(wave_x), int(wave_y)), 3)
    
    def _draw_crystalline_telegraph(self, screen, effect):
        """Draw enhanced crystalline telegraph"""
        if effect.duration > 0:
            # Draw crystalline warning pattern
            alpha = min(1.0, effect.duration / 30)
            color = tuple(int(c * alpha) for c in effect.color)
            
            # Draw crystalline star pattern
            points = []
            for i in range(8):
                angle = (math.pi * 2 * i) / 8
                outer_x = effect.x + math.cos(angle) * effect.radius
                outer_y = effect.y + math.sin(angle) * effect.radius
                points.append((outer_x, outer_y))
                
                inner_angle = angle + math.pi / 8
                inner_x = effect.x + math.cos(inner_angle) * (effect.radius // 2)
                inner_y = effect.y + math.sin(inner_angle) * (effect.radius // 2)
                points.append((inner_x, inner_y))
            
            pygame.draw.polygon(screen, color, points, 2)


