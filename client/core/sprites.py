import pygame
import json
import os

def load_sprites(SPRITE_PATH):
    with open(SPRITE_PATH, 'r') as f:
        data = json.load(f)
    palette = [
        data["palette"]["floor"],
        data["palette"]["wall"],
        data["palette"]["exit"],
        data["palette"]["waypoint"],
        data["palette"]["event"],
        data["palette"]["boss"],
        data["palette"]["player_brute"],
        data["palette"]["player_scout"],
        data["palette"]["player_savant"],
        data["palette"]["player_vanguard"],
        data["palette"]["monster_goblin"],
        data["palette"]["monster_skeleton"],
        data["palette"]["monster_slime"],
        data["palette"]["boss_final"]
    ]
    return palette, data["tiles"], data["characters"], data["monsters"], data["boss"]

def draw_sprite(screen, sprite, palette, x, y, scale):
    for row in range(len(sprite)):
        for col in range(len(sprite[row])):
            color_idx = sprite[row][col]
            if color_idx == 0:
                continue  # transparent
            color = palette[color_idx]
            rect = pygame.Rect(x + col*scale, y + row*scale, scale, scale)
            pygame.draw.rect(screen, color, rect)
