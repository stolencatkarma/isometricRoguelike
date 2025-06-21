# Entry point for the Python client
# Uses pygame for isometric rendering and websockets for networking
import asyncio
import websockets
import json
import pygame
import sys
import threading

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
player_pos = [5, 5]

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

# Party info
party_members = []
party_invites = []
party_id = None
invite_input = ""
show_party_panel = False

# Monster state from server
visible_monsters = []
# Zoom level
zoom = 1.0
ZOOM_MIN = 0.5
ZOOM_MAX = 2.5
ZOOM_STEP = 0.1

async def network_loop(uri, send_queue, recv_queue):
    global map_data, map_grid, map_width, map_height, player_class, player_stats, player_level, player_xp, player_id, party_members, party_invites, party_id
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
            global player_class, player_stats, player_level, player_xp, party_members, party_invites, party_id
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
                    elif data.get("type") == "party_info":
                        payload = data["payload"]
                        party_id = payload.get("party_id")
                        party_members = payload.get("members", [])
                        party_invites = payload.get("invites", [])
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
    x, y = pos
    sx = int(((x - y) * (TILE_WIDTH // 2) + screen.get_width() // 2) * zoom + (1-zoom)*screen.get_width()//2)
    sy = int(((x + y) * (TILE_HEIGHT // 2) + 50) * zoom + (1-zoom)*screen.get_height()//2)
    pygame.draw.circle(screen, PLAYER_COLOR, (sx + int(TILE_WIDTH//2 * zoom), sy + int(TILE_HEIGHT//2 * zoom)), int(12*zoom))

def draw_monsters(screen, monsters):
    for m in monsters:
        x, y = m["pos"]
        sx = int(((x - y) * (TILE_WIDTH // 2) + screen.get_width() // 2) * zoom + (1-zoom)*screen.get_width()//2)
        sy = int(((x + y) * (TILE_HEIGHT // 2) + 50) * zoom + (1-zoom)*screen.get_height()//2)
        color = (0,255,0) if m["type"]=="goblin" else (200,200,200) if m["type"]=="skeleton" else (0,255,255)
        pygame.draw.rect(screen, color, (sx + int(TILE_WIDTH//4*zoom), sy + int(TILE_HEIGHT//4*zoom), int(TILE_WIDTH//2*zoom), int(TILE_HEIGHT//2*zoom)))

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

    global player_pos, visible_monsters, zoom
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
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
                # Zoom controls
                if event.key == pygame.K_EQUALS or event.key == pygame.K_PLUS:
                    zoom = min(ZOOM_MAX, zoom + ZOOM_STEP)
                elif event.key == pygame.K_MINUS:
                    zoom = max(ZOOM_MIN, zoom - ZOOM_STEP)
                else:
                    move = None
                    if event.key == pygame.K_UP:
                        move = (0, -1)
                    elif event.key == pygame.K_DOWN:
                        move = (0, 1)
                    elif event.key == pygame.K_LEFT:
                        move = (-1, 0)
                    elif event.key == pygame.K_RIGHT:
                        move = (1, 0)
                    if move:
                        # Send move request to server
                        msg = json.dumps({
                            "type": "move",
                            "payload": {"dx": move[0], "dy": move[1]}
                        })
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
        except asyncio.QueueEmpty:
            pass
        screen.fill(BG_COLOR)
        draw_isometric_grid(screen)
        draw_monsters(screen, visible_monsters)
        draw_player(screen, player_pos)
        draw_ui(screen)
        if show_party_panel:
            draw_party_panel(screen)
        pygame.display.flip()
        clock.tick(30)
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    asyncio.run(main())
