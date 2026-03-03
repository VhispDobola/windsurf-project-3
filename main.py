import pygame
import random
import math
from core import Player, RenderLayer
from core.effect import Telegraph
from ui import UIManager
from utils import PerformanceLogger
from core import ArenaRenderer, BossManager
from utils import position_boss_pair
from core.game_state import GameState, StateManager
from core.collision_system import CollisionSystem
from core.upgrade_system import UpgradeSystem
from core.render_system import RenderSystem, ScreenShakeEffect
from core.audio_manager import AudioManager
from core.auto_balance import AutoBalanceSystem
from utils.error_handler import GameErrorHandler, validate_game_config
from config.constants import (
    WIDTH, HEIGHT, FPS, BLACK, YELLOW,
    init_pygame,
    BOSS_INTRO_DURATION,
    HEAL_AFTER_BOSS_PERCENTAGE, UPGRADE_COUNT, UPGRADE_CARD_WIDTH, 
    UPGRADE_CARD_HEIGHT, UPGRADE_CARD_GAP
)

# Import all bosses
from bosses import (
    EternalGuardian, BladeMaster, NexusCore, VoidAssassin, 
    Chronomancer, TheVirusQueen, TempestLord, ThunderEmperor,
    ImmortalPhoenix, CrystallineDestroyer, EternalDragon,
    IceTyrant, MagmaSovereign, CyberOverlord
)

class Game:
    def __init__(self):
        # Initialize error handler first so startup validation can log consistently.
        self.error_handler = GameErrorHandler()

        # Validate game configuration
        config_errors = validate_game_config()
        if config_errors:
            self.error_handler.logger.warning("Configuration errors found:")
            for error in config_errors:
                self.error_handler.logger.warning("  - %s", error)
        
        # Initialize pygame first
        self.error_handler.safe_pygame_operation(init_pygame)
        
        self.fullscreen = False
        self._windowed_size = (WIDTH, HEIGHT)
        self.screen = self.error_handler.safe_pygame_operation(
            lambda: pygame.display.set_mode((WIDTH, HEIGHT))
        )
        if not self.screen:
            # Fallback to direct pygame initialization
            self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Boss Rush Game")
        self.clock = pygame.time.Clock()
        self.running = True
        
        self.ui_manager = UIManager()
        self.state_manager = StateManager()
        self.performance_logger = PerformanceLogger()
        self.collision_system = CollisionSystem(self.performance_logger, WIDTH, HEIGHT)
        self.upgrade_system = UpgradeSystem()
        self.render_system = RenderSystem(WIDTH, HEIGHT)
        self.screen_shake = ScreenShakeEffect()
        self.audio_manager = AudioManager()
        self.state_manager.change_state(GameState.MENU)
        self.player = Player(WIDTH // 2 - 15, HEIGHT - 100)
        self.player._game_ref = self  # Set game reference for player
        self.current_boss = None
        self.current_bosses = []  # Support multiple bosses
        self.boss_manager = BossManager()
        if getattr(self.boss_manager, "balance_notes", None):
            self.error_handler.logger.info("Auto-balance adjustments (from latest performance log):")
            for note in self.boss_manager.balance_notes:
                self.error_handler.logger.info("  - %s", note)
        self._check_boss_name_consistency()
        
        self.score = 0
        self.fight_start_time = 0
        self.total_time = 0
        self.intro_timer = 0

        self.pending_upgrades = []
        self.pending_between_round_heal = False
        self.bottom_camp_frames = 0
        self.pressure_cooldown = 0
        self.last_player_pos = (self.player.x, self.player.y)
        
        # Flags to prevent repeated operations
        self.victory_analysis_printed = False
        self.game_over_analysis_printed = False
        self.hovered_upgrade_index = -1
        
        # Initialize auto-balance system
        self.auto_balance = AutoBalanceSystem()
        
        self.arena_seed = 1
        self.arena_style = "default"
        self.boss_hints = {
            "Eternal Guardian": "Hint: Watch the timing on heavy swings.",
            "Blade Master": "Hint: Dash through charges to counter.",
            "Nexus Core": "Hint: Shields block shots; reposition.",
            "Void Assassin": "Hint: Expect sudden dashes and feints.",
            "Chronomancer": "Hint: Projectiles change pace over time.",
            "The Virus Queen": "Hint: Keep moving to avoid clusters.",
            "Tempest Lord": "Hint: Learn the storm pattern spacing.",
            "Thunder Emperor": "Hint: Telegraphs are short but clear.",
            "Immortal Phoenix": "Hint: Each stage changes attack style.",
            "Crystalline Destroyer": "Hint: Crystals punish standing still.",
            "Eternal Dragon": "Hint: Breath attacks cover wide lanes.",
            "Ice Tyrant": "Hint: Slow zones reduce movement options.",
            "Magma Sovereign": "Hint: Hazards linger longer than they look.",
            "Cyber Overlord": "Hint: Lines of fire force quick direction swaps.",
        }
        self.boss_music_tracks = {
            "Blade Master": "BladeMasterM.mp3",
            "Nexus Core": "NexusCoreM.mp3",
            "Void Assassin": "VoidAssassainM.mp3",
            "Chronomancer": ("ChronomancerM.mp3", "Chronostasis Clash.mp3"),
            "The Virus Queen": "VirusQueenM.mp3",
            "Tempest Lord": "TempestLordM.mp3",
            "Thunder Emperor": "ThunderEmperorM.mp3",
            "Immortal Phoenix": "ImmortalPhoenixM.mp3",
            "Crystalline Destroyer": "CrystallineDestroyerM.mp3",
            "Eternal Dragon": "EternalDragonM.mp3",
            "Ice Tyrant": "IceTyrantM.mp3",
            "Magma Sovereign": "MagmaSovereignM.mp3",
            "Cyber Overlord": "CyberOverlordM.mp3",
        }

    def _check_boss_name_consistency(self):
        mismatches = self.boss_manager.validate_boss_name_consistency()
        if mismatches:
            self.error_handler.logger.warning("Boss name consistency warnings:")
            for class_name, actual, expected in mismatches:
                self.error_handler.logger.warning("  - %s: '%s' -> '%s'", class_name, actual, expected)
        
    @property
    def state(self):
        """Get current game state"""
        return self.state_manager.current_state
    
    @state.setter
    def state(self, value):
        """Set game state"""
        self.state_manager.change_state(value)
        
    def toggle_fullscreen(self):
        """Toggle between fullscreen and windowed mode with error handling"""
        current_surface = pygame.display.get_surface()
        if current_surface:
            self._windowed_size = current_surface.get_size()

        def toggle_operation():
            if self.fullscreen:
                self.fullscreen = False
                self.screen = pygame.display.set_mode(self._windowed_size)
                return True

            if pygame.display.get_driver() in ("x11", "wayland"):
                self.fullscreen = True
                pygame.display.toggle_fullscreen()
                self.screen = pygame.display.get_surface() or self.screen
                return True

            info = pygame.display.Info()
            self.fullscreen = True
            self.screen = pygame.display.set_mode((info.current_w, info.current_h), pygame.FULLSCREEN)
            return True

        result = self.error_handler.safe_pygame_operation(toggle_operation)
        if not result:
            self.fullscreen = False
            self.screen = self.error_handler.safe_pygame_operation(
                lambda: pygame.display.set_mode(self._windowed_size)
            )

    def reset_game(self):
        """Reset game for a new run"""
        self.state = GameState.MENU
        self.audio_manager.stop_music()
        self.player = Player(WIDTH // 2 - 15, HEIGHT - 100)
        self.player._game_ref = self  # Set game reference for player
        self.current_boss = None
        self.current_bosses = []
        self.boss_manager.reset()
        
        self.score = 0
        self.total_time = 0
        self.intro_timer = 0
        self.victory_analysis_printed = False
        self.game_over_analysis_printed = False
        self.hovered_upgrade_index = -1
        self.pending_upgrades = []  # Clear any pending upgrades
        self.pending_between_round_heal = False
        self.bottom_camp_frames = 0
        self.pressure_cooldown = 0
        self.last_player_pos = (self.player.x, self.player.y)
        self.performance_logger = PerformanceLogger()
        self.collision_system = CollisionSystem(self.performance_logger, WIDTH, HEIGHT)
        self.render_system.clear_batches()
        
    def start_boss_fight(self):
        # Check if we should have single or paired bosses
        if self.boss_manager.bosses_defeated_count < 10:
            # Single boss fight
            boss = self.boss_manager.get_next_boss()
            if boss:
                self.current_boss = boss
                self.current_bosses = [boss]
                boss.game = self
                
                # Apply auto-balance adjustments
                adjustments = self.auto_balance.get_boss_adjustments(boss.name)
                if adjustments:
                    boss.apply_balance_adjustments(adjustments)
                    self.auto_balance.log_balance_change(boss.name, adjustments)
                
                self.state = GameState.BOSS_INTRO
                self.intro_timer = BOSS_INTRO_DURATION
                self.fight_start_time = pygame.time.get_ticks() / 1000
                
                self.arena_seed = (pygame.time.get_ticks() + self.boss_manager.bosses_defeated_count * 1337) & 0xFFFFFFFF
                self.arena_style = self._get_arena_style(boss)
                
                # Reset flags for new fight
                self.victory_analysis_printed = False
                self.game_over_analysis_printed = False
                self._play_boss_music([boss])
                
                self.performance_logger.start_boss_fight(boss.name)
            else:
                self.state = GameState.VICTORY
        else:
            # Paired boss fight
            boss1, boss2 = self.boss_manager.get_next_boss_pair()
            if boss1 and boss2:
                # Position bosses on screen
                boss1, boss2 = position_boss_pair(boss1, boss2, WIDTH, HEIGHT)
                
                self.current_boss = boss1  # Keep for compatibility
                self.current_bosses = [boss1, boss2]
                
                for boss in self.current_bosses:
                    boss.game = self
                    
                    # Apply auto-balance adjustments
                    adjustments = self.auto_balance.get_boss_adjustments(boss.name)
                    if adjustments:
                        boss.apply_balance_adjustments(adjustments)
                        self.auto_balance.log_balance_change(boss.name, adjustments)
                
                self.state = GameState.BOSS_INTRO
                self.intro_timer = BOSS_INTRO_DURATION
                self.fight_start_time = pygame.time.get_ticks() / 1000
                
                self.arena_seed = (pygame.time.get_ticks() + self.boss_manager.bosses_defeated_count * 1337) & 0xFFFFFFFF
                self.arena_style = self._get_arena_style(boss1)  # Use first boss for arena style
                
                # Reset flags for new fight
                self.victory_analysis_printed = False
                self.game_over_analysis_printed = False
                self._play_boss_music(self.current_bosses)
                
                for boss in self.current_bosses:
                    self.performance_logger.start_boss_fight(boss.name)
            else:
                self.state = GameState.VICTORY
                self.audio_manager.stop_music()

    def _play_boss_music(self, bosses):
        """Play mapped boss track for the current fight, if available."""
        if not bosses:
            return
        for boss in bosses:
            filename = self.boss_music_tracks.get(boss.name)
            if isinstance(filename, (list, tuple)):
                filename = random.choice(filename)
            if filename:
                self.audio_manager.play_music(filename)
                return

    def _get_arena_style(self, boss):
        return ArenaRenderer.get_arena_style(boss)

    def _draw_arena_background(self, screen):
        ArenaRenderer.draw_arena_background(screen, self.arena_style, self.arena_seed)

    def _get_boss_hint_text(self):
        if not self.current_bosses:
            return None
        if len(self.current_bosses) > 1:
            return "Hint: Split your attention and keep lanes open."
        boss = self.current_bosses[0]
        return self.boss_hints.get(boss.name, "Hint: Dodge patterns and find openings.")

    def heal_after_boss(self):
        heal_amount = max(1, int(self.player.max_health * HEAL_AFTER_BOSS_PERCENTAGE))
        self.player.health = min(self.player.max_health, self.player.health + heal_amount)

    def open_upgrade_screen(self):
        self.pending_upgrades = self.upgrade_system.get_random_upgrades(self.player)
        self.audio_manager.stop_music()
        self.state = GameState.UPGRADE

    def get_hovered_upgrade_index(self, mouse_pos):
        if not self.pending_upgrades:
            return -1
            
        cards = self.pending_upgrades[:UPGRADE_COUNT]
        card_w = UPGRADE_CARD_WIDTH
        card_h = UPGRADE_CARD_HEIGHT
        gap = UPGRADE_CARD_GAP
        total_w = (card_w * UPGRADE_COUNT) + (gap * (UPGRADE_COUNT - 1))
        start_x = (self.screen.get_width() - total_w) // 2
        y = self.screen.get_height() // 2 - card_h // 2 + 30
        
        mx, my = mouse_pos
        
        for i in range(len(cards)):
            x = start_x + i * (card_w + gap)
            rect = pygame.Rect(x, y, card_w, card_h)
            if rect.collidepoint(mx, my):
                return i
        
        return -1

    def apply_upgrade(self, upgrade_index):
        """Apply upgrade with input validation"""
        validated_index = self.error_handler.validate_input(
            upgrade_index, "int", min_val=0, max_val=len(self.pending_upgrades) - 1
        )
        if validated_index is None:
            return

        upgrade_index = validated_index

        if upgrade_index < 0 or upgrade_index >= len(self.pending_upgrades):
            return
        
        try:
            upgrade = self.pending_upgrades[upgrade_index]
            upgrade["apply"]()

            if self.pending_between_round_heal:
                self.heal_after_boss()
                self.pending_between_round_heal = False

            if self.player.health > self.player.max_health:
                self.player.health = self.player.max_health

            self.pending_upgrades = []
            self.hovered_upgrade_index = -1

            # Start next boss fight using the boss manager
            self.start_boss_fight()
        except Exception as e:
            self.error_handler.logger.error(f"Error applying upgrade: {e}")
            
    def handle_collisions(self):
        """Handle collisions using the collision system"""
        if not self.current_bosses:
            return
        
        self.collision_system.handle_collisions(self.player, self.current_bosses)

    def _apply_anti_camp_pressure(self):
        """Nudge players out of bottom camping with readable telegraphed danger."""
        if not self.current_bosses:
            return

        if self.pressure_cooldown > 0:
            self.pressure_cooldown -= 1

        px, py = self.player.x, self.player.y
        lx, ly = self.last_player_pos
        moved_sq = (px - lx) * (px - lx) + (py - ly) * (py - ly)
        self.last_player_pos = (px, py)

        screen_h = self.screen.get_height()
        in_bottom_zone = self.player.y > int(screen_h * 0.62)
        mostly_stationary = moved_sq < 2.25

        if in_bottom_zone and mostly_stationary:
            self.bottom_camp_frames += 1
        else:
            self.bottom_camp_frames = max(0, self.bottom_camp_frames - 2)

        if self.bottom_camp_frames < 75 or self.pressure_cooldown > 0:
            return

        target_x = self.player.x + self.player.width // 2 + random.randint(-20, 20)
        target_y = self.player.y + self.player.height // 2 + random.randint(-20, 20)
        for boss in self.current_bosses:
            t = Telegraph(target_x, target_y, 50, 50, (255, 120, 60), damage=8, warning_type="pulse")
            t.active_start = 28
            t.active_end = 50
            boss.effects.append(t)

        self.pressure_cooldown = 150
        self.bottom_camp_frames = 30
                
    def update(self):
        if self.state == GameState.FIGHTING:
            keys = pygame.key.get_pressed()
            self.player.move(keys)
            
            if keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]:
                self.player.dash()
            if keys[pygame.K_SPACE]:
                mx, my = pygame.mouse.get_pos()
                self.player.shoot(mx, my)
            if pygame.mouse.get_pressed()[0]:
                mx, my = pygame.mouse.get_pos()
                self.player.shoot(mx, my)
                
            self.player.update()
            
            # Update all bosses
            for boss in self.current_bosses:
                boss.update()

            # Record performance stats
            self.performance_logger.tick_frame(self.player, self.current_bosses)
            self._apply_anti_camp_pressure()
            
            self.handle_collisions()
            
            if self.player.health <= 0:
                self.state = GameState.GAME_OVER
                self.audio_manager.stop_music()
                for boss in self.current_bosses:
                    self.performance_logger.end_boss_fight(boss.name, victory=False)

            # Remove dead bosses from the list (but keep them for performance tracking)
            dead_bosses = [boss for boss in self.current_bosses if boss.health <= 0]
            if dead_bosses:
                for dead_boss in dead_bosses:
                    self.performance_logger.end_boss_fight(dead_boss.name, victory=True)
                    self.boss_manager.on_boss_defeated(dead_boss)
                
                # Remove dead bosses from current_bosses
                self.current_bosses = [boss for boss in self.current_bosses if boss.health > 0]
                
                # If any bosses died, add score immediately
                if dead_bosses:
                    self.score += 500 * len(dead_bosses)

            # Check if all bosses are defeated
            all_bosses_defeated = len(self.current_bosses) == 0
            
            if all_bosses_defeated:
                # End current boss fight with victory - all bosses have been removed
                fight_time = (pygame.time.get_ticks() / 1000) - self.fight_start_time
                self.total_time += fight_time

                # Save performance data after each boss fight
                self.performance_logger.save_session()

                # Apply post-fight heal after upgrade selection, right before next fight.
                self.pending_between_round_heal = True
                self.open_upgrade_screen()

        elif self.state == GameState.BOSS_INTRO:
            self.intro_timer -= 1
            if self.intro_timer <= 0:
                self.state = GameState.FIGHTING

        # Update screen shake
        if self.screen_shake.duration > 0:
            self.screen_shake.update()

    def draw(self):
        # Simple drawing approach to fix black screen
        
        if self.state == GameState.MENU:
            # Clear screen and draw menu
            self.screen.fill(BLACK)
            self.ui_manager.draw_menu(self.screen)
        elif self.state == GameState.BOSS_INTRO:
            # Draw arena background first
            self._draw_arena_background(self.screen)
            # Show boss intro for all current bosses
            if self.current_bosses:
                boss_names = " & ".join([boss.name for boss in self.current_bosses])
                self.ui_manager.draw_boss_intro(self.screen, boss_names, self._get_boss_hint_text())
        elif self.state == GameState.FIGHTING:
            # Keep render culling aligned with current window/fullscreen size.
            self.render_system.width = self.screen.get_width()
            self.render_system.height = self.screen.get_height()
            self.render_system.clear_batches()
            self._populate_render_batches()
            self.render_system.render(self.screen, background_draw=self._draw_arena_background)

            self._draw_offscreen_indicators()
                
            # Draw health bars for multiple bosses
            if len(self.current_bosses) > 1:
                self.ui_manager.draw_multiple_health_bars(self.screen, self.current_bosses)
        elif self.state == GameState.UPGRADE:
            self.screen.fill(BLACK)
            self.ui_manager.draw_upgrade_screen(self.screen, self.pending_upgrades, self.hovered_upgrade_index)
        elif self.state == GameState.VICTORY:
            self.screen.fill(BLACK)
            self.ui_manager.draw_victory(self.screen, self.score, self.total_time)
            if not self.victory_analysis_printed:
                self.performance_logger.print_analysis()
                self.performance_logger.save_session()
                self.victory_analysis_printed = True
        elif self.state == GameState.GAME_OVER:
            self.screen.fill(BLACK)
            self.ui_manager.draw_game_over(self.screen)
            if not self.game_over_analysis_printed:
                self.performance_logger.print_analysis()
                self.performance_logger.save_session()
                self.game_over_analysis_printed = True

        # Apply screen shake at the end
        if self.screen_shake.duration > 0:
            self.screen_shake.apply_offset(self.screen)
        
        # Update display
        pygame.display.flip()

    def _draw_offscreen_indicators(self):
        if not self.current_bosses:
            return
        screen_w = self.screen.get_width()
        screen_h = self.screen.get_height()
        center_x = screen_w // 2
        center_y = screen_h // 2
        max_indicators = 20
        count = 0

        for boss in self.current_bosses:
            for projectile in boss.get_all_projectiles():
                if count >= max_indicators:
                    return
                pos = self._get_projectile_position(projectile)
                if pos is None:
                    continue
                px, py = pos
                if -10 <= px <= screen_w + 10 and -10 <= py <= screen_h + 10:
                    continue

                angle = math.atan2(py - center_y, px - center_x)
                edge_x = min(max(int(center_x + math.cos(angle) * (screen_w // 2 - 12)), 8), screen_w - 8)
                edge_y = min(max(int(center_y + math.sin(angle) * (screen_h // 2 - 12)), 8), screen_h - 8)

                tip = (edge_x + int(math.cos(angle) * 8), edge_y + int(math.sin(angle) * 8))
                left = (edge_x + int(math.cos(angle + 2.5) * 6), edge_y + int(math.sin(angle + 2.5) * 6))
                right = (edge_x + int(math.cos(angle - 2.5) * 6), edge_y + int(math.sin(angle - 2.5) * 6))

                pygame.draw.polygon(self.screen, YELLOW, [tip, left, right])
                count += 1

    def _get_projectile_position(self, projectile):
        """Safely extract projectile position from object or dict-like sources."""
        if isinstance(projectile, dict):
            if "x" in projectile and "y" in projectile:
                return projectile["x"], projectile["y"]
            return None
        if hasattr(projectile, "x") and hasattr(projectile, "y"):
            return projectile.x, projectile.y
        if hasattr(projectile, "get_rect"):
            rect = projectile.get_rect()
            return rect.centerx, rect.centery
        return None
    
    def _populate_render_batches(self):
        """Populate render batches with all visible objects"""
        # Player and bosses own drawing of their nested objects (projectiles/effects).
        # Batching only top-level entities avoids double-rendering.
        player_layer = getattr(self.player, "render_layer", RenderLayer.ENTITIES)
        self.render_system.add_object(self.player, player_layer)
        
        # Add bosses
        for boss in self.current_bosses:
            boss_layer = getattr(boss, "render_layer", RenderLayer.ENTITIES)
            self.render_system.add_object(boss, boss_layer)
            
    def run(self):
        while self.running:
            mouse_pos = pygame.mouse.get_pos()
            
            # Check for auto-balance updates periodically
            if self.auto_balance.should_run_balance_check():
                self.auto_balance.update_balance_adjustments()
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_F11:
                        self.toggle_fullscreen()
                    elif event.key == pygame.K_SPACE:
                        if self.state == GameState.MENU:
                            self.start_boss_fight()
                        elif self.state == GameState.VICTORY:
                            self.reset_game()
                            self.start_boss_fight()
                    elif self.state == GameState.UPGRADE:
                        if event.key == pygame.K_1:
                            self.apply_upgrade(0)
                        elif event.key == pygame.K_2:
                            self.apply_upgrade(1)
                        elif event.key == pygame.K_3:
                            self.apply_upgrade(2)
                        elif event.key == pygame.K_4:
                            self.apply_upgrade(3)
                    elif event.key == pygame.K_r:
                        if self.state == GameState.GAME_OVER:
                            self.reset_game()
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1 and self.state == GameState.UPGRADE:
                        if 0 <= self.hovered_upgrade_index < len(self.pending_upgrades):
                            self.apply_upgrade(self.hovered_upgrade_index)
            
            if self.state == GameState.UPGRADE:
                self.hovered_upgrade_index = self.get_hovered_upgrade_index(mouse_pos)
                            
            try:
                self.update()
                self.draw()
            except Exception:
                self.error_handler.logger.exception("Unhandled error in main game loop")
                self.running = False
            self.clock.tick(FPS)
            
        pygame.quit()
        self.audio_manager.cleanup()

if __name__ == "__main__":
    game = Game()
    game.run()
