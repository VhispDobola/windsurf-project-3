import os
import zlib

import pygame

from config.constants import WIDTH, HEIGHT, FPS, init_pygame
from core.progression_system import ProgressionSystem
from core.network_sync import NetworkClient
from ui import UIManager


def run_network_client():
    init_pygame()
    host = os.getenv("BOSS_RUSH_HOST", "127.0.0.1").strip()
    port = int(os.getenv("BOSS_RUSH_PORT", "50000"))
    slot_env = os.getenv("BOSS_RUSH_PLAYER_SLOT", "auto").strip().lower()
    if slot_env in ("auto", "0", ""):
        player_index = 0
        player_slot = None
    else:
        try:
            player_slot = int(slot_env)
        except ValueError:
            player_slot = 2
        player_slot = max(2, min(4, player_slot))
        player_index = player_slot - 1

    progression = ProgressionSystem()
    identity = progression.get_lobby_profile()
    client = NetworkClient(host, port, player_index=player_index, profile=identity)
    try:
        client.connect()
    except (OSError, TimeoutError) as exc:
        print(f"Unable to connect to host {host}:{port} for player slot {player_slot}.")
        print(f"Reason: {exc}")
        print("Check host IP, firewall, and that host mode is running.")
        pygame.quit()
        return

    assigned_slot = client.assigned_player_slot or player_slot or 2
    info = pygame.display.Info()
    screen = pygame.display.set_mode((info.current_w, info.current_h), pygame.FULLSCREEN)
    pygame.display.set_caption(f"Boss Rush Game (LAN Client P{assigned_slot})")
    clock = pygame.time.Clock()
    running = True
    latest_surface = None
    latest_state = None
    font = pygame.font.Font(None, 24)
    ui_manager = UIManager()
    ready = False
    controls = {
        "left": pygame.K_LEFT,
        "right": pygame.K_RIGHT,
        "up": pygame.K_UP,
        "down": pygame.K_DOWN,
        "dash": pygame.K_RCTRL,
        "shoot": pygame.K_RSHIFT,
    }

    while running and client.running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    ready = not ready
                    client.set_ready(ready)

        keys = pygame.key.get_pressed()
        input_state = {
            "left": bool(keys[controls["left"]]),
            "right": bool(keys[controls["right"]]),
            "up": bool(keys[controls["up"]]),
            "down": bool(keys[controls["down"]]),
            "dash": bool(keys[controls["dash"]]),
            "shoot": bool(keys[controls["shoot"]]),
        }
        client.send_input(input_state=input_state)

        update = client.get_latest_update()
        if update:
            update_type = update.get("type")
            if update_type == "frame":
                w = int(update.get("w", WIDTH))
                h = int(update.get("h", HEIGHT))
                latest_state = update.get("state", latest_state)
                packed = update.get("data", b"")
                try:
                    raw = zlib.decompress(packed)
                    latest_surface = pygame.image.fromstring(raw, (w, h), "RGB")
                    if screen.get_width() != w or screen.get_height() != h:
                        display_info = pygame.display.Info()
                        screen = pygame.display.set_mode(
                            (display_info.current_w, display_info.current_h),
                            pygame.FULLSCREEN,
                        )
                except (zlib.error, ValueError):
                    latest_surface = None
            elif update_type == "state":
                latest_state = update.get("state", {})

        if isinstance(latest_state, dict) and latest_state.get("game_state") == "lobby":
            screen.fill((12, 14, 20))
            lobby_slots = latest_state.get("lobby", [])
            can_start = all(
                bool(slot.get("ready", False) or slot.get("slot") == 1)
                for slot in lobby_slots
                if slot.get("connected")
            )
            ui_manager.draw_lobby(
                screen,
                lobby_slots,
                local_slot=assigned_slot,
                host_address=latest_state.get("host_address"),
                can_start=can_start,
                host_mode=False,
            )
        elif client.sync_mode == "state":
            screen.fill((15, 18, 24))
            title = font.render(f"Authoritative State Sync | P{assigned_slot}", True, (220, 220, 220))
            screen.blit(title, (16, 12))
            y = 40
            for line in (
                f"State: {latest_state.get('game_state', 'unknown')}" if isinstance(latest_state, dict) else "State: unknown",
                f"Score: {latest_state.get('score', 0)}" if isinstance(latest_state, dict) else "Score: 0",
                f"Players: {len(latest_state.get('players', []))}" if isinstance(latest_state, dict) else "Players: 0",
                f"Bosses: {len(latest_state.get('bosses', []))}" if isinstance(latest_state, dict) else "Bosses: 0",
            ):
                surf = font.render(line, True, (180, 200, 220))
                screen.blit(surf, (16, y))
                y += 24
        else:
            if latest_surface:
                screen.blit(latest_surface, (0, 0))
            else:
                screen.fill((0, 0, 0))

        status = client.get_status()
        net_line = f"Ping: {status.get('ping_ms', 0)} ms | Ready: {'Yes' if ready else 'No'} (Enter)"
        net_surf = font.render(net_line, True, (255, 240, 120))
        screen.blit(net_surf, (12, screen.get_height() - 28))

        pygame.display.flip()
        clock.tick(FPS)

    client.close()
    pygame.quit()
