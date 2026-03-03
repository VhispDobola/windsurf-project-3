import pygame
import math
import random
from config.constants import WIDTH, HEIGHT
from config.constants import init_pygame, WHITE, YELLOW

class BossTitleAnimator:
    def __init__(self):
        self.animation_timer = 0
        self.animation_duration = 180  # 3 seconds at 60 FPS
        self.current_boss = ""
        self.animation_phase = "teleport_in"  # teleport_in, display, teleport_out
        self.particles = []
        self.title_effects = []
        
        # Theme-specific colors and effects
        self.boss_themes = {
            "crystalline": {
                "colors": [(150, 150, 255), (200, 200, 255), (100, 100, 255)],
                "particle_color": (150, 150, 255),
                "effect": "crystal_shards"
            },
            "eternal": {
                "colors": [(255, 50, 0), (255, 100, 0), (200, 50, 0)],
                "particle_color": (255, 100, 0),
                "effect": "fire_breath"
            },
            "magma": {
                "colors": [(255, 100, 0), (255, 50, 0), (200, 0, 0)],
                "particle_color": (255, 50, 0),
                "effect": "lava_bubbles"
            },
            "abyssal": {
                "colors": [(128, 0, 128), (50, 0, 50), (200, 0, 200)],
                "particle_color": (128, 0, 128),
                "effect": "void_particles"
            },
            "chronomancer": {
                "colors": [(0, 255, 255), (100, 200, 255), (0, 150, 255)],
                "particle_color": (0, 255, 255),
                "effect": "clock_gears"
            },
            "immortal": {
                "colors": [(255, 150, 255), (255, 100, 200), (255, 200, 100)],
                "particle_color": (255, 150, 255),
                "effect": "phoenix_feathers"
            },
            "digital": {
                "colors": [(0, 255, 0), (0, 200, 0), (100, 255, 100)],
                "particle_color": (0, 255, 0),
                "effect": "digital_glitch"
            },
            "tempest": {
                "colors": [(100, 100, 255), (150, 150, 255), (50, 50, 200)],
                "particle_color": (100, 100, 255),
                "effect": "lightning_bolts"
            },
            "thunder": {
                "colors": [(255, 255, 0), (255, 200, 0), (200, 200, 100)],
                "particle_color": (255, 255, 0),
                "effect": "electric_arcs"
            },
            "void assassin": {
                "colors": [(50, 0, 50), (100, 0, 100), (0, 0, 0)],
                "particle_color": (100, 0, 100),
                "effect": "shadow_daggers"
            },
            "eternal guardian": {
                "colors": [(200, 100, 255), (150, 50, 200), (255, 150, 255)],
                "particle_color": (200, 100, 255),
                "effect": "energy_orbs"
            },
            "cyber": {
                "colors": [(255, 0, 255), (200, 0, 200), (100, 0, 100)],
                "particle_color": (255, 0, 255),
                "effect": "matrix_rain"
            },
            "ice": {
                "colors": [(100, 200, 255), (150, 220, 255), (50, 150, 200)],
                "particle_color": (100, 200, 255),
                "effect": "snow_flakes"
            },
            "blade": {
                "colors": [(255, 100, 0), (255, 150, 50), (200, 100, 0)],
                "particle_color": (255, 100, 0),
                "effect": "blade_sparks"
            },
            "nexus": {
                "colors": [(255, 0, 0), (200, 0, 0), (255, 100, 100)],
                "particle_color": (255, 0, 0),
                "effect": "energy_pulses"
            },
            "virus queen": {
                "colors": [(0, 255, 0), (0, 200, 0), (100, 255, 100)],
                "particle_color": (0, 255, 0),
                "effect": "digital_glitch"
            }
        }
    
    def start_animation(self, boss_name):
        self.current_boss = boss_name
        self.animation_timer = 0
        self.animation_phase = "teleport_in"
        self.particles = []
        self.title_effects = []
        self._create_theme_effects()
    
    def _create_theme_effects(self):
        boss_lower = self.current_boss.lower()
        theme_key = None
        
        # Find matching theme
        for key in self.boss_themes:
            if key in boss_lower:
                theme_key = key
                break
        
        if not theme_key:
            theme_key = "default"
        
        theme = self.boss_themes.get(theme_key, self.boss_themes["crystalline"])
        
        # Create particles based on theme
        if theme["effect"] == "crystal_shards":
            for _ in range(20):
                self.particles.append({
                    "x": random.randint(0, WIDTH),
                    "y": random.randint(-50, -10),
                    "vx": random.uniform(-2, 2),
                    "vy": random.uniform(2, 5),
                    "size": random.randint(2, 6),
                    "color": theme["particle_color"],
                    "lifetime": random.randint(60, 120),
                    "type": "crystal"
                })
        
        elif theme["effect"] == "fire_breath":
            for _ in range(15):
                self.particles.append({
                    "x": random.randint(0, WIDTH),
                    "y": HEIGHT + 20,
                    "vx": random.uniform(-1, 1),
                    "vy": random.uniform(-4, -2),
                    "size": random.randint(3, 8),
                    "color": theme["particle_color"],
                    "lifetime": random.randint(80, 140),
                    "type": "fire"
                })
        
        elif theme["effect"] == "lava_bubbles":
            for _ in range(12):
                self.particles.append({
                    "x": random.randint(0, WIDTH),
                    "y": HEIGHT + 30,
                    "vx": random.uniform(-0.5, 0.5),
                    "vy": random.uniform(-3, -1),
                    "size": random.randint(4, 10),
                    "color": theme["particle_color"],
                    "lifetime": random.randint(100, 180),
                    "type": "bubble"
                })
        
        elif theme["effect"] == "void_particles":
            for _ in range(25):
                angle = random.uniform(0, math.pi * 2)
                speed = random.uniform(1, 3)
                self.particles.append({
                    "x": WIDTH // 2 + math.cos(angle) * 200,
                    "y": HEIGHT // 2 + math.sin(angle) * 150,
                    "vx": -math.cos(angle) * speed,
                    "vy": -math.sin(angle) * speed,
                    "size": random.randint(2, 5),
                    "color": theme["particle_color"],
                    "lifetime": random.randint(90, 150),
                    "type": "void"
                })
        
        elif theme["effect"] == "clock_gears":
            for _ in range(8):
                self.particles.append({
                    "x": random.randint(50, WIDTH - 50),
                    "y": random.randint(50, HEIGHT - 50),
                    "angle": 0,
                    "rotation_speed": random.uniform(0.02, 0.05),
                    "size": random.randint(15, 25),
                    "color": theme["particle_color"],
                    "lifetime": 200,
                    "type": "gear"
                })
        
        elif theme["effect"] == "phoenix_feathers":
            for _ in range(18):
                self.particles.append({
                    "x": random.randint(0, WIDTH),
                    "y": random.randint(-30, 0),
                    "vx": random.uniform(-1, 1),
                    "vy": random.uniform(1, 3),
                    "size": random.randint(3, 7),
                    "color": theme["particle_color"],
                    "lifetime": random.randint(100, 160),
                    "type": "feather"
                })
        
        elif theme["effect"] == "digital_glitch":
            for _ in range(30):
                self.particles.append({
                    "x": random.randint(0, WIDTH),
                    "y": random.randint(0, HEIGHT),
                    "char": random.choice(["01", "10", "11", "00"]),
                    "lifetime": random.randint(20, 60),
                    "type": "digital"
                })
        
        elif theme["effect"] == "lightning_bolts":
            for _ in range(6):
                self.particles.append({
                    "x": random.randint(100, WIDTH - 100),
                    "y": 0,
                    "target_y": HEIGHT,
                    "lifetime": random.randint(10, 30),
                    "type": "lightning"
                })
        
        elif theme["effect"] == "electric_arcs":
            for _ in range(10):
                self.particles.append({
                    "x": random.randint(0, WIDTH),
                    "y": random.randint(0, HEIGHT),
                    "angle": random.uniform(0, math.pi * 2),
                    "length": random.randint(20, 40),
                    "lifetime": random.randint(15, 40),
                    "type": "arc"
                })
        
        elif theme["effect"] == "shadow_daggers":
            for _ in range(12):
                self.particles.append({
                    "x": random.randint(0, WIDTH),
                    "y": random.randint(-20, 0),
                    "vx": random.uniform(-2, 2),
                    "vy": random.uniform(2, 4),
                    "size": random.randint(8, 15),
                    "color": theme["particle_color"],
                    "lifetime": random.randint(80, 120),
                    "type": "dagger"
                })
        
        elif theme["effect"] == "energy_orbs":
            for _ in range(15):
                self.particles.append({
                    "x": random.randint(0, WIDTH),
                    "y": random.randint(0, HEIGHT),
                    "vx": random.uniform(-1, 1),
                    "vy": random.uniform(-1, 1),
                    "size": random.randint(5, 12),
                    "color": theme["particle_color"],
                    "lifetime": random.randint(100, 180),
                    "type": "orb"
                })
        
        elif theme["effect"] == "matrix_rain":
            for _ in range(40):
                self.particles.append({
                    "x": random.randint(0, WIDTH),
                    "y": random.randint(-HEIGHT, 0),
                    "vy": random.uniform(3, 6),
                    "char": random.choice(["0", "1"]),
                    "lifetime": random.randint(60, 120),
                    "type": "matrix"
                })
        
        elif theme["effect"] == "snow_flakes":
            for _ in range(30):
                self.particles.append({
                    "x": random.randint(0, WIDTH),
                    "y": random.randint(-HEIGHT, 0),
                    "vx": random.uniform(-1, 1),
                    "vy": random.uniform(1, 3),
                    "size": random.randint(2, 6),
                    "color": theme["particle_color"],
                    "lifetime": random.randint(120, 200),
                    "type": "snow"
                })
        
        elif theme["effect"] == "blade_sparks":
            for _ in range(20):
                self.particles.append({
                    "x": random.randint(0, WIDTH),
                    "y": random.randint(-20, HEIGHT + 20),
                    "vx": random.uniform(-3, 3),
                    "vy": random.uniform(-2, 2),
                    "size": random.randint(1, 4),
                    "color": theme["particle_color"],
                    "lifetime": random.randint(40, 80),
                    "type": "spark"
                })
        
        elif theme["effect"] == "energy_pulses":
            for _ in range(10):
                self.particles.append({
                    "x": random.randint(0, WIDTH),
                    "y": random.randint(0, HEIGHT),
                    "radius": 0,
                    "max_radius": random.randint(30, 60),
                    "growth": random.uniform(1, 2),
                    "color": theme["particle_color"],
                    "lifetime": random.randint(60, 100),
                    "type": "pulse"
                })
    
    def update(self):
        self.animation_timer += 1
        
        # Update particles
        for particle in self.particles[:]:
            particle["lifetime"] -= 1
            
            if particle["lifetime"] <= 0:
                self.particles.remove(particle)
                continue
            
            # Update particle position based on type
            if particle["type"] in ["crystal", "fire", "bubble", "void", "feather", "dagger", "spark"]:
                particle["x"] += particle["vx"]
                particle["y"] += particle["vy"]
                
            elif particle["type"] == "gear":
                particle["angle"] += particle["rotation_speed"]
                
            elif particle["type"] == "digital":
                if particle["lifetime"] % 10 == 0:
                    particle["x"] = random.randint(0, WIDTH)
                    particle["y"] = random.randint(0, HEIGHT)
                    
            elif particle["type"] == "lightning":
                if particle["lifetime"] % 5 == 0:
                    particle["x"] = random.randint(100, WIDTH - 100)
                    
            elif particle["type"] == "arc":
                particle["angle"] += 0.1
                particle["x"] += math.cos(particle["angle"]) * 2
                particle["y"] += math.sin(particle["angle"]) * 2
                
            elif particle["type"] in ["orb", "snow"]:
                particle["x"] += particle["vx"]
                particle["y"] += particle["vy"]
                particle["vx"] *= 0.98
                particle["vy"] *= 0.98
                
            elif particle["type"] == "matrix":
                particle["y"] += particle["vy"]
                
            elif particle["type"] == "pulse":
                particle["radius"] += particle["growth"]
                if particle["radius"] > particle["max_radius"]:
                    particle["radius"] = 0
        
        # Update animation phase
        if self.animation_timer >= self.animation_duration:
            if self.animation_phase == "teleport_in":
                self.animation_phase = "display"
                self.animation_timer = 0
            elif self.animation_phase == "display":
                self.animation_phase = "teleport_out"
                self.animation_timer = 0
    
    def draw(self, screen, font_large, font_medium):
        if self.animation_phase == "teleport_in":
            self._draw_teleport_in(screen, font_large)
        elif self.animation_phase == "display":
            self._draw_display(screen, font_large, font_medium)
        elif self.animation_phase == "teleport_out":
            self._draw_teleport_out(screen, font_large)
        
        # Draw particles
        self._draw_particles(screen)
    
    def _draw_teleport_in(self, screen, font):
        progress = self.animation_timer / 60  # First second
        
        # Teleport effect - title appears from random positions
        for i in range(5):
            offset_x = random.randint(-200, 200) * (1 - progress)
            offset_y = random.randint(-150, 150) * (1 - progress)
            
            alpha = int(255 * (1 - progress))
            color = (*self._get_theme_color()[:3], alpha) if len(self._get_theme_color()) == 4 else self._get_theme_color()
            
            text = font.render(self.current_boss, True, color)
            text_rect = text.get_rect(center=(screen.get_width() // 2 + offset_x, screen.get_height() // 2 + offset_y))
            screen.blit(text, text_rect)
        
        # Main title fades in
        main_alpha = int(255 * progress)
        main_color = (*self._get_theme_color()[:3], main_alpha) if len(self._get_theme_color()) == 4 else self._get_theme_color()
        
        main_text = font.render(self.current_boss, True, main_color)
        main_rect = main_text.get_rect(center=(screen.get_width() // 2, screen.get_height() // 2))
        screen.blit(main_text, main_rect)
    
    def _draw_display(self, screen, font_large, font_medium):
        # Pulsing, glowing title
        pulse = math.sin(self.animation_timer * 0.05) * 0.3 + 0.7
        
        # Multiple layers for glow effect
        for i in range(3):
            scale = 1.0 + i * 0.05
            alpha = int(100 * pulse * (1 - i * 0.3))
            color = (*self._get_theme_color()[:3], alpha) if len(self._get_theme_color()) == 4 else self._get_theme_color()
            
            glow_font = pygame.font.Font(None, int(56 * scale))
            text = glow_font.render(self.current_boss, True, color)
            text_rect = text.get_rect(center=(screen.get_width() // 2, screen.get_height() // 2))
            screen.blit(text, text_rect)
        
        # Main title
        main_color = self._get_theme_color()
        main_text = font_large.render(self.current_boss, True, main_color)
        main_rect = main_text.get_rect(center=(screen.get_width() // 2, screen.get_height() // 2))
        screen.blit(main_text, main_rect)
        
        # "Get Ready!" text
        ready_alpha = min(255, self.animation_timer * 2)
        ready_color = (*YELLOW[:3], ready_alpha) if len(YELLOW) == 3 else YELLOW
        ready = font_medium.render("GET READY!", True, ready_color)
        ready_rect = ready.get_rect(center=(screen.get_width() // 2, screen.get_height() // 2 + 80))
        screen.blit(ready, ready_rect)
    
    def _draw_teleport_out(self, screen, font):
        progress = self.animation_timer / 60  # First second
        
        # Title breaks apart and teleports away
        for i in range(8):
            angle = (math.pi * 2 * i) / 8
            distance = progress * 300
            offset_x = math.cos(angle) * distance
            offset_y = math.sin(angle) * distance
            
            alpha = int(255 * (1 - progress))
            color = (*self._get_theme_color()[:3], alpha) if len(self._get_theme_color()) == 4 else self._get_theme_color()
            
            text = font.render(self.current_boss, True, color)
            text_rect = text.get_rect(center=(screen.get_width() // 2 + offset_x, screen.get_height() // 2 + offset_y))
            screen.blit(text, text_rect)
    
    def _draw_particles(self, screen):
        for particle in self.particles:
            alpha = min(255, particle["lifetime"] * 2)
            
            if particle["type"] == "crystal":
                color = (*particle.get("color", [255, 255, 255])[:3], alpha) if len(particle.get("color", [255, 255, 255])) == 3 else particle.get("color", [255, 255, 255])
                pygame.draw.polygon(screen, color, [
                    (particle["x"], particle["y"] - particle["size"]),
                    (particle["x"] - particle["size"], particle["y"] + particle["size"]),
                    (particle["x"] + particle["size"], particle["y"] + particle["size"])
                ])
                
            elif particle["type"] == "fire":
                color = (*particle.get("color", [255, 255, 255])[:3], alpha) if len(particle.get("color", [255, 255, 255])) == 3 else particle.get("color", [255, 255, 255])
                pygame.draw.circle(screen, color, (int(particle["x"]), int(particle["y"])), particle["size"])
                
            elif particle["type"] == "bubble":
                color = (*particle.get("color", [255, 255, 255])[:3], alpha) if len(particle.get("color", [255, 255, 255])) == 3 else particle.get("color", [255, 255, 255])
                pygame.draw.circle(screen, color, (int(particle["x"]), int(particle["y"])), particle["size"], 2)
                
            elif particle["type"] == "void":
                color = (*particle.get("color", [255, 255, 255])[:3], alpha) if len(particle.get("color", [255, 255, 255])) == 3 else particle.get("color", [255, 255, 255])
                pygame.draw.circle(screen, color, (int(particle["x"]), int(particle["y"])), particle["size"])
                
            elif particle["type"] == "gear":
                color = (*particle.get("color", [255, 255, 255])[:3], alpha) if len(particle.get("color", [255, 255, 255])) == 3 else particle.get("color", [255, 255, 255])
                # Draw rotating gear
                center_x, center_y = int(particle["x"]), int(particle["y"])
                for i in range(6):
                    angle = particle["angle"] + (math.pi * 2 * i) / 6
                    x = center_x + math.cos(angle) * particle["size"]
                    y = center_y + math.sin(angle) * particle["size"]
                    pygame.draw.circle(screen, color, (int(x), int(y)), 3)
                
            elif particle["type"] == "feather":
                color = (*particle.get("color", [255, 255, 255])[:3], alpha) if len(particle.get("color", [255, 255, 255])) == 3 else particle.get("color", [255, 255, 255])
                points = [
                    (particle["x"], particle["y"] - particle["size"]),
                    (particle["x"] - particle["size"] // 2, particle["y"]),
                    (particle["x"] + particle["size"] // 2, particle["y"])
                ]
                pygame.draw.polygon(screen, color, points)
                
            elif particle["type"] == "digital":
                color = (*particle.get("color", [255, 255, 255])[:3], alpha) if len(particle.get("color", [255, 255, 255])) == 3 else particle.get("color", [255, 255, 255])
                font = pygame.font.Font(None, 20)
                text = font.render(particle["char"], True, color)
                screen.blit(text, (particle["x"], particle["y"]))
                
            elif particle["type"] == "lightning":
                color = (*particle.get("color", [255, 255, 255])[:3], alpha) if len(particle.get("color", [255, 255, 255])) == 3 else particle.get("color", [255, 255, 255])
                pygame.draw.line(screen, color, (particle["x"], 0), (particle["x"], particle["target_y"]), 2)
                
            elif particle["type"] == "arc":
                color = (*particle.get("color", [255, 255, 255])[:3], alpha) if len(particle.get("color", [255, 255, 255])) == 3 else particle.get("color", [255, 255, 255])
                end_x = particle["x"] + math.cos(particle["angle"]) * particle["length"]
                end_y = particle["y"] + math.sin(particle["angle"]) * particle["length"]
                pygame.draw.line(screen, color, (particle["x"], particle["y"]), (end_x, end_y), 2)
                
            elif particle["type"] == "dagger":
                color = (*particle.get("color", [255, 255, 255])[:3], alpha) if len(particle.get("color", [255, 255, 255])) == 3 else particle.get("color", [255, 255, 255])
                # Draw dagger shape
                points = [
                    (particle["x"], particle["y"] - particle["size"]),
                    (particle["x"] - particle["size"] // 3, particle["y"]),
                    (particle["x"], particle["y"] + particle["size"]),
                    (particle["x"] + particle["size"] // 3, particle["y"])
                ]
                pygame.draw.polygon(screen, color, points)
                
            elif particle["type"] == "orb":
                color = (*particle.get("color", [255, 255, 255])[:3], alpha) if len(particle.get("color", [255, 255, 255])) == 3 else particle.get("color", [255, 255, 255])
                pygame.draw.circle(screen, color, (int(particle["x"]), int(particle["y"])), particle["size"], 2)
                
            elif particle["type"] == "matrix":
                color = (*particle.get("color", [255, 255, 255])[:3], alpha) if len(particle.get("color", [255, 255, 255])) == 3 else particle.get("color", [255, 255, 255])
                font = pygame.font.Font(None, 16)
                text = font.render(particle["char"], True, color)
                screen.blit(text, (particle["x"], particle["y"]))
                
            elif particle["type"] == "snow":
                color = (*particle.get("color", [255, 255, 255])[:3], alpha) if len(particle.get("color", [255, 255, 255])) == 3 else particle.get("color", [255, 255, 255])
                # Draw snowflake
                for i in range(6):
                    angle = (math.pi * 2 * i) / 6
                    x = particle["x"] + math.cos(angle) * particle["size"]
                    y = particle["y"] + math.sin(angle) * particle["size"]
                    pygame.draw.line(screen, color, (particle["x"], particle["y"]), (x, y), 1)
                
            elif particle["type"] == "spark":
                color = (*particle.get("color", [255, 255, 255])[:3], alpha) if len(particle.get("color", [255, 255, 255])) == 3 else particle.get("color", [255, 255, 255])
                pygame.draw.circle(screen, color, (int(particle["x"]), int(particle["y"])), particle["size"])
                
            elif particle["type"] == "pulse":
                color = (*particle.get("color", [255, 255, 255])[:3], alpha) if len(particle.get("color", [255, 255, 255])) == 3 else particle.get("color", [255, 255, 255])
                if particle["radius"] > 0:
                    pygame.draw.circle(screen, color, (int(particle["x"]), int(particle["y"])), int(particle["radius"]), 2)
    
    def _get_theme_color(self):
        boss_lower = self.current_boss.lower()
        
        # Special case for Virus Queen (keep as requested)
        if "virus" in boss_lower and "queen" in boss_lower:
            return (0, 255, 0)  # Green for Virus Queen
        
        for key, theme in self.boss_themes.items():
            if key in boss_lower:
                return theme["colors"][0]  # Return primary color
        
        return (255, 255, 255)  # Default white
    
    def is_animation_complete(self):
        return self.animation_phase == "teleport_out" and self.animation_timer >= 60
