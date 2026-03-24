"""
Upgrade system for player progression
"""

import random
from config.constants import UPGRADE_COUNT


class UpgradeSystem:
    """Manages player upgrades and upgrade selection"""
    
    def __init__(self):
        self.last_offer_ids = []
        self.last_milestone_offer_ids = []
        self.upgrade_defs = [
            {"id": "max_hp_10", "name": "+10 Max HP", "desc": "Increase max health by 10.", "weight": 8, "apply": self._apply_max_health, "predicate": self._can_gain_max_health},
            {"id": "heal_20", "name": "+30 HP Now", "desc": "Heal 30 HP instantly.", "weight": 11, "apply": self._apply_heal, "predicate": self._needs_heal},
            {"id": "speed_1", "name": "+0.75 Speed", "desc": "Move faster permanently.", "weight": 6, "apply": self._apply_speed, "predicate": self._can_gain_speed},
            {"id": "dash_speed_10", "name": "+8% Dash Speed", "desc": "Dash faster by 8%.", "weight": 5, "apply": self._apply_dash_speed, "predicate": self._can_gain_dash_speed},
            {"id": "dash_cd_12", "name": "-10% Dash Cooldown", "desc": "Dash becomes available faster.", "weight": 5, "apply": self._apply_dash_cooldown, "predicate": self._can_reduce_dash_cooldown},
            {"id": "shoot_cd_10", "name": "-8% Shoot Cooldown", "desc": "Shoot a bit faster.", "weight": 6, "apply": self._apply_shoot_cooldown, "predicate": self._can_reduce_shoot_cooldown},
            {"id": "damage_1", "name": "+1 Projectile Damage", "desc": "Increase shot damage by 1.", "weight": 5, "apply": self._apply_damage, "predicate": self._can_gain_damage},
            {"id": "proj_speed_10", "name": "+8% Projectile Speed", "desc": "Shots travel faster.", "weight": 4, "apply": self._apply_projectile_speed, "predicate": self._can_gain_projectile_speed},
            {"id": "burst_glass", "name": "Glass Cannon", "desc": "+2 damage, -16 max HP.", "weight": 3, "apply": self._apply_glass_cannon, "predicate": self._can_use_glass_cannon},
            {"id": "bulwark", "name": "Bulwark", "desc": "+20 Max HP, heal 16 HP, -6% fire rate.", "weight": 5, "apply": self._apply_bulwark, "predicate": self._can_gain_max_health},
        ]
        self.milestone_upgrade_defs = [
            {"id": "spread_shot", "name": "Spread Shot", "desc": "Fire a wider multi-shot volley. Spread pellets deal 33% less damage.", "weight": 1, "apply": self._apply_spread_shot, "predicate": self._can_gain_spread_shot},
            {"id": "reflect_shield", "name": "Reflection Shield", "desc": "Gain shield charges that reflect enemy projectiles.", "weight": 1, "apply": self._apply_reflection_shield, "predicate": self._can_gain_reflection_shield},
            {"id": "nanite_repair", "name": "Nanite Repair", "desc": "Regenerate health during combat and recover some HP immediately.", "weight": 1, "apply": self._apply_nanite_repair, "predicate": self._can_gain_nanite_repair},
            {"id": "overdrive_rounds", "name": "Overdrive Rounds", "desc": "Shots pierce and gain extra damage.", "weight": 1, "apply": self._apply_overdrive_rounds, "predicate": self._can_gain_overdrive_rounds},
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

        return self._build_upgrade_payload(player, picks)

    def get_milestone_upgrades(self, player, count=UPGRADE_COUNT):
        eligible = []
        for upgrade in self.milestone_upgrade_defs:
            predicate = upgrade.get("predicate")
            if predicate and not predicate(player):
                continue
            weight = upgrade.get("weight", 1)
            if upgrade["id"] in self.last_milestone_offer_ids:
                weight = max(1, weight // 2)
            eligible.append((upgrade, weight))

        if not eligible:
            return self.get_random_upgrades(player, count=count)

        picks = self._weighted_unique_sample(eligible, min(count, len(eligible)))
        self.last_milestone_offer_ids = [u["id"] for u in picks]
        return self._build_upgrade_payload(player, picks)

    def _build_upgrade_payload(self, player, upgrades):
        payload = []
        for upgrade in upgrades:
            payload.append({
                "id": upgrade["id"],
                "name": upgrade["name"],
                "desc": upgrade.get("desc", ""),
                "apply": (lambda p=player, fn=upgrade["apply"]: fn(p)),
                "apply_to": upgrade["apply"],
            })
        return payload

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

    def _can_gain_max_health(self, player):
        return player.max_health < 220

    def _can_gain_speed(self, player):
        return player.base_speed < 7.5

    def _can_gain_dash_speed(self, player):
        return player.dash_speed < 18

    def _can_reduce_dash_cooldown(self, player):
        return player.dash_cooldown_frames > 30

    def _can_reduce_shoot_cooldown(self, player):
        return player.shoot_cooldown_frames > 4

    def _can_gain_damage(self, player):
        return player.projectile_damage < 9

    def _can_gain_projectile_speed(self, player):
        return player.projectile_speed < 18

    def _can_use_glass_cannon(self, player):
        return player.projectile_damage < 10 and player.max_health > 60

    def _can_gain_spread_shot(self, player):
        return getattr(player, "spread_shot_level", 0) < 2

    def _can_gain_reflection_shield(self, player):
        return not getattr(player, "reflect_shield", False) or getattr(player, "reflect_charges", 0) < 6

    def _can_gain_nanite_repair(self, player):
        return getattr(player, "regen_level", 0) < 3

    def _can_gain_overdrive_rounds(self, player):
        return not getattr(player, "piercing_shots", False) or player.projectile_damage < 10
    
    def _apply_max_health(self, player):
        """Apply max health upgrade"""
        player.max_health = min(220, player.max_health + 10)
        if player.health > player.max_health:
            player.health = player.max_health
    
    def _apply_speed(self, player):
        """Apply speed upgrade"""
        player.base_speed = min(7.5, player.base_speed + 0.75)
    
    def _apply_dash_speed(self, player):
        """Apply dash speed upgrade"""
        player.dash_speed = min(18, player.dash_speed * 1.08)

    def _apply_dash_cooldown(self, player):
        """Apply dash cooldown reduction"""
        player.dash_cooldown_frames = max(30, int(player.dash_cooldown_frames * 0.90))
    
    def _apply_shoot_cooldown(self, player):
        """Apply shoot cooldown upgrade"""
        player.shoot_cooldown_frames = max(4, int(player.shoot_cooldown_frames * 0.92))
    
    def _apply_heal(self, player):
        """Apply healing upgrade"""
        player.health = min(player.max_health, player.health + 30)
    
    def _apply_damage(self, player):
        """Apply damage upgrade"""
        player.projectile_damage = min(9, player.projectile_damage + 1)

    def _apply_projectile_speed(self, player):
        """Apply projectile speed upgrade"""
        player.projectile_speed = min(18, player.projectile_speed * 1.08)

    def _apply_glass_cannon(self, player):
        """High-risk damage upgrade"""
        player.projectile_damage = min(10, player.projectile_damage + 2)
        player.max_health = max(30, player.max_health - 16)
        player.health = min(player.health, player.max_health)

    def _apply_bulwark(self, player):
        """Tankier setup with slower fire rate"""
        player.max_health = min(220, player.max_health + 20)
        player.health = min(player.max_health, player.health + 16)
        player.shoot_cooldown_frames = min(20, int(player.shoot_cooldown_frames * 1.06))

    def _apply_spread_shot(self, player):
        player.spread_shot_level = min(2, getattr(player, "spread_shot_level", 0) + 1)
        player.projectile_speed = min(19, player.projectile_speed + 0.5)

    def _apply_reflection_shield(self, player):
        player.reflect_shield = True
        player.reflect_charges = min(6, getattr(player, "reflect_charges", 0) + 3)

    def _apply_nanite_repair(self, player):
        player.regen_level = min(3, getattr(player, "regen_level", 0) + 1)
        player.health = min(player.max_health, player.health + 18)

    def _apply_overdrive_rounds(self, player):
        player.piercing_shots = True
        player.projectile_damage = min(10, player.projectile_damage + 1)
        player.projectile_speed = min(19, player.projectile_speed + 1)
