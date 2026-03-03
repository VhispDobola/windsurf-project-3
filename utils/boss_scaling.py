import random

def apply_weakening(boss, health_reduction=0.35, damage_reduction=0.25):
    """Apply weakening effects to a boss for paired fights"""
    # Reduce health
    original_health = boss.max_health
    boss.max_health = int(original_health * (1 - health_reduction))
    boss.health = boss.max_health
    
    # Store original values
    boss.original_max_health = original_health
    boss.is_weakened = True
    
    # Reduce attack damage if boss has damage attributes
    if hasattr(boss, 'projectile_damage'):
        boss.original_projectile_damage = boss.projectile_damage
        boss.projectile_damage = int(boss.projectile_damage * (1 - damage_reduction))
    
    # Reduce ability damage values
    if hasattr(boss, 'lava_pools'):
        for pool in boss.lava_pools:
            if 'damage' in pool:
                pool['damage'] = int(pool['damage'] * (1 - damage_reduction))
    
    if hasattr(boss, 'molten_ground'):
        for ground in boss.molten_ground:
            if 'damage' in ground:
                ground['damage'] = int(ground['damage'] * (1 - damage_reduction))
    
    # Reduce cooldown times (make attacks less frequent)
    if hasattr(boss, 'eruption_timer'):
        boss.eruption_timer = int(boss.eruption_timer * 1.3)
    if hasattr(boss, 'lava_wave_timer'):
        boss.lava_wave_timer = int(boss.lava_wave_timer * 1.3)
    
    return boss

def get_balanced_pair(boss_classes):
    """Get a balanced pair of bosses avoiding similar mechanics"""
    # Define boss categories to avoid pairing similar types
    categories = {
        'elemental': ['MagmaSovereign', 'IceTyrant', 'TempestLord', 'ThunderEmperor'],
        'tech': ['CyberOverlord', 'TheVirusQueen', 'NexusCore'],
        'magic': ['Chronomancer', 'VoidAssassin'],
        'physical': ['EternalGuardian', 'BladeMaster', 'EternalDragon'],
        'special': ['ImmortalPhoenix', 'CrystallineDestroyer']
    }
    
    # Try to avoid same category pairs
    attempts = 0
    while attempts < 10:
        selected = random.sample(boss_classes, 2)
        boss1_name = selected[0].__name__
        boss2_name = selected[1].__name__
        
        # Check if they're in different categories
        different_categories = True
        for category, bosses in categories.items():
            if boss1_name in bosses and boss2_name in bosses:
                different_categories = False
                break
        
        if different_categories or attempts >= 5:  # Allow same category after 5 attempts
            return selected
        
        attempts += 1
    
    return random.sample(boss_classes, 2)

def position_boss_pair(boss1, boss2, screen_width, screen_height):
    """Position two bosses on screen without overlap"""
    # Position bosses on opposite sides
    margin = 100
    y_position = 100
    
    boss1.x = margin
    boss1.y = y_position
    boss1.update_rect()
    
    boss2.x = screen_width - margin - boss2.width
    boss2.y = y_position
    boss2.update_rect()
    
    return boss1, boss2
