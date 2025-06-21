import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import asyncio
import pygame
from core.sprites import load_sprites
from core.network import network_loop
from core.pathfinding import find_path
from core.game import draw_game

async def main():
    # --- State and asset setup ---
    state = {
        'player_pos': [5, 5, 1, 1],
        'player_class': None,
        'map_grid': [],
        'map_width': 0,
        'map_height': 0,
        'zoom': 1.0,
        'in_city': False,
        # ...add more state as needed...
    }
    assets = {
        'TILE_WIDTH': 64,
        'TILE_HEIGHT': 32,
    }
    pygame.init()
    SPRITE_PATH = os.path.join(os.path.dirname(__file__), '../assets/sprites_palette.json')
    palette, tiles, chars, monsters, boss = load_sprites(SPRITE_PATH)
    assets['SPRITE_PALETTE'] = palette
    assets['SPRITE_TILES'] = tiles
    assets['SPRITE_CHARACTERS'] = chars
    assets['SPRITE_MONSTERS'] = monsters
    assets['SPRITE_BOSS'] = boss
    screen = pygame.display.set_mode((800, 600))
    pygame.display.set_caption("Isometric Roguelike Client")
    clock = pygame.time.Clock()
    send_queue = asyncio.Queue()
    recv_queue = asyncio.Queue()
    uri = "ws://localhost:8765"

    # Start networking in background
    asyncio.create_task(network_loop(uri, send_queue, recv_queue, state))

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            # ...handle input, update state, send network messages...
        # ...handle pathfinding, auto-attack, etc...
        screen.fill((30, 30, 30))
        draw_game(screen, state, assets)
        pygame.display.flip()
        clock.tick(30)
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    asyncio.run(main())
