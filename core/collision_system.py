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

    def update_bounds(self, width, height):
        """Resize collision grid when screen size changes."""
        width = max(1, int(width))
        height = max(1, int(height))
        if width == self.spatial_grid.width and height == self.spatial_grid.height:
            return
        self.spatial_grid = SpatialGrid(width, height, cell_size=self.spatial_grid.cell_size)
    
    def handle_collisions(self, player, bosses):
        """Handle all collisions between one or more players and bosses."""
        if not bosses or not player:
            return

        players = player if isinstance(player, (list, tuple)) else [player]
        players = [p for p in players if p is not None]
        if not players:
            return

        # Update spatial grid
        self.spatial_grid.clear()
        total_damage = 0
        self._populate_grid(players, bosses)

        for active_player in players:
            if getattr(active_player, "health", 0) <= 0:
                continue

            nearby_objects = self.spatial_grid.get_nearby_objects(active_player)
            nearby_object_ids = {id(obj) for obj in nearby_objects}
            damage_sources = self._collect_damage_sources(bosses, nearby_object_ids)
            player_rect = active_player.get_rect()

            # Handle special boss collisions (like Blade Master charge)
            total_damage += self._handle_special_collisions(active_player, bosses)

            # Handle projectile and effect collisions with spatial optimization
            for damage_source in damage_sources:
                if damage_source.active:
                    if hasattr(damage_source, 'projectile') and self._try_reflect_projectile(active_player, damage_source, bosses):
                        continue
                    damage = damage_source.check_collision(player_rect, target_id=id(active_player))
                    if damage > 0:
                        damage = int(damage * getattr(damage_source, 'damage_scale', 1.0))
                        # Projectiles are one-hit globally. Persistent area effects can hit
                        # multiple players independently.
                        if hasattr(damage_source, 'projectile'):
                            damage_source.deactivate()
                        if active_player.take_damage(damage):
                            total_damage += damage
                            self._log_damage(damage_source, bosses, damage)
                            self._log_ability_hit(damage_source, damage)

        # Handle player projectiles hitting bosses with spatial optimization
        for active_player in players:
            self._handle_player_projectiles(active_player, bosses)

        return total_damage

    def _try_reflect_projectile(self, player, damage_source, bosses):
        projectile = getattr(damage_source, 'projectile', None)
        if projectile is None:
            return False
        if not getattr(player, 'reflect_shield', False):
            return False
        if getattr(player, 'reflect_cooldown', 0) > 0:
            return False
        if getattr(player, 'reflect_charges', 0) <= 0:
            return False
        if not projectile.get_rect().colliderect(player.get_rect()):
            return False

        original_parent = getattr(projectile, 'parent_list', None)
        projectile.damage = max(projectile.damage, getattr(player, 'projectile_damage', projectile.damage))
        projectile.dx = -projectile.dx
        projectile.dy = -projectile.dy
        projectile.color = getattr(player, 'color', projectile.color)
        projectile.parent_list = player.projectiles
        projectile.x = player.x + player.width // 2
        projectile.y = player.y + player.height // 2
        projectile.update_rect()
        setattr(projectile, 'reflected', True)
        player.projectiles.append(projectile)

        if original_parent is not None and projectile in original_parent and original_parent is not player.projectiles:
            original_parent.remove(projectile)

        player.reflect_charges -= 1
        player.reflect_cooldown = 18
        return True
    
    def _populate_grid(self, players, bosses):
        """Populate spatial grid with all objects"""
        # Add players
        for player in players:
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
        for player in players:
            for projectile in player.projectiles:
                self.spatial_grid.add_object(projectile)
    
    def _collect_damage_sources(self, bosses, nearby_object_ids=None):
        """Collect all damage sources from bosses"""
        damage_sources = []
        
        for boss in bosses:
            ability_balance = getattr(boss, "dynamic_ability_balance", {})
            # Add projectiles
            for projectile in boss.get_all_projectiles():
                if not self._is_projectile_like(projectile):
                    continue
                if nearby_object_ids is not None and id(projectile) not in nearby_object_ids:
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
                            game = getattr(player, "_game_ref", None) or getattr(player, "game", None)
                            if game:
                                game.score += 100
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
            projectile_rect = projectile.get_rect()

            projectile_consumed = False
            for obj in nearby_objects:
                if obj in bosses:
                    boss_rect = obj.get_rect()

                    if projectile_rect.colliderect(boss_rect):
                        previous_health = float(getattr(obj, 'health', 0))
                        obj.take_damage(projectile.damage)
                        current_health_raw = float(getattr(obj, 'health', previous_health))
                        current_health = max(0.0, current_health_raw)
                        actual_damage = max(0.0, min(previous_health, previous_health - current_health))
                        actual_damage = int(round(actual_damage))

                        if actual_damage > 0:
                            if hasattr(player, '_game_ref') and player._game_ref:
                                player._game_ref.score += 10
                                if hasattr(player._game_ref, 'damage_numbers'):
                                    player._game_ref.damage_numbers.register_damage(obj, actual_damage)
                            if self.performance_logger:
                                self.performance_logger.log_damage(obj.name, actual_damage, damage_to_player=False)
                                self.performance_logger.log_attack(obj.name, is_player_attack=True)

                        projectile_consumed = True
                        break
            if not projectile_consumed:
                remaining_projectiles.append(projectile)
        player.projectiles = remaining_projectiles
    
    def _log_damage(self, damage_source, bosses, damage):
        """Log damage dealt to player"""
        if self.performance_logger:
            boss = None
            source_boss_name = getattr(damage_source, "boss_name", None)
            if source_boss_name:
                boss = next((b for b in bosses if getattr(b, "name", None) == source_boss_name), None)
            if boss is None:
                boss = bosses[0]
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
