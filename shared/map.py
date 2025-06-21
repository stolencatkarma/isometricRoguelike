# shared/map.py
"""
Map representation and utilities for the isometric roguelike game.
"""

import random

# Tile codes
FLOOR = 0
WALL = 1
EXIT = 2

TILE_NAMES = {
    FLOOR: "floor",
    WALL: "wall",
    EXIT: "exit"
}

MAX_MAP_SIZE = 256

class GameMap:
    def __init__(self, width, height):
        self.width = min(width, MAX_MAP_SIZE)
        self.height = min(height, MAX_MAP_SIZE)
        self.grid = [[FLOOR for _ in range(self.width)] for _ in range(self.height)]
        self.generate_walls_and_exits()

    def generate_walls_and_exits(self):
        # Simple random walls and one exit for demo
        for y in range(self.height):
            for x in range(self.width):
                if x == 0 or y == 0 or x == self.width-1 or y == self.height-1:
                    self.grid[y][x] = WALL
                elif random.random() < 0.1:
                    self.grid[y][x] = WALL
        # Place an exit in a random location on the edge
        edge = random.choice([0, self.width-1])
        self.grid[random.randint(1, self.height-2)][edge] = EXIT

    def is_walkable(self, x, y):
        if 0 <= x < self.width and 0 <= y < self.height:
            return self.grid[y][x] != WALL
        return False

    def is_exit(self, x, y):
        if 0 <= x < self.width and 0 <= y < self.height:
            return self.grid[y][x] == EXIT
        return False

    def to_dict(self):
        return {
            "width": self.width,
            "height": self.height,
            "grid": self.grid
        }
