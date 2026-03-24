import json
import os
import shutil
from copy import deepcopy


class ProgressionSystem:
    PROFILE_VERSION = 1
    DEFAULT_LOADOUT_SIZE = 4

    def __init__(
        self,
        save_path="data/player_profile.json",
        relic_defs_path="data/relic_definitions.json",
    ):
        self.save_path = save_path
        self.relic_defs_path = relic_defs_path
        self.relic_definitions = {}
        self.profile = self._default_profile()
        self.load_relic_definitions()
        self.load_profile()

    def _default_profile(self):
        return {
            "version": self.PROFILE_VERSION,
            "player_identity": {
                "username": "Player",
                "color": [0, 100, 255],
                "hat": "None",
            },
            "currencies": {"credits": 0},
            "materials": {},
            "boss_kill_counts": {},
            "relic_inventory": {},
            "equipped_relics": [None] * self.DEFAULT_LOADOUT_SIZE,
            "meta_unlocks": {},
            "stats": {
                "total_runs": 0,
                "total_victories": 0,
                "deepest_boss_count": 0,
            },
        }

    def load_relic_definitions(self):
        if not os.path.exists(self.relic_defs_path):
            self.relic_definitions = {}
            return
        with open(self.relic_defs_path, "r", encoding="utf-8") as handle:
            payload = json.load(handle)
        relics = payload.get("relics", [])
        self.relic_definitions = {
            relic["id"]: relic for relic in relics if isinstance(relic, dict) and relic.get("id")
        }

    def load_profile(self):
        os.makedirs(os.path.dirname(self.save_path), exist_ok=True)
        if not os.path.exists(self.save_path):
            self.profile = self._default_profile()
            self.save_profile()
            return
        try:
            with open(self.save_path, "r", encoding="utf-8") as handle:
                payload = json.load(handle)
        except (OSError, json.JSONDecodeError):
            self._backup_corrupt_profile()
            self.profile = self._default_profile()
            self.save_profile()
            return

        self.profile = self._merge_profile(payload)
        self._sanitize_profile()
        self.save_profile()

    def _backup_corrupt_profile(self):
        if not os.path.exists(self.save_path):
            return
        backup_path = self.save_path + ".corrupt.bak"
        try:
            shutil.copyfile(self.save_path, backup_path)
        except OSError:
            pass

    def _merge_profile(self, payload):
        merged = self._default_profile()
        if not isinstance(payload, dict):
            return merged
        for key in merged:
            if key in payload and isinstance(payload[key], type(merged[key])):
                if isinstance(merged[key], dict):
                    merged[key].update(payload[key])
                elif isinstance(merged[key], list):
                    merged[key] = list(payload[key])
                else:
                    merged[key] = payload[key]
        merged["version"] = self.PROFILE_VERSION
        return merged

    def _sanitize_profile(self):
        identity = self.profile.get("player_identity", {})
        username = str(identity.get("username", "Player")).strip()[:16] or "Player"
        color = identity.get("color", [0, 100, 255])
        if not isinstance(color, (list, tuple)) or len(color) != 3:
            color = [0, 100, 255]
        self.profile["player_identity"] = {
            "username": username,
            "color": [max(0, min(255, int(channel))) for channel in color],
            "hat": str(identity.get("hat", "None")).strip() or "None",
        }

        loadout = list(self.profile.get("equipped_relics", []))
        if len(loadout) < self.DEFAULT_LOADOUT_SIZE:
            loadout.extend([None] * (self.DEFAULT_LOADOUT_SIZE - len(loadout)))
        loadout = loadout[: self.DEFAULT_LOADOUT_SIZE]
        seen = set()
        sanitized = []
        for relic_id in loadout:
            if (
                relic_id
                and relic_id in self.relic_definitions
                and self.profile["relic_inventory"].get(relic_id, {}).get("owned")
                and relic_id not in seen
            ):
                sanitized.append(relic_id)
                seen.add(relic_id)
            else:
                sanitized.append(None)
        self.profile["equipped_relics"] = sanitized

        inventory = {}
        for relic_id, entry in self.profile.get("relic_inventory", {}).items():
            if relic_id not in self.relic_definitions:
                continue
            rank = int(entry.get("rank", 0))
            max_rank = int(self.relic_definitions[relic_id].get("max_rank", 1))
            inventory[relic_id] = {
                "owned": bool(entry.get("owned", False)),
                "rank": max(0, min(max_rank, rank)),
            }
        self.profile["relic_inventory"] = inventory

    def save_profile(self):
        os.makedirs(os.path.dirname(self.save_path), exist_ok=True)
        with open(self.save_path, "w", encoding="utf-8") as handle:
            json.dump(self.profile, handle, indent=2)

    def canonical_boss_id_from_name(self, name):
        normalized = (name or "").strip().lower()
        slug = []
        last_was_sep = False
        for char in normalized:
            if char.isalnum():
                slug.append(char)
                last_was_sep = False
            elif not last_was_sep:
                slug.append("_")
                last_was_sep = True
        return "".join(slug).strip("_")

    def _get_meta_discount_multiplier(self):
        if self.profile["meta_unlocks"].get("relic_upgrade_discount"):
            return 0.9
        return 1.0

    def _credit_multiplier(self):
        unlocked = sum(
            1
            for key in ("credit_gain_1", "credit_gain_2", "credit_gain_3")
            if self.profile["meta_unlocks"].get(key)
        )
        return 1.0 + (0.1 * unlocked)

    def _essence_bonus(self):
        return 1 if self.profile["meta_unlocks"].get("essence_gain_bonus") else 0

    def _add_currency(self, key, amount):
        bucket = self.profile["currencies"]
        bucket[key] = int(bucket.get(key, 0)) + int(amount)

    def _add_material(self, key, amount):
        bucket = self.profile["materials"]
        bucket[key] = int(bucket.get(key, 0)) + int(amount)

    def _spend_cost(self, cost):
        credits = int(cost.get("credits", 0))
        self.profile["currencies"]["credits"] = max(
            0, int(self.profile["currencies"].get("credits", 0)) - credits
        )
        for key, amount in cost.items():
            if key == "credits":
                continue
            material_key = key.removeprefix("essence_")
            self.profile["materials"][material_key] = max(
                0, int(self.profile["materials"].get(material_key, 0)) - int(amount)
            )

    def _can_afford_cost(self, cost):
        if int(self.profile["currencies"].get("credits", 0)) < int(cost.get("credits", 0)):
            return False
        for key, amount in cost.items():
            if key == "credits":
                continue
            material_key = key.removeprefix("essence_")
            if int(self.profile["materials"].get(material_key, 0)) < int(amount):
                return False
        return True

    def grant_boss_rewards(self, boss, weakened=False, victory=False):
        boss_id = self.canonical_boss_id_from_name(getattr(boss, "name", "boss"))
        existing_kills = int(self.profile["boss_kill_counts"].get(boss_id, 0))
        credit_base = 70 if weakened else 100
        essence_base = 2 if weakened else 3
        credits = int(round(credit_base * self._credit_multiplier()))
        essence = essence_base + self._essence_bonus()
        first_time = existing_kills == 0
        if first_time:
            credits += int(round(150 * self._credit_multiplier()))
            essence += 5

        self._add_currency("credits", credits)
        self._add_material(boss_id, essence)
        self.profile["boss_kill_counts"][boss_id] = existing_kills + 1
        self.save_profile()

        rewards = {
            "credits": credits,
            "materials": {boss_id: essence},
            "first_time": first_time,
            "boss_name": getattr(boss, "name", "Boss"),
        }
        if victory:
            rewards["victory"] = self.grant_run_victory_bonus()
        return rewards

    def grant_run_victory_bonus(self):
        credits = int(round(300 * self._credit_multiplier()))
        self._add_currency("credits", credits)
        self.profile["stats"]["total_victories"] = int(
            self.profile["stats"].get("total_victories", 0)
        ) + 1
        self.save_profile()
        return {"credits": credits}

    def record_run_started(self):
        self.profile["stats"]["total_runs"] = int(
            self.profile["stats"].get("total_runs", 0)
        ) + 1
        self.save_profile()

    def update_deepest_boss_count(self, defeated_count):
        current = int(self.profile["stats"].get("deepest_boss_count", 0))
        if defeated_count > current:
            self.profile["stats"]["deepest_boss_count"] = int(defeated_count)
            self.save_profile()

    def can_craft_relic(self, relic_id):
        relic = self.relic_definitions.get(relic_id)
        if not relic:
            return False
        entry = self.profile["relic_inventory"].get(relic_id, {})
        if entry.get("owned"):
            return False
        return self._can_afford_cost(relic.get("unlock_cost", {}))

    def craft_relic(self, relic_id):
        if not self.can_craft_relic(relic_id):
            return False
        relic = self.relic_definitions[relic_id]
        self._spend_cost(relic.get("unlock_cost", {}))
        self.profile["relic_inventory"][relic_id] = {"owned": True, "rank": 1}
        self.save_profile()
        return True

    def can_upgrade_relic(self, relic_id):
        relic = self.relic_definitions.get(relic_id)
        entry = self.profile["relic_inventory"].get(relic_id, {})
        if not relic or not entry.get("owned"):
            return False
        current_rank = int(entry.get("rank", 0))
        max_rank = int(relic.get("max_rank", 1))
        if current_rank >= max_rank:
            return False
        rank_costs = relic.get("rank_costs", [])
        if current_rank - 1 >= len(rank_costs):
            return False
        cost = self._discounted_cost(rank_costs[current_rank - 1])
        return self._can_afford_cost(cost)

    def _discounted_cost(self, cost):
        multiplier = self._get_meta_discount_multiplier()
        discounted = {}
        for key, amount in cost.items():
            discounted[key] = max(1, int(round(int(amount) * multiplier)))
        return discounted

    def upgrade_relic(self, relic_id):
        if not self.can_upgrade_relic(relic_id):
            return False
        relic = self.relic_definitions[relic_id]
        entry = self.profile["relic_inventory"][relic_id]
        current_rank = int(entry.get("rank", 0))
        cost = self._discounted_cost(relic.get("rank_costs", [])[current_rank - 1])
        self._spend_cost(cost)
        entry["rank"] = current_rank + 1
        self.save_profile()
        return True

    def equip_relic(self, relic_id, slot_index):
        if relic_id not in self.relic_definitions:
            return False
        entry = self.profile["relic_inventory"].get(relic_id, {})
        if not entry.get("owned"):
            return False
        if not 0 <= slot_index < self.DEFAULT_LOADOUT_SIZE:
            return False
        loadout = self.profile["equipped_relics"]
        if relic_id in loadout and loadout[slot_index] != relic_id:
            return False
        loadout[slot_index] = relic_id
        self.save_profile()
        return True

    def unequip_relic(self, slot_index):
        if 0 <= slot_index < self.DEFAULT_LOADOUT_SIZE:
            self.profile["equipped_relics"][slot_index] = None
            self.save_profile()

    def get_equipped_relics(self):
        return list(self.profile.get("equipped_relics", []))

    def get_relic_entry(self, relic_id):
        return deepcopy(self.profile["relic_inventory"].get(relic_id, {"owned": False, "rank": 0}))

    def get_all_relics(self):
        return [self.relic_definitions[key] for key in sorted(self.relic_definitions.keys())]

    def get_visible_relics(self):
        visible = []
        for relic in self.get_all_relics():
            relic_id = relic.get("id")
            entry = self.profile["relic_inventory"].get(relic_id, {})
            if entry.get("owned"):
                visible.append(relic)
                continue
            boss_key = self.canonical_boss_id_from_name(relic.get("source_boss", ""))
            if int(self.profile["boss_kill_counts"].get(boss_key, 0)) > 0:
                visible.append(relic)
        return visible

    def get_player_identity(self):
        identity = deepcopy(self.profile.get("player_identity", {}))
        color = identity.get("color", [0, 100, 255])
        identity["color"] = tuple(color) if isinstance(color, list) else tuple(color)
        return identity

    def get_lobby_profile(self):
        identity = self.get_player_identity()
        loadout = []
        for relic_id in self.get_equipped_relics():
            if not relic_id:
                continue
            relic = self.relic_definitions.get(relic_id, {})
            entry = self.get_relic_entry(relic_id)
            loadout.append(
                {
                    "id": relic_id,
                    "name": relic.get("name", relic_id),
                    "rank": int(entry.get("rank", 1)),
                }
            )
        identity["loadout"] = loadout
        return identity

    def update_player_identity(self, username=None, color=None, hat=None):
        identity = self.profile.get("player_identity", {})
        if username is not None:
            identity["username"] = str(username).strip()[:16] or "Player"
        if color is not None:
            if isinstance(color, tuple):
                color = list(color)
            if isinstance(color, list) and len(color) == 3:
                identity["color"] = [max(0, min(255, int(channel))) for channel in color]
        if hat is not None:
            identity["hat"] = str(hat).strip() or "None"
        self.profile["player_identity"] = identity
        self.save_profile()

    def get_active_relic_effects(self):
        active = []
        for relic_id in self.profile.get("equipped_relics", []):
            if not relic_id:
                continue
            relic = self.relic_definitions.get(relic_id)
            entry = self.profile["relic_inventory"].get(relic_id, {})
            if not relic or not entry.get("owned"):
                continue
            active.append(
                {
                    "id": relic_id,
                    "name": relic.get("name", relic_id),
                    "rank": int(entry.get("rank", 1)),
                    "effects": self._scaled_effects(relic, int(entry.get("rank", 1))),
                }
            )
        return active

    def _scaled_effects(self, relic, rank):
        rank = max(1, rank)
        effects = {}
        for key, value in relic.get("effects", {}).items():
            if isinstance(value, (int, float)):
                effects[key] = value * rank
            else:
                effects[key] = value
        return effects

    def get_player_meta_modifiers(self):
        modifiers = {
            "max_health_flat": 0,
            "base_speed_flat": 0.0,
            "dash_speed_mult": 1.0,
            "dash_cooldown_mult": 1.0,
            "shoot_cooldown_mult": 1.0,
            "damage_taken_mult": 1.0,
            "projectile_damage_flat": 0,
            "projectile_speed_flat": 0.0,
            "reflect_charges_flat": 0,
            "regen_level_flat": 0,
            "spread_shot_level_flat": 0,
            "piercing_shots": False,
            "starting_heal_flat": 0,
            "shield_max_flat": 0,
            "shield_regen_delay_frames": 0,
            "shield_regen_rate_flat": 0,
        }

        if self.profile["meta_unlocks"].get("starting_heal_bonus"):
            modifiers["starting_heal_flat"] += 10

        for active in self.get_active_relic_effects():
            for key, value in active["effects"].items():
                if key in (
                    "dash_speed_mult",
                    "dash_cooldown_mult",
                    "shoot_cooldown_mult",
                    "damage_taken_mult",
                ):
                    modifiers[key] *= float(value)
                elif key == "piercing_shots":
                    modifiers[key] = modifiers[key] or bool(value)
                else:
                    modifiers[key] = modifiers.get(key, 0) + value
        return modifiers

    def apply_meta_bonuses_to_player(self, player):
        player.reset_to_run_base_stats()
        player.apply_meta_modifier_bundle(self.get_player_meta_modifiers())
