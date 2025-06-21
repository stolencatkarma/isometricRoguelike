import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import asyncio
from core.network import start_server
from core.party import get_party_id
from core.classes import CLASSES, CLASS_MAIN_STAT
from shared.map import GameMap
from shared.maps_campaign import get_campaign_map, SUBTILES_PER_TILE, is_walkable_subtile
from shared.maps_city import get_city_map
from shared.maps_endgame import generate_endgame_map
import json
import uuid
import time

connected_clients = {}
player_states = {}
# Track player progress: {client_id: {act: int, zone: int}}
player_progress = {}
# Party system: {party_id: {"act": int, "zone": int, "members": set, "map": GameMap, "map_data": dict, "created": float, "invites": set, "kick_votes": dict}}
parties = {}
# Player XP/level: {client_id: {"level": int, "xp": int}}
player_xp = {}
# Monster system: {party_id: [ {"id": str, "pos": [x, y], "type": str, "hp": int, ...}, ... ]}
monsters = {}
# Player emotes: {client_id: {"type": str, "until": float}}
emotes = {}

# Add player HP tracking (for future use)
player_hp = {}
player_max_hp = {}

def get_party_id(act, zone, endgame_depth=None):
    if act > 3:
        return f"endgame_{endgame_depth or 1}"
    return f"act{act}_zone{zone}"

# Load campaign map for chapter 1 (index 0)
campaign_chapter = 1
campaign_zone = 1
campaign_map_data = get_campaign_map(campaign_chapter, campaign_zone)
if campaign_map_data:
    GAME_MAP = GameMap(campaign_map_data["width"], campaign_map_data["height"])
    GAME_MAP.grid = campaign_map_data["grid"]
else:
    GAME_MAP = GameMap(20, 20)  # fallback

XP_PER_LEVEL = 100  # Each level takes 100 XP (constant)
CAMPAIGN_TARGET_LEVEL = 100
CAMPAIGN_TOTAL_TIME_SEC = 3 * 60 * 60  # 3 hours
CAMPAIGN_ZONES = 30
XP_PER_ZONE = (XP_PER_LEVEL * CAMPAIGN_TARGET_LEVEL) // CAMPAIGN_ZONES  # XP per zone completion

# Ability score gain per level (example: +1 to main stat every 2 levels, +1 to others every 4 levels)
CLASS_MAIN_STAT = {
    "Brute": "Strength",
    "Scout": "Agility",
    "Savant": "Mind",
    "Vanguard": None  # Balanced
}

# Player city state: {client_id: bool}
player_in_city = {}
# City instance (shared for all)
CITY_INSTANCE = {
    "map": get_city_map(),
    "members": set()
}

async def handler(websocket, path):
    # Assign a unique ID to each client
    client_id = str(uuid.uuid4())
    connected_clients[client_id] = websocket
    # For demo: start all new players at act 1, zone 1
    player_progress[client_id] = {"act": 1, "zone": 1, "endgame_depth": None}
    player_xp[client_id] = {"level": 1, "xp": 0}
    # For demo: assign class randomly (replace with client selection later)
    import random
    class_name = random.choice(list(CLASSES.keys()))
    player_info[client_id] = {"class": class_name, "stats": dict(CLASSES[class_name])}
    act = player_progress[client_id]["act"]
    zone = player_progress[client_id]["zone"]
    endgame_depth = player_progress[client_id].get("endgame_depth")
    party_id = get_party_id(act, zone, endgame_depth)
    # Create or join party instance
    if party_id not in parties:
        if act > 3:
            # Endgame: generate procedural map
            depth = endgame_depth or 1
            map_data = generate_endgame_map(depth=depth)
            from shared.map import GameMap
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
        monsters[party_id] = []
        for i in range(10):
            while True:
                mx = random.randint(0, game_map.width-1)
                my = random.randint(0, game_map.height-1)
                if game_map.grid[my][mx] == 0:
                    break
            monsters[party_id].append({
                "id": str(uuid.uuid4()),
                "pos": [mx, my],
                "type": random.choice(["goblin", "skeleton", "slime"]),
                "hp": 10
            })
    parties[party_id]["members"].add(client_id)
    # Find a random floor subtile for spawn
    game_map = parties[party_id]["map"]
    for y in range(game_map.height):
        for x in range(game_map.width):
            if game_map.grid[y][x] == 0:
                player_states[client_id] = {"pos": [x, y, 1, 1]}  # center subtile
                break
        if client_id in player_states:
            break
    print(f"Client {client_id} joined party {party_id} (Act {act} Zone {zone}).")
    try:
        # Send a JSON welcome message
        welcome_msg = json.dumps({
            "type": "welcome",
            "sender": "server",
            "payload": {
                "client_id": client_id,
                "map": parties[party_id]["map_data"],
                "act": act,
                "zone": zone,
                "boss": parties[party_id]["map_data"].get("boss")
            }
        })
        await websocket.send(welcome_msg)
        async for message in websocket:
            try:
                data = json.loads(message)
                if "sender" not in data:
                    data["sender"] = client_id
                # Handle class selection
                if data.get("type") == "class_select":
                    chosen = data["payload"].get("class")
                    if chosen in CLASSES:
                        player_info[client_id]["class"] = chosen
                        player_info[client_id]["stats"] = dict(CLASSES[chosen])
                # Handle move requests (city or campaign)
                if data.get("type") == "move":
                    pos = player_states[client_id]["pos"]
                    dx = data["payload"].get("dx", 0)
                    dy = data["payload"].get("dy", 0)
                    dsx = data["payload"].get("dsx", 0)
                    dsy = data["payload"].get("dsy", 0)
                    if player_in_city[client_id]:
                        city_map = CITY_INSTANCE["map"]
                        new_x = max(0, min(city_map["width"]-1, pos[0] + dx))
                        new_y = max(0, min(city_map["height"]-1, pos[1] + dy))
                        new_sx = max(0, min(SUBTILES_PER_TILE-1, pos[2] + dsx))
                        new_sy = max(0, min(SUBTILES_PER_TILE-1, pos[3] + dsy))
                        if city_map["grid"][new_y][new_x] != 1 and is_walkable_subtile(city_map["grid"], new_x, new_y, new_sx, new_sy):
                            player_states[client_id]["pos"] = [new_x, new_y, new_sx, new_sy]
                    else:
                        game_map = parties[party_id]["map"]
                        new_x = max(0, min(game_map.width-1, pos[0] + dx))
                        new_y = max(0, min(game_map.height-1, pos[1] + dy))
                        new_sx = max(0, min(SUBTILES_PER_TILE-1, pos[2] + dsx))
                        new_sy = max(0, min(SUBTILES_PER_TILE-1, pos[3] + dsy))
                        if game_map.is_walkable(new_x, new_y) and is_walkable_subtile(game_map.grid, new_x, new_y, new_sx, new_sy):
                            player_states[client_id]["pos"] = [new_x, new_y, new_sx, new_sy]
                            # Check for exit
                            if game_map.is_exit(new_x, new_y):
                                print(f"Player {client_id} reached an exit!")
                                # Award XP for zone completion
                                player_xp[client_id]["xp"] += XP_PER_ZONE
                                # Level up if enough XP
                                while player_xp[client_id]["xp"] >= XP_PER_LEVEL:
                                    player_xp[client_id]["xp"] -= XP_PER_LEVEL
                                    player_xp[client_id]["level"] += 1
                                    # Stat gain on level up
                                    class_name = player_info[client_id]["class"]
                                    main_stat = CLASS_MAIN_STAT[class_name]
                                    for stat in ["Strength", "Agility", "Mind"]:
                                        if class_name == "Vanguard":
                                            player_info[client_id]["stats"][stat] += 1 if player_xp[client_id]["level"] % 3 == 0 else 0
                                        elif stat == main_stat:
                                            player_info[client_id]["stats"][stat] += 1 if player_xp[client_id]["level"] % 2 == 0 else 0
                                        else:
                                            player_info[client_id]["stats"][stat] += 1 if player_xp[client_id]["level"] % 4 == 0 else 0
                                # Progress to next zone or act
                                if act <= 3:
                                    if zone < 10:
                                        player_progress[client_id]["zone"] += 1
                                    else:
                                        player_progress[client_id]["act"] += 1
                                        player_progress[client_id]["zone"] = 1
                                else:
                                    # Endgame: go deeper
                                    if not player_progress[client_id]["endgame_depth"]:
                                        player_progress[client_id]["endgame_depth"] = 1
                                    player_progress[client_id]["endgame_depth"] += 1
                                # TODO: move party to next instance, respawn all
                    # Compute visible monsters for this player
                    def is_visible(monster_pos, player_pos, radius=5):
                        dx = monster_pos[0] - player_pos[0]
                        dy = monster_pos[1] - player_pos[1]
                        return dx*dx + dy*dy <= radius*radius
                    visible_monsters = [m for m in monsters.get(party_id, []) if is_visible(m["pos"], player_states[client_id]["pos"][:2])]
                    party_positions = [
                        {"id": pid, "pos": player_states[pid]["pos"]}
                        for pid in parties[party_id]["members"]
                        if pid in player_states and pid != client_id
                    ]
                    # Send updated state to this client
                    state_msg = json.dumps({
                        "type": "state",
                        "sender": "server",
                        "payload": {
                            "player": {
                                "id": client_id,
                                "pos": player_states[client_id]["pos"],
                                "level": player_xp[client_id]["level"],
                                "xp": player_xp[client_id]["xp"],
                                "class": player_info[client_id]["class"],
                                "stats": player_info[client_id]["stats"],
                                "hp": player_hp[client_id],
                                "max_hp": player_max_hp[client_id]
                            },
                            "map": None,
                            "monsters": visible_monsters,
                            "party_positions": party_positions
                        }
                    })
                    await websocket.send(state_msg)
                # Handle teleport to party member
                if data.get("type") == "teleport":
                    target_id = data["payload"].get("target_id")
                    if target_id in parties[party_id]["members"] and target_id in player_states:
                        player_states[client_id]["pos"] = player_states[target_id]["pos"][:]
                        tp_msg = json.dumps({
                            "type": "state",
                            "sender": "server",
                            "payload": {"player": {"id": client_id, "pos": player_states[client_id]["pos"]}, "map": None, "teleported": True}
                        })
                        await websocket.send(tp_msg)
                # Handle party invite
                if data.get("type") == "party_invite":
                    invitee = data["payload"].get("invitee_id")
                    if invitee and invitee not in parties[party_id]["members"]:
                        parties[party_id]["invites"].add(invitee)
                        invite_msg = json.dumps({
                            "type": "party_invite",
                            "sender": client_id,
                            "payload": {"party_id": party_id}
                        })
                        if invitee in connected_clients:
                            await connected_clients[invitee].send(invite_msg)
                # Handle party join (by invite)
                if data.get("type") == "party_join":
                    joiner = client_id
                    join_party_id = data["payload"].get("party_id")
                    if join_party_id in parties and joiner in parties[join_party_id]["invites"]:
                        parties[join_party_id]["members"].add(joiner)
                        parties[join_party_id]["invites"].discard(joiner)
                        # Move player to party's act/zone
                        player_progress[joiner]["act"] = parties[join_party_id]["act"]
                        player_progress[joiner]["zone"] = parties[join_party_id]["zone"]
                        # Respawn on party map
                        game_map = parties[join_party_id]["map"]
                        for y in range(game_map.height):
                            for x in range(game_map.width):
                                if game_map.grid[y][x] == 0:
                                    player_states[joiner] = {"pos": [x, y, 1, 1]}  # center subtile
                                    break
                            if joiner in player_states:
                                break
                        # Notify party
                        join_msg = json.dumps({
                            "type": "party_joined",
                            "sender": joiner,
                            "payload": {"party_id": join_party_id}
                        })
                        for other_id in parties[join_party_id]["members"]:
                            if other_id in connected_clients:
                                await connected_clients[other_id].send(join_msg)
                # Handle party info request
                if data.get("type") == "party_info":
                    members = list(parties[party_id]["members"])
                    info_msg = json.dumps({
                        "type": "party_info",
                        "sender": "server",
                        "payload": {
                            "party_id": party_id,
                            "members": members,
                            "invites": list(parties[party_id]["invites"])
                        }
                    })
                    await websocket.send(info_msg)
                # Handle party chat
                if data.get("type") == "party_chat":
                    chat_msg = json.dumps({
                        "type": "party_chat",
                        "sender": client_id,
                        "payload": data["payload"]
                    })
                    for other_id in parties[party_id]["members"]:
                        if other_id in connected_clients:
                            await connected_clients[other_id].send(chat_msg)
                # Handle vote-kick
                if data.get("type") == "party_kick_vote":
                    target_id = data["payload"].get("target_id")
                    now = time.time()
                    if target_id in parties[party_id]["members"] and target_id != client_id:
                        votes = parties[party_id]["kick_votes"].setdefault(target_id, {})
                        # Only allow one vote per 15min per voter
                        if client_id not in votes or now - votes[client_id] > 900:
                            votes[client_id] = now
                            # If >50% of party votes, kick
                            if len(votes) > len(parties[party_id]["members"]) // 2:
                                parties[party_id]["members"].discard(target_id)
                                if target_id in connected_clients:
                                    kick_msg = json.dumps({
                                        "type": "party_kicked",
                                        "sender": "server",
                                        "payload": {"party_id": party_id, "target_id": target_id}
                                    })
                                    await connected_clients[target_id].send(kick_msg)
                                # Notify others
                                for other_id in parties[party_id]["members"]:
                                    if other_id in connected_clients:
                                        await connected_clients[other_id].send(kick_msg)
                # Handle emote action
                if data.get("type") == "emote":
                    emote_type = data["payload"].get("emote")
                    duration = 2.0  # seconds
                    emotes[client_id] = {"type": emote_type, "until": time.time() + duration}
                    # Broadcast to party
                    emote_msg = json.dumps({
                        "type": "emote",
                        "sender": client_id,
                        "payload": {"emote": emote_type, "duration": duration}
                    })
                    for other_id in parties[party_id]["members"]:
                        if other_id in connected_clients:
                            await connected_clients[other_id].send(emote_msg)
                # Relay chat/join messages only to players in the same party
                relay_types = {"chat", "join"}
                if data.get("type") in relay_types:
                    for other_id in parties[party_id]["members"]:
                        if other_id != client_id and other_id in connected_clients:
                            relay_msg = json.dumps(data)
                            await connected_clients[other_id].send(relay_msg)
                # Handle attack requests
                if data.get("type") == "attack":
                    target_id = data["payload"].get("target_id")
                    # Find monster in party
                    for m in monsters.get(party_id, []):
                        if m["id"] == target_id:
                            # Check if in range (1 tile for now)
                            px, py, psx, psy = player_states[client_id]["pos"]
                            mx, my = m["pos"]
                            if abs(mx - px) <= 1 and abs(my - py) <= 1:
                                dmg = 3  # Example: flat damage
                                m["hp"] -= dmg
                                # Send damage message to all party members
                                dmg_msg = json.dumps({
                                    "type": "damage",
                                    "payload": {"target_id": m["id"], "amount": dmg, "pos": [mx, my, 1, 1]}
                                })
                                for pid in parties[party_id]["members"]:
                                    if pid in connected_clients:
                                        await connected_clients[pid].send(dmg_msg)
                                # If monster dies, remove it
                                if m["hp"] <= 0:
                                    monsters[party_id].remove(m)
                            break
            except json.JSONDecodeError:
                print(f"Invalid JSON from {client_id}: {message}")
    except websockets.ConnectionClosed:
        print(f"Client {client_id} disconnected.")
    finally:
        del connected_clients[client_id]
        del player_states[client_id]
        del player_progress[client_id]
        del player_xp[client_id]
        del player_info[client_id]
        parties[party_id]["members"].discard(client_id)
        # Clean up empty party and expired zones
        now = time.time()
        expired = [pid for pid, p in parties.items() if not p["members"] or (now - p["created"] > 600)]
        for pid in expired:
            del parties[pid]

async def main():
    print("Server starting on ws://localhost:8765 ...")
    async with start_server(handler):
        await asyncio.Future()  # run forever

if __name__ == "__main__":
    asyncio.run(main())
