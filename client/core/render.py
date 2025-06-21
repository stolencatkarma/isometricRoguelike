import pygame
import math
from .sprites import draw_sprite

def draw_isometric_grid(screen, map_grid, map_height, map_width, SPRITE_PALETTE, SPRITE_TILES, TILE_WIDTH, TILE_HEIGHT, zoom):
    if not map_grid or not SPRITE_PALETTE or not SPRITE_TILES:
        return
    for y in range(map_height):
        for x in range(map_width):
            tile = map_grid[y][x]
            sx = int(((x - y) * (TILE_WIDTH // 2) + screen.get_width() // 2) * zoom + (1-zoom)*screen.get_width()//2)
            sy = int(((x + y) * (TILE_HEIGHT // 2) + 50) * zoom + (1-zoom)*screen.get_height()//2)
            # Choose sprite by tile type
            if tile == 0:
                sprite = SPRITE_TILES["floor"]
            elif tile == 1:
                sprite = SPRITE_TILES["wall"]
            elif tile == 2:
                sprite = SPRITE_TILES["exit"]
            elif tile == 3:
                sprite = SPRITE_TILES.get("waypoint", SPRITE_TILES["exit"])
            elif tile == 4:
                sprite = SPRITE_TILES.get("event", SPRITE_TILES["floor"])
            else:
                sprite = SPRITE_TILES["floor"]
            draw_sprite(screen, sprite, SPRITE_PALETTE, sx, sy, 4)

def draw_player(screen, pos, player_class, SPRITE_PALETTE, SPRITE_CHARACTERS, TILE_WIDTH, TILE_HEIGHT, zoom):
    x, y, sx, sy = pos
    offset_x = (sx - 1) * (TILE_WIDTH // 6)
    offset_y = (sy - 1) * (TILE_HEIGHT // 6)
    sx_iso = int(((x - y) * (TILE_WIDTH // 2) + screen.get_width() // 2) * zoom + (1-zoom)*screen.get_width()//2 + TILE_WIDTH//2*zoom + offset_x)
    sy_iso = int(((x + y) * (TILE_HEIGHT // 2) + 50) * zoom + (1-zoom)*screen.get_height()//2 + TILE_HEIGHT//2*zoom + offset_y)
    if SPRITE_PALETTE and SPRITE_CHARACTERS:
        sprite = SPRITE_CHARACTERS.get(player_class.lower(), SPRITE_CHARACTERS["brute"])
        draw_sprite(screen, sprite, SPRITE_PALETTE, sx_iso-16, sy_iso-16, 4)
    else:
        pygame.draw.circle(screen, (255, 100, 100), (sx_iso, sy_iso), int(12*zoom))
