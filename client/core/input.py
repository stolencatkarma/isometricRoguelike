import pygame
import json
from core.pathfinding import find_path

# Input handling and game state update

def handle_input(event, state, send_queue):
    import math
    import pygame
    if event.type == pygame.QUIT:
        print("[DEBUG] Quit event received.", flush=True)
        return False
    # Example: handle movement keys
    if event.type == pygame.KEYDOWN:
        print(f"[DEBUG] Keydown: {event.key}, scene: {state.get('scene')}", flush=True)
        if event.key == pygame.K_UP:
            # Example: move up
            state['player_pos'][1] = max(0, state['player_pos'][1] - 1)
            # Send move to server (stub)
            # await send_queue.put(json.dumps(...))
        # ...add more input handling...
    # Handle mouse click for map movement
    if event.type == pygame.MOUSEBUTTONDOWN and state.get('scene') == 'game':
        mx, my = event.pos
        TILE_WIDTH = state.get('TILE_WIDTH', 64)
        TILE_HEIGHT = state.get('TILE_HEIGHT', 32)
        zoom = state.get('zoom', 1.0)
        sw, sh = 800, 600  # Default window size
        if 'map_width' in state and 'map_height' in state:
            sw = sw
            sh = sh
        mx_centered = (mx - sw//2) / zoom - (1-zoom)*sw//2
        my_centered = (my - 50) / zoom - (1-zoom)*sh//2
        x = int((mx_centered / (TILE_WIDTH//2) + my_centered / (TILE_HEIGHT//2)) / 2)
        y = int((my_centered / (TILE_HEIGHT//2) - mx_centered / (TILE_WIDTH//2)) / 2)
        x = max(0, min(state.get('map_width', 0)-1, x))
        y = max(0, min(state.get('map_height', 0)-1, y))
        print(f"[DEBUG] Map click at screen=({mx},{my}) -> map=({x},{y})", flush=True)
        grid = state.get('map_grid', [])
        if grid and 0 <= y < len(grid) and 0 <= x < len(grid[0]) and grid[y][x] in (0, 2):
            # Pathfind to clicked tile (center subtile)
            from core.pathfinding import find_path
            start = tuple(state['player_pos'])
            goal = (x, y, 1, 1)
            path = find_path(grid, start, goal)
            if path:
                state['move_path'] = path[1:]  # Exclude current position
                print(f"[DEBUG] Path found: {path}", flush=True)
            else:
                print(f"[DEBUG] No path found to ({x},{y})", flush=True)
    return True

def handle_main_menu_input(event, state):
    if event.type == pygame.KEYDOWN:
        print(f"[DEBUG] Main menu input: {event.key}", flush=True)
        if event.key == pygame.K_RETURN:
            if state.get('network_ready'):
                print("[DEBUG] Switching to character_select scene.", flush=True)
                state['scene'] = 'character_select'
            else:
                print("[DEBUG] Network not ready, please wait...", flush=True)
        elif event.key == pygame.K_ESCAPE:
            print("[DEBUG] Escape pressed in main menu. Exiting.", flush=True)
            return False
    return True

def handle_character_select_input(event, state, send_queue):
    classes = ["Brute", "Scout", "Savant", "Vanguard"]
    if not state.get('network_ready'):
        print("[DEBUG] Network not ready, cannot select class yet.", flush=True)
        return True
    if event.type == pygame.KEYDOWN:
        print(f"[DEBUG] Character select input: {event.key}", flush=True)
        if event.key in [pygame.K_1, pygame.K_KP1]:
            state['selected_class'] = classes[0]
            print(f"[DEBUG] Selected class: {classes[0]}", flush=True)
        elif event.key in [pygame.K_2, pygame.K_KP2]:
            state['selected_class'] = classes[1]
            print(f"[DEBUG] Selected class: {classes[1]}", flush=True)
        elif event.key in [pygame.K_3, pygame.K_KP3]:
            state['selected_class'] = classes[2]
            print(f"[DEBUG] Selected class: {classes[2]}", flush=True)
        elif event.key in [pygame.K_4, pygame.K_KP4]:
            state['selected_class'] = classes[3]
            print(f"[DEBUG] Selected class: {classes[3]}", flush=True)
        elif event.key == pygame.K_RETURN and state.get('selected_class'):
            # Send class selection to server (if connected)
            import json
            msg = json.dumps({"type": "class_select", "payload": {"class": state['selected_class']}})
            print(f"[DEBUG] Sending class_select to server: {msg}", flush=True)
            if send_queue:
                send_queue.put_nowait(msg)
            print("[DEBUG] Switching to game scene.", flush=True)
            state['scene'] = 'game'  # Switch to game scene after selection
        elif event.key == pygame.K_ESCAPE:
            print("[DEBUG] Escape pressed in character select. Returning to main menu.", flush=True)
            state['scene'] = 'main_menu'
    return True

# Add more input/UI logic as needed
