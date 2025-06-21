# Entry point for the Python client
# Uses pygame for isometric rendering and websockets for networking
import asyncio
import websockets
import json
import pygame
import sys
import threading
import math
import heapq
from shared.maps_campaign import SUBTILES_PER_TILE, is_walkable_subtile

# Isometric tile settings
TILE_WIDTH = 64
TILE_HEIGHT = 32
MAP_WIDTH = 10
MAP_HEIGHT = 10

# Colors
BG_COLOR = (30, 30, 30)
FLOOR_COLOR = (100, 200, 255)
WALL_COLOR = (60, 60, 60)
EXIT_COLOR = (255, 220, 80)
PLAYER_COLOR = (255, 100, 100)

# Dummy player state (updated only from server)
player_pos = [5, 5, 1, 1]  # (x, y, sx, sy)

# Map data from server
map_data = None
map_grid = []
map_width = 0
map_height = 0

# Player info
player_class = None
player_stats = {"Strength": 0, "Agility": 0, "Mind": 0}
player_level = 1
player_xp = 0
player_id = None
# Add player HP state
player_hp = 20
player_max_hp = 20

# Party info
party_members = []
party_invites = []
party_id = None
invite_input = ""
show_party_panel = False

# Monster state from server
visible_monsters = []
# Party member positions from server
party_positions = []
# Zoom level
zoom = 1.0
ZOOM_MIN = 0.5
ZOOM_MAX = 2.5
ZOOM_STEP = 0.1

# Emote state for party members: {id: {"type": str, "until": float}}
party_emotes = {}
# Emote definitions
EMOTE_TYPES = {
    "come_here": {"key": pygame.K_1, "label": "Come Here", "color": (255, 255, 0)},
    "wait": {"key": pygame.K_2, "label": "Wait", "color": (0, 255, 255)},
    "danger": {"key": pygame.K_3, "label": "Danger", "color": (255, 0, 0)},
    "ok": {"key": pygame.K_4, "label": "OK", "color": (0, 255, 0)},
    "thanks": {"key": pygame.K_5, "label": "Thanks", "color": (255, 128, 0)}
}

WAYPOINT_TILE = 2  # Use tile value 2 for waypoints (EXIT_COLOR)
CITY_MAP_NAME = "city"

# City state
in_city = False
CITY_MAP_WIDTH = 12
CITY_MAP_HEIGHT = 8
CITY_BG_COLOR = (80, 80, 120)
CITY_LABEL_COLOR = (255, 255, 0)
CITY_UI_COLOR = (0, 200, 255)

# Floating damage numbers: list of dicts {"pos": (x, y, sx, sy), "value": int, "timer": float, "dx": float}
floating_damage = []

async def network_loop(uri, send_queue, recv_queue):
    global map_data, map_grid, map_width, map_height, player_class, player_stats, player_level, player_xp, player_id, party_members, party_invites, party_id, in_city
    async with websockets.connect(uri) as websocket:
        welcome = await websocket.recv()
        welcome_data = json.loads(welcome)
        player_id = welcome_data["payload"]["client_id"]
        # Get map data from server
        map_data = welcome_data["payload"].get("map")
        if map_data:
            map_grid = map_data["grid"]
            map_width = map_data["width"]
            map_height = map_data["height"]
            in_city = map_data.get("city", False)
        # Class selection UI (console for now)
        if player_class is None:
            print("Select your class:")
            print("1. Brute  2. Scout  3. Savant  4. Vanguard")
            choice = input("Enter class number: ")
            class_map = {"1": "Brute", "2": "Scout", "3": "Savant", "4": "Vanguard"}
            chosen = class_map.get(choice, "Vanguard")
            player_class = chosen
            msg = json.dumps({
                "type": "class_select",
                "payload": {"class": chosen}
            })
            await websocket.send(msg)
        # Send join message
        join_msg = json.dumps({
            "type": "join",
            "sender": player_id,
            "payload": {"name": "Player"}
        })
        await websocket.send(join_msg)
        # Request party info after join
        info_msg = json.dumps({"type": "party_info"})
        await websocket.send(info_msg)
        # Start send/receive loop
        async def sender():
            while True:
                msg = await send_queue.get()
                await websocket.send(msg)
        async def receiver():
            global player_class, player_stats, player_level, player_xp, party_members, party_invites, party_id, map_data, map_grid, map_width, map_height, in_city
            while True:
                msg = await websocket.recv()
                await recv_queue.put(msg)
                # Parse state updates for player info
                try:
                    data = json.loads(msg)
                    if data.get("type") == "state":
                        player = data["payload"].get("player", {})
                        player_class = player.get("class", player_class)
                        player_stats = player.get("stats", player_stats)
                        player_level = player.get("level", player_level)
                        player_xp = player.get("xp", player_xp)
                        # Player HP
                        global player_hp, player_max_hp
                        player_hp = player.get("hp", 20)
                        player_max_hp = player.get("max_hp", 20)
                        # Map/city state
                        if "map" in data["payload"]:
                            map_data = data["payload"]["map"]
                            map_grid = map_data["grid"]
                            map_width = map_data["width"]
                            map_height = map_data["height"]
                            in_city = map_data.get("city", False)
                    elif data.get("type") == "party_info":
                        payload = data["payload"]
                        party_id = payload.get("party_id")
                        party_members = payload.get("members", [])
                        party_invites = payload.get("invites", [])
                    elif data.get("type") == "emote":
                        sender = data.get("sender")
                        emote_type = data["payload"].get("emote")
                        duration = data["payload"].get("duration", 2.0)
                        now = pygame.time.get_ticks() / 1000.0
                        party_emotes[sender] = {"type": emote_type, "until": now + duration}
                    elif data.get("type") == "damage":
                        # Expect payload: {"target_id": str, "amount": int, "pos": [x, y, sx, sy]}
                        payload = data["payload"]
                        floating_damage.append({
                            "pos": tuple(payload["pos"]),
                            "value": payload["amount"],
                            "timer": 0.0,
                            "dx": 0.5 - (pygame.time.get_ticks() % 1000) / 1000.0  # random left/right
                        })
                except Exception:
                    pass
        await asyncio.gather(sender(), receiver())

def draw_isometric_grid(screen):
    if not map_grid:
        return
    for y in range(map_height):
        for x in range(map_width):
            tile = map_grid[y][x]
            sx = int(((x - y) * (TILE_WIDTH // 2) + screen.get_width() // 2) * zoom + (1-zoom)*screen.get_width()//2)
            sy = int(((x + y) * (TILE_HEIGHT // 2) + 50) * zoom + (1-zoom)*screen.get_height()//2)
            points = [
                (sx, sy + int(TILE_HEIGHT//2 * zoom)),
                (sx + int(TILE_WIDTH//2 * zoom), sy),
                (sx + int(TILE_WIDTH * zoom), sy + int(TILE_HEIGHT//2 * zoom)),
                (sx + int(TILE_WIDTH//2 * zoom), sy + int(TILE_HEIGHT * zoom))
            ]
            color = FLOOR_COLOR if tile == 0 else WALL_COLOR if tile == 1 else EXIT_COLOR
            pygame.draw.polygon(screen, color, points, 0)
            pygame.draw.polygon(screen, (0,0,0), points, 1)

def draw_player(screen, pos):
    x, y, sx, sy = pos
    # Offset within tile for subtile
    offset_x = (sx - 1) * (TILE_WIDTH // 6)
    offset_y = (sy - 1) * (TILE_HEIGHT // 6)
    sx_iso = int(((x - y) * (TILE_WIDTH // 2) + screen.get_width() // 2) * zoom + (1-zoom)*screen.get_width()//2 + TILE_WIDTH//2*zoom + offset_x)
    sy_iso = int(((x + y) * (TILE_HEIGHT // 2) + 50) * zoom + (1-zoom)*screen.get_height()//2 + TILE_HEIGHT//2*zoom + offset_y)
    pygame.draw.circle(screen, PLAYER_COLOR, (sx_iso, sy_iso), int(12*zoom))

def draw_player_hp(screen, pos, hp, max_hp):
    x, y, sx, sy = pos
    offset_x = (sx - 1) * (TILE_WIDTH // 6)
    offset_y = (sy - 1) * (TILE_HEIGHT // 6)
    sx_iso = int(((x - y) * (TILE_WIDTH // 2) + screen.get_width() // 2) * zoom + (1-zoom)*screen.get_width()//2 + TILE_WIDTH//2*zoom + offset_x)
    sy_iso = int(((x + y) * (TILE_HEIGHT // 2) + 50) * zoom + (1-zoom)*screen.get_height()//2 + TILE_HEIGHT//2*zoom + offset_y)
    bar_w = int(TILE_WIDTH//2 * zoom)
    bar_x = sx_iso - bar_w//2
    bar_y = sy_iso + int(18*zoom)
    hp_w = int(bar_w * (hp / max_hp))
    pygame.draw.rect(screen, (0, 0, 0), (bar_x, bar_y, bar_w, 6))
    pygame.draw.rect(screen, (0, 200, 0), (bar_x, bar_y, hp_w, 6))

def draw_monsters(screen, monsters):
    for m in monsters:
        x, y = m["pos"]
        sx = int(((x - y) * (TILE_WIDTH // 2) + screen.get_width() // 2) * zoom + (1-zoom)*screen.get_width()//2)
        sy = int(((x + y) * (TILE_HEIGHT // 2) + 50) * zoom + (1-zoom)*screen.get_height()//2)
        color = (0,255,0) if m["type"]=="goblin" else (200,200,200) if m["type"]=="skeleton" else (0,255,255)
        pygame.draw.rect(screen, color, (sx + int(TILE_WIDTH//4*zoom), sy + int(TILE_HEIGHT//4*zoom), int(TILE_WIDTH//2*zoom), int(TILE_HEIGHT//2*zoom)))
        # Draw HP bar above monster
        if "hp" in m:
            max_hp = 10  # For now, hardcoded
            hp = max(0, min(m["hp"], max_hp))
            bar_w = int(TILE_WIDTH//2 * zoom)
            bar_x = sx + int(TILE_WIDTH//4*zoom)
            bar_y = sy + int(TILE_HEIGHT//4*zoom) - 10
            hp_w = int(bar_w * (hp / max_hp))
            pygame.draw.rect(screen, (60, 0, 0), (bar_x, bar_y, bar_w, 5))
            pygame.draw.rect(screen, (255, 0, 0), (bar_x, bar_y, hp_w, 5))

def draw_floating_damage(screen):
    now = pygame.time.get_ticks() / 1000.0
    for dmg in floating_damage:
        x, y, sx, sy = dmg["pos"]
        offset_x = (sx - 1) * (TILE_WIDTH // 6)
        offset_y = (sy - 1) * (TILE_HEIGHT // 6)
        sx_iso = int(((x - y) * (TILE_WIDTH // 2) + screen.get_width() // 2) * zoom + (1-zoom)*screen.get_width()//2 + TILE_WIDTH//2*zoom + offset_x + dmg["dx"]*dmg["timer"]*20)
        sy_iso = int(((x + y) * (TILE_HEIGHT // 2) + 50) * zoom + (1-zoom)*screen.get_height()//2 + TILE_HEIGHT//2*zoom - int(dmg["timer"]*30))
        alpha = max(0, 255 - int(dmg["timer"]*180))
        font = pygame.font.SysFont(None, 22, bold=True)
        text = font.render(str(dmg["value"]), True, (255, 64, 64))
        text.set_alpha(alpha)
        surf = pygame.Surface(text.get_size(), pygame.SRCALPHA)
        surf.blit(text, (0,0))
        screen.blit(surf, (sx_iso, sy_iso))

def is_on_waypoint():
    if not map_grid or not player_pos:
        return False
    x, y = player_pos
    if 0 <= y < len(map_grid) and 0 <= x < len(map_grid[0]):
        return map_grid[y][x] == WAYPOINT_TILE
    return False

def draw_ui(screen):
    font = pygame.font.SysFont(None, 24)
    lines = [
        f"Class: {player_class}",
        f"Level: {player_level}  XP: {player_xp}/100",
        f"Strength: {player_stats.get('Strength', 0)}",
        f"Agility: {player_stats.get('Agility', 0)}",
        f"Mind: {player_stats.get('Mind', 0)}"
    ]
    for i, line in enumerate(lines):
        text = font.render(line, True, (255,255,255))
        screen.blit(text, (10, 10 + i*22))
    # Show warp to city prompt if on waypoint
    if is_on_waypoint():
        text = font.render("[W] Warp to City", True, (255,255,0))
        screen.blit(text, (10, 130))

def draw_party_panel(screen):
    font = pygame.font.SysFont("Courier", 18, bold=True)
    panel_rect = pygame.Rect(600, 10, 190, 180)
    pygame.draw.rect(screen, (0,0,128), panel_rect)
    pygame.draw.rect(screen, (255,255,0), panel_rect, 2)
    y = 20
    screen.blit(font.render("Party Info", True, (255,255,0)), (610, y))
    y += 24
    screen.blit(font.render("Members:", True, (255,255,255)), (610, y))
    y += 20
    for m in party_members:
        screen.blit(font.render(m[:8], True, (0,255,0)), (620, y))
        y += 18
    y += 6
    screen.blit(font.render("Invites:", True, (255,255,255)), (610, y))
    y += 20
    for i in party_invites:
        screen.blit(font.render(i[:8], True, (255,128,0)), (620, y))
        y += 18
    # Invite input box
    pygame.draw.rect(screen, (0,0,0), (610, 160, 100, 20))
    pygame.draw.rect(screen, (255,255,0), (610, 160, 100, 20), 1)
    screen.blit(font.render(invite_input, True, (255,255,255)), (614, 162))
    screen.blit(font.render("[I]nvite", True, (255,255,0)), (720, 160))
    # Buttons
    screen.blit(font.render("[T]eleport", True, (255,255,0)), (610, 185))
    screen.blit(font.render("[K]ick", True, (255,255,0)), (720, 185))

def draw_party_markers(screen, player_pos, party_positions, zoom):
    width, height = screen.get_size()
    px, py, psx, psy = player_pos
    psx_iso = int(((px - py) * (TILE_WIDTH // 2) + width // 2) * zoom + (1-zoom)*width//2 + TILE_WIDTH//2*zoom + (psx-1)*(TILE_WIDTH//6))
    psy_iso = int(((px + py) * (TILE_HEIGHT // 2) + 50) * zoom + (1-zoom)*height//2 + TILE_HEIGHT//2*zoom + (psy-1)*(TILE_HEIGHT//6))
    for member in party_positions:
        mx, my, msx, msy = member["pos"]
        msx_iso = int(((mx - my) * (TILE_WIDTH // 2) + width // 2) * zoom + (1-zoom)*width//2 + TILE_WIDTH//2*zoom + (msx-1)*(TILE_WIDTH//6))
        msy_iso = int(((mx + my) * (TILE_HEIGHT // 2) + 50) * zoom + (1-zoom)*height//2 + TILE_HEIGHT//2*zoom + (msy-1)*(TILE_HEIGHT//6))
        margin = 32
        if 0 <= msx_iso < width and 0 <= msy_iso < height:
            continue
        dx = msx_iso - psx_iso
        dy = msy_iso - psy_iso
        if dx == 0 and dy == 0:
            continue
        angle = math.atan2(dy, dx)
        edge_x = psx_iso
        edge_y = psy_iso
        while 0 < edge_x < width and 0 < edge_y < height:
            edge_x += math.cos(angle) * 5
            edge_y += math.sin(angle) * 5
        edge_x = max(margin, min(width-margin, edge_x))
        edge_y = max(margin, min(height-margin, edge_y))
        points = [
            (edge_x, edge_y),
            (edge_x - 10*math.sin(angle), edge_y + 10*math.cos(angle)),
            (edge_x + 10*math.sin(angle), edge_y - 10*math.cos(angle))
        ]
        pygame.draw.polygon(screen, (255,255,0), points)
        # Optionally, draw member id
        font = pygame.font.SysFont(None, 16)
        screen.blit(font.render(member["id"][:4], True, (255,255,0)), (edge_x+8, edge_y-8))

def draw_emote(screen, sx, sy, emote_type, t):
    # Simple placeholder: colored circle and label, animates up and down
    color = EMOTE_TYPES[emote_type]["color"]
    label = EMOTE_TYPES[emote_type]["label"]
    offset = int(10 * math.sin(t * 6))
    pygame.draw.circle(screen, color, (sx, sy - 32 + offset), 16)
    font = pygame.font.SysFont(None, 18, bold=True)
    text = font.render(label, True, color)
    screen.blit(text, (sx - text.get_width() // 2, sy - 56 + offset))

def draw_party_emotes(screen, player_pos, party_positions, party_emotes, zoom):
    width, height = screen.get_size()
    now = pygame.time.get_ticks() / 1000.0
    px, py = player_pos
    for member in party_positions:
        mx, my = member["pos"]
        mid = member["id"]
        sx = int(((mx - my) * (TILE_WIDTH // 2) + width // 2) * zoom + (1-zoom)*width//2 + TILE_WIDTH//2*zoom)
        sy = int(((mx + my) * (TILE_HEIGHT // 2) + 50) * zoom + (1-zoom)*height//2 + TILE_HEIGHT//2*zoom)
        if mid in party_emotes:
            emote = party_emotes[mid]
            if emote["until"] > now:
                t = now % 1.0
                draw_emote(screen, sx, sy, emote["type"], t)

def draw_city(screen):
    screen.fill(CITY_BG_COLOR)
    font = pygame.font.SysFont(None, 36, bold=True)
    label = font.render("Main City: Imperial Americanopolis", True, CITY_LABEL_COLOR)
    screen.blit(label, (screen.get_width()//2 - label.get_width()//2, 40))
    # Draw city features (placeholder)
    font2 = pygame.font.SysFont(None, 28)
    features = [
        "[S]hop: Gear Up",
        "[R]est: Restore HP/MP",
        "[W]aypoint: Warp to Campaign",
        "Vendors, Crafting, Socialize..."
    ]
    for i, f in enumerate(features):
        text = font2.render(f, True, CITY_UI_COLOR)
        screen.blit(text, (screen.get_width()//2 - text.get_width()//2, 120 + i*36))
    # Draw city map (placeholder rectangles)
    pygame.draw.rect(screen, (120, 120, 180), (180, 300, 440, 180))
    pygame.draw.rect(screen, (255, 255, 0), (180, 300, 440, 180), 3)
    font3 = pygame.font.SysFont(None, 24)
    screen.blit(font3.render("Rest Area", True, (255,255,255)), (200, 320))
    screen.blit(font3.render("Gear Shop", True, (255,255,255)), (500, 320))
    screen.blit(font3.render("Waypoint", True, (255,255,255)), (340, 420))

def find_path(grid, start, goal):
    """A* pathfinding on (x, y, sx, sy) subtiles."""
    def neighbors(pos):
        x, y, sx, sy = pos
        for dx, dy, dsx, dsy in [
            (0, 0, 1, 0), (0, 0, -1, 0), (0, 0, 0, 1), (0, 0, 0, -1),
            (1, 0, 0, 0), (-1, 0, 0, 0), (0, 1, 0, 0), (0, -1, 0, 0)
        ]:
            nx, ny, nsx, nsy = x+dx, y+dy, sx+dsx, sy+dsy
            if 0 <= nx < len(grid[0]) and 0 <= ny < len(grid) and 0 <= nsx < SUBTILES_PER_TILE and 0 <= nsy < SUBTILES_PER_TILE:
                if is_walkable_subtile(grid, nx, ny, nsx, nsy):
                    yield (nx, ny, nsx, nsy)
    def heuristic(a, b):
        return abs(a[0]-b[0]) + abs(a[1]-b[1]) + abs(a[2]-b[2]) + abs(a[3]-b[3])
    open_set = [(0, start)]
    came_from = {}
    g_score = {start: 0}
    while open_set:
        _, current = heapq.heappop(open_set)
        if current == goal:
            path = []
            while current in came_from:
                path.append(current)
                current = came_from[current]
            path.append(start)
            return path[::-1]
        for neighbor in neighbors(current):
            tentative_g = g_score[current] + 1
            if neighbor not in g_score or tentative_g < g_score[neighbor]:
                came_from[neighbor] = current
                g_score[neighbor] = tentative_g
                heapq.heappush(open_set, (tentative_g + heuristic(neighbor, goal), neighbor))
    return []

def main():
    pygame.init()
    screen = pygame.display.set_mode((800, 600))
    pygame.display.set_caption("Isometric Roguelike Client")
    clock = pygame.time.Clock()
    send_queue = asyncio.Queue()
    recv_queue = asyncio.Queue()
    uri = "ws://localhost:8765"

    # Start networking in background
    loop = asyncio.get_event_loop()
    asyncio.ensure_future(network_loop(uri, send_queue, recv_queue))

    global player_pos, visible_monsters, zoom, in_city, invite_input, show_party_panel
    path = []
    path_index = 0
    auto_attack_target = None
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                # City UI controls
                if in_city:
                    if event.key == pygame.K_w:
                        # Warp to campaign (request to server)
                        msg = json.dumps({"type": "warp_from_city"})
                        loop.create_task(send_queue.put(msg))
                    elif event.key == pygame.K_s:
                        # Shop (placeholder)
                        pass
                    elif event.key == pygame.K_r:
                        # Rest (placeholder)
                        pass
                    continue  # Don't process campaign controls
                # Toggle party panel
                if event.key == pygame.K_p:
                    show_party_panel = not show_party_panel
                # Invite input
                elif show_party_panel and event.key == pygame.K_BACKSPACE:
                    invite_input = invite_input[:-1]
                elif show_party_panel and event.key == pygame.K_RETURN:
                    if invite_input:
                        msg = json.dumps({"type": "party_invite", "payload": {"invitee_id": invite_input}})
                        loop.create_task(send_queue.put(msg))
                        invite_input = ""
                elif show_party_panel and event.unicode.isalnum() and len(invite_input) < 8:
                    invite_input += event.unicode
                # Buttons
                elif show_party_panel and event.key == pygame.K_i:
                    if invite_input:
                        msg = json.dumps({"type": "party_invite", "payload": {"invitee_id": invite_input}})
                        loop.create_task(send_queue.put(msg))
                        invite_input = ""
                elif show_party_panel and event.key == pygame.K_t:
                    # Teleport to first member (for demo)
                    if party_members:
                        msg = json.dumps({"type": "teleport", "payload": {"target_id": party_members[0]}})
                        loop.create_task(send_queue.put(msg))
                elif show_party_panel and event.key == pygame.K_k:
                    # Vote kick first member (for demo)
                    if party_members:
                        msg = json.dumps({"type": "party_kick_vote", "payload": {"target_id": party_members[0]}})
                        loop.create_task(send_queue.put(msg))
                # Warp to city if on waypoint
                if event.key == pygame.K_w and is_on_waypoint():
                    msg = json.dumps({"type": "warp_to_city"})
                    loop.create_task(send_queue.put(msg))
                # Zoom controls
                if event.key == pygame.K_EQUALS or event.key == pygame.K_PLUS:
                    zoom = min(ZOOM_MAX, zoom + ZOOM_STEP)
                elif event.key == pygame.K_MINUS:
                    zoom = max(ZOOM_MIN, zoom - ZOOM_STEP)
                else:
                    move = None
                    ds = [0, 0]
                    if event.key == pygame.K_UP:
                        move = (0, -1)
                    elif event.key == pygame.K_DOWN:
                        move = (0, 1)
                    elif event.key == pygame.K_LEFT:
                        move = (-1, 0)
                    elif event.key == pygame.K_RIGHT:
                        move = (1, 0)
                    # Subtile movement with shift+arrow
                    if event.mod & pygame.KMOD_SHIFT:
                        if event.key == pygame.K_UP:
                            ds = [0, -1]
                        elif event.key == pygame.K_DOWN:
                            ds = [0, 1]
                        elif event.key == pygame.K_LEFT:
                            ds = [-1, 0]
                        elif event.key == pygame.K_RIGHT:
                            ds = [1, 0]
                        move = (0, 0)
                    if move or ds != [0, 0]:
                        msg = json.dumps({
                            "type": "move",
                            "payload": {"dx": move[0] if move else 0, "dy": move[1] if move else 0, "dsx": ds[0], "dsy": ds[1]}
                        })
                        loop.create_task(send_queue.put(msg))
                # Emote keys
                for emote_type, emote_info in EMOTE_TYPES.items():
                    if event.key == emote_info["key"]:
                        msg = json.dumps({"type": "emote", "payload": {"emote": emote_type}})
                        loop.create_task(send_queue.put(msg))
            elif event.type == pygame.MOUSEBUTTONDOWN and not in_city:
                mx, my = pygame.mouse.get_pos()
                # Convert screen to isometric tile/subtile
                for y in range(map_height):
                    for x in range(map_width):
                        for sx in range(SUBTILES_PER_TILE):
                            for sy in range(SUBTILES_PER_TILE):
                                # Calculate screen pos for this subtile
                                offset_x = (sx - 1) * (TILE_WIDTH // 6)
                                offset_y = (sy - 1) * (TILE_HEIGHT // 6)
                                sx_iso = int(((x - y) * (TILE_WIDTH // 2) + screen.get_width() // 2) * zoom + (1-zoom)*screen.get_width()//2 + TILE_WIDTH//2*zoom + offset_x)
                                sy_iso = int(((x + y) * (TILE_HEIGHT // 2) + 50) * zoom + (1-zoom)*screen.get_height()//2 + TILE_HEIGHT//2*zoom + offset_y)
                                if abs(mx - sx_iso) < 12 and abs(my - sy_iso) < 12:
                                    if is_walkable_subtile(map_grid, x, y, sx, sy):
                                        start = tuple(player_pos)
                                        goal = (x, y, sx, sy)
                                        path = find_path(map_grid, start, goal)
                                        path_index = 0
                                    break
        # Step along path if any
        if path and path_index < len(path):
            next_pos = path[path_index]
            dx = next_pos[0] - player_pos[0]
            dy = next_pos[1] - player_pos[1]
            dsx = next_pos[2] - player_pos[2]
            dsy = next_pos[3] - player_pos[3]
            if (dx, dy, dsx, dsy) != (0, 0, 0, 0):
                msg = json.dumps({
                    "type": "move",
                    "payload": {"dx": dx, "dy": dy, "dsx": dsx, "dsy": dsy}
                })
                loop.create_task(send_queue.put(msg))
            path_index += 1
            if path_index >= len(path):
                path = []
        # Auto-attack if monster in range
        weapon_range = 1  # 1 subtile for now
        auto_attack_target = None
        for m in visible_monsters:
            mx, my = m["pos"]
            # Check if monster is within 1 tile (any subtile)
            if abs(mx - player_pos[0]) <= 1 and abs(my - player_pos[1]) <= 1:
                auto_attack_target = m
                break
        if auto_attack_target:
            # Send attack command (automatic)
            msg = json.dumps({"type": "attack", "payload": {"target_id": auto_attack_target["id"]}})
            loop.create_task(send_queue.put(msg))
        # Handle messages from server
        try:
            while True:
                msg = recv_queue.get_nowait()
                data = json.loads(msg)
                if data.get("type") == "state":
                    # Update player position from server state
                    player = data["payload"].get("player")
                    if player:
                        player_pos = player["pos"]
                    # Update visible monsters
                    visible_monsters = data["payload"].get("monsters", [])
                    # Update party member positions
                    party_positions = data["payload"].get("party_positions", [])
        except asyncio.QueueEmpty:
            pass
        screen.fill(BG_COLOR)
        if in_city:
            draw_city(screen)
        else:
            draw_isometric_grid(screen)
            draw_monsters(screen, visible_monsters)
            draw_floating_damage(screen)
            draw_player(screen, player_pos)
            draw_party_markers(screen, player_pos, party_positions, zoom)
            draw_ui(screen)
            if show_party_panel:
                draw_party_panel(screen)
            draw_party_emotes(screen, player_pos, party_positions, party_emotes, zoom)
            # Draw player HP bar
            draw_player_hp(screen, player_pos, player_hp, player_max_hp)
            # Show warp prompt if on waypoint
            if map_grid and map_grid[player_pos[1]][player_pos[0]] == 3:
                font = pygame.font.SysFont(None, 28, bold=True)
                text = font.render("[W] Warp to City", True, (255,255,0))
                screen.blit(text, (screen.get_width()//2 - text.get_width()//2, 10))
        pygame.display.flip()
        clock.tick(30)
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    asyncio.run(main())
