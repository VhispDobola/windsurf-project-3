import pygame
import math
import random
from core.boss import Boss
from core.projectile import Projectile
from core.effect import Telegraph
from config.constants import WIDTH, HEIGHT, RED, BLUE, GREEN, YELLOW, PURPLE, ORANGE, CYAN, WHITE

class Particle:
    def __init__(self, x, y, dx, dy, color, lifetime, size=3):
        self.x = x
        self.y = y
        self.dx = dx
        self.dy = dy
        self.color = color
        self.lifetime = lifetime
        self.max_lifetime = lifetime
        self.size = size
        
    def update(self):
        self.x += self.dx
        self.y += self.dy
        self.lifetime -= 1
        self.dx *= 0.98  # Friction
        self.dy *= 0.98
        return self.lifetime > 0
        
    def draw(self, screen):
        alpha = self.lifetime / self.max_lifetime
        size = int(self.size * alpha)
        if size > 0:
            pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), size)

class ShadowClone:
    def __init__(self, x, y, is_real=False):
        self.x = x
        self.y = y
        self.width = 60
        self.height = 60
        self.is_real = is_real
        self.lifetime = 300 if not is_real else 999999
        self.alpha = 0.5 if not is_real else 1.0
        self.color = (50, 0, 50) if not is_real else (100, 0, 100)
        self.projectiles = []
        
    def update(self):
        self.lifetime -= 1
        if not self.is_real:
            self.alpha = 0.3 + 0.2 * math.sin(self.lifetime * 0.1)
            
        active_projectiles = []
        for projectile in self.projectiles:
            projectile.update()
            if not projectile.is_off_screen():
                active_projectiles.append(projectile)
        self.projectiles = active_projectiles
                
        return self.lifetime > 0
        
    def shoot(self, target_x, target_y):
        if self.is_real:
            dx = (target_x - self.x) / 50
            dy = (target_y - self.y) / 50
            self.projectiles.append(Projectile(self.x + self.width // 2, self.y + self.height // 2, dx, dy, 8, PURPLE, 6))
            
    def draw(self, screen):
        color = tuple(int(c * self.alpha) for c in self.color)
        rect = pygame.Rect(int(self.x), int(self.y), self.width, self.height)
        pygame.draw.rect(screen, (0, 0, 0), rect.inflate(6, 6), border_radius=8)
        pygame.draw.rect(screen, color, rect, border_radius=6)
        if self.is_real:
            pygame.draw.rect(screen, WHITE, rect, 2, border_radius=6)
            
        for projectile in self.projectiles:
            projectile.draw(screen)

class VoidAssassin(Boss):
    def __init__(self):
        super().__init__(WIDTH // 2 - 40, 150, 80, 80, 700, "Void Assassin")
        self.color = (50, 0, 50)
        self.stealth_mode = False
        self.stealth_timer = 0
        self.shadow_clones = []
        self.clone_timer = 0
        self.assassination_cooldown = 0
        self.shadow_step_cooldown = 0
        self.particles = []
        self.revealed_timer = 0
        self.smoke_bomb_cooldown = 0
        self.void_projectile_cooldown = 0
        self.shadow_veil_timer = 0
        self.phantom_mode = False
        
    def run_attacks(self):
        self.stealth_timer -= 1
        self.clone_timer -= 1
        self.assassination_cooldown -= 1
        self.shadow_step_cooldown -= 1
        self.revealed_timer -= 1
        self.smoke_bomb_cooldown -= 1
        self.void_projectile_cooldown -= 1
        self.shadow_veil_timer -= 1
        
        # End stealth mode when revealed timer expires
        if self.stealth_mode and self.revealed_timer <= 0:
            self.stealth_mode = False

        if self.shadow_veil_timer <= 0:
            self.phantom_mode = False
        
        if self.phase == 1:
            if self.stealth_timer <= 0 and not self.stealth_mode:
                self.enter_stealth()
                self.stealth_timer = 180
            elif self.clone_timer <= 0:
                self.create_shadow_clones(2)
                self.clone_timer = 150
            elif self.smoke_bomb_cooldown <= 0:
                self.smoke_bomb_escape()
                self.smoke_bomb_cooldown = 200
            elif self.void_projectile_cooldown <= 0:
                self.void_projectile_attack(2)
                self.void_projectile_cooldown = 120
                
        elif self.phase == 2:
            if self.stealth_timer <= 0 and not self.stealth_mode:
                self.enter_stealth()
                self.stealth_timer = 120
            elif self.clone_timer <= 0:
                self.create_shadow_clones(3)
                self.clone_timer = 100
            elif self.assassination_cooldown <= 0:
                self.assassination_strike()
                self.assassination_cooldown = 200
            elif self.void_projectile_cooldown <= 0:
                self.void_projectile_attack(4)
                self.void_projectile_cooldown = 90
                
        else:  # phase 3
            if self.stealth_timer <= 0 and not self.stealth_mode:
                self.enter_stealth()
                self.stealth_timer = 90
            elif self.clone_timer <= 0:
                self.create_shadow_clones(4)
                self.clone_timer = 80
            elif self.assassination_cooldown <= 0:
                self.multi_assassination()
                self.assassination_cooldown = 150
            elif self.shadow_step_cooldown <= 0:
                self.shadow_step_barrage()
                self.shadow_step_cooldown = 180
            elif self.void_projectile_cooldown <= 0:
                self.activate_shadow_veil()
                self.void_projectile_attack(6)
                self.void_projectile_cooldown = 70
                
        self.movement()
        self.update_clones()
        self.update_particles()
        
    def enter_stealth(self):
        self.stealth_mode = True
        self.revealed_timer = 60
        for _ in range(20):
            self.particles.append(Particle(
                self.x + self.width // 2, self.y + self.height // 2,
                random.uniform(-3, 3), random.uniform(-3, 3),
                (50, 0, 50), 30, 4
            ))
            
    def create_shadow_clones(self, count):
        for i in range(count):
            is_real = (i == count - 1)  # Last clone is real
            clone_x = self.x + random.randint(-150, 150)
            clone_y = self.y + random.randint(-100, 100)
            clone_x = max(50, min(WIDTH - 110, clone_x))
            clone_y = max(50, min(HEIGHT - 160, clone_y))
            self.shadow_clones.append(ShadowClone(clone_x, clone_y, is_real))
            
    def assassination_strike(self):
        if self.game and self.game.player:
            target_x = self.game.player.x + self.game.player.width // 2
            target_y = self.game.player.y + self.game.player.height // 2
            
            for clone in self.shadow_clones:
                if clone.is_real:
                    clone.shoot(target_x, target_y)
                    self.effects.append(Telegraph(clone.x + clone.width // 2, clone.y + clone.height // 2, 30, 30, RED))
                    
    def multi_assassination(self):
        if self.game and self.game.player:
            target_x = self.game.player.x + self.game.player.width // 2
            target_y = self.game.player.y + self.game.player.height // 2
            
            for clone in self.shadow_clones:
                clone.shoot(target_x, target_y)
                self.effects.append(Telegraph(clone.x + clone.width // 2, clone.y + clone.height // 2, 25, 25, RED))
                
    def smoke_bomb_escape(self):
        # Create smoke cloud at current position
        for _ in range(40):
            self.particles.append(Particle(
                self.x + self.width // 2, self.y + self.height // 2,
                random.uniform(-6, 6), random.uniform(-6, 6),
                (100, 100, 100), 60, 8
            ))
        
        # Teleport to new position with safe boundaries
        old_x, old_y = self.x, self.y
        # Ensure teleportation stays within screen bounds (50px margin from edges)
        self.x = random.randint(50, WIDTH - self.width - 50)
        self.y = random.randint(50, HEIGHT - self.height - 50)
        self.update_rect()
        
        # Create smoke at new position
        for _ in range(20):
            self.particles.append(Particle(
                self.x + self.width // 2, self.y + self.height // 2,
                random.uniform(-4, 4), random.uniform(-4, 4),
                (50, 50, 50), 40, 6
            ))
        
        # Leave shadow clone at old position
        shadow = ShadowClone(old_x, old_y, False)
        shadow.lifetime = 120
        self.shadow_clones.append(shadow)
        
        # Add screen shake
        if self.game:
            self.game.screen_shake.start(2, 10)
            
    def shadow_step_barrage(self):
        for _ in range(5):
            new_x = random.randint(50, WIDTH - self.width - 50)
            new_y = random.randint(50, HEIGHT - self.height - 50)
            
            for _ in range(10):
                self.particles.append(Particle(
                    self.x + self.width // 2, self.y + self.height // 2,
                    random.uniform(-5, 5), random.uniform(-5, 5),
                    (100, 0, 100), 20, 3
                ))
                
            self.x = new_x
            self.y = new_y
            self.update_rect()
            
            # Create projectile burst at new location
            for i in range(8):
                angle = (math.pi * 2 * i) / 8
                dx = math.cos(angle) * 4
                dy = math.sin(angle) * 4
                self.projectiles.append(Projectile(
                    self.x + self.width // 2, self.y + self.height // 2,
                    dx, dy, 6, PURPLE, 5
                ))

    def activate_shadow_veil(self):
        """Brief near-invisibility window with heavy afterimages."""
        self.phantom_mode = True
        self.shadow_veil_timer = 90
        self.stealth_mode = True
        self.revealed_timer = 30
        for _ in range(24):
            self.particles.append(Particle(
                self.x + self.width // 2,
                self.y + self.height // 2,
                random.uniform(-4, 4),
                random.uniform(-4, 4),
                (70, 0, 90),
                28,
                4,
            ))

    def void_projectile_attack(self, count):
        """Dark orbs that briefly curve toward the player, then commit to their lane."""
        cx = self.x + self.width // 2
        cy = self.y + self.height // 2
        for i in range(count):
            angle = (math.pi * 2 * i) / max(1, count)
            orb = Projectile(cx, cy, math.cos(angle) * 3.5, math.sin(angle) * 3.5, 9, PURPLE, 6)
            orb.void_homing = True
            orb.void_homing_frames = 28
            orb.void_homing_interval = 1
            orb.void_homing_strength = 0.04
            orb.void_target_locked = False
            self.projectiles.append(orb)
                
    def movement(self):
        if not self.stealth_mode:
            self.x += math.sin(pygame.time.get_ticks() * 0.001) * 2
            self.y += math.cos(pygame.time.get_ticks() * 0.0015) * 1.5
            
            self.x = max(50, min(WIDTH - 130, self.x))
            self.y = max(50, min(HEIGHT - 200, self.y))
            self.update_rect()
            
    def update_clones(self):
        for clone in self.shadow_clones[:]:
            if not clone.update():
                self.shadow_clones.remove(clone)
            else:
                # Add clone projectiles to main projectiles list
                self.projectiles.extend(clone.projectiles)
                clone.projectiles.clear()
                
    def update_particles(self):
        for particle in self.particles[:]:
            if not particle.update():
                self.particles.remove(particle)

        # Handle homing on dedicated void projectiles.
        if self.game and self.game.player:
            tx = self.game.player.x + self.game.player.width // 2
            ty = self.game.player.y + self.game.player.height // 2
            for projectile in self.projectiles:
                if hasattr(projectile, 'void_homing') and projectile.void_homing:
                    homing_frames = getattr(projectile, "void_homing_frames", 0)
                    if homing_frames > 0 and hasattr(projectile, "steer_towards"):
                        interval = max(1, int(getattr(projectile, "void_homing_interval", 1)))
                        if homing_frames % interval == 0:
                            projectile.steer_towards(
                                tx,
                                ty,
                                desired_speed=4.4,
                                max_turn=float(getattr(projectile, "void_homing_strength", 0.04)),
                                accel=0.14,
                            )
                        projectile.void_homing_frames = homing_frames - 1
                    else:
                        projectile.void_homing = False
                        projectile.void_target_locked = True
                
    def draw(self, screen):
        # Draw particles first (behind everything)
        for particle in self.particles:
            particle.draw(screen)
            
        # Draw shadow clones
        for clone in self.shadow_clones:
            clone.draw(screen)
            
        # Draw main boss
        drew_main = False
        if not self.stealth_mode or self.revealed_timer > 0:
            if self.phantom_mode:
                alpha = 0.2 + 0.3 * max(0, self.shadow_veil_timer / 90)
            else:
                alpha = 1.0 if not self.stealth_mode else 0.3 + 0.7 * (self.revealed_timer / 60)
            old_color = self.color
            self.color = (int(old_color[0] * alpha), int(old_color[1] * alpha), int(old_color[2] * alpha))
            Boss.draw(self, screen)
            self.color = old_color
            drew_main = True

        # Keep HP visible even while fully stealthed.
        if not drew_main:
            self.health_bar_color = GREEN
            self.draw_health_bar(screen)
