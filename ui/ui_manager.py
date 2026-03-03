import pygame
from config.constants import WHITE, YELLOW, GREEN, RED
from .boss_title_animator import BossTitleAnimator
from core.render_system import RenderSystem


class UIManager:
    def __init__(self, render_system=None):
        self.render_system = render_system
        self.font_large = self._get_font(56)
        self.font_medium = self._get_font(34)
        self.font_small = self._get_font(22)
        self.font_tiny = self._get_font(18)
        self.boss_animator = BossTitleAnimator()
    
    def _get_font(self, size):
        """Get font from render system cache or create new one"""
        if self.render_system:
            return self.render_system.get_font(size)
        return pygame.font.Font(None, size)
        
    def _draw_center_text(self, screen, text, font, y, color):
        surf = font.render(text, True, color)
        rect = surf.get_rect(center=(screen.get_width() // 2, y))
        screen.blit(surf, rect)

    def _draw_panel(self, screen, rect, fill_color, border_color):
        shadow = rect.move(6, 6)
        pygame.draw.rect(screen, (0, 0, 0), shadow, border_radius=14)
        pygame.draw.rect(screen, border_color, rect.inflate(6, 6), border_radius=16)
        pygame.draw.rect(screen, fill_color, rect, border_radius=14)

    def draw_menu(self, screen):
        screen_width = screen.get_width()
        screen_height = screen.get_height()

        self._draw_center_text(screen, "BOSS RUSH", self.font_large, screen_height // 3, WHITE)
        self._draw_center_text(screen, "Press SPACE to Start", self.font_medium, screen_height // 2, YELLOW)
        
        controls = [
            "WASD/Arrows: Move",
            "SHIFT: Dash",
            "SPACE: Shoot"
        ]
        
        y = int(screen_height * 0.586)
        for control in controls:
            text = self.font_small.render(control, True, WHITE)
            text_rect = text.get_rect(center=(screen_width // 2, y))
            screen.blit(text, text_rect)
            y += 30
            
    def draw_boss_intro(self, screen, boss_name, hint_text=None):
        # Start animated boss intro
        if not self.boss_animator.current_boss or self.boss_animator.current_boss != boss_name:
            self.boss_animator.start_animation(boss_name)
        
        # Update and draw animation
        self.boss_animator.update()
        self.boss_animator.draw(screen, self.font_large, self.font_medium)

        if hint_text:
            hint_color = (220, 220, 220)
            hint_surf = self.font_small.render(hint_text, True, hint_color)
            hint_rect = hint_surf.get_rect(center=(screen.get_width() // 2, screen.get_height() // 2 + 130))
            screen.blit(hint_surf, hint_rect)
        
        return self.boss_animator.is_animation_complete()
        
    def draw_multiple_health_bars(self, screen, bosses):
        """Draw health bars for multiple bosses"""
        if not bosses:
            return

        screen_width = screen.get_width()
            
        bar_width = 250
        bar_height = 6
        bar_spacing = 40
        total_width = (bar_width * len(bosses)) + (bar_spacing * (len(bosses) - 1))
        start_x = (screen_width - total_width) // 2
        bar_y = 30
        
        font = pygame.font.Font(None, 20)
        
        for i, boss in enumerate(bosses):
            x = start_x + i * (bar_width + bar_spacing)
            
            # Boss name
            name_text = boss.name
            # Special handling for Virus Queen splits to show cleaner names
            if "The Virus Queen" in boss.name:
                if "(Original)" in boss.name:
                    name_text = "Virus Queen (1)"
                elif "(Split)" in boss.name:
                    name_text = "Virus Queen (2)"
                else:
                    name_text = "Virus Queen"
                    
            if hasattr(boss, 'is_weakened') and boss.is_weakened:
                name_text += " (Weakened)"
            
            name_surf = font.render(name_text, True, WHITE)
            name_rect = name_surf.get_rect(center=(x + bar_width // 2, bar_y - 10))
            screen.blit(name_surf, name_rect)
            
            # Health bar background
            pygame.draw.rect(screen, RED, (x, bar_y, bar_width, bar_height))
            
            # Health fill
            health_percentage = max(0, boss.health / boss.max_health)
            health_color = getattr(boss, 'health_bar_color', GREEN)
            pygame.draw.rect(screen, health_color, (x, bar_y, bar_width * health_percentage, bar_height))

            # Phase markers
            marker_color = (30, 30, 30)
            for threshold in (0.6, 0.3):
                marker_x = x + int(bar_width * threshold)
                pygame.draw.line(screen, marker_color, (marker_x, bar_y - 2), (marker_x, bar_y + bar_height + 2), 2)
        
    def draw_victory(self, screen, score, time):
        screen_width = screen.get_width()
        screen_height = screen.get_height()
        
        victory = self.font_large.render("VICTORY!", True, GREEN)
        victory_rect = victory.get_rect(center=(screen_width // 2, screen_height // 3))
        screen.blit(victory, victory_rect)
        
        score_text = self.font_medium.render(f"Score: {score}", True, WHITE)
        score_rect = score_text.get_rect(center=(screen_width // 2, screen_height // 2))
        screen.blit(score_text, score_rect)
        
        time_text = self.font_medium.render(f"Time: {time:.1f}s", True, WHITE)
        time_rect = time_text.get_rect(center=(screen_width // 2, screen_height // 2 + 40))
        screen.blit(time_text, time_rect)
        
        continue_text = self.font_small.render("Press SPACE to Continue", True, YELLOW)
        continue_rect = continue_text.get_rect(center=(screen_width // 2, screen_height // 2 + 100))
        screen.blit(continue_text, continue_rect)
        
    def draw_game_over(self, screen):
        screen_width = screen.get_width()
        screen_height = screen.get_height()
        
        game_over = self.font_large.render("GAME OVER", True, RED)
        game_over_rect = game_over.get_rect(center=(screen_width // 2, screen_height // 2))
        screen.blit(game_over, game_over_rect)
        
        restart = self.font_small.render("Press R to Restart", True, YELLOW)
        restart_rect = restart.get_rect(center=(screen_width // 2, screen_height // 2 + 60))
        screen.blit(restart, restart_rect)

    def draw_upgrade_screen(self, screen, upgrades, hovered_index=-1):
        screen_width = screen.get_width()
        screen_height = screen.get_height()
        
        overlay = pygame.Surface((screen_width, screen_height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 140))
        screen.blit(overlay, (0, 0))

        self._draw_center_text(screen, "CHOOSE UPGRADE", self.font_large, screen_height // 6, YELLOW)
        self._draw_center_text(screen, "Press 1-4 or Click to pick", self.font_small, screen_height // 6 + 42, WHITE)

        cards = upgrades[:4]
        card_w = 240
        card_h = 280
        gap = 30
        total_w = (card_w * 4) + (gap * 3)
        start_x = (screen_width - total_w) // 2
        y = screen_height // 2 - card_h // 2 + 30

        for i, up in enumerate(cards):
            x = start_x + i * (card_w + gap)
            rect = pygame.Rect(x, y, card_w, card_h)

            # Hover effects
            is_hovered = (i == hovered_index)
            scale = 1.08 if is_hovered else 1.0
            
            if is_hovered:
                # Scale up card for hover
                scaled_w = int(card_w * scale)
                scaled_h = int(card_h * scale)
                scaled_x = x - (scaled_w - card_w) // 2
                scaled_y = y - (scaled_h - card_h) // 2
                scaled_rect = pygame.Rect(scaled_x, scaled_y, scaled_w, scaled_h)
                
                # Enhanced glow effect
                glow_surf = pygame.Surface((scaled_w + 30, scaled_h + 30), pygame.SRCALPHA)
                pygame.draw.rect(glow_surf, (100, 150, 255, 60), glow_surf.get_rect(), border_radius=20)
                pygame.draw.rect(glow_surf, (200, 220, 255, 40), glow_surf.get_rect(), border_radius=16)
                screen.blit(glow_surf, (scaled_x - 15, scaled_y - 15))
                
                draw_rect = scaled_rect
                accent = (120, 100, 200)
                fill = (40, 35, 60)
                border = (180, 160, 255)
            else:
                draw_rect = rect
                accent = (80, 70, 100)
                fill = (25, 22, 35)
                border = (120, 110, 150)
                
            self._draw_panel(screen, draw_rect, fill, border)

            # Header
            header = pygame.Rect(draw_rect.x + 16, draw_rect.y + 16, draw_rect.width - 32, 40)
            pygame.draw.rect(screen, accent, header, border_radius=12)
            
            # Key indicator
            key_bg = pygame.Rect(draw_rect.x + 12, draw_rect.y + 20, 24, 24)
            pygame.draw.rect(screen, (255, 220, 100), key_bg, border_radius=6)
            key = self.font_medium.render(str(i + 1), True, (50, 40, 80))
            key_rect = key.get_rect(center=key_bg.center)
            screen.blit(key, key_rect)

            # Upgrade name
            name_surf = self.font_small.render(up["name"], True, WHITE)
            name_rect = name_surf.get_rect(center=(draw_rect.centerx, draw_rect.y + 70))
            screen.blit(name_surf, name_rect)

            # Upgrade description
            desc = up.get("desc", "")
            if desc:
                desc_surf = self.font_tiny.render(desc, True, (200, 200, 220))
                desc_rect = desc_surf.get_rect(center=(draw_rect.centerx, draw_rect.y + 95))
                screen.blit(desc_surf, desc_rect)

            # Icon
            icon_r = 28
            icon_cx = draw_rect.centerx
            icon_cy = draw_rect.y + 140
            
            # Draw lightning bolt icon for upgrades
            if "Speed" in up["name"]:
                # Lightning bolt shape
                points = [
                    (icon_cx - 8, icon_cy - 12),
                    (icon_cx + 2, icon_cy - 4),
                    (icon_cx - 2, icon_cy + 4),
                    (icon_cx + 8, icon_cy + 12)
                ]
                pygame.draw.lines(screen, (255, 220, 100), False, points, 3)
            elif "HP" in up["name"]:
                # Health cross
                pygame.draw.rect(screen, (255, 100, 100), (icon_cx - 12, icon_cy - 12, 24, 24), border_radius=4)
                pygame.draw.rect(screen, (100, 255, 100), (icon_cx - 8, icon_cy - 8, 16, 16), border_radius=2)
            else:
                # Default circle
                pygame.draw.circle(screen, (0, 0, 0), (icon_cx, icon_cy), icon_r + 4)
                pygame.draw.circle(screen, (100, 150, 255), (icon_cx, icon_cy), icon_r + 2)
                pygame.draw.circle(screen, YELLOW if is_hovered else (200, 200, 200), (icon_cx, icon_cy), icon_r, 2)

            # Footer
            footer = self.font_tiny.render("SELECT" if is_hovered else "PICK", True, (255, 220, 100) if is_hovered else (180, 180, 200))
            footer_rect = footer.get_rect(center=(draw_rect.centerx, draw_rect.bottom - 25))
            screen.blit(footer, footer_rect)
