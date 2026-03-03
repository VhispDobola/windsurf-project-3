import json
import time
import logging
from datetime import datetime

class PerformanceLogger:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.session_data = {
            "session_start": datetime.now().isoformat(),
            "bosses": {},
            "total_damage_dealt": 0,
            "total_time_spent": 0,
            "player_deaths": 0
        }
        self._last_tick_time = None
        
    def start_boss_fight(self, boss_name):
        self.session_data["bosses"][boss_name] = {
            "start_time": time.time(),
            "damage_taken": 0,
            "player_damage_taken": 0,
            "attacks_landed": 0,
            "player_attacks_landed": 0,
            "phase_changes": 0,
            "special_abilities_used": 0,
            "ability_damage": {},  # Track damage by specific ability
            "ability_stats": {},   # Track ability uses/hits/damage
            "phase_time": {},       # Seconds spent in each phase
            "health_samples": [],   # (timestamp, health, max_health)
            "player_health_samples": [],  # (timestamp, health, max_health)
            "events": []            # Timeline of notable events
        }
        self._last_tick_time = time.time()

    def tick_frame(self, player, bosses):
        """Record per-frame/per-tick stats for bosses and player."""
        if not bosses:
            return
        now = time.time()
        if self._last_tick_time is None:
            self._last_tick_time = now
        delta = max(0.0, now - self._last_tick_time)
        self._last_tick_time = now

        for boss in bosses:
            if boss.name not in self.session_data["bosses"]:
                # Safety: initialize if missing
                self.start_boss_fight(boss.name)
            data = self.session_data["bosses"][boss.name]

            # Phase timing
            phase_key = f"phase_{getattr(boss, 'phase', 1)}"
            data["phase_time"][phase_key] = data["phase_time"].get(phase_key, 0.0) + delta

            # Health samples (sparse)
            if len(data["health_samples"]) == 0 or (now - data["health_samples"][-1][0]) > 0.5:
                data["health_samples"].append((now, boss.health, boss.max_health))

            # Player health samples (sparse)
            if player is not None:
                if len(data["player_health_samples"]) == 0 or (now - data["player_health_samples"][-1][0]) > 0.5:
                    data["player_health_samples"].append((now, player.health, player.max_health))

    def log_event(self, boss_name, event_type, details=None):
        """Log a structured event for later analysis."""
        if boss_name in self.session_data["bosses"]:
            self.session_data["bosses"][boss_name]["events"].append({
                "time": time.time(),
                "type": event_type,
                "details": details or {}
            })
        
    def log_damage(self, boss_name, damage, damage_to_player=False):
        if boss_name in self.session_data["bosses"]:
            if damage_to_player:
                # Damage dealt to player by boss
                self.session_data["bosses"][boss_name]["player_damage_taken"] += damage
            else:
                # Damage dealt to boss by player
                self.session_data["bosses"][boss_name]["damage_taken"] += damage
                self.session_data["total_damage_dealt"] += damage
                
    def log_attack(self, boss_name, is_player_attack=False):
        if boss_name in self.session_data["bosses"]:
            if is_player_attack:
                self.session_data["bosses"][boss_name]["player_attacks_landed"] += 1
            else:
                self.session_data["bosses"][boss_name]["attacks_landed"] += 1
                
    def log_phase_change(self, boss_name):
        if boss_name in self.session_data["bosses"]:
            self.session_data["bosses"][boss_name]["phase_changes"] += 1
            
    def log_special_ability(self, boss_name):
        if boss_name in self.session_data["bosses"]:
            self.session_data["bosses"][boss_name]["special_abilities_used"] += 1
            
    def log_ability_damage(self, boss_name, ability_name, damage):
        """Log damage dealt by a specific ability"""
        if boss_name in self.session_data["bosses"]:
            if ability_name not in self.session_data["bosses"][boss_name]["ability_damage"]:
                self.session_data["bosses"][boss_name]["ability_damage"][ability_name] = 0
            self.session_data["bosses"][boss_name]["ability_damage"][ability_name] += damage

            # Track ability hit stats
            ability_stats = self.session_data["bosses"][boss_name]["ability_stats"]
            if ability_name not in ability_stats:
                ability_stats[ability_name] = {"uses": 0, "hits": 0, "damage": 0}
            ability_stats[ability_name]["hits"] += 1
            ability_stats[ability_name]["damage"] += damage

    def log_ability_use(self, boss_name, ability_name):
        """Log an ability use (e.g., projectile fired, hazard created)."""
        if boss_name in self.session_data["bosses"]:
            ability_stats = self.session_data["bosses"][boss_name]["ability_stats"]
            if ability_name not in ability_stats:
                ability_stats[ability_name] = {"uses": 0, "hits": 0, "damage": 0}
            ability_stats[ability_name]["uses"] += 1
            
    def end_boss_fight(self, boss_name, victory):
        self.logger.info("Ending boss fight: %s, Victory: %s", boss_name, victory)
        if boss_name in self.session_data["bosses"]:
            fight_time = time.time() - self.session_data["bosses"][boss_name]["start_time"]
            self.session_data["bosses"][boss_name]["end_time"] = time.time()
            self.session_data["bosses"][boss_name]["fight_duration"] = fight_time
            self.session_data["bosses"][boss_name]["victory"] = victory
            self.session_data["total_time_spent"] += fight_time
            self.logger.info("Fight duration: %.2fs", fight_time)
            
            if not victory:
                self.session_data["player_deaths"] += 1
        else:
            self.logger.warning("Boss %s not found in session data", boss_name)
                
    def analyze_performance(self):
        analysis = {
            "boss_rankings": [],
            "recommendations": [],
            "balance_issues": []
        }
        
        for boss_name, data in self.session_data["bosses"].items():
            if "fight_duration" in data:
                dps = data["damage_taken"] / max(data["fight_duration"], 1)
                player_dps = data["player_damage_taken"] / max(data["fight_duration"], 1)
                phase_time = data.get("phase_time", {})
                phase_summary = {k: round(v, 2) for k, v in phase_time.items()}
                ability_stats = data.get("ability_stats", {})
                ability_summary = {}
                for ability, stats in ability_stats.items():
                    uses = stats.get("uses", 0)
                    hits = stats.get("hits", 0)
                    ability_summary[ability] = {
                        "uses": uses,
                        "hits": hits,
                        "damage": stats.get("damage", 0),
                        "hit_rate": round(hits / uses, 3) if uses > 0 else 0.0
                    }
                
                analysis["boss_rankings"].append({
                    "name": boss_name,
                    "duration": data["fight_duration"],
                    "boss_dps": dps,
                    "player_dps": player_dps,
                    "damage_taken": data["damage_taken"],
                    "attacks_landed": data["attacks_landed"],
                    "victory": data.get("victory", False),
                    "phase_time": phase_summary,
                    "ability_stats": ability_summary
                })
                
        # Sort by difficulty (longer duration = harder)
        analysis["boss_rankings"].sort(key=lambda boss: boss["duration"], reverse=True)
        
        # Generate recommendations
        for boss in analysis["boss_rankings"]:
            if boss["duration"] < 30:  # Too easy
                analysis["recommendations"].append(f"{boss['name']}: Increase health or add more complex patterns")
                analysis["balance_issues"].append(boss["name"])
            elif boss["duration"] > 180:  # Too hard
                analysis["recommendations"].append(f"{boss['name']}: Reduce health or simplify patterns")
                
            if boss["boss_dps"] < 10:  # Low damage output
                analysis["recommendations"].append(f"{boss['name']}: Increase damage output")
                analysis["balance_issues"].append(boss["name"])
                
        return analysis
        
    def save_session(self):
        try:
            self.logger.info("Saving performance session...")
            # Create data directory if it doesn't exist
            import os
            if not os.path.exists("data"):
                os.makedirs("data")
                self.logger.info("Created data directory")
            
            payload = {
                "session": self.session_data,
                "analysis": self.analyze_performance()
            }

            with open("data/boss_performance_log.json", "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2)
            
            self.export_csv("data/boss_performance_log.csv", payload)
            self.logger.info("Performance data saved to data/boss_performance_log.json")
            self.logger.info("Session data: %s bosses recorded", len(self.session_data["bosses"]))
        except OSError as e:
            self.logger.error("Failed to save performance data: %s", e)

    def export_csv(self, path, payload=None):
        """Export a flat CSV summary for tuning."""
        import csv
        if payload is None:
            payload = {
                "session": self.session_data,
                "analysis": self.analyze_performance()
            }
        
        rows = []
        for boss_name, data in payload["session"]["bosses"].items():
            duration = data.get("fight_duration", 0)
            phase_time = data.get("phase_time", {})
            rows.append({
                "boss": boss_name,
                "duration_s": round(duration, 2),
                "damage_taken": data.get("damage_taken", 0),
                "player_damage_taken": data.get("player_damage_taken", 0),
                "attacks_landed": data.get("attacks_landed", 0),
                "player_attacks_landed": data.get("player_attacks_landed", 0),
                "phase_changes": data.get("phase_changes", 0),
                "special_abilities_used": data.get("special_abilities_used", 0),
                "phase_1_s": round(phase_time.get("phase_1", 0), 2),
                "phase_2_s": round(phase_time.get("phase_2", 0), 2),
                "phase_3_s": round(phase_time.get("phase_3", 0), 2),
                "victory": data.get("victory", False)
            })
        
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()) if rows else [
                "boss", "duration_s", "damage_taken", "player_damage_taken",
                "attacks_landed", "player_attacks_landed", "phase_changes",
                "special_abilities_used", "phase_1_s", "phase_2_s", "phase_3_s", "victory"
            ])
            writer.writeheader()
            if rows:
                writer.writerows(rows)
            
    def print_analysis(self):
        analysis = self.analyze_performance()
        self.logger.info("\n%s", "=" * 50)
        self.logger.info("BOSS PERFORMANCE ANALYSIS")
        self.logger.info("%s", "=" * 50)
        
        self.logger.info("\nBoss Rankings (by difficulty):")
        for i, boss in enumerate(analysis["boss_rankings"], 1):
            status = "VICTORY" if boss["victory"] else "DEFEAT"
            self.logger.info("%s. %s - %.1fs - %s", i, boss["name"], boss["duration"], status)
            self.logger.info("   Boss DPS: %.1f | Player DPS: %.1f", boss["boss_dps"], boss["player_dps"])
            self.logger.info("   Damage Dealt: %s | Attacks Landed: %s", boss["damage_taken"], boss["attacks_landed"])
            
        # Show ability damage breakdown
        self.logger.info("\n%s", "=" * 50)
        self.logger.info("ABILITY DAMAGE BREAKDOWN")
        self.logger.info("%s", "=" * 50)
        
        for boss_name, data in self.session_data["bosses"].items():
            if data.get("ability_damage"):
                self.logger.info("\n%s:", boss_name)
                total_ability_damage = sum(data["ability_damage"].values())
                for ability, damage in sorted(data["ability_damage"].items(), key=lambda x: x[1], reverse=True):
                    percentage = (damage / total_ability_damage * 100) if total_ability_damage > 0 else 0
                    self.logger.info("  %s: %s damage (%.1f%%)", ability, damage, percentage)
                self.logger.info("  Total Ability Damage: %s", total_ability_damage)
            else:
                self.logger.info("\n%s: No ability damage tracked", boss_name)
            
        if analysis["recommendations"]:
            self.logger.info("\nBalance Recommendations:")
            for rec in analysis["recommendations"]:
                self.logger.info("- %s", rec)
                
        self.logger.info("%s", "=" * 50)
