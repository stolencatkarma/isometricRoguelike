import pygame
import json
from core.pathfinding import find_path

# Game update logic (pathfinding, auto-attack, etc.)
def update_game(state, send_queue):
    # Only move if we have a path and are waiting for server approval
    if 'move_path' in state and state['move_path'] and not state.get('move_waiting'):
        # Send the next step to the server, but do not update local position yet
        next_pos = state['move_path'][0]
        move_msg = json.dumps({
            "type": "move",
            "payload": {"pos": list(next_pos)}
        })
        if send_queue:
            send_queue.put_nowait(move_msg)
        state['move_waiting'] = True  # Wait for server to confirm
    # ...add more update logic as needed...
