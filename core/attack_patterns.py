import pygame
import math
import random
from core.projectile import Projectile, ProjectileBehavior
from core.effect import Telegraph
from config.constants import WIDTH, HEIGHT

class AttackPattern:
    """Reusable attack patterns for bosses"""
    
    @staticmethod
    def spiral_attack(boss, projectile_count=8, speed=4.0, damage=6, size=6, clockwise=True, color=None):
        """Create spiral pattern of projectiles"""
        time = pygame.time.get_ticks() * 0.001
        direction = 1 if clockwise else -1
        
        for i in range(projectile_count):
            angle = (360 / projectile_count) * i + time * 50 * direction
            rad = math.radians(angle)
            vel_x = math.cos(rad) * speed
            vel_y = math.sin(rad) * speed
            
            projectile = Projectile(
                boss.x + boss.width // 2,
                boss.y + boss.height // 2,
                vel_x, vel_y, damage, color if color is not None else boss.color, size
            )
            projectile.behavior = ProjectileBehavior.SPIRAL if clockwise else ProjectileBehavior.SPIRAL_REVERSE
            boss.projectiles.append(projectile)
    
    @staticmethod
    def wave_attack(boss, waves=3, projectiles_per_wave=5, speed=5.0, damage=8):
        """Create waves of projectiles"""
        for wave in range(waves):
            for i in range(projectiles_per_wave):
                x = boss.x + boss.width // 2 + (i - projectiles_per_wave // 2) * 30
                y = boss.y + boss.height
                
                projectile = Projectile(x, y, 0, speed, damage, boss.color, 8)
                boss.projectiles.append(projectile)
    
    @staticmethod
    def shotgun_attack(boss, spread_angle=30, pellet_count=5, speed=6.0, damage=10):
        """Create shotgun-like spread attack"""
        if not boss.game or not boss.game.player:
            return
            
        # Calculate base angle to player
        dx = boss.game.player.x - boss.x
        dy = boss.game.player.y - boss.y
        base_angle = math.degrees(math.atan2(dy, dx))
        
        for i in range(pellet_count):
            angle = base_angle + (i - pellet_count // 2) * (spread_angle / pellet_count)
            rad = math.radians(angle)
            vel_x = math.cos(rad) * speed
            vel_y = math.sin(rad) * speed
            
            projectile = Projectile(
                boss.x + boss.width // 2,
                boss.y + boss.height // 2,
                vel_x, vel_y, damage, boss.color, 6
            )
            boss.projectiles.append(projectile)
    
    @staticmethod
    def laser_sweep(boss, start_angle=0, sweep_speed=2, length=300, damage=15):
        """Create sweeping laser attack"""
        from core.projectile import Projectile
        
        angle = start_angle + pygame.time.get_ticks() * 0.001 * sweep_speed
        rad = math.radians(angle)
        
        # Create multiple projectiles to form laser line
        for i in range(0, length, 20):
            x = boss.x + boss.width // 2 + math.cos(rad) * i
            y = boss.y + boss.height // 2 + math.sin(rad) * i
            
            projectile = Projectile(x, y, 0, 0, damage, boss.color, 10)
            projectile.behavior = ProjectileBehavior.LASER
            boss.projectiles.append(projectile)
    
    @staticmethod
    def bouncing_projectiles(boss, count=3, speed=4.0, damage=12):
        """Create projectiles that bounce off walls"""
        for i in range(count):
            angle = random.randint(0, 360)
            rad = math.radians(angle)
            vel_x = math.cos(rad) * speed
            vel_y = math.sin(rad) * speed
            
            projectile = Projectile(
                boss.x + boss.width // 2,
                boss.y + boss.height // 2,
                vel_x, vel_y, damage, boss.color, 8
            )
            projectile.behavior = ProjectileBehavior.BOUNCING
            boss.projectiles.append(projectile)
    
    @staticmethod
    def homing_attack(boss, count=2, speed=3.0, damage=8):
        """Create homing projectiles"""
        for i in range(count):
            projectile = Projectile(
                boss.x + boss.width // 2,
                boss.y + boss.height // 2,
                0, 0, damage, boss.color, 10
            )
            projectile.behavior = ProjectileBehavior.HOMING
            projectile.target_x = boss.game.player.x + boss.game.player.width // 2 if boss.game and boss.game.player else None
            projectile.target_y = boss.game.player.y + boss.game.player.height // 2 if boss.game and boss.game.player else None
            projectile.lifetime = 240  # Reduced from 600 to 240 (4 seconds instead of 10)
            boss.projectiles.append(projectile)
    
    @staticmethod
    def cross_attack(boss, speed=5.0, damage=10):
        """Create cross-shaped projectile pattern"""
        from core.projectile import Projectile
        
        # Horizontal line
        for i in range(-5, 6):
            projectile = Projectile(
                boss.x + boss.width // 2 + i * 20,
                boss.y + boss.height // 2,
                0, speed, damage, boss.color, 6
            )
            boss.projectiles.append(projectile)
        
        # Vertical line
        for i in range(-5, 6):
            projectile = Projectile(
                boss.x + boss.width // 2,
                boss.y + boss.height // 2 + i * 20,
                speed, 0, damage, boss.color, 6
            )
            boss.projectiles.append(projectile)
    
    @staticmethod
    def random_burst(boss, count=12, speed_range=(3, 7), damage_range=(5, 15)):
        """Create random burst of projectiles"""
        for i in range(count):
            angle = random.randint(0, 360)
            rad = math.radians(angle)
            speed = random.uniform(*speed_range)
            damage = random.randint(*damage_range)
            
            vel_x = math.cos(rad) * speed
            vel_y = math.sin(rad) * speed
            
            projectile = Projectile(
                boss.x + boss.width // 2,
                boss.y + boss.height // 2,
                vel_x, vel_y, damage, boss.color, random.randint(4, 10)
            )
            boss.projectiles.append(projectile)
    
    @staticmethod
    def ring_attack(boss, ring_count=3, projectiles_per_ring=8, speed=4.0, damage=8):
        """Create multiple rings of projectiles"""
        for ring in range(ring_count):
            delay = ring * 20  # Delay between rings
            for i in range(projectiles_per_ring):
                angle = (360 / projectiles_per_ring) * i
                rad = math.radians(angle)
                vel_x = math.cos(rad) * speed
                vel_y = math.sin(rad) * speed
                
                projectile = Projectile(
                    boss.x + boss.width // 2,
                    boss.y + boss.height // 2,
                    vel_x, vel_y, damage, boss.color, 6
                )
                projectile.delay = delay
                boss.projectiles.append(projectile)
    
    @staticmethod
    def create_hazard_zone(boss, x, y, radius, damage, duration, hazard_type="zone"):
        """Create a persistent hazard zone"""
        hazard = {
            'x': x, 'y': y,
            'radius': radius, 'damage': damage,
            'lifetime': duration, 'type': hazard_type
        }
        
        if not hasattr(boss, 'arena_hazards'):
            boss.arena_hazards = []
        boss.arena_hazards.append(hazard)
        
        # Add telegraph warning
        telegraph = Telegraph(x, y, duration, radius, (255, 0, 0))
        telegraph.active_start = 30
        boss.effects.append(telegraph)
        
        return hazard
