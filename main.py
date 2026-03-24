import json
import os
import random
import socket
import time
from datetime import datetime

import pygame

from config.constants import (
    BOSS_INTRO_DURATION,
    FPS,
    HEAL_AFTER_BOSS_PERCENTAGE,
    HEIGHT,
    UPGRADE_CARD_GAP,
    UPGRADE_CARD_HEIGHT,
    UPGRADE_CARD_WIDTH,
    UPGRADE_COUNT,
    WIDTH,
    init_pygame,
)
from core import ArenaRenderer, BossManager, Player, ProgressionSystem
from core.audio_manager import AudioManager
from core.auto_balance import AutoBalanceSystem
from core.collision_system import CollisionSystem
from core.damage_numbers import DamageNumberManager
from core.effect import Telegraph
from core.game_customization_helpers import (
    apply_customization_to_player,
    default_customization,
    handle_customization_key,
)
from core.game_render_helpers import (
    draw as draw_game,
)
from core.game_state import GameState, StateManager
from core.network_client_runner import run_network_client
from core.network_sync import NetworkHost
from core.render_system import RenderSystem, ScreenShakeEffect
from core.upgrade_system import UpgradeSystem
from ui import UIManager
from utils import PerformanceLogger, position_boss_pair
from utils.error_handler import GameErrorHandler, validate_game_config


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

        self.fullscreen = True
        self._windowed_size = (WIDTH, HEIGHT)
        self.screen = self.error_handler.safe_pygame_operation(self._create_default_display)
        if not self.screen:
            # Fallback to direct pygame initialization
            self.screen = self._create_default_display()
        pygame.display.set_caption("Boss Rush Game")
        self.clock = pygame.time.Clock()
        self.running = True
        self.network_mode = os.getenv("BOSS_RUSH_NETWORK_MODE", "off").strip().lower()
        self.network_host_ip = os.getenv("BOSS_RUSH_HOST", "0.0.0.0").strip()
        self.network_port = int(os.getenv("BOSS_RUSH_PORT", "50000"))
        self.network_sync_mode = (
            os.getenv("BOSS_RUSH_SYNC_MODE", "frame").strip().lower()
        )
        self.network_stream_fps = int(os.getenv("BOSS_RUSH_STREAM_FPS", "30"))
        self.network_zlib_level = int(os.getenv("BOSS_RUSH_STREAM_ZLIB", "1"))
        self.network_host = None
        self.replay_log_enabled = os.getenv("BOSS_RUSH_REPLAY_LOG", "0").strip() == "1"
        self.replay_log_frames = []

        self.ui_manager = UIManager()
        self.state_manager = StateManager()
        self.performance_logger = PerformanceLogger()
        self.collision_system = CollisionSystem(self.performance_logger, WIDTH, HEIGHT)
        self.upgrade_system = UpgradeSystem()
        self.progression_system = ProgressionSystem()
        self.render_system = RenderSystem(WIDTH, HEIGHT)
        self.screen_shake = ScreenShakeEffect()
        self.audio_manager = AudioManager()
        self.audio_manager.load_sounds()
        self.audio_manager.register_custom_sound("blade_dash", "blade_dash.mp3")
        self.audio_manager.register_custom_sound("time_stop", "timestop.mp3")
        self.damage_numbers = DamageNumberManager()
        self.state_manager.change_state(self._default_frontend_state())
        self.color_options = [
            (0, 100, 255),  # blue
            (0, 220, 180),  # teal
            (255, 170, 0),  # orange
            (120, 240, 90),  # green
            (245, 80, 90),  # red
            (210, 110, 255),  # violet
        ]
        self.hat_options = ["None", "Cap", "Crown", "Beanie"]
        self.player_customizations = []
        self.customization_player_index = 0
        self.customization_field_index = 0
        self.progression_selected_relic_index = 0
        self.progression_selected_slot_index = 0
        self.progression_focus_area = "inventory"
        self.progression_status_message = ""
        self.progression_status_timer = 0
        self.join_menu_host = "127.0.0.1"
        self.join_menu_port = "50000"
        self.join_menu_slot_options = ["auto", "2", "3", "4"]
        self.join_menu_slot_index = 0
        self.join_menu_field_index = 0
        self.join_menu_status = ""
        self.launch_network_client_after_exit = False
        self.reward_toasts = []
        self.run_in_progress = False
        self.players = []
        self.player = None
        self.control_profiles = self._build_player_control_profiles()
        self._init_players()
        self.current_boss = None
        self.current_bosses = []  # Support multiple bosses
        self.boss_manager = BossManager()
        if getattr(self.boss_manager, "balance_notes", None):
            self.error_handler.logger.info(
                "Auto-balance adjustments (from latest performance log):"
            )
            for note in self.boss_manager.balance_notes:
                self.error_handler.logger.info("  - %s", note)
        self._check_boss_name_consistency()

        self.score = 0
        self.fight_start_time = 0
        self.total_time = 0
        self.intro_timer = 0

        self.pending_upgrades = []
        self.pending_between_round_heal = False
        self.milestone_upgrade_round = False
        self.bottom_camp_frames = {}
        self.pressure_cooldown = 0
        self.last_player_pos = {}
        self._prime_player_tracking()

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

        if self.network_mode == "host":
            self._start_network_host()

    def _init_players(self):
        """Initialize local multiplayer roster and per-player input profiles."""
        default_player_count = 1
        requested_count = default_player_count
        try:
            requested_count = int(
                os.getenv("BOSS_RUSH_PLAYERS", str(default_player_count))
            )
        except ValueError:
            requested_count = default_player_count

        player_count = max(1, min(4, requested_count))
        while len(self.player_customizations) < player_count:
            self.player_customizations.append(
                self._default_customization(len(self.player_customizations))
            )

        self.players = []
        for i in range(player_count):
            self.players.append(self._create_player(i))

        self.player = self.players[0]
        self._prime_player_tracking()

    def _start_network_host(self):
        if self.network_host:
            return True
        self.network_host = NetworkHost(
            self.network_host_ip,
            self.network_port,
            max_remote_players=3,
            stream_fps=self.network_stream_fps,
            sync_mode=self.network_sync_mode,
            zlib_level=self.network_zlib_level,
        )
        try:
            self.network_host.start()
        except OSError as exc:
            self.error_handler.logger.error(
                "Unable to start LAN host on %s:%s: %s",
                self.network_host_ip,
                self.network_port,
                exc,
            )
            self.network_host = None
            self.network_mode = "off"
            return False

        self.error_handler.logger.info(
            "LAN host mode enabled on %s:%s (sync=%s, fps=%s)",
            self.network_host_ip,
            self.network_port,
            self.network_sync_mode,
            self.network_stream_fps,
        )
        return True

    def open_host_lobby(self):
        self.network_mode = "host"
        if not self._start_network_host():
            self.state = GameState.MENU
            return
        self.state = GameState.LOBBY

    def _create_player(self, player_index):
        center_x = WIDTH // 2 - 15
        base_y = HEIGHT - 100
        spawn_offsets = [-120, -40, 40, 120]
        offset = (
            spawn_offsets[player_index] if 0 <= player_index < len(spawn_offsets) else 0
        )
        px = max(0, min(WIDTH - 30, center_x + offset))
        player = Player(px, base_y)
        player._game_ref = self
        player.player_index = player_index
        player.input_profile = self.control_profiles[player_index]
        self._apply_progression_to_player(player)
        self._apply_customization_to_player(player, player_index)
        return player

    def _default_customization(self, index):
        profile = default_customization(self, index)
        if index == 0:
            identity = self.progression_system.get_player_identity()
            profile["username"] = identity.get("username", profile["username"])
            profile["color"] = tuple(identity.get("color", profile["color"]))
            profile["hat"] = identity.get("hat", profile["hat"])
        return profile

    def _apply_customization_to_player(self, player, player_index):
        return apply_customization_to_player(self, player, player_index)

    def _apply_progression_to_player(self, player):
        self.progression_system.apply_meta_bonuses_to_player(player)

    def _show_status_message(self, text, duration=180):
        self.progression_status_message = text
        self.progression_status_timer = duration

    def _queue_reward_toast(self, text, color=(255, 255, 0), duration=240):
        self.reward_toasts.append(
            {"text": text, "color": color, "timer": duration, "duration": duration}
        )

    def _queue_reward_summary(self, rewards):
        credits = int(rewards.get("credits", 0))
        if credits:
            self._queue_reward_toast(f"+{credits} Credits", (255, 230, 120))
        for boss_id, amount in rewards.get("materials", {}).items():
            label = boss_id.replace("_", " ").title()
            self._queue_reward_toast(f"+{amount} {label} Essence", (140, 220, 255))
        if rewards.get("first_time"):
            self._queue_reward_toast(
                f"First kill bonus: {rewards.get('boss_name', 'Boss')}",
                (140, 255, 170),
            )

    def _get_progression_relics(self):
        return self.progression_system.get_visible_relics()

    def _default_frontend_state(self):
        if self.network_mode == "host":
            return GameState.LOBBY
        return GameState.MENU

    def _build_local_lobby_profile(self):
        profile = self.progression_system.get_lobby_profile()
        if self.player_customizations:
            customization = self.player_customizations[0]
        else:
            customization = self._default_customization(0)
        profile["username"] = (
            str(customization.get("username", profile.get("username", "Player"))).strip()[:16]
            or "Player"
        )
        profile["color"] = list(customization.get("color", profile.get("color", (0, 100, 255))))
        profile["hat"] = str(customization.get("hat", profile.get("hat", "None"))).strip() or "None"
        return profile

    def _create_default_display(self):
        if self.fullscreen:
            info = pygame.display.Info()
            return pygame.display.set_mode((info.current_w, info.current_h), pygame.FULLSCREEN)
        return pygame.display.set_mode((WIDTH, HEIGHT))

    def get_display_host_address(self):
        if self.network_mode != "host":
            return None
        if self.network_host_ip and self.network_host_ip not in ("0.0.0.0", "::"):
            return f"{self.network_host_ip}:{self.network_port}"
        ip_candidates = []
        try:
            addresses = socket.gethostbyname_ex(socket.gethostname())[2]
            ip_candidates = [
                ip for ip in addresses if ip and "." in ip and not ip.startswith("127.")
            ]
        except OSError:
            ip_candidates = []
        if not ip_candidates:
            return f"Share your PC's LAN IP on port {self.network_port}"
        return " | ".join(f"{ip}:{self.network_port}" for ip in sorted(set(ip_candidates)))

    def get_join_slot_label(self):
        value = self.join_menu_slot_options[self.join_menu_slot_index]
        return "Auto" if value == "auto" else f"Player {value}"

    def open_join_menu(self):
        self.join_menu_status = ""
        self.state = GameState.JOIN_SETUP

    def launch_network_client_from_menu(self):
        host = self.join_menu_host.strip()
        port = self.join_menu_port.strip()
        if not host:
            self.join_menu_status = "Host IP is required."
            return
        try:
            parsed_port = int(port)
            if parsed_port <= 0 or parsed_port > 65535:
                raise ValueError
        except ValueError:
            self.join_menu_status = "Port must be a number from 1 to 65535."
            return

        os.environ["BOSS_RUSH_NETWORK_MODE"] = "client"
        os.environ["BOSS_RUSH_HOST"] = host
        os.environ["BOSS_RUSH_PORT"] = str(parsed_port)
        os.environ["BOSS_RUSH_PLAYER_SLOT"] = self.join_menu_slot_options[self.join_menu_slot_index]
        self.launch_network_client_after_exit = True
        self.join_menu_status = "Launching client..."
        self.running = False

    def _handle_join_menu_key(self, event):
        if event.key == pygame.K_ESCAPE:
            self.join_menu_status = ""
            self.state = GameState.MENU
            return
        if event.key in (pygame.K_TAB, pygame.K_DOWN):
            self.join_menu_field_index = (self.join_menu_field_index + 1) % 3
            return
        if event.key == pygame.K_UP:
            self.join_menu_field_index = (self.join_menu_field_index - 1) % 3
            return
        if event.key == pygame.K_RETURN:
            self.launch_network_client_from_menu()
            return

        if self.join_menu_field_index == 2:
            if event.key == pygame.K_LEFT:
                self.join_menu_slot_index = (self.join_menu_slot_index - 1) % len(self.join_menu_slot_options)
            elif event.key == pygame.K_RIGHT:
                self.join_menu_slot_index = (self.join_menu_slot_index + 1) % len(self.join_menu_slot_options)
            return

        if event.key == pygame.K_BACKSPACE:
            if self.join_menu_field_index == 0:
                self.join_menu_host = self.join_menu_host[:-1]
            elif self.join_menu_field_index == 1:
                self.join_menu_port = self.join_menu_port[:-1]
            return

        if self.join_menu_field_index == 0:
            if event.unicode and (event.unicode.isalnum() or event.unicode in ".:-"):
                self.join_menu_host = (self.join_menu_host + event.unicode)[:64]
            return

        if self.join_menu_field_index == 1:
            if event.unicode and event.unicode.isdigit():
                self.join_menu_port = (self.join_menu_port + event.unicode)[:5]

    def get_lobby_slots(self):
        slots = [
            {
                "slot": 1,
                "connected": True,
                "ready": True,
                "profile": self._build_local_lobby_profile(),
                "status": "Host",
                "status_color": (140, 255, 180),
                "ping_text": None,
            }
        ]
        remote_lobby = self.network_host.get_lobby_state() if self.network_host else {}
        for idx in range(1, 4):
            entry = remote_lobby.get(idx)
            if entry:
                ready = bool(entry.get("ready", False))
                slots.append(
                    {
                        "slot": idx + 1,
                        "connected": True,
                        "ready": ready,
                        "profile": dict(entry.get("profile", {})),
                        "status": "Ready" if ready else "Waiting",
                        "status_color": (140, 255, 180) if ready else (255, 220, 120),
                        "ping_text": f"{int(entry.get('ping_ms', 0))} ms",
                    }
                )
            else:
                slots.append(
                    {
                        "slot": idx + 1,
                        "connected": False,
                        "ready": False,
                        "profile": {
                            "username": f"Open Slot {idx + 1}",
                            "color": [70, 70, 90],
                            "hat": "None",
                        },
                        "status": "Open Slot",
                        "status_color": (170, 170, 190),
                        "ping_text": None,
                    }
                )
        return slots

    def can_start_from_lobby(self):
        if self.network_mode != "host" or not self.network_host:
            return True
        return self.network_host.all_connected_ready()

    def _move_progression_selection(self, direction):
        if self.progression_focus_area == "inventory":
            relics = self._get_progression_relics()
            if relics:
                self.progression_selected_relic_index = max(
                    0,
                    min(
                        len(relics) - 1,
                        self.progression_selected_relic_index + direction,
                    ),
                )
        else:
            self.progression_selected_slot_index = max(
                0,
                min(
                    self.progression_system.DEFAULT_LOADOUT_SIZE - 1,
                    self.progression_selected_slot_index + direction,
                ),
            )

    def _selected_relic_id(self):
        relics = self._get_progression_relics()
        if not relics:
            return None
        index = max(0, min(self.progression_selected_relic_index, len(relics) - 1))
        return relics[index]["id"]

    def _handle_progression_key(self, event):
        if event.key in (pygame.K_ESCAPE, pygame.K_p):
            self.state = self._default_frontend_state()
            self._show_status_message("", duration=0)
            return
        if event.key == pygame.K_UP:
            self._move_progression_selection(-1)
            return
        if event.key == pygame.K_DOWN:
            self._move_progression_selection(1)
            return
        if event.key in (pygame.K_LEFT, pygame.K_RIGHT):
            self.progression_focus_area = (
                "loadout" if self.progression_focus_area == "inventory" else "inventory"
            )
            return

        if self.progression_focus_area == "loadout":
            if event.key == pygame.K_BACKSPACE:
                self.progression_system.unequip_relic(self.progression_selected_slot_index)
                self._show_status_message(
                    f"Cleared slot {self.progression_selected_slot_index + 1}."
                )
            return

        relic_id = self._selected_relic_id()
        if not relic_id:
            return
        relic = self.progression_system.relic_definitions.get(relic_id, {})

        if event.key in (pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4):
            slot_index = event.key - pygame.K_1
            if self.progression_system.equip_relic(relic_id, slot_index):
                self.progression_selected_slot_index = slot_index
                self._show_status_message(
                    f"Equipped {relic.get('name', relic_id)} to slot {slot_index + 1}."
                )
            else:
                self._show_status_message("Equip failed. Own the relic and avoid duplicates.")
            return
        if event.key == pygame.K_c:
            if self.progression_system.craft_relic(relic_id):
                self._show_status_message(f"Crafted {relic.get('name', relic_id)}.")
                self._queue_reward_toast(
                    f"Unlocked: {relic.get('name', relic_id)}",
                    (140, 255, 180),
                )
            else:
                self._show_status_message("Not enough credits/essence to craft.")
            return
        if event.key == pygame.K_u:
            if self.progression_system.upgrade_relic(relic_id):
                entry = self.progression_system.get_relic_entry(relic_id)
                self._show_status_message(
                    f"Upgraded {relic.get('name', relic_id)} to rank {entry.get('rank', 1)}."
                )
            else:
                self._show_status_message("Upgrade unavailable or unaffordable.")

    def _build_player_control_profiles(self):
        return [
            {
                "move": {
                    "left": (pygame.K_a,),
                    "right": (pygame.K_d,),
                    "up": (pygame.K_w,),
                    "down": (pygame.K_s,),
                },
                "dash": (pygame.K_LSHIFT,),
                "shoot_keyboard": (pygame.K_SPACE,),
                "shoot_mouse": True,
            },
            {
                "move": {
                    "left": (pygame.K_LEFT,),
                    "right": (pygame.K_RIGHT,),
                    "up": (pygame.K_UP,),
                    "down": (pygame.K_DOWN,),
                },
                "dash": (pygame.K_RCTRL,),
                "shoot_keyboard": (pygame.K_RSHIFT,),
                "shoot_mouse": False,
            },
            {
                "move": {
                    "left": (pygame.K_j,),
                    "right": (pygame.K_l,),
                    "up": (pygame.K_i,),
                    "down": (pygame.K_k,),
                },
                "dash": (pygame.K_u,),
                "shoot_keyboard": (pygame.K_o,),
                "shoot_mouse": False,
            },
            {
                "move": {
                    "left": (pygame.K_KP4,),
                    "right": (pygame.K_KP6,),
                    "up": (pygame.K_KP8,),
                    "down": (pygame.K_KP5,),
                },
                "dash": (pygame.K_KP7,),
                "shoot_keyboard": (pygame.K_KP9,),
                "shoot_mouse": False,
            },
        ]

    def _sync_network_player_roster(self):
        if self.network_mode != "host" or not self.network_host:
            return

        connected_remote = self.network_host.get_connected_player_indices()
        connected_remote = [idx for idx in connected_remote if 1 <= idx <= 3]
        desired_indices = [0] + connected_remote
        current_indices = sorted(player.player_index for player in self.players)
        if current_indices != sorted(desired_indices):
            current_by_index = {player.player_index: player for player in self.players}
            for idx in desired_indices:
                if idx not in current_by_index:
                    current_by_index[idx] = self._create_player(idx)

            self.players = [current_by_index[idx] for idx in sorted(desired_indices)]
        lobby_state = self.network_host.get_lobby_state()
        for player in self.players:
            if player.player_index <= 0:
                continue
            info = lobby_state.get(player.player_index, {})
            profile = info.get("profile", {})
            if not profile:
                continue
            player.username = profile.get(
                "username", player.username or f"P{player.player_index + 1}"
            )
            player.color = tuple(profile.get("color", player.color))
            player.hat_style = profile.get("hat", player.hat_style or "None")
        self.player = next(
            (p for p in self.players if p.player_index == 0), self.players[0]
        )
        self.customization_player_index = min(
            self.customization_player_index, max(0, len(self.players) - 1)
        )
        self._prime_player_tracking()

    def get_alive_players(self):
        return [p for p in self.players if p.health > 0]

    def get_target_player(self, actor=None):
        """Pick the nearest alive player to the requesting actor; fallback to primary."""
        alive_players = self.get_alive_players()
        if not alive_players:
            return self.player
        if actor is None or not hasattr(actor, "x") or not hasattr(actor, "y"):
            return alive_players[0]

        actor_cx = actor.x + getattr(actor, "width", 0) * 0.5
        actor_cy = actor.y + getattr(actor, "height", 0) * 0.5
        return min(
            alive_players,
            key=lambda p: (
                (p.x + p.width * 0.5 - actor_cx) ** 2
                + (p.y + p.height * 0.5 - actor_cy) ** 2
            ),
        )

    def _prime_player_tracking(self):
        self.bottom_camp_frames = {id(player): 0 for player in self.players}
        self.last_player_pos = {
            id(player): (player.x, player.y) for player in self.players
        }

    def _is_any_key_pressed(self, keys, bindings):
        return any(keys[key] for key in bindings)

    def _virtual_keys_from_input(self, profile, input_state):
        key_state = {}
        move = profile.get("move", {})
        if input_state.get("left"):
            for key in move.get("left", ()):
                key_state[key] = True
        if input_state.get("right"):
            for key in move.get("right", ()):
                key_state[key] = True
        if input_state.get("up"):
            for key in move.get("up", ()):
                key_state[key] = True
        if input_state.get("down"):
            for key in move.get("down", ()):
                key_state[key] = True
        return key_state

    def _get_auto_target_for_player(self, player):
        if not self.current_bosses:
            return (player.x + player.width // 2, player.y - 100)
        target_boss = min(
            self.current_bosses,
            key=lambda boss: (
                (boss.x + boss.width * 0.5 - (player.x + player.width * 0.5)) ** 2
                + (boss.y + boss.height * 0.5 - (player.y + player.height * 0.5)) ** 2
            ),
        )
        target_x = int(target_boss.x + target_boss.width * 0.5)
        target_y = int(target_boss.y + target_boss.height * 0.5)
        return (target_x, target_y)

    def _build_network_world_state(self):
        players = []
        for player in self.players:
            players.append(
                {
                    "slot": int(getattr(player, "player_index", 0)) + 1,
                    "x": int(player.x),
                    "y": int(player.y),
                    "hp": int(player.health),
                    "max_hp": int(player.max_health),
                }
            )
        bosses = []
        for boss in self.current_bosses:
            bosses.append(
                {
                    "name": str(getattr(boss, "name", "Boss")),
                    "x": int(getattr(boss, "x", 0)),
                    "y": int(getattr(boss, "y", 0)),
                    "hp": int(getattr(boss, "health", 0)),
                    "max_hp": int(getattr(boss, "max_health", 1)),
                }
            )
        return {
            "game_state": str(self.state.value),
            "score": int(self.score),
            "players": players,
            "bosses": bosses,
            "lobby": self.get_lobby_slots() if self.network_mode == "host" else [],
            "host_address": self.get_display_host_address(),
        }

    def _record_replay_frame(self):
        if not self.replay_log_enabled:
            return
        frame = {
            "t": round(time.time(), 3),
            "state": self.state.value,
            "score": int(self.score),
            "players": [
                {
                    "slot": int(getattr(player, "player_index", 0)) + 1,
                    "x": round(float(player.x), 2),
                    "y": round(float(player.y), 2),
                    "hp": int(player.health),
                }
                for player in self.players
            ],
            "bosses": [
                {
                    "name": str(getattr(boss, "name", "Boss")),
                    "x": round(float(getattr(boss, "x", 0)), 2),
                    "y": round(float(getattr(boss, "y", 0)), 2),
                    "hp": int(getattr(boss, "health", 0)),
                }
                for boss in self.current_bosses
            ],
        }
        if self.network_mode == "host" and self.network_host:
            frame["inputs"] = {
                str(slot + 1): self.network_host.get_player_input(slot)
                for slot in self.network_host.get_connected_player_indices()
            }
        self.replay_log_frames.append(frame)

    def _flush_replay_log(self):
        if not self.replay_log_enabled or not self.replay_log_frames:
            return
        os.makedirs("logs", exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = os.path.join("logs", f"replay_{ts}.json")
        payload = {
            "created_at": datetime.now().isoformat(),
            "network_mode": self.network_mode,
            "sync_mode": self.network_sync_mode,
            "frames": self.replay_log_frames,
        }
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2)

    def _handle_customization_key(self, event):
        return handle_customization_key(self, event)

    def _check_boss_name_consistency(self):
        mismatches = self.boss_manager.validate_boss_name_consistency()
        if mismatches:
            self.error_handler.logger.warning("Boss name consistency warnings:")
            for class_name, actual, expected in mismatches:
                self.error_handler.logger.warning(
                    "  - %s: '%s' -> '%s'", class_name, actual, expected
                )

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
        if current_surface and not self.fullscreen:
            self._windowed_size = current_surface.get_size()

        def toggle_operation():
            if self.fullscreen:
                self.fullscreen = False
                self.screen = pygame.display.set_mode(self._windowed_size)
                self.collision_system.update_bounds(
                    self.screen.get_width(), self.screen.get_height()
                )
                return True

            if pygame.display.get_driver() in ("x11", "wayland"):
                self.fullscreen = True
                pygame.display.toggle_fullscreen()
                self.screen = pygame.display.get_surface() or self.screen
                return True

            info = pygame.display.Info()
            self.fullscreen = True
            self.screen = pygame.display.set_mode(
                (info.current_w, info.current_h), pygame.FULLSCREEN
            )
            self.collision_system.update_bounds(
                self.screen.get_width(), self.screen.get_height()
            )
            return True

        result = self.error_handler.safe_pygame_operation(toggle_operation)
        if not result:
            self.fullscreen = False
            self.screen = self.error_handler.safe_pygame_operation(
                lambda: pygame.display.set_mode(self._windowed_size)
            )
        if self.screen:
            self.collision_system.update_bounds(
                self.screen.get_width(), self.screen.get_height()
            )

    def reset_game(self):
        """Reset game for a new run"""
        self.state = self._default_frontend_state()
        self.audio_manager.stop_music()
        self.run_in_progress = False
        self._init_players()
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
        self.milestone_upgrade_round = False
        self.bottom_camp_frames = {}
        self.pressure_cooldown = 0
        self.last_player_pos = {}
        self._prime_player_tracking()
        self.performance_logger = PerformanceLogger()
        self.collision_system = CollisionSystem(self.performance_logger, WIDTH, HEIGHT)
        self.render_system.clear_batches()
        self.damage_numbers.clear()
        self.progression_status_message = ""
        self.progression_status_timer = 0

    def start_boss_fight(self):
        if not self.run_in_progress:
            self.run_in_progress = True
            self.progression_system.record_run_started()

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
                self.boss_manager.apply_player_progression_scaling(boss, self.players)

                self.state = GameState.BOSS_INTRO
                self.intro_timer = BOSS_INTRO_DURATION
                self.fight_start_time = pygame.time.get_ticks() / 1000

                self.arena_seed = (
                    pygame.time.get_ticks()
                    + self.boss_manager.bosses_defeated_count * 1337
                ) & 0xFFFFFFFF
                self.arena_style = self._get_arena_style(boss)

                # Reset flags for new fight
                self.victory_analysis_printed = False
                self.game_over_analysis_printed = False
                self._play_boss_music([boss])

                self.performance_logger.start_boss_fight(boss.name)
            else:
                self.state = GameState.VICTORY
                reward = self.progression_system.grant_run_victory_bonus()
                self._queue_reward_toast(
                    f"Victory bonus: +{reward.get('credits', 0)} Credits",
                    (140, 255, 180),
                )
                self.run_in_progress = False
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
                    self.boss_manager.apply_player_progression_scaling(boss, self.players)

                self.state = GameState.BOSS_INTRO
                self.intro_timer = BOSS_INTRO_DURATION
                self.fight_start_time = pygame.time.get_ticks() / 1000

                self.arena_seed = (
                    pygame.time.get_ticks()
                    + self.boss_manager.bosses_defeated_count * 1337
                ) & 0xFFFFFFFF
                self.arena_style = self._get_arena_style(
                    boss1
                )  # Use first boss for arena style

                # Reset flags for new fight
                self.victory_analysis_printed = False
                self.game_over_analysis_printed = False
                self._play_boss_music(self.current_bosses)

                for boss in self.current_bosses:
                    self.performance_logger.start_boss_fight(boss.name)
            else:
                self.state = GameState.VICTORY
                self.audio_manager.stop_music()
                reward = self.progression_system.grant_run_victory_bonus()
                self._queue_reward_toast(
                    f"Victory bonus: +{reward.get('credits', 0)} Credits",
                    (140, 255, 180),
                )
                self.run_in_progress = False

    def _play_boss_music(self, bosses):
        """Play mapped boss track for the current fight, if available."""
        if not bosses:
            return
        for boss in bosses:
            filename = self.boss_music_tracks.get(boss.name)
            if isinstance(filename, (list, tuple)):
                filename = random.choice(filename)
            if filename:
                if filename == "VoidAssassinM.mp3":
                    filename = "VoidAssassainM.mp3"
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
        for player in self.players:
            heal_amount = max(1, int(player.max_health * HEAL_AFTER_BOSS_PERCENTAGE))
            player.health = min(player.max_health, player.health + heal_amount)

    def open_upgrade_screen(self):
        upgrade_anchor = (
            self.get_alive_players()[0] if self.get_alive_players() else self.player
        )
        defeated = self.boss_manager.bosses_defeated_count
        self.milestone_upgrade_round = defeated > 0 and defeated % 5 == 0
        if self.milestone_upgrade_round:
            self.pending_upgrades = self.upgrade_system.get_milestone_upgrades(upgrade_anchor)
        else:
            self.pending_upgrades = self.upgrade_system.get_random_upgrades(upgrade_anchor)
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
            apply_to = upgrade.get("apply_to")
            if callable(apply_to):
                for player in self.players:
                    apply_to(player)
            else:
                upgrade["apply"]()

            if self.pending_between_round_heal:
                self.heal_after_boss()
                self.pending_between_round_heal = False

            for player in self.players:
                if player.health > player.max_health:
                    player.health = player.max_health

            self.pending_upgrades = []
            self.hovered_upgrade_index = -1
            self.milestone_upgrade_round = False

            # Start next boss fight using the boss manager
            self.start_boss_fight()
        except Exception as e:
            self.error_handler.logger.error(f"Error applying upgrade: {e}")

    def handle_collisions(self):
        """Handle collisions using the collision system"""
        if not self.current_bosses:
            return

        self.collision_system.handle_collisions(self.players, self.current_bosses)

    def _apply_anti_camp_pressure(self):
        """Nudge bottom-camping players with readable telegraphed danger."""
        if not self.current_bosses:
            return

        if self.pressure_cooldown > 0:
            self.pressure_cooldown -= 1

        screen_h = self.screen.get_height()
        biggest_camper = None
        biggest_frames = -1

        for player in self.get_alive_players():
            pid = id(player)
            lx, ly = self.last_player_pos.get(pid, (player.x, player.y))
            moved_sq = (player.x - lx) * (player.x - lx) + (player.y - ly) * (
                player.y - ly
            )
            self.last_player_pos[pid] = (player.x, player.y)

            in_bottom_zone = player.y > int(screen_h * 0.62)
            mostly_stationary = moved_sq < 2.25
            frames = self.bottom_camp_frames.get(pid, 0)

            if in_bottom_zone and mostly_stationary:
                frames += 1
            else:
                frames = max(0, frames - 2)

            self.bottom_camp_frames[pid] = frames
            if frames > biggest_frames:
                biggest_frames = frames
                biggest_camper = player

        if biggest_camper is None or biggest_frames < 75 or self.pressure_cooldown > 0:
            return

        target_x = (
            biggest_camper.x + biggest_camper.width // 2 + random.randint(-20, 20)
        )
        target_y = (
            biggest_camper.y + biggest_camper.height // 2 + random.randint(-20, 20)
        )
        for boss in self.current_bosses:
            t = Telegraph(
                target_x,
                target_y,
                50,
                50,
                (255, 120, 60),
                damage=8,
                warning_type="pulse",
            )
            t.active_start = 28
            t.active_end = 50
            boss.effects.append(t)

        self.pressure_cooldown = 150
        self.bottom_camp_frames[id(biggest_camper)] = 30

    def update(self):
        self._sync_network_player_roster()

        if self.state == GameState.FIGHTING:
            self.collision_system.update_bounds(
                self.screen.get_width(), self.screen.get_height()
            )
            keys = pygame.key.get_pressed()
            mouse_pressed = pygame.mouse.get_pressed()
            mx, my = pygame.mouse.get_pos()

            for player in self.players:
                if player.health <= 0:
                    continue

                profile = (
                    getattr(player, "input_profile", None) or self.control_profiles[0]
                )
                use_network_input = (
                    self.network_mode == "host"
                    and self.network_host is not None
                    and player.player_index > 0
                    and self.network_host.has_client(player.player_index)
                )

                if use_network_input:
                    remote_input = self.network_host.get_player_input(
                        player.player_index
                    )
                    virtual_keys = self._virtual_keys_from_input(profile, remote_input)
                    player.move(virtual_keys, profile.get("move"))
                    if remote_input.get("dash"):
                        player.dash()
                    if remote_input.get("shoot"):
                        tx, ty = self._get_auto_target_for_player(player)
                        player.shoot(tx, ty)
                elif self.network_mode != "host" or player.player_index == 0:
                    player.move(keys, profile.get("move"))

                    if self._is_any_key_pressed(keys, profile.get("dash", ())):
                        player.dash()

                    keyboard_shoot = self._is_any_key_pressed(
                        keys, profile.get("shoot_keyboard", ())
                    )
                    mouse_shoot = profile.get("shoot_mouse", False) and bool(
                        mouse_pressed[0]
                    )
                    if keyboard_shoot or mouse_shoot:
                        if profile.get("shoot_mouse", False):
                            player.shoot(mx, my)
                        else:
                            tx, ty = self._get_auto_target_for_player(player)
                            player.shoot(tx, ty)

            for player in self.players:
                player.update()

            # Update all bosses
            primary_player = self.player
            for boss in self.current_bosses:
                self.player = self.get_target_player(boss)
                boss.update()
            self.player = primary_player

            # Record performance stats
            sample_player = (
                self.get_alive_players()[0] if self.get_alive_players() else self.player
            )
            self.performance_logger.tick_frame(sample_player, self.current_bosses)
            self._apply_anti_camp_pressure()

            self.handle_collisions()
            self.damage_numbers.update(self.current_bosses)
            self._record_replay_frame()

            if not self.get_alive_players():
                self.state = GameState.GAME_OVER
                self.audio_manager.stop_music()
                self.run_in_progress = False
                for boss in self.current_bosses:
                    self.performance_logger.end_boss_fight(boss.name, victory=False)
                self.progression_system.update_deepest_boss_count(
                    self.boss_manager.bosses_defeated_count
                )

            # Remove dead bosses from the list (but keep them for performance tracking)
            dead_bosses = [boss for boss in self.current_bosses if boss.health <= 0]
            if dead_bosses:
                for dead_boss in dead_bosses:
                    self.performance_logger.end_boss_fight(dead_boss.name, victory=True)
                    self.boss_manager.on_boss_defeated(dead_boss)
                    rewards = self.progression_system.grant_boss_rewards(
                        dead_boss,
                        weakened=bool(getattr(dead_boss, "is_weakened", False)),
                    )
                    self._queue_reward_summary(rewards)

                # Remove dead bosses from current_bosses
                self.current_bosses = [
                    boss for boss in self.current_bosses if boss.health > 0
                ]

                # If any bosses died, add score immediately
                if dead_bosses:
                    self.score += 500 * len(dead_bosses)
                    self.progression_system.update_deepest_boss_count(
                        self.boss_manager.bosses_defeated_count
                    )

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
                # Short grace to avoid instant unavoidable hits on intro end.
                for player in self.players:
                    player.invincible_time = max(player.invincible_time, 24)

        # Update screen shake
        if self.screen_shake.duration > 0:
            self.screen_shake.update()

        if self.progression_status_timer > 0:
            self.progression_status_timer -= 1
            if self.progression_status_timer <= 0:
                self.progression_status_message = ""

        active_toasts = []
        for toast in self.reward_toasts:
            toast["timer"] -= 1
            if toast["timer"] > 0:
                active_toasts.append(toast)
        self.reward_toasts = active_toasts

    def draw(self):
        return draw_game(self)

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
                    if self.state == GameState.JOIN_SETUP:
                        self._handle_join_menu_key(event)
                        continue
                    if self.state == GameState.PROGRESSION:
                        self._handle_progression_key(event)
                        continue
                    if self.state == GameState.CUSTOMIZATION:
                        self._handle_customization_key(event)
                        continue
                    if event.key == pygame.K_F11:
                        self.toggle_fullscreen()
                    elif event.key == pygame.K_h and self.state == GameState.MENU:
                        self.open_host_lobby()
                    elif event.key == pygame.K_j and self.state == GameState.MENU:
                        self.open_join_menu()
                    elif event.key == pygame.K_c and self.state in (GameState.MENU, GameState.LOBBY):
                        self.customization_player_index = 0
                        self.customization_field_index = 0
                        self.state = GameState.CUSTOMIZATION
                    elif event.key == pygame.K_p and self.state in (GameState.MENU, GameState.LOBBY):
                        self.progression_focus_area = "inventory"
                        self.progression_selected_relic_index = 0
                        self.progression_selected_slot_index = 0
                        self.progression_status_message = ""
                        self.state = GameState.PROGRESSION
                    elif event.key == pygame.K_SPACE:
                        if self.state in (GameState.MENU, GameState.LOBBY):
                            if (
                                self.network_mode == "host"
                                and self.network_host
                                and not self.can_start_from_lobby()
                            ):
                                self.error_handler.logger.info(
                                    "Waiting for all connected clients to be ready."
                                )
                                continue
                            self.start_boss_fight()
                        elif self.state == GameState.VICTORY:
                            if (
                                self.network_mode == "host"
                                and self.network_host
                                and not self.network_host.all_connected_ready()
                            ):
                                self.error_handler.logger.info(
                                    "Waiting for all connected clients to be ready."
                                )
                                continue
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
                if self.network_mode == "host" and self.network_host:
                    self.network_host.send_frame(
                        self.screen,
                        pygame,
                        world_state=self._build_network_world_state(),
                    )
            except Exception:
                self.error_handler.logger.exception("Unhandled error in main game loop")
                self.running = False
            self.clock.tick(FPS)

        pygame.quit()
        self.audio_manager.cleanup()
        if self.network_host:
            self.network_host.stop()
        self.progression_system.save_profile()
        self._flush_replay_log()


if __name__ == "__main__":
    mode = os.getenv("BOSS_RUSH_NETWORK_MODE", "off").strip().lower()
    if mode == "client":
        run_network_client()
    else:
        game = Game()
        game.run()
        if game.launch_network_client_after_exit:
            run_network_client()
