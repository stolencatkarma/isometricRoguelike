import asyncio
import websockets
import uuid
import json
import time
from shared.map import GameMap
from shared.maps_campaign import get_campaign_map, SUBTILES_PER_TILE, is_walkable_subtile
from shared.maps_city import get_city_map
from shared.maps_endgame import generate_endgame_map
from .party import get_party_id
from .classes import CLASSES, CLASS_MAIN_STAT

def get_or_create_party(state, act, zone, endgame_depth=None):
    party_id = get_party_id(act, zone, endgame_depth)
    parties = state['parties']
    if party_id not in parties:
        if act > 3:
            depth = endgame_depth or 1
            map_data = generate_endgame_map(depth=depth)
            game_map = GameMap(map_data["width"], map_data["height"])
            game_map.grid = map_data["grid"]
        else:
            map_data = get_campaign_map(act, zone)
            if map_data:
                game_map = GameMap(map_data["width"], map_data["height"])
                game_map.grid = map_data["grid"]
            else:
                game_map = GameMap(20, 20)
                map_data = game_map.to_dict()
        parties[party_id] = {
            "act": act,
            "zone": zone,
            "endgame_depth": endgame_depth,
            "members": set(),
            "map": game_map,
            "map_data": map_data,
            "created": time.time(),
            "invites": set(),
            "kick_votes": {}
        }
        # Spawn monsters for this party instance
        import random
        state['monsters'][party_id] = []
        for i in range(10):
            while True:
                mx = random.randint(0, game_map.width-1)
                my = random.randint(0, game_map.height-1)
                if game_map.grid[my][mx] == 0:
                    break
            state['monsters'][party_id].append({
                "id": str(uuid.uuid4()),
                "pos": [mx, my],
                "type": random.choice(["goblin", "skeleton", "slime"]),
                "hp": 10
            })
    return party_id

async def handler(websocket, path, state):
    # Assign a unique ID to each client
    client_id = str(uuid.uuid4())
    state['connected_clients'][client_id] = websocket
    # For demo: start all new players at act 1, zone 1
    state['player_progress'][client_id] = {"act": 1, "zone": 1, "endgame_depth": None}
    state['player_xp'][client_id] = {"level": 1, "xp": 0}
    # Do NOT assign class yet; wait for class_select from client
    print(f"Client {client_id} connected, waiting for class selection.")
    party_id = None
    try:
        # Wait for class_select message before proceeding
        while True:
            message = await websocket.recv()
            try:
                data = json.loads(message)
                if data.get("type") == "class_select":
                    class_name = data.get("class")
                    if class_name not in CLASSES:
                        await websocket.send(json.dumps({
                            "type": "error", "payload": {"msg": "Invalid class."}
                        }))
                        continue
                    state['player_info'][client_id] = {"class": class_name, "stats": dict(CLASSES[class_name])}
                    break
                else:
                    await websocket.send(json.dumps({
                        "type": "error", "payload": {"msg": "Please select a class first."}
                    }))
            except json.JSONDecodeError:
                print(f"Invalid JSON from {client_id}: {message}")
        # Now assign party and spawn
        act = state['player_progress'][client_id]["act"]
        zone = state['player_progress'][client_id]["zone"]
        endgame_depth = state['player_progress'][client_id].get("endgame_depth")
        party_id = get_or_create_party(state, act, zone, endgame_depth)
        state['parties'][party_id]["members"].add(client_id)
        # Find a random floor subtile for spawn
        game_map = state['parties'][party_id]["map"]
        for y in range(game_map.height):
            for x in range(game_map.width):
                if game_map.grid[y][x] == 0:
                    state['player_states'][client_id] = {"pos": [x, y, 1, 1]}
                    break
            if client_id in state['player_states']:
                break
        print(f"Client {client_id} joined party {party_id} (Act {act} Zone {zone}).")
        # Send a JSON welcome message
        welcome_msg = json.dumps({
            "type": "welcome",
            "sender": "server",
            "payload": {
                "client_id": client_id,
                "map": state['parties'][party_id]["map_data"],
                "act": act,
                "zone": zone,
                "boss": state['parties'][party_id]["map_data"].get("boss")
            }
        })
        await websocket.send(welcome_msg)
        async for message in websocket:
            try:
                data = json.loads(message)
                if "sender" not in data:
                    data["sender"] = client_id
                # ...existing message handling logic (move, teleport, party, emote, attack, etc.)...
            except json.JSONDecodeError:
                print(f"Invalid JSON from {client_id}: {message}")
    except websockets.ConnectionClosed:
        print(f"Client {client_id} disconnected.")
    finally:
        del state['connected_clients'][client_id]
        del state['player_states'][client_id]
        del state['player_progress'][client_id]
        del state['player_xp'][client_id]
        del state['player_info'][client_id]
        if party_id and party_id in state['parties']:
            state['parties'][party_id]["members"].discard(client_id)
        # Clean up empty party and expired zones
        now = time.time()
        expired = [pid for pid, p in state['parties'].items() if not p["members"] or (now - p["created"] > 600)]
        for pid in expired:
            del state['parties'][pid]

async def start_server(state):
    print("Server starting on ws://localhost:8765 ...")
    async with websockets.serve(lambda ws, p: handler(ws, p, state), "localhost", 8765):
        await asyncio.Future()  # run forever
