import asyncio
import websockets
import json

async def network_loop(uri, send_queue, recv_queue, state):
    while True:
        try:
            print(f"[DEBUG] Attempting to connect to server at {uri}...", flush=True)
            async with websockets.connect(uri) as websocket:
                print("[DEBUG] Connected to server.", flush=True)
                state['network_ready'] = True
                # Main message loop
                while True:
                    # Send any queued messages
                    try:
                        msg = send_queue.get_nowait()
                        await websocket.send(msg)
                        print(f"[DEBUG] Sent to server: {msg}", flush=True)
                    except asyncio.QueueEmpty:
                        pass
                    # Receive and process messages
                    try:
                        message = await asyncio.wait_for(websocket.recv(), timeout=0.05)
                        print(f"[DEBUG] Received from server: {message}", flush=True)
                        data = json.loads(message)
                        if data.get('type') == 'welcome':
                            payload = data['payload']
                            state['player_id'] = payload['client_id']
                            map_data = payload.get('map')
                            if map_data:
                                state['map_grid'] = map_data['grid']
                                state['map_width'] = map_data['width']
                                state['map_height'] = map_data['height']
                                state['in_city'] = map_data.get('city', False)
                            else:
                                print("[DEBUG] No map data in welcome message!", flush=True)
                            player_info = payload.get('player_info')
                            if player_info:
                                state['player_class'] = player_info.get('class')
                                print(f"[DEBUG] Player class set from server: {state['player_class']}", flush=True)
                            player_pos = payload.get('player_pos')
                            if player_pos:
                                state['player_pos'] = player_pos
                                print(f"[DEBUG] Player position set from server: {state['player_pos']}", flush=True)
                            # Reset other_players
                            state['other_players'] = {}
                        elif data.get('type') == 'move':
                            # Server authoritative move: update player position
                            payload = data.get('payload', {})
                            pos = payload.get('pos')
                            move_client_id = payload.get('client_id')
                            if pos and move_client_id:
                                if move_client_id == state.get('player_id'):
                                    state['player_pos'] = pos
                                    print(f"[DEBUG] Server move: player_pos set to {pos}", flush=True)
                                    # Remove the step from move_path if it matches
                                    if 'move_path' in state and state['move_path']:
                                        if tuple(pos) == tuple(state['move_path'][0]):
                                            state['move_path'] = state['move_path'][1:]
                                            if not state['move_path']:
                                                del state['move_path']
                                    state['move_waiting'] = False
                                else:
                                    # Update other player's position
                                    if 'other_players' not in state:
                                        state['other_players'] = {}
                                    if move_client_id not in state['other_players']:
                                        state['other_players'][move_client_id] = {"pos": pos, "class": "Brute"}
                                    else:
                                        state['other_players'][move_client_id]['pos'] = pos
                                    print(f"[DEBUG] Other player {move_client_id} moved to {pos}", flush=True)
                        # ...handle other message types as needed...
                    except asyncio.TimeoutError:
                        await asyncio.sleep(0.01)
                        continue
        except Exception as e:
            print(f"[DEBUG] Network error: {e}", flush=True)
            state['network_ready'] = False
            await asyncio.sleep(0.5)
