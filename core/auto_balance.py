import json
import os
import logging
from datetime import datetime
from typing import Dict, List

class AutoBalanceSystem:
    def __init__(self, data_file="data/boss_performance_log.json"):
        self.logger = logging.getLogger(__name__)
        self.data_file = data_file
        self.balance_file = "data/balance_adjustments.json"
        self.performance_history = []
        self.balance_adjustments = {}
        self.min_fights_for_balance = 3
        self._last_balance_check = 0.0
        self.load_balance_data()
        
    def load_balance_data(self):
        """Load existing balance adjustments"""
        try:
            if os.path.exists(self.balance_file):
                with open(self.balance_file, 'r', encoding='utf-8') as f:
                    self.balance_adjustments = json.load(f)
        except (OSError, json.JSONDecodeError) as e:
            self.logger.warning("Failed to read balance file %s: %s", self.balance_file, e)
            self.balance_adjustments = {}
            
    def save_balance_data(self):
        """Save balance adjustments to file"""
        try:
            os.makedirs(os.path.dirname(self.balance_file), exist_ok=True)
            with open(self.balance_file, 'w', encoding='utf-8') as f:
                json.dump(self.balance_adjustments, f, indent=2)
        except OSError as e:
            self.logger.error("Failed to save balance data: %s", e)
            
    def load_performance_data(self):
        """Load and analyze recent performance data"""
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if 'session' in data and 'bosses' in data['session']:
                        return data['session']['bosses']
        except (OSError, json.JSONDecodeError) as e:
            self.logger.error("Failed to load performance data: %s", e)
        return {}
        
    def analyze_boss_performance(self, boss_name: str, boss_data: Dict) -> Dict:
        """Analyze performance metrics for a single boss"""
        if not boss_data:
            return {}
            
        victory_rate = 1.0 if boss_data.get('victory', False) else 0.0
        fight_duration = boss_data.get('fight_duration', 0)
        damage_taken = boss_data.get('damage_taken', 0)
        player_damage_taken = boss_data.get('player_damage_taken', 0)
        attacks_landed = boss_data.get('attacks_landed', 0)
        player_attacks_landed = boss_data.get('player_attacks_landed', 0)
        
        # Calculate derived metrics
        boss_dps = damage_taken / max(fight_duration, 1) if fight_duration > 0 else 0
        player_dps = player_damage_taken / max(fight_duration, 1) if fight_duration > 0 else 0
        hit_rate = attacks_landed / max(player_attacks_landed, 1) if player_attacks_landed > 0 else 0
        
        return {
            'victory_rate': victory_rate,
            'fight_duration': fight_duration,
            'boss_dps': boss_dps,
            'player_dps': player_dps,
            'hit_rate': hit_rate,
            'damage_taken': damage_taken,
            'player_damage_taken': player_damage_taken
        }
        
    def get_balance_recommendations(self, boss_name: str, performance_data: List[Dict]) -> Dict:
        """Generate balance recommendations based on performance data"""
        if len(performance_data) < self.min_fights_for_balance:
            return {}
            
        # Aggregate performance data
        total_fights = len(performance_data)
        victories = sum(1 for fight in performance_data if fight.get('victory_rate', 0) > 0)
        victory_rate = victories / total_fights
        avg_duration = sum(fight.get('fight_duration', 0) for fight in performance_data) / total_fights
        avg_boss_dps = sum(fight.get('boss_dps', 0) for fight in performance_data) / total_fights
        avg_player_dps = sum(fight.get('player_dps', 0) for fight in performance_data) / total_fights
        
        recommendations = {}
        
        # Victory rate balancing
        if victory_rate < 0.3:  # Too hard
            recommendations['health_multiplier'] = 0.85
            recommendations['damage_multiplier'] = 0.8
            recommendations['speed_multiplier'] = 0.9
        elif victory_rate > 0.8:  # Too easy
            recommendations['health_multiplier'] = 1.15
            recommendations['damage_multiplier'] = 1.1
            recommendations['speed_multiplier'] = 1.05
        else:
            recommendations['health_multiplier'] = 1.0
            recommendations['damage_multiplier'] = 1.0
            recommendations['speed_multiplier'] = 1.0
            
        # Duration balancing
        if avg_duration < 15:  # Too short
            recommendations['health_multiplier'] *= 1.2
        elif avg_duration > 80:  # Too long
            recommendations['health_multiplier'] *= 0.9
            recommendations['damage_multiplier'] *= 1.1
            
        # DPS balancing
        if avg_boss_dps > 80:  # Boss deals too much damage
            recommendations['damage_multiplier'] *= 0.85
        elif avg_boss_dps < 30:  # Boss deals too little damage
            recommendations['damage_multiplier'] *= 1.15
            
        # Player DPS balancing (indicates difficulty)
        if avg_player_dps < 5:  # Player can't damage boss effectively
            recommendations['health_multiplier'] *= 0.95
            recommendations['speed_multiplier'] *= 0.95
            
        # Clamp multipliers to reasonable ranges
        recommendations['health_multiplier'] = max(0.5, min(2.0, recommendations['health_multiplier']))
        recommendations['damage_multiplier'] = max(0.5, min(2.0, recommendations['damage_multiplier']))
        recommendations['speed_multiplier'] = max(0.5, min(2.0, recommendations['speed_multiplier']))
        
        return recommendations
        
    def update_balance_adjustments(self):
        """Update balance adjustments based on recent performance"""
        performance_data = self.load_performance_data()
        
        for boss_name, boss_data in performance_data.items():
            performance = self.analyze_boss_performance(boss_name, boss_data)
            
            # Store performance for trend analysis
            if boss_name not in self.balance_adjustments:
                self.balance_adjustments[boss_name] = {
                    'performance_history': [],
                    'current_adjustments': {},
                    'last_updated': None
                }
                
            self.balance_adjustments[boss_name]['performance_history'].append({
                'timestamp': datetime.now().isoformat(),
                'performance': performance
            })
            
            # Keep only last 10 performances
            if len(self.balance_adjustments[boss_name]['performance_history']) > 10:
                self.balance_adjustments[boss_name]['performance_history'] = \
                    self.balance_adjustments[boss_name]['performance_history'][-10:]
                    
            # Generate new recommendations
            recent_performances = [entry['performance'] for entry in 
                                 self.balance_adjustments[boss_name]['performance_history']]
            recommendations = self.get_balance_recommendations(boss_name, recent_performances)
            
            if recommendations:
                self.balance_adjustments[boss_name]['current_adjustments'] = recommendations
                self.balance_adjustments[boss_name]['last_updated'] = datetime.now().isoformat()
                
        self.save_balance_data()
        
    def get_boss_adjustments(self, boss_name: str) -> Dict:
        """Get current balance adjustments for a specific boss"""
        return self.balance_adjustments.get(boss_name, {}).get('current_adjustments', {})
        
    def apply_adjustments_to_boss(self, boss):
        """Apply balance adjustments to a boss instance"""
        boss_name = boss.name
        adjustments = self.get_boss_adjustments(boss_name)
        
        if not adjustments:
            return
            
        # Apply health adjustments
        if 'health_multiplier' in adjustments:
            original_max_health = getattr(boss, '_original_max_health', boss.max_health)
            if not hasattr(boss, '_original_max_health'):
                boss._original_max_health = boss.max_health
            boss.max_health = int(original_max_health * adjustments['health_multiplier'])
            boss.health = min(boss.health, boss.max_health)
            
        # Apply damage adjustments
        if 'damage_multiplier' in adjustments:
            boss._damage_multiplier = adjustments['damage_multiplier']
            
        # Apply speed adjustments
        if 'speed_multiplier' in adjustments:
            boss._speed_multiplier = adjustments['speed_multiplier']
            
    def log_balance_change(self, boss_name: str, adjustments: Dict):
        """Log balance changes for debugging"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.logger.info("[%s] Auto-balance: %s", timestamp, boss_name)
        for key, value in adjustments.items():
            self.logger.info("  %s: %.2f", key, value)
            
    def should_run_balance_check(self) -> bool:
        """Check if enough time has passed to run balance check"""
        current_time = datetime.now().timestamp()
        # Run balance check every 5 minutes or at startup
        if self._last_balance_check == 0 or current_time - self._last_balance_check > 300:
            self._last_balance_check = current_time
            return True
        return False
