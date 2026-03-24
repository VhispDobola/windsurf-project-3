import math

import pygame

from config.constants import BLACK, YELLOW
from core import RenderLayer
from core.game_state import GameState


def draw(game):
    if game.state == GameState.MENU:
        game.screen.fill(BLACK)
        game.ui_manager.draw_menu(game.screen)
    elif game.state == GameState.LOBBY:
        game.screen.fill(BLACK)
        game.ui_manager.draw_lobby(
            game.screen,
            game.get_lobby_slots(),
            local_slot=1,
            host_address=game.get_display_host_address(),
            can_start=game.can_start_from_lobby(),
            host_mode=True,
        )
    elif game.state == GameState.JOIN_SETUP:
        game.screen.fill(BLACK)
        game.ui_manager.draw_join_setup(
            game.screen,
            game.join_menu_host,
            game.join_menu_port,
            game.get_join_slot_label(),
            game.join_menu_field_index,
            game.join_menu_status,
        )
    elif game.state == GameState.CUSTOMIZATION:
        game.screen.fill(BLACK)
        game.ui_manager.draw_customization(
            game.screen,
            game.players,
            game.customization_player_index,
            game.customization_field_index,
            game.color_options,
            game.hat_options,
        )
    elif game.state == GameState.PROGRESSION:
        game.screen.fill(BLACK)
        game.ui_manager.draw_progression_menu(
            game.screen,
            game.progression_system,
            game.progression_selected_relic_index,
            game.progression_selected_slot_index,
            game.progression_focus_area,
            game.progression_status_message,
        )
    elif game.state == GameState.BOSS_INTRO:
        game._draw_arena_background(game.screen)
        if game.current_bosses:
            game.ui_manager.draw_boss_intro(game.screen, game.current_bosses, game._get_boss_hint_text())
    elif game.state == GameState.FIGHTING:
        game.render_system.width = game.screen.get_width()
        game.render_system.height = game.screen.get_height()
        game.render_system.clear_batches()
        populate_render_batches(game)
        game.render_system.render(game.screen, background_draw=game._draw_arena_background)

        draw_offscreen_indicators(game)
        game.damage_numbers.draw(game.screen)
        game.ui_manager.draw_player_status(game.screen, game.players)
        game.ui_manager.draw_boss_hud(game.screen, game.current_bosses)
    elif game.state == GameState.UPGRADE:
        game.screen.fill(BLACK)
        title = "POWER UPGRADE" if getattr(game, "milestone_upgrade_round", False) else "CHOOSE UPGRADE"
        subtitle = "Boss milestone reward" if getattr(game, "milestone_upgrade_round", False) else "Press 1-4 or Click to pick"
        game.ui_manager.draw_upgrade_screen(game.screen, game.pending_upgrades, game.hovered_upgrade_index, title=title, subtitle=subtitle)
    elif game.state == GameState.VICTORY:
        game.screen.fill(BLACK)
        game.ui_manager.draw_victory(game.screen, game.score, game.total_time)
        if not game.victory_analysis_printed:
            game.performance_logger.print_analysis()
            game.performance_logger.save_session()
            game.victory_analysis_printed = True
    elif game.state == GameState.GAME_OVER:
        game.screen.fill(BLACK)
        game.ui_manager.draw_game_over(game.screen)
        if not game.game_over_analysis_printed:
            game.performance_logger.print_analysis()
            game.performance_logger.save_session()
            game.game_over_analysis_printed = True

    if game.network_mode == "host" and game.network_host:
        _draw_host_network_overlay(game)

    game.ui_manager.draw_reward_toasts(game.screen, getattr(game, "reward_toasts", []))

    if game.screen_shake.duration > 0:
        game.screen_shake.apply_offset(game.screen)

    pygame.display.flip()


def draw_offscreen_indicators(game):
    if not game.current_bosses:
        return
    screen_w = game.screen.get_width()
    screen_h = game.screen.get_height()
    center_x = screen_w // 2
    center_y = screen_h // 2
    max_indicators = 20
    count = 0

    for boss in game.current_bosses:
        for projectile in boss.get_all_projectiles():
            if count >= max_indicators:
                return
            pos = get_projectile_position(projectile)
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

            pygame.draw.polygon(game.screen, YELLOW, [tip, left, right])
            count += 1


def get_projectile_position(projectile):
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


def populate_render_batches(game):
    for player in game.players:
        player_layer = getattr(player, "render_layer", RenderLayer.ENTITIES)
        game.render_system.add_object(player, player_layer)

    for boss in game.current_bosses:
        boss_layer = getattr(boss, "render_layer", RenderLayer.ENTITIES)
        game.render_system.add_object(boss, boss_layer)


def _draw_host_network_overlay(game):
    stats = game.network_host.get_stats()
    font = pygame.font.Font(None, 20)
    x = 10
    y = game.screen.get_height() - 18
    if not stats:
        text = "LAN: no clients connected"
        surf = font.render(text, True, (190, 190, 190))
        game.screen.blit(surf, (x, y))
        return
    parts = []
    for idx in sorted(stats.keys()):
        entry = stats[idx]
        parts.append(
            f"P{idx + 1} ping {entry.get('ping_ms', 0)}ms {'R' if entry.get('ready', False) else 'NR'}"
        )
    text = "LAN: " + " | ".join(parts)
    surf = font.render(text, True, (255, 240, 120))
    game.screen.blit(surf, (x, y))
