"""
Log-driven automatic balance tuning.
"""

import json
import os


def _clamp(value, low, high):
    return max(low, min(high, value))


def load_log_driven_balance(path="data/boss_performance_log.json"):
    """
    Load latest performance log and return:
    - per-boss multipliers: {boss_name: {"health": x, "damage": y}}
    - per-ability multipliers: {boss_name: {ability_name: x}}
    - human-readable notes list
    """
    if not os.path.exists(path):
        return {}, {}, []

    try:
        with open(path, "r", encoding="utf-8") as f:
            payload = json.load(f)
    except Exception:
        return {}, {}, []

    session = payload.get("session", {})
    bosses = session.get("bosses", {})
    if not bosses:
        return {}, {}, []

    boss_balance = {}
    ability_balance = {}
    notes = []

    for boss_name, data in bosses.items():
        duration = float(data.get("fight_duration", 0.0) or 0.0)
        victory = bool(data.get("victory", False))
        player_damage_taken = float(data.get("player_damage_taken", 0.0) or 0.0)

        health_scale = 1.0
        damage_scale = 1.0

        # Boss-level tuning from outcome + pace.
        if victory and duration < 30:
            health_scale += 0.18
            damage_scale += 0.08
        elif victory and duration < 50:
            health_scale += 0.08
        elif not victory and duration < 20:
            health_scale -= 0.08
            damage_scale -= 0.12
        elif not victory:
            health_scale -= 0.16
            damage_scale -= 0.10

        if victory and player_damage_taken <= 5:
            damage_scale += 0.06
        elif player_damage_taken > 80:
            damage_scale -= 0.10

        if duration > 150:
            health_scale -= 0.18

        health_scale = _clamp(health_scale, 0.55, 1.35)
        damage_scale = _clamp(damage_scale, 0.70, 1.30)

        if abs(health_scale - 1.0) > 0.01 or abs(damage_scale - 1.0) > 0.01:
            boss_balance[boss_name] = {"health": health_scale, "damage": damage_scale}
            notes.append(
                f"{boss_name}: auto-tune health x{health_scale:.2f}, damage x{damage_scale:.2f}"
            )

        # Ability-level tuning based on hit-rate and damage share.
        ability_stats = data.get("ability_stats", {}) or {}
        total_ability_damage = 0.0
        for stats in ability_stats.values():
            total_ability_damage += float(stats.get("damage", 0) or 0)

        boss_ability_scales = {}
        for ability_name, stats in ability_stats.items():
            uses = int(stats.get("uses", 0) or 0)
            hits = int(stats.get("hits", 0) or 0)
            damage = float(stats.get("damage", 0) or 0)
            if uses < 6:
                continue

            hit_rate = hits / uses if uses > 0 else 0.0
            share = (damage / total_ability_damage) if total_ability_damage > 0 else 0.0

            scale = 1.0
            if hit_rate > 0.45 and hits >= 4:
                scale *= 0.85
            elif hit_rate < 0.05 and uses >= 10:
                scale *= 1.15

            if share > 0.45 and damage >= 20:
                scale *= 0.90
            elif share < 0.05 and uses >= 10:
                scale *= 1.08

            scale = _clamp(scale, 0.75, 1.25)
            if abs(scale - 1.0) > 0.01:
                boss_ability_scales[ability_name] = scale
                notes.append(
                    f"{boss_name} -> {ability_name}: auto ability damage x{scale:.2f}"
                )

        if boss_ability_scales:
            ability_balance[boss_name] = boss_ability_scales

    return boss_balance, ability_balance, notes

