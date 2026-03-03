import random
from config.constants import BOSS_GLOBAL_HEALTH_MULTIPLIER
from utils import load_log_driven_balance
from bosses import (
    EternalGuardian, BladeMaster, NexusCore, VoidAssassin, 
    Chronomancer, TheVirusQueen, TempestLord, ThunderEmperor,
    ImmortalPhoenix, CrystallineDestroyer, EternalDragon,
    IceTyrant, MagmaSovereign, CyberOverlord
)

class BossManager:
    CANONICAL_BOSS_NAMES = {
        "EternalGuardian": "Eternal Guardian",
        "BladeMaster": "Blade Master",
        "NexusCore": "Nexus Core",
        "VoidAssassin": "Void Assassin",
        "Chronomancer": "Chronomancer",
        "TheVirusQueen": "The Virus Queen",
        "TempestLord": "Tempest Lord",
        "ThunderEmperor": "Thunder Emperor",
        "ImmortalPhoenix": "Immortal Phoenix",
        "CrystallineDestroyer": "Crystalline Destroyer",
        "EternalDragon": "Eternal Dragon",
        "IceTyrant": "Ice Tyrant",
        "MagmaSovereign": "Magma Sovereign",
        "CyberOverlord": "Cyber Overlord",
    }
    # Log-driven per-boss tuning layer on top of progression scaling.
    # Values are conservative and can be iterated from future logs.
    BOSS_BALANCE = {
        "Void Assassin": {"health": 0.62, "damage": 1.10},
        "Chronomancer": {"health": 0.72, "damage": 1.00},
        "Thunder Emperor": {"health": 0.86, "damage": 1.00},
        "Tempest Lord": {"health": 1.08, "damage": 0.72},
    }

    def __init__(self):
        self.all_boss_classes = [
            EternalGuardian, BladeMaster, NexusCore, VoidAssassin, 
            Chronomancer, TheVirusQueen, TempestLord, ThunderEmperor,
            ImmortalPhoenix, CrystallineDestroyer, EternalDragon,
            IceTyrant, MagmaSovereign, CyberOverlord
        ]
        self.available_bosses = self.all_boss_classes.copy()
        self.defeated_bosses = []
        self.bosses_defeated_count = 0
        self.dynamic_boss_balance, self.dynamic_ability_balance, self.balance_notes = load_log_driven_balance()
        
    def get_next_boss(self):
        """Get next boss for single boss fights (first 10)"""
        if self.bosses_defeated_count < 10:
            # Random selection without replacement
            if not self.available_bosses:
                # If we run out, reset with all bosses except those already fought
                self.available_bosses = [boss for boss in self.all_boss_classes 
                                       if boss not in self.defeated_bosses[:10]]
            
            if self.available_bosses:
                boss_class = random.choice(self.available_bosses)
                self.available_bosses.remove(boss_class)
                boss = boss_class()
                self._apply_canonical_name(boss)
                self._apply_difficulty_scaling(boss)
                return boss
        else:
            # After 10 bosses, random selection with replacement
            boss_class = random.choice(self.all_boss_classes)
            boss = boss_class()
            self._apply_canonical_name(boss)
            self._apply_difficulty_scaling(boss)
            return boss
            
        return None
        
    def get_next_boss_pair(self):
        """Get next pair of weakened bosses (after 10)"""
        # Select 2 random bosses
        boss_classes = random.sample(self.all_boss_classes, 2)
        boss1 = boss_classes[0]()
        boss2 = boss_classes[1]()
        self._apply_canonical_name(boss1)
        self._apply_canonical_name(boss2)
        
        # Apply weakening to both bosses
        self._weaken_boss(boss1)
        self._weaken_boss(boss2)
        self._apply_difficulty_scaling(boss1)
        self._apply_difficulty_scaling(boss2)
        
        return boss1, boss2
        
    def _weaken_boss(self, boss):
        """Apply weakening to a boss for paired fights"""
        # Reduce health by 35%
        boss.max_health = int(boss.max_health * 0.65)
        boss.health = boss.max_health
        
        # Store original values for reference
        boss.original_max_health = getattr(boss, 'original_max_health', boss.max_health * 1.54)  # Approximate original
        
        # Mark as weakened for UI purposes
        boss.is_weakened = True

    def _apply_difficulty_scaling(self, boss):
        """Scale boss health and damage based on progression"""
        count = self.bosses_defeated_count
        if count < 5:
            health_scale = 0.9
            damage_scale = 0.85
        elif count < 10:
            health_scale = 1.0
            damage_scale = 1.0
        elif count < 15:
            health_scale = 1.1
            damage_scale = 1.15
        else:
            health_scale = 1.25
            damage_scale = 1.3
        
        # Apply per-boss balance first, then progression scaling.
        boss_name = getattr(boss, "name", "")
        static_balance = self.BOSS_BALANCE.get(boss_name, {"health": 1.0, "damage": 1.0})
        dynamic_balance = self.dynamic_boss_balance.get(boss_name, {"health": 1.0, "damage": 1.0})
        health_scale *= static_balance.get("health", 1.0) * dynamic_balance.get("health", 1.0)
        damage_scale *= static_balance.get("damage", 1.0) * dynamic_balance.get("damage", 1.0)

        boss.max_health = max(1, int(boss.max_health * health_scale))
        boss.max_health = max(1, int(boss.max_health * BOSS_GLOBAL_HEALTH_MULTIPLIER))
        boss.health = boss.max_health
        boss.damage_scale = damage_scale
        boss.dynamic_ability_balance = self.dynamic_ability_balance.get(boss_name, {})
        if hasattr(boss, 'original_health'):
            boss.original_health = boss.max_health

    def _apply_canonical_name(self, boss):
        """Enforce canonical display names for consistency across UI/logs."""
        class_name = type(boss).__name__
        canonical_name = self.CANONICAL_BOSS_NAMES.get(class_name)
        if canonical_name:
            boss.name = canonical_name

    def validate_boss_name_consistency(self):
        """Return list of (class_name, actual_name, expected_name) mismatches."""
        mismatches = []
        for boss_cls in self.all_boss_classes:
            try:
                boss = boss_cls()
            except Exception:
                continue
            class_name = boss_cls.__name__
            expected = self.CANONICAL_BOSS_NAMES.get(class_name)
            if expected and boss.name != expected:
                mismatches.append((class_name, boss.name, expected))
        return mismatches
        
    def on_boss_defeated(self, boss):
        """Track boss defeat"""
        self.defeated_bosses.append(type(boss))
        self.bosses_defeated_count += 1
        
    def reset(self):
        """Reset boss manager for new game"""
        self.available_bosses = self.all_boss_classes.copy()
        self.defeated_bosses = []
        self.bosses_defeated_count = 0
