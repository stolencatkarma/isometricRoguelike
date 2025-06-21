import pygame
import json
from core.pathfinding import find_path

# Input handling and game state update

def handle_input(event, state, send_queue):
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
    return True

def handle_main_menu_input(event, state):
    if event.type == pygame.KEYDOWN:
        print(f"[DEBUG] Main menu input: {event.key}", flush=True)
        if event.key == pygame.K_RETURN:
            print("[DEBUG] Switching to character_select scene.", flush=True)
            state['scene'] = 'character_select'
        elif event.key == pygame.K_ESCAPE:
            print("[DEBUG] Escape pressed in main menu. Exiting.", flush=True)
            return False
    return True

def handle_character_select_input(event, state, send_queue):
    classes = ["Brute", "Scout", "Savant", "Vanguard"]
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
            msg = json.dumps({"type": "class_select", "class": state['selected_class']})
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
