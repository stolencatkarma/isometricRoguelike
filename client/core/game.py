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

def draw_main_menu(screen):
    screen.fill((20, 20, 40))
    font = pygame.font.SysFont(None, 48, bold=True)
    title = font.render("Isometric Roguelike", True, (255,255,0))
    screen.blit(title, (screen.get_width()//2 - title.get_width()//2, 120))
    font2 = pygame.font.SysFont(None, 36)
    play = font2.render("[ENTER] Play", True, (0,255,0))
    quit = font2.render("[ESC] Quit", True, (255,0,0))
    screen.blit(play, (screen.get_width()//2 - play.get_width()//2, 250))
    screen.blit(quit, (screen.get_width()//2 - quit.get_width()//2, 300))

def draw_character_select(screen, selected_class):
    screen.fill((30, 30, 60))
    font = pygame.font.SysFont(None, 40, bold=True)
    label = font.render("Select Your Class", True, (255,255,255))
    screen.blit(label, (screen.get_width()//2 - label.get_width()//2, 80))
    classes = ["Brute", "Scout", "Savant", "Vanguard"]
    font2 = pygame.font.SysFont(None, 32)
    for i, c in enumerate(classes):
        color = (255,255,0) if c == selected_class else (200,200,200)
        text = font2.render(f"{i+1}. {c}", True, color)
        screen.blit(text, (screen.get_width()//2 - text.get_width()//2, 160 + i*50))
    info = font2.render("[1-4] Select, [ENTER] Confirm", True, (0,255,255))
    screen.blit(info, (screen.get_width()//2 - info.get_width()//2, 400))
