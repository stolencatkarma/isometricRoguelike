# Endgame procedural map generation skeleton for isometric roguelike
# This module will provide functions to generate random dungeon maps for the endgame dive.
# Actual generation logic will be implemented later.

import random

ENDGAME_TILE_FLOOR = 0
ENDGAME_TILE_WALL = 1
ENDGAME_TILE_EXIT = 2


def generate_endgame_map(depth=1, width=12, height=12):
    """
    Generate a random dungeon map for the endgame dive.
    Difficulty and complexity should increase with depth.
    For now, returns a simple empty map with walls around the edge and a single exit.
    """
    grid = [[ENDGAME_TILE_FLOOR for _ in range(width)] for _ in range(height)]
    # Add walls around the edge
    for y in range(height):
        for x in range(width):
            if x == 0 or y == 0 or x == width-1 or y == height-1:
                grid[y][x] = ENDGAME_TILE_WALL
    # Place an exit at bottom right
    grid[height-2][width-2] = ENDGAME_TILE_EXIT
    return {
        "grid": grid,
        "width": width,
        "height": height,
        "depth": depth,
        "city": False,
        "endgame": True
    }

# Later: add monster placement, traps, loot, etc. based on depth
