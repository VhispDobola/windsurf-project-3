"""
Collision detection and damage handling system
"""

import math
import pygame
from .damage_source import ProjectileDamageSource, TelegraphDamageSource, HazardDamageSource
from .spatial_partition import SpatialGrid


class CollisionSystem:
    """Handles all collision detection and damage calculations"""
    
    def __init__(self, performance_logger=None, width=1000, height=700):
        self.performance_logger = performance_logger
        self.spatial_grid = SpatialGrid(width, height, cell_size=64)
        self.hazard_cooldowns = {}
    
    def handle_collisions(self, player, bosses):
        """Handle all collisions between player and bosses"""
        if not bosses:
            return
            
        # Update spatial grid
        self.spatial_grid.clear()
        self._populate_grid(player, bosses)
        # Keep as list: hazard/projectile containers may include dicts (unhashable).
        nearby_objects = self.spatial_grid.get_nearby_objects(player)
        
        damage_sources = self._collect_damage_sources(bosses, nearby_objects)
        player_rect = player.get_rect()
        total_damage = 0
        
        # Handle special boss collisions (like Blade Master charge)
        total_damage += self._handle_special_collisions(player, bosses)
        
        # Handle projectile and effect collisions with spatial optimization
        for damage_source in damage_sources:
            if damage_source.active:
                damage = damage_source.check_collision(player_rect)
                if damage > 0:
                    damage = int(damage * getattr(damage_source, 'damage_scale', 1.0))
                    # Consume one-hit sources on first contact, even if player is
                    # currently invincible, to prevent sticky overlap damage.
                    damage_source.deactivate()
                    if player.take_damage(damage):
                        total_damage += damage
                        self._log_damage(bosses[0], damage)
                        self._log_ability_hit(damage_source, damage)
        
        # Handle player projectiles hitting bosses with spatial optimization
        self._handle_player_projectiles(player, bosses)
        
        return total_damage
    
    def _populate_grid(self, player, bosses):
        """Populate spatial grid with all objects"""
        # Add player
        self.spatial_grid.add_object(player)
        
        # Add bosses
        for boss in bosses:
            self.spatial_grid.add_object(boss)
        
        # Add projectiles
        for boss in bosses:
            for projectile in boss.get_all_projectiles():
                if self._is_projectile_like(projectile):
                    self.spatial_grid.add_object(projectile)
        
        # Add player projectiles
        for projectile in player.projectiles:
            self.spatial_grid.add_object(projectile)
    
    def _collect_damage_sources(self, bosses, nearby_objects=None):
        """Collect all damage sources from bosses"""
        damage_sources = []
        
        for boss in bosses:
            ability_balance = getattr(boss, "dynamic_ability_balance", {})
            # Add projectiles
            for projectile in boss.get_all_projectiles():
                if not self._is_projectile_like(projectile):
                    continue
                if nearby_objects is not None and projectile not in nearby_objects:
                    continue
                if not hasattr(projectile, 'parent_list'):
                    if hasattr(boss, 'get_projectile_parent_list'):
                        projectile.parent_list = boss.get_projectile_parent_list(projectile)
                    else:
                        projectile.parent_list = boss.projectiles
                damage_sources.append(ProjectileDamageSource(projectile))
                ability_name = self._get_ability_name(projectile)
                ability_scale = ability_balance.get(ability_name, 1.0) if ability_name else 1.0
                damage_sources[-1].damage_scale = getattr(boss, 'damage_scale', 1.0) * ability_scale
                damage_sources[-1].boss_name = boss.name
                self._tag_ability_use(boss, projectile)
            
            # Add telegraphs
            for effect in boss.effects:
                if hasattr(effect, 'check_collision'):
                    damage_sources.append(TelegraphDamageSource(effect))
                    ability_name = self._get_ability_name(effect)
                    ability_scale = ability_balance.get(ability_name, 1.0) if ability_name else 1.0
                    damage_sources[-1].damage_scale = getattr(boss, 'damage_scale', 1.0) * ability_scale
                    damage_sources[-1].boss_name = boss.name
                    self._tag_ability_use(boss, effect)
            
            # Add hazards
            if hasattr(boss, 'arena_hazards'):
                self._update_hazard_cooldowns(boss)
                hazard_cooldown_dict = getattr(boss, 'hazard_damage_cooldown', self.hazard_cooldowns)
                for hazard in boss.arena_hazards:
                    if isinstance(hazard, dict):
                        damage_sources.append(HazardDamageSource(hazard, hazard_cooldown_dict))
                        ability_name = hazard.get("ability_name")
                        ability_scale = ability_balance.get(ability_name, 1.0) if ability_name else 1.0
                        damage_sources[-1].damage_scale = getattr(boss, 'damage_scale', 1.0) * ability_scale
                        damage_sources[-1].boss_name = boss.name
                        self._tag_ability_use(boss, hazard)
        
        return damage_sources

    def _is_projectile_like(self, projectile):
        """Return True for projectile objects that work with generic collision flow."""
        return hasattr(projectile, 'get_rect') and hasattr(projectile, 'damage')

    def _tag_ability_use(self, boss, obj):
        """Tag and log ability usage for projectiles/effects/hazards."""
        if not self.performance_logger or not boss:
            return

        if isinstance(obj, dict):
            ability_name = obj.get('ability_name')
            if ability_name and not obj.get('_ability_logged'):
                self.performance_logger.log_ability_use(boss.name, ability_name)
                obj['_ability_logged'] = True
            return

        if hasattr(obj, '_ability_logged') and obj._ability_logged:
            return

        ability_name = self._get_ability_name(obj)
        if ability_name:
            self.performance_logger.log_ability_use(boss.name, ability_name)
            obj._ability_logged = True
            obj.ability_name = ability_name

    def _get_ability_name(self, obj):
        """Derive ability name from object flags."""
        flag_map = [
            ('mutation', 'Mutation Burst'),
            ('red_virus', 'Red Virus'),
            ('cluster', 'Cluster Burst'),
            ('mega_cluster', 'Mega Cluster Burst'),
            ('homing', 'Homing Projectile'),
            ('laser', 'Laser'),
            ('beam', 'Prism Beam'),
            ('chain', 'Chain Lightning'),
            ('antibody', 'Antibody'),
            ('phoenix', 'Phoenix Flame'),
            ('solar', 'Solar Flare'),
            ('fire', 'Fire Breath'),
            ('ice', 'Ice Shards'),
            ('lightning', 'Lightning Strike'),
            ('diamond', 'Diamond Storm'),
            ('crystalline', 'Crystalline Shards'),
            ('prism', 'Prism Beam'),
            ('time', 'Time Attack'),
            ('rewind', 'Time Rewind'),
            ('freeze', 'Time Freeze'),
            ('glitch', 'Matrix Glitch'),
            ('bouncing', 'Bouncing Shot'),
            ('spiral', 'Spiral Shot'),
            ('seeking', 'Seeking Shot'),
            ('pellet', 'Pellet'),
            ('claw', 'Claw Swipe'),
            ('gust', 'Wing Gust'),
        ]
        for attr, name in flag_map:
            if hasattr(obj, attr) and getattr(obj, attr):
                return name
        return getattr(obj, 'ability_name', None)

    def _get_hazard_rect(self, hazard):
        """Create a rect for a hazard dict if possible"""
        if 'radius' in hazard:
            radius = hazard['radius']
            return pygame.Rect(hazard['x'] - radius, hazard['y'] - radius, radius * 2, radius * 2)
        if 'width' in hazard and 'height' in hazard:
            return pygame.Rect(hazard['x'] - hazard['width'] // 2,
                               hazard['y'] - hazard['height'] // 2,
                               hazard['width'], hazard['height'])
        return None
    
    def _update_hazard_cooldowns(self, boss):
        """Update hazard damage cooldowns"""
        cooldown_dict = getattr(boss, 'hazard_damage_cooldown', self.hazard_cooldowns)
        for hazard_id in list(cooldown_dict.keys()):
            if cooldown_dict[hazard_id] > 0:
                cooldown_dict[hazard_id] -= 1
            else:
                del cooldown_dict[hazard_id]
    
    def _handle_special_collisions(self, player, bosses):
        """Handle special collision cases like boss charge attacks"""
        total_damage = 0
        
        for boss in bosses:
            if hasattr(boss, 'is_charging') and boss.is_charging:
                boss_rect = boss.get_rect()
                expanded_player_rect = player.get_rect().inflate(20, 20)
                
                if boss_rect.colliderect(expanded_player_rect):
                    if hasattr(player, 'dash_duration') and player.dash_duration > 0:
                        # Player is dashing - trigger counter-attack
                        if hasattr(boss, 'trigger_dodge_counter'):
                            boss.trigger_dodge_counter()
                            if player.game:
                                player.game.score += 100
                    else:
                        # Player takes damage from charge
                        damage = int(15 * getattr(boss, 'damage_scale', 1.0))
                        if player.take_damage(damage):
                            if hasattr(player, '_game_ref') and player._game_ref and hasattr(player._game_ref, 'screen_shake'):
                                player._game_ref.screen_shake.start(3, 12)
                            total_damage += damage
                            self._log_ability_damage(boss, "Charge Attack", damage)
                        
                        # Push boss back to prevent continuous collision
                        self._push_boss_back(boss, player)
        
        return total_damage
    
    def _push_boss_back(self, boss, player):
        """Push boss away from player to prevent continuous collision"""
        dx = boss.x - player.x
        dy = boss.y - player.y
        dist = math.sqrt(dx**2 + dy**2)
        if dist > 0:
            boss.x += (dx / dist) * 50
            boss.y += (dy / dist) * 50
            boss.update_rect()
    
    def _handle_player_projectiles(self, player, bosses):
        """Handle player projectiles hitting bosses with spatial optimization"""
        # Use spatial grid to find potential collisions
        remaining_projectiles = []
        for projectile in player.projectiles:
            nearby_objects = self.spatial_grid.get_nearby_objects(projectile)

            projectile_consumed = False
            for obj in nearby_objects:
                if obj in bosses:
                    projectile_rect = projectile.get_rect()
                    boss_rect = obj.get_rect()
                    
                    if projectile_rect.colliderect(boss_rect):
                        obj.take_damage(projectile.damage)
                        if hasattr(player, '_game_ref') and player._game_ref:
                            player._game_ref.score += 10
                        if self.performance_logger:
                            self.performance_logger.log_damage(obj.name, projectile.damage, damage_to_player=False)
                            self.performance_logger.log_attack(obj.name, is_player_attack=True)
                        projectile_consumed = True
                        break
            if not projectile_consumed:
                remaining_projectiles.append(projectile)
        player.projectiles = remaining_projectiles
    
    def _log_damage(self, boss, damage):
        """Log damage dealt to player"""
        if self.performance_logger:
            self.performance_logger.log_damage(boss.name, damage, damage_to_player=True)
            self.performance_logger.log_attack(boss.name, is_player_attack=False)
    
    def _log_ability_damage(self, boss, ability_name, damage):
        """Log specific ability damage"""
        if self.performance_logger:
            self.performance_logger.log_ability_damage(boss.name, ability_name, damage)

    def _log_ability_hit(self, damage_source, damage):
        """Log ability hits with derived ability name."""
        if not self.performance_logger:
            return
        boss_name = getattr(damage_source, 'boss_name', None)
        if not boss_name:
            return
        ability_name = self._get_ability_name_from_source(damage_source)
        if ability_name:
            self.performance_logger.log_ability_damage(boss_name, ability_name, damage)

    def _get_ability_name_from_source(self, damage_source):
        if hasattr(damage_source, 'projectile'):
            return self._get_ability_name(damage_source.projectile)
        if hasattr(damage_source, 'telegraph'):
            return self._get_ability_name(damage_source.telegraph)
        if hasattr(damage_source, 'hazard'):
            if isinstance(damage_source.hazard, dict):
                return damage_source.hazard.get('ability_name')
        return None
