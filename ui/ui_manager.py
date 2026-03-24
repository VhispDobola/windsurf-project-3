import os

import pygame
from config.constants import WHITE, YELLOW, GREEN, RED
from .boss_title_animator import BossTitleAnimator


class UIManager:
    def __init__(self, render_system=None):
        self.render_system = render_system
        self.font_large = self._get_font(56)
        self.font_medium = self._get_font(34)
        self.font_small = self._get_font(22)
        self.font_tiny = self._get_font(18)
        self.boss_animator = BossTitleAnimator()
        self._relic_icon_cache = {}
    
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

    def _wrap_text(self, text, font, max_width):
        words = (text or "").split()
        if not words:
            return []
        lines = []
        current = words[0]
        for word in words[1:]:
            trial = f"{current} {word}"
            if font.size(trial)[0] <= max_width:
                current = trial
            else:
                lines.append(current)
                current = word
        lines.append(current)
        return lines

    def _get_relic_icon(self, relic, size):
        icon_path = relic.get("icon_path")
        abs_path = None
        icon_mtime = None
        if icon_path:
            abs_path = os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                icon_path.replace("/", os.sep),
            )
            if os.path.exists(abs_path):
                try:
                    icon_mtime = os.path.getmtime(abs_path)
                except OSError:
                    icon_mtime = None

        icon_key = (relic.get("id"), size, abs_path, icon_mtime)
        if icon_key in self._relic_icon_cache:
            return self._relic_icon_cache[icon_key]

        image = None
        if abs_path and os.path.exists(abs_path):
            try:
                image = pygame.image.load(abs_path).convert_alpha()
                image = pygame.transform.smoothscale(image, (size, size))
            except pygame.error:
                image = None

        if image is None:
            image = self._build_relic_icon_fallback(relic, size)

        self._relic_icon_cache[icon_key] = image
        return image

    def _build_relic_icon_fallback(self, relic, size):
        category = relic.get("category", "utility")
        palette = {
            "offense": ((70, 22, 28), (240, 90, 90), (255, 220, 220)),
            "defense": ((20, 40, 62), (90, 220, 255), (220, 250, 255)),
            "mobility": ((28, 50, 38), (110, 255, 170), (220, 255, 235)),
            "utility": ((58, 46, 18), (255, 210, 90), (255, 248, 220)),
        }
        bg, accent, text_color = palette.get(category, palette["utility"])
        surf = pygame.Surface((size, size), pygame.SRCALPHA)
        pygame.draw.rect(surf, bg, (0, 0, size, size), border_radius=12)
        pygame.draw.rect(surf, accent, (0, 0, size, size), 2, border_radius=12)
        glow = pygame.Surface((size, size), pygame.SRCALPHA)
        pygame.draw.circle(glow, (*accent, 55), (size // 2, size // 2), max(10, size // 3))
        surf.blit(glow, (0, 0))

        initials = "".join(part[:1] for part in relic.get("name", "?").split()[:2]).upper() or "?"
        font = self._get_font(max(16, size // 3))
        label = font.render(initials, True, text_color)
        surf.blit(label, label.get_rect(center=(size // 2, size // 2)))
        return surf

    def draw_menu(self, screen):
        screen_width = screen.get_width()
        screen_height = screen.get_height()

        self._draw_center_text(screen, "BOSS RUSH", self.font_large, screen_height // 3, WHITE)
        self._draw_center_text(screen, "Press SPACE to Start", self.font_medium, screen_height // 2, YELLOW)
        self._draw_center_text(screen, "Press C to Customize", self.font_small, screen_height // 2 + 36, GREEN)
        self._draw_center_text(screen, "Press P for Progression", self.font_small, screen_height // 2 + 68, (120, 220, 255))
        self._draw_center_text(screen, "Press H to Host Online Lobby", self.font_small, screen_height // 2 + 100, (140, 255, 180))
        self._draw_center_text(screen, "Press J to Join Multiplayer", self.font_small, screen_height // 2 + 132, (150, 220, 255))
        
        controls = [
            "P1: WASD + LSHIFT + SPACE/Mouse",
            "P2/P3/P4: LAN client slots 2/3/4",
            "F11: Toggle Fullscreen"
        ]
        
        y = int(screen_height * 0.64)
        for control in controls:
            text = self.font_small.render(control, True, WHITE)
            text_rect = text.get_rect(center=(screen_width // 2, y))
            screen.blit(text, text_rect)
            y += 30

    def draw_join_setup(self, screen, host, port, slot_label, selected_field, status_message=None):
        screen_w = screen.get_width()
        screen_h = screen.get_height()
        self._draw_center_text(screen, "JOIN MULTIPLAYER", self.font_large, 70, YELLOW)
        self._draw_center_text(
            screen,
            "Tab/Up/Down: Move  |  Type to edit  |  Left/Right: Change slot  |  Enter: Connect  |  Esc: Back",
            self.font_tiny,
            104,
            WHITE,
        )

        panel = pygame.Rect(screen_w // 2 - 280, 150, 560, 280)
        self._draw_panel(screen, panel, (20, 22, 28), (110, 130, 180))
        field_colors = [WHITE, WHITE, WHITE]
        if 0 <= selected_field < len(field_colors):
            field_colors[selected_field] = YELLOW

        host_text = self.font_small.render(f"Host IP: {host}", True, field_colors[0])
        port_text = self.font_small.render(f"Port: {port}", True, field_colors[1])
        slot_text = self.font_small.render(f"Slot: {slot_label}", True, field_colors[2])
        screen.blit(host_text, (panel.x + 40, panel.y + 60))
        screen.blit(port_text, (panel.x + 40, panel.y + 120))
        screen.blit(slot_text, (panel.x + 40, panel.y + 180))

        help_lines = [
            "Examples: 127.0.0.1, 192.168.1.20, or a Tailscale/ZeroTier IP",
            "Use Auto slot unless you need a fixed player number.",
        ]
        for idx, line in enumerate(help_lines):
            self._draw_center_text(screen, line, self.font_tiny, panel.y + 230 + idx * 22, (190, 205, 220))

        if status_message:
            self._draw_center_text(screen, status_message, self.font_small, screen_h - 40, GREEN if "Launching" in status_message else RED)

    def _draw_hat_icon(self, screen, rect, hat_style):
        hat = (hat_style or "None").lower()
        if hat == "none":
            return
        if hat == "cap":
            pygame.draw.ellipse(screen, (30, 30, 30), (rect.x + 6, rect.y - 6, rect.width - 12, 6))
            pygame.draw.rect(screen, (220, 70, 70), (rect.x + 8, rect.y - 11, rect.width - 16, 7), border_radius=3)
        elif hat == "crown":
            points = [
                (rect.x + 8, rect.y + 2),
                (rect.x + 12, rect.y - 8),
                (rect.centerx, rect.y - 1),
                (rect.right - 12, rect.y - 8),
                (rect.right - 8, rect.y + 2),
            ]
            pygame.draw.polygon(screen, (240, 200, 70), points)
            pygame.draw.rect(screen, (200, 160, 50), (rect.x + 8, rect.y + 1, rect.width - 16, 3))
        elif hat == "beanie":
            pygame.draw.ellipse(screen, (80, 180, 255), (rect.x + 5, rect.y - 8, rect.width - 10, 10))
            pygame.draw.circle(screen, (240, 240, 240), (rect.centerx, rect.y - 8), 3)

    def _draw_avatar_card(
        self,
        screen,
        rect,
        username,
        color,
        hat_style,
        status_text,
        status_color,
        ping_text=None,
        selected=False,
    ):
        border = YELLOW if selected else (100, 100, 120)
        self._draw_panel(screen, rect, (24, 26, 34), border)
        preview = pygame.Rect(rect.x + 18, rect.y + 24, 46, 46)
        pygame.draw.rect(screen, (0, 0, 0), preview.inflate(10, 10), border_radius=10)
        pygame.draw.rect(screen, color, preview, border_radius=8)
        self._draw_hat_icon(screen, preview, hat_style)

        name = self.font_small.render(username, True, WHITE)
        screen.blit(name, (rect.x + 84, rect.y + 18))
        status = self.font_tiny.render(status_text, True, status_color)
        screen.blit(status, (rect.x + 84, rect.y + 46))
        hat = self.font_tiny.render(f"Hat: {hat_style}", True, (190, 205, 220))
        screen.blit(hat, (rect.x + 84, rect.y + 68))
        if ping_text:
            ping = self.font_tiny.render(ping_text, True, (150, 220, 255))
            screen.blit(ping, (rect.right - ping.get_width() - 14, rect.y + 18))

    def draw_lobby(self, screen, lobby_slots, local_slot, host_address=None, can_start=False, host_mode=False):
        screen_w = screen.get_width()
        screen_h = screen.get_height()
        self._draw_center_text(screen, "ONLINE LOBBY", self.font_large, 60, YELLOW)
        subtitle = "SPACE: Start match | C: Customize | P: Armory" if host_mode else "ENTER: Ready up"
        self._draw_center_text(screen, subtitle, self.font_tiny, 98, WHITE)
        if host_address:
            self._draw_center_text(screen, f"Join address: {host_address}", self.font_tiny, 124, (150, 220, 255))

        start_y = 170
        card_h = 102
        gap = 14
        card_w = min(620, screen_w - 120)
        start_x = (screen_w - card_w) // 2

        for index, slot in enumerate(lobby_slots):
            rect = pygame.Rect(start_x, start_y + index * (card_h + gap), card_w, card_h)
            profile = slot.get("profile", {})
            self._draw_avatar_card(
                screen,
                rect,
                profile.get("username", f"P{slot.get('slot', index + 1)}"),
                tuple(profile.get("color", (0, 100, 255))),
                profile.get("hat", "None"),
                slot.get("status", "Open Slot"),
                slot.get("status_color", (180, 180, 190)),
                ping_text=slot.get("ping_text"),
                selected=slot.get("slot") == local_slot,
            )

        footer = "All connected players are ready." if can_start else "Waiting for players to join and ready up."
        footer_color = GREEN if can_start else (210, 210, 220)
        self._draw_center_text(screen, footer, self.font_small, screen_h - 40, footer_color)

    def draw_progression_menu(
        self,
        screen,
        progression_system,
        selected_relic_index,
        selected_slot_index,
        focus_area,
        status_message=None,
    ):
        screen_w = screen.get_width()
        screen_h = screen.get_height()
        relics = progression_system.get_visible_relics()
        profile = progression_system.profile

        self._draw_center_text(screen, "ARMORY", self.font_large, 50, YELLOW)
        self._draw_center_text(
            screen,
            "P/Esc: Back  |  Up/Down: Move  |  Left/Right: Focus  |  1-4: Equip  |  C: Craft  |  U: Upgrade  |  Backspace: Unequip",
            self.font_tiny,
            84,
            WHITE,
        )

        currency_rect = pygame.Rect(24, 120, 240, screen_h - 190)
        inventory_rect = pygame.Rect(284, 120, 430, screen_h - 190)
        loadout_rect = pygame.Rect(screen_w - 262, 120, 238, screen_h - 190)

        self._draw_panel(screen, currency_rect, (20, 24, 32), (80, 120, 150))
        self._draw_panel(
            screen,
            inventory_rect,
            (20, 20, 28),
            (220, 200, 90) if focus_area == "inventory" else (100, 100, 130),
        )
        self._draw_panel(
            screen,
            loadout_rect,
            (24, 20, 30),
            (220, 200, 90) if focus_area == "loadout" else (100, 100, 130),
        )

        self.draw_currency_summary(screen, currency_rect, profile)
        self.draw_relic_inventory(
            screen,
            inventory_rect,
            progression_system,
            relics,
            selected_relic_index,
        )
        self.draw_loadout_panel(
            screen,
            loadout_rect,
            progression_system,
            selected_slot_index,
        )

        if status_message:
            self._draw_center_text(screen, status_message, self.font_small, screen_h - 30, GREEN)

    def draw_currency_summary(self, screen, rect, profile):
        title = self.font_medium.render("Resources", True, YELLOW)
        screen.blit(title, (rect.x + 14, rect.y + 12))

        credits = int(profile.get("currencies", {}).get("credits", 0))
        credits_text = self.font_small.render(f"Credits: {credits}", True, WHITE)
        screen.blit(credits_text, (rect.x + 14, rect.y + 56))

        materials = profile.get("materials", {})
        materials_title = self.font_small.render("Boss Essence", True, (150, 210, 255))
        screen.blit(materials_title, (rect.x + 14, rect.y + 96))

        sorted_materials = sorted(materials.items(), key=lambda item: item[0])
        if not sorted_materials:
            empty = self.font_tiny.render("No essence collected yet.", True, (170, 170, 190))
            screen.blit(empty, (rect.x + 14, rect.y + 126))
            return

        y = rect.y + 126
        for material_key, amount in sorted_materials[:16]:
            label = material_key.replace("_", " ").title()
            text = self.font_tiny.render(f"{label}: {amount}", True, WHITE)
            screen.blit(text, (rect.x + 14, y))
            y += 22

    def draw_relic_inventory(self, screen, rect, progression_system, relics, selected_relic_index):
        title = self.font_medium.render("Relics", True, WHITE)
        screen.blit(title, (rect.x + 14, rect.y + 12))

        if not relics:
            empty = self.font_small.render("No unlocked relics are visible yet.", True, RED)
            screen.blit(empty, (rect.x + 14, rect.y + 56))
            return

        selected_relic_index = max(0, min(selected_relic_index, len(relics) - 1))
        y = rect.y + 52
        card_h = 124
        visible_count = max(1, (rect.height - 70) // (card_h + 8))
        start = min(max(0, selected_relic_index - visible_count // 2), max(0, len(relics) - visible_count))

        for offset, relic in enumerate(relics[start : start + visible_count]):
            index = start + offset
            card = pygame.Rect(rect.x + 12, y + offset * (card_h + 8), rect.width - 24, card_h)
            entry = progression_system.get_relic_entry(relic["id"])
            owned = entry.get("owned", False)
            craftable = progression_system.can_craft_relic(relic["id"])
            upgradable = progression_system.can_upgrade_relic(relic["id"])

            fill = (42, 56, 68) if owned else (34, 30, 38)
            border = (255, 220, 110) if index == selected_relic_index else (100, 100, 120)
            pygame.draw.rect(screen, fill, card, border_radius=10)
            pygame.draw.rect(screen, border, card, 2, border_radius=10)

            icon = self._get_relic_icon(relic, 56)
            screen.blit(icon, (card.x + 10, card.y + 20))

            status = "Owned" if owned else "Craftable" if craftable else "Locked"
            if owned and upgradable:
                status = "Upgradeable"
            name = self.font_small.render(relic["name"], True, WHITE)
            screen.blit(name, (card.x + 78, card.y + 10))

            meta = self.font_tiny.render(
                f"{relic.get('category', 'relic').title()} | Rank {entry.get('rank', 0)}/{relic.get('max_rank', 1)} | {status}",
                True,
                (190, 210, 230),
            )
            screen.blit(meta, (card.x + 78, card.y + 34))

            text_width = card.width - 92
            desc_lines = self._wrap_text(relic.get("ui_desc", ""), self.font_tiny, text_width)
            for line_idx, line in enumerate(desc_lines[:2]):
                desc = self.font_tiny.render(line, True, (220, 220, 230))
                screen.blit(desc, (card.x + 78, card.y + 56 + line_idx * 16))

            appearance_lines = self._wrap_text(
                relic.get("appearance", ""),
                self.font_tiny,
                text_width,
            )
            for line_idx, line in enumerate(appearance_lines[:2]):
                appearance = self.font_tiny.render(line, True, (170, 185, 205))
                screen.blit(appearance, (card.x + 78, card.y + 88 + line_idx * 16))

    def draw_loadout_panel(self, screen, rect, progression_system, selected_slot_index):
        title = self.font_medium.render("Loadout", True, WHITE)
        screen.blit(title, (rect.x + 14, rect.y + 12))

        loadout = progression_system.get_equipped_relics()
        y = rect.y + 58
        for i, relic_id in enumerate(loadout):
            slot_rect = pygame.Rect(rect.x + 16, y + i * 76, rect.width - 32, 62)
            border = YELLOW if i == selected_slot_index else (100, 100, 120)
            pygame.draw.rect(screen, (34, 34, 42), slot_rect, border_radius=10)
            pygame.draw.rect(screen, border, slot_rect, 2, border_radius=10)
            icon_rect = pygame.Rect(slot_rect.x + 8, slot_rect.y + 7, 48, 48)
            label = self.font_small.render(f"Slot {i + 1}", True, WHITE)
            screen.blit(label, (slot_rect.x + 64, slot_rect.y + 8))
            if relic_id:
                relic = progression_system.relic_definitions.get(relic_id, {})
                entry = progression_system.get_relic_entry(relic_id)
                icon = self._get_relic_icon(relic, 48)
                screen.blit(icon, icon_rect.topleft)
                name = self.font_tiny.render(
                    f"{relic.get('name', relic_id)} (R{entry.get('rank', 1)})",
                    True,
                    (180, 225, 255),
                )
            else:
                placeholder = self._build_relic_icon_fallback({"name": "Empty", "category": "utility"}, 48)
                screen.blit(placeholder, icon_rect.topleft)
                name = self.font_tiny.render("Empty", True, (160, 160, 180))
            screen.blit(name, (slot_rect.x + 64, slot_rect.y + 34))

    def draw_reward_toasts(self, screen, reward_toasts):
        if not reward_toasts:
            return

        y = 18
        for toast in reward_toasts[:5]:
            alpha = max(60, min(255, int(255 * (toast.get("timer", 1) / max(1, toast.get("duration", 1))))))
            surf = pygame.Surface((420, 30), pygame.SRCALPHA)
            pygame.draw.rect(surf, (15, 18, 24, alpha), surf.get_rect(), border_radius=10)
            text = self.font_tiny.render(toast.get("text", ""), True, toast.get("color", YELLOW))
            surf.blit(text, (10, 7))
            screen.blit(surf, (screen.get_width() - 440, y))
            y += 36

    def draw_customization(self, screen, players, selected_player, selected_field, color_options, hat_options):
        screen_w = screen.get_width()

        self._draw_center_text(screen, "CUSTOMIZATION", self.font_large, 70, YELLOW)
        self._draw_center_text(screen, "TAB: Switch Player  |  Arrows: Edit  |  Enter/Esc: Back", self.font_tiny, 104, WHITE)

        if not players:
            return

        selected_player = max(0, min(selected_player, len(players) - 1))
        player = players[selected_player]
        username = getattr(player, "username", "") or f"P{selected_player + 1}"
        hat = getattr(player, "hat_style", "None")
        color = getattr(player, "color", WHITE)

        panel = pygame.Rect(screen_w // 2 - 250, 140, 500, 360)
        self._draw_panel(screen, panel, (22, 22, 28), (130, 130, 180))

        self._draw_center_text(screen, f"Editing Player {selected_player + 1}", self.font_medium, 180, color)

        field_colors = [WHITE, WHITE, WHITE]
        if 0 <= selected_field < len(field_colors):
            field_colors[selected_field] = YELLOW

        user_text = self.font_small.render(f"Username: {username}", True, field_colors[0])
        color_text = self.font_small.render(f"Color: {color}", True, field_colors[1])
        hat_text = self.font_small.render(f"Hat: {hat}", True, field_colors[2])
        screen.blit(user_text, (panel.x + 40, panel.y + 90))
        screen.blit(color_text, (panel.x + 40, panel.y + 140))
        screen.blit(hat_text, (panel.x + 40, panel.y + 190))

        for i, option in enumerate(color_options):
            swatch = pygame.Rect(panel.x + 40 + (i * 34), panel.y + 235, 26, 26)
            pygame.draw.rect(screen, option, swatch, border_radius=4)
            if option == color:
                pygame.draw.rect(screen, WHITE, swatch.inflate(4, 4), 2, border_radius=5)

        preview_rect = pygame.Rect(panel.centerx + 120, panel.y + 120, 38, 38)
        pygame.draw.rect(screen, (0, 0, 0), preview_rect.inflate(8, 8), border_radius=8)
        pygame.draw.rect(screen, color, preview_rect, border_radius=6)
        name_preview = self.font_tiny.render(username, True, WHITE)
        screen.blit(name_preview, name_preview.get_rect(center=(preview_rect.centerx, preview_rect.y - 14)))

        help_lines = [
            "While Username selected: type letters/numbers, Backspace to delete",
            "While Color/Hat selected: Left/Right to cycle options",
            f"Hat options: {', '.join(hat_options)}",
        ]
        for idx, line in enumerate(help_lines):
            self._draw_center_text(screen, line, self.font_tiny, panel.y + 290 + idx * 22, WHITE)

    def draw_player_status(self, screen, players):
        if not players:
            return

        panel_x = 12
        panel_y = 12
        panel_w = 230
        panel_h = 30 + (len(players) * 28)
        panel = pygame.Rect(panel_x, panel_y, panel_w, panel_h)
        pygame.draw.rect(screen, (0, 0, 0), panel, border_radius=10)
        pygame.draw.rect(screen, (255, 255, 255), panel, 2, border_radius=10)

        title = self.font_tiny.render("Players", True, YELLOW)
        screen.blit(title, (panel_x + 10, panel_y + 7))

        for i, player in enumerate(players):
            alive = player.health > 0
            color = getattr(player, "color", WHITE)
            label_color = color if alive else (130, 130, 130)
            hp = max(0, int(player.health))
            max_hp = max(1, int(player.max_health))
            status = "DOWN" if not alive else f"{hp}/{max_hp}"
            username = getattr(player, "username", f"P{i + 1}") or f"P{i + 1}"
            text = self.font_tiny.render(f"{username}: {status}", True, label_color)
            screen.blit(text, (panel_x + 10, panel_y + 30 + (i * 26)))
            
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
            
            # Health bar background and border stay readable across all boss colors.
            background_rect = pygame.Rect(x, bar_y, bar_width, bar_height)
            pygame.draw.rect(screen, (45, 10, 10), background_rect)
            pygame.draw.rect(screen, WHITE, background_rect, 1)
            
            # Health fill
            max_health = max(1, boss.max_health)
            health_percentage = max(0.0, min(1.0, boss.health / max_health))
            health_color = getattr(boss, 'health_bar_color', GREEN)
            fill_width = int(bar_width * health_percentage)
            if boss.health > 0 and fill_width <= 0:
                fill_width = 1
            pygame.draw.rect(screen, health_color, (x, bar_y, fill_width, bar_height))

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

    def draw_upgrade_screen(self, screen, upgrades, hovered_index=-1, title="CHOOSE UPGRADE", subtitle="Press 1-4 or Click to pick"):
        screen_width = screen.get_width()
        screen_height = screen.get_height()
        
        overlay = pygame.Surface((screen_width, screen_height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 140))
        screen.blit(overlay, (0, 0))

        self._draw_center_text(screen, title, self.font_large, screen_height // 6, YELLOW)
        self._draw_center_text(screen, subtitle, self.font_small, screen_height // 6 + 42, WHITE)

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
