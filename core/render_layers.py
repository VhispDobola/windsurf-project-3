from enum import IntEnum


class RenderLayer(IntEnum):
    MAP_BG = 0
    MAP_FG = 10
    EFFECTS_BG = 20
    PROJECTILES = 30
    ENTITIES = 40
    EFFECTS_FG = 50
    UI = 100
