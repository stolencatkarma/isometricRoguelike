import pygame
from .render import draw_isometric_grid, draw_player

def draw_game(screen, state, assets):
    draw_isometric_grid(
        screen,
        state['map_grid'],
        state['map_height'],
        state['map_width'],
        assets['SPRITE_PALETTE'],
        assets['SPRITE_TILES'],
        assets['TILE_WIDTH'],
        assets['TILE_HEIGHT'],
        state['zoom']
    )
    draw_player(
        screen,
        state['player_pos'],
        state['player_class'],
        assets['SPRITE_PALETTE'],
        assets['SPRITE_CHARACTERS'],
        assets['TILE_WIDTH'],
        assets['TILE_HEIGHT'],
        state['zoom']
    )
    # ...add more draw calls for monsters, UI, etc...
