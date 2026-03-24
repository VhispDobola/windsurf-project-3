import pygame
import math
import random
from core.boss import Boss
from core.projectile import Projectile, ProjectileBehavior
from core.effect import Telegraph, Effect
from config.constants import WIDTH, HEIGHT, RED, BLUE, GREEN, YELLOW, PURPLE, ORANGE, CYAN
from utils import load_image_with_transparency

class Corruption:
    def __init__(self, x, y, sprite=None):
        self.x = x
        self.y = y
        self.radius = 10
        self.max_radius = 80
        self.growth_rate = 0.5
        self.damage = 1
        self.sprite = sprite
        
    def update(self):
        if self.radius < self.max_radius:
            self.radius += self.growth_rate
        return True
        
    def draw(self, screen):
        if self.sprite:
            size = max(8, int(self.radius * 2))
            scaled = pygame.transform.smoothscale(self.sprite, (size, size))
            rect = scaled.get_rect(center=(int(self.x), int(self.y)))
            screen.blit(scaled, rect)
            return
        alpha = 1.0 - (self.radius / self.max_radius)
        color = (int(128 * alpha), 0, int(64 * alpha))
        pygame.draw.circle(screen, color, (int(self.x), int(self.y)), int(self.radius), 2)
        
    def get_rect(self):
        return pygame.Rect(self.x - self.radius, self.y - self.radius, self.radius * 2, self.radius * 2)

class TheVirusQueen(Boss):
    def __init__(self):
        super().__init__(WIDTH // 2 - 60, 100, 120, 120, 600, "The Virus Queen")
        self.color = (0, 128, 0)
        self.corruptions = []
        self.virus_spread_timer = 0
        self.mutation_timer = 0
        self.infection_phase = 1
        self.antibodies = []
        self.data_stream_cooldown = 0
        self.corruption_field = []
        self.mutation_burst_cooldown = 0
        self.cluster_burst_cooldown = 0
        self.red_virus_cooldown = 0
        self.firewall_cooldown = 0
        self.glitch_storm_cooldown = 0
        self.system_crash_cooldown = 0
        self.malware_injection_cooldown = 0
        self.split_form = False
        self.second_phase = False
        self.original_health = 600
        self.damage_cooldowns = {}  # Track damage cooldowns for each projectile
        self.corruption_damage_cooldowns = {}
        self.firewalls = []
        self.attack_sprites = {}
        
        # Load the Virus Queen sprite
        try:
            self.sprite = load_image_with_transparency("assets", "sprites", "virus_queen.png", transparent_color=(0, 0, 0))
            # Scale sprite to fit the boss dimensions
            self.sprite = pygame.transform.scale(self.sprite, (self.width, self.height))
            self.use_sprite = True
            self.logger.info("Virus Queen sprite loaded successfully")
        except Exception as e:
            # Fallback to drawn version if sprite not found
            self.use_sprite = False
            self.logger.warning("Virus Queen sprite not found - %s", e)

        self._load_attack_sprites()

    def _load_attack_sprites(self):
        sprite_files = {
            "data_corruption": "virus_data_corruption.png",
            "virus_spread": "virus_virus_spread.png",
            "firewall": "virus_firewall_attack.png",
            "system_crash": "virus_system_crash.png",
            "malware_injection": "virus_malware_injection.png",
        }
        for key, filename in sprite_files.items():
            try:
                self.attack_sprites[key] = load_image_with_transparency("assets", "sprites", filename, transparent_color=(0, 0, 0))
            except Exception:
                continue

    def _apply_attack_sprite(self, projectile, key, size=None):
        sprite = self.attack_sprites.get(key)
        if not sprite:
            return
        projectile.use_custom_sprite = True
        projectile.custom_sprite = sprite
        projectile.sprite_size = size if size is not None else max(projectile.width, projectile.height)

    def _spawn_projectile(self, x, y, dx, dy, damage, color, radius=5, lifetime=180, behavior=None, sprite_key=None):
        projectile = Projectile(x, y, dx, dy, damage, color, radius)
        projectile.lifetime = lifetime
        if behavior is not None:
            projectile.behavior = behavior
        if self.game:
            projectile._game_ref = self.game
        if sprite_key:
            self._apply_attack_sprite(projectile, sprite_key)
        self.projectiles.append(projectile)
        return projectile

    def _enforce_attack_limits(self):
        max_projectiles = 120 + (self.phase - 1) * 45 + (20 if self.split_form else 0)
        if len(self.projectiles) > max_projectiles:
            self.projectiles = self.projectiles[-max_projectiles:]

        if len(self.corruptions) > 24:
            self.corruptions = self.corruptions[-24:]
        if len(self.antibodies) > 18:
            self.antibodies = self.antibodies[-18:]
        if len(self.firewalls) > 12:
            self.firewalls = self.firewalls[-12:]
        
    def run_attacks(self):
        self.virus_spread_timer -= 1
        self.mutation_timer -= 1
        self.data_stream_cooldown -= 1
        self.mutation_burst_cooldown -= 1
        self.cluster_burst_cooldown -= 1
        self.red_virus_cooldown -= 1
        self.firewall_cooldown -= 1
        self.glitch_storm_cooldown -= 1
        self.system_crash_cooldown -= 1
        self.malware_injection_cooldown -= 1
        
        # Update damage cooldowns
        for proj_id in list(self.damage_cooldowns.keys()):
            if self.damage_cooldowns[proj_id] > 0:
                self.damage_cooldowns[proj_id] -= 1
            else:
                del self.damage_cooldowns[proj_id]

        for cooldown_key in list(self.corruption_damage_cooldowns.keys()):
            if self.corruption_damage_cooldowns[cooldown_key] > 0:
                self.corruption_damage_cooldowns[cooldown_key] -= 1
            else:
                del self.corruption_damage_cooldowns[cooldown_key]
        
        if self.phase == 1:
            if self.virus_spread_timer <= 0:
                self.spread_corruption()
                self.virus_spread_timer = 120
            elif self.data_stream_cooldown <= 0:
                self.data_stream_attack()
                self.data_stream_cooldown = 100
            elif self.mutation_burst_cooldown <= 0:
                self.mutation_burst_attack()
                self.mutation_burst_cooldown = 180
            elif self.cluster_burst_cooldown <= 0:
                self.cluster_burst_attack()
                self.cluster_burst_cooldown = 200
            elif self.firewall_cooldown <= 0:
                self.firewall_attack()
                self.firewall_cooldown = 220
                
        elif self.phase == 2:
            if self.virus_spread_timer <= 0:
                self.spread_corruption()
                self.spread_corruption()  # Double spread
                self.virus_spread_timer = 90
            elif self.data_stream_cooldown <= 0:
                self.enhanced_data_stream()
                self.data_stream_cooldown = 80
            elif self.mutation_timer <= 0:
                self.mutate()
                self.mutation_timer = 200
            elif self.red_virus_cooldown <= 0:
                self.red_virus_attack()
                self.red_virus_cooldown = 150
            elif self.malware_injection_cooldown <= 0:
                self.malware_injection_attack(aggressive=False)
                self.malware_injection_cooldown = 130
            elif self.glitch_storm_cooldown <= 0:
                self.glitch_storm_attack()
                self.glitch_storm_cooldown = 160
                
        else:  # phase 3
            if self.virus_spread_timer <= 0:
                self.mass_corruption_spread()
                self.virus_spread_timer = 60
            elif self.data_stream_cooldown <= 0:
                self.viral_barrage()
                self.data_stream_cooldown = 50
            elif self.mutation_timer <= 0:
                self.super_mutate()
                self.mutation_timer = 150
            elif self.cluster_burst_cooldown <= 0:
                self.mega_cluster_burst()
                self.cluster_burst_cooldown = 120
            elif self.malware_injection_cooldown <= 0:
                self.malware_injection_attack(aggressive=True)
                self.malware_injection_cooldown = 95
            elif self.system_crash_cooldown <= 0:
                self.system_crash_attack()
                self.system_crash_cooldown = 180
                
        self.movement()
        self.update_corruptions()
        self.update_antibodies()
        self.update_projectiles_with_tracking()
        self.update_firewalls()
        self._enforce_attack_limits()
        
    def spread_corruption(self):
        anchor_x = self.x + self.width // 2
        anchor_y = self.y + self.height // 2
        if self.game and self.game.player:
            anchor_x = self.game.player.x + self.game.player.width // 2
            anchor_y = self.game.player.y + self.game.player.height // 2

        for _ in range(3):
            x = max(50, min(WIDTH - 50, anchor_x + random.randint(-90, 90)))
            y = max(70, min(HEIGHT - 50, anchor_y + random.randint(-90, 90)))
            self.corruptions.append(Corruption(x, y, self.attack_sprites.get("virus_spread")))
                
    def cluster_burst_attack(self):
        # Create clusters of virus particles that explode
        burst_x = self.x + self.width // 2
        burst_y = self.y + self.height // 2
        
        # Create 3 clusters
        for cluster in range(3):
            angle = random.uniform(0, math.pi * 2)
            distance = random.uniform(50, 150)
            cluster_x = burst_x + math.cos(angle) * distance
            cluster_y = burst_y + math.sin(angle) * distance
            
            # Each cluster has multiple particles
            for particle in range(8):
                particle_angle = (math.pi * 2 * particle) / 8
                speed = random.uniform(2, 5)
                dx = math.cos(particle_angle) * speed
                dy = math.sin(particle_angle) * speed
                
                virus = self._spawn_projectile(
                    cluster_x, cluster_y, dx, dy, 8, (0, 200, 100),
                    radius=6, lifetime=155, sprite_key="malware_injection"
                )
                virus.cluster = True
                virus.cluster_id = f"cluster_{cluster}_{particle}"
                
    def red_virus_attack(self):
        # Create aggressive red virus projectiles
        if self.game and self.game.player:
            target_x = self.game.player.x + self.game.player.width // 2
            target_y = self.game.player.y + self.game.player.height // 2
            
            # Create 5 red viruses that seek aggressively
            for i in range(5):
                angle = (math.pi * 2 * i) / 5 + random.uniform(-0.3, 0.3)
                speed = random.uniform(4, 7)
                dx = math.cos(angle) * speed
                dy = math.sin(angle) * speed
                
                red_virus = self._spawn_projectile(
                    self.x + self.width // 2, self.y + self.height // 2,
                    dx, dy, 12, (255, 50, 50), radius=8, lifetime=210,
                    behavior=ProjectileBehavior.SEEKING, sprite_key="malware_injection"
                )
                red_virus.red_virus = True
                red_virus.seeking = True
                red_virus.aggressive_seek = True
                red_virus.target_x = target_x
                red_virus.target_y = target_y
                red_virus.virus_id = f"red_{i}"
                
    def mega_cluster_burst(self):
        # Enhanced cluster burst for phase 3
        burst_x = self.x + self.width // 2
        burst_y = self.y + self.height // 2
        
        # Create 5 clusters with more particles
        for cluster in range(5):
            angle = (math.pi * 2 * cluster) / 5
            distance = random.uniform(80, 200)
            cluster_x = burst_x + math.cos(angle) * distance
            cluster_y = burst_y + math.sin(angle) * distance
            
            # Each cluster has more particles
            for particle in range(12):
                particle_angle = (math.pi * 2 * particle) / 12
                speed = random.uniform(3, 7)
                dx = math.cos(particle_angle) * speed
                dy = math.sin(particle_angle) * speed
                
                virus = self._spawn_projectile(
                    cluster_x, cluster_y, dx, dy, 10, (255, 100, 0),
                    radius=7, lifetime=165, sprite_key="malware_injection"
                )
                virus.mega_cluster = True
                virus.cluster_id = f"mega_cluster_{cluster}_{particle}"
                
        # Add screen shake for impact
        if self.game:
            self.game.screen_shake.start(3, 15)

    def mass_corruption_spread(self):
        # Create large corruption field
        for i in range(8):
            angle = (math.pi * 2 * i) / 8
            x = self.x + self.width // 2 + math.cos(angle) * 100
            y = self.y + self.height // 2 + math.sin(angle) * 100
            self.corruptions.append(Corruption(x, y, self.attack_sprites.get("data_corruption")))
            
    def data_stream_attack(self):
        # Fan toward player with mild spread so it is readable but threatening.
        cx = self.x + self.width // 2
        cy = self.y + self.height // 2
        if self.game and self.game.player:
            tx = self.game.player.x + self.game.player.width // 2
            ty = self.game.player.y + self.game.player.height // 2
            base_angle = math.atan2(ty - cy, tx - cx)
            angles = [base_angle + (i - 3) * 0.22 for i in range(7)]
        else:
            angles = [(math.pi * 2 * i) / 6 for i in range(6)]

        for angle in angles:
            dx = math.cos(angle) * 5.3
            dy = math.sin(angle) * 5.3
            projectile = self._spawn_projectile(
                cx, cy, dx, dy, 8, (0, 255, 0), radius=6, lifetime=150, sprite_key="malware_injection"
            )
            projectile.data_trail = True
            
    def enhanced_data_stream(self):
        # More complex data stream with seeking behavior
        if self.game and self.game.player:
            target_x = self.game.player.x + self.game.player.width // 2
            target_y = self.game.player.y + self.game.player.height // 2
            
            for i in range(7):
                angle = (math.pi * 2 * i) / 7
                dx = math.cos(angle) * 5
                dy = math.sin(angle) * 5
                projectile = self._spawn_projectile(
                    self.x + self.width // 2, self.y + self.height // 2,
                    dx, dy, 10, (0, 200, 0), radius=7, lifetime=200,
                    behavior=ProjectileBehavior.SEEKING, sprite_key="malware_injection"
                )
                projectile.seeking = True
                projectile.target_x = target_x
                projectile.target_y = target_y
                
    def viral_barrage(self):
        # Massive bullet hell attack
        for i in range(22):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(3, 7)
            dx = math.cos(angle) * speed
            dy = math.sin(angle) * speed
            projectile = self._spawn_projectile(
                self.x + self.width // 2, self.y + self.height // 2,
                dx, dy, 5, (128, 255, 0), radius=4, lifetime=140, sprite_key="malware_injection"
            )
            
    def mutate(self):
        # Change attack patterns and appearance
        self.infection_phase = (self.infection_phase % 3) + 1
        colors = [(0, 128, 0), (128, 0, 128), (0, 128, 128)]
        self.color = colors[self.infection_phase - 1]
        
        # Create mutation effect
        for _ in range(30):
            particle_x = self.x + self.width // 2 + random.randint(-30, 30)
            particle_y = self.y + self.height // 2 + random.randint(-30, 30)
            self.effects.append(Effect(
                particle_x, particle_y, 40,
                self.color
            ))
            
    def mutation_burst_attack(self):
        # Create explosive mutation burst
        if self.game and hasattr(self.game, 'performance_logger'):
            self.game.performance_logger.log_special_ability(self.name)
            
        burst_x = self.x + self.width // 2
        burst_y = self.y + self.height // 2
        
        # Create expanding ring of virus particles
        for ring in range(3):
            radius = 30 + ring * 20
            for i in range(10):
                angle = (math.pi * 2 * i) / 10
                x = burst_x + math.cos(angle) * radius
                y = burst_y + math.sin(angle) * radius

                outward_angle = math.atan2(y - burst_y, x - burst_x)
                speed = 2.2 + ring * 0.65
                virus = self._spawn_projectile(
                    x, y, math.cos(outward_angle) * speed, math.sin(outward_angle) * speed,
                    8, self.color, radius=6, lifetime=150, behavior=ProjectileBehavior.MUTATION,
                    sprite_key="data_corruption"
                )
                virus.mutation = True
                virus.homing_delay = random.randint(34, 58)
                
        # Create mutation visual effect
        for _ in range(50):
            self.effects.append(Effect(
                burst_x + random.randint(-60, 60),
                burst_y + random.randint(-60, 60),
                random.randint(30, 60),
                (random.randint(0, 128), random.randint(128, 255), random.randint(0, 128))
            ))
            
        # Add screen shake
        if self.game:
            self.game.screen_shake.start(4, 20)
            
    def super_mutate(self):
        # Extreme mutation with multiple effects
        self.mutate()
        
        # Create antibodies that attack player
        if self.game and self.game.player:
            for _ in range(3):
                antibody = Projectile(
                    self.x + self.width // 2, self.y + self.height // 2,
                    0, 0, 15, (255, 0, 0), 8
                )
                antibody.antibody = True
                antibody.target = self.game.player
                self._apply_attack_sprite(antibody, "malware_injection")
                self.antibodies.append(antibody)

    def firewall_attack(self):
        """Create blocking corrupted code walls with one safe lane."""
        lane_count = 5
        safe_lane = random.randint(0, lane_count - 1)
        lane_h = (HEIGHT - 120) // lane_count
        direction = random.choice([-1, 1])
        start_x = 0 if direction > 0 else WIDTH - 26
        speed = 4 * direction
        for lane in range(lane_count):
            if lane == safe_lane:
                continue
            y = 70 + lane * lane_h
            self.firewalls.append({
                'x': start_x,
                'y': y,
                'w': 26,
                'h': max(30, lane_h - 6),
                'vx': speed,
                'lifetime': 160,
                'damage': 12,
                'cooldown': 0,
            })
            self.effects.append(Telegraph(start_x + 13, y + lane_h // 2, 24, lane_h, (180, 0, 120), warning_type="cross"))

    def glitch_storm_attack(self):
        """Erratic malware injection storm with randomized vectors."""
        cx = self.x + self.width // 2
        cy = self.y + self.height // 2
        for _ in range(18):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(3.5, 8.5)
            p = self._spawn_projectile(
                cx, cy, math.cos(angle) * speed, math.sin(angle) * speed,
                7, (120, 255, 60), radius=6, lifetime=145,
                behavior=ProjectileBehavior.GLITCH, sprite_key="malware_injection"
            )
            p.glitch = True
            p.glitchy = True
            p.erratic = True

    def system_crash_attack(self):
        """Large corruption burst representing a system-wide crash."""
        cx = self.x + self.width // 2
        cy = self.y + self.height // 2
        self.effects.append(Telegraph(cx, cy, 170, 170, (255, 60, 180), damage=0, warning_type="pulse"))
        for i in range(28):
            angle = (math.pi * 2 * i) / 28
            speed = 5.5 + (i % 4) * 1.2
            p = self._spawn_projectile(
                cx, cy, math.cos(angle) * speed, math.sin(angle) * speed,
                10, (255, 100, 0), radius=8, lifetime=190, sprite_key="system_crash"
            )
            p.system_crash = True

        for i in range(14):
            angle = (math.pi * 2 * i) / 14 + math.pi / 14
            speed = 7.8
            p = self._spawn_projectile(
                cx, cy, math.cos(angle) * speed, math.sin(angle) * speed,
                9, (255, 180, 0), radius=6, lifetime=165, sprite_key="system_crash"
            )
            p.system_crash = True
            p.delay = 12
        if self.game:
            self.game.screen_shake.start(5, 18)

    def malware_injection_attack(self, aggressive=False):
        """Deploy semi-homing malware packets with staggered timing."""
        if not (self.game and self.game.player):
            return

        cx = self.x + self.width // 2
        cy = self.y + self.height // 2
        tx = self.game.player.x + self.game.player.width // 2
        ty = self.game.player.y + self.game.player.height // 2
        base_angle = math.atan2(ty - cy, tx - cx)
        count = 6 if not aggressive else 10

        for i in range(count):
            offset = (i - (count - 1) / 2.0) * (0.22 if not aggressive else 0.16)
            angle = base_angle + offset
            speed = 4.8 if not aggressive else 6.0
            p = self._spawn_projectile(
                cx, cy, math.cos(angle) * speed, math.sin(angle) * speed,
                9 if not aggressive else 10, (100, 255, 120), radius=6,
                lifetime=175 if not aggressive else 210,
                behavior=ProjectileBehavior.SEEKING, sprite_key="malware_injection"
            )
            p.seeking = True
            p.target_x = tx
            p.target_y = ty
            p.malware_packet = True
            if aggressive and i % 2 == 1:
                p.delay = 8
                
    def movement(self):
        # Erratic movement that gets more chaotic in later phases
        chaos = 1 + (self.phase - 1) * 0.5
        self.x += math.sin(pygame.time.get_ticks() * 0.001 * chaos) * 4
        self.y += math.cos(pygame.time.get_ticks() * 0.0015 * chaos) * 3
        
        self.x = max(50, min(WIDTH - 170, self.x))
        self.y = max(50, min(HEIGHT - 220, self.y))
        self.update_rect()
        
    def update_corruptions(self):
        for corruption in self.corruptions[:]:
            corruption.update()
            
            # Check collision with player
            if self.game and self.game.player:
                if corruption.get_rect().colliderect(self.game.player.get_rect()):
                    cooldown_key = (id(corruption), id(self.game.player))
                    if self.corruption_damage_cooldowns.get(cooldown_key, 0) <= 0:
                        damage = corruption.damage
                        self.game.player.take_damage(damage)
                        self.corruption_damage_cooldowns[cooldown_key] = 32

                        # Log ability damage
                        if hasattr(self.game, 'performance_logger'):
                            phase_name = ["Phase 1", "Phase 2", "Phase 3"][self.phase - 1]
                            self.game.performance_logger.log_ability_damage(self.name, f"{phase_name} - Corruption Spread", damage)
                    
            # Remove old corruptions
            if corruption.radius >= corruption.max_radius:
                self.corruptions.remove(corruption)
                
    def update_antibodies(self):
        for antibody in self.antibodies[:]:
            if hasattr(antibody, 'antibody') and antibody.antibody:
                # Seek towards player
                if hasattr(antibody, 'target') and antibody.target:
                    tx = antibody.target.x + antibody.target.width // 2
                    ty = antibody.target.y + antibody.target.height // 2
                    if hasattr(antibody, "steer_towards"):
                        antibody.steer_towards(tx, ty, desired_speed=5.8, max_turn=0.07, accel=0.24)
                        
            antibody.update()
            if antibody.is_off_screen():
                self.antibodies.remove(antibody)
                
            # Check collision with player
            if self.game and self.game.player:
                antibody_rect = pygame.Rect(antibody.x - antibody.radius, antibody.y - antibody.radius,
                                         antibody.radius * 2, antibody.radius * 2)
                if antibody_rect.colliderect(self.game.player.get_rect()):
                    damage = antibody.damage
                    self.game.player.take_damage(damage)
                    self.antibodies.remove(antibody)
                    
                    # Log ability damage
                    if hasattr(self.game, 'performance_logger'):
                        phase_name = ["Phase 1", "Phase 2", "Phase 3"][self.phase - 1]
                        self.game.performance_logger.log_ability_damage(self.name, f"{phase_name} - Antibodies", damage)
                
    def update_projectiles_with_tracking(self):
        # Update special projectile behavior only.
        # Base Boss.update handles movement/off-screen cleanup for self.projectiles.
        if not (self.game and self.game.player):
            return

        tx = self.game.player.x + self.game.player.width // 2
        ty = self.game.player.y + self.game.player.height // 2
        for projectile in self.projectiles[:]:
            if hasattr(projectile, 'seeking') and projectile.seeking:
                projectile.target_x = tx
                projectile.target_y = ty

            if hasattr(projectile, 'erratic') and projectile.erratic:
                projectile.dx += random.uniform(-0.15, 0.15)
                projectile.dy += random.uniform(-0.15, 0.15)
                speed = math.sqrt(projectile.dx * projectile.dx + projectile.dy * projectile.dy)
                if speed > 9.2:
                    scale = 9.2 / speed
                    projectile.dx *= scale
                    projectile.dy *= scale

            if hasattr(projectile, 'aggressive_seek') and projectile.aggressive_seek:
                if hasattr(projectile, "steer_towards"):
                    projectile.steer_towards(tx, ty, desired_speed=6.6, max_turn=0.09, accel=0.28)

            if hasattr(projectile, 'mutation') and projectile.mutation:
                if getattr(projectile, 'age', 0) >= getattr(projectile, 'homing_delay', 30):
                    if hasattr(projectile, "steer_towards"):
                        projectile.steer_towards(tx, ty, desired_speed=4.8, max_turn=0.06, accel=0.20)

    def update_firewalls(self):
        if not self.game or not getattr(self.game, "player", None):
            return
        player_rect = self.game.player.get_rect()
        for wall in self.firewalls[:]:
            wall['x'] += wall['vx']
            wall['lifetime'] -= 1
            if wall['lifetime'] <= 0 or wall['x'] < -40 or wall['x'] > WIDTH + 40:
                self.firewalls.remove(wall)
                continue
            if wall['cooldown'] > 0:
                wall['cooldown'] -= 1
            wall_rect = pygame.Rect(int(wall['x']), int(wall['y']), int(wall['w']), int(wall['h']))
            if wall_rect.colliderect(player_rect) and wall['cooldown'] <= 0:
                self.game.player.take_damage(wall['damage'])
                wall['cooldown'] = 25
                
    def take_damage(self, damage):
        self.health -= damage
        self.hit_flash = 5
        
        # Check for split mechanic - handle before game detects defeat
        if not self.split_form and self.health <= 0:
            self.split_into_two()
            # Set health to positive value to prevent instant defeat detection
            self.health = max(1, self.original_health // 2)
            
    def split_into_two(self):
        if self.split_form:
            return
            
        if self.game and hasattr(self.game, 'performance_logger'):
            self.game.performance_logger.log_special_ability(self.name)
            
        self.split_form = True
        self.second_phase = True
        # Don't set health here - let take_damage handle it to avoid conflicts
        
        # Create visual split effect
        for _ in range(40):
            self.effects.append(Effect(
                self.x + self.width // 2 + random.randint(-40, 40),
                self.y + self.height // 2 + random.randint(-40, 40),
                random.randint(40, 80),
                (255, 100, 100)
            ))
            
        # Change appearance to indicate split form
        self.color = (150, 0, 150)  # Purple color for split form
        self.width = 80  # Smaller width
        self.height = 100  # Smaller height
        self.update_rect()
        
        # Spawn second split form
        if self.game and hasattr(self.game, 'current_bosses'):
            split = TheVirusQueen()
            split.split_form = True
            split.second_phase = True
            split.name = "The Virus Queen (Split)"  # Unique name for the split
            split.color = (150, 0, 150)
            split.width = 80
            split.height = 100
            split.health = max(1, self.original_health // 2)
            split.max_health = split.health
            split.x = min(WIDTH - split.width - 50, self.x + 120)
            split.y = min(HEIGHT - split.height - 50, self.y + 40)
            split.update_rect()
            split.game = self.game
            # Share cooldowns to avoid immediate double spam
            split.virus_spread_timer = self.virus_spread_timer
            split.data_stream_cooldown = self.data_stream_cooldown
            split.mutation_burst_cooldown = self.mutation_burst_cooldown
            split.cluster_burst_cooldown = self.cluster_burst_cooldown
            split.red_virus_cooldown = self.red_virus_cooldown
            split.malware_injection_cooldown = self.malware_injection_cooldown
            self.game.current_bosses.append(split)
            
            # Update our own name to distinguish from the split
            self.name = "The Virus Queen (Original)"
        
        # Add screen shake
        if self.game:
            self.game.screen_shake.start(5, 25)
                
    def draw(self, screen):
        # Draw corruptions first
        for corruption in self.corruptions:
            corruption.draw(screen)
            
        # Draw main boss with sprite or fallback
        if hasattr(self, 'use_sprite') and self.use_sprite:
            # Draw the Virus Queen sprite
            self.draw_sprite_to_hitbox(screen)
        else:
            # Fallback to default boss drawing
            pygame.draw.rect(screen, self.color, self.get_rect())
        
        # Draw split form indicator
        if self.split_form:
            # Draw split aura
            aura_radius = 40 + 10 * math.sin(pygame.time.get_ticks() * 0.01)
            aura_color = (150, 0, 150, 100) if len(self.color) == 3 else self.color
            pygame.draw.circle(screen, aura_color[:3] if len(aura_color) == 3 else aura_color, 
                             (self.x + self.width // 2, self.y + self.height // 2), 
                             int(aura_radius), 3)
            
            # Draw "SPLIT" text
            font = pygame.font.Font(None, 20)
            split_text = font.render("SPLIT", True, (255, 255, 255))
            text_rect = split_text.get_rect(center=(self.x + self.width // 2, self.y - 10))
            screen.blit(split_text, text_rect)
        
        # Draw infection aura
        if self.phase > 1:
            aura_radius = 60 + self.phase * 10
            aura_alpha = 0.3 + 0.1 * math.sin(pygame.time.get_ticks() * 0.005)
            aura_color = tuple(int(c * aura_alpha) for c in self.color)
            pygame.draw.circle(screen, aura_color, 
                             (self.x + self.width // 2, self.y + self.height // 2), 
                             aura_radius, 3)
            
        # Draw projectiles
        for projectile in self.projectiles:
            projectile.draw(screen)
            
        # Draw antibodies
        for antibody in self.antibodies:
            antibody.draw(screen)
            
        # Draw effects
        for effect in self.effects:
            effect.draw(screen)

        # Draw firewall attack walls
        for wall in self.firewalls:
            rect = pygame.Rect(int(wall['x']), int(wall['y']), int(wall['w']), int(wall['h']))
            firewall_sprite = self.attack_sprites.get("firewall")
            if firewall_sprite:
                scaled = pygame.transform.smoothscale(firewall_sprite, (max(1, rect.width), max(1, rect.height)))
                screen.blit(scaled, rect.topleft)
            else:
                pygame.draw.rect(screen, (130, 0, 110), rect)
                pygame.draw.rect(screen, (255, 90, 220), rect, 2)
                for i in range(rect.top + 4, rect.bottom, 9):
                    pygame.draw.line(screen, (255, 180, 240), (rect.left + 3, i), (rect.right - 3, i), 1)
            
        # Use the base health bar drawing with custom color
        self.health_bar_color = self.color
        self.draw_health_bar(screen)


