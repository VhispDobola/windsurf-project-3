"""
Upgrade system for player progression
"""

import random
from config.constants import UPGRADE_COUNT


class UpgradeSystem:
    """Manages player upgrades and upgrade selection"""
    
    def __init__(self):
        self.last_offer_ids = []
        self.upgrade_defs = [
            {"id": "max_hp_10", "name": "+10 Max HP", "desc": "Increase max health by 10.", "weight": 8, "apply": self._apply_max_health},
            {"id": "heal_20", "name": "+20 HP Now", "desc": "Heal 20 HP instantly.", "weight": 10, "apply": self._apply_heal, "predicate": self._needs_heal},
            {"id": "speed_1", "name": "+1 Speed", "desc": "Move faster permanently.", "weight": 7, "apply": self._apply_speed},
            {"id": "dash_speed_10", "name": "+10% Dash Speed", "desc": "Dash faster by 10%.", "weight": 6, "apply": self._apply_dash_speed},
            {"id": "dash_cd_12", "name": "-12% Dash Cooldown", "desc": "Dash becomes available faster.", "weight": 6, "apply": self._apply_dash_cooldown},
            {"id": "shoot_cd_10", "name": "-10% Shoot Cooldown", "desc": "Shoot 10% faster.", "weight": 8, "apply": self._apply_shoot_cooldown},
            {"id": "damage_1", "name": "+1 Projectile Damage", "desc": "Increase shot damage by 1.", "weight": 8, "apply": self._apply_damage},
            {"id": "proj_speed_10", "name": "+10% Projectile Speed", "desc": "Shots travel faster.", "weight": 5, "apply": self._apply_projectile_speed},
            {"id": "burst_glass", "name": "Glass Cannon", "desc": "+2 damage, -10 max HP.", "weight": 4, "apply": self._apply_glass_cannon},
            {"id": "bulwark", "name": "Bulwark", "desc": "+20 Max HP, -5% fire rate.", "weight": 4, "apply": self._apply_bulwark},
        ]
    
    def get_random_upgrades(self, player, count=UPGRADE_COUNT):
        """Get weighted/context-aware upgrades with anti-repeat behavior."""
        eligible = []
        for upgrade in self.upgrade_defs:
            predicate = upgrade.get("predicate")
            if predicate and not predicate(player):
                continue
            weight = upgrade.get("weight", 1)
            # Reduce repetition from previous offer set.
            if upgrade["id"] in self.last_offer_ids:
                weight = max(1, weight // 2)
            eligible.append((upgrade, weight))

        if not eligible:
            return []

        picks = self._weighted_unique_sample(eligible, min(count, len(eligible)))
        self.last_offer_ids = [u["id"] for u in picks]

        upgrades = []
        for upgrade in picks:
            upgrades.append({
                "id": upgrade["id"],
                "name": upgrade["name"],
                "desc": upgrade.get("desc", ""),
                "apply": (lambda p=player, fn=upgrade["apply"]: fn(p)),
            })
        return upgrades

    def _weighted_unique_sample(self, weighted_items, k):
        """Sample unique items by weight without replacement."""
        pool = list(weighted_items)
        result = []
        for _ in range(k):
            total = sum(weight for _, weight in pool)
            if total <= 0:
                break
            r = random.uniform(0, total)
            acc = 0.0
            chosen_index = 0
            for i, (_, w) in enumerate(pool):
                acc += w
                if r <= acc:
                    chosen_index = i
                    break
            item, _ = pool.pop(chosen_index)
            result.append(item)
        return result

    def _needs_heal(self, player):
        return player.health <= player.max_health * 0.8
    
    def _apply_max_health(self, player):
        """Apply max health upgrade"""
        player.max_health += 10
        if player.health > player.max_health:
            player.health = player.max_health
    
    def _apply_speed(self, player):
        """Apply speed upgrade"""
        player.base_speed += 1
    
    def _apply_dash_speed(self, player):
        """Apply dash speed upgrade"""
        player.dash_speed = int(player.dash_speed * 1.10)

    def _apply_dash_cooldown(self, player):
        """Apply dash cooldown reduction"""
        player.dash_cooldown_frames = max(25, int(player.dash_cooldown_frames * 0.88))
    
    def _apply_shoot_cooldown(self, player):
        """Apply shoot cooldown upgrade"""
        player.shoot_cooldown_frames = max(2, int(player.shoot_cooldown_frames * 0.90))
    
    def _apply_heal(self, player):
        """Apply healing upgrade"""
        player.health = min(player.max_health, player.health + 20)
    
    def _apply_damage(self, player):
        """Apply damage upgrade"""
        player.projectile_damage += 1

    def _apply_projectile_speed(self, player):
        """Apply projectile speed upgrade"""
        player.projectile_speed = min(24, int(player.projectile_speed * 1.10))

    def _apply_glass_cannon(self, player):
        """High-risk damage upgrade"""
        player.projectile_damage += 2
        player.max_health = max(30, player.max_health - 10)
        player.health = min(player.health, player.max_health)

    def _apply_bulwark(self, player):
        """Tankier setup with slower fire rate"""
        player.max_health += 20
        player.health = min(player.max_health, player.health + 10)
        player.shoot_cooldown_frames = min(20, int(player.shoot_cooldown_frames * 1.05))
