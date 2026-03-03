"""
Common boss attack patterns and behaviors to reduce code duplication
"""

import math
import random
from .projectile import Projectile
from config.constants import WIDTH, HEIGHT


class BossAttackPattern:
    """Reusable boss attack patterns"""
    
    @staticmethod
    def radial_spread(boss, projectile_count=8, speed=5, damage=10, color=None, offset_angle=0):
        """Create radial spread of projectiles"""
        if color is None:
            color = boss.color
            
        boss_center_x = boss.x + boss.width // 2
        boss_center_y = boss.y + boss.height // 2
        
        for i in range(projectile_count):
            angle = offset_angle + (i * 2 * math.pi / projectile_count)
            dx = math.cos(angle) * speed
            dy = math.sin(angle) * speed
            
            projectile = Projectile(boss_center_x, boss_center_y, dx, dy, damage, color)
            boss.projectiles.append(projectile)
    
    @staticmethod
    def aimed_spread(boss, player, projectile_count=3, speed=6, damage=10, color=None, spread_angle=0.3):
        """Create aimed spread of projectiles"""
        if color is None:
            color = boss.color
            
        boss_center_x = boss.x + boss.width // 2
        boss_center_y = boss.y + boss.height // 2
        player_center_x = player.x + player.width // 2
        player_center_y = player.y + player.height // 2
        
        base_angle = math.atan2(player_center_y - boss_center_y, player_center_x - boss_center_x)
        
        for i in range(projectile_count):
            angle_offset = (i - projectile_count // 2) * spread_angle
            angle = base_angle + angle_offset
            dx = math.cos(angle) * speed
            dy = math.sin(angle) * speed
            
            projectile = Projectile(boss_center_x, boss_center_y, dx, dy, damage, color)
            boss.projectiles.append(projectile)
    
    @staticmethod
    def spiral_pattern(boss, speed=4, damage=10, color=None, duration=120, clockwise=True):
        """Create spiral pattern of projectiles"""
        if color is None:
            color = boss.color
            
        if not hasattr(boss, '_spiral_timer'):
            boss._spiral_timer = 0
        if not hasattr(boss, '_spiral_angle'):
            boss._spiral_angle = 0
            
        boss_center_x = boss.x + boss.width // 2
        boss_center_y = boss.y + boss.height // 2
        
        if boss._spiral_timer < duration:
            angle_increment = 0.1 if clockwise else -0.1
            boss._spiral_angle += angle_increment
            
            dx = math.cos(boss._spiral_angle) * speed
            dy = math.sin(boss._spiral_angle) * speed
            
            projectile = Projectile(boss_center_x, boss_center_y, dx, dy, damage, color)
            boss.projectiles.append(projectile)
            
            boss._spiral_timer += 1
        else:
            boss._spiral_timer = 0
    
    @staticmethod
    def wall_barrage(boss, speed=3, damage=15, color=None, wall_count=4):
        """Create walls of projectiles from screen edges"""
        if color is None:
            color = boss.color
            
        for wall in range(wall_count):
            # Top wall
            for x in range(0, WIDTH, 40):
                projectile = Projectile(x, 0, 0, speed, damage, color)
                boss.projectiles.append(projectile)
            
            # Bottom wall
            for x in range(0, WIDTH, 40):
                projectile = Projectile(x, HEIGHT - 20, 0, -speed, damage, color)
                boss.projectiles.append(projectile)
    
    @staticmethod
    def shotgun_blast(boss, player, pellet_count=12, speed=8, damage=5, color=None):
        """Create shotgun-like blast towards player"""
        if color is None:
            color = boss.color
            
        boss_center_x = boss.x + boss.width // 2
        boss_center_y = boss.y + boss.height // 2
        player_center_x = player.x + player.width // 2
        player_center_y = player.y + player.height // 2
        
        base_angle = math.atan2(player_center_y - boss_center_y, player_center_x - boss_center_x)
        
        for i in range(pellet_count):
            angle_offset = random.uniform(-0.5, 0.5)
            angle = base_angle + angle_offset
            dx = math.cos(angle) * speed
            dy = math.sin(angle) * speed
            
            projectile = Projectile(boss_center_x, boss_center_y, dx, dy, damage, color)
            projectile.pellet = True  # Mark as pellet for special behavior
            boss.projectiles.append(projectile)
    
    @staticmethod
    def bouncing_projectiles(boss, speed=5, damage=12, color=None, count=3):
        """Create projectiles that bounce off walls"""
        if color is None:
            color = boss.color
            
        boss_center_x = boss.x + boss.width // 2
        boss_center_y = boss.y + boss.height // 2
        
        for i in range(count):
            angle = random.uniform(0, 2 * math.pi)
            dx = math.cos(angle) * speed
            dy = math.sin(angle) * speed
            
            projectile = Projectile(boss_center_x, boss_center_y, dx, dy, damage, color)
            projectile.bouncing = True
            projectile.bounces_left = 3
            boss.projectiles.append(projectile)
    
    @staticmethod
    def timed_explosion(boss, delay=60, radius=100, damage=20, color=None):
        """Create delayed explosion at boss position"""
        if color is None:
            color = boss.color
            
        if not hasattr(boss, '_explosion_timers'):
            boss._explosion_timers = []
        
        boss_center_x = boss.x + boss.width // 2
        boss_center_y = boss.y + boss.height // 2
        
        # Add new explosion timer
        boss._explosion_timers.append({'timer': delay, 'x': boss_center_x, 'y': boss_center_y, 
                                   'radius': radius, 'damage': damage, 'color': color})
        
        # Update existing timers
        for explosion in boss._explosion_timers[:]:
            explosion['timer'] -= 1
            if explosion['timer'] <= 0:
                # Create explosion effect
                from .effect import Telegraph
                explosion_effect = Telegraph(explosion['x'], explosion['y'], 30, radius, color, damage)
                explosion_effect.active_start = 0
                explosion_effect.active_end = 10
                boss.effects.append(explosion_effect)
                
                boss._explosion_timers.remove(explosion)


class BossMovementPattern:
    """Reusable boss movement patterns"""
    
    @staticmethod
    def sine_wave_movement(boss, amplitude=50, frequency=0.02, center_y=None):
        """Move boss in sine wave pattern"""
        if center_y is None:
            center_y = HEIGHT // 4
            
        if not hasattr(boss, '_sine_time'):
            boss._sine_time = 0
            
        boss._sine_time += frequency
        boss.y = center_y + math.sin(boss._sine_time) * amplitude
        
        # Keep boss on screen
        boss.x = max(0, min(WIDTH - boss.width, boss.x))
        boss.update_rect()
    
    @staticmethod
    def circular_movement(boss, center_x, center_y, radius=100, speed=0.02):
        """Move boss in circular pattern"""
        if not hasattr(boss, '_circle_angle'):
            boss._circle_angle = 0
            
        boss._circle_angle += speed
        boss.x = center_x + math.cos(boss._circle_angle) * radius - boss.width // 2
        boss.y = center_y + math.sin(boss._circle_angle) * radius - boss.height // 2
        
        boss.update_rect()
    
    @staticmethod
    def dash_movement(boss, player, dash_speed=15, cooldown=120):
        """Dash towards player periodically"""
        if not hasattr(boss, '_dash_timer'):
            boss._dash_timer = 0
        if not hasattr(boss, '_dash_cooldown'):
            boss._dash_cooldown = 0
            
        boss_center_x = boss.x + boss.width // 2
        boss_center_y = boss.y + boss.height // 2
        player_center_x = player.x + player.width // 2
        player_center_y = player.y + player.height // 2
        
        if boss._dash_cooldown <= 0:
            # Start dash
            angle = math.atan2(player_center_y - boss_center_y, player_center_x - boss_center_x)
            boss._dash_dx = math.cos(angle) * dash_speed
            boss._dash_dy = math.sin(angle) * dash_speed
            boss._dash_timer = 20  # Dash duration
            boss._dash_cooldown = cooldown
        elif boss._dash_timer > 0:
            # Continue dash
            boss.x += boss._dash_dx
            boss.y += boss._dash_dy
            boss._dash_timer -= 1
        else:
            boss._dash_cooldown -= 1
        
        boss.update_rect()


class BossPhaseManager:
    """Standardized phase management for bosses"""
    
    @staticmethod
    def check_phase_transition(boss, phase_thresholds=None):
        """Check and handle phase transitions"""
        if phase_thresholds is None:
            phase_thresholds = [0.6, 0.3]  # Phase 2 at 60%, Phase 3 at 30%
        
        old_phase = getattr(boss, 'current_phase', 1)
        health_percentage = boss.health / boss.max_health
        
        new_phase = 1
        for i, threshold in enumerate(phase_thresholds):
            if health_percentage <= threshold:
                new_phase = i + 2
        
        if new_phase != old_phase:
            boss.current_phase = new_phase
            if hasattr(boss, 'on_phase_change'):
                boss.on_phase_change(old_phase, new_phase)
            return True
        
        return False
    
    @staticmethod
    def get_phase_multiplier(boss, phase_multipliers=None):
        """Get multiplier based on current phase"""
        if phase_multipliers is None:
            phase_multipliers = [1.0, 1.5, 2.0]  # Phase 1, 2, 3
        
        current_phase = getattr(boss, 'current_phase', 1)
        return phase_multipliers[min(current_phase - 1, len(phase_multipliers) - 1)]
