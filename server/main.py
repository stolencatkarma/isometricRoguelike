# Entry point for the Python server
# Uses websockets for multiplayer
import asyncio
import websockets
import uuid
import json
import time
from shared.map import GameMap
from shared.maps_campaign import get_campaign_map

connected_clients = {}
player_states = {}
# Track player progress: {client_id: {act: int, zone: int}}
player_progress = {}
# Party system: {party_id: {"act": int, "zone": int, "members": set, "map": GameMap, "map_data": dict, "created": float, "invites": set, "kick_votes": dict}}
parties = {}
# Player XP/level: {client_id: {"level": int, "xp": int}}
player_xp = {}
# Monster system: {party_id: [ {"id": str, "pos": [x, y], "type": str, ...}, ... ]}
monsters = {}

# Class definitions
CLASSES = {
    "Brute": {"Strength": 10, "Agility": 5, "Mind": 3},
    "Scout": {"Strength": 4, "Agility": 10, "Mind": 4},
    "Savant": {"Strength": 3, "Agility": 5, "Mind": 10},
    "Vanguard": {"Strength": 7, "Agility": 7, "Mind": 7},  # Balanced
}

# Player info: {client_id: {"class": str, "stats": {"Strength": int, "Agility": int, "Mind": int}}}
player_info = {}

def get_party_id(act, zone):
    return f"act{act}_zone{zone}"

# Load campaign map for chapter 1 (index 0)
campaign_chapter = 0
campaign_map_data = get_campaign_map(campaign_chapter)
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

async def handler(websocket, path):
    # Assign a unique ID to each client
    client_id = str(uuid.uuid4())
    connected_clients[client_id] = websocket
    # For demo: start all new players at act 1, zone 1
    player_progress[client_id] = {"act": 1, "zone": 1}
    player_xp[client_id] = {"level": 1, "xp": 0}
    # For demo: assign class randomly (replace with client selection later)
    import random
    class_name = random.choice(list(CLASSES.keys()))
    player_info[client_id] = {"class": class_name, "stats": dict(CLASSES[class_name])}
    act = player_progress[client_id]["act"]
    zone = player_progress[client_id]["zone"]
    party_id = get_party_id(act, zone)
    # Create or join party instance
    if party_id not in parties:
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
            "members": set(),
            "map": game_map,
            "map_data": map_data,
            "created": time.time(),
            "invites": set(),
            "kick_votes": {}  # {target_id: {voter_id: timestamp}}
        }
        # Spawn monsters for this party instance
        import random
        monsters[party_id] = []
        for i in range(10):  # Example: 10 monsters per map
            while True:
                mx = random.randint(0, game_map.width-1)
                my = random.randint(0, game_map.height-1)
                if game_map.grid[my][mx] == 0:
                    break
            monsters[party_id].append({
                "id": str(uuid.uuid4()),
                "pos": [mx, my],
                "type": random.choice(["goblin", "skeleton", "slime"])
            })
    parties[party_id]["members"].add(client_id)
    # Find a random floor tile for spawn
    game_map = parties[party_id]["map"]
    for y in range(game_map.height):
        for x in range(game_map.width):
            if game_map.grid[y][x] == 0:
                player_states[client_id] = {"pos": [x, y]}
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
                # Handle move requests
                if data.get("type") == "move":
                    dx = data["payload"].get("dx", 0)
                    dy = data["payload"].get("dy", 0)
                    pos = player_states[client_id]["pos"]
                    new_x = max(0, min(game_map.width-1, pos[0] + dx))
                    new_y = max(0, min(game_map.height-1, pos[1] + dy))
                    # Only move if walkable
                    if game_map.is_walkable(new_x, new_y):
                        player_states[client_id]["pos"] = [new_x, new_y]
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
                            if zone < 10:
                                player_progress[client_id]["zone"] += 1
                            else:
                                player_progress[client_id]["act"] += 1
                                player_progress[client_id]["zone"] = 1
                            # TODO: move party to next instance, respawn all
                    # Compute visible monsters for this player
                    def is_visible(monster_pos, player_pos, radius=5):
                        dx = monster_pos[0] - player_pos[0]
                        dy = monster_pos[1] - player_pos[1]
                        return dx*dx + dy*dy <= radius*radius
                    visible_monsters = [m for m in monsters.get(party_id, []) if is_visible(m["pos"], player_states[client_id]["pos"])]
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
                                "stats": player_info[client_id]["stats"]
                            },
                            "map": None,
                            "monsters": visible_monsters
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
                                    player_states[joiner] = {"pos": [x, y]}
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
                # Relay chat/join messages only to players in the same party
                relay_types = {"chat", "join"}
                if data.get("type") in relay_types:
                    for other_id in parties[party_id]["members"]:
                        if other_id != client_id and other_id in connected_clients:
                            relay_msg = json.dumps(data)
                            await connected_clients[other_id].send(relay_msg)
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
    async with websockets.serve(handler, "localhost", 8765):
        await asyncio.Future()  # run forever

if __name__ == "__main__":
    asyncio.run(main())
