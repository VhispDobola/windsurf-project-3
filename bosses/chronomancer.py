import pygame
import math
import random
from bosses.boss_base import BaseBoss
from core.projectile import Projectile, ProjectileBehavior
from core.effect import Telegraph
from core.particle_system import ParticleSystem, TimeOrb
from core.entity import DamageType
from config.constants import WIDTH, HEIGHT, RED, BLUE, GREEN, YELLOW, PURPLE, ORANGE, CYAN, WHITE
from utils import load_image_with_transparency

class Chronomancer(BaseBoss):
    def __init__(self):
        super().__init__(WIDTH // 2 - 50, 100, 100, 100, 750, "Chronomancer")
        self.color = CYAN
        self.time_orbs = []
        self.time_field_active = False
        self.time_field_timer = 0
        self.rewind_cooldown = 0
        self.rewind_visual_timer = 0
        self.rewind_motion_timer = 0
        self.freeze_cooldown = 0
        self.time_bullets = []
        self.paradox_mode = False
        self.paradox_timer = 0
        self.paradox_mode_timer = 0
        self.paradox_rifts = []
        self.time_stop_active = False
        self.time_stop_duration = 0
        self.time_stop_cooldown = 0
        self.time_stop_warning = 0  # Add warning timer
        self.phantom_mode = False
        self.clockwork_cooldown = 0
        self.clockwork_nodes = []
        self.position_history = []
        self.particle_system = ParticleSystem()
        self.attack_sprites = {}
        self.time_stop_base_duration = 60
        
        # Load the Chronomancer sprite
        try:
            self.sprite = load_image_with_transparency("assets", "sprites", "chronomancer.png", transparent_color=(0, 0, 0))
            # Scale sprite to fit the boss dimensions
            self.sprite = pygame.transform.scale(self.sprite, (self.width, self.height))
            self.use_sprite = True
            self.logger.info("Chronomancer sprite loaded successfully")
        except Exception as e:
            # Fallback to drawn version if sprite not found
            self.use_sprite = False
            self.logger.warning("Chronomancer sprite not found - %s", e)

        try:
            self.time_orb_sprite = load_image_with_transparency("assets", "sprites", "time_orbs.png", transparent_color=(0, 0, 0))
        except Exception:
            self.time_orb_sprite = None

        self._load_attack_sprites()

    def _load_attack_sprites(self):
        sprite_files = {
            "clockwork": "chronomancer_clockwork_barrage.png",
            "time_stop": "chronomancer_time_stop.png",
            "paradox": "chronomancer_paradox_attack.png",
        }
        for key, filename in sprite_files.items():
            try:
                self.attack_sprites[key] = load_image_with_transparency(
                    "assets", "sprites", filename, transparent_color=(0, 0, 0)
                )
            except Exception as e:
                self.logger.warning("Chronomancer attack sprite not found for %s - %s", key, e)

    def _apply_attack_sprite(self, projectile, key, size=None):
        sprite = self.attack_sprites.get(key)
        if not sprite:
            return
        projectile.use_custom_sprite = True
        projectile.custom_sprite = sprite
        projectile.sprite_size = size if size is not None else max(projectile.width, projectile.height)
        
    def run_attacks(self):
        self.time_field_timer -= 1
        self.rewind_cooldown -= 1
        self.rewind_visual_timer -= 1
        self.rewind_motion_timer -= 1
        self.freeze_cooldown -= 1
        self.paradox_timer -= 1
        self.paradox_mode_timer -= 1
        self.time_stop_cooldown -= 1
        self.time_stop_duration -= 1
        self.time_stop_warning -= 1
        self.clockwork_cooldown -= 1

        if self.paradox_mode_timer <= 0:
            self.paradox_mode = False
            self.paradox_rifts.clear()
        
        if self.time_stop_duration <= 0:
            self.time_stop_active = False
        
        if self.phase == 1:
            if self.time_field_timer <= 0:
                self.create_time_field("slow")
                self.time_field_timer = 150
            elif self.rewind_cooldown <= 0:
                self.time_rewind_bullets()
                self.rewind_cooldown = 120
            elif self.clockwork_cooldown <= 0:
                self.clockwork_barrage()
                self.clockwork_cooldown = 180
            elif self.time_stop_cooldown <= 0:
                self.time_stop_cooldown = 300
                self.time_stop_warning = 60  # 1 second warning
                
        elif self.phase == 2:
            if self.time_field_timer <= 0:
                field_type = "slow" if random.random() < 0.5 else "fast"
                self.create_time_field(field_type)
                self.time_field_timer = 100
            elif self.rewind_cooldown <= 0:
                self.time_rewind_bullets()
                self.rewind_cooldown = 90
            elif self.freeze_cooldown <= 0:
                self.time_freeze_burst()
                self.freeze_cooldown = 180
            elif self.clockwork_cooldown <= 0:
                self.clockwork_barrage(denser=True)
                self.clockwork_cooldown = 150
            elif self.time_stop_cooldown <= 0:
                self.time_stop_cooldown = 250
                self.time_stop_warning = 60
                
        else:  # phase 3
            if self.time_field_timer <= 0:
                self.create_time_field("slow")
                self.create_time_field("fast")
                self.time_field_timer = 80
            elif self.rewind_cooldown <= 0:
                self.advanced_rewind_pattern()
                self.rewind_cooldown = 70
            elif self.freeze_cooldown <= 0:
                self.time_freeze_burst()
                self.freeze_cooldown = 120
            elif self.paradox_timer <= 0:
                self.paradox_mode = True
                self.paradox_timer = 260
                self.paradox_mode_timer = 180
                self.create_paradox_field()
            elif self.clockwork_cooldown <= 0:
                self.clockwork_barrage(denser=True, homing=True)
                self.clockwork_cooldown = 110
            elif self.time_stop_cooldown <= 0:
                self.time_stop_cooldown = 200
                self.time_stop_warning = 60
                
        # Activate time stop after warning
        if self.time_stop_warning <= 0 and self.time_stop_warning > -1:
            self.activate_time_stop()
                
        self.update_paradox_rifts()
        self.movement()
        self.update_time_orbs()
        self.update_time_bullets()
        self._update_clockwork_nodes()
        
    def create_time_field(self, field_type):
        orb_x = random.randint(100, WIDTH - 100)
        orb_y = random.randint(100, HEIGHT - 200)
        self.particle_system.add_time_orb(orb_x, orb_y, field_type, sprite=self.time_orb_sprite)
        field = Telegraph(orb_x, orb_y, 90, 120 if field_type == "slow" else 100, CYAN if field_type == "slow" else ORANGE)
        field.warning_type = "pulse"
        self.effects.append(field)
        
    def time_rewind_bullets(self):
        self.rewind_visual_timer = 60
        self.rewind_motion_timer = 30
        for i in range(6):
            angle = (math.pi * 2 * i) / 6
            dx = math.cos(angle) * 3
            dy = math.sin(angle) * 3
            bullet = Projectile(
                self.x + self.width // 2, self.y + self.height // 2,
                dx, dy, 8, CYAN, 6
            )
            bullet.rewind = True
            bullet.rewind_trail = []
            if self.paradox_mode:
                self._apply_attack_sprite(bullet, "paradox", size=24)
            self.time_bullets.append(bullet)
            
    def advanced_rewind_pattern(self):
        # Spiral pattern with rewind bullets
        self.rewind_visual_timer = 80
        self.rewind_motion_timer = 40
        for i in range(12):
            angle = (math.pi * 2 * i) / 12 + pygame.time.get_ticks() * 0.001
            dx = math.cos(angle) * 4
            dy = math.sin(angle) * 4
            bullet = Projectile(
                self.x + self.width // 2, self.y + self.height // 2,
                dx, dy, 10, CYAN, 7
            )
            bullet.rewind = True
            bullet.rewind_trail = []
            self._apply_attack_sprite(bullet, "paradox", size=26)
            self.time_bullets.append(bullet)
            
    def time_freeze_burst(self):
        if self.game and self.game.player:
            # Create freeze effect around player
            player_x = self.game.player.x + self.game.player.width // 2
            player_y = self.game.player.y + self.game.player.height // 2
            
            for i in range(16):
                angle = (math.pi * 2 * i) / 16
                spawn_radius = 70
                spawn_x = player_x + math.cos(angle) * spawn_radius
                spawn_y = player_y + math.sin(angle) * spawn_radius
                dx = -math.cos(angle) * 3.2
                dy = -math.sin(angle) * 3.2
                bullet = Projectile(
                    spawn_x, spawn_y,
                    dx, dy, 7, (150, 150, 255), 5
                )
                bullet.freeze = True
                bullet.freeze_ring = True
                bullet.lifetime = 110
                self.time_bullets.append(bullet)
                
            self.effects.append(Telegraph(player_x, player_y, 90, 90, (150, 150, 255)))
            
    def activate_time_stop(self):
        # Check if player is dashing - if so, cancel time stop
        if self.game and self.game.player and self.game.player.dash_duration > 0:
            return  # Player avoided time stop by dashing
            
        # Reduced duration and added counterplay
        self.time_stop_active = True
        self.time_stop_duration = self.time_stop_base_duration
        if self.game and hasattr(self.game, "audio_manager"):
            self.game.audio_manager.play_custom_sound("time_stop", volume_scale=0.95)
        
        # Create time stop visual effect with better warning
        for i in range(24):
            angle = (math.pi * 2 * i) / 24
            x = self.x + self.width // 2 + math.cos(angle) * 100
            y = self.y + self.height // 2 + math.sin(angle) * 100
            self.effects.append(Telegraph(x, y, 30, 30, (255, 255, 255)))
            
        # Add screen shake
        if self.game:
            self.game.screen_shake.start(2, 8)
            
    def create_paradox_field(self):
        # Create random temporal rifts that pull the player.
        self.paradox_rifts = []
        for _ in range(4):
            rift_x = random.randint(120, WIDTH - 120)
            rift_y = random.randint(120, HEIGHT - 180)
            rift = {
                "x": float(rift_x),
                "y": float(rift_y),
                "radius": random.randint(90, 140),
                "pull": random.uniform(0.4, 0.9),
                "phase": random.uniform(0, math.pi * 2),
            }
            self.paradox_rifts.append(rift)
            self.particle_system.add_time_orb(rift_x, rift_y, "paradox", sprite=self.time_orb_sprite)
            self.effects.append(Telegraph(rift_x, rift_y, 70, rift["radius"], (90, 255, 255), warning_type="pulse"))

    def clockwork_barrage(self, denser=False, homing=False):
        """Floating clocks launch temporal projectiles with mini-time-stop impact."""
        ring = 10 if denser else 7
        speed = 4.6 if denser else 4.0
        cx = self.x + self.width // 2
        cy = self.y + self.height // 2
        self.clockwork_nodes = []
        for i in range(ring):
            angle = (math.pi * 2 * i) / ring + random.uniform(-0.08, 0.08)
            orbit = 65 if denser else 55
            launch_x = cx + math.cos(angle) * orbit
            launch_y = cy + math.sin(angle) * orbit
            bullet = Projectile(launch_x, launch_y, math.cos(angle) * speed, math.sin(angle) * speed, 9, CYAN, 6)
            bullet.clockwork = True
            bullet.mini_time_stop = True
            bullet.homing_temporal = homing
            self._apply_attack_sprite(bullet, "clockwork", size=24 if denser else 22)
            self.time_bullets.append(bullet)
            self.clockwork_nodes.append(
                {
                    "base_angle": angle,
                    "orbit": orbit,
                    "time_offset": random.uniform(0.0, math.pi * 2),
                    "timer": 85,
                }
            )

    def _update_clockwork_nodes(self):
        for node in self.clockwork_nodes[:]:
            node["timer"] -= 1
            if node["timer"] <= 0:
                self.clockwork_nodes.remove(node)

    def update_paradox_rifts(self):
        if not (self.paradox_mode and self.paradox_rifts and self.game and self.game.player):
            return
        player = self.game.player
        px = player.x + player.width // 2
        py = player.y + player.height // 2
        for rift in self.paradox_rifts:
            rift["phase"] += 0.06
            dx = rift["x"] - px
            dy = rift["y"] - py
            dist = math.sqrt(dx * dx + dy * dy)
            if 1 < dist < rift["radius"]:
                pull_scale = (1 - (dist / rift["radius"])) * rift["pull"]
                player.x += (dx / dist) * pull_scale * 1.6
                player.y += (dy / dist) * pull_scale * 1.6
                player.update_rect()
            
    def movement(self):
        if self.rewind_motion_timer > 0 and self.position_history:
            rewind_index = max(0, len(self.position_history) - 1 - min(4, self.rewind_motion_timer))
            hx, hy = self.position_history[rewind_index]
            self.x = hx
            self.y = hy
            self.update_rect()
            return

        self.position_history.append((self.x, self.y))
        if len(self.position_history) > 120:
            self.position_history.pop(0)

        self.x += math.sin(pygame.time.get_ticks() * 0.0008) * 3
        self.y += math.cos(pygame.time.get_ticks() * 0.0012) * 2
        
        self.x = max(50, min(WIDTH - 150, self.x))
        self.y = max(50, min(HEIGHT - 200, self.y))
        self.update_rect()
        
    def update_time_orbs(self):
        if not self.time_stop_active:
            self.particle_system.update()
        
        # Apply time effects to player if in range
        player = self.game.player if self.game and hasattr(self.game, 'player') and self.game.player else None
        if player:
            for particle in self.particle_system.particles:
                if isinstance(particle, TimeOrb):
                    dist = math.sqrt((player.x - particle.x)**2 + (player.y - particle.y)**2)
                    field_radius = particle.size + 80
                    if dist < field_radius:
                        # Time field slows player and nearby projectiles and creates temporal trails.
                        if particle.orb_type == "slow":
                            player.add_speed_modifier(0.55, 10)
                            for projectile in self.game.player.projectiles[:]:
                                pdx = projectile.x - particle.x
                                pdy = projectile.y - particle.y
                                if (pdx * pdx + pdy * pdy) <= (field_radius * field_radius):
                                    projectile.dx *= 0.92
                                    projectile.dy *= 0.92
                                    self.particle_system.add_particle(
                                        projectile.x, projectile.y,
                                        random.uniform(-0.6, 0.6), random.uniform(-0.6, 0.6),
                                        (140, 255, 255), 16, 2
                                    )
                        elif particle.orb_type == "fast":
                            player.add_speed_modifier(2.0, 60)  # Speed up to 200% for 1 second
                        elif particle.orb_type == "paradox":
                            player.add_speed_modifier(0.7, 8)
                            
        # Apply complete time stop freeze.
        if self.time_stop_active and self.game and self.game.player:
            self.game.player.time_stopped = True
            self.game.player.set_speed_override(0.0, 5)
            
            # Freeze player projectiles.
            for projectile in self.game.player.projectiles[:]:
                if not hasattr(projectile, 'original_dx'):
                    projectile.original_dx = projectile.dx
                    projectile.original_dy = projectile.dy
                projectile.time_stopped = True
                projectile.dx = 0
                projectile.dy = 0
                
            # Freeze boss projectiles.
            for projectile in self.projectiles[:]:
                if not hasattr(projectile, 'original_dx'):
                    projectile.original_dx = projectile.dx
                    projectile.original_dy = projectile.dy
                projectile.time_stopped = True
                projectile.dx = 0
                projectile.dy = 0

            # Freeze Chronomancer temporal bullets.
            for bullet in self.time_bullets[:]:
                if not hasattr(bullet, 'original_dx'):
                    bullet.original_dx = bullet.dx
                    bullet.original_dy = bullet.dy
                bullet.time_stopped = True
                bullet.dx = 0
                bullet.dy = 0
                
        elif self.game and self.game.player:
            self.game.player.time_stopped = False
            # Don't reset speed here - let the status effect system handle it
            
            # Unfreeze all projectiles and restore original speeds
            for projectile in self.game.player.projectiles[:]:
                projectile.time_stopped = False
                if hasattr(projectile, 'original_dx'):
                    projectile.dx = projectile.original_dx
                    projectile.dy = projectile.original_dy
                    delattr(projectile, 'original_dx')
                    delattr(projectile, 'original_dy')
                
            for projectile in self.projectiles[:]:
                projectile.time_stopped = False
                if hasattr(projectile, 'original_dx'):
                    projectile.dx = projectile.original_dx
                    projectile.dy = projectile.original_dy
                    delattr(projectile, 'original_dx')
                    delattr(projectile, 'original_dy')

            for bullet in self.time_bullets[:]:
                bullet.time_stopped = False
                if hasattr(bullet, 'original_dx'):
                    bullet.dx = bullet.original_dx
                    bullet.dy = bullet.original_dy
                    delattr(bullet, 'original_dx')
                    delattr(bullet, 'original_dy')
                            
    def update_time_bullets(self):
        for bullet in self.time_bullets[:]:
            if getattr(bullet, "time_stopped", False):
                continue

            if hasattr(bullet, 'homing_temporal') and bullet.homing_temporal and self.game and self.game.player:
                tx = self.game.player.x + self.game.player.width // 2
                ty = self.game.player.y + self.game.player.height // 2
                if hasattr(bullet, "steer_towards"):
                    bullet.steer_towards(tx, ty, desired_speed=4.2, max_turn=0.06, accel=0.18)

            if hasattr(bullet, 'rewind') and bullet.rewind:
                # Rewind bullets move in reverse pattern
                bullet.dy *= -0.98
                bullet.dx *= 0.98
                if not hasattr(bullet, "rewind_trail"):
                    bullet.rewind_trail = []
                bullet.rewind_trail.append((bullet.x + bullet.width // 2, bullet.y + bullet.height // 2))
                if len(bullet.rewind_trail) > 8:
                    bullet.rewind_trail.pop(0)

            if hasattr(bullet, 'mini_time_stop') and bullet.mini_time_stop and self.game and self.game.player:
                if bullet.get_rect().colliderect(self.game.player.get_rect()):
                    self.game.player.add_speed_modifier(0.6, 35)
                    self.effects.append(
                        Telegraph(
                            self.game.player.x + self.game.player.width // 2,
                            self.game.player.y + self.game.player.height // 2,
                            24,
                            36,
                            CYAN,
                            warning_type="pulse",
                        )
                    )
                    self.time_bullets.remove(bullet)
                    continue

            bullet.update()
            if bullet.is_off_screen():
                self.time_bullets.remove(bullet)
                
    def draw(self, screen):
        # Draw time stop warning
        if self.time_stop_warning > 0:
            # Draw pulsing warning circle around boss
            warning_radius = 120 + (60 - self.time_stop_warning) * 2
            warning_alpha = self.time_stop_warning / 60
            for i in range(3):
                radius = warning_radius - i * 20
                if radius > 0:
                    color = (255, int(255 * warning_alpha), int(100 * warning_alpha))
                    pygame.draw.circle(screen, color, 
                                     (self.x + self.width // 2, self.y + self.height // 2), 
                                     radius, 3)
            
            # Draw warning text
            if self.time_stop_warning > 30:
                font = pygame.font.Font(None, 36)
                text = font.render("TIME STOP!", True, (255, 255, 0))
                text_rect = text.get_rect(center=(WIDTH // 2, 100))
                screen.blit(text, text_rect)
        
        # Draw time fields
        self.particle_system.draw(screen)
        ticks = pygame.time.get_ticks()
        for particle in self.particle_system.particles:
            if not isinstance(particle, TimeOrb):
                continue
            radius = int(particle.size + 78 + 8 * math.sin(ticks * 0.004 + particle.x * 0.01))
            center = (int(particle.x), int(particle.y))
            pygame.draw.circle(screen, (80, 220, 255), center, radius, 1)
            for mark in range(12):
                mark_angle = (math.pi * 2 * mark / 12) + ticks * 0.001
                inner = (
                    int(center[0] + math.cos(mark_angle) * (radius - 8)),
                    int(center[1] + math.sin(mark_angle) * (radius - 8)),
                )
                outer = (
                    int(center[0] + math.cos(mark_angle) * radius),
                    int(center[1] + math.sin(mark_angle) * radius),
                )
                pygame.draw.line(screen, (110, 255, 255), inner, outer, 1)

        if self.paradox_mode:
            for rift in self.paradox_rifts:
                center = (int(rift["x"]), int(rift["y"]))
                pulse = 1 + 0.22 * math.sin(rift["phase"] * 3.0)
                radius = int(rift["radius"] * pulse)
                pygame.draw.circle(screen, (90, 255, 255), center, radius, 2)
                if self.attack_sprites.get("paradox"):
                    swirl = pygame.transform.rotozoom(
                        self.attack_sprites["paradox"], -pygame.time.get_ticks() * 0.2, 0.45
                    )
                    swirl.set_alpha(135)
                    rect = swirl.get_rect(center=center)
                    screen.blit(swirl, rect)

        if self.time_stop_active:
            time_stop_sprite = self.attack_sprites.get("time_stop")
            if time_stop_sprite:
                total = max(1, self.time_stop_base_duration)
                elapsed = max(0, total - self.time_stop_duration)
                progress = max(0.0, min(1.0, elapsed / total))

                # Start small, rotate continuously, and scale up through the attack.
                scale = 0.2 + (1.8 * progress)
                angle = (elapsed * 12) % 360
                pulse = 0.9 + 0.1 * math.sin(pygame.time.get_ticks() * 0.015)
                transformed = pygame.transform.rotozoom(time_stop_sprite, angle, scale * pulse)
                transformed.set_alpha(int(100 + 120 * progress))

                if self.game and self.game.player:
                    center = (
                        int(self.game.player.x + self.game.player.width // 2),
                        int(self.game.player.y + self.game.player.height // 2),
                    )
                else:
                    center = (WIDTH // 2, HEIGHT // 2)

                sprite_rect = transformed.get_rect(center=center)
                screen.blit(transformed, sprite_rect)

            # Crystallization shards and cyan freeze outlines for all frozen objects.
            if self.game and self.game.player:
                px = int(self.game.player.x + self.game.player.width // 2)
                py = int(self.game.player.y + self.game.player.height // 2)
                for i in range(8):
                    shard_angle = (math.pi * 2 * i / 8) + pygame.time.get_ticks() * 0.002
                    tip_x = px + int(math.cos(shard_angle) * 46)
                    tip_y = py + int(math.sin(shard_angle) * 46)
                    left_x = px + int(math.cos(shard_angle + 0.22) * 26)
                    left_y = py + int(math.sin(shard_angle + 0.22) * 26)
                    right_x = px + int(math.cos(shard_angle - 0.22) * 26)
                    right_y = py + int(math.sin(shard_angle - 0.22) * 26)
                    pygame.draw.polygon(screen, (120, 255, 255), [(tip_x, tip_y), (left_x, left_y), (right_x, right_y)], 1)

                for projectile in self.game.player.projectiles + self.projectiles + self.time_bullets:
                    if getattr(projectile, "time_stopped", False):
                        rect = projectile.get_rect()
                        pygame.draw.rect(screen, (80, 255, 255), rect.inflate(6, 6), 1)
            
        # Draw main boss with paradox effect and sprite support
        if self.paradox_mode:
            # Draw multiple ghost images
            for i in range(3):
                offset_x = math.sin(pygame.time.get_ticks() * 0.01 + i * 2) * 10
                offset_y = math.cos(pygame.time.get_ticks() * 0.01 + i * 2) * 10
                alpha = 0.3 + 0.2 * math.sin(pygame.time.get_ticks() * 0.02 + i)
                color = tuple(int(c * alpha) for c in self.color)
                pygame.draw.rect(screen, color, (self.x + offset_x, self.y + offset_y, self.width, self.height))
                
        # Draw the sprite or fallback
        if hasattr(self, 'use_sprite') and self.use_sprite:
            # Draw the Chronomancer sprite
            self.draw_sprite_to_hitbox(screen)
        else:
            # Fallback to default boss drawing
            pygame.draw.rect(screen, self.color, (self.x, self.y, self.width, self.height))
        
        # Draw time bullets
        for bullet in self.time_bullets:
            if hasattr(bullet, "rewind_trail") and bullet.rewind_trail:
                for idx, point in enumerate(bullet.rewind_trail):
                    trail_alpha = (idx + 1) / max(1, len(bullet.rewind_trail))
                    trail_size = max(1, int(4 * trail_alpha))
                    pygame.draw.circle(screen, (120, 255, 255), (int(point[0]), int(point[1])), trail_size, 1)
            bullet.draw(screen)

        # Floating clocks that launch clockwork barrages (different "time" hand offsets).
        if self.clockwork_nodes:
            cx = self.x + self.width // 2
            cy = self.y + self.height // 2
            for node in self.clockwork_nodes:
                t = pygame.time.get_ticks() * 0.004 + node["base_angle"]
                nx = cx + math.cos(t) * node["orbit"]
                ny = cy + math.sin(t) * node["orbit"]
                pygame.draw.circle(screen, (210, 245, 255), (int(nx), int(ny)), 12, 2)
                minute_angle = t * 2.2 + node["time_offset"]
                hour_angle = t * 0.7 + node["time_offset"] * 0.5
                minute_tip = (int(nx + math.cos(minute_angle) * 9), int(ny + math.sin(minute_angle) * 9))
                hour_tip = (int(nx + math.cos(hour_angle) * 6), int(ny + math.sin(hour_angle) * 6))
                pygame.draw.line(screen, (120, 255, 255), (int(nx), int(ny)), minute_tip, 2)
                pygame.draw.line(screen, (170, 255, 255), (int(nx), int(ny)), hour_tip, 2)

        if self.rewind_visual_timer > 0:
            center = (int(self.x + self.width // 2), int(self.y + self.height // 2))
            spin = pygame.time.get_ticks() * -0.008  # Counter-clockwise.
            for r in (24, 42, 60):
                pygame.draw.circle(screen, (120, 255, 255), center, r, 1)
                hand_tip = (
                    int(center[0] + math.cos(spin + r * 0.03) * (r - 4)),
                    int(center[1] + math.sin(spin + r * 0.03) * (r - 4)),
                )
                pygame.draw.line(screen, (170, 255, 255), center, hand_tip, 2)
            
        # Draw effects
        for effect in self.effects:
            effect.draw(screen)
            
        # Use the base health bar drawing
        self.draw_health_bar(screen)


