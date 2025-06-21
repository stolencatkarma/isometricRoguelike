import asyncio
import websockets
import json

async def network_loop(uri, send_queue, recv_queue, state):
    async with websockets.connect(uri) as websocket:
        print("[DEBUG] Connected to server.", flush=True)
        welcome = await websocket.recv()
        print(f"[DEBUG] Received from server: {welcome}", flush=True)
        welcome_data = json.loads(welcome)
        state['player_id'] = welcome_data['payload']['client_id']
        map_data = welcome_data['payload'].get('map')
        if map_data:
            print(f"[DEBUG] Map data received: width={map_data.get('width')}, height={map_data.get('height')}", flush=True)
            state['map_grid'] = map_data['grid']
            state['map_width'] = map_data['width']
            state['map_height'] = map_data['height']
            state['in_city'] = map_data.get('city', False)
        else:
            print("[DEBUG] No map data in welcome message!", flush=True)
        # ...additional logic for class selection, join, party info, sender/receiver...
        # This is a stub; move the rest of the networking logic here from main.py
