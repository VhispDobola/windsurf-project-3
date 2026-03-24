import pygame

from config.constants import BLUE, CYAN, ORANGE, GREEN
from core.game_state import GameState


def default_customization(game, index):
    default_colors = [BLUE, CYAN, ORANGE, GREEN]
    return {
        "username": f"P{index + 1}",
        "color": default_colors[index % len(default_colors)],
        "hat": "None",
    }


def apply_customization_to_player(game, player, player_index):
    profile = game.player_customizations[player_index]
    player.color = profile.get("color", BLUE)
    player.username = profile.get("username", f"P{player_index + 1}")
    player.hat_style = profile.get("hat", "None")


def persist_primary_identity(game):
    if not getattr(game, "progression_system", None):
        return
    if not game.player_customizations:
        return
    profile = game.player_customizations[0]
    game.progression_system.update_player_identity(
        username=profile.get("username"),
        color=profile.get("color"),
        hat=profile.get("hat"),
    )


def cycle_color(game, direction):
    if not game.players:
        return
    idx = game.customization_player_index
    current = game.players[idx].color
    try:
        current_idx = game.color_options.index(current)
    except ValueError:
        current_idx = 0
    new_idx = (current_idx + direction) % len(game.color_options)
    new_color = game.color_options[new_idx]
    game.players[idx].color = new_color
    game.player_customizations[idx]["color"] = new_color
    if idx == 0:
        persist_primary_identity(game)


def cycle_hat(game, direction):
    if not game.players:
        return
    idx = game.customization_player_index
    current_hat = game.players[idx].hat_style
    try:
        current_idx = game.hat_options.index(current_hat)
    except ValueError:
        current_idx = 0
    new_idx = (current_idx + direction) % len(game.hat_options)
    new_hat = game.hat_options[new_idx]
    game.players[idx].hat_style = new_hat
    game.player_customizations[idx]["hat"] = new_hat
    if idx == 0:
        persist_primary_identity(game)


def append_username_char(game, char):
    if not game.players:
        return
    if not char:
        return
    if not (char.isalnum() or char in (" ", "_", "-")):
        return
    idx = game.customization_player_index
    current = game.players[idx].username or ""
    if len(current) >= 16:
        return
    updated = current + char
    game.players[idx].username = updated
    game.player_customizations[idx]["username"] = updated
    if idx == 0:
        persist_primary_identity(game)


def remove_username_char(game):
    if not game.players:
        return
    idx = game.customization_player_index
    current = game.players[idx].username or ""
    updated = current[:-1]
    if not updated:
        updated = f"P{idx + 1}"
    game.players[idx].username = updated
    game.player_customizations[idx]["username"] = updated
    if idx == 0:
        persist_primary_identity(game)


def handle_customization_key(game, event):
    if event.key in (pygame.K_ESCAPE, pygame.K_RETURN):
        game.state = game._default_frontend_state()
        return

    if event.key == pygame.K_TAB:
        game.customization_player_index = (game.customization_player_index + 1) % len(game.players)
        return
    if event.key == pygame.K_UP:
        game.customization_field_index = (game.customization_field_index - 1) % 3
        return
    if event.key == pygame.K_DOWN:
        game.customization_field_index = (game.customization_field_index + 1) % 3
        return

    if game.customization_field_index == 0:
        if event.key == pygame.K_BACKSPACE:
            remove_username_char(game)
        else:
            append_username_char(game, event.unicode)
        return

    if game.customization_field_index == 1:
        if event.key == pygame.K_LEFT:
            cycle_color(game, -1)
        elif event.key == pygame.K_RIGHT:
            cycle_color(game, 1)
        return

    if game.customization_field_index == 2:
        if event.key == pygame.K_LEFT:
            cycle_hat(game, -1)
        elif event.key == pygame.K_RIGHT:
            cycle_hat(game, 1)
