import pygame


class DamageNumberManager:
    """Shows immediate per-hit damage plus a short combo total per boss."""

    MERGE_WINDOW_MS = 1000
    HOLD_AFTER_WINDOW_MS = 500
    HIT_LIFETIME_MS = 520

    def __init__(self):
        self.entries = {}
        self.hit_popups = []
        self.font_small = None
        self.font_big = None

    def _ensure_font(self):
        if self.font_small is None:
            self.font_small = pygame.font.Font(None, 26)
        if self.font_big is None:
            self.font_big = pygame.font.Font(None, 34)

    def _entry_key(self, boss):
        return id(boss)

    def register_damage(self, boss, damage):
        damage = int(damage)
        if damage <= 0 or boss is None:
            return

        now = pygame.time.get_ticks()
        key = self._entry_key(boss)
        entry = self.entries.get(key)

        if entry is None or (now - entry["last_hit_ms"]) > self.MERGE_WINDOW_MS:
            rect = boss.get_rect()
            entry = {
                "boss": boss,
                "total": 0,
                "x": float(rect.centerx),
                "y": float(rect.top - 18),
                "created_ms": now,
                "last_hit_ms": now,
            }
            self.entries[key] = entry

        entry["total"] += damage
        entry["last_hit_ms"] = now
        rect = boss.get_rect()
        self.hit_popups.append({
            "value": damage,
            "x": float(rect.centerx + ((now % 7) - 3) * 3),
            "y": float(rect.top - 8),
            "created_ms": now,
        })

    def clear(self):
        self.entries.clear()
        self.hit_popups.clear()

    def update(self, active_bosses):
        now = pygame.time.get_ticks()
        active_set = set(active_bosses or [])

        for key in list(self.entries.keys()):
            entry = self.entries[key]
            boss = entry["boss"]

            if boss in active_set:
                rect = boss.get_rect()
                entry["x"] = float(rect.centerx)
                target_y = rect.top - 18
                entry["y"] += (target_y - entry["y"]) * 0.2

            age_since_last_hit = now - entry["last_hit_ms"]
            if age_since_last_hit > (self.MERGE_WINDOW_MS + self.HOLD_AFTER_WINDOW_MS):
                del self.entries[key]

        active_hit_popups = []
        for popup in self.hit_popups:
            age = now - popup["created_ms"]
            if age <= self.HIT_LIFETIME_MS:
                popup["y"] -= 0.85
                active_hit_popups.append(popup)
        self.hit_popups = active_hit_popups

    def draw(self, screen):
        if not self.entries and not self.hit_popups:
            return

        self._ensure_font()
        now = pygame.time.get_ticks()

        for popup in self.hit_popups:
            age = now - popup["created_ms"]
            t = max(0.0, min(1.0, age / self.HIT_LIFETIME_MS))
            alpha = int(255 * (1.0 - t))
            scale = 1.0 + (1.0 - t) * 0.18

            value = str(int(popup["value"]))
            text = self.font_small.render(value, True, (255, 240, 120)).convert_alpha()
            outline = self.font_small.render(value, True, (20, 20, 20)).convert_alpha()
            text.set_alpha(alpha)
            outline.set_alpha(alpha)

            if abs(scale - 1.0) > 0.001:
                tw, th = text.get_size()
                sw = max(1, int(tw * scale))
                sh = max(1, int(th * scale))
                text = pygame.transform.smoothscale(text, (sw, sh))
                outline = pygame.transform.smoothscale(outline, (sw, sh))

            x = int(popup["x"])
            y = int(popup["y"])
            rect = text.get_rect(center=(x, y))
            for ox, oy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                screen.blit(outline, rect.move(ox, oy))
            screen.blit(text, rect)

        for entry in self.entries.values():
            age_since_last_hit = now - entry["last_hit_ms"]
            fade_start = self.MERGE_WINDOW_MS
            fade_end = self.MERGE_WINDOW_MS + self.HOLD_AFTER_WINDOW_MS

            if age_since_last_hit <= fade_start:
                alpha = 255
            elif age_since_last_hit >= fade_end:
                alpha = 0
            else:
                t = (age_since_last_hit - fade_start) / max(1, (fade_end - fade_start))
                alpha = int(255 * (1.0 - t))

            # Combo total is immediate and accurate for all hits in the 1s merge window.
            value = str(int(entry["total"]))
            text = self.font_big.render(value, True, (255, 196, 72))
            text = text.convert_alpha()
            text.set_alpha(max(0, min(255, alpha)))

            outline = self.font_big.render(value, True, (0, 0, 0)).convert_alpha()
            outline.set_alpha(max(0, min(255, alpha)))

            x = int(entry["x"])
            y = int(entry["y"])
            rect = text.get_rect(center=(x, y))

            for ox, oy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                screen.blit(outline, rect.move(ox, oy))
            screen.blit(text, rect)
