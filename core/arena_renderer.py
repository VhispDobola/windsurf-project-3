import pygame
import math
import random

class ArenaRenderer:
    """Handles arena background rendering for different boss themes"""
    
    ARENA_CONFIGS = {
        "void": {"base": (8, 6, 14), "accent": (120, 70, 255)},
        "storm": {"base": (8, 12, 18), "accent": (60, 200, 255)},
        "fire": {"base": (18, 8, 6), "accent": (255, 120, 40)},
        "dragon": {"base": (18, 8, 6), "accent": (255, 120, 40)},
        "crystal": {"base": (8, 14, 18), "accent": (120, 240, 255)},
        "machine": {"base": (10, 10, 12), "accent": (200, 200, 210)},
        "virus": {"base": (6, 14, 10), "accent": (80, 255, 140)},
        "time": {"base": (10, 10, 18), "accent": (255, 220, 120)},
        "shadow": {"base": (10, 10, 10), "accent": (160, 120, 255)},
        "ice": {"base": (6, 12, 18), "accent": (150, 200, 255)},
        "lava": {"base": (18, 6, 4), "accent": (255, 80, 20)},
        "thunder": {"base": (8, 8, 16), "accent": (255, 255, 100)},
        "sentinel": {"base": (12, 10, 14), "accent": (180, 150, 200)},
        "duelist": {"base": (14, 8, 8), "accent": (220, 100, 100)},
        "core": {"base": (8, 8, 12), "accent": (150, 150, 200)},
        "default": {"base": (10, 10, 16), "accent": (255, 220, 120)}
    }
    
    @staticmethod
    def get_arena_style(boss):
        """Determine arena style based on boss name"""
        name = getattr(boss, "name", "").lower()
        if "tempest" in name:
            return "storm"
        if "abyssal" in name:
            return "void"
        if "guardian" in name:
            return "sentinel"
        if "phoenix" in name or "immortal" in name:
            return "fire"
        if "crystalline" in name or "crystal" in name:
            return "crystal"
        if "dragon" in name:
            return "dragon"
        if "cyber" in name or "machine" in name:
            return "machine"
        if "digital" in name or "plague" in name:
            return "virus"
        if "chronomancer" in name or "time" in name:
            return "time"
        if "assassin" in name:
            return "shadow"
        if "blade" in name:
            return "duelist"
        if "nexus" in name or "core" in name:
            return "core"
        if "ice" in name or "tyrant" in name:
            return "ice"
        if "magma" in name or "sovereign" in name:
            return "lava"
        if "thunder" in name:
            return "thunder"
        return "default"
    
    @classmethod
    def draw_arena_background(cls, screen, arena_style, arena_seed):
        """Draw the arena background with specified style and seed"""
        rnd = random.Random(arena_seed)
        config = cls.ARENA_CONFIGS.get(arena_style, cls.ARENA_CONFIGS["default"])
        base = config["base"]
        accent = config["accent"]
        
        screen.fill(base)
        
        # Draw style-specific effects
        if arena_style == "storm":
            cls._draw_storm_effects(screen, rnd, accent)
        elif arena_style == "void":
            cls._draw_void_effects(screen, rnd, accent)
        elif arena_style == "crystal":
            cls._draw_crystal_effects(screen, rnd, accent)
        elif arena_style == "machine":
            cls._draw_machine_effects(screen, rnd, accent)
        elif arena_style in ["fire", "dragon"]:
            cls._draw_fire_effects(screen, rnd, accent)
        elif arena_style == "ice":
            cls._draw_ice_effects(screen, rnd, accent)
        elif arena_style == "lava":
            cls._draw_lava_effects(screen, rnd, accent)
        elif arena_style == "thunder":
            cls._draw_thunder_effects(screen, rnd, accent)
        
        # Draw common grid and particles
        cls._draw_grid(screen, base)
        cls._draw_particles(screen, rnd, accent)
        cls._draw_frame(screen)
    
    @staticmethod
    def _draw_storm_effects(screen, rnd, accent):
        """Draw storm-themed lightning effects"""
        screen_width = screen.get_width()
        screen_height = screen.get_height()
        for i in range(12):
            x1 = rnd.randint(0, screen_width)
            y1 = rnd.randint(0, screen_height)
            x2 = x1 + rnd.randint(-220, 220)
            y2 = y1 + rnd.randint(-220, 220)
            pygame.draw.line(screen, accent, (x1, y1), (x2, y2), 2)
    
    @staticmethod
    def _draw_void_effects(screen, rnd, accent):
        """Draw void-themed ring effects"""
        screen_width = screen.get_width()
        screen_height = screen.get_height()
        for i in range(5):
            cx = rnd.randint(120, screen_width - 120)
            cy = rnd.randint(120, screen_height - 120)
            for r in range(40, 200, 28):
                a = max(10, 70 - r // 3)
                ring = pygame.Surface((r * 2 + 2, r * 2 + 2), pygame.SRCALPHA)
                pygame.draw.circle(ring, (*accent, a), (r + 1, r + 1), r, 3)
                screen.blit(ring, (cx - r - 1, cy - r - 1))
    
    @staticmethod
    def _draw_crystal_effects(screen, rnd, accent):
        """Draw crystal-themed triangle effects"""
        screen_width = screen.get_width()
        screen_height = screen.get_height()
        for _ in range(18):
            x = rnd.randint(0, screen_width)
            y = rnd.randint(0, screen_height)
            s = rnd.randint(20, 70)
            pts = [(x, y), (x + s, y + s // 3), (x + s // 2, y + s)]
            pygame.draw.polygon(screen, accent, pts, 2)
    
    @staticmethod
    def _draw_machine_effects(screen, rnd, accent):
        """Draw machine-themed rectangle effects"""
        screen_width = screen.get_width()
        screen_height = screen.get_height()
        for _ in range(26):
            x = rnd.randint(30, screen_width - 130)
            y = rnd.randint(30, screen_height - 130)
            w = rnd.randint(60, 180)
            h = rnd.randint(20, 90)
            pygame.draw.rect(screen, (30, 30, 35), (x, y, w, h), border_radius=6)
            pygame.draw.rect(screen, (70, 70, 85), (x, y, w, h), 2, border_radius=6)
    
    @staticmethod
    def _draw_fire_effects(screen, rnd, accent):
        """Draw fire-themed ember effects"""
        screen_width = screen.get_width()
        screen_height = screen.get_height()
        for _ in range(60):
            x = rnd.randint(0, screen_width)
            y = rnd.randint(0, screen_height)
            r = rnd.randint(2, 5)
            a = rnd.randint(18, 60)
            ember = pygame.Surface((r * 4, r * 4), pygame.SRCALPHA)
            pygame.draw.circle(ember, (*accent, a), (r * 2, r * 2), r)
            screen.blit(ember, (x - r * 2, y - r * 2))
    
    @staticmethod
    def _draw_ice_effects(screen, rnd, accent):
        """Draw ice-themed snowflake effects"""
        screen_width = screen.get_width()
        screen_height = screen.get_height()
        for _ in range(25):
            x = rnd.randint(0, screen_width)
            y = rnd.randint(0, screen_height)
            size = rnd.randint(10, 30)
            snowflake = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
            for i in range(6):
                angle = i * 60
                end_x = size + int(size * 0.8 * math.cos(math.radians(angle)))
                end_y = size + int(size * 0.8 * math.sin(math.radians(angle)))
                pygame.draw.line(snowflake, (*accent, 100), (size, size), (end_x, end_y), 1)
            screen.blit(snowflake, (x - size, y - size))
    
    @staticmethod
    def _draw_lava_effects(screen, rnd, accent):
        """Draw lava-themed bubble effects"""
        screen_width = screen.get_width()
        screen_height = screen.get_height()
        for _ in range(40):
            x = rnd.randint(0, screen_width)
            y = rnd.randint(0, screen_height)
            r = rnd.randint(3, 8)
            a = rnd.randint(30, 80)
            lava_bubble = pygame.Surface((r * 4, r * 4), pygame.SRCALPHA)
            pygame.draw.circle(lava_bubble, (*accent, a), (r * 2, r * 2), r)
            screen.blit(lava_bubble, (x - r * 2, y - r * 2))
    
    @staticmethod
    def _draw_thunder_effects(screen, rnd, accent):
        """Draw thunder-themed lightning bolt effects"""
        screen_width = screen.get_width()
        screen_height = screen.get_height()
        for _ in range(8):
            x1 = rnd.randint(0, screen_width)
            y1 = 0
            x2 = x1 + rnd.randint(-100, 100)
            y2 = screen_height
            mid_x = (x1 + x2) // 2 + rnd.randint(-50, 50)
            mid_y = screen_height // 2
            pygame.draw.line(screen, accent, (x1, y1), (mid_x, mid_y), 2)
            pygame.draw.line(screen, accent, (mid_x, mid_y), (x2, y2), 2)
    
    @staticmethod
    def _draw_grid(screen, base):
        """Draw background grid"""
        screen_width = screen.get_width()
        screen_height = screen.get_height()
        grid = 50
        for x in range(0, screen_width + 1, grid):
            c = (base[0] + 6, base[1] + 6, base[2] + 10)
            pygame.draw.line(screen, c, (x, 0), (x, screen_height), 1)
        for y in range(0, screen_height + 1, grid):
            c = (base[0] + 6, base[1] + 6, base[2] + 10)
            pygame.draw.line(screen, c, (0, y), (screen_width, y), 1)
    
    @staticmethod
    def _draw_particles(screen, rnd, accent):
        """Draw ambient particles"""
        screen_width = screen.get_width()
        screen_height = screen.get_height()
        for _ in range(70):
            px = rnd.randint(0, screen_width)
            py = rnd.randint(0, screen_height)
            r = rnd.randint(1, 3)
            a = rnd.randint(18, 70)
            dot = pygame.Surface((r * 2 + 2, r * 2 + 2), pygame.SRCALPHA)
            pygame.draw.circle(dot, (*accent, a), (r + 1, r + 1), r)
            screen.blit(dot, (px - r, py - r))
    
    @staticmethod
    def _draw_frame(screen):
        """Draw arena frame"""
        screen_width = screen.get_width()
        screen_height = screen.get_height()
        frame = pygame.Rect(18, 18, screen_width - 36, screen_height - 36)
        pygame.draw.rect(screen, (0, 0, 0), frame.inflate(10, 10), border_radius=18)
        pygame.draw.rect(screen, (30, 30, 40), frame, border_radius=16)
